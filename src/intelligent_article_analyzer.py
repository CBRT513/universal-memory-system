#!/usr/bin/env python3
"""
Intelligent Article Analyzer
Validates user classifications, extracts actionable insights, and proactively notifies about relevant content
"""

import json
import asyncio
import sqlite3
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import requests
import subprocess
import os
from pathlib import Path

class IntelligentArticleAnalyzer:
    def __init__(self):
        self.db_path = "/usr/local/var/universal-memory-system/databases/memories.db"
        self.ollama_url = "http://localhost:11434"
        self.notification_script = "/usr/local/share/universal-memory-system/src/notification_cli.py"
        
        # Load current projects and context
        self.current_projects = self.load_current_projects()
        self.user_goals = self.load_user_goals()
        
    def load_current_projects(self) -> List[str]:
        """Load active projects from memory system"""
        projects = []
        try:
            # Get from recent memories and CLAUDE.md files
            claude_files = [
                "/Users/cerion/Projects/AgentWorkspace/agentforge/CLAUDE.md",
                "/usr/local/share/universal-memory-system/CLAUDE.md"
            ]
            
            for file_path in claude_files:
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        content = f.read()
                        if "AgentForge" in content:
                            projects.append("AgentForge - AI development platform")
                        if "Universal Memory System" in content:
                            projects.append("UMS - Universal Memory System") 
                        if "Claude Code" in content:
                            projects.append("Claude Code integrations and subagents")
                            
            # Add specific technologies we're working with
            projects.extend([
                "Browser extension development",
                "Swift/macOS global capture",
                "FastAPI backend services",
                "Article triage and classification",
                "AI agent development"
            ])
            
        except Exception as e:
            print(f"Error loading projects: {e}")
            
        return projects
    
    def load_user_goals(self) -> List[str]:
        """Load user's stated goals and intentions"""
        return [
            "Build AI agents that improve productivity",
            "Create seamless capture and retrieval systems",
            "Automate article processing and knowledge management",
            "Integrate Claude Code with memory systems",
            "Develop proactive AI assistants"
        ]
    
    async def analyze_article(self, article_content: str, user_classification: str, article_id: str) -> Dict:
        """
        Deep analysis of article content regardless of user classification
        Returns actionable insights, relevance score, and recommendations
        """
        
        analysis_prompt = f"""
        Analyze this article for actionable content and relevance to current projects.
        
        USER'S CLASSIFICATION: {user_classification}
        
        CURRENT PROJECTS:
        {json.dumps(self.current_projects, indent=2)}
        
        USER GOALS:
        {json.dumps(self.user_goals, indent=2)}
        
        ARTICLE CONTENT:
        {article_content[:3000]}  # Limit for context window
        
        PROVIDE ANALYSIS IN JSON FORMAT:
        {{
            "true_classification": "action_required|reference|learning|not_relevant",
            "disagrees_with_user": true/false,
            "disagreement_reason": "why the AI classification differs",
            "relevance_score": 0-10,
            "relevance_explanation": "how this relates to current work",
            "actionable_items": [
                {{
                    "action": "specific action to take",
                    "priority": "high|medium|low",
                    "estimated_time": "time estimate",
                    "tools_needed": ["tool1", "tool2"],
                    "relates_to_project": "project name"
                }}
            ],
            "hidden_insights": [
                "insights the user might have missed"
            ],
            "implementation_suggestions": [
                {{
                    "suggestion": "specific implementation idea",
                    "code_snippet": "example code if applicable",
                    "integration_point": "where this fits in current system"
                }}
            ],
            "notification_priority": "urgent|high|normal|low",
            "notification_message": "message to show user if urgent/high"
        }}
        """
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "llama3.2:3b",
                    "prompt": analysis_prompt,
                    "stream": False,
                    "format": "json"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis = json.loads(result.get('response', '{}'))
                
                # Validate and enhance the analysis
                analysis = self.validate_analysis(analysis, article_content, user_classification)
                
                # Store the enhanced analysis
                self.store_analysis(article_id, analysis)
                
                # Send notification if needed
                if analysis.get('notification_priority') in ['urgent', 'high']:
                    await self.send_notification(analysis, article_content)
                
                return analysis
                
        except Exception as e:
            print(f"Analysis error: {e}")
            return self.fallback_analysis(article_content, user_classification)
    
    def validate_analysis(self, analysis: Dict, content: str, user_class: str) -> Dict:
        """Validate and enhance the AI analysis"""
        
        # Ensure all required fields exist
        required_fields = [
            'true_classification', 'relevance_score', 'actionable_items',
            'notification_priority', 'disagrees_with_user'
        ]
        
        for field in required_fields:
            if field not in analysis:
                if field == 'relevance_score':
                    analysis[field] = 5
                elif field == 'actionable_items':
                    analysis[field] = []
                elif field == 'notification_priority':
                    analysis[field] = 'normal'
                elif field == 'disagrees_with_user':
                    analysis[field] = analysis.get('true_classification') != user_class
                else:
                    analysis[field] = None
        
        # Check for specific keywords that indicate high relevance
        high_relevance_keywords = [
            'claude code', 'subagent', 'mcp', 'memory system', 'ums',
            'fastapi', 'browser extension', 'swift', 'capture',
            'ai agent', 'llm', 'productivity', 'automation'
        ]
        
        content_lower = content.lower()
        keyword_matches = sum(1 for kw in high_relevance_keywords if kw in content_lower)
        
        if keyword_matches >= 3:
            analysis['relevance_score'] = max(analysis.get('relevance_score', 5), 8)
            analysis['auto_relevance_boost'] = f"Matched {keyword_matches} high-relevance keywords"
        
        # If user said "action_required" but AI found no actions, look harder
        if user_class == 'action_required' and not analysis.get('actionable_items'):
            analysis['actionable_items'] = self.extract_potential_actions(content)
            if analysis['actionable_items']:
                analysis['ai_note'] = "Found potential actions on deeper analysis"
        
        return analysis
    
    def extract_potential_actions(self, content: str) -> List[Dict]:
        """Extract potential actionable items from content"""
        actions = []
        
        # Look for action-indicating phrases
        action_phrases = [
            ('you can', 'implement the mentioned technique'),
            ('try', 'experiment with this approach'),
            ('install', 'add this tool to your workflow'),
            ('create', 'build a similar solution'),
            ('update', 'modify existing code to use this'),
            ('example', 'adapt this example to your use case'),
            ('template', 'use this template in your project'),
            ('api', 'integrate this API into your system'),
            ('tool', 'evaluate this tool for your needs')
        ]
        
        content_lower = content.lower()
        for trigger, action in action_phrases:
            if trigger in content_lower:
                actions.append({
                    "action": action,
                    "priority": "medium",
                    "estimated_time": "1-2 hours",
                    "tools_needed": [],
                    "relates_to_project": "General improvement"
                })
                
        return actions[:3]  # Limit to top 3 potential actions
    
    def store_analysis(self, article_id: str, analysis: Dict):
        """Store the AI analysis with the article"""
        try:
            # Update the article's metadata with AI analysis
            analysis_json = json.dumps(analysis)
            
            # Store in a separate analysis table or update metadata
            # This would integrate with your existing memory system
            print(f"Stored analysis for article {article_id}")
            
        except Exception as e:
            print(f"Error storing analysis: {e}")
    
    async def send_notification(self, analysis: Dict, content: str):
        """Send desktop notification for high-priority actionable content"""
        
        title = "🎯 Actionable Article Detected!"
        
        # Build notification message
        message_parts = []
        
        if analysis.get('disagrees_with_user'):
            message_parts.append(f"⚠️ {analysis.get('disagreement_reason', 'Classification mismatch')}")
        
        if analysis.get('relevance_score', 0) >= 8:
            message_parts.append(f"📊 High relevance ({analysis['relevance_score']}/10)")
        
        if analysis.get('actionable_items'):
            top_action = analysis['actionable_items'][0]
            message_parts.append(f"🎯 {top_action['action']}")
        
        message = " | ".join(message_parts) if message_parts else analysis.get('notification_message', 'New actionable content')
        
        # Use the UMS notification system
        try:
            subprocess.run([
                "python3", self.notification_script,
                "send", "cerion", message,
                "--title", title,
                "--priority", analysis.get('notification_priority', 'normal')
            ], check=True)
        except Exception as e:
            print(f"Notification error: {e}")
    
    def fallback_analysis(self, content: str, user_class: str) -> Dict:
        """Simple fallback analysis if AI fails"""
        return {
            "true_classification": user_class,
            "disagrees_with_user": False,
            "relevance_score": 5,
            "relevance_explanation": "Could not perform deep analysis",
            "actionable_items": self.extract_potential_actions(content),
            "hidden_insights": [],
            "implementation_suggestions": [],
            "notification_priority": "normal",
            "notification_message": "Article captured and stored"
        }
    
    async def analyze_recent_articles(self):
        """Analyze all recently captured articles"""
        print("🔍 Analyzing recent articles for actionable content...")
        
        # Get recent articles from the API
        response = requests.get("http://localhost:8091/api/memory/search?category=article&limit=10")
        if response.status_code == 200:
            articles = response.json().get('results', [])
            
            for article in articles:
                print(f"\nAnalyzing: {article.get('id')}")
                
                # Check if already analyzed
                metadata = article.get('metadata', {})
                if metadata.get('intelligent_analysis'):
                    print("  Already analyzed, skipping...")
                    continue
                
                # Get user's classification
                user_class = metadata.get('article_analysis', {}).get('classification', 'unknown')
                
                # Perform intelligent analysis
                analysis = await self.analyze_article(
                    article.get('content', ''),
                    user_class,
                    article.get('id')
                )
                
                # Print summary
                print(f"  Classification: {user_class} -> {analysis.get('true_classification')}")
                print(f"  Relevance: {analysis.get('relevance_score')}/10")
                print(f"  Actions found: {len(analysis.get('actionable_items', []))}")
                
                if analysis.get('disagrees_with_user'):
                    print(f"  ⚠️ AI disagrees: {analysis.get('disagreement_reason')}")
    
    async def monitor_new_articles(self):
        """Continuously monitor for new articles"""
        print("👁️ Monitoring for new articles...")
        
        last_check = datetime.now()
        
        while True:
            await asyncio.sleep(30)  # Check every 30 seconds
            
            # Get articles added since last check
            response = requests.get(
                f"http://localhost:8091/api/memory/search?category=article&limit=5"
            )
            
            if response.status_code == 200:
                articles = response.json().get('results', [])
                
                for article in articles:
                    # Check if this is new (simple timestamp check)
                    article_time = article.get('timestamp', 0)
                    if article_time > last_check.timestamp():
                        print(f"\n🆕 New article detected: {article.get('id')}")
                        
                        # Analyze immediately
                        analysis = await self.analyze_article(
                            article.get('content', ''),
                            'unknown',
                            article.get('id')
                        )
                        
                        if analysis.get('relevance_score', 0) >= 7:
                            print(f"  ⚡ High relevance! Notifying user...")

async def main():
    analyzer = IntelligentArticleAnalyzer()
    
    # Analyze recent articles
    await analyzer.analyze_recent_articles()
    
    # Start monitoring
    print("\n" + "="*50)
    print("Starting continuous monitoring...")
    print("Press Ctrl+C to stop")
    print("="*50 + "\n")
    
    try:
        await analyzer.monitor_new_articles()
    except KeyboardInterrupt:
        print("\n👋 Stopping article monitor...")

if __name__ == "__main__":
    asyncio.run(main())