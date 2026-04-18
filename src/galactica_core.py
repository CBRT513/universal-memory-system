#!/usr/local/share/universal-memory-system/venv/bin/python3
"""
Galactica Core - The Universal AI Interface
Your persistent, intelligent interface to everything
"""

import os
import json
import asyncio
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import subprocess
import requests
from dataclasses import dataclass
import yaml

@dataclass
class GalacticaSession:
    """Represents a persistent Galactica session"""
    id: str
    user: str
    context: Dict
    memory_stream: List[Dict]
    active_project: Optional[str]
    capabilities: List[str]
    
class GalacticaCore:
    """
    The central intelligence that:
    - Maintains persistent identity
    - Routes to appropriate tools
    - Remembers everything
    - Learns from interactions
    """
    
    def __init__(self):
        self.home = Path("/usr/local/share/universal-memory-system")
        self.db_path = self.home / "galactica.db"
        self.config = self.load_config()
        self.session = None
        self.init_db()
        self.load_capabilities()
        
    def load_config(self):
        """Load Galactica configuration"""
        config_path = self.home / "galactica_config.yaml"
        if config_path.exists():
            with open(config_path) as f:
                return yaml.safe_load(f)
        return {
            "name": "Galactica",
            "version": "1.0",
            "personality": "helpful, intelligent, focused",
            "default_model": "claude",
            "tools": {
                "claude": "claude",
                "ollama": "ollama",
                "python": "python3",
                "bash": "bash"
            }
        }
        
    def init_db(self):
        """Initialize Galactica's persistent database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user TEXT,
                started_at TIMESTAMP,
                last_active TIMESTAMP,
                context TEXT,
                memory_count INTEGER DEFAULT 0
            )
        """)
        
        # Interactions table - every interaction is remembered
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp TIMESTAMP,
                user_input TEXT,
                galactica_response TEXT,
                tool_used TEXT,
                context TEXT,
                success BOOLEAN,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        """)
        
        # Knowledge table - learned patterns and preferences
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern TEXT,
                response_template TEXT,
                frequency INTEGER DEFAULT 1,
                last_used TIMESTAMP,
                effectiveness REAL DEFAULT 0.5
            )
        """)
        
        # Capabilities table - what Galactica can do
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS capabilities (
                name TEXT PRIMARY KEY,
                description TEXT,
                command_template TEXT,
                requirements TEXT,
                enabled BOOLEAN DEFAULT TRUE
            )
        """)
        
        conn.commit()
        conn.close()
        
    def load_capabilities(self):
        """Load and register Galactica's capabilities"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Register core capabilities
        capabilities = [
            ("code_analysis", "Analyze and understand code", "claude '{prompt}'", "claude", True),
            ("code_generation", "Generate new code", "claude '{prompt}'", "claude", True),
            ("memory_search", "Search memories", "curl http://127.0.0.1:8091/api/memory/search?q={query}", "ums", True),
            ("memory_store", "Store memories", "curl -X POST http://127.0.0.1:8091/api/memory/store", "ums", True),
            ("run_python", "Execute Python code", "python3 -c '{code}'", "python3", True),
            ("run_bash", "Execute bash commands", "bash -c '{command}'", "bash", True),
            ("web_search", "Search the web", "claude --web-search '{query}'", "claude", True),
            ("project_context", "Detect project context", "python3 {home}/src/galactica_context.py {path}", "python3", True),
            ("triage_memory", "Score memory relevance", "python3 {home}/src/galactica_triage.py '{memory}'", "python3", True),
        ]
        
        for cap in capabilities:
            cursor.execute("""
                INSERT OR IGNORE INTO capabilities (name, description, command_template, requirements, enabled)
                VALUES (?, ?, ?, ?, ?)
            """, cap)
            
        conn.commit()
        conn.close()
        
    def start_session(self, user: str = None) -> str:
        """Start a new Galactica session"""
        import uuid
        session_id = f"galactica_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO sessions (id, user, started_at, last_active, context)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, user or "default", datetime.now(), datetime.now(), "{}"))
        
        conn.commit()
        conn.close()
        
        self.session = GalacticaSession(
            id=session_id,
            user=user or "default",
            context={},
            memory_stream=[],
            active_project=None,
            capabilities=self.get_enabled_capabilities()
        )
        
        return session_id
        
    def get_enabled_capabilities(self) -> List[str]:
        """Get list of enabled capabilities"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM capabilities WHERE enabled = TRUE")
        capabilities = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return capabilities
        
    def remember_interaction(self, user_input: str, response: str, tool: str, success: bool = True):
        """Store every interaction in memory"""
        if not self.session:
            return
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO interactions (session_id, timestamp, user_input, galactica_response, tool_used, context, success)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            self.session.id,
            datetime.now(),
            user_input,
            response,
            tool,
            json.dumps(self.session.context),
            success
        ))
        
        # Update session last_active
        cursor.execute("""
            UPDATE sessions SET last_active = ?, memory_count = memory_count + 1
            WHERE id = ?
        """, (datetime.now(), self.session.id))
        
        conn.commit()
        conn.close()
        
        # Add to memory stream
        self.session.memory_stream.append({
            "timestamp": datetime.now().isoformat(),
            "input": user_input,
            "response": response,
            "tool": tool
        })
        
    def learn_pattern(self, pattern: str, response: str, effectiveness: float = 0.5):
        """Learn from successful interactions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if pattern exists
        cursor.execute("SELECT frequency FROM knowledge WHERE pattern = ?", (pattern,))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute("""
                UPDATE knowledge 
                SET frequency = frequency + 1, 
                    last_used = ?,
                    effectiveness = (effectiveness + ?) / 2
                WHERE pattern = ?
            """, (datetime.now(), effectiveness, pattern))
        else:
            cursor.execute("""
                INSERT INTO knowledge (pattern, response_template, frequency, last_used, effectiveness)
                VALUES (?, ?, 1, ?, ?)
            """, (pattern, response, datetime.now(), effectiveness))
            
        conn.commit()
        conn.close()
        
    def route_request(self, request: str) -> Dict:
        """
        Intelligently route requests to appropriate tools
        Returns the tool to use and processed request
        """
        request_lower = request.lower()
        
        # Detect intent
        if any(word in request_lower for word in ['code', 'write', 'create', 'implement', 'fix', 'debug']):
            return {"tool": "claude", "action": "code"}
        elif any(word in request_lower for word in ['remember', 'recall', 'search memory', 'what did']):
            return {"tool": "memory", "action": "search"}
        elif any(word in request_lower for word in ['store', 'save', 'note']):
            return {"tool": "memory", "action": "store"}
        elif any(word in request_lower for word in ['run', 'execute', 'test']):
            if '.py' in request or 'python' in request_lower:
                return {"tool": "python", "action": "execute"}
            else:
                return {"tool": "bash", "action": "execute"}
        elif any(word in request_lower for word in ['analyze', 'explain', 'what is', 'how does']):
            return {"tool": "claude", "action": "analyze"}
        else:
            return {"tool": "claude", "action": "general"}
            
    def execute_tool(self, tool: str, action: str, request: str) -> str:
        """Execute the appropriate tool with the request"""
        
        if tool == "claude":
            # For now, return a message about what would be done
            # In production, this would use Claude API or a non-interactive mode
            return f"[Would use Claude for: {action} - {request[:100]}...]"
            
        elif tool == "memory" and action == "search":
            # Search memories
            query = request.replace("search", "").replace("remember", "").strip()
            response = requests.get(f"http://127.0.0.1:8091/api/memory/search?q={query}")
            if response.ok:
                memories = response.json().get('results', [])
                return "\n".join([m.get('content', '') for m in memories[:5]])
            return "No memories found"
            
        elif tool == "memory" and action == "store":
            # Store memory
            content = request.replace("store", "").replace("save", "").strip()
            response = requests.post(
                "http://127.0.0.1:8091/api/memory/store",
                json={"content": content, "kind": "note", "tags": ["galactica"]}
            )
            return "Memory stored" if response.ok else "Failed to store memory"
            
        elif tool == "python":
            # Execute Python
            code = request.replace("run", "").replace("execute", "").strip()
            result = subprocess.run(["python3", "-c", code], capture_output=True, text=True)
            return result.stdout or result.stderr
            
        elif tool == "bash":
            # Execute bash
            cmd = request.replace("run", "").replace("execute", "").strip()
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.stdout or result.stderr
            
        return "Unknown tool or action"
        
    def process(self, user_input: str) -> str:
        """
        Main processing function - the heart of Galactica
        """
        # Start session if needed
        if not self.session:
            self.start_session()
            
        # Route the request
        routing = self.route_request(user_input)
        
        # Execute with appropriate tool
        response = self.execute_tool(routing['tool'], routing['action'], user_input)
        
        # Remember the interaction
        self.remember_interaction(user_input, response, routing['tool'])
        
        # Learn from it
        if response and "error" not in response.lower():
            self.learn_pattern(user_input[:50], response[:100], 0.8)
            
        return response
        
    def get_context_prompt(self) -> str:
        """Generate context prompt for Claude or other tools"""
        if not self.session:
            return ""
            
        recent_memories = self.session.memory_stream[-5:] if self.session.memory_stream else []
        
        prompt = f"""You are part of Galactica, a unified AI system.
        
Current session: {self.session.id}
Active project: {self.session.active_project or 'None'}

Recent interactions:
"""
        for mem in recent_memories:
            prompt += f"- {mem['input'][:50]}... -> {mem['tool']}\n"
            
        return prompt


# CLI Interface
if __name__ == "__main__":
    import sys
    import readline  # For better CLI experience
    
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                    GALACTICA CORE                         ║
    ║              Your Universal AI Interface                  ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    galactica = GalacticaCore()
    session_id = galactica.start_session()
    print(f"Session started: {session_id}")
    print("Type 'help' for commands, 'exit' to quit\n")
    
    while True:
        try:
            user_input = input("Galactica> ").strip()
            
            if user_input.lower() == 'exit':
                print("Galactica session ended.")
                break
            elif user_input.lower() == 'help':
                print("""
Commands:
- Any natural language request
- 'remember [query]' - Search memories
- 'store [content]' - Store memory
- 'run [code]' - Execute code
- 'analyze [topic]' - Analyze something
- 'exit' - End session
                """)
            else:
                response = galactica.process(user_input)
                print(response)
                print()
                
        except KeyboardInterrupt:
            print("\nGalactica session interrupted.")
            break
        except Exception as e:
            print(f"Error: {e}")
            continue