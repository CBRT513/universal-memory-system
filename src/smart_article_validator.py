#!/usr/bin/env python3
"""
Smart Article Validator
Validates user classifications and sends proactive notifications for truly actionable content
"""

import json
import requests
import subprocess
from typing import Dict, List
import time

class SmartArticleValidator:
    def __init__(self):
        self.api_base = "http://localhost:8091"
        self.notification_cli = "/usr/local/share/universal-memory-system/src/notification_cli.py"
        
        # Keywords that indicate actionable content for YOUR specific work
        self.actionable_keywords = [
            # Your tools
            'claude code', 'subagent', 'mcp', 'mcp tools', 'model context protocol',
            'universal memory', 'ums', 'memory system',
            
            # Your tech stack
            'fastapi', 'swift', 'browser extension', 'chrome extension',
            'tailwind', 'react', 'vue', 'typescript',
            
            # Your goals
            'ai agent', 'llm integration', 'productivity tool', 'automation',
            'workflow optimization', 'development tool',
            
            # Action words
            'template', 'boilerplate', 'starter', 'example code',
            'implementation', 'tutorial', 'step-by-step', 'how to build'
        ]
        
        self.reference_keywords = [
            'theory', 'research', 'paper', 'study', 'analysis',
            'comparison', 'benchmark', 'survey', 'overview'
        ]
    
    def validate_classification(self, article: Dict) -> Dict:
        """
        Quick validation of user's classification
        Returns whether it agrees and why
        """
        
        content = article.get('content', '').lower()
        user_classification = article.get('metadata', {}).get('article_analysis', {}).get('classification', 'unknown')
        
        # Count keyword matches
        actionable_score = sum(1 for kw in self.actionable_keywords if kw in content)
        reference_score = sum(1 for kw in self.reference_keywords if kw in content)
        
        # Determine true classification
        true_classification = 'unknown'
        confidence = 0
        
        if actionable_score >= 3:
            true_classification = 'action_required'
            confidence = min(actionable_score * 20, 100)
        elif reference_score >= 2:
            true_classification = 'reference'
            confidence = min(reference_score * 25, 100)
        elif actionable_score >= 1:
            true_classification = 'potentially_actionable'
            confidence = 50
        else:
            true_classification = 'reference'
            confidence = 30
        
        # Check if we disagree with user
        disagrees = user_classification != true_classification
        
        result = {
            'user_classification': user_classification,
            'ai_classification': true_classification,
            'confidence': confidence,
            'disagrees': disagrees,
            'actionable_score': actionable_score,
            'reference_score': reference_score,
            'matched_keywords': [kw for kw in self.actionable_keywords if kw in content][:5]
        }
        
        # If this is highly actionable, prepare notification
        if actionable_score >= 3 and true_classification == 'action_required':
            result['should_notify'] = True
            result['notification'] = self.create_notification(article, result)
        
        return result
    
    def create_notification(self, article: Dict, validation: Dict) -> Dict:
        """Create notification for truly actionable content"""
        
        # Extract key info
        content_preview = article.get('content', '')[:200]
        matched = validation['matched_keywords']
        
        # Determine urgency
        if validation['actionable_score'] >= 5:
            priority = 'high'
            title = "🔥 Highly Actionable Article!"
        else:
            priority = 'normal'  
            title = "🎯 Actionable Article"
        
        # Build message
        message_parts = []
        
        if validation['disagrees']:
            message_parts.append(f"📍 Reclassified as actionable (was: {validation['user_classification']})")
        
        message_parts.append(f"🎯 Matched: {', '.join(matched[:3])}")
        
        if 'claude code' in ' '.join(matched).lower():
            message_parts.append("⚡ Claude Code related!")
        elif 'mcp' in ' '.join(matched).lower():
            message_parts.append("⚡ MCP tools related!")
        
        return {
            'title': title,
            'message': ' | '.join(message_parts),
            'priority': priority
        }
    
    def send_notification(self, notification: Dict):
        """Send desktop notification"""
        
        try:
            cmd = [
                "python3", self.notification_cli,
                "send", "cerion",
                notification['message'],
                "--title", notification['title'],
                "--priority", notification['priority']
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"📢 Notification sent: {notification['title']}")
            
        except Exception as e:
            print(f"Notification error: {e}")
    
    def validate_recent_articles(self, limit: int = 5):
        """Validate recently captured articles"""
        
        print("🔍 Validating recent article classifications...\n")
        
        # Get recent articles
        response = requests.get(f"{self.api_base}/api/memory/search?category=article&limit={limit}")
        
        if response.status_code != 200:
            print("Error fetching articles")
            return
        
        articles = response.json().get('results', [])
        
        for article in articles:
            print(f"Article: {article['id']}")
            
            # Validate classification
            validation = self.validate_classification(article)
            
            # Display results
            print(f"  User said: {validation['user_classification']}")
            print(f"  AI thinks: {validation['ai_classification']} (confidence: {validation['confidence']}%)")
            print(f"  Actionable score: {validation['actionable_score']}")
            
            if validation['matched_keywords']:
                print(f"  Matched: {', '.join(validation['matched_keywords'][:3])}")
            
            if validation['disagrees']:
                print(f"  ⚠️  DISAGREEMENT - AI suggests reclassification")
            
            if validation.get('should_notify'):
                print(f"  📢 Sending notification...")
                self.send_notification(validation['notification'])
            
            print()
    
    def monitor_new_articles(self):
        """Monitor for new articles in real-time"""
        
        print("👁️  Monitoring for new articles...")
        print("    (Press Ctrl+C to stop)\n")
        
        seen_articles = set()
        
        # Get initial articles
        response = requests.get(f"{self.api_base}/api/memory/search?category=article&limit=10")
        if response.status_code == 200:
            for article in response.json().get('results', []):
                seen_articles.add(article['id'])
        
        while True:
            try:
                time.sleep(10)  # Check every 10 seconds
                
                # Get latest articles
                response = requests.get(f"{self.api_base}/api/memory/search?category=article&limit=5")
                
                if response.status_code == 200:
                    articles = response.json().get('results', [])
                    
                    for article in articles:
                        if article['id'] not in seen_articles:
                            print(f"\n🆕 New article detected: {article['id'][:20]}...")
                            seen_articles.add(article['id'])
                            
                            # Validate immediately
                            validation = self.validate_classification(article)
                            
                            print(f"   Classification: {validation['ai_classification']}")
                            print(f"   Actionable score: {validation['actionable_score']}")
                            
                            if validation.get('should_notify'):
                                self.send_notification(validation['notification'])
                                print("   📢 Notification sent!")
                            
                            # If highly actionable, extract actions
                            if validation['actionable_score'] >= 4:
                                print("   🎯 Extracting action items...")
                                subprocess.run([
                                    "python3", 
                                    "/usr/local/share/universal-memory-system/src/article_action_extractor.py",
                                    article['id']
                                ], capture_output=True)
                
            except KeyboardInterrupt:
                print("\n👋 Stopping monitor...")
                break
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(5)

def main():
    import sys
    
    validator = SmartArticleValidator()
    
    if len(sys.argv) > 1 and sys.argv[1] == 'monitor':
        validator.monitor_new_articles()
    else:
        validator.validate_recent_articles()
        
        print("\n" + "="*50)
        print("To start real-time monitoring, run:")
        print("python3 smart_article_validator.py monitor")
        print("="*50)

if __name__ == "__main__":
    main()