#!/usr/bin/env python3
"""
Memory Deduplicator - Find and merge duplicate/similar memories
Uses Sentence-Transformers embeddings to detect semantic similarity and consolidate memories
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
from pathlib import Path
from collections import defaultdict

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from memory_service import UniversalMemoryService
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN
import sqlite3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemoryDeduplicator:
    """
    Fastdup-inspired deduplication system for memories
    Finds duplicates, near-duplicates, and conflicting information using embeddings
    """
    
    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize the deduplicator
        
        Args:
            similarity_threshold: Cosine similarity threshold for considering memories as duplicates (0-1)
        """
        self.memory_service = UniversalMemoryService()
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.similarity_threshold = similarity_threshold
        
        # Different thresholds for different types of duplicates
        self.thresholds = {
            "exact_duplicate": 0.95,    # Nearly identical content
            "near_duplicate": 0.85,     # Very similar content
            "related": 0.70,            # Related but not duplicate
            "conflicting": 0.60         # Similar topic but potentially conflicting
        }
    
    def find_duplicates(self, project_filter: Optional[str] = None, batch_size: int = 100) -> Dict[str, Any]:
        """
        Find all types of duplicates in the memory system
        
        Args:
            project_filter: Optional project to limit search
            batch_size: Number of memories to process at once
            
        Returns:
            Complete duplicate analysis results
        """
        logger.info("🔍 Starting duplicate detection analysis...")
        start_time = datetime.now()
        
        try:
            # Get all memories
            memories = self._get_all_memories(project_filter)
            if len(memories) < 2:
                return {"error": "Need at least 2 memories for duplicate detection"}
            
            logger.info(f"Analyzing {len(memories)} memories for duplicates...")
            
            # Generate embeddings for all memories
            embeddings = self._generate_embeddings(memories, batch_size)
            
            # Find different types of duplicates
            results = {
                "analysis_timestamp": datetime.now().isoformat(),
                "total_memories": len(memories),
                "processing_time": 0,
                "duplicates": {
                    "exact_duplicates": [],
                    "near_duplicates": [],
                    "related_clusters": [],
                    "conflicting_pairs": []
                },
                "recommendations": {
                    "auto_merge": [],
                    "manual_review": [],
                    "conflicts_to_resolve": []
                },
                "statistics": {}
            }
            
            # Detect exact and near duplicates
            duplicate_pairs = self._find_duplicate_pairs(memories, embeddings)
            results["duplicates"]["exact_duplicates"] = duplicate_pairs["exact"]
            results["duplicates"]["near_duplicates"] = duplicate_pairs["near"]
            
            # Find related memory clusters
            clusters = self._find_memory_clusters(memories, embeddings)
            results["duplicates"]["related_clusters"] = clusters
            
            # Detect potentially conflicting information
            conflicts = self._find_conflicting_memories(memories, embeddings)
            results["duplicates"]["conflicting_pairs"] = conflicts
            
            # Generate recommendations
            recommendations = self._generate_recommendations(results["duplicates"])
            results["recommendations"] = recommendations
            
            # Calculate statistics
            stats = self._calculate_statistics(results)
            results["statistics"] = stats
            
            processing_time = (datetime.now() - start_time).total_seconds()
            results["processing_time"] = processing_time
            
            logger.info(f"✅ Duplicate analysis complete in {processing_time:.2f}s")
            logger.info(f"Found {len(duplicate_pairs['exact'])} exact duplicates, {len(duplicate_pairs['near'])} near duplicates")
            
            return results
            
        except Exception as e:
            logger.error(f"Duplicate detection error: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    def _get_all_memories(self, project_filter: Optional[str] = None) -> List[Dict]:
        """Get all memories for analysis"""
        try:
            with self.memory_service._get_connection() as conn:
                cursor = conn.cursor()
                
                if project_filter:
                    cursor.execute("""
                        SELECT id, content, project, category, tags, importance, 
                               timestamp, access_count, content_hash
                        FROM memories 
                        WHERE status = 'active' AND project = ?
                        ORDER BY timestamp DESC
                    """, (project_filter,))
                else:
                    cursor.execute("""
                        SELECT id, content, project, category, tags, importance, 
                               timestamp, access_count, content_hash
                        FROM memories 
                        WHERE status = 'active'
                        ORDER BY timestamp DESC
                    """)
                
                memories = []
                for row in cursor.fetchall():
                    memories.append({
                        "id": row["id"],
                        "content": row["content"],
                        "project": row["project"],
                        "category": row["category"],
                        "tags": json.loads(row["tags"]) if row["tags"] else [],
                        "importance": row["importance"],
                        "timestamp": row["timestamp"],
                        "access_count": row["access_count"],
                        "content_hash": row["content_hash"]
                    })
                
                return memories
                
        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")
            return []
    
    def _generate_embeddings(self, memories: List[Dict], batch_size: int = 100) -> np.ndarray:
        """Generate embeddings for all memories"""
        logger.info("Generating embeddings for similarity analysis...")
        
        contents = [mem["content"] for mem in memories]
        
        # Process in batches for memory efficiency
        all_embeddings = []
        for i in range(0, len(contents), batch_size):
            batch = contents[i:i + batch_size]
            batch_embeddings = self.embedder.encode(batch, convert_to_numpy=True)
            all_embeddings.append(batch_embeddings)
            
            if len(all_embeddings) % 5 == 0:  # Progress indicator
                logger.info(f"Processed {len(all_embeddings) * batch_size} embeddings...")
        
        return np.vstack(all_embeddings)
    
    def _find_duplicate_pairs(self, memories: List[Dict], embeddings: np.ndarray) -> Dict[str, List]:
        """Find exact and near duplicate pairs"""
        exact_duplicates = []
        near_duplicates = []
        
        # Calculate similarity matrix (upper triangle only to avoid duplicates)
        similarity_matrix = cosine_similarity(embeddings)
        
        for i in range(len(memories)):
            for j in range(i + 1, len(memories)):
                similarity = similarity_matrix[i][j]
                
                mem1 = memories[i]
                mem2 = memories[j]
                
                # Create duplicate pair info
                pair_info = {
                    "memory1": {
                        "id": mem1["id"],
                        "content_preview": mem1["content"][:200] + "..." if len(mem1["content"]) > 200 else mem1["content"],
                        "project": mem1["project"],
                        "importance": mem1["importance"],
                        "timestamp": mem1["timestamp"],
                        "access_count": mem1["access_count"]
                    },
                    "memory2": {
                        "id": mem2["id"],
                        "content_preview": mem2["content"][:200] + "..." if len(mem2["content"]) > 200 else mem2["content"],
                        "project": mem2["project"],
                        "importance": mem2["importance"],
                        "timestamp": mem2["timestamp"],
                        "access_count": mem2["access_count"]
                    },
                    "similarity_score": float(similarity),
                    "merge_recommendation": self._get_merge_recommendation(mem1, mem2, similarity)
                }
                
                if similarity >= self.thresholds["exact_duplicate"]:
                    exact_duplicates.append(pair_info)
                elif similarity >= self.thresholds["near_duplicate"]:
                    near_duplicates.append(pair_info)
        
        # Sort by similarity score (highest first)
        exact_duplicates.sort(key=lambda x: x["similarity_score"], reverse=True)
        near_duplicates.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return {
            "exact": exact_duplicates,
            "near": near_duplicates
        }
    
    def _find_memory_clusters(self, memories: List[Dict], embeddings: np.ndarray) -> List[Dict]:
        """Find clusters of related memories using DBSCAN"""
        try:
            # Use DBSCAN for clustering
            # eps: maximum distance between samples in a cluster
            # min_samples: minimum number of samples in a cluster
            clustering = DBSCAN(eps=0.3, min_samples=3, metric='cosine').fit(embeddings)
            
            clusters = defaultdict(list)
            for i, cluster_id in enumerate(clustering.labels_):
                if cluster_id != -1:  # -1 means noise/outlier
                    clusters[cluster_id].append(memories[i])
            
            # Convert to list format with cluster info
            cluster_list = []
            for cluster_id, cluster_memories in clusters.items():
                if len(cluster_memories) >= 3:  # Only include significant clusters
                    # Calculate cluster statistics
                    avg_importance = sum(m["importance"] for m in cluster_memories) / len(cluster_memories)
                    projects = list(set(m["project"] for m in cluster_memories))
                    categories = list(set(m["category"] for m in cluster_memories))
                    
                    # Get common tags
                    all_tags = []
                    for mem in cluster_memories:
                        all_tags.extend(mem["tags"])
                    tag_counts = defaultdict(int)
                    for tag in all_tags:
                        tag_counts[tag] += 1
                    common_tags = [tag for tag, count in tag_counts.items() if count >= len(cluster_memories) / 2]
                    
                    cluster_list.append({
                        "cluster_id": int(cluster_id),
                        "size": len(cluster_memories),
                        "memories": [
                            {
                                "id": mem["id"],
                                "content_preview": mem["content"][:150] + "..." if len(mem["content"]) > 150 else mem["content"],
                                "importance": mem["importance"]
                            }
                            for mem in cluster_memories
                        ],
                        "statistics": {
                            "avg_importance": avg_importance,
                            "projects": projects,
                            "categories": categories,
                            "common_tags": common_tags
                        },
                        "consolidation_opportunity": len(cluster_memories) >= 5  # Suggest consolidation for large clusters
                    })
            
            # Sort clusters by size (largest first)
            cluster_list.sort(key=lambda x: x["size"], reverse=True)
            return cluster_list
            
        except Exception as e:
            logger.warning(f"Clustering failed: {e}")
            return []
    
    def _find_conflicting_memories(self, memories: List[Dict], embeddings: np.ndarray) -> List[Dict]:
        """Find memories that might contain conflicting information"""
        conflicts = []
        
        # Look for memories that are similar in topic but might have conflicting info
        # This is a heuristic approach - look for similar embeddings but different conclusions
        
        similarity_matrix = cosine_similarity(embeddings)
        
        for i in range(len(memories)):
            for j in range(i + 1, len(memories)):
                similarity = similarity_matrix[i][j]
                
                # Look for memories that are related but might conflict
                if self.thresholds["conflicting"] <= similarity < self.thresholds["related"]:
                    mem1 = memories[i]
                    mem2 = memories[j]
                    
                    # Basic heuristics for detecting potential conflicts
                    conflict_indicators = self._detect_conflict_indicators(mem1["content"], mem2["content"])
                    
                    if conflict_indicators["potential_conflict"]:
                        conflicts.append({
                            "memory1": {
                                "id": mem1["id"],
                                "content_preview": mem1["content"][:200] + "...",
                                "project": mem1["project"],
                                "timestamp": mem1["timestamp"]
                            },
                            "memory2": {
                                "id": mem2["id"],
                                "content_preview": mem2["content"][:200] + "...",
                                "project": mem2["project"],
                                "timestamp": mem2["timestamp"]
                            },
                            "similarity_score": float(similarity),
                            "conflict_indicators": conflict_indicators,
                            "resolution_priority": "high" if abs(mem1["timestamp"] - mem2["timestamp"]) < 86400 else "medium"  # Same day = high priority
                        })
        
        # Sort by similarity score (most similar conflicts first)
        conflicts.sort(key=lambda x: x["similarity_score"], reverse=True)
        return conflicts[:20]  # Limit to top 20 potential conflicts
    
    def _detect_conflict_indicators(self, content1: str, content2: str) -> Dict[str, Any]:
        """Detect potential conflict indicators between two pieces of content"""
        indicators = {
            "potential_conflict": False,
            "reasons": []
        }
        
        content1_lower = content1.lower()
        content2_lower = content2.lower()
        
        # Look for contradictory statements
        conflict_patterns = [
            (["is not", "isn't", "doesn't work", "failed", "wrong"], ["is", "works", "successful", "correct"]),
            (["old", "outdated", "deprecated"], ["new", "latest", "current"]),
            (["slow", "poor performance"], ["fast", "good performance", "optimized"]),
            (["don't", "avoid", "not recommended"], ["do", "recommended", "should"])
        ]
        
        for negative_patterns, positive_patterns in conflict_patterns:
            has_negative_1 = any(pattern in content1_lower for pattern in negative_patterns)
            has_positive_1 = any(pattern in content1_lower for pattern in positive_patterns)
            has_negative_2 = any(pattern in content2_lower for pattern in negative_patterns)
            has_positive_2 = any(pattern in content2_lower for pattern in positive_patterns)
            
            if (has_negative_1 and has_positive_2) or (has_positive_1 and has_negative_2):
                indicators["potential_conflict"] = True
                indicators["reasons"].append("Contradictory statements detected")
                break
        
        # Check for version conflicts (e.g., different version numbers)
        import re
        version_pattern = r'\d+\.\d+\.?\d*'
        versions_1 = set(re.findall(version_pattern, content1))
        versions_2 = set(re.findall(version_pattern, content2))
        
        if versions_1 and versions_2 and versions_1 != versions_2:
            indicators["potential_conflict"] = True
            indicators["reasons"].append("Different versions mentioned")
        
        return indicators
    
    def _get_merge_recommendation(self, mem1: Dict, mem2: Dict, similarity: float) -> Dict[str, Any]:
        """Get recommendation for merging two similar memories"""
        recommendation = {
            "action": "manual_review",
            "confidence": similarity,
            "preferred_memory": None,
            "reasons": []
        }
        
        # Auto-merge recommendation for very high similarity
        if similarity >= 0.95:
            recommendation["action"] = "auto_merge"
            recommendation["reasons"].append("Very high similarity (>95%)")
            
            # Choose preferred memory based on various factors
            if mem1["importance"] > mem2["importance"]:
                recommendation["preferred_memory"] = mem1["id"]
                recommendation["reasons"].append("Higher importance score")
            elif mem2["importance"] > mem1["importance"]:
                recommendation["preferred_memory"] = mem2["id"]
                recommendation["reasons"].append("Higher importance score")
            elif mem1["access_count"] > mem2["access_count"]:
                recommendation["preferred_memory"] = mem1["id"]
                recommendation["reasons"].append("More frequently accessed")
            elif mem2["access_count"] > mem1["access_count"]:
                recommendation["preferred_memory"] = mem2["id"]
                recommendation["reasons"].append("More frequently accessed")
            elif mem1["timestamp"] > mem2["timestamp"]:
                recommendation["preferred_memory"] = mem1["id"]
                recommendation["reasons"].append("More recent")
            else:
                recommendation["preferred_memory"] = mem2["id"]
                recommendation["reasons"].append("More recent")
        
        return recommendation
    
    def _generate_recommendations(self, duplicates: Dict) -> Dict[str, List]:
        """Generate actionable recommendations based on duplicate analysis"""
        recommendations = {
            "auto_merge": [],
            "manual_review": [],
            "conflicts_to_resolve": []
        }
        
        # Process exact duplicates for auto-merge
        for duplicate in duplicates["exact_duplicates"]:
            if duplicate["merge_recommendation"]["action"] == "auto_merge":
                recommendations["auto_merge"].append({
                    "type": "exact_duplicate",
                    "primary_memory": duplicate["merge_recommendation"]["preferred_memory"],
                    "duplicate_memory": duplicate["memory2"]["id"] if duplicate["merge_recommendation"]["preferred_memory"] == duplicate["memory1"]["id"] else duplicate["memory1"]["id"],
                    "similarity": duplicate["similarity_score"],
                    "reason": "Exact duplicate with high confidence"
                })
        
        # Process near duplicates for manual review
        for duplicate in duplicates["near_duplicates"]:
            recommendations["manual_review"].append({
                "type": "near_duplicate",
                "memory1": duplicate["memory1"]["id"],
                "memory2": duplicate["memory2"]["id"],
                "similarity": duplicate["similarity_score"],
                "reason": "Similar content requiring human judgment"
            })
        
        # Process conflicts
        for conflict in duplicates["conflicting_pairs"]:
            recommendations["conflicts_to_resolve"].append({
                "type": "potential_conflict",
                "memory1": conflict["memory1"]["id"],
                "memory2": conflict["memory2"]["id"],
                "similarity": conflict["similarity_score"],
                "conflict_reasons": conflict["conflict_indicators"]["reasons"],
                "priority": conflict["resolution_priority"]
            })
        
        return recommendations
    
    def _calculate_statistics(self, duplicates: Dict) -> Dict[str, Any]:
        """Calculate useful statistics from the duplicate analysis"""
        stats = {
            "duplicate_rate": 0,
            "potential_space_savings": 0,
            "cluster_distribution": {},
            "conflict_rate": 0
        }
        
        total_memories = duplicates.get("total_memories", 0) if isinstance(duplicates, dict) else 0
        if total_memories > 0:
            total_duplicates = len(duplicates["exact_duplicates"]) + len(duplicates["near_duplicates"])
            stats["duplicate_rate"] = total_duplicates / total_memories
            
            # Estimate space savings (approximate)
            stats["potential_space_savings"] = len(duplicates["exact_duplicates"])
            
            # Cluster size distribution
            cluster_sizes = [cluster["size"] for cluster in duplicates["related_clusters"]]
            if cluster_sizes:
                stats["cluster_distribution"] = {
                    "avg_cluster_size": sum(cluster_sizes) / len(cluster_sizes),
                    "largest_cluster": max(cluster_sizes),
                    "total_clusters": len(cluster_sizes)
                }
            
            stats["conflict_rate"] = len(duplicates["conflicting_pairs"]) / total_memories
        
        return stats
    
    def execute_auto_merge(self, recommendations: List[Dict]) -> Dict[str, Any]:
        """Execute automatic merge recommendations (with caution)"""
        logger.warning("Auto-merge is a destructive operation. Use with caution!")
        
        results = {
            "merged": [],
            "failed": [],
            "timestamp": datetime.now().isoformat()
        }
        
        for rec in recommendations:
            if rec["type"] == "exact_duplicate":
                try:
                    # Mark the duplicate as merged (soft delete)
                    success = self._merge_memories(rec["primary_memory"], rec["duplicate_memory"])
                    if success:
                        results["merged"].append(rec)
                    else:
                        results["failed"].append({**rec, "error": "Merge operation failed"})
                        
                except Exception as e:
                    results["failed"].append({**rec, "error": str(e)})
        
        logger.info(f"Auto-merge complete: {len(results['merged'])} merged, {len(results['failed'])} failed")
        return results
    
    def _merge_memories(self, primary_id: str, duplicate_id: str) -> bool:
        """Merge two memories (keep primary, mark duplicate as merged)"""
        try:
            with self.memory_service._get_connection() as conn:
                cursor = conn.cursor()
                
                # Update the duplicate memory status
                cursor.execute("""
                    UPDATE memories 
                    SET status = 'merged', 
                        metadata = json_set(COALESCE(metadata, '{}'), '$.merged_into', ?)
                    WHERE id = ?
                """, (primary_id, duplicate_id))
                
                # Optionally update the primary memory to note the merge
                cursor.execute("""
                    UPDATE memories 
                    SET metadata = json_set(COALESCE(metadata, '{}'), '$.merged_from', 
                                           json_insert(COALESCE(json_extract(metadata, '$.merged_from'), '[]'), '$[#]', ?))
                    WHERE id = ?
                """, (duplicate_id, primary_id))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Memory merge failed: {e}")
            return False


async def test_deduplicator():
    """Test the memory deduplication system"""
    
    print("🔍 Initializing Memory Deduplicator...")
    deduplicator = MemoryDeduplicator(similarity_threshold=0.85)
    
    print("\n" + "="*60)
    print("🧹 MEMORY DEDUPLICATION ANALYSIS")
    print("="*60)
    
    # Run duplicate analysis
    print("Analyzing memories for duplicates...")
    results = deduplicator.find_duplicates()
    
    if "error" in results:
        print(f"❌ Error: {results['error']}")
        return
    
    # Display results
    stats = results["statistics"]
    duplicates = results["duplicates"]
    recommendations = results["recommendations"]
    
    print(f"\n📊 Analysis Results:")
    print(f"   Total memories analyzed: {results['total_memories']}")
    print(f"   Processing time: {results['processing_time']:.2f}s")
    print(f"   Duplicate rate: {stats.get('duplicate_rate', 0):.1%}")
    
    print(f"\n🔍 Duplicates Found:")
    print(f"   Exact duplicates: {len(duplicates['exact_duplicates'])}")
    print(f"   Near duplicates: {len(duplicates['near_duplicates'])}")
    print(f"   Related clusters: {len(duplicates['related_clusters'])}")
    print(f"   Potential conflicts: {len(duplicates['conflicting_pairs'])}")
    
    # Show some examples
    if duplicates["exact_duplicates"]:
        print(f"\n📋 Example Exact Duplicate:")
        dup = duplicates["exact_duplicates"][0]
        print(f"   Similarity: {dup['similarity_score']:.3f}")
        print(f"   Memory 1: {dup['memory1']['content_preview'][:100]}...")
        print(f"   Memory 2: {dup['memory2']['content_preview'][:100]}...")
    
    if duplicates["related_clusters"]:
        print(f"\n🗂️  Largest Related Cluster:")
        cluster = duplicates["related_clusters"][0]
        print(f"   Size: {cluster['size']} memories")
        print(f"   Common tags: {', '.join(cluster['statistics']['common_tags'][:3])}")
    
    print(f"\n💡 Recommendations:")
    print(f"   Auto-merge candidates: {len(recommendations['auto_merge'])}")
    print(f"   Manual review needed: {len(recommendations['manual_review'])}")
    print(f"   Conflicts to resolve: {len(recommendations['conflicts_to_resolve'])}")
    
    print("\n" + "="*60)
    print("✅ Deduplication analysis complete!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_deduplicator())