#!/usr/bin/env python3
"""
Implementation Queue System - Manages pending implementations from articles
Provides approval/hold/deny functionality with GUI support
"""

import json
import sqlite3
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImplementationQueue:
    """Manages the queue of pending implementations awaiting approval"""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the implementation queue"""
        if db_path is None:
            db_path = Path.home() / ".ai-memory" / "implementation_queue.db"
        
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize the queue database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS implementation_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    memory_id TEXT,
                    article_title TEXT,
                    implementation_type TEXT,
                    description TEXT,
                    details TEXT,
                    priority TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reviewed_at TIMESTAMP,
                    decision TEXT,
                    decision_reason TEXT,
                    metadata TEXT
                )
            """)
            conn.commit()
    
    def add_implementation(self, 
                         memory_id: str,
                         article_title: str,
                         implementation_type: str,
                         description: str,
                         details: Dict[str, Any],
                         priority: str = "medium",
                         metadata: Optional[Dict] = None) -> int:
        """Add a new implementation to the queue"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO implementation_queue 
                (memory_id, article_title, implementation_type, description, 
                 details, priority, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                memory_id,
                article_title,
                implementation_type,
                description,
                json.dumps(details),
                priority,
                json.dumps(metadata or {})
            ))
            
            implementation_id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"Added implementation #{implementation_id} to queue: {description[:50]}...")
            return implementation_id
    
    def get_pending_implementations(self, limit: Optional[int] = None) -> List[Dict]:
        """Get all pending implementations awaiting approval"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            query = """
                SELECT * FROM implementation_queue 
                WHERE status = 'pending'
                ORDER BY 
                    CASE priority 
                        WHEN 'high' THEN 1
                        WHEN 'medium' THEN 2
                        WHEN 'low' THEN 3
                    END,
                    created_at DESC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor = conn.execute(query)
            
            implementations = []
            for row in cursor:
                impl = dict(row)
                impl['details'] = json.loads(impl['details'])
                impl['metadata'] = json.loads(impl['metadata']) if impl['metadata'] else {}
                implementations.append(impl)
            
            return implementations
    
    def get_implementation_by_id(self, impl_id: int) -> Optional[Dict]:
        """Get a specific implementation by ID"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM implementation_queue WHERE id = ?", 
                (impl_id,)
            )
            
            row = cursor.fetchone()
            if row:
                impl = dict(row)
                impl['details'] = json.loads(impl['details'])
                impl['metadata'] = json.loads(impl['metadata']) if impl['metadata'] else {}
                return impl
            
            return None
    
    def approve_implementation(self, impl_id: int, reason: Optional[str] = None) -> bool:
        """Approve an implementation for execution"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE implementation_queue 
                SET status = 'approved',
                    decision = 'approved',
                    decision_reason = ?,
                    reviewed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (reason or "User approved", impl_id))
            
            conn.commit()
            
            logger.info(f"Implementation #{impl_id} approved")
            return True
    
    def deny_implementation(self, impl_id: int, reason: Optional[str] = None) -> bool:
        """Deny an implementation"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE implementation_queue 
                SET status = 'denied',
                    decision = 'denied',
                    decision_reason = ?,
                    reviewed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (reason or "User denied", impl_id))
            
            conn.commit()
            
            logger.info(f"Implementation #{impl_id} denied")
            return True
    
    def hold_implementation(self, impl_id: int, reason: Optional[str] = None) -> bool:
        """Put an implementation on hold for later review"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE implementation_queue 
                SET status = 'on_hold',
                    decision = 'hold',
                    decision_reason = ?,
                    reviewed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (reason or "On hold for later review", impl_id))
            
            conn.commit()
            
            logger.info(f"Implementation #{impl_id} put on hold")
            return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get queue statistics"""
        
        with sqlite3.connect(self.db_path) as conn:
            # Count by status
            cursor = conn.execute("""
                SELECT status, COUNT(*) as count 
                FROM implementation_queue 
                GROUP BY status
            """)
            
            status_counts = {row[0]: row[1] for row in cursor}
            
            # Count by type
            cursor = conn.execute("""
                SELECT implementation_type, COUNT(*) as count 
                FROM implementation_queue 
                WHERE status = 'pending'
                GROUP BY implementation_type
            """)
            
            type_counts = {row[0]: row[1] for row in cursor}
            
            # Count by priority
            cursor = conn.execute("""
                SELECT priority, COUNT(*) as count 
                FROM implementation_queue 
                WHERE status = 'pending'
                GROUP BY priority
            """)
            
            priority_counts = {row[0]: row[1] for row in cursor}
            
            return {
                "total_pending": status_counts.get('pending', 0),
                "total_approved": status_counts.get('approved', 0),
                "total_denied": status_counts.get('denied', 0),
                "total_on_hold": status_counts.get('on_hold', 0),
                "by_type": type_counts,
                "by_priority": priority_counts,
                "status_breakdown": status_counts
            }
    
    def execute_approved_implementations(self) -> Dict[str, Any]:
        """Execute all approved implementations"""
        
        results = {
            "executed": [],
            "failed": [],
            "total": 0
        }
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM implementation_queue 
                WHERE status = 'approved' AND decision = 'approved'
                ORDER BY created_at
            """)
            
            for row in cursor:
                impl = dict(row)
                impl['details'] = json.loads(impl['details'])
                
                try:
                    # Execute based on type
                    if impl['implementation_type'] == 'package_install':
                        result = self._execute_package_install(impl['details'])
                    elif impl['implementation_type'] == 'code_creation':
                        result = self._execute_code_creation(impl['details'])
                    elif impl['implementation_type'] == 'config_change':
                        result = self._execute_config_change(impl['details'])
                    else:
                        result = {"success": False, "error": f"Unknown type: {impl['implementation_type']}"}
                    
                    if result.get("success"):
                        results["executed"].append({
                            "id": impl['id'],
                            "description": impl['description'],
                            "result": result
                        })
                        
                        # Mark as executed
                        conn.execute(
                            "UPDATE implementation_queue SET status = 'executed' WHERE id = ?",
                            (impl['id'],)
                        )
                    else:
                        results["failed"].append({
                            "id": impl['id'],
                            "description": impl['description'],
                            "error": result.get("error")
                        })
                        
                except Exception as e:
                    results["failed"].append({
                        "id": impl['id'],
                        "description": impl['description'],
                        "error": str(e)
                    })
            
            conn.commit()
        
        results["total"] = len(results["executed"]) + len(results["failed"])
        return results
    
    def _execute_package_install(self, details: Dict) -> Dict:
        """Execute a package installation"""
        import subprocess
        
        try:
            packages = details.get("packages", [])
            if not packages:
                return {"success": False, "error": "No packages specified"}
            
            cmd = ["pip3", "install"] + packages
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return {"success": True, "output": result.stdout}
            else:
                return {"success": False, "error": result.stderr}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _execute_code_creation(self, details: Dict) -> Dict:
        """Create a code implementation file"""
        try:
            file_path = Path(details.get("file_path", ""))
            code_content = details.get("code", "")
            
            if not file_path or not code_content:
                return {"success": False, "error": "Missing file path or code content"}
            
            # Create parent directories
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the code
            file_path.write_text(code_content)
            
            return {"success": True, "file_created": str(file_path)}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _execute_config_change(self, details: Dict) -> Dict:
        """Execute a configuration change"""
        # For now, just log it - actual implementation would modify config files
        return {
            "success": False, 
            "error": "Config changes require manual review for safety"
        }


# Example usage for testing
if __name__ == "__main__":
    queue = ImplementationQueue()
    
    # Add some test implementations
    impl_id = queue.add_implementation(
        memory_id="test_001",
        article_title="Browser Automation Article",
        implementation_type="package_install",
        description="Install Playwright for browser automation",
        details={"packages": ["playwright"]},
        priority="high"
    )
    
    impl_id2 = queue.add_implementation(
        memory_id="test_002",
        article_title="Python Libraries Article",
        implementation_type="code_creation",
        description="Create Sentence-Transformers integration",
        details={
            "file_path": "implementations/sentence_transformer_example.py",
            "code": "from sentence_transformers import SentenceTransformer\n# Example code"
        },
        priority="medium"
    )
    
    # Get pending implementations
    pending = queue.get_pending_implementations()
    print(f"\n📋 Pending Implementations: {len(pending)}")
    for impl in pending:
        print(f"  - [{impl['priority']}] {impl['description']}")
    
    # Get statistics
    stats = queue.get_statistics()
    print(f"\n📊 Queue Statistics:")
    print(f"  Pending: {stats['total_pending']}")
    print(f"  Approved: {stats['total_approved']}")
    print(f"  On Hold: {stats['total_on_hold']}")