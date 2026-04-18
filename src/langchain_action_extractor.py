#!/usr/bin/env python3
"""
LangChain-based Action Extraction for Articles
Automatically extracts concrete action items, implementation steps, and tasks from articles.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from pydantic import BaseModel, Field
from typing import List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for structured output
class ActionItem(BaseModel):
    """Represents a single action item extracted from an article"""
    action: str = Field(description="The specific action to take")
    details: str = Field(description="Detailed description of how to implement")
    priority: str = Field(description="Priority level: high, medium, or low")
    effort: str = Field(description="Effort required: small, medium, large")
    technologies: List[str] = Field(default=[], description="Technologies/tools involved")
    code_example: Optional[str] = Field(default=None, description="Code example if applicable")

class ImplementationPlan(BaseModel):
    """Complete implementation plan extracted from an article"""
    summary: str = Field(description="Brief summary of the article's main points")
    key_concepts: List[str] = Field(description="Key concepts and technologies discussed")
    action_items: List[ActionItem] = Field(description="Concrete action items to implement")
    prerequisites: List[str] = Field(default=[], description="Prerequisites or dependencies")
    estimated_time: str = Field(description="Estimated total implementation time")
    recommended_project: Optional[str] = Field(default=None, description="Suggested project to implement in")

class LangChainActionExtractor:
    """Extract actionable items from articles using LangChain"""
    
    def __init__(self, use_local_llm: bool = True):
        """
        Initialize the action extractor
        
        Args:
            use_local_llm: If True, use Ollama; if False, use OpenAI (requires API key)
        """
        self.use_local_llm = use_local_llm
        self.llm = self._initialize_llm()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=3000,
            chunk_overlap=200
        )
        
        # Output parser for structured extraction
        self.output_parser = PydanticOutputParser(pydantic_object=ImplementationPlan)
        self.fixing_parser = OutputFixingParser.from_llm(parser=self.output_parser, llm=self.llm)
        
        # Create the extraction prompt
        self.extraction_prompt = PromptTemplate(
            template="""You are an expert at extracting actionable insights from technical articles.
            
Analyze the following article and extract concrete action items that can be implemented.

Article Content:
{article_content}

{format_instructions}

Focus on:
1. Specific implementation steps that can be taken
2. Code patterns or techniques that can be applied
3. Tools or libraries that should be explored
4. Best practices that should be adopted
5. Problems that can be solved using the article's content

