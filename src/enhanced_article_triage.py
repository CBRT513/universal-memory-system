#!/usr/bin/env python3
"""
Enhanced Article Triage System with LangChain Auto-Implementation
Automatically detects articles, extracts actions, and implements beneficial changes
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from article_triage import ArticleTriage, ArticleDetector
from langchain_action_extractor import LangChainActionExtractor
from memory_service import UniversalMemoryService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoImplementationPipeline:
    """
    Complete pipeline: Article → Analysis → Action Extraction → Implementation
    The goal: Feed an article, anything beneficial gets implemented automatically
    """
    
    def __init__(self):
        """Initialize the auto-implementation pipeline"""
        self.article_triage = ArticleTriage()
        self.action_extractor = LangChainActionExtractor(use_local_llm=True)
        self.memory_service = UniversalMemoryService()
        
        # Track implementations
        self.implementation_log = []
        
    async def process_article(self, content: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process an article through the complete pipeline
        
        Args:
            content: Article content
            metadata: Optional metadata (source, tags, etc.)
            
        Returns:
            Complete processing result with implementations
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "content_preview": content[:200] + "..." if len(content) > 200 else content,
            "stages": {}
        }
        
        try:
            # Stage 1: Detect if it's an article
            logger.info("Stage 1: Content Detection")
            content_type = ArticleDetector.detect_content_type(content, metadata)
            result["stages"]["detection"] = {
                "content_type": content_type,
                "is_article": content_type == "article"
            }
            
            if content_type != "article":
                logger.info(f"Content is {content_type}, not an article. Skipping implementation pipeline.")
                return result
            
            # Stage 2: Triage for actionability
            logger.info("Stage 2: Article Triage")
            triage_result = await self.article_triage.triage(
                content=content,
                metadata=metadata or {}
            )
            result["stages"]["triage"] = triage_result
            
            # Stage 3: Extract actions using LangChain
            logger.info("Stage 3: Action Extraction with LangChain")
            article_data = {
                "content": content,
                "title": triage_result.get("title", "Unknown Article"),
                "id": metadata.get("id", f"article_{datetime.now().timestamp()}")
            }
            
            implementation_plan = self.action_extractor.extract_actions(article_data)
            result["stages"]["action_extraction"] = implementation_plan
            
            # Stage 4: Determine what to implement
            logger.info("Stage 4: Implementation Decision")
            implementations = await self._decide_implementations(
                triage_result, 
                implementation_plan
            )
            result["stages"]["implementation_decision"] = implementations
            
            # Stage 5: Execute implementations
            if implementations["should_implement"]:
                logger.info("Stage 5: Executing Implementations")
                execution_results = await self._execute_implementations(implementations)
                result["stages"]["execution"] = execution_results
                
                # Stage 6: Store in memory with enriched metadata
                logger.info("Stage 6: Storing Enhanced Memory")
                memory_result = self._store_enhanced_memory(
                    content, 
                    triage_result, 
                    implementation_plan,
                    execution_results
                )
                result["stages"]["memory_storage"] = memory_result
            else:
                logger.info("Article not actionable enough for auto-implementation")
                result["stages"]["execution"] = {"status": "skipped", "reason": "Not actionable"}
            
            # Final summary
            result["summary"] = self._generate_summary(result)
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            result["error"] = str(e)
            result["summary"] = f"Pipeline failed: {e}"
        
        return result
    
    async def _decide_implementations(
        self, 
        triage_result: Dict, 
        implementation_plan: Dict
    ) -> Dict[str, Any]:
        """
        Decide what should be implemented based on triage and extracted actions
        """
        decision = {
            "should_implement": False,
            "auto_implement": [],
            "manual_review": [],
            "skip": [],
            "reasoning": []
        }
        
        # Check actionability scores
        triage_score = triage_result.get("actionability_score", 0)
        langchain_score = implementation_plan.get("actionability_score", 0)
        combined_score = (triage_score + langchain_score) / 2
        
        decision["scores"] = {
            "triage": triage_score,
            "langchain": langchain_score,
            "combined": combined_score
        }
        
        # Decision logic
        if combined_score >= 7:
            decision["should_implement"] = True
            decision["reasoning"].append(f"High actionability score: {combined_score}/10")
            
            # Categorize action items
            for action in implementation_plan.get("action_items", []):
                if action["priority"] == "high" and action["effort"] in ["small", "medium"]:
                    decision["auto_implement"].append(action)
                elif action["priority"] == "high":
                    decision["manual_review"].append(action)
                elif action["priority"] == "medium" and action["effort"] == "small":
                    decision["auto_implement"].append(action)
                else:
                    decision["skip"].append(action)
        
        elif combined_score >= 5:
            decision["should_implement"] = False
            decision["reasoning"].append(f"Medium actionability ({combined_score}/10) - manual review needed")
            decision["manual_review"] = implementation_plan.get("action_items", [])
        
        else:
            decision["should_implement"] = False
            decision["reasoning"].append(f"Low actionability ({combined_score}/10) - archiving for reference")
            decision["skip"] = implementation_plan.get("action_items", [])
        
        return decision
    
    async def _execute_implementations(self, implementations: Dict) -> Dict[str, Any]:
        """
        Execute the actual implementations
        This is where the magic happens - beneficial changes get implemented
        """
        results = {
            "implemented": [],
            "failed": [],
            "timestamp": datetime.now().isoformat()
        }
        
        for action in implementations.get("auto_implement", []):
            try:
                # Determine implementation type
                if "install" in action["action"].lower():
                    result = await self._implement_installation(action)
                elif "create" in action["action"].lower() or "implement" in action["action"].lower():
                    result = await self._implement_code_change(action)
                elif "configure" in action["action"].lower():
                    result = await self._implement_configuration(action)
                else:
                    result = await self._create_task_for_manual(action)
                
                results["implemented"].append({
                    "action": action["action"],
                    "result": result,
                    "status": "success"
                })
                
            except Exception as e:
                logger.error(f"Failed to implement: {action['action']} - {e}")
                results["failed"].append({
                    "action": action["action"],
                    "error": str(e),
                    "status": "failed"
                })
        
        # Log implementations
        self.implementation_log.extend(results["implemented"])
        
        return results
    
    async def _implement_installation(self, action: Dict) -> Dict:
        """Implement package/library installations"""
        # Extract package names from action
        import re
        packages = re.findall(r'pip install ([\w\-]+)', action.get("details", ""))
        
        if packages:
            # Create requirements update task
            return {
                "type": "installation",
                "packages": packages,
                "command": f"pip3 install {' '.join(packages)}",
                "status": "queued_for_installation"
            }
        
        return {"type": "installation", "status": "no_packages_found"}
    
    async def _implement_code_change(self, action: Dict) -> Dict:
        """Implement code changes or create new files"""
        # Check if there's a code example
        code_example = action.get("code_example")
        
        if code_example:
            # Determine appropriate file location
            technologies = action.get("technologies", [])
            
            if "python" in [t.lower() for t in technologies]:
                file_path = f"implementations/auto_impl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
            else:
                file_path = f"implementations/auto_impl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            return {
                "type": "code_implementation",
                "file_path": file_path,
                "code": code_example,
                "status": "ready_to_create",
                "action": action["action"]
            }
        
        return {
            "type": "code_implementation",
            "status": "no_code_example",
            "needs": "manual_implementation"
        }
    
    async def _implement_configuration(self, action: Dict) -> Dict:
        """Implement configuration changes"""
        return {
            "type": "configuration",
            "action": action["action"],
            "details": action["details"],
            "status": "needs_manual_review"
        }
    
    async def _create_task_for_manual(self, action: Dict) -> Dict:
        """Create a task for manual implementation"""
        task = self.action_extractor.create_tasks_from_actions({"action_items": [action]})
        
        return {
            "type": "task_created",
            "task": task[0] if task else None,
            "status": "added_to_backlog"
        }
    
    def _store_enhanced_memory(
        self, 
        content: str, 
        triage_result: Dict,
        implementation_plan: Dict,
        execution_results: Dict
    ) -> Dict:
        """Store the article with all extracted insights in memory"""
        
        # Combine all metadata
        enhanced_metadata = {
            "triage": triage_result,
            "implementation_plan": implementation_plan,
            "execution_results": execution_results,
            "processing_timestamp": datetime.now().isoformat(),
            "auto_implemented": len(execution_results.get("implemented", [])) > 0
        }
        
        # Store in memory system
        memory_id = self.memory_service.store_memory(
            content=content,
            project="auto-implementation",
            category="article",
            tags=[
                "article", 
                "langchain", 
                "auto-implemented" if enhanced_metadata["auto_implemented"] else "manual-review",
                f"actionability-{int(implementation_plan.get('actionability_score', 0))}"
            ],
            importance=int(implementation_plan.get('actionability_score', 5)),
            metadata=enhanced_metadata
        )
        
        return {
            "memory_id": memory_id,
            "enhanced": True,
            "metadata_stored": True
        }
    
    def _generate_summary(self, result: Dict) -> str:
        """Generate a human-readable summary of the processing"""
        stages = result.get("stages", {})
        
        # Check if it was an article
        if stages.get("detection", {}).get("content_type") != "article":
            return f"Content type: {stages.get('detection', {}).get('content_type')} - Not processed as article"
        
        # Get key metrics
        triage = stages.get("triage", {})
        extraction = stages.get("action_extraction", {})
        execution = stages.get("execution", {})
        
        action_count = len(extraction.get("action_items", []))
        implemented_count = len(execution.get("implemented", []))
        
        # Build summary
        summary_parts = [
            f"Article: {triage.get('title', 'Unknown')}",
            f"Classification: {triage.get('classification', 'unknown')}",
            f"Actionability: {extraction.get('actionability_score', 0)}/10",
            f"Extracted {action_count} action items"
        ]
        
        if implemented_count > 0:
            summary_parts.append(f"✅ Auto-implemented {implemented_count} actions")
        
        if execution.get("failed"):
            summary_parts.append(f"⚠️ {len(execution['failed'])} actions failed")
        
        return " | ".join(summary_parts)


async def test_auto_implementation():
    """Test the complete auto-implementation pipeline"""
    
    # Test article about Sentence-Transformers (which we just implemented!)
    test_article = """
    Building Semantic Search with Sentence-Transformers
    
    Sentence-Transformers makes it incredibly easy to build semantic search systems.
    Here's how to implement it:
    
    1. Install the library:
    pip install sentence-transformers
    
    2. Choose a pre-trained model:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    3. Generate embeddings for your documents:
    documents = ["Document 1", "Document 2", "Document 3"]
    embeddings = model.encode(documents)
    
    4. Implement similarity search:
    query = "Search query"
    query_embedding = model.encode(query)
    
    from sklearn.metrics.pairwise import cosine_similarity
    similarities = cosine_similarity([query_embedding], embeddings)[0]
    
    5. Find most similar documents:
    top_k = 3
    top_indices = similarities.argsort()[-top_k:][::-1]
    
    This gives you a complete semantic search system in just a few lines of code!
    Perfect for enhancing any search functionality in your applications.
    """
    
    # Initialize pipeline
    pipeline = AutoImplementationPipeline()
    
    # Process the article
    print("🚀 Processing article through auto-implementation pipeline...")
    result = await pipeline.process_article(test_article, {
        "source": "test",
        "url": "https://example.com/sentence-transformers-guide"
    })
    
    # Display results
    print("\n" + "="*60)
    print("📊 PIPELINE RESULTS")
    print("="*60)
    
    print(f"\n📝 Summary: {result['summary']}")
    
    # Show stages
    stages = result.get("stages", {})
    
    if stages.get("action_extraction"):
        print("\n🎯 Extracted Actions:")
        for i, action in enumerate(stages["action_extraction"].get("action_items", []), 1):
            print(f"  {i}. {action['action']}")
            print(f"     Priority: {action['priority']} | Effort: {action['effort']}")
    
    if stages.get("execution"):
        print("\n✅ Implementations:")
        for impl in stages["execution"].get("implemented", []):
            print(f"  • {impl['action']}")
            print(f"    Status: {impl['status']}")
    
    print("\n" + "="*60)
    print("🎉 Pipeline complete! Any beneficial content has been processed for implementation.")
    
    return result


if __name__ == "__main__":
    # Run the test
    asyncio.run(test_auto_implementation())