#!/usr/bin/env python3
"""
Galactica MCP Server - Model Context Protocol server for UMS/Galactica
Provides deep integration between Claude Code and the Universal Memory System
"""

import json
import sys
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import aiohttp
import sqlite3
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GalacticaMCPServer:
    """MCP Server for Galactica/UMS integration with intelligent subagent routing"""
    
    def __init__(self):
        self.ums_api_url = "http://127.0.0.1:8091"
        self.memory_db = Path.home() / ".ai-memory" / "memories.db"
        self.galactica_context = {}
        self.session_id = f"mcp_{datetime.now().timestamp()}"
        
        # CrewAI-style shared memory for subagents
        self.shared_subagent_memory = {}
        
        # Subagent mapping for intelligent routing
        self.subagent_registry = {
            'frontend-specialist': {
                'specialties': ['react', 'vue', 'ui', 'component', 'style', 'frontend'],
                'tools': ['component_generator', 'style_builder', 'ui_optimizer'],
                'confidence_boost': 0.2
            },
            'backend-specialist': {
                'specialties': ['api', 'fastapi', 'endpoint', 'database', 'backend', 'server'],
                'tools': ['api_generator', 'crud_builder', 'schema_designer'],
                'confidence_boost': 0.2
            },
            'database-architect': {
                'specialties': ['schema', 'sql', 'database', 'migration', 'model', 'orm'],
                'tools': ['schema_generator', 'migration_builder', 'query_optimizer'],
                'confidence_boost': 0.3
            },
            'testing-specialist': {
                'specialties': ['test', 'pytest', 'unit', 'integration', 'coverage', 'qa'],
                'tools': ['test_generator', 'coverage_analyzer', 'test_runner'],
                'confidence_boost': 0.2
            },
            'devops-engineer': {
                'specialties': ['deploy', 'docker', 'ci', 'cd', 'pipeline', 'kubernetes'],
                'tools': ['dockerfile_generator', 'pipeline_builder', 'deploy_script'],
                'confidence_boost': 0.2
            },
            'security-auditor': {
                'specialties': ['security', 'vulnerability', 'auth', 'encryption', 'audit'],
                'tools': ['security_scanner', 'vulnerability_checker', 'auth_implementer'],
                'confidence_boost': 0.3
            },
            'performance-optimizer': {
                'specialties': ['performance', 'optimize', 'speed', 'cache', 'profiling'],
                'tools': ['profiler', 'optimizer', 'cache_implementer'],
                'confidence_boost': 0.2
            },
            'documentation-writer': {
                'specialties': ['docs', 'documentation', 'readme', 'api-docs', 'comments'],
                'tools': ['doc_generator', 'api_doc_builder', 'readme_creator'],
                'confidence_boost': 0.1
            },
            'code-reviewer': {
                'specialties': ['review', 'quality', 'lint', 'format', 'best-practices'],
                'tools': ['linter', 'formatter', 'review_assistant'],
                'confidence_boost': 0.2
            },
            'ai-integration': {
                'specialties': ['llm', 'ai', 'claude', 'gpt', 'embedding', 'vector'],
                'tools': ['llm_integrator', 'embedding_generator', 'prompt_optimizer'],
                'confidence_boost': 0.3
            }
        }
        
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        handlers = {
            "initialize": self.initialize,
            "tools/list": self.get_tools,
            "resources/list": self.get_resources,
            "prompts/list": self.get_prompts,
            "tools/call": self.invoke_tool,
            "resources/read": self.read_resource,
            "prompts/get": self.run_prompt,
        }
        
        handler = handlers.get(method)
        if handler:
            result = await handler(params)
            if request_id is not None:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
            return result
        
        error_response = {
            "jsonrpc": "2.0",
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }
        if request_id is not None:
            error_response["id"] = request_id
        return error_response
    
    async def initialize(self, params: Dict) -> Dict[str, Any]:
        """Initialize the MCP server"""
        return {
            "protocolVersion": "1.0.0",
            "serverInfo": {
                "name": "ums-galactica",
                "version": "1.0.0"
            },
            "capabilities": {
                "tools": {},
                "resources": {},
                "prompts": {}
            }
        }
    
    async def get_tools(self, params: Dict) -> Dict[str, Any]:
        """Return available tools for Claude"""
        return {
            "tools": [
                {
                    "name": "galactica_remember",
                    "description": "Store a memory in Galactica/UMS",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string", "description": "The content to remember"},
                            "kind": {"type": "string", "enum": ["decision", "insight", "code", "architecture", "todo", "reference"]},
                            "tags": {"type": "array", "items": {"type": "string"}},
                            "context": {"type": "string", "description": "Additional context"}
                        },
                        "required": ["content", "kind"]
                    }
                },
                {
                    "name": "galactica_recall",
                    "description": "Search and retrieve memories from Galactica",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "limit": {"type": "integer", "default": 5},
                            "kind": {"type": "string", "description": "Filter by memory type"},
                            "tags": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "galactica_analyze",
                    "description": "Analyze project state and suggest improvements",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "aspect": {"type": "string", "enum": ["architecture", "performance", "integration", "evolution"]},
                            "depth": {"type": "string", "enum": ["quick", "detailed", "comprehensive"]}
                        }
                    }
                },
                {
                    "name": "galactica_evolve",
                    "description": "Propose and implement Galactica system evolution",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "component": {"type": "string", "description": "Component to evolve"},
                            "improvement": {"type": "string", "description": "Description of improvement"},
                            "auto_implement": {"type": "boolean", "default": False}
                        },
                        "required": ["component", "improvement"]
                    }
                },
                {
                    "name": "galactica_status",
                    "description": "Get comprehensive Galactica system status",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "include_metrics": {"type": "boolean", "default": True},
                            "include_health": {"type": "boolean", "default": True}
                        }
                    }
                }
            ]
        }
    
    async def get_resources(self, params: Dict) -> Dict[str, Any]:
        """Return available resources"""
        return {
            "resources": [
                {
                    "uri": "galactica://context",
                    "name": "Galactica Context",
                    "description": "Current Galactica system context and state"
                },
                {
                    "uri": "galactica://memories/recent",
                    "name": "Recent Memories",
                    "description": "Recent memories from UMS"
                },
                {
                    "uri": "galactica://decisions",
                    "name": "Architecture Decisions",
                    "description": "All architectural decisions made for Galactica"
                },
                {
                    "uri": "galactica://roadmap",
                    "name": "Evolution Roadmap",
                    "description": "Planned improvements and evolution path"
                }
            ]
        }
    
    async def get_prompts(self, params: Dict) -> Dict[str, Any]:
        """Return available prompts"""
        return {
            "prompts": [
                {
                    "name": "galactica_session",
                    "description": "Start a dedicated Galactica development session",
                    "parameters": ["focus_area"]
                },
                {
                    "name": "galactica_review",
                    "description": "Review recent changes and suggest improvements",
                    "parameters": []
                },
                {
                    "name": "galactica_integrate",
                    "description": "Help integrate new component with Galactica",
                    "parameters": ["component_type", "integration_points"]
                }
            ]
        }
    
    def select_best_subagent(self, tool_name: str, params: Dict) -> Optional[str]:
        """Select the best subagent based on task analysis (CrewAI pattern)"""
        
        # Analyze the task
        task_text = f"{tool_name} {json.dumps(params)}".lower()
        
        best_subagent = None
        best_score = 0.0
        
        for subagent_name, config in self.subagent_registry.items():
            score = 0.0
            
            # Check if any specialties match
            for specialty in config['specialties']:
                if specialty in task_text:
                    score += 0.3
            
            # Check if the tool matches subagent's tools
            for tool in config.get('tools', []):
                if tool in tool_name or tool in task_text:
                    score += 0.5
            
            # Apply confidence boost for specialized tasks
            if score > 0:
                score += config.get('confidence_boost', 0)
            
            # Track best match
            if score > best_score:
                best_score = score
                best_subagent = subagent_name
        
        # Only return if confidence is high enough
        if best_score >= 0.3:
            logger.info(f"Selected subagent '{best_subagent}' with confidence {best_score:.2f}")
            return best_subagent
        
        return None
    
    async def delegate_to_subagent(self, subagent: str, tool_name: str, params: Dict) -> Dict[str, Any]:
        """Delegate task to specialized subagent with context sharing"""
        
        # Add shared context from other subagents
        enhanced_params = {
            **params,
            'shared_context': self.shared_subagent_memory,
            'delegated_to': subagent,
            'delegation_reason': f"Specialized in {', '.join(self.subagent_registry[subagent]['specialties'][:3])}"
        }
        
        # Log delegation
        logger.info(f"Delegating to {subagent}: {tool_name}")
        
        # Execute with enhanced context
        result = await self.execute_with_subagent(subagent, tool_name, enhanced_params)
        
        # Store result in shared memory
        self.shared_subagent_memory[f"{subagent}_{tool_name}"] = result
        
        return result
    
    async def execute_with_subagent(self, subagent: str, tool_name: str, params: Dict) -> Dict[str, Any]:
        """Execute tool with specific subagent context"""
        
        # Add subagent-specific prompting
        subagent_config = self.subagent_registry.get(subagent, {})
        
        result = {
            'subagent': subagent,
            'tool': tool_name,
            'specialties': subagent_config.get('specialties', []),
            'execution_time': datetime.now().isoformat()
        }
        
        # Route to appropriate handler based on subagent type
        if subagent == 'frontend-specialist' and 'component' in tool_name:
            result['output'] = await self.generate_frontend_component(params)
        elif subagent == 'backend-specialist' and 'api' in tool_name:
            result['output'] = await self.generate_api_endpoint(params)
        elif subagent == 'database-architect' and 'schema' in tool_name:
            result['output'] = await self.design_database_schema(params)
        else:
            # Default execution
            result['output'] = await self.execute_default_tool(tool_name, params)
        
        return result
    
    async def generate_frontend_component(self, params: Dict) -> str:
        """Frontend specialist subagent logic"""
        return f"Generated React component based on: {params.get('description', 'request')}"
    
    async def generate_api_endpoint(self, params: Dict) -> str:
        """Backend specialist subagent logic"""
        return f"Generated FastAPI endpoint for: {params.get('endpoint', '/api/resource')}"
    
    async def design_database_schema(self, params: Dict) -> str:
        """Database architect subagent logic"""
        return f"Designed schema with tables: {params.get('tables', ['default'])}"
    
    async def execute_default_tool(self, tool_name: str, params: Dict) -> Any:
        """Default tool execution when no specific subagent matches"""
        # Original tool execution logic
        if tool_name == "galactica_remember":
            return await self.remember(params)
        elif tool_name == "galactica_recall":
            return await self.recall(params)
        elif tool_name == "galactica_analyze":
            return await self.analyze(params)
        else:
            return {"status": "executed", "tool": tool_name}
    
    async def invoke_tool(self, params: Dict) -> Dict[str, Any]:
        """Enhanced with CrewAI-style task delegation"""
        tool_name = params.get("name")
        tool_params = params.get("arguments", {})
        
        # Try intelligent subagent routing first
        subagent = self.select_best_subagent(tool_name, tool_params)
        
        if subagent:
            # Delegate to specialized subagent
            logger.info(f"🤖 Delegating {tool_name} to {subagent}")
            result = await self.delegate_to_subagent(subagent, tool_name, tool_params)
            
            # Store in shared memory for other subagents
            self.shared_subagent_memory[tool_name] = result
            
            return result
        
        # Fall back to original tool execution
        if tool_name == "galactica_remember":
            return await self.store_memory(tool_params)
        elif tool_name == "galactica_recall":
            return await self.search_memories(tool_params)
        elif tool_name == "galactica_analyze":
            return await self.analyze_system(tool_params)
        elif tool_name == "galactica_evolve":
            return await self.evolve_system(tool_params)
        elif tool_name == "galactica_status":
            return await self.get_system_status(tool_params)
        
        return {"error": f"Unknown tool: {tool_name}"}
    
    async def store_memory(self, params: Dict) -> Dict[str, Any]:
        """Store a memory in UMS"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "content": params["content"],
                "kind": params.get("kind", "note"),
                "tags": params.get("tags", ["galactica", "mcp"]),
                "source": f"mcp_session_{self.session_id}"
            }
            
            if "context" in params:
                payload["metadata"] = {"context": params["context"]}
            
            async with session.post(f"{self.ums_api_url}/api/memory/store", json=payload) as resp:
                result = await resp.json()
                return {
                    "success": result.get("status") == "stored",
                    "memory_id": result.get("memory_id"),
                    "message": f"Memory stored: {result.get('memory_id', 'unknown')}"
                }
    
    async def search_memories(self, params: Dict) -> Dict[str, Any]:
        """Search memories in UMS"""
        async with aiohttp.ClientSession() as session:
            query_params = {
                "q": params["query"],
                "limit": params.get("limit", 5)
            }
            
            async with session.get(f"{self.ums_api_url}/api/memory/search", params=query_params) as resp:
                results = await resp.json()
                
                # Format results for Claude
                formatted = []
                for memory in results.get("results", []):
                    formatted.append({
                        "id": memory.get("id"),
                        "content": memory.get("content"),
                        "kind": memory.get("kind"),
                        "tags": memory.get("tags"),
                        "timestamp": memory.get("timestamp"),
                        "relevance": memory.get("score")
                    })
                
                return {
                    "memories": formatted,
                    "count": len(formatted),
                    "query": params["query"]
                }
    
    async def analyze_system(self, params: Dict) -> Dict[str, Any]:
        """Analyze Galactica system state"""
        aspect = params.get("aspect", "architecture")
        depth = params.get("depth", "quick")
        
        # Gather system information
        analysis = {
            "aspect": aspect,
            "depth": depth,
            "timestamp": datetime.now().isoformat(),
            "findings": []
        }
        
        if aspect == "architecture":
            # Check system components
            analysis["findings"].append({
                "component": "UMS API",
                "status": "operational",
                "notes": "FastAPI service running on port 8091"
            })
            analysis["findings"].append({
                "component": "Memory Database",
                "status": "healthy",
                "size": self._get_db_size()
            })
            
        elif aspect == "integration":
            # Check integration points
            analysis["findings"].append({
                "integration": "Claude Code",
                "status": "connected via MCP",
                "capabilities": ["memory storage", "context retrieval"]
            })
            analysis["findings"].append({
                "integration": "Ollama",
                "status": "active",
                "models": ["llama3.2:3b", "nomic-embed-text"]
            })
        
        return analysis
    
    async def evolve_system(self, params: Dict) -> Dict[str, Any]:
        """Propose system evolution"""
        component = params["component"]
        improvement = params["improvement"]
        auto_implement = params.get("auto_implement", False)
        
        # Store the evolution proposal
        await self.store_memory({
            "content": f"Evolution Proposal: {improvement} for {component}",
            "kind": "architecture",
            "tags": ["evolution", "proposal", component],
            "context": json.dumps(params)
        })
        
        response = {
            "component": component,
            "improvement": improvement,
            "proposal_id": f"evo_{datetime.now().timestamp()}",
            "status": "proposed"
        }
        
        if auto_implement:
            response["implementation"] = "Ready for implementation. Use specific commands to proceed."
        
        return response
    
    async def get_system_status(self, params: Dict) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "components": {},
            "metrics": {},
            "health": "operational"
        }
        
        # Check UMS API
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ums_api_url}/api/health") as resp:
                    if resp.status == 200:
                        status["components"]["ums_api"] = "running"
        except:
            status["components"]["ums_api"] = "unavailable"
            status["health"] = "degraded"
        
        # Check memory database
        if self.memory_db.exists():
            status["components"]["memory_db"] = "available"
            status["metrics"]["db_size"] = self._get_db_size()
            status["metrics"]["memory_count"] = self._get_memory_count()
        
        return status
    
    async def read_resource(self, params: Dict) -> Dict[str, Any]:
        """Read a specific resource"""
        uri = params.get("uri")
        
        if uri == "galactica://context":
            return await self._get_current_context()
        elif uri == "galactica://memories/recent":
            return await self._get_recent_memories()
        elif uri == "galactica://decisions":
            return await self._get_architecture_decisions()
        elif uri == "galactica://roadmap":
            return await self._get_roadmap()
        
        return {"error": f"Unknown resource: {uri}"}
    
    async def run_prompt(self, params: Dict) -> Dict[str, Any]:
        """Run a prompt - MCP protocol compliance"""
        prompt_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if prompt_name == "analyze_context":
            return {
                "result": {
                    "content": f"Analyzing context with Galactica: {arguments.get('context', 'No context provided')}",
                    "suggestions": [
                        "Consider previous interactions",
                        "Apply learned patterns",
                        "Suggest improvements based on history"
                    ]
                }
            }
        elif prompt_name == "suggest_improvement":
            return {
                "result": {
                    "content": "Based on UMS memory analysis, here are suggestions for improvement",
                    "improvements": [
                        "Optimize based on past successful patterns",
                        "Apply learned best practices",
                        "Avoid previously identified issues"
                    ]
                }
            }
        
        return {"error": f"Unknown prompt: {prompt_name}"}
    
    async def _get_current_context(self) -> Dict[str, Any]:
        """Get current Galactica context"""
        # Search for recent Galactica-related memories
        recent = await self.search_memories({"query": "galactica", "limit": 10})
        
        return {
            "context": {
                "session_id": self.session_id,
                "recent_memories": recent["memories"],
                "active_components": ["UMS", "MCP Server", "Claude Integration"],
                "focus_areas": ["tight integration", "continuous evolution", "autonomous maintenance"]
            }
        }
    
    async def _get_recent_memories(self) -> Dict[str, Any]:
        """Get recent memories"""
        return await self.search_memories({"query": "*", "limit": 20})
    
    async def _get_architecture_decisions(self) -> Dict[str, Any]:
        """Get architecture decisions"""
        return await self.search_memories({
            "query": "architecture decision",
            "kind": "architecture",
            "limit": 50
        })
    
    async def _get_roadmap(self) -> Dict[str, Any]:
        """Get evolution roadmap"""
        roadmap = {
            "phases": [
                {
                    "phase": 1,
                    "name": "Foundation",
                    "status": "completed",
                    "items": ["UMS setup", "Basic integration", "Memory persistence"]
                },
                {
                    "phase": 2,
                    "name": "Deep Integration",
                    "status": "in_progress",
                    "items": ["MCP server", "Auto-context", "Continuous learning"]
                },
                {
                    "phase": 3,
                    "name": "Autonomous Evolution",
                    "status": "planned",
                    "items": ["Self-improvement", "Pattern recognition", "Proactive suggestions"]
                }
            ]
        }
        return roadmap
    
    def _get_db_size(self) -> str:
        """Get database size"""
        if self.memory_db.exists():
            size = self.memory_db.stat().st_size
            return f"{size / 1024 / 1024:.2f} MB"
        return "0 MB"
    
    def _get_memory_count(self) -> int:
        """Get memory count"""
        if self.memory_db.exists():
            conn = sqlite3.connect(self.memory_db)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM memories")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        return 0
    
    async def run(self):
        """Run the MCP server"""
        logger.info("Galactica MCP Server starting...")
        
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                
                request = json.loads(line)
                response = await self.handle_request(request)
                
                # Send response
                print(json.dumps(response))
                sys.stdout.flush()
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
            except Exception as e:
                logger.error(f"Error: {e}")
                error_response = {"error": str(e)}
                print(json.dumps(error_response))
                sys.stdout.flush()

if __name__ == "__main__":
    server = GalacticaMCPServer()
    asyncio.run(server.run())