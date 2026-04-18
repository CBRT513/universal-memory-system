#!/usr/bin/env python3
"""
Galactica Triage & Learning Service
Intelligent memory scoring, decay, and pattern extraction
"""

import re
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import Counter
import numpy as np

@dataclass
class MemoryScore:
    """Multi-dimensional memory scoring"""
    relevance: float      # 0-10: Context relevance
    importance: float     # 0-10: Explicit importance
    frequency: int        # Access count
    recency: datetime     # Last accessed
    decay_rate: float     # How fast it becomes irrelevant
    
    def compute_priority(self, context=None) -> float:
        """Calculate overall priority for surfacing"""
        # Time decay factor
        days_old = (datetime.now() - self.recency).days
        age_factor = 1.0 / (1 + days_old * self.decay_rate)
        
        # Frequency boost (logarithmic)
        freq_factor = min(np.log1p(self.frequency) / 3, 1.0)
        
        # Context boost if provided
        context_factor = 1.2 if context else 1.0
        
        priority = (
            self.relevance * 0.35 +
            self.importance * 0.35 +
            freq_factor * 0.15 +
            age_factor * 0.15
        ) * context_factor
        
        return min(priority, 10.0)

class TriageSystem:
    """Intelligent memory triage and scoring"""
    
    # Pattern-based scoring rules
    SCORING_RULES = [
        # Architecture & Design
        (r"ARCHITECTURE|DECISION|DESIGN\s+PATTERN", 9, 9, 0.1),  # pattern, relevance, importance, decay
        (r"TODO:|FIXME:|HACK:", 8, 6, 0.3),
        (r"BREAKING\s+CHANGE|MIGRATION", 10, 10, 0.2),
        
        # Code & Development
        (r"def |class |function |import |require", 5, 4, 0.5),
        (r"error|exception|traceback|failed", 8, 7, 0.7),
        (r"test_|spec\.|describe\(", 4, 3, 0.6),
        
        # Documentation
        (r"README|CONTRIBUTING|LICENSE", 6, 5, 0.1),
        (r"https?://|www\.", 4, 3, 0.8),
        
        # Commands & Operations  
        (r"^(ls|cd|pwd|echo|cat|grep)\s", 2, 1, 0.9),
        (r"git (add|commit|push|pull)", 3, 2, 0.8),
        (r"npm|pip|cargo|brew|apt", 3, 2, 0.7),
        
        # Insights & Learning
        (r"LEARNED:|INSIGHT:|PATTERN:", 9, 10, 0.05),
        (r"works|fixed|solved|resolved", 7, 8, 0.2),
        (r"doesn't work|broken|issue", 8, 6, 0.4),
    ]
    
    def __init__(self, db_path: str = "/usr/local/var/universal-memory-system/triage.db"):
        self.db_path = db_path
        self.init_db()
        
    def init_db(self):
        """Initialize triage database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_scores (
                memory_id TEXT PRIMARY KEY,
                relevance REAL DEFAULT 5.0,
                importance REAL DEFAULT 5.0,
                frequency INTEGER DEFAULT 0,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                decay_rate REAL DEFAULT 0.5,
                context_scores TEXT,  -- JSON dict of context-specific scores
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern TEXT,
                occurrences INTEGER DEFAULT 1,
                contexts TEXT,  -- JSON list of contexts where seen
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_insight BOOLEAN DEFAULT FALSE
            )
        """)
        
        conn.commit()
        conn.close()
        
    def score_memory(self, memory_id: str, content: str, context: Optional[str] = None) -> MemoryScore:
        """Score a memory based on content and context"""
        relevance = 5.0  # Default
        importance = 5.0
        decay_rate = 0.5
        
        # Apply pattern-based rules
        for pattern, rel, imp, decay in self.SCORING_RULES:
            if re.search(pattern, content, re.IGNORECASE):
                relevance = max(relevance, rel)
                importance = max(importance, imp)
                decay_rate = min(decay_rate, decay)  # Use slowest decay
                
        # Get or create score record
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR IGNORE INTO memory_scores (memory_id, relevance, importance, decay_rate)
            VALUES (?, ?, ?, ?)
        """, (memory_id, relevance, importance, decay_rate))
        
        cursor.execute("""
            SELECT relevance, importance, frequency, last_accessed, decay_rate
            FROM memory_scores WHERE memory_id = ?
        """, (memory_id,))
        
        row = cursor.fetchone()
        
        # Update access info
        cursor.execute("""
            UPDATE memory_scores 
            SET frequency = frequency + 1, last_accessed = CURRENT_TIMESTAMP
            WHERE memory_id = ?
        """, (memory_id,))
        
        conn.commit()
        conn.close()
        
        return MemoryScore(
            relevance=row[0],
            importance=row[1],
            frequency=row[2] + 1,
            recency=datetime.fromisoformat(row[3]),
            decay_rate=row[4]
        )
        
    def apply_decay(self):
        """Apply time-based decay to all memories"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Decay relevance based on age and decay rate
        cursor.execute("""
            UPDATE memory_scores
            SET relevance = MAX(1.0, relevance * (1.0 - decay_rate * 
                (julianday('now') - julianday(last_accessed)) / 7.0))
            WHERE julianday('now') - julianday(last_accessed) > 1
        """)
        
        conn.commit()
        conn.close()
        
    def get_top_memories(self, context: Optional[str] = None, limit: int = 20) -> List[Tuple[str, float]]:
        """Get highest priority memories for context"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT memory_id, relevance, importance, frequency, last_accessed, decay_rate
            FROM memory_scores
            ORDER BY (relevance * 0.35 + importance * 0.35 + 
                     MIN(LOG(1 + frequency) / 3, 1) * 0.15 +
                     (1.0 / (1 + julianday('now') - julianday(last_accessed))) * 0.15) DESC
            LIMIT ?
        """, (limit,))
        
        results = []
        for row in cursor.fetchall():
            score = MemoryScore(
                relevance=row[1],
                importance=row[2],
                frequency=row[3],
                recency=datetime.fromisoformat(row[4]),
                decay_rate=row[5]
            )
            priority = score.compute_priority(context)
            results.append((row[0], priority))
            
        conn.close()
        return results


