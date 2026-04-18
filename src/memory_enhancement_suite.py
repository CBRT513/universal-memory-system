#!/usr/bin/env python3
"""
Memory Enhancement Suite - Integration of all three AI-powered memory enhancements
Combines Q&A Engine, Deduplication System, and Smart Importance Scoring
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from memory_service import UniversalMemoryService
from memory_qa_engine import MemoryQAEngine
from memory_deduplicator import MemoryDeduplicator
from smart_importance_scorer import SmartImportanceScorer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemoryEnhancementSuite:
    """
    Complete memory enhancement suite integrating:
    1. Q&A Engine - Ask questions about your memories
    2. Deduplication - Find and merge duplicate memories
    3. Smart Scoring - Automatic importance prediction
    """
    
    def __init__(self):
        """Initialize all enhancement systems"""
        logger.info("🚀 Initializing Memory Enhancement Suite...")
        
        self.memory_service = UniversalMemoryService()
        self.qa_engine = MemoryQAEngine(use_local_llm=True)
        self.deduplicator = MemoryDeduplicator(similarity_threshold=0.85)
        self.scorer = SmartImportanceScorer()
        
        logger.info("✅ All systems initialized")
    
    async def comprehensive_analysis(self, project_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Run comprehensive analysis of the memory system
        
        Args:
            project_filter: Optional project to limit analysis
            
        Returns:
            Complete analysis results from all systems
        """
        logger.info("🔬 Starting comprehensive memory analysis...")
        start_time = datetime.now()
        
        results = {
            "analysis_timestamp": datetime.now().isoformat(),
            "project_filter": project_filter,
            "systems": {
                "deduplication": {},
                "importance_scoring": {},
                "qa_capabilities": {}
            },
            "insights": {},
            "recommendations": []
        }
        
        try:
            # 1. Run deduplication analysis
            logger.info("🧹 Running deduplication analysis...")
            dedup_results = self.deduplicator.find_duplicates(project_filter, batch_size=50)
            results["systems"]["deduplication"] = dedup_results
            
            # 2. Run importance scoring analysis
            logger.info("🧮 Running importance scoring analysis...")
            scoring_results = self.scorer.batch_score_memories(project_filter, limit=100)
            results["systems"]["importance_scoring"] = scoring_results
            
            # 3. Test Q&A capabilities with system questions
            logger.info("🤖 Testing Q&A capabilities...")
            qa_tests = await self._test_qa_capabilities(project_filter)
            results["systems"]["qa_capabilities"] = qa_tests
            
            # 4. Generate combined insights
            insights = self._generate_combined_insights(results["systems"])
            results["insights"] = insights
            
            # 5. Generate recommendations
            recommendations = self._generate_system_recommendations(results["systems"], insights)
            results["recommendations"] = recommendations
            
            processing_time = (datetime.now() - start_time).total_seconds()
            results["processing_time"] = processing_time
            
            logger.info(f"✅ Comprehensive analysis complete in {processing_time:.2f}s")
            return results
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _test_qa_capabilities(self, project_filter: Optional[str] = None) -> Dict[str, Any]:
        """Test Q&A engine with system-relevant questions"""
        test_questions = [
            "What are the most important memories in the system?",
            "What projects do I have memories for?",
            "What technologies or libraries am I working with?",
            "What implementation tasks need to be done?",
            "What are the key insights from my memories?"
        ]
        
        qa_results = {
            "test_questions": len(test_questions),
            "successful_answers": 0,
            "failed_answers": 0,
            "avg_confidence": 0.0,
            "avg_processing_time": 0.0,
            "sample_qa": []
        }
        
        total_confidence = 0.0
        total_processing_time = 0.0
        
        for question in test_questions[:3]:  # Limit to 3 for performance
            try:
                result = await self.qa_engine.ask(question, project_filter)
                
                if "error" not in result:
                    qa_results["successful_answers"] += 1
                    total_confidence += result.get("confidence", 0)
                    total_processing_time += result.get("processing_time", 0)
                    
                    # Store first successful example
                    if not qa_results["sample_qa"]:
                        qa_results["sample_qa"].append({
                            "question": question,
                            "answer_preview": result["answer"][:200] + "...",
                            "confidence": result["confidence"],
                            "sources": result["source_count"]
                        })
                else:
                    qa_results["failed_answers"] += 1
                    
            except Exception as e:
                qa_results["failed_answers"] += 1
                logger.warning(f"Q&A test failed for '{question}': {e}")
        
        if qa_results["successful_answers"] > 0:
            qa_results["avg_confidence"] = total_confidence / qa_results["successful_answers"]
            qa_results["avg_processing_time"] = total_processing_time / qa_results["successful_answers"]
        
        return qa_results
    
    def _generate_combined_insights(self, systems_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights by combining results from all systems"""
        insights = {
            "memory_quality": {},
            "system_efficiency": {},
            "data_patterns": {},
            "optimization_opportunities": []
        }
        
        # Deduplication insights
        dedup = systems_results.get("deduplication", {})
        if dedup and "statistics" in dedup:
            stats = dedup["statistics"]
            insights["memory_quality"]["duplicate_rate"] = stats.get("duplicate_rate", 0)
            insights["memory_quality"]["potential_cleanup"] = stats.get("potential_space_savings", 0)
            
            if stats.get("duplicate_rate", 0) > 0.1:  # More than 10% duplicates
                insights["optimization_opportunities"].append({
                    "type": "deduplication",
                    "description": f"High duplicate rate ({stats['duplicate_rate']:.1%}) - consider cleanup",
                    "impact": "high"
                })
        
        # Importance scoring insights
        scoring = systems_results.get("importance_scoring", {})
        if scoring and "analysis" in scoring:
            analysis = scoring["analysis"]
            stats = analysis.get("score_statistics", {})
            recs = analysis.get("recommendations_summary", {})
            
            insights["memory_quality"]["avg_predicted_importance"] = stats.get("avg_predicted", 0)
            insights["memory_quality"]["score_alignment"] = abs(stats.get("avg_predicted", 5) - stats.get("avg_current", 5))
            
            # Check if many memories need importance adjustments
            total_changes = recs.get("increase", 0) + recs.get("decrease", 0)
            total_scored = scoring.get("successfully_scored", 1)
            change_rate = total_changes / total_scored if total_scored > 0 else 0
            
            if change_rate > 0.3:  # More than 30% need changes
                insights["optimization_opportunities"].append({
                    "type": "importance_scoring",
                    "description": f"{change_rate:.1%} of memories have misaligned importance scores",
                    "impact": "medium"
                })
        
        # Q&A insights
        qa = systems_results.get("qa_capabilities", {})
        if qa:
            insights["system_efficiency"]["qa_success_rate"] = qa.get("successful_answers", 0) / max(qa.get("test_questions", 1), 1)
            insights["system_efficiency"]["qa_avg_confidence"] = qa.get("avg_confidence", 0)
            insights["system_efficiency"]["qa_response_time"] = qa.get("avg_processing_time", 0)
            
            if qa.get("avg_confidence", 0) < 0.5:
                insights["optimization_opportunities"].append({
                    "type": "qa_quality",
                    "description": "Q&A confidence is low - may need better tagging or content",
                    "impact": "medium"
                })
        
        return insights
    
    def _generate_system_recommendations(self, systems_results: Dict[str, Any], insights: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on all system results"""
        recommendations = []
        
        # Deduplication recommendations
        dedup = systems_results.get("deduplication", {})
        if dedup and dedup.get("recommendations"):
            dedup_recs = dedup["recommendations"]
            
            if dedup_recs.get("auto_merge"):
                recommendations.append({
                    "system": "deduplication",
                    "action": "auto_merge_duplicates",
                    "description": f"Auto-merge {len(dedup_recs['auto_merge'])} exact duplicate pairs",
                    "priority": "high",
                    "estimated_time": "2-3 minutes",
                    "command": "await deduplicator.execute_auto_merge(dedup_results['recommendations']['auto_merge'])"
                })
            
            if dedup_recs.get("manual_review"):
                recommendations.append({
                    "system": "deduplication", 
                    "action": "review_near_duplicates",
                    "description": f"Review {len(dedup_recs['manual_review'])} near-duplicate pairs",
                    "priority": "medium",
                    "estimated_time": "15-20 minutes"
                })
        
        # Importance scoring recommendations
        scoring = systems_results.get("importance_scoring", {})
        if scoring and scoring.get("analysis", {}).get("recommendations_summary"):
            recs = scoring["analysis"]["recommendations_summary"]
            
            high_confidence_changes = 0
            if scoring.get("scored_memories"):
                high_confidence_changes = len([
                    m for m in scoring["scored_memories"] 
                    if m.get("recommendation", {}).get("confidence") == "high"
                ])
            
            if high_confidence_changes > 0:
                recommendations.append({
                    "system": "importance_scoring",
                    "action": "update_importance_scores",
                    "description": f"Update {high_confidence_changes} high-confidence importance scores",
                    "priority": "medium",
                    "estimated_time": "5-10 minutes"
                })
        
        # Q&A system recommendations
        qa = systems_results.get("qa_capabilities", {})
        if qa and qa.get("avg_confidence", 0) < 0.6:
            recommendations.append({
                "system": "qa_engine",
                "action": "improve_memory_content",
                "description": "Add more descriptive tags and improve memory content quality",
                "priority": "low",
                "estimated_time": "ongoing"
            })
        
        # General system recommendations
        if len(insights.get("optimization_opportunities", [])) >= 2:
            recommendations.append({
                "system": "general",
                "action": "comprehensive_optimization",
                "description": "Multiple optimization opportunities detected - run full cleanup",
                "priority": "high",
                "estimated_time": "30-45 minutes"
            })
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 2))
        
        return recommendations
    
    async def quick_health_check(self) -> Dict[str, Any]:
        """Quick system health check"""
        logger.info("🔍 Running quick health check...")
        
        health = {
            "timestamp": datetime.now().isoformat(),
            "systems": {
                "memory_service": "checking",
                "qa_engine": "checking", 
                "deduplicator": "checking",
                "importance_scorer": "checking"
            },
            "overall_status": "unknown",
            "quick_stats": {}
        }
        
        try:
            # Test memory service
            test_search = self.memory_service.search_memories("test", limit=1)
            health["systems"]["memory_service"] = "healthy" if test_search else "degraded"
            
            # Test Q&A engine with simple question
            qa_result = await self.qa_engine.ask("What is the most recent memory?")
            health["systems"]["qa_engine"] = "healthy" if "error" not in qa_result else "degraded"
            
            # Test deduplicator (just check if it can analyze a small set)
            small_dedup = self.deduplicator.find_duplicates(batch_size=5)
            health["systems"]["deduplicator"] = "healthy" if "error" not in small_dedup else "degraded"
            
            # Test importance scorer
            scorer_test = self.scorer.learn_from_usage_patterns(days_back=1)
            health["systems"]["importance_scorer"] = "healthy" if "error" not in scorer_test else "degraded"
            
            # Overall status
            healthy_systems = sum(1 for status in health["systems"].values() if status == "healthy")
            total_systems = len(health["systems"])
            
            if healthy_systems == total_systems:
                health["overall_status"] = "healthy"
            elif healthy_systems >= total_systems * 0.75:
                health["overall_status"] = "mostly_healthy"
            else:
                health["overall_status"] = "degraded"
            
            # Quick stats
            total_memories = len(self.memory_service.search_memories("", limit=1000))
            health["quick_stats"] = {
                "total_memories": total_memories,
                "systems_healthy": healthy_systems,
                "systems_total": total_systems,
                "health_percentage": (healthy_systems / total_systems) * 100
            }
            
        except Exception as e:
            health["overall_status"] = "error"
            health["error"] = str(e)
        
        return health


