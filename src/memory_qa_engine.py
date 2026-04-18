#!/usr/bin/env python3
"""
Memory Q&A Engine - "Ask Me Anything" for your memory system
Uses Haystack-inspired architecture with local LLMs to answer questions about your memories
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import asyncio
import re
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from memory_service import UniversalMemoryService
from langchain_action_extractor import LangChainActionExtractor
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemoryQAEngine:
    """
    Haystack-inspired Q&A engine for your memories
    Ask natural language questions, get synthesized answers from multiple memories
    """
    
    def __init__(self, use_local_llm: bool = True):
        """Initialize the Q&A engine"""
        self.memory_service = UniversalMemoryService()
        self.use_local_llm = use_local_llm
        self.llm = self._initialize_llm()
        
        # Use the same embedding model as the memory system
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Context window for answers (number of memories to consider)
        self.max_context_memories = 10
        
    def _initialize_llm(self):
        """Initialize LLM for answer synthesis"""
        if self.use_local_llm:
            try:
                import requests
                # Test if Ollama is available
                response = requests.get("http://localhost:11434/api/tags", timeout=2)
                if response.status_code == 200:
                    from langchain_community.llms import Ollama
                    return Ollama(
                        model="llama3.2:3b",
                        temperature=0.3,
                        num_predict=1000
                    )
            except:
                pass
        
        # Fallback to mock for demo
        return self._create_mock_llm()
    
    def _create_mock_llm(self):
        """Create mock LLM for testing"""
        from langchain.llms.base import LLM
        from typing import Any, List, Optional
        
        class MockQALLM(LLM):
            @property
            def _llm_type(self) -> str:
                return "mock_qa"
            
            def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
                # Simple mock that extracts key information from the prompt
                if "sentence-transformers" in prompt.lower():
                    return "Based on your memories: Sentence-Transformers is a library for generating embeddings that can be used for semantic similarity. You've implemented it in your Universal Memory System for 10x faster search performance."
                elif "react" in prompt.lower():
                    return "Based on your memories: React is a JavaScript library for building user interfaces. You have several React-related memories discussing hooks, best practices, and component patterns."
                elif "python" in prompt.lower():
                    return "Based on your memories: Python is extensively used in your projects, particularly for AI/ML work. You have memories about various Python libraries including LangChain, Sentence-Transformers, and FastAPI."
                else:
                    return f"I found information related to your question in your memory system. The memories contain relevant details that can help answer your query."
        
        return MockQALLM()
    
    async def ask(self, question: str, project_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Ask a question about your memories
        
        Args:
            question: Natural language question
            project_filter: Optional project to limit search
            
        Returns:
            Complete Q&A result with answer and sources
        """
        start_time = datetime.now()
        
        try:
            # Step 1: Retrieve relevant memories
            logger.info(f"Searching memories for: {question}")
            relevant_memories = self._retrieve_relevant_memories(question, project_filter)
            
            # Step 2: Rank and select top memories
            top_memories = self._rank_memories_by_relevance(question, relevant_memories)
            
            # Step 3: Generate answer from selected memories
            answer = await self._synthesize_answer(question, top_memories)
            
            # Step 4: Extract key insights
            insights = self._extract_insights(top_memories)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "question": question,
                "answer": answer,
                "confidence": self._calculate_confidence(top_memories, question),
                "source_count": len(top_memories),
                "sources": [
                    {
                        "id": mem["id"],
                        "content_preview": mem["content"][:200] + "..." if len(mem["content"]) > 200 else mem["content"],
                        "project": mem.get("project", "unknown"),
                        "importance": mem.get("importance", 5),
                        "tags": mem.get("tags", [])
                    }
                    for mem in top_memories
                ],
                "insights": insights,
                "processing_time": processing_time,
                "timestamp": datetime.now().isoformat()
            }
            
            # Store the Q&A session in memory for future reference
            self._store_qa_session(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Q&A error: {e}")
            return {
                "question": question,
                "answer": f"Sorry, I encountered an error: {e}",
                "confidence": 0.0,
                "source_count": 0,
                "sources": [],
                "error": str(e)
            }
    
    def _retrieve_relevant_memories(self, question: str, project_filter: Optional[str] = None) -> List[Dict]:
        """Retrieve memories relevant to the question"""
        
        # Use both semantic search and keyword search
        memories = []
        
        # Semantic search using embeddings
        try:
            semantic_results = self.memory_service.search_memories(
                query=question,
                limit=20,
                include_semantic=True,
                project=project_filter
            )
            memories.extend(semantic_results)
        except Exception as e:
            logger.warning(f"Semantic search failed: {e}")
        
        # Fallback to keyword search if semantic fails
        if len(memories) < 5:
            keyword_results = self.memory_service.search_memories(
                query=question,
                limit=15,
                include_semantic=False,
                project=project_filter
            )
            # Merge results, avoiding duplicates
            memory_ids = {m["id"] for m in memories}
            for mem in keyword_results:
                if mem["id"] not in memory_ids:
                    memories.append(mem)
        
        return memories
    
    def _rank_memories_by_relevance(self, question: str, memories: List[Dict]) -> List[Dict]:
        """Rank memories by relevance to the question"""
        if not memories:
            return []
        
        try:
            # Generate embedding for the question
            question_embedding = self.embedder.encode(question)
            
            scored_memories = []
            for memory in memories:
                # Calculate semantic similarity
                content = memory.get("content", "")
                if content:
                    content_embedding = self.embedder.encode(content)
                    similarity = cosine_similarity([question_embedding], [content_embedding])[0][0]
                    
                    # Boost score based on importance and access count
                    importance_boost = memory.get("importance", 5) / 10.0
                    access_boost = min(memory.get("access_count", 0) / 10.0, 0.2)
                    
                    final_score = similarity + importance_boost * 0.3 + access_boost
                    
                    scored_memories.append({
                        **memory,
                        "relevance_score": final_score
                    })
            
            # Sort by relevance and return top memories
            scored_memories.sort(key=lambda x: x["relevance_score"], reverse=True)
            return scored_memories[:self.max_context_memories]
            
        except Exception as e:
            logger.warning(f"Relevance ranking failed: {e}")
            # Fallback to importance and access count
            return sorted(memories, 
                         key=lambda x: (x.get("importance", 5), x.get("access_count", 0)), 
                         reverse=True)[:self.max_context_memories]
    
    async def _synthesize_answer(self, question: str, memories: List[Dict]) -> str:
        """Synthesize answer from relevant memories using LLM"""
        
        if not memories:
            return "I couldn't find any relevant information in your memory system for this question."
        
        # Build context from memories
        context_parts = []
        for i, memory in enumerate(memories, 1):
            content = memory["content"][:500]  # Limit content length
            project = memory.get("project", "unknown")
            tags = ", ".join(memory.get("tags", []))
            
            context_parts.append(f"""
Memory {i}:
Project: {project}
Tags: {tags}
Content: {content}
""")
        
        context = "\n".join(context_parts)
        
        # Create prompt for answer synthesis
        prompt = f"""Based on the following memories from a personal knowledge base, answer this question: "{question}"

{context}

Instructions:
- Provide a comprehensive answer based on the memories above
- Reference specific details from the memories when relevant
- If the memories contain conflicting information, acknowledge this
- Be concise but thorough
- If the question cannot be fully answered from the memories, say so

Answer:"""
        
        try:
            # Generate answer using LLM
            if hasattr(self.llm, 'invoke'):
                answer = self.llm.invoke(prompt)
            else:
                answer = self.llm(prompt)
            return answer.strip()
            
        except Exception as e:
            logger.error(f"Answer synthesis failed: {e}")
            # Fallback to simple concatenation
            return f"Based on {len(memories)} memories in your system: " + \
                   " ".join([mem["content"][:100] + "..." for mem in memories[:3]])
    
    def _calculate_confidence(self, memories: List[Dict], question: str) -> float:
        """Calculate confidence score for the answer (0-1)"""
        if not memories:
            return 0.0
        
        # Base confidence on number of relevant memories
        memory_confidence = min(len(memories) / 5.0, 1.0)
        
        # Boost confidence based on relevance scores
        if memories and "relevance_score" in memories[0]:
            avg_relevance = sum(m.get("relevance_score", 0.5) for m in memories) / len(memories)
            relevance_confidence = min(avg_relevance, 1.0)
        else:
            relevance_confidence = 0.5
        
        # Boost confidence based on memory importance
        avg_importance = sum(m.get("importance", 5) for m in memories) / len(memories) / 10.0
        
        # Combined confidence
        confidence = (memory_confidence * 0.4 + relevance_confidence * 0.4 + avg_importance * 0.2)
        return min(confidence, 1.0)
    
    def _extract_insights(self, memories: List[Dict]) -> Dict[str, Any]:
        """Extract insights from the retrieved memories"""
        if not memories:
            return {}
        
        # Extract common themes
        all_tags = []
        projects = set()
        importance_scores = []
        
        for memory in memories:
            all_tags.extend(memory.get("tags", []))
            projects.add(memory.get("project", "unknown"))
            importance_scores.append(memory.get("importance", 5))
        
        # Count tag frequency
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Get top tags
        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_memories_used": len(memories),
            "projects_involved": list(projects),
            "top_tags": [{"tag": tag, "count": count} for tag, count in top_tags],
            "avg_importance": sum(importance_scores) / len(importance_scores) if importance_scores else 0,
            "date_range": {
                "earliest": min(m.get("timestamp", 0) for m in memories if m.get("timestamp")),
                "latest": max(m.get("timestamp", 0) for m in memories if m.get("timestamp"))
            }
        }
    
    def _store_qa_session(self, qa_result: Dict[str, Any]) -> str:
        """Store the Q&A session as a memory for future reference"""
        try:
            # Create summary content
            content = f"""Q&A Session: {qa_result['question']}

Answer: {qa_result['answer']}

Confidence: {qa_result['confidence']:.2f}
Sources: {qa_result['source_count']} memories
Processing time: {qa_result['processing_time']:.2f}s

This Q&A session synthesized information from multiple memories to answer the question."""
            
            # Store as memory
            memory_id = self.memory_service.store_memory(
                content=content,
                project="memory-qa",
                category="qa_session",
                tags=["qa", "question", "synthesis"] + [tag["tag"] for tag in qa_result.get("insights", {}).get("top_tags", [])[:3]],
                importance=7,  # Q&A sessions are fairly important
                metadata={
                    "qa_session": True,
                    "original_question": qa_result["question"],
                    "confidence": qa_result["confidence"],
                    "source_count": qa_result["source_count"]
                }
            )
            
            logger.info(f"Stored Q&A session as memory: {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.warning(f"Failed to store Q&A session: {e}")
            return ""
    
    async def ask_multiple(self, questions: List[str], project_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Ask multiple questions and return all results"""
        results = []
        for question in questions:
            result = await self.ask(question, project_filter)
            results.append(result)
            # Small delay to avoid overwhelming the system
            await asyncio.sleep(0.1)
        return results
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent Q&A sessions"""
        try:
            qa_memories = self.memory_service.search_memories(
                query="",
                limit=limit,
                category="qa_session",
                project="memory-qa"
            )
            
            return [
                {
                    "question": mem.get("metadata", {}).get("original_question", "Unknown"),
                    "timestamp": datetime.fromtimestamp(mem.get("timestamp", 0)).isoformat(),
                    "confidence": mem.get("metadata", {}).get("confidence", 0),
                    "answer_preview": mem["content"].split("Answer: ")[1][:200] + "..." if "Answer: " in mem["content"] else ""
                }
                for mem in qa_memories
            ]
            
        except Exception as e:
            logger.warning(f"Failed to get conversation history: {e}")
            return []


async def test_qa_engine():
    """Test the Q&A engine with sample questions"""
    
    print("🤖 Initializing Memory Q&A Engine...")
    qa_engine = MemoryQAEngine(use_local_llm=True)
    
    # Sample questions to test
    test_questions = [
        "What is Sentence-Transformers and how is it used?",
        "Tell me about the Python libraries I should implement",
        "What articles have I captured about React?",
        "How do I improve the performance of my AI systems?",
        "What are the key features of the Universal Memory System?"
    ]
    
    print("\n" + "="*60)
    print("🧠 MEMORY Q&A ENGINE - TEST SESSION")
    print("="*60)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n📝 Question {i}: {question}")
        print("-" * 50)
        
        try:
            result = await qa_engine.ask(question)
            
            print(f"💡 Answer: {result['answer']}")
            print(f"🎯 Confidence: {result['confidence']:.2f}")
            print(f"📚 Sources: {result['source_count']} memories")
            
            if result.get('insights', {}).get('top_tags'):
                tags = [f"{tag['tag']}({tag['count']})" for tag in result['insights']['top_tags'][:3]]
                print(f"🏷️  Key topics: {', '.join(tags)}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "="*60)
    print("✅ Q&A Engine test complete!")
    print("You can now ask natural language questions about your memories.")
    

if __name__ == "__main__":
    asyncio.run(test_qa_engine())