Be specific and practical. Each action item should be something a developer can actually do.
""",
            input_variables=["article_content"],
            partial_variables={"format_instructions": self.output_parser.get_format_instructions()}
        )
        
        # Create the extraction chain
        self.extraction_chain = LLMChain(
            llm=self.llm,
            prompt=self.extraction_prompt
        )
    
    def _initialize_llm(self):
        """Initialize the LLM (Ollama or OpenAI)"""
        if self.use_local_llm:
            try:
                from langchain_community.llms import Ollama
                logger.info("Using Ollama for action extraction")
                return Ollama(
                    model="llama3.2:3b",  # Use same model as article triage
                    temperature=0.3,
                    num_predict=2000
                )
            except Exception as e:
                logger.error(f"Failed to initialize Ollama: {e}")
                logger.info("Falling back to mock LLM")
                return self._create_mock_llm()
        else:
            # Use OpenAI (requires API key)
            try:
                from langchain_openai import ChatOpenAI
                import os
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY not set")
                return ChatOpenAI(
                    model="gpt-4o-mini",
                    temperature=0.3,
                    api_key=api_key
                )
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI: {e}")
                return self._create_mock_llm()
    
    def _create_mock_llm(self):
        """Create a mock LLM for testing when real LLM is not available"""
        from langchain.llms.base import LLM
        from typing import Any, List, Optional
        
        class MockLLM(LLM):
            @property
            def _llm_type(self) -> str:
                return "mock"
            
            def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
                # Return a valid JSON response that matches our schema
                return json.dumps({
                    "summary": "Article about implementing AI solutions",
                    "key_concepts": ["AI", "automation", "implementation"],
                    "action_items": [
                        {
                            "action": "Implement the discussed solution",
                            "details": "Follow the article's implementation guide",
                            "priority": "high",
                            "effort": "medium",
                            "technologies": ["Python", "AI"],
                            "code_example": "# Example code from article"
                        }
                    ],
                    "prerequisites": ["Python knowledge", "Basic AI understanding"],
                    "estimated_time": "2-3 hours",
                    "recommended_project": "current-project"
                })
        
        return MockLLM()
    
    def extract_actions(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract action items from an article
        
        Args:
            article: Dictionary containing article content and metadata
            
        Returns:
            Dictionary containing extracted actions and implementation plan
        """
        try:
            # Get article content
            content = article.get("content", "")
            if not content:
                logger.warning("No content in article")
                return self._empty_result()
            
            # For long articles, use the most relevant chunks
            if len(content) > 3000:
                chunks = self.text_splitter.split_text(content)
                # Focus on first and last chunks (intro and conclusion often have key points)
                relevant_content = f"{chunks[0]}\n\n[...middle content...]\n\n{chunks[-1] if len(chunks) > 1 else ''}"
            else:
                relevant_content = content
            
            # Extract actions using LangChain
            try:
                raw_output = self.extraction_chain.run(article_content=relevant_content)
                
                # Parse the output
                try:
                    implementation_plan = self.output_parser.parse(raw_output)
                except Exception as parse_error:
                    logger.warning(f"Parse error, attempting to fix: {parse_error}")
                    implementation_plan = self.fixing_parser.parse(raw_output)
                
                # Convert to dictionary
                result = implementation_plan.dict()
                
            except Exception as chain_error:
                logger.error(f"Chain execution error: {chain_error}")
                # Fallback to basic extraction
                result = self._basic_extraction(content)
            
            # Add metadata
            result["article_id"] = article.get("id")
            result["article_title"] = article.get("title", "Unknown")
            result["extraction_timestamp"] = datetime.now().isoformat()
            result["extraction_method"] = "langchain" if not isinstance(self.llm._llm_type, str) or self.llm._llm_type != "mock" else "mock"
            
            # Calculate actionability score
            result["actionability_score"] = self._calculate_actionability_score(result)
            
            logger.info(f"Extracted {len(result.get('action_items', []))} action items from article")
            return result
            
        except Exception as e:
            logger.error(f"Error extracting actions: {e}")
            return self._empty_result()
    
    def _basic_extraction(self, content: str) -> Dict[str, Any]:
        """Basic extraction when LLM fails"""
        # Simple keyword-based extraction
        keywords = {
            "implement": "high",
            "try": "medium",
            "consider": "low",
            "install": "high",
            "create": "high",
            "build": "high",
            "use": "medium"
        }
        
        action_items = []
        lines = content.split('\n')
        
        for line in lines[:50]:  # Check first 50 lines
            line_lower = line.lower()
            for keyword, priority in keywords.items():
                if keyword in line_lower and len(line) > 20:
                    action_items.append({
                        "action": line.strip()[:100],
                        "details": "Extracted from article text",
                        "priority": priority,
                        "effort": "medium",
                        "technologies": [],
                        "code_example": None
                    })
                    break
            
            if len(action_items) >= 5:  # Limit to 5 items
                break
        
        return {
            "summary": "Article content analyzed for actionable items",
            "key_concepts": [],
            "action_items": action_items,
            "prerequisites": [],
            "estimated_time": "varies",
            "recommended_project": None
        }
    
    def _calculate_actionability_score(self, result: Dict[str, Any]) -> float:
        """Calculate how actionable the extracted content is (0-10)"""
        score = 0.0
        
        # Points for action items
        action_items = result.get("action_items", [])
        score += min(len(action_items) * 2, 6)  # Up to 6 points for actions
        
        # Points for code examples
        has_code = any(item.get("code_example") for item in action_items)
        if has_code:
            score += 2
        
        # Points for specific technologies
        all_techs = set()
        for item in action_items:
            all_techs.update(item.get("technologies", []))
        score += min(len(all_techs) * 0.5, 2)  # Up to 2 points for technologies
        
        return min(score, 10.0)
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result structure"""
        return {
            "summary": "No actionable content extracted",
            "key_concepts": [],
            "action_items": [],
            "prerequisites": [],
            "estimated_time": "0",
            "recommended_project": None,
            "actionability_score": 0.0,
            "extraction_timestamp": datetime.now().isoformat(),
            "extraction_method": "none"
        }
    
    def create_tasks_from_actions(self, implementation_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert action items into task format for todo systems
        
        Args:
            implementation_plan: The extracted implementation plan
            
        Returns:
            List of tasks ready for todo systems
        """
        tasks = []
        
        for idx, action_item in enumerate(implementation_plan.get("action_items", [])):
            task = {
                "title": action_item["action"],
                "description": action_item["details"],
                "priority": action_item["priority"],
                "effort": action_item["effort"],
                "tags": action_item.get("technologies", []),
                "source": f"Article: {implementation_plan.get('article_title', 'Unknown')}",
                "created_at": datetime.now().isoformat(),
                "status": "pending"
            }
            
            # Add code example as attachment if present
            if action_item.get("code_example"):
                task["code_snippet"] = action_item["code_example"]
            
            tasks.append(task)
        
        return tasks


def test_extraction():
    """Test the action extraction with sample article"""
    
    # Sample article (from the 7 Python Libraries article)
    sample_article = {
        "id": "test_001",
        "title": "7 Python Libraries So AI-Ready",
        "content": """
        Sentence-Transformers — Text Meaning in a Single Vector
        When you need to know if two pieces of text mean the same thing, you don't need to spin up BERT from scratch — you just need this.

        from sentence_transformers import SentenceTransformer, util
        
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings = model.encode(["Python is great", "I love programming in Python"])
        similarity = util.cos_sim(embeddings[0], embeddings[1])
        print(similarity)
        
        It's the glue for everything semantic — clustering, recommendation, intent detection — without you ever seeing a training loop.
        
        Implementation steps:
        1. Install sentence-transformers: pip install sentence-transformers
        2. Choose an appropriate model for your use case
        3. Generate embeddings for your text data
        4. Use embeddings for similarity search, clustering, or classification
        5. Integrate with your existing search or recommendation system
        """
    }
    
    # Initialize extractor
    extractor = LangChainActionExtractor(use_local_llm=True)
    
    # Extract actions
    print("🔍 Extracting actions from article...")
    result = extractor.extract_actions(sample_article)
    
    # Display results
    print("\n📋 Extraction Results:")
    print(f"Summary: {result['summary']}")
    print(f"Actionability Score: {result['actionability_score']}/10")
    print(f"Estimated Time: {result['estimated_time']}")
    
    print("\n🎯 Action Items:")
    for i, action in enumerate(result['action_items'], 1):
        print(f"{i}. {action['action']}")
        print(f"   Priority: {action['priority']} | Effort: {action['effort']}")
        if action.get('technologies'):
            print(f"   Technologies: {', '.join(action['technologies'])}")
    
    # Convert to tasks
    tasks = extractor.create_tasks_from_actions(result)
    print(f"\n✅ Created {len(tasks)} tasks from action items")
    
    return result


if __name__ == "__main__":
    test_extraction()