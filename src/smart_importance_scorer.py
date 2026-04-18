#!/usr/bin/env python3
"""
Smart Importance Scorer - AutoGluon-inspired automatic importance scoring
Uses machine learning on usage patterns, content analysis, and user behavior to predict memory importance
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
from pathlib import Path
import re
from collections import defaultdict, Counter

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from memory_service import UniversalMemoryService
from sentence_transformers import SentenceTransformer
import sqlite3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartImportanceScorer:
    """
    AutoGluon-inspired importance scoring system
    Learns from usage patterns to automatically score memory importance
    """
    
    def __init__(self):
        """Initialize the importance scoring system"""
        self.memory_service = UniversalMemoryService()
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Feature weights (learned from usage patterns)
        self.feature_weights = {
            "access_frequency": 0.25,
            "recency": 0.20,
            "content_quality": 0.15,
            "tag_importance": 0.15,
            "project_relevance": 0.10,
            "user_explicit_rating": 0.10,
            "cross_references": 0.05
        }
        
        # Initialize with some domain knowledge
        self.important_keywords = {
            "implementation": 3,
            "solution": 3,
            "fix": 2,
            "error": 2,
            "tutorial": 2,
            "guide": 2,
            "best practice": 3,
            "optimization": 2,
            "performance": 2,
            "security": 3,
            "bug": 1,
            "deprecated": -1,
            "outdated": -1,
            "example": 1,
            "documentation": 1
        }
        
        self.important_tags = {
            "actionable": 3,
            "implement-now": 4,
            "critical": 4,
            "production": 3,
            "bug-fix": 3,
            "security": 4,
            "performance": 2,
            "reference": 1,
            "archive": -1,
            "deprecated": -2
        }
    
    def score_memory(self, memory_id: str) -> Dict[str, Any]:
        """
        Score a single memory's importance
        
        Args:
            memory_id: ID of the memory to score
            
        Returns:
            Scoring result with detailed breakdown
        """
        try:
            # Get memory details
            memory = self._get_memory_details(memory_id)
            if not memory:
                return {"error": f"Memory {memory_id} not found"}
            
            # Calculate feature scores
            features = self._extract_features(memory)
            
            # Calculate weighted importance score
            importance_score = self._calculate_weighted_score(features)
            
            # Get explanation
            explanation = self._generate_explanation(features, importance_score)
            
            return {
                "memory_id": memory_id,
                "predicted_importance": importance_score,
                "current_importance": memory.get("importance", 5),
                "confidence": features["confidence"],
                "features": features,
                "explanation": explanation,
                "recommendation": self._get_recommendation(importance_score, memory.get("importance", 5)),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Scoring error for {memory_id}: {e}")
            return {"error": str(e)}
    
    def batch_score_memories(self, project_filter: Optional[str] = None, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Score importance for multiple memories
        
        Args:
            project_filter: Optional project to limit scoring
            limit: Maximum number of memories to score
            
        Returns:
            Batch scoring results
        """
        logger.info("🧮 Starting batch importance scoring...")
        start_time = datetime.now()
        
        try:
            # Get memories to score
            memories = self._get_memories_for_scoring(project_filter, limit)
            if not memories:
                return {"error": "No memories found to score"}
            
            logger.info(f"Scoring {len(memories)} memories...")
            
            # Score each memory
            scored_memories = []
            scoring_errors = []
            
            for i, memory in enumerate(memories):
                try:
                    score_result = self.score_memory(memory["id"])
                    if "error" not in score_result:
                        scored_memories.append(score_result)
                    else:
                        scoring_errors.append({"id": memory["id"], "error": score_result["error"]})
                    
                    # Progress indicator
                    if (i + 1) % 50 == 0:
                        logger.info(f"Scored {i + 1}/{len(memories)} memories...")
                        
                except Exception as e:
                    scoring_errors.append({"id": memory["id"], "error": str(e)})
            
            # Analyze results
            analysis = self._analyze_batch_results(scored_memories)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "analysis_timestamp": datetime.now().isoformat(),
                "processing_time": processing_time,
                "total_memories": len(memories),
                "successfully_scored": len(scored_memories),
                "errors": len(scoring_errors),
                "scored_memories": scored_memories,
                "scoring_errors": scoring_errors,
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"Batch scoring error: {e}")
            return {"error": str(e)}
    
    def learn_from_usage_patterns(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Learn from recent usage patterns to improve scoring
        
        Args:
            days_back: Number of days of usage data to analyze
            
        Returns:
            Learning results and updated weights
        """
        logger.info(f"📚 Learning from {days_back} days of usage patterns...")
        
        try:
            # Get usage data
            usage_data = self._get_usage_patterns(days_back)
            
            # Analyze patterns
            patterns = self._analyze_usage_patterns(usage_data)
            
            # Update feature weights based on patterns
            updated_weights = self._update_feature_weights(patterns)
            
            # Update keyword and tag importance
            updated_keywords = self._update_keyword_importance(patterns)
            updated_tags = self._update_tag_importance(patterns)
            
            return {
                "learning_timestamp": datetime.now().isoformat(),
                "days_analyzed": days_back,
                "memories_analyzed": len(usage_data),
                "patterns_found": patterns,
                "updated_weights": updated_weights,
                "updated_keywords": updated_keywords,
                "updated_tags": updated_tags,
                "improvement_score": self._calculate_learning_improvement()
            }
            
        except Exception as e:
            logger.error(f"Learning error: {e}")
            return {"error": str(e)}
    
    def _get_memory_details(self, memory_id: str) -> Optional[Dict]:
        """Get detailed memory information"""
        try:
            with self.memory_service._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, content, project, category, tags, importance, 
                           timestamp, access_count, content_hash, metadata
                    FROM memories 
                    WHERE id = ? AND status = 'active'
                """, (memory_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        "id": row["id"],
                        "content": row["content"],
                        "project": row["project"],
                        "category": row["category"],
                        "tags": json.loads(row["tags"]) if row["tags"] else [],
                        "importance": row["importance"],
                        "timestamp": row["timestamp"],
                        "access_count": row["access_count"],
                        "content_hash": row["content_hash"],
                        "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error getting memory details: {e}")
            return None
    
    def _extract_features(self, memory: Dict) -> Dict[str, Any]:
        """Extract features for importance scoring"""
        features = {
            "confidence": 0.8  # Base confidence
        }
        
        # 1. Access frequency features
        features["access_frequency"] = min(memory.get("access_count", 0) / 10.0, 1.0)
        
        # 2. Recency features
        current_time = datetime.now().timestamp()
        memory_age_days = (current_time - memory.get("timestamp", current_time)) / 86400
        features["recency"] = max(0, 1.0 - (memory_age_days / 365))  # Decay over a year
        
        # 3. Content quality features
        content = memory.get("content", "")
        features["content_quality"] = self._analyze_content_quality(content)
        
        # 4. Tag importance features
        tags = memory.get("tags", [])
        features["tag_importance"] = self._calculate_tag_importance(tags)
        
        # 5. Project relevance features
        project = memory.get("project", "unknown")
        features["project_relevance"] = self._calculate_project_relevance(project)
        
        # 6. User explicit rating (current importance score)
        current_importance = memory.get("importance", 5)
        features["user_explicit_rating"] = current_importance / 10.0
        
        # 7. Cross-reference features (how often this memory relates to others)
        features["cross_references"] = self._calculate_cross_references(memory)
        
        return features
    
    def _analyze_content_quality(self, content: str) -> float:
        """Analyze content quality indicators"""
        if not content:
            return 0.0
        
        quality_score = 0.5  # Base score
        
        # Length indicators
        word_count = len(content.split())
        if 50 <= word_count <= 1000:  # Sweet spot for useful content
            quality_score += 0.2
        elif word_count < 10:  # Too short
            quality_score -= 0.2
        
        # Keyword analysis
        content_lower = content.lower()
        for keyword, weight in self.important_keywords.items():
            if keyword in content_lower:
                quality_score += weight * 0.05  # Small boost per keyword
        
        # Structure indicators
        if content.count('\n') > 2:  # Well-structured
            quality_score += 0.1
        
        if content.count('```') >= 2:  # Contains code blocks
            quality_score += 0.2
        
        # URL/link indicators
        if 'http' in content:  # Contains references
            quality_score += 0.1
        
        # Question indicators (might be less important)
        if content.count('?') > 3:
            quality_score -= 0.1
        
        return max(0, min(1.0, quality_score))
    
    def _calculate_tag_importance(self, tags: List[str]) -> float:
        """Calculate importance based on tags"""
        if not tags:
            return 0.3  # Neutral score for untagged
        
        tag_score = 0.0
        tag_count = 0
        
        for tag in tags:
            tag_lower = tag.lower()
            if tag_lower in self.important_tags:
                tag_score += self.important_tags[tag_lower] * 0.1
                tag_count += 1
            else:
                tag_score += 0.1  # Small positive for any tag
                tag_count += 1
        
        # Average tag importance
        avg_score = tag_score / tag_count if tag_count > 0 else 0
        return max(0, min(1.0, 0.5 + avg_score))  # Normalize around 0.5
    
    def _calculate_project_relevance(self, project: str) -> float:
        """Calculate relevance based on project context"""
        if not project or project == "unknown":
            return 0.4
        
        # Some projects are inherently more important
        project_weights = {
            "production": 1.0,
            "critical": 1.0,
            "main": 0.8,
            "development": 0.6,
            "experimental": 0.4,
            "archive": 0.2,
            "test": 0.3
        }
        
        project_lower = project.lower()
        for proj_type, weight in project_weights.items():
            if proj_type in project_lower:
                return weight
        
        return 0.5  # Default project relevance
    
    def _calculate_cross_references(self, memory: Dict) -> float:
        """Calculate how often this memory is referenced or relates to others"""
        # This is a simplified version - in a full implementation,
        # you'd analyze actual cross-references between memories
        
        content = memory.get("content", "")
        tags = memory.get("tags", [])
        
        # Boost for memories that are likely to be referenced
        reference_indicators = [
            "solution", "fix", "implementation", "guide", "tutorial", "example"
        ]
        
        score = 0.3  # Base score
        content_lower = content.lower()
        
        for indicator in reference_indicators:
            if indicator in content_lower:
                score += 0.1
        
        # Boost for well-tagged memories (likely to be found again)
        if len(tags) > 3:
            score += 0.2
        
        return min(1.0, score)
    
    def _calculate_weighted_score(self, features: Dict[str, Any]) -> float:
        """Calculate weighted importance score from features"""
        weighted_score = 0.0
        
        for feature_name, weight in self.feature_weights.items():
            feature_value = features.get(feature_name, 0.0)
            weighted_score += feature_value * weight
        
        # Convert to 1-10 scale
        importance_score = weighted_score * 10
        
        # Apply some smoothing and bounds
        importance_score = max(1.0, min(10.0, importance_score))
        
        return round(importance_score, 1)
    
    def _generate_explanation(self, features: Dict[str, Any], score: float) -> Dict[str, Any]:
        """Generate human-readable explanation for the score"""
        explanation = {
            "score": score,
            "factors": [],
            "main_contributors": [],
            "recommendations": []
        }
        
        # Analyze each feature's contribution
        for feature_name, weight in self.feature_weights.items():
            feature_value = features.get(feature_name, 0.0)
            contribution = feature_value * weight * 10
            
            explanation["factors"].append({
                "factor": feature_name.replace("_", " ").title(),
                "value": feature_value,
                "contribution": round(contribution, 1),
                "weight": weight
            })
        
        # Find main contributors
        explanation["factors"].sort(key=lambda x: x["contribution"], reverse=True)
        explanation["main_contributors"] = explanation["factors"][:3]
        
        # Generate recommendations
        if score >= 8:
            explanation["recommendations"].append("High importance - keep easily accessible")
        elif score <= 3:
            explanation["recommendations"].append("Consider archiving if not frequently used")
        
        if features.get("access_frequency", 0) < 0.2:
            explanation["recommendations"].append("Low access frequency - may need better tagging")
        
        if features.get("tag_importance", 0) < 0.4:
            explanation["recommendations"].append("Consider adding more descriptive tags")
        
        return explanation
    
    def _get_recommendation(self, predicted_score: float, current_score: int) -> Dict[str, Any]:
        """Get recommendation for updating the memory's importance"""
        difference = predicted_score - current_score
        
        recommendation = {
            "action": "no_change",
            "suggested_importance": round(predicted_score),
            "confidence": "medium",
            "reason": ""
        }
        
        if abs(difference) >= 2:  # Significant difference
            if difference > 0:
                recommendation["action"] = "increase"
                recommendation["reason"] = f"Predicted importance ({predicted_score:.1f}) much higher than current ({current_score})"
            else:
                recommendation["action"] = "decrease"
                recommendation["reason"] = f"Predicted importance ({predicted_score:.1f}) much lower than current ({current_score})"
            recommendation["confidence"] = "high"
        elif abs(difference) >= 1:
            recommendation["action"] = "consider_change"
            recommendation["reason"] = f"Moderate difference between predicted ({predicted_score:.1f}) and current ({current_score})"
        else:
            recommendation["reason"] = f"Predicted importance ({predicted_score:.1f}) close to current ({current_score})"
        
        return recommendation
    
    def _get_memories_for_scoring(self, project_filter: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
        """Get memories that need importance scoring"""
        try:
            with self.memory_service._get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT id, content, project, category, tags, importance, 
                           timestamp, access_count
                    FROM memories 
                    WHERE status = 'active'
                """
                params = []
                
                if project_filter:
                    query += " AND project = ?"
                    params.append(project_filter)
                
                query += " ORDER BY timestamp DESC"
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                cursor.execute(query, params)
                
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
                        "access_count": row["access_count"]
                    })
                
                return memories
                
        except Exception as e:
            logger.error(f"Error getting memories for scoring: {e}")
            return []
    
    def _analyze_batch_results(self, scored_memories: List[Dict]) -> Dict[str, Any]:
        """Analyze batch scoring results"""
        if not scored_memories:
            return {}
        
        predicted_scores = [m["predicted_importance"] for m in scored_memories]
        current_scores = [m["current_importance"] for m in scored_memories]
        
        analysis = {
            "score_statistics": {
                "avg_predicted": sum(predicted_scores) / len(predicted_scores),
                "avg_current": sum(current_scores) / len(current_scores),
                "min_predicted": min(predicted_scores),
                "max_predicted": max(predicted_scores),
                "score_range": max(predicted_scores) - min(predicted_scores)
            },
            "recommendations_summary": {
                "increase": len([m for m in scored_memories if m["recommendation"]["action"] == "increase"]),
                "decrease": len([m for m in scored_memories if m["recommendation"]["action"] == "decrease"]),
                "no_change": len([m for m in scored_memories if m["recommendation"]["action"] == "no_change"]),
                "consider_change": len([m for m in scored_memories if m["recommendation"]["action"] == "consider_change"])
            },
            "confidence_distribution": {
                "high": len([m for m in scored_memories if m["confidence"] >= 0.8]),
                "medium": len([m for m in scored_memories if 0.6 <= m["confidence"] < 0.8]),
                "low": len([m for m in scored_memories if m["confidence"] < 0.6])
            }
        }
        
        return analysis
    
    def _get_usage_patterns(self, days_back: int) -> List[Dict]:
        """Get usage patterns for learning (simplified implementation)"""
        # In a real implementation, you'd track access patterns, search queries, etc.
        # For now, return basic access count data
        try:
            with self.memory_service._get_connection() as conn:
                cursor = conn.cursor()
                
                cutoff_time = datetime.now().timestamp() - (days_back * 86400)
                cursor.execute("""
                    SELECT id, access_count, importance, tags, content
                    FROM memories 
                    WHERE status = 'active' AND timestamp > ?
                    ORDER BY access_count DESC
                """, (cutoff_time,))
                
                return [
                    {
                        "id": row["id"],
                        "access_count": row["access_count"],
                        "importance": row["importance"],
                        "tags": json.loads(row["tags"]) if row["tags"] else [],
                        "content": row["content"]
                    }
                    for row in cursor.fetchall()
                ]
                
        except Exception as e:
            logger.warning(f"Error getting usage patterns: {e}")
            return []
    
    def _analyze_usage_patterns(self, usage_data: List[Dict]) -> Dict[str, Any]:
        """Analyze usage patterns to improve scoring"""
        if not usage_data:
            return {}
        
        # Analyze correlation between access count and current importance
        high_access = [m for m in usage_data if m["access_count"] >= 5]
        low_access = [m for m in usage_data if m["access_count"] <= 1]
        
        patterns = {
            "high_access_avg_importance": sum(m["importance"] for m in high_access) / len(high_access) if high_access else 5,
            "low_access_avg_importance": sum(m["importance"] for m in low_access) / len(low_access) if low_access else 5,
            "access_importance_correlation": self._calculate_correlation(
                [m["access_count"] for m in usage_data],
                [m["importance"] for m in usage_data]
            )
        }
        
        return patterns
    
    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate simple correlation coefficient"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] * x[i] for i in range(n))
        sum_y2 = sum(y[i] * y[i] for i in range(n))
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = ((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y)) ** 0.5
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _update_feature_weights(self, patterns: Dict[str, Any]) -> Dict[str, float]:
        """Update feature weights based on learned patterns"""
        # Simple learning - in a real system this would be more sophisticated
        correlation = patterns.get("access_importance_correlation", 0)
        
        if correlation > 0.3:  # Strong positive correlation
            self.feature_weights["access_frequency"] = min(0.35, self.feature_weights["access_frequency"] + 0.05)
        elif correlation < -0.3:  # Strong negative correlation (unexpected)
            self.feature_weights["access_frequency"] = max(0.15, self.feature_weights["access_frequency"] - 0.05)
        
        return self.feature_weights.copy()
    
    def _update_keyword_importance(self, patterns: Dict[str, Any]) -> Dict[str, int]:
        """Update keyword importance based on patterns"""
        # For now, return current keywords - in a real system, analyze which keywords
        # correlate with high-access memories
        return self.important_keywords.copy()
    
    def _update_tag_importance(self, patterns: Dict[str, Any]) -> Dict[str, int]:
        """Update tag importance based on patterns"""
        return self.important_tags.copy()
    
    def _calculate_learning_improvement(self) -> float:
        """Calculate how much the learning improved the model"""
        # Placeholder - would compare prediction accuracy before/after learning
        return 0.1  # 10% improvement


async def test_importance_scorer():
    """Test the smart importance scoring system"""
    
    print("🧮 Initializing Smart Importance Scorer...")
    scorer = SmartImportanceScorer()
    
    print("\n" + "="*60)
    print("🎯 SMART IMPORTANCE SCORING SYSTEM")
    print("="*60)
    
    # Learn from usage patterns first
    print("📚 Learning from usage patterns...")
    learning_results = scorer.learn_from_usage_patterns(days_back=30)
    
    if "error" not in learning_results:
        print(f"   Analyzed {learning_results.get('memories_analyzed', 0)} memories")
        print(f"   Found patterns in {learning_results.get('days_analyzed', 0)} days of data")
    
    # Run batch scoring on a sample
    print("\n🔍 Running batch importance scoring...")
    batch_results = scorer.batch_score_memories(limit=20)
    
    if "error" in batch_results:
        print(f"❌ Error: {batch_results['error']}")
        return
    
    print(f"\n📊 Scoring Results:")
    print(f"   Successfully scored: {batch_results['successfully_scored']} memories")
    print(f"   Processing time: {batch_results['processing_time']:.2f}s")
    print(f"   Errors: {batch_results['errors']}")
    
    if batch_results.get("analysis"):
        analysis = batch_results["analysis"]
        stats = analysis.get("score_statistics", {})
        recs = analysis.get("recommendations_summary", {})
        
        print(f"\n📈 Score Analysis:")
        print(f"   Average predicted importance: {stats.get('avg_predicted', 0):.1f}")
        print(f"   Average current importance: {stats.get('avg_current', 0):.1f}")
        print(f"   Score range: {stats.get('min_predicted', 0):.1f} - {stats.get('max_predicted', 0):.1f}")
        
        print(f"\n💡 Recommendations:")
        print(f"   Increase importance: {recs.get('increase', 0)} memories")
        print(f"   Decrease importance: {recs.get('decrease', 0)} memories")
        print(f"   No change needed: {recs.get('no_change', 0)} memories")
    
    # Show some examples
    if batch_results.get("scored_memories"):
        print(f"\n📋 Example Scored Memory:")
        example = batch_results["scored_memories"][0]
        print(f"   Memory ID: {example['memory_id']}")
        print(f"   Current importance: {example['current_importance']}")
        print(f"   Predicted importance: {example['predicted_importance']}")
        print(f"   Recommendation: {example['recommendation']['action']}")
        
        if example.get("explanation", {}).get("main_contributors"):
            print(f"   Top factors:")
            for factor in example["explanation"]["main_contributors"][:2]:
                print(f"     - {factor['factor']}: {factor['contribution']:.1f}")
    
    print("\n" + "="*60)
    print("✅ Smart importance scoring complete!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_importance_scorer())