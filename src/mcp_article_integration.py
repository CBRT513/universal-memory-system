#!/usr/bin/env python3
"""
MCP-Enhanced Article Analysis Integration
Combines MCP tools with Article Analysis Crew for powerful automation
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add UMS src to path
sys.path.insert(0, '/usr/local/share/universal-memory-system/src')

from article_crew import ArticleAnalysisCrew
from mcp_tools_bridge import MCPToolsBridge

class MCPArticleIntegration:
    """
    Integrates MCP tools with Article Analysis Crew
    Enables agents to use GitHub, Git, filesystem, and browser tools
    """
    
    def __init__(self):
        self.crew = ArticleAnalysisCrew()
        self.mcp_bridge = MCPToolsBridge()
        self.project_context = self._load_project_context()
        
    def _load_project_context(self) -> Dict:
        """Load context about user's projects"""
        return {
            "projects": [
                {
                    "name": "AgentForge",
                    "path": "/Users/cerion/Projects/AgentWorkspace/agentforge",
                    "repo": "cerion/agentforge",
                    "description": "AI application development platform"
                },
                {
                    "name": "Machine Maintenance",
                    "path": "/Users/cerion/Projects/Machine_Maintenance_App",
                    "repo": "CBRT513/machine-maintenance-system",
                    "description": "Cincinnati Barge & Rail maintenance system"
                },
                {
                    "name": "UMS",
                    "path": "/usr/local/share/universal-memory-system",
                    "repo": None,
                    "description": "Universal Memory System"
                }
            ],
            "focus_areas": ["AI agents", "automation", "memory systems", "React apps"]
        }
    
    async def analyze_article_with_mcp(self, article: Dict) -> Dict:
        """
        Analyze article and use MCP tools to take actions
        """
        
        # For now, simulate crew analysis based on tags
        # (In production, this would use the actual ArticleAnalysisCrew)
        if "actionable" in article.get("tags", []) or "implement-now" in article.get("tags", []):
            verdict = "IMPLEMENT_NOW"
            action_items = [
                {
                    "action": f"Implement {article['title'].split()[0].lower()} concepts in relevant projects",
                    "details": "Review article and apply learnings to current codebase",
                    "priority": "high",
                    "effort": "medium",
                    "project": "AgentForge"
                }
            ]
        elif "reference" in article.get("tags", []):
            verdict = "REFERENCE_ONLY"
            action_items = []
        else:
            verdict = "REVIEW_MANUALLY"
            action_items = [
                {
                    "action": f"Review {article['title']} for potential improvements",
                    "details": "Assess if concepts can improve existing systems",
                    "priority": "medium",
                    "effort": "low"
                }
            ]
        
        crew_analysis = {
            "verdict": verdict,
            "action_items": action_items,
            "confidence": 0.85,
            "article_id": article.get("id")
        }
        
        # If article is actionable, use MCP tools
        if crew_analysis.get("verdict") in ["IMPLEMENT_NOW", "REVIEW_MANUALLY"]:
            mcp_actions = await self._execute_mcp_actions(article, crew_analysis)
            crew_analysis["mcp_actions"] = mcp_actions
        
        return crew_analysis
    
    async def _execute_mcp_actions(self, article: Dict, analysis: Dict) -> List[Dict]:
        """
        Execute MCP tool actions based on article analysis
        """
        actions = []
        
        # Extract action items
        action_items = analysis.get("action_items", [])
        
        for item in action_items:
            action_type = self._classify_action(item)
            
            if action_type == "create_issue":
                result = await self._create_github_issue(item, article)
                actions.append(result)
                
            elif action_type == "update_code":
                result = await self._prepare_code_update(item, article)
                actions.append(result)
                
            elif action_type == "research":
                result = await self._research_implementation(item)
                actions.append(result)
                
            elif action_type == "document":
                result = await self._create_documentation(item, article)
                actions.append(result)
        
        return actions
    
    def _classify_action(self, action_item: Dict) -> str:
        """Classify what type of MCP action to take"""
        
        text = action_item.get("action", "").lower()
        
        if any(word in text for word in ["bug", "issue", "problem", "fix"]):
            return "create_issue"
        elif any(word in text for word in ["implement", "add", "create", "build"]):
            return "update_code"
        elif any(word in text for word in ["research", "explore", "investigate"]):
            return "research"
        elif any(word in text for word in ["document", "readme", "explain"]):
            return "document"
        else:
            return "unknown"
    
    async def _create_github_issue(self, action_item: Dict, article: Dict) -> Dict:
        """Create GitHub issue for action item"""
        
        # Determine which project
        project = self._find_relevant_project(action_item)
        
        if not project or not project.get("repo"):
            return {
                "action": "create_issue",
                "status": "skipped",
                "reason": "No GitHub repo configured"
            }
        
        # Create issue
        result = await self.mcp_bridge.execute_tool("github_create_issue", {
            "repo": project["repo"],
            "title": f"[Article Action] {action_item.get('action', 'Action needed')}",
            "body": f"""## Action Item from Article Analysis

**Article**: {article.get('title', 'Unknown')}
**URL**: {article.get('url', 'N/A')}

### Action Required:
{action_item.get('action')}

### Details:
{action_item.get('details', 'No additional details')}

### Priority: {action_item.get('priority', 'medium')}
### Effort: {action_item.get('effort', 'unknown')}

---
*Created automatically by MCP Article Integration*
"""
        })
        
        return {
            "action": "create_issue",
            "status": "success" if result.get("status") == "success" else "failed",
            "project": project["name"],
            "issue_url": result.get("issue_url")
        }
    
    async def _prepare_code_update(self, action_item: Dict, article: Dict) -> Dict:
        """Prepare code update based on action item"""
        
        project = self._find_relevant_project(action_item)
        
        if not project:
            return {
                "action": "update_code",
                "status": "skipped",
                "reason": "Could not determine relevant project"
            }
        
        # Check git status
        git_status = await self.mcp_bridge.execute_tool("git_status", {
            "repo_path": project["path"]
        })
        
        # Create implementation plan file
        plan_content = f"""# Implementation Plan

## Article: {article.get('title', 'Unknown')}

## Action: {action_item.get('action')}

## Implementation Steps:
1. {action_item.get('details', 'Review article for specific requirements')}
2. TODO: Add specific implementation steps

## Files to Modify:
- TODO: List files

## Testing Required:
- TODO: Add test cases

---
Generated: {datetime.now().isoformat()}
"""
        
        plan_path = f"{project['path']}/IMPLEMENTATION_PLAN_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        result = await self.mcp_bridge.execute_tool("filesystem_write", {
            "path": plan_path,
            "content": plan_content
        })
        
        return {
            "action": "update_code",
            "status": "prepared",
            "project": project["name"],
            "plan_file": plan_path,
            "git_status": git_status
        }
    
    async def _research_implementation(self, action_item: Dict) -> Dict:
        """Research implementation approach"""
        
        # Search for related code in projects
        search_results = []
        
        for project in self.project_context["projects"]:
            if os.path.exists(project["path"]):
                # Search for relevant files
                result = await self.mcp_bridge.execute_tool("filesystem_search", {
                    "path": project["path"],
                    "pattern": action_item.get("action", "").split()[0]
                })
                
                if result and result.get("status") == "success":
                    search_results.append({
                        "project": project["name"],
                        "matches": result.get("matches", [])
                    })
        
        return {
            "action": "research",
            "status": "completed",
            "search_results": search_results
        }
    
    async def _create_documentation(self, action_item: Dict, article: Dict) -> Dict:
        """Create documentation for action item"""
        
        doc_content = f"""# Documentation: {action_item.get('action')}

## Source Article
- Title: {article.get('title')}
- URL: {article.get('url')}
- Date Analyzed: {datetime.now().isoformat()}

## Action Item
{action_item.get('action')}

## Details
{action_item.get('details', 'No additional details provided')}

## Implementation Notes
- Priority: {action_item.get('priority', 'medium')}
- Effort: {action_item.get('effort', 'unknown')}
- Project: {action_item.get('project', 'TBD')}

## Next Steps
1. Review this documentation
2. Create implementation plan
3. Execute implementation
4. Test and verify

---
*Generated by MCP Article Integration*
"""
        
        doc_path = f"/tmp/article_doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        result = await self.mcp_bridge.execute_tool("filesystem_write", {
            "path": doc_path,
            "content": doc_content
        })
        
        # Store in UMS memory
        memory_result = await self.mcp_bridge.execute_tool("memory_store", {
            "content": doc_content,
            "tags": ["documentation", "article-action", action_item.get('project', 'general')],
            "category": "documentation"
        })
        
        return {
            "action": "document",
            "status": "created",
            "doc_path": doc_path,
            "memory_stored": memory_result.get("status") == "success"
        }
    
    def _find_relevant_project(self, action_item: Dict) -> Optional[Dict]:
        """Find which project an action item relates to"""
        
        action_text = action_item.get("action", "").lower()
        
        for project in self.project_context["projects"]:
            project_keywords = project["name"].lower().split() + \
                             project["description"].lower().split()
            
            if any(keyword in action_text for keyword in project_keywords):
                return project
        
        # Default to AgentForge if no match
        return self.project_context["projects"][0]
    
    async def process_recent_articles(self, limit: int = 5) -> List[Dict]:
        """
        Process recent articles with MCP enhancement
        """
        
        # Get recent articles from UMS
        articles = self._get_recent_articles(limit)
        
        results = []
        for article in articles:
            print(f"\n📄 Processing: {article.get('title', 'Unknown')}")
            
            analysis = await self.analyze_article_with_mcp(article)
            results.append(analysis)
            
            # Print summary
            print(f"  Verdict: {analysis.get('verdict')}")
            if "mcp_actions" in analysis:
                print(f"  MCP Actions: {len(analysis['mcp_actions'])}")
                for action in analysis["mcp_actions"]:
                    print(f"    - {action['action']}: {action['status']}")
        
        return results
    
    def _get_recent_articles(self, limit: int) -> List[Dict]:
        """Get recent articles from UMS database"""
        
        # For testing, return mock articles based on actual articles from the conversation
        mock_articles = [
            {
                "id": "mock_1",
                "title": "How to Build AI Agents with CrewAI",
                "content": """CrewAI is a framework for orchestrating autonomous AI agents. 
                It allows you to create crews of agents that work together on complex tasks.
                Key concepts include Agents, Tasks, Tools, Memory, and Process types.
                You can implement sequential, parallel, or hierarchical execution patterns.""",
                "url": "https://example.com/crewai-tutorial",
                "category": "article",
                "tags": ["ai", "agents", "crewai", "actionable"],
                "created_at": datetime.now().isoformat()
            },
            {
                "id": "mock_2", 
                "title": "MCP Tools for Claude Desktop",
                "content": """Model Context Protocol (MCP) tools enable Claude to interact
                with external systems. Available tools include GitHub integration, Git operations,
                filesystem access, and browser automation. These tools can be configured
                in Claude Desktop for enhanced capabilities.""",
                "url": "https://example.com/mcp-tools",
                "category": "article",
                "tags": ["mcp", "tools", "claude", "implement-now"],
                "created_at": datetime.now().isoformat()
            },
            {
                "id": "mock_3",
                "title": "React Best Practices 2024",
                "content": """Modern React development emphasizes functional components,
                hooks, and proper state management. Use Context API for global state,
                implement error boundaries, and optimize with React.memo and useMemo.""",
                "url": "https://example.com/react-best-practices",
                "category": "article", 
                "tags": ["react", "frontend", "reference"],
                "created_at": datetime.now().isoformat()
            }
        ]
        
        return mock_articles[:limit]


async def main():
    """Test MCP Article Integration"""
    
    print("🚀 MCP-Enhanced Article Analysis")
    print("=" * 50)
    
    integration = MCPArticleIntegration()
    
    # Process recent articles
    results = await integration.process_recent_articles(limit=3)
    
    print("\n" + "=" * 50)
    print("📊 Summary")
    print("=" * 50)
    
    total_actions = sum(len(r.get("mcp_actions", [])) for r in results)
    print(f"Articles processed: {len(results)}")
    print(f"Total MCP actions taken: {total_actions}")
    
    # Count action types
    action_counts = {}
    for result in results:
        for action in result.get("mcp_actions", []):
            action_type = action["action"]
            action_counts[action_type] = action_counts.get(action_type, 0) + 1
    
    print("\nActions by type:")
    for action_type, count in action_counts.items():
        print(f"  - {action_type}: {count}")


if __name__ == "__main__":
    asyncio.run(main())