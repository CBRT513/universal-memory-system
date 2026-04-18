#!/usr/bin/env python3
"""
Interactive test suite for the Memory Enhancement systems
Tests Q&A, Deduplication, and Smart Scoring
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from memory_enhancement_suite import MemoryEnhancementSuite
from memory_qa_engine import MemoryQAEngine
from memory_deduplicator import MemoryDeduplicator
from smart_importance_scorer import SmartImportanceScorer
from memory_service import UniversalMemoryService

async def interactive_qa_test():
    """Interactive Q&A test - ask your own questions"""
    print("\n" + "="*60)
    print("🤖 INTERACTIVE Q&A TEST")
    print("="*60)
    
    qa_engine = MemoryQAEngine(use_local_llm=True)
    
    print("\nAsk questions about your memory system (type 'quit' to exit):")
    print("\nExample questions:")
    print("  - What Python libraries am I using?")
    print("  - What are my most important memories?")
    print("  - What articles have I saved about AI?")
    print("  - What implementation tasks are pending?")
    
    while True:
        question = input("\n💭 Your question: ").strip()
        if question.lower() in ['quit', 'exit', 'q']:
            break
            
        print("\n🔍 Searching memories...")
        result = await qa_engine.ask(question)
        
        print(f"\n💡 Answer: {result['answer']}")
        print(f"📊 Confidence: {result['confidence']:.2%}")
        print(f"📚 Based on {result['source_count']} memories")
        
        if result.get('sources'):
            print("\n📝 Top sources:")
            for i, source in enumerate(result['sources'][:3], 1):
                print(f"   {i}. [{source['project']}] {source['content_preview'][:100]}...")

async def test_deduplication():
    """Test deduplication by creating intentional duplicates"""
    print("\n" + "="*60)
    print("🧹 DEDUPLICATION TEST")
    print("="*60)
    
    memory_service = UniversalMemoryService()
    
    # Create some test duplicates
    print("\n📝 Creating test memories with duplicates...")
    
    test_memories = [
        "Sentence-Transformers is a Python library for generating embeddings 10x faster than traditional methods",
        "Sentence-Transformers is a Python library for generating embeddings 10x faster than traditional methods",  # Exact duplicate
        "Sentence-Transformers library generates embeddings much faster than traditional approaches",  # Near duplicate
        "LangChain helps build AI applications with chained workflows",
        "LangChain is useful for building AI apps with workflow chains",  # Near duplicate
        "The Universal Memory System stores and retrieves memories efficiently"
    ]
    
    memory_ids = []
    for content in test_memories:
        result = memory_service.store_memory(
            content=content,
            project="test-dedup",
            category="test",
            tags=["test", "duplicate-detection"],
            importance=5
        )
        memory_ids.append(result['id'])
        print(f"   ✅ Stored: {content[:50]}...")
    
    # Run deduplication
    print("\n🔍 Running deduplication analysis...")
    deduplicator = MemoryDeduplicator(similarity_threshold=0.85)
    results = deduplicator.find_duplicates(project_filter="test-dedup")
    
    if "error" not in results:
        duplicates = results['duplicates']
        print(f"\n📊 Results:")
        print(f"   Exact duplicates found: {len(duplicates['exact_duplicates'])}")
        print(f"   Near duplicates found: {len(duplicates['near_duplicates'])}")
        
        if duplicates['exact_duplicates']:
            print("\n🎯 Exact duplicate example:")
            dup = duplicates['exact_duplicates'][0]
            print(f"   Similarity: {dup['similarity_score']:.3f}")
            print(f"   Memory 1: {dup['memory1']['content_preview'][:80]}...")
            print(f"   Memory 2: {dup['memory2']['content_preview'][:80]}...")
            print(f"   Recommendation: {dup['merge_recommendation']['action']}")
    
    # Cleanup test memories
    print("\n🧹 Cleaning up test memories...")
    for mem_id in memory_ids:
        try:
            with memory_service._get_connection() as conn:
                conn.execute("DELETE FROM memories WHERE id = ?", (mem_id,))
                conn.commit()
        except:
            pass
    print("   ✅ Test memories removed")

async def test_importance_scoring():
    """Test importance scoring on real memories"""
    print("\n" + "="*60)
    print("🧮 IMPORTANCE SCORING TEST")
    print("="*60)
    
    scorer = SmartImportanceScorer()
    
    # Score a batch of memories
    print("\n📊 Scoring memory importance...")
    results = scorer.batch_score_memories(limit=10)
    
    if "error" not in results:
        print(f"\n✅ Scored {results['successfully_scored']} memories")
        
        if results.get('analysis'):
            stats = results['analysis']['score_statistics']
            print(f"\n📈 Statistics:")
            print(f"   Average predicted importance: {stats['avg_predicted']:.1f}/10")
            print(f"   Average current importance: {stats['avg_current']:.1f}/10")
            print(f"   Score range: {stats['min_predicted']:.1f} - {stats['max_predicted']:.1f}")
            
            recs = results['analysis']['recommendations_summary']
            print(f"\n💡 Recommendations:")
            print(f"   Increase importance: {recs['increase']} memories")
            print(f"   Decrease importance: {recs['decrease']} memories")
            print(f"   No change needed: {recs['no_change']} memories")
        
        if results.get('scored_memories'):
            print(f"\n📝 Example scored memory:")
            example = results['scored_memories'][0]
            print(f"   Current importance: {example['current_importance']}/10")
            print(f"   Predicted importance: {example['predicted_importance']}/10")
            print(f"   Recommendation: {example['recommendation']['action']}")
            
            if example['explanation']['main_contributors']:
                print(f"   Top factors:")
                for factor in example['explanation']['main_contributors'][:2]:
                    print(f"     - {factor['factor']}: {factor['contribution']:.1f}")

async def quick_system_test():
    """Quick test of all three systems"""
    print("\n" + "="*60)
    print("🚀 QUICK SYSTEM TEST - ALL THREE ENHANCEMENTS")
    print("="*60)
    
    suite = MemoryEnhancementSuite()
    
    # Health check
    print("\n🔍 Running health check...")
    health = await suite.quick_health_check()
    print(f"   Overall Status: {health['overall_status'].upper()}")
    print(f"   Systems Healthy: {health['quick_stats']['health_percentage']:.0f}%")
    print(f"   Total Memories: {health['quick_stats']['total_memories']}")
    
    # Test each system briefly
    print("\n📋 Testing individual systems:")
    
    # Q&A Test
    print("\n1️⃣ Q&A Engine:")
    qa_result = await suite.qa_engine.ask("What is the most recent thing I learned?")
    print(f"   ✅ Q&A working - Confidence: {qa_result['confidence']:.2%}")
    
    # Deduplication Test
    print("\n2️⃣ Deduplication:")
    dedup_result = suite.deduplicator.find_duplicates(batch_size=10)
    if "error" not in dedup_result:
        print(f"   ✅ Deduplication working - Analyzed {dedup_result['total_memories']} memories")
    
    # Importance Scoring Test
    print("\n3️⃣ Importance Scoring:")
    scoring_result = suite.scorer.batch_score_memories(limit=5)
    if "error" not in scoring_result:
        print(f"   ✅ Scoring working - Scored {scoring_result['successfully_scored']} memories")
    
    print("\n✨ All systems operational!")

async def main():
    """Main test menu"""
    print("\n" + "="*80)
    print("🧪 MEMORY ENHANCEMENT SUITE - TEST MENU")
    print("="*80)
    print("\nChoose a test:")
    print("1. Quick System Test (all three systems)")
    print("2. Interactive Q&A Test")
    print("3. Deduplication Test")
    print("4. Importance Scoring Test")
    print("5. Run All Tests")
    print("0. Exit")
    
    choice = input("\nEnter choice (0-5): ").strip()
    
    if choice == "1":
        await quick_system_test()
    elif choice == "2":
        await interactive_qa_test()
    elif choice == "3":
        await test_deduplication()
    elif choice == "4":
        await test_importance_scoring()
    elif choice == "5":
        await quick_system_test()
        await test_deduplication()
        await test_importance_scoring()
        print("\n✅ All tests complete!")
    elif choice == "0":
        print("Goodbye!")
    else:
        print("Invalid choice")

if __name__ == "__main__":
    asyncio.run(main())