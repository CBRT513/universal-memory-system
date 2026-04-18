#!/usr/bin/env python3
"""
Article Action Extractor
Extracts concrete, implementable actions from articles and creates TODO items
"""

import json
import requests
from typing import List, Dict, Optional
import subprocess
import os
from datetime import datetime

class ArticleActionExtractor:
    def __init__(self):
        self.ollama_url = "http://localhost:11434"
        self.api_base = "http://localhost:8091"
        
    def extract_actions(self, article_content: str, article_title: str = "") -> Dict:
        """
        Extract concrete, implementable actions from an article
        Returns structured action items with implementation details
        """
        
        prompt = f"""
        Extract ONLY concrete, implementable actions from this article.
        Focus on things that can actually be coded, configured, or built.
        
        ARTICLE TITLE: {article_title}
        
        ARTICLE CONTENT:
        {article_content[:4000]}
        
        For each action, determine:
        1. Is this something that can actually be implemented in code?
        2. What specific files, functions, or systems would need to be created/modified?
        3. What is the concrete deliverable?
        
        Return ONLY actions that meet these criteria:
        - Has a clear implementation path
        - Results in actual code, configuration, or system changes  
        - Is relevant to software development, AI, or automation
        - Can be completed in a defined timeframe
        
        SKIP actions that are:
        - Vague concepts or theories
        - General advice without specifics
        - Marketing or promotional content
        - Things that require external services we don't have
        
        FORMAT YOUR RESPONSE AS JSON:
        {{
            "article_summary": "2-3 sentence summary of article's main point",
            "implementation_relevant": true/false,
            "concrete_actions": [
                {{
                    "action_title": "Build X feature/system",
                    "description": "Specific description of what to build",
                    "implementation_steps": [
                        "Step 1: Create file X",
                        "Step 2: Implement function Y",
                        "Step 3: Test with Z"
                    ],
                    "deliverables": [
                        "Working X feature",
                        "Documentation for Y"
                    ],
                    "estimated_hours": 2,
                    "required_tools": ["tool1", "tool2"],
                    "code_example": "Sample code snippet if applicable",
                    "integration_point": "Where this fits in existing system",
                    "priority_score": 1-10,
                    "priority_reason": "Why this priority"
                }}
            ],
            "key_insights": [
                "Non-actionable but valuable insights from the article"
            ],
            "technologies_mentioned": ["tech1", "tech2"],
            "immediate_action": "The ONE thing to do right now if anything"
        }}
        """
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "llama3.2:3b",
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                actions = json.loads(result.get('response', '{}'))
                
                # Validate and enhance extracted actions
                actions = self.validate_actions(actions, article_content)
                
                return actions
                
        except Exception as e:
            print(f"Error extracting actions: {e}")
            return self.fallback_extraction(article_content)
    
    def validate_actions(self, actions: Dict, content: str) -> Dict:
        """Validate extracted actions are truly implementable"""
        
        if not actions.get('concrete_actions'):
            actions['concrete_actions'] = []
        
        # Filter out vague actions
        valid_actions = []
        for action in actions.get('concrete_actions', []):
            if self.is_action_valid(action):
                valid_actions.append(action)
        
        actions['concrete_actions'] = valid_actions
        
        # Add validation metadata
        actions['validation'] = {
            'validated_at': datetime.now().isoformat(),
            'action_count': len(valid_actions),
            'is_actionable': len(valid_actions) > 0
        }
        
        return actions
    
    def is_action_valid(self, action: Dict) -> bool:
        """Check if an action is truly implementable"""
        
        # Must have clear deliverables
        if not action.get('deliverables'):
            return False
        
        # Must have implementation steps
        if not action.get('implementation_steps'):
            return False
        
        # Must be specific (not vague)
        vague_terms = ['consider', 'think about', 'explore', 'research']
        action_text = action.get('action_title', '').lower()
        if any(term in action_text for term in vague_terms):
            return False
        
        return True
    
    def create_todo_items(self, actions: Dict, article_id: str) -> List[str]:
        """Create TODO items from extracted actions"""
        
        todos = []
        
        for action in actions.get('concrete_actions', []):
            # Create detailed TODO
            todo = {
                'title': action['action_title'],
                'description': action['description'],
                'steps': action['implementation_steps'],
                'estimated_hours': action.get('estimated_hours', 2),
                'priority': action.get('priority_score', 5),
                'source_article': article_id,
                'created_at': datetime.now().isoformat()
            }
            
            # Store TODO in memory system
            self.store_todo(todo)
            todos.append(todo['title'])
        
        return todos
    
    def store_todo(self, todo: Dict):
        """Store TODO item in memory system"""
        
        try:
            response = requests.post(
                f"{self.api_base}/api/memory/store",
                json={
                    'content': json.dumps(todo, indent=2),
                    'category': 'todo',
                    'tags': ['extracted-action', 'auto-generated', 'from-article'],
                    'importance': todo.get('priority', 5),
                    'metadata': {
                        'todo_type': 'extracted_action',
                        'source': todo.get('source_article'),
                        'estimated_hours': todo.get('estimated_hours')
                    }
                }
            )
            
            if response.status_code == 200:
                print(f"✅ Created TODO: {todo['title']}")
                
        except Exception as e:
            print(f"Error storing TODO: {e}")
    
    def fallback_extraction(self, content: str) -> Dict:
        """Simple extraction if AI fails"""
        
        # Look for common action patterns
        actions = []
        
        action_keywords = [
            ('install', 'Install mentioned tool or library'),
            ('create', 'Create mentioned component or feature'),
            ('implement', 'Implement described functionality'),
            ('build', 'Build described system'),
            ('add', 'Add mentioned feature to existing system')
        ]
        
        content_lower = content.lower()
        for keyword, action_template in action_keywords:
            if keyword in content_lower:
                actions.append({
                    'action_title': action_template,
                    'description': f"Review article for {keyword} instructions",
                    'implementation_steps': ["Review article", "Plan implementation", "Execute"],
                    'deliverables': ["Implemented feature"],
                    'estimated_hours': 4,
                    'priority_score': 5
                })
                break
        
        return {
            'article_summary': 'Article requires manual review',
            'implementation_relevant': len(actions) > 0,
            'concrete_actions': actions,
            'key_insights': [],
            'validation': {
                'is_fallback': True,
                'action_count': len(actions)
            }
        }
    
    def generate_implementation_plan(self, action: Dict) -> str:
        """Generate detailed implementation plan for an action"""
        
        plan = f"""
# Implementation Plan: {action['action_title']}

## Overview
{action['description']}

## Steps
"""
        for i, step in enumerate(action.get('implementation_steps', []), 1):
            plan += f"{i}. {step}\n"
        
        plan += f"""

## Deliverables
"""
        for deliverable in action.get('deliverables', []):
            plan += f"- {deliverable}\n"
        
        if action.get('code_example'):
            plan += f"""

## Code Example
```
{action['code_example']}
```
"""
        
        plan += f"""

## Integration Point
{action.get('integration_point', 'To be determined')}

## Estimated Time
{action.get('estimated_hours', 'Unknown')} hours

## Priority
{action.get('priority_score', 5)}/10 - {action.get('priority_reason', 'No reason provided')}
"""
        
        return plan