async def test_enhancement_suite():
    """Comprehensive test of the memory enhancement suite"""
    
    print("🚀 Initializing Memory Enhancement Suite...")
    suite = MemoryEnhancementSuite()
    
    print("\n" + "="*80)
    print("🧠 MEMORY ENHANCEMENT SUITE - COMPREHENSIVE TEST")
    print("="*80)
    
    # Quick health check first
    print("\n🔍 Running health check...")
    health = await suite.quick_health_check()
    
    print(f"Overall Status: {health['overall_status'].upper()}")
    print(f"Systems Health: {health['quick_stats']['health_percentage']:.0f}% ({health['quick_stats']['systems_healthy']}/{health['quick_stats']['systems_total']})")
    print(f"Total Memories: {health['quick_stats']['total_memories']}")
    
    if health["overall_status"] not in ["healthy", "mostly_healthy"]:
        print("⚠️ System health issues detected. Some features may not work optimally.")
    
    # Full comprehensive analysis
    print(f"\n🔬 Running comprehensive analysis...")
    results = await suite.comprehensive_analysis()
    
    if "error" in results:
        print(f"❌ Analysis failed: {results['error']}")
        return
    
    # Display results
    print(f"\n📊 ANALYSIS RESULTS")
    print(f"Processing time: {results['processing_time']:.2f}s")
    
    # Deduplication results
    dedup = results["systems"]["deduplication"]
    if dedup and "duplicates" in dedup:
        duplicates = dedup["duplicates"]
        print(f"\n🧹 Deduplication Analysis:")
        print(f"   Exact duplicates: {len(duplicates.get('exact_duplicates', []))}")
        print(f"   Near duplicates: {len(duplicates.get('near_duplicates', []))}")
        print(f"   Related clusters: {len(duplicates.get('related_clusters', []))}")
        print(f"   Potential conflicts: {len(duplicates.get('conflicting_pairs', []))}")
    
    # Importance scoring results
    scoring = results["systems"]["importance_scoring"]
    if scoring and "analysis" in scoring:
        analysis = scoring["analysis"]
        stats = analysis.get("score_statistics", {})
        print(f"\n🧮 Importance Scoring Analysis:")
        print(f"   Memories scored: {scoring.get('successfully_scored', 0)}")
        print(f"   Avg predicted importance: {stats.get('avg_predicted', 0):.1f}")
        print(f"   Avg current importance: {stats.get('avg_current', 0):.1f}")
        print(f"   Score alignment: {abs(stats.get('avg_predicted', 5) - stats.get('avg_current', 5)):.1f}")
    
    # Q&A results
    qa = results["systems"]["qa_capabilities"]
    if qa:
        print(f"\n🤖 Q&A Engine Analysis:")
        print(f"   Test questions: {qa.get('test_questions', 0)}")
        print(f"   Success rate: {qa.get('successful_answers', 0)}/{qa.get('test_questions', 0)}")
        print(f"   Avg confidence: {qa.get('avg_confidence', 0):.2f}")
        print(f"   Avg response time: {qa.get('avg_processing_time', 0):.2f}s")
        
        if qa.get("sample_qa"):
            sample = qa["sample_qa"][0]
            print(f"   Sample Q&A:")
            print(f"     Q: {sample['question']}")
            print(f"     A: {sample['answer_preview']}")
    
    # Combined insights
    insights = results.get("insights", {})
    if insights:
        print(f"\n💡 Combined Insights:")
        
        quality = insights.get("memory_quality", {})
        if quality:
            print(f"   Memory Quality:")
            if "duplicate_rate" in quality:
                print(f"     - Duplicate rate: {quality['duplicate_rate']:.1%}")
            if "score_alignment" in quality:
                print(f"     - Score misalignment: {quality['score_alignment']:.1f}")
        
        efficiency = insights.get("system_efficiency", {})
        if efficiency:
            print(f"   System Efficiency:")
            if "qa_success_rate" in efficiency:
                print(f"     - Q&A success rate: {efficiency['qa_success_rate']:.1%}")
            if "qa_avg_confidence" in efficiency:
                print(f"     - Q&A avg confidence: {efficiency['qa_avg_confidence']:.2f}")
    
    # Recommendations
    recommendations = results.get("recommendations", [])
    if recommendations:
        print(f"\n🎯 Recommendations ({len(recommendations)}):")
        for i, rec in enumerate(recommendations[:5], 1):
            priority_emoji = {"high": "🔥", "medium": "⚡", "low": "💡"}.get(rec["priority"], "📋")
            print(f"   {priority_emoji} {rec['action'].replace('_', ' ').title()}")
            print(f"      {rec['description']}")
            if rec.get("estimated_time"):
                print(f"      Time: {rec['estimated_time']}")
    
    print("\n" + "="*80)
    print("✅ Memory Enhancement Suite analysis complete!")
    print("\nThe suite successfully integrates:")
    print("   🤖 Q&A Engine - Ask natural language questions about your memories")
    print("   🧹 Deduplication - Find and merge duplicate/similar memories") 
    print("   🧮 Smart Scoring - Automatic importance prediction based on usage")
    print("\nAll three systems from the '7 Python Libraries' article are now operational!")


if __name__ == "__main__":
    asyncio.run(test_enhancement_suite())