class LearningService:
    """Extract patterns and insights from memory usage"""
    
    def __init__(self, triage: TriageSystem):
        self.triage = triage
        
    def extract_patterns(self, memories: List[Dict]) -> List[Dict]:
        """Find recurring patterns across memories"""
        conn = sqlite3.connect(self.triage.db_path)
        cursor = conn.cursor()
        
        patterns = []
        
        # Extract command patterns
        commands = Counter()
        for mem in memories:
            content = mem.get('content', '')
            # Look for command-like patterns
            cmd_match = re.match(r'^(\w+)\s', content)
            if cmd_match:
                commands[cmd_match.group(1)] += 1
                
        # Store frequent command patterns
        for cmd, count in commands.most_common(10):
            if count >= 3:  # Seen at least 3 times
                cursor.execute("""
                    INSERT OR REPLACE INTO patterns (pattern, occurrences, last_seen)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (f"command:{cmd}", count))
                
                patterns.append({
                    'type': 'command',
                    'pattern': cmd,
                    'frequency': count
                })
                
        # Extract error patterns
        errors = Counter()
        for mem in memories:
            content = mem.get('content', '')
            if 'error' in content.lower() or 'exception' in content.lower():
                # Extract error type
                error_match = re.search(r'(\w+Error|\w+Exception)', content)
                if error_match:
                    errors[error_match.group(1)] += 1
                    
        # Store error patterns
        for error, count in errors.most_common(5):
            if count >= 2:
                cursor.execute("""
                    INSERT OR REPLACE INTO patterns (pattern, occurrences, last_seen, is_insight)
                    VALUES (?, ?, CURRENT_TIMESTAMP, TRUE)
                """, (f"error:{error}", count))
                
                patterns.append({
                    'type': 'error_pattern',
                    'pattern': error,
                    'frequency': count,
                    'insight': f"Recurring {error} detected {count} times"
                })
                
        conn.commit()
        conn.close()
        
        return patterns
        
    def suggest_improvements(self) -> List[str]:
        """Suggest improvements based on patterns"""
        conn = sqlite3.connect(self.triage.db_path)
        cursor = conn.cursor()
        
        suggestions = []
        
        # Check for frequently accessed old memories
        cursor.execute("""
            SELECT memory_id, frequency, relevance
            FROM memory_scores
            WHERE frequency > 5 
            AND julianday('now') - julianday(last_accessed) > 7
            AND relevance < 5
        """)
        
        old_but_frequent = cursor.fetchall()
        if old_but_frequent:
            suggestions.append(
                f"Consider archiving {len(old_but_frequent)} old memories that are frequently accessed but low relevance"
            )
            
        # Check for error patterns
        cursor.execute("""
            SELECT pattern, occurrences
            FROM patterns
            WHERE pattern LIKE 'error:%'
            AND occurrences > 3
        """)
        
        error_patterns = cursor.fetchall()
        for pattern, count in error_patterns:
            error_type = pattern.split(':')[1]
            suggestions.append(
                f"Investigate recurring {error_type} ({count} occurrences)"
            )
            
        # Check for command patterns
        cursor.execute("""
            SELECT pattern, occurrences
            FROM patterns
            WHERE pattern LIKE 'command:%'
            AND occurrences > 10
        """)
        
        freq_commands = cursor.fetchall()
        if len(freq_commands) > 5:
            suggestions.append(
                "Consider creating aliases or scripts for frequently used commands"
            )
            
        conn.close()
        return suggestions
        
    def identify_insights(self) -> List[Dict]:
        """Identify cross-project insights"""
        conn = sqlite3.connect(self.triage.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT pattern, occurrences, contexts
            FROM patterns
            WHERE is_insight = TRUE
            OR occurrences > 5
            ORDER BY occurrences DESC
            LIMIT 10
        """)
        
        insights = []
        for pattern, occurrences, contexts_json in cursor.fetchall():
            contexts = json.loads(contexts_json) if contexts_json else []
            
            insight = {
                'pattern': pattern,
                'occurrences': occurrences,
                'contexts': contexts,
                'type': 'cross_project' if len(contexts) > 1 else 'project_specific'
            }
            
            # Generate insight text
            if pattern.startswith('error:'):
                insight['text'] = f"Error pattern {pattern.split(':')[1]} seen {occurrences} times"
            elif pattern.startswith('command:'):
                insight['text'] = f"Command '{pattern.split(':')[1]}' used {occurrences} times"
            else:
                insight['text'] = f"Pattern '{pattern}' detected {occurrences} times"
                
            insights.append(insight)
            
        conn.close()
        return insights


# CLI Testing
if __name__ == "__main__":
    import sys
    
    triage = TriageSystem()
    learning = LearningService(triage)
    
    if len(sys.argv) > 1:
        # Score a test memory
        test_content = " ".join(sys.argv[1:])
        score = triage.score_memory("test_memory", test_content)
        print(f"Content: {test_content}")
        print(f"Relevance: {score.relevance}")
        print(f"Importance: {score.importance}")
        print(f"Priority: {score.compute_priority()}")
        print(f"Decay rate: {score.decay_rate}")
    else:
        print("Applying decay...")
        triage.apply_decay()
        
        print("\nTop memories:")
        for memory_id, priority in triage.get_top_memories(limit=5):
            print(f"  {memory_id}: {priority:.2f}")
            
        print("\nSuggested improvements:")
        for suggestion in learning.suggest_improvements():
            print(f"  - {suggestion}")