async def analyze_article_for_actions(article_id: str):
    """Analyze a specific article and extract actions"""
    
    extractor = ArticleActionExtractor()
    
    # Get article from memory system
    response = requests.get(f"http://localhost:8091/api/memory/search?id={article_id}")
    
    if response.status_code == 200:
        results = response.json().get('results', [])
        if results:
            article = results[0]
            print(f"\n📄 Analyzing article: {article_id}")
            
            # Extract actions
            actions = extractor.extract_actions(
                article.get('content', ''),
                article_id
            )
            
            # Display results
            print(f"\n📊 Analysis Results:")
            print(f"  Implementation Relevant: {actions.get('implementation_relevant')}")
            print(f"  Concrete Actions Found: {len(actions.get('concrete_actions', []))}")
            
            if actions.get('concrete_actions'):
                print("\n🎯 Extracted Actions:")
                for i, action in enumerate(actions['concrete_actions'], 1):
                    print(f"\n  {i}. {action['action_title']}")
                    print(f"     Priority: {action.get('priority_score')}/10")
                    print(f"     Time: {action.get('estimated_hours')} hours")
                    print(f"     Steps: {len(action.get('implementation_steps', []))}")
                
                # Create TODOs
                todos = extractor.create_todo_items(actions, article_id)
                print(f"\n✅ Created {len(todos)} TODO items")
                
                # Generate implementation plan for top action
                if actions['concrete_actions']:
                    top_action = actions['concrete_actions'][0]
                    plan = extractor.generate_implementation_plan(top_action)
                    
                    # Save plan
                    plan_file = f"/tmp/implementation_plan_{article_id}.md"
                    with open(plan_file, 'w') as f:
                        f.write(plan)
                    print(f"\n📝 Implementation plan saved to: {plan_file}")
                    
                    # Show immediate action
                    if actions.get('immediate_action'):
                        print(f"\n⚡ IMMEDIATE ACTION: {actions['immediate_action']}")
            else:
                print("\n📚 This appears to be reference material without concrete actions")
                if actions.get('key_insights'):
                    print("\n💡 Key Insights:")
                    for insight in actions['key_insights']:
                        print(f"  - {insight}")

if __name__ == "__main__":
    import asyncio
    import sys
    
    if len(sys.argv) > 1:
        article_id = sys.argv[1]
        asyncio.run(analyze_article_for_actions(article_id))
    else:
        print("Usage: python3 article_action_extractor.py <article_id>")
        print("\nAnalyzing most recent article...")
        
        # Get most recent article
        response = requests.get("http://localhost:8091/api/memory/search?category=article&limit=1")
        if response.status_code == 200:
            results = response.json().get('results', [])
            if results:
                article_id = results[0]['id']
                asyncio.run(analyze_article_for_actions(article_id))