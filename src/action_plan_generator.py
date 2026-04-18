#!/usr/bin/env python3
"""
Action Plan Generator for Implement_Now Articles
Automatically creates actionable plans when articles are triaged as implement_now
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class ActionPlanGenerator:
    """Generate action plans from implement_now articles"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(Path.home() / ".ai-memory" / "memories.db")
        self._init_action_plans_table()
    
    def _init_action_plans_table(self):
        """Create action plans table"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS action_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    memory_id TEXT,
                    article_title TEXT,
                    priority TEXT,
                    rationale TEXT,
                    prerequisites TEXT,
                    implementation_steps TEXT,
                    estimated_time TEXT,
                    potential_benefits TEXT,
                    risks_considerations TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at INTEGER,
                    FOREIGN KEY (memory_id) REFERENCES memories(id)
                )
            """)
            conn.commit()
    
    def generate_action_plan(self, memory_id: str, article_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an action plan from article analysis"""
        
        title = article_analysis.get('title', 'Untitled')
        action_items = article_analysis.get('action_items', [])
        technologies = article_analysis.get('technologies', [])
        summary = article_analysis.get('summary', '')
        
        # Generate rationale
        rationale = self._generate_rationale(title, summary, technologies)
        
        # Determine priority
        priority = self._determine_priority(article_analysis)
        
        # Create implementation steps
        implementation_steps = self._create_implementation_steps(action_items, technologies)
        
        # Estimate time
        estimated_time = self._estimate_time(action_items)
        
        # Identify benefits
        benefits = self._identify_benefits(title, technologies)
        
        # Consider risks
        risks = self._consider_risks(technologies)
        
        # Prerequisites
        prerequisites = self._identify_prerequisites(technologies)
        
        action_plan = {
            'memory_id': memory_id,
            'article_title': title,
            'priority': priority,
            'rationale': rationale,
            'prerequisites': prerequisites,
            'implementation_steps': implementation_steps,
            'estimated_time': estimated_time,
            'potential_benefits': benefits,
            'risks_considerations': risks,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        
        # Store in database
        self._store_action_plan(action_plan)
        
        return action_plan
    
    def _generate_rationale(self, title: str, summary: str, technologies: List[str]) -> str:
        """Generate why we should consider this"""
        
        rationale_parts = []
        
        # Check for specific value indicators
        if 'Claude Code' in str(technologies):
            rationale_parts.append("Enhances our existing Claude Code workflow")
        
        if 'free' in summary.lower() or 'open source' in summary.lower():
            rationale_parts.append("Cost-effective solution with no licensing fees")
        
        if 'performance' in summary.lower() or 'faster' in summary.lower():
            rationale_parts.append("Potential performance improvements")
        
        if 'integration' in title.lower() or 'connect' in title.lower():
            rationale_parts.append("Improves tool integration and workflow")
        
        if not rationale_parts:
            rationale_parts.append(f"Explores new capabilities in {', '.join(technologies[:3]) if technologies else 'development'}")
        
        return " | ".join(rationale_parts)
    
    def _determine_priority(self, analysis: Dict[str, Any]) -> str:
        """Determine action priority"""
        
        actionability = analysis.get('actionability_score', 5)
        relevance = analysis.get('relevance_score', 5)
        
        combined_score = (actionability + relevance) / 2
        
        if combined_score >= 9:
            return "HIGH - Implement this week"
        elif combined_score >= 7:
            return "MEDIUM - Schedule for next sprint"
        elif combined_score >= 5:
            return "LOW - Add to backlog"
        else:
            return "RESEARCH - Needs more investigation"
    
    def _create_implementation_steps(self, action_items: List[str], technologies: List[str]) -> List[str]:
        """Create concrete implementation steps"""
        
        steps = []
        
        # Add research step if new technologies
        if technologies:
            steps.append(f"Research and understand: {', '.join(technologies[:3])}")
        
        # Add the actual action items
        for item in action_items[:5]:  # Limit to 5 steps
            steps.append(item)
        
        # Add testing step
        steps.append("Test implementation in development environment")
        
        # Add documentation step
        steps.append("Document setup and configuration for team")
        
        return steps
    
    def _estimate_time(self, action_items: List[str]) -> str:
        """Estimate implementation time"""
        
        num_items = len(action_items)
        
        if num_items <= 2:
            return "1-2 hours"
        elif num_items <= 5:
            return "Half day (4 hours)"
        elif num_items <= 10:
            return "Full day (8 hours)"
        else:
            return "2-3 days"
    
    def _identify_benefits(self, title: str, technologies: List[str]) -> List[str]:
        """Identify potential benefits"""
        
        benefits = []
        
        title_lower = title.lower()
        
        if 'performance' in title_lower or 'faster' in title_lower:
            benefits.append("Improved performance and efficiency")
        
        if 'cli' in title_lower or 'terminal' in title_lower:
            benefits.append("Enhanced command-line productivity")
        
        if 'integration' in title_lower:
            benefits.append("Better tool integration")
        
        if 'automat' in title_lower:
            benefits.append("Increased automation capabilities")
        
        if any(tech in ['AI', 'ML', 'GPT', 'Claude'] for tech in technologies):
            benefits.append("Enhanced AI-assisted development")
        
        if not benefits:
            benefits.append("Expanded technical capabilities")
        
        return benefits
    
    def _consider_risks(self, technologies: List[str]) -> List[str]:
        """Consider potential risks"""
        
        risks = []
        
        # Check for new/unfamiliar technologies
        new_tech = [t for t in technologies if t not in ['Python', 'JavaScript', 'Git']]
        if new_tech:
            risks.append(f"Learning curve for: {', '.join(new_tech[:3])}")
        
        # Check for integration complexity
        if len(technologies) > 5:
            risks.append("Complex integration with multiple technologies")
        
        # Default minimal risk
        if not risks:
            risks.append("Minimal risk - straightforward implementation")
        
        return risks
    
    def _identify_prerequisites(self, technologies: List[str]) -> List[str]:
        """Identify what's needed before starting"""
        
        prereqs = []
        
        # Check for specific requirements
        if 'Docker' in technologies:
            prereqs.append("Docker installed and configured")
        
        if 'AWS' in technologies or 'Azure' in technologies:
            prereqs.append("Cloud account and credentials")
        
        if 'API' in str(technologies):
            prereqs.append("API keys or authentication tokens")
        
        if any('GPT' in t or 'Claude' in t for t in technologies):
            prereqs.append("AI service access (API keys or local models)")
        
        if not prereqs:
            prereqs.append("No special prerequisites - ready to start")
        
        return prereqs
    
    def _store_action_plan(self, plan: Dict[str, Any]):
        """Store action plan in database"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO action_plans (
                    memory_id, article_title, priority, rationale,
                    prerequisites, implementation_steps, estimated_time,
                    potential_benefits, risks_considerations, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                plan['memory_id'],
                plan['article_title'],
                plan['priority'],
                plan['rationale'],
                json.dumps(plan['prerequisites']),
                json.dumps(plan['implementation_steps']),
                plan['estimated_time'],
                json.dumps(plan['potential_benefits']),
                json.dumps(plan['risks_considerations']),
                plan['status'],
                int(datetime.now().timestamp())
            ))
            conn.commit()
    
    def get_pending_action_plans(self) -> List[Dict[str, Any]]:
        """Get all pending action plans"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM action_plans
                WHERE status = 'pending'
                ORDER BY created_at DESC
            """)
            
            columns = [description[0] for description in cursor.description]
            plans = []
            
            for row in cursor.fetchall():
                plan = dict(zip(columns, row))
                # Parse JSON fields
                for field in ['prerequisites', 'implementation_steps', 'potential_benefits', 'risks_considerations']:
                    if plan.get(field):
                        try:
                            plan[field] = json.loads(plan[field])
                        except:
                            pass
                plans.append(plan)
            
            return plans
    
    def format_action_plan(self, plan: Dict[str, Any]) -> str:
        """Format action plan for display"""
        
        output = []
        output.append(f"\n{'='*60}")
        output.append(f"ACTION PLAN: {plan['article_title']}")
        output.append(f"{'='*60}\n")
        
        output.append(f"📊 PRIORITY: {plan['priority']}")
        output.append(f"⏱️  TIME ESTIMATE: {plan['estimated_time']}")
        output.append(f"\n💡 RATIONALE:")
        output.append(f"   {plan['rationale']}")
        
        output.append(f"\n📋 PREREQUISITES:")
        for prereq in plan.get('prerequisites', []):
            output.append(f"   ✓ {prereq}")
        
        output.append(f"\n🎯 IMPLEMENTATION STEPS:")
        for i, step in enumerate(plan.get('implementation_steps', []), 1):
            output.append(f"   {i}. {step}")
        
        output.append(f"\n✨ POTENTIAL BENEFITS:")
        for benefit in plan.get('potential_benefits', []):
            output.append(f"   • {benefit}")
        
        output.append(f"\n⚠️  RISKS & CONSIDERATIONS:")
        for risk in plan.get('risks_considerations', []):
            output.append(f"   • {risk}")
        
        output.append(f"\n📅 CREATED: {plan.get('created_at', 'Unknown')}")
        output.append(f"🔖 STATUS: {plan.get('status', 'pending').upper()}")
        
        return '\n'.join(output)


def generate_action_plan_for_article(memory_id: str, analysis: Dict[str, Any]):
    """Generate an action plan for an implement_now article"""
    
    generator = ActionPlanGenerator()
    plan = generator.generate_action_plan(memory_id, analysis)
    formatted = generator.format_action_plan(plan)
    
    print(formatted)
    return plan


if __name__ == "__main__":
    # Test with the GPT-OSS article
    test_analysis = {
        'title': 'How to Use gpt-oss with Claude Code',
        'summary': 'Guide shows three ways to connect Claude Code to GPT-OSS using Hugging Face',
        'action_items': [
            'Deploy a private TGI server with OpenAI compatibility',
            'Point Claude Code at your endpoint',
            'Verify the connection'
        ],
        'technologies': ['Claude Code', 'GPT-OSS', 'Hugging Face', 'OpenAI'],
        'actionability_score': 8,
        'relevance_score': 9
    }
    
    plan = generate_action_plan_for_article('test_123', test_analysis)