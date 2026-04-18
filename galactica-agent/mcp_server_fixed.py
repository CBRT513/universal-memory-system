#!/usr/bin/env python3
"""
Galactica MCP Server - Model Context Protocol compliant server for UMS/Galactica
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
    """MCP Server for Galactica/UMS integration with proper MCP protocol support"""
    
    def __init__(self):
        self.ums_api_url = "http://127.0.0.1:8091"
        self.memory_db = Path.home() / ".ai-memory" / "memories.db"
        self.session_id = f"mcp_{datetime.now().timestamp()}"
        
    async def handle_jsonrpc(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle JSON-RPC 2.0 messages"""
        method = message.get("method")
        params = message.get("params", {})
        msg_id = message.get("id")
        
        try:
            if method == "initialize":
                result = await self.initialize(params)
            elif method == "tools/list":
                result = await self.list_tools()
            elif method == "tools/call":
                result = await self.call_tool(params)
            elif method == "resources/list":
                result = await self.list_resources()
            elif method == "resources/read":
                result = await self.read_resource(params)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                }
            
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error handling {method}: {e}")
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32603, "message": str(e)}
            }
    
    async def initialize(self, params: Dict) -> Dict[str, Any]:
        """Handle MCP initialization"""
        logger.info("Initializing Galactica MCP Server")
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {}
            },
            "serverInfo": {
                "name": "galactica-mcp-server",
                "version": "1.0.0"
            }
        }
    
    async def list_tools(self) -> Dict[str, Any]:
        """Return available tools"""
        return {
            "tools": [
                {
                    "name": "galactica_remember",
                    "description": "Store a memory in Galactica/UMS",
                    "inputSchema": {
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
                    "inputSchema": {
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
                    "name": "galactica_status",
                    "description": "Get comprehensive Galactica system status",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "include_metrics": {"type": "boolean", "default": True},
                            "include_health": {"type": "boolean", "default": True}
                        }
                    }
                }
            ]
        }
    
    async def call_tool(self, params: Dict) -> Dict[str, Any]:
        """Call a tool"""
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        if name == "galactica_remember":
            return await self.store_memory(arguments)
        elif name == "galactica_recall":
            return await self.search_memories(arguments)
        elif name == "galactica_status":
            return await self.get_status(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    async def list_resources(self) -> Dict[str, Any]:
        """Return available resources"""
        return {
            "resources": [
                {
                    "uri": "galactica://context",
                    "name": "Galactica Context",
                    "description": "Current Galactica system context and state",
                    "mimeType": "application/json"
                },
                {
                    "uri": "galactica://memories/recent",
                    "name": "Recent Memories",
                    "description": "Recent memories from UMS",
                    "mimeType": "application/json"
                }
            ]
        }
    
    async def read_resource(self, params: Dict) -> Dict[str, Any]:
        """Read a resource"""
        uri = params.get("uri")
        
        if uri == "galactica://context":
            return {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(await self._get_current_context())}]}
        elif uri == "galactica://memories/recent":
            return {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(await self._get_recent_memories())}]}
        else:
            raise ValueError(f"Unknown resource: {uri}")
    
    async def store_memory(self, args: Dict) -> Dict[str, Any]:
        """Store a memory in UMS"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.ums_api_url}/api/memories", json=args) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {"content": [{"type": "text", "text": f"Memory stored successfully: {result.get('id', 'unknown')}"}]}
                    else:
                        return {"content": [{"type": "text", "text": f"Failed to store memory: {response.status}"}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Error storing memory: {str(e)}"}]}
    
    async def search_memories(self, args: Dict) -> Dict[str, Any]:
        """Search memories in UMS"""
        try:
            async with aiohttp.ClientSession() as session:
                params = {"q": args.get("query", ""), "limit": args.get("limit", 5)}
                async with session.get(f"{self.ums_api_url}/api/search", params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        memories_text = json.dumps(result, indent=2)
                        return {"content": [{"type": "text", "text": f"Found memories:\n{memories_text}"}]}
                    else:
                        return {"content": [{"type": "text", "text": f"Failed to search memories: {response.status}"}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Error searching memories: {str(e)}"}]}
    
    async def get_status(self, args: Dict) -> Dict[str, Any]:
        """Get system status"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ums_api_url}/api/health") as response:
                    if response.status == 200:
                        health = await response.json()
                        status = {
                            "system": "Galactica MCP Server",
                            "session_id": self.session_id,
                            "ums_health": health,
                            "memory_db_size": self._get_db_size(),
                            "memory_count": self._get_memory_count()
                        }
                        return {"content": [{"type": "text", "text": json.dumps(status, indent=2)}]}
                    else:
                        return {"content": [{"type": "text", "text": f"UMS health check failed: {response.status}"}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Error getting status: {str(e)}"}]}
    
    async def _get_current_context(self) -> Dict[str, Any]:
        """Get current Galactica context"""
        return {
            "session_id": self.session_id,
            "active_components": ["UMS", "MCP Server", "Claude Integration"],
            "focus_areas": ["tight integration", "continuous evolution", "autonomous maintenance"]
        }
    
    async def _get_recent_memories(self) -> Dict[str, Any]:
        """Get recent memories"""
        return await self.search_memories({"query": "*", "limit": 20})
    
    def _get_db_size(self) -> str:
        """Get database size"""
        if self.memory_db.exists():
            size = self.memory_db.stat().st_size
            return f"{size / 1024 / 1024:.2f} MB"
        return "0 MB"
    
    def _get_memory_count(self) -> int:
        """Get memory count"""
        if self.memory_db.exists():
            try:
                conn = sqlite3.connect(self.memory_db)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM memories")
                count = cursor.fetchone()[0]
                conn.close()
                return count
            except:
                return 0
        return 0
    
    async def run(self):
        """Run the MCP server"""
        logger.info("Galactica MCP Server starting...")
        
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                
                message = json.loads(line.strip())
                response = await self.handle_jsonrpc(message)
                
                print(json.dumps(response))
                sys.stdout.flush()
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": "Parse error"}
                }
                print(json.dumps(error_response))
                sys.stdout.flush()
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                error_response = {
                    "jsonrpc": "2.0", 
                    "id": None,
                    "error": {"code": -32603, "message": str(e)}
                }
                print(json.dumps(error_response))
                sys.stdout.flush()

if __name__ == "__main__":
    server = GalacticaMCPServer()
    asyncio.run(server.run())
