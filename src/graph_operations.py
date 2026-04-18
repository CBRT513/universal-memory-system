#!/usr/bin/env python3
"""
Graph Operations Module - Milestone C
Idempotent operations for graph manipulation
"""

import json
import sqlite3
import logging
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

try:
    from .graph_normalization import normalize_name, entity_hash, edge_hash
except ImportError:
    from graph_normalization import normalize_name, entity_hash, edge_hash

logger = logging.getLogger(__name__)

class GraphOperations:
    """Handles idempotent graph operations"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Use the canonical database
            db_path = Path.home() / ".ai-memory" / "memories.db"
        self.db_path = str(db_path)
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def upsert_entity(self, 
                     project_id: str, 
                     name: str, 
                     etype: str, 
                     belief: float = 0.7,
                     metadata: Optional[Dict] = None,
                     source: str = "rule",
                     confidence: Optional[float] = None,
                     extractor_version: str = "rule@1") -> int:
        """
        Idempotent entity upsert
        
        Args:
            project_id: Project identifier
            name: Raw entity name
            etype: Entity type (person, org, tech, concept, etc.)
            belief: Confidence score
            metadata: Additional metadata
        
        Returns:
            Entity ID (existing or newly created)
        """
        conn = self.get_connection()
        try:
            # Normalize name
            try:
                nn = normalize_name(name, etype)
            except ValueError as e:
                logger.warning(f"Cannot normalize entity name '{name}': {e}")
                return None
            
            # Generate hash
            eh = entity_hash(etype, nn, project_id)
            
            # Check if exists
            cur = conn.execute(
                "SELECT id FROM entities WHERE entity_hash=?", 
                (eh,)
            )
            row = cur.fetchone()
            if row:
                return row[0]
            
            # Use confidence if provided, otherwise use belief
            final_confidence = confidence if confidence is not None else belief
            
            # Insert new entity with source info
            cur = conn.execute(
                """INSERT INTO entities(project_id, type, name, normalized_name, belief, entity_hash, 
                                      source, confidence, extractor_version)
                   VALUES(?,?,?,?,?,?,?,?,?)""",
                (project_id, etype, name, nn, belief, eh, source, final_confidence, extractor_version)
            )
            conn.commit()
            
            entity_id = cur.lastrowid
            logger.info(f"Created entity {entity_id}: {etype}:{nn}")
            return entity_id
            
        finally:
            conn.close()
    
    def upsert_edge(self,
                   project_id: str,
                   src_id: int,
                   dst_id: int,
                   etype: str,
                   key_props: Optional[Dict] = None,
                   confidence: float = 0.8,
                   weight: Optional[float] = None,
                   origin: str = "extractor",
                   extractor_version: str = "c1",
                   source: str = "rule") -> bool:
        """
        Idempotent edge upsert
        
        Args:
            project_id: Project identifier
            src_id: Source node ID
            dst_id: Destination node ID
            etype: Edge type (MENTIONS, REFERENCES, etc.)
            key_props: Identifying properties
            confidence: Confidence score
            weight: Edge weight
            origin: Origin of edge (extractor, adapter, user)
            extractor_version: Version of extractor
        
        Returns:
            True if edge was created, False if already exists
        """
        conn = self.get_connection()
        try:
            # Generate hash
            eh = edge_hash(src_id, dst_id, etype, key_props or {}, project_id)
            
            # Check if exists
            cur = conn.execute("SELECT id FROM edges WHERE edge_hash=?", (eh,))
            if cur.fetchone():
                return False
            
            # Insert new edge with source info
            conn.execute(
                """INSERT INTO edges(project_id, src_id, dst_id, type, props_json, 
                                   confidence, weight, origin, extractor_version, edge_hash, source)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (project_id, src_id, dst_id, etype, json.dumps(key_props or {}), 
                 confidence, weight, origin, extractor_version, eh, source)
            )
            conn.commit()
            
            logger.info(f"Created edge: {src_id} -{etype}-> {dst_id}")
            return True
            
        finally:
            conn.close()
    
    def create_document_node(self, 
                           capture_id: str,
                           project_id: str = "vader-lab") -> int:
        """
        Create document node from capture
        
        Args:
            capture_id: Capture ID to convert
            project_id: Project identifier
        
        Returns:
            Document node ID
        """
        conn = self.get_connection()
        try:
            # Get capture data
            cur = conn.execute(
                """SELECT c.*, cc.text, cc.summary 
                   FROM captures c
                   LEFT JOIN capture_content cc ON c.id = cc.capture_id
                   WHERE c.id = ?""",
                (capture_id,)
            )
            capture = cur.fetchone()
            
            if not capture:
                raise ValueError(f"Capture {capture_id} not found")
            
            # Check if document already exists for this capture
            cur = conn.execute(
                "SELECT id FROM document_nodes WHERE capture_id = ?",
                (capture_id,)
            )
            existing = cur.fetchone()
            if existing:
                return existing[0]
            
            # Insert document node
            cur = conn.execute(
                """INSERT INTO document_nodes(project_id, capture_id, title, url, content)
                   VALUES(?,?,?,?,?)""",
                (project_id, capture_id, 
                 capture['source_title'], 
                 capture['source_url'],
                 capture['text'] if capture else None)
            )
            conn.commit()
            
            doc_id = cur.lastrowid
            logger.info(f"Created document node {doc_id} for capture {capture_id}")
            return doc_id
            
        finally:
            conn.close()
    
    def merge_entities(self, 
                      from_id: int, 
                      to_id: int,
                      aliases: Optional[List[str]] = None) -> int:
        """
        Merge entities, moving all edges and creating aliases
        
        Args:
            from_id: Entity to merge from (will be deleted)
            to_id: Entity to merge into (will be kept)
            aliases: Additional aliases to record
        
        Returns:
            Number of edges moved
        """
        conn = self.get_connection()
        try:
            # Start transaction
            conn.execute("BEGIN")
            
            # Get the name of from_entity for alias
            cur = conn.execute(
                "SELECT name FROM entities WHERE id = ?",
                (from_id,)
            )
            from_entity = cur.fetchone()
            if from_entity:
                # Add as alias
                conn.execute(
                    """INSERT OR IGNORE INTO entity_aliases(entity_id, alias, source, confidence)
                       VALUES(?, ?, 'merge', 0.9)""",
                    (to_id, from_entity['name'])
                )
            
            # Add any additional aliases
            if aliases:
                for alias in aliases:
                    conn.execute(
                        """INSERT OR IGNORE INTO entity_aliases(entity_id, alias, source, confidence)
                           VALUES(?, ?, 'user', 0.95)""",
                        (to_id, alias)
                    )
            
            # Move edges where from_id is source
            cur = conn.execute(
                "UPDATE edges SET src_id = ? WHERE src_id = ?",
                (to_id, from_id)
            )
            edges_moved = cur.rowcount
            
            # Move edges where from_id is destination
            cur = conn.execute(
                "UPDATE edges SET dst_id = ? WHERE dst_id = ?",
                (to_id, from_id)
            )
            edges_moved += cur.rowcount
            
            # Delete the from entity
            conn.execute("DELETE FROM entities WHERE id = ?", (from_id,))
            
            # Commit transaction
            conn.commit()
            
            logger.info(f"Merged entity {from_id} into {to_id}, moved {edges_moved} edges")
            return edges_moved
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to merge entities: {e}")
            raise
        finally:
            conn.close()
    
    def find_similar_entities(self, 
                            project_id: str,
                            etype: Optional[str] = None,
                            threshold: float = 0.9) -> List[Tuple[int, int, str, str]]:
        """
        Find potentially duplicate entities based on normalized names
        
        Args:
            project_id: Project identifier
            etype: Filter by entity type
            threshold: Similarity threshold (not used in exact match)
        
        Returns:
            List of (id1, id2, name1, name2) tuples
        """
        conn = self.get_connection()
        try:
            query = """
                SELECT e1.id, e2.id, e1.name, e2.name
                FROM entities e1
                JOIN entities e2 ON e1.normalized_name = e2.normalized_name
                WHERE e1.project_id = ?
                  AND e2.project_id = ?
                  AND e1.id < e2.id
            """
            params = [project_id, project_id]
            
            if etype:
                query += " AND e1.type = ? AND e2.type = ?"
                params.extend([etype, etype])
            
            cur = conn.execute(query, params)
            duplicates = cur.fetchall()
            
            return [(row[0], row[1], row[2], row[3]) for row in duplicates]
            
        finally:
            conn.close()
    
    def run_integrity_check(self) -> Dict[str, Any]:
        """
        Run integrity checks and log issues
        
        Returns:
            Summary of integrity issues found
        """
        conn = self.get_connection()
        try:
            issues = {}
            
            # Check for orphan edges (source)
            cur = conn.execute("""
                SELECT COUNT(*) FROM edges e
                LEFT JOIN entities n ON e.src_id = n.id
                WHERE n.id IS NULL
            """)
            orphan_src = cur.fetchone()[0]
            if orphan_src > 0:
                issues['orphan_edges_src'] = orphan_src
            
            # Check for orphan edges (destination)
            cur = conn.execute("""
                SELECT COUNT(*) FROM edges e
                LEFT JOIN entities n ON e.dst_id = n.id
                WHERE n.id IS NULL
            """)
            orphan_dst = cur.fetchone()[0]
            if orphan_dst > 0:
                issues['orphan_edges_dst'] = orphan_dst
            
            # Check for duplicate entities
            cur = conn.execute("""
                SELECT COUNT(*) FROM (
                    SELECT normalized_name, type, project_id, COUNT(*) as cnt
                    FROM entities
                    WHERE normalized_name IS NOT NULL
                    GROUP BY normalized_name, type, project_id
                    HAVING cnt > 1
                )
            """)
            dup_entities = cur.fetchone()[0]
            if dup_entities > 0:
                issues['duplicate_entities'] = dup_entities
            
            # Log issues
            if issues:
                conn.execute(
                    "INSERT INTO graph_integrity_events(kind, details_json) VALUES(?, ?)",
                    ("integrity_check", json.dumps(issues))
                )
                conn.commit()
            
            logger.info(f"Integrity check completed: {issues}")
            return issues
            
        finally:
            conn.close()

# Singleton instance
_graph_ops = None

def get_graph_operations() -> GraphOperations:
    """Get or create the graph operations singleton"""
    global _graph_ops
    if _graph_ops is None:
        _graph_ops = GraphOperations()
    return _graph_ops