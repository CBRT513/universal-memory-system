#!/usr/bin/env python3
"""
Article Capture Database Schema
Part of Milestone A - Visual MVP
"""

import sqlite3
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def create_capture_tables(db_path: str = None):
    """Create capture-related tables in the UMS database"""
    
    if db_path is None:
        # Use the main UMS database
        db_path = Path(__file__).parent.parent / "memories.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Main captures table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS captures (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            project TEXT DEFAULT 'vader-lab',
            source_url TEXT,
            source_domain TEXT,
            source_title TEXT,
            source_author TEXT,
            notes TEXT,
            score REAL,
            actionability TEXT,
            status TEXT DEFAULT 'queued',
            error TEXT,
            dedup_hash TEXT,
            UNIQUE(dedup_hash)
        )
        """)
        
        # Create index for dedup lookups
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_captures_dedup 
        ON captures(dedup_hash, created_at)
        """)
        
        # Content storage (separated for performance)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS capture_content (
            capture_id TEXT PRIMARY KEY,
            text TEXT NOT NULL,
            summary TEXT,
            length_tokens INTEGER,
            FOREIGN KEY (capture_id) REFERENCES captures(id)
        )
        """)
        
        # Job status tracking
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS capture_status (
            job_id TEXT PRIMARY KEY,
            capture_id TEXT,
            created_at TEXT NOT NULL,
            last_update TEXT NOT NULL,
            state TEXT NOT NULL DEFAULT 'queued',
            progress_msg TEXT,
            FOREIGN KEY (capture_id) REFERENCES captures(id)
        )
        """)
        
        # Create indexes for common queries
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_captures_created 
        ON captures(created_at DESC)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_captures_project 
        ON captures(project, created_at DESC)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_capture_status_state 
        ON capture_status(state, last_update DESC)
        """)
        
        conn.commit()
        logger.info("Capture tables created successfully")
        
    except Exception as e:
        logger.error(f"Error creating capture tables: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def migrate_existing_database():
    """Run this to add capture tables to existing UMS database"""
    db_path = "/usr/local/share/universal-memory-system/memories.db"
    
    if not Path(db_path).exists():
        # Try alternate locations
        alt_paths = [
            Path.home() / ".ums" / "memories.db",
            Path(__file__).parent.parent / "memories.db"
        ]
        for alt in alt_paths:
            if alt.exists():
                db_path = str(alt)
                break
    
    print(f"Adding capture tables to: {db_path}")
    create_capture_tables(db_path)
    print("Migration complete!")

if __name__ == "__main__":
    migrate_existing_database()