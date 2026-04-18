#!/usr/bin/env python3
"""
Article Analysis Crew - Multiple specialized agents working together
Based on CrewAI patterns but using your existing tools
"""

import json
import asyncio
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import sys
import os

# Import your existing agents
sys.path.append('/usr/local/share/universal-memory-system/src')
from smart_article_validator import SmartArticleValidator
from article_action_extractor import ArticleActionExtractor

class ArticleAnalysisCrew:
    """
    Coordinates multiple article analysis agents with shared memory
    Implements CrewAI patterns: Crew, Agents, Tasks, Tools, Memory, Process
    """
    
    def __init__(self):
        # Your existing agents become crew members
        self.validator_agent = SmartArticleValidator()
        self.extractor_agent = ArticleActionExtractor()
        
        # Shared context between agents (CrewAI pattern)
        self.shared_memory = {}
        self.api_base = "http://localhost:8091"
        
        # Agent roles and capabilities
        self.agent_roles = {
            'validator': {
                'agent': self.validator_agent,
                'role': 'Classification Validator',
                'goal': 'Ensure articles are correctly classified',
                'backstory': 'Expert at identifying actionable content'
            },
            'extractor': {
                'agent': self.extractor_agent,
                'role': 'Action Extractor',
                'goal': 'Extract concrete implementation tasks',
                'backstory': 'Specialist in finding implementable actions'
            },
            'analyzer': {
                'agent': None,  # Will use inline analysis
                'role': 'Deep Analyzer',
                'goal': 'Find hidden insights and patterns',
                'backstory': 'Expert at connecting concepts to projects'
            }
        }
        
        # Process configuration (sequential or parallel)
        self.process_type = 'sequential'  # Can be 'parallel' for faster processing
    
    async def process_article(self, article_id: str) -> Dict:
        """
        Process article through all agents in crew
        Each agent builds on previous agent's work
        """
        
        print(f"\n🚢 Article Analysis Crew Starting")
        print(f"   Article ID: {article_id}")
        print(f"   Process: {self.process_type}")
        print(f"   Crew Members: {len(self.agent_roles)}")
        
        # Get article from memory
        article = await self.fetch_article(article_id)
        if not article:
            return {'error': 'Article not found'}
        
        self.shared_memory['article'] = article
        
        # Phase 1: Validation Agent
        print("\n🤖 Validator Agent working...")
        validation_result = await self.run_validator_agent(article)
        self.shared_memory['validation'] = validation_result
        
        # Phase 2: Extractor Agent (only if actionable)
        if validation_result.get('actionable_score', 0) >= 3:
            print("🤖 Extractor Agent working...")
            extraction_result = await self.run_extractor_agent(article)
            self.shared_memory['extraction'] = extraction_result
        else:
            print("⏭️  Skipping Extractor (not actionable enough)")
            self.shared_memory['extraction'] = None
        
        # Phase 3: Analyzer Agent (synthesis)
        print("🤖 Analyzer Agent working...")
        analysis_result = await self.run_analyzer_agent()
        self.shared_memory['analysis'] = analysis_result
        
        # Generate crew consensus report
        consensus = self.generate_crew_consensus()
        
        # Take action based on consensus
        await self.execute_crew_decisions(consensus)
        
        return consensus
    
    async def fetch_article(self, article_id: str) -> Optional[Dict]:
        """Fetch article from memory system"""
        try:
            response = requests.get(
                f"{self.api_base}/api/memory/search",
                params={'id': article_id}
            )
            
            if response.status_code == 200:
                results = response.json().get('results', [])
                if results:
                    return results[0]
        except Exception as e:
            print(f"Error fetching article: {e}")
        
        return None
    
    async def run_validator_agent(self, article: Dict) -> Dict:
        """Run validation agent"""
        try:
            # Use existing validator
            validation = self.validator_agent.validate_classification(article)
            
            # Enhance with agent perspective
            validation['agent_assessment'] = {
                'confidence': validation.get('confidence', 0),
                'should_reclassify': validation.get('disagrees', False),
                'key_signals': validation.get('matched_keywords', [])
            }
            
            print(f"   ✓ Classification: {validation.get('ai_classification')}")
            print(f"   ✓ Confidence: {validation.get('confidence')}%")
            
            return validation
            
        except Exception as e:
            print(f"   ✗ Validator error: {e}")
            return {'error': str(e)}
    
    async def run_extractor_agent(self, article: Dict) -> Dict:
        """Run action extractor agent"""
        try:
            # Use existing extractor
            actions = self.extractor_agent.extract_actions(
                article.get('content', ''),
                article.get('id', '')
            )
            
            # Filter for truly implementable actions
            concrete_actions = [
                action for action in actions.get('concrete_actions', [])
                if action.get('deliverables') and action.get('implementation_steps')
            ]
            
            actions['filtered_actions'] = concrete_actions
            actions['action_count'] = len(concrete_actions)
            
            print(f"   ✓ Actions found: {len(concrete_actions)}")
            
            if concrete_actions:
                print(f"   ✓ Top action: {concrete_actions[0].get('action_title')}")
            
            return actions
            
        except Exception as e:
            print(f"   ✗ Extractor error: {e}")
            return {'error': str(e)}
    
    async def run_analyzer_agent(self) -> Dict:
        """
        Analyzer agent synthesizes findings from other agents
        This is where the crew coordination shines
        """
        
        validation = self.shared_memory.get('validation', {})
        extraction = self.shared_memory.get('extraction', {})
        article = self.shared_memory.get('article', {})
        
        analysis = {
            'synthesis_timestamp': datetime.now().isoformat(),
            'crew_findings': {}
        }
        
        # Synthesize validation findings
        if validation:
            analysis['crew_findings']['classification'] = {
                'user_said': validation.get('user_classification'),
                'ai_believes': validation.get('ai_classification'),
                'confidence': validation.get('confidence'),
                'agreement': not validation.get('disagrees', False)
            }
        
        # Synthesize extraction findings
        if extraction and extraction.get('filtered_actions'):
            analysis['crew_findings']['actions'] = {
                'count': extraction.get('action_count', 0),
                'top_priority': extraction.get('filtered_actions', [{}])[0].get('action_title'),
                'total_hours': sum(
                    a.get('estimated_hours', 0) 
                    for a in extraction.get('filtered_actions', [])
                ),
                'has_immediate_win': extraction.get('immediate_action') is not None
            }
        
        # Determine overall recommendation
        if validation.get('actionable_score', 0) >= 5:
            if extraction and extraction.get('action_count', 0) > 0:
                analysis['crew_recommendation'] = 'IMPLEMENT_NOW'
                analysis['reasoning'] = 'High relevance with concrete actions'
            else:
                analysis['crew_recommendation'] = 'REVIEW_MANUALLY'
                analysis['reasoning'] = 'High relevance but needs action extraction'
        elif validation.get('actionable_score', 0) >= 3:
            analysis['crew_recommendation'] = 'IMPLEMENT_LATER'
            analysis['reasoning'] = 'Moderate relevance, queue for later'
        else:
            analysis['crew_recommendation'] = 'REFERENCE_ONLY'
            analysis['reasoning'] = 'Low relevance to current projects'
        
        print(f"   ✓ Recommendation: {analysis['crew_recommendation']}")
        
        return analysis
    
    def generate_crew_consensus(self) -> Dict:
        """
        Generate final consensus from all agents
        This is the crew's collective decision
        """
        
        validation = self.shared_memory.get('validation', {})
        extraction = self.shared_memory.get('extraction', {})
        analysis = self.shared_memory.get('analysis', {})
        article = self.shared_memory.get('article', {})
        
        consensus = {
            'article_id': article.get('id'),
            'crew_verdict': analysis.get('crew_recommendation', 'UNKNOWN'),
            'reasoning': analysis.get('reasoning', ''),
            'confidence_level': validation.get('confidence', 0),
            'actionable_score': validation.get('actionable_score', 0),
            'actions_found': extraction.get('action_count', 0) if extraction else 0,
            'estimated_work': sum(
                a.get('estimated_hours', 0) 
                for a in extraction.get('filtered_actions', [])
            ) if extraction else 0,
            'key_findings': [],
            'next_steps': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # Add key findings
        if validation.get('disagrees'):
            consensus['key_findings'].append(
                f"Classification mismatch: User said {validation.get('user_classification')}, "
                f"AI suggests {validation.get('ai_classification')}"
            )
        
        if extraction and extraction.get('immediate_action'):
            consensus['key_findings'].append(
                f"Quick win available: {extraction['immediate_action']}"
            )
        
        # Determine next steps based on verdict
        if consensus['crew_verdict'] == 'IMPLEMENT_NOW':
            consensus['next_steps'] = [
                'Create implementation TODOs',
                'Send notification to user',
                'Generate implementation plan'
            ]
        elif consensus['crew_verdict'] == 'REVIEW_MANUALLY':
            consensus['next_steps'] = [
                'Flag for manual review',
                'Extract more context'
            ]
        elif consensus['crew_verdict'] == 'IMPLEMENT_LATER':
            consensus['next_steps'] = [
                'Add to backlog',
                'Set reminder for review'
            ]
        else:
            consensus['next_steps'] = [
                'Archive as reference'
            ]
        
        return consensus
    
    async def execute_crew_decisions(self, consensus: Dict):
        """
        Execute the crew's decisions
        This is where actions are taken based on consensus
        """
        
        verdict = consensus.get('crew_verdict')
        
        if verdict == 'IMPLEMENT_NOW':
            print("\n🎯 Executing IMPLEMENT_NOW protocol...")
            
            # Create TODOs if we have actions
            extraction = self.shared_memory.get('extraction', {})
            if extraction and extraction.get('filtered_actions'):
                for action in extraction['filtered_actions'][:3]:  # Top 3 actions
                    await self.create_implementation_todo(action, consensus['article_id'])
            
            # Send notification
            await self.send_notification(
                "🔥 High-Priority Article Processed",
                f"Found {consensus['actions_found']} actions, ~{consensus['estimated_work']} hours of work",
                'high'
            )
            
        elif verdict == 'REVIEW_MANUALLY':
            print("\n👀 Flagging for manual review...")
            await self.flag_for_review(consensus['article_id'], consensus['reasoning'])
            
        elif verdict == 'IMPLEMENT_LATER':
            print("\n📋 Adding to backlog...")
            await self.add_to_backlog(consensus['article_id'], consensus)
        
        else:
            print("\n📚 Archived as reference")
    
    async def create_implementation_todo(self, action: Dict, article_id: str):
        """Create TODO from action"""
        try:
            todo_content = {
                'title': action.get('action_title'),
                'description': action.get('description'),
                'steps': action.get('implementation_steps', []),
                'estimated_hours': action.get('estimated_hours', 2),
                'source_article': article_id,
                'created_by': 'Article Analysis Crew',
                'created_at': datetime.now().isoformat()
            }
            
            response = requests.post(
                f"{self.api_base}/api/memory/store",
                json={
                    'content': json.dumps(todo_content, indent=2),
                    'category': 'todo',
                    'tags': ['crew-generated', 'implementation', 'auto-created'],
                    'importance': action.get('priority_score', 5)
                }
            )
            
            if response.status_code == 200:
                print(f"   ✓ Created TODO: {action.get('action_title')}")
            
        except Exception as e:
            print(f"   ✗ Failed to create TODO: {e}")
    
    async def send_notification(self, title: str, message: str, priority: str = 'normal'):
        """Send notification to user"""
        try:
            import subprocess
            subprocess.run([
                'python3',
                '/usr/local/share/universal-memory-system/src/notification_cli.py',
                'send', 'cerion', message,
                '--title', title,
                '--priority', priority
            ], capture_output=True)
            print(f"   ✓ Notification sent")
        except:
            pass  # Fail silently if notification system isn't available
    
    async def flag_for_review(self, article_id: str, reason: str):
        """Flag article for manual review"""
        try:
            response = requests.post(
                f"{self.api_base}/api/memory/store",
                json={
                    'content': f"Review needed for article {article_id}: {reason}",
                    'category': 'review_needed',
                    'tags': ['needs-review', 'crew-flagged'],
                    'importance': 7
                }
            )
            print(f"   ✓ Flagged for review")
        except:
            pass
    
    async def add_to_backlog(self, article_id: str, consensus: Dict):
        """Add to implementation backlog"""
        try:
            response = requests.post(
                f"{self.api_base}/api/memory/store",
                json={
                    'content': json.dumps({
                        'article_id': article_id,
                        'consensus': consensus,
                        'backlog_date': datetime.now().isoformat()
                    }, indent=2),
                    'category': 'backlog',
                    'tags': ['implement-later', 'crew-assessed'],
                    'importance': 4
                }
            )
            print(f"   ✓ Added to backlog")
        except:
            pass

# CLI Interface
async def main():
    """
    Run the Article Analysis Crew
    Can process single article or batch
    """
    
    crew = ArticleAnalysisCrew()
    
    if len(sys.argv) > 1:
        # Process specific article
        article_id = sys.argv[1]
        print(f"🚀 Processing article: {article_id}")
        consensus = await crew.process_article(article_id)
        
        print("\n" + "="*50)
        print("📊 CREW CONSENSUS REPORT")
        print("="*50)
        print(f"Verdict: {consensus.get('crew_verdict')}")
        print(f"Reasoning: {consensus.get('reasoning')}")
        print(f"Confidence: {consensus.get('confidence_level')}%")
        print(f"Actions Found: {consensus.get('actions_found')}")
        print(f"Estimated Work: {consensus.get('estimated_work')} hours")
        
        if consensus.get('key_findings'):
            print("\nKey Findings:")
            for finding in consensus['key_findings']:
                print(f"  • {finding}")
        
        if consensus.get('next_steps'):
            print("\nNext Steps:")
            for step in consensus['next_steps']:
                print(f"  → {step}")
    
    else:
        # Process recent articles
        print("🚀 Processing recent articles with crew...")
        
        # Get recent articles
        response = requests.get(
            "http://localhost:8091/api/memory/search?category=article&limit=3"
        )
        
        if response.status_code == 200:
            articles = response.json().get('results', [])
            
            for article in articles:
                print(f"\n{'='*50}")
                consensus = await crew.process_article(article['id'])
                print(f"\nVerdict: {consensus.get('crew_verdict')}")
                
                # Brief pause between articles
                await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())