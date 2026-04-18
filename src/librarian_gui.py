#!/usr/bin/env python3
"""
Universal AI Memory System - Web Librarian GUI
Production-ready web interface with chat-based interaction
"""
import os
import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    print("Error: FastAPI not available. Please install: pip install fastapi uvicorn jinja2")
    sys.exit(1)

from memory_service import get_memory_service, UniversalMemoryService

app = FastAPI(title="Universal AI Memory Librarian", version="1.0.0")

# Setup templates and static files
templates_dir = Path(__file__).parent.parent / "templates"
static_dir = Path(__file__).parent.parent / "static"
templates_dir.mkdir(exist_ok=True)
static_dir.mkdir(exist_ok=True)

templates = Jinja2Templates(directory=str(templates_dir))
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Global memory service
memory_service: Optional[UniversalMemoryService] = None

class LibrarianAgent:
    """Intelligent librarian agent for helping users"""
    
    def __init__(self, memory_service: UniversalMemoryService):
        self.service = memory_service
        self.conversation_history = []
        
        # Intent classification using embeddings
        self.intent_examples = {
            'store_memory': [
                "remember this solution",
                "save this insight", 
                "store this information",
                "keep track of this",
                "remember that JWT auth works",
                "save this code pattern",
                "remember this doesn't work"
            ],
            'search_memories': [
                "find memories about React",
                "search for database solutions", 
                "look for authentication issues",
                "show me performance tips",
                "what do I know about caching",
                "find anything about deployment"
            ],
            'get_statistics': [
                "how many memories do I have",
                "show system statistics",
                "what's my memory count",
                "system status",
                "show me the stats",
                "memory overview numbers"
            ],
            'summarize_memories': [
                "summarize my memories",
                "give me an overview of what I've stored",
                "what have I learned so far", 
                "show me a summary",
                "review my memories",
                "what insights do I have"
            ],
            'get_context': [
                "give me context for this project",
                "what background do I have on authentication",
                "provide context for database work",
                "what do I know about React optimization",
                "give me relevant background",
                "context for debugging issues"
            ],
            'general_help': [
                "how does this work",
                "what can you do",
                "help me understand the system",
                "what are your capabilities",
                "how do I use this",
                "what commands are available"
            ]
        }
        
        # Pre-compute intent embeddings for fast classification
        self._intent_embeddings = None
        self._initialize_intent_classifier()
        
        # Knowledge base for common questions
        self.knowledge_base = {
            "how_to_store": {
                "answer": "To store a memory, use the `memory remember` command:\n\n```\nmemory remember \"Your solution or insight here\" --tags tag1,tag2 --importance 8\n```\n\nOr use the web interface - just type what you want to remember!",
                "examples": [
                    'memory remember "Use React.memo for expensive components" --tags react,performance',
                    'memory remember "JWT auth working perfectly - don\'t change!" --status working --protection high'
                ]
            },
            "how_to_search": {
                "answer": "Search memories using semantic or keyword matching:\n\n```\nmemory search \"database optimization\"\nmemory search --project myapp --tags performance\nmemory recall \"authentication issues\"\n```",
                "examples": [
                    'memory search "React performance"',
                    'memory search --category solution --importance 8',
                    'memory recall "database" --tag optimization'
                ]
            },
            "how_to_get_context": {
                "answer": "Get intelligent context for AI conversations:\n\n```\nmemory context --relevant-to \"your question\" --copy\nmemory ai-context --question \"How to optimize React?\" --ai chatgpt --copy\n```\n\nThis generates context from your memories and copies it to clipboard!",
                "examples": [
                    'memory context --relevant-to "authentication problems" --copy',
                    'memory ai-context -q "database performance" --ai claude'
                ]
            },
            "anti_regression": {
                "answer": "Protect working systems from being changed:\n\n```\nmemory remember \"Auth system working perfectly\" --status working --protection high\n```\n\nWhen you get context, protected memories are highlighted as \"DO NOT CHANGE\"",
                "examples": [
                    'memory remember "Payment API stable for 6 months" --status working --protection critical',
                    'memory remember "MongoDB failed for our use case" --status failed'
                ]
            },
            "projects": {
                "answer": "The system auto-detects projects from your git repository or directory:\n\n```\nmemory projects  # List all projects\nmemory search --project myapp  # Search specific project\nmemory context --project myapp  # Get project context\n```",
                "examples": [
                    'memory search --project "my-web-app" --category solution',
                    'memory context --project backend-api --relevant-to "performance"'
                ]
            },
            "browser_integration": {
                "answer": "Capture insights from any AI website:\n\n1. Start memory service: `./start-memory-service.sh`\n2. Open browser_integration.html\n3. Drag bookmarklet to bookmark bar\n4. Use on ChatGPT, Claude, etc. to save insights",
                "examples": [
                    "Select text in ChatGPT → click bookmarklet → add tags → save"
                ]
            },
            "troubleshooting": {
                "answer": "Common issues and solutions:\n\n```\nmemory doctor  # Run diagnostics\nmemory server --status  # Check if service running\nmemory stats  # View system statistics\n```\n\nFor embedding issues, install Ollama or use sentence-transformers.",
                "examples": [
                    'memory doctor',
                    'memory cleanup --duplicates --dry-run',
                    'memory backup --destination ~/backups/'
                ]
            }
        }
    
    def _initialize_intent_classifier(self):
        """Initialize the embedding-based intent classifier"""
        try:
            # Get embeddings for all intent examples
            all_examples = []
            intent_labels = []
            
            for intent, examples in self.intent_examples.items():
                for example in examples:
                    all_examples.append(example)
                    intent_labels.append(intent)
            
            # Get embeddings using the memory service's embedding provider
            embeddings = []
            for example in all_examples:
                if hasattr(self.service, 'embedding_service') and self.service.embedding_service:
                    embedding = self.service.embedding_service.get_embedding(example)
                    embeddings.append(embedding)
                else:
                    # Fallback: no embeddings available
                    embeddings = None
                    break
            
            if embeddings:
                import numpy as np
                self._intent_embeddings = np.array(embeddings)
                self._intent_labels = intent_labels
                print("✅ Intent classifier initialized with semantic embeddings")
            else:
                self._intent_embeddings = None
                print("⚠️  Intent classifier using fallback pattern matching")
                
        except Exception as e:
            print(f"⚠️  Intent classifier initialization failed: {e}")
            self._intent_embeddings = None
    
    def _classify_intent(self, user_message: str) -> str:
        """Classify user intent using semantic similarity"""
        if self._intent_embeddings is None:
            return self._fallback_intent_classification(user_message)
        
        try:
            # Get embedding for user message
            if hasattr(self.service, 'embedding_service') and self.service.embedding_service:
                user_embedding = self.service.embedding_service.get_embedding(user_message)
                
                # Calculate cosine similarities
                import numpy as np
                similarities = np.dot(self._intent_embeddings, user_embedding) / (
                    np.linalg.norm(self._intent_embeddings, axis=1) * np.linalg.norm(user_embedding)
                )
                
                # Get best match
                best_idx = np.argmax(similarities)
                confidence = similarities[best_idx]
                
                if confidence > 0.5:  # Confidence threshold
                    intent = self._intent_labels[best_idx]
                    print(f"🎯 Intent classified: {intent} (confidence: {confidence:.3f})")
                    return intent
                else:
                    print(f"🤷 Low confidence ({confidence:.3f}), using general help")
                    return 'general_help'
            
        except Exception as e:
            print(f"⚠️  Intent classification error: {e}")
        
        return self._fallback_intent_classification(user_message)
    
    def _fallback_intent_classification(self, user_message: str) -> str:
        """Enhanced fallback pattern-based intent classification"""
        user_message_lower = user_message.lower()
        
        # Storage patterns
        if any(phrase in user_message_lower for phrase in [
            'remember', 'save', 'store', 'keep track', 'note this', 'record that',
            'i need to save', 'let me store', 'please remember'
        ]):
            return 'store_memory'
            
        # Search patterns  
        elif any(phrase in user_message_lower for phrase in [
            'find', 'search', 'look for', 'recall information', 'help me recall',
            'show me what i know', 'do i have anything', 'what do i know about'
        ]):
            return 'search_memories'
            
        # Statistics patterns
        elif any(phrase in user_message_lower for phrase in [
            'stats', 'statistics', 'count', 'how many', 'current status',
            'system status', 'memory count', 'total memories'
        ]):
            return 'get_statistics'
            
        # Summary patterns
        elif any(phrase in user_message_lower for phrase in [
            'summarize', 'summary', 'overview', 'what i\'ve stored', 'stored recently',
            'give me an overview', 'review my memories', 'what have i learned'
        ]):
            return 'summarize_memories'
            
        # Context patterns
        elif any(phrase in user_message_lower for phrase in [
            'context', 'background', 'what do you know', 'tell me about',
            'give me context', 'background information'
        ]):
            return 'get_context'
            
        else:
            return 'general_help'

    def generate_response(self, user_message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate intelligent response using NLP intent classification"""
        
        # Classify the user's intent using semantic similarity
        intent = self._classify_intent(user_message)
        
        try:
            # Handle each intent with appropriate logic
            if intent == 'store_memory':
                return self._handle_store_memory(user_message)
                
            elif intent == 'search_memories':
                return self._handle_search_memories(user_message)
                
            elif intent == 'get_statistics':
                return self._handle_get_statistics(user_message)
                
            elif intent == 'summarize_memories':
                return self._handle_summarize_memories(user_message)
                
            elif intent == 'get_context':
                return self._handle_get_context(user_message)
                
            else:  # general_help
                return self._handle_general_help(user_message)
                
        except Exception as e:
            return {
                'type': 'error',
                'message': f"Processing error: {str(e)}"
            }
    
    def _handle_store_memory(self, user_message: str) -> Dict[str, Any]:
        """Handle memory storage requests"""
        # Extract content to remember
        content = user_message
        user_message_lower = user_message.lower()
        
        for trigger in ['remember', 'store', 'save']:
            if trigger in user_message_lower:
                idx = user_message_lower.index(trigger)
                content = user_message[idx + len(trigger):].strip()
                if content.startswith('that '):
                    content = content[5:]
                break
        
        if len(content) > 10:  # Meaningful content
            result = self.service.store_memory(content=content, source='librarian_gui')
            return {
                'type': 'memory_stored',
                'result': result,
                'content': content
            }
        else:
            return {
                'type': 'error',
                'message': "Please provide more details about what you'd like to remember."
            }
    
    def _handle_search_memories(self, user_message: str) -> Dict[str, Any]:
        """Handle memory search requests"""
        # Extract search terms
        search_terms = user_message
        user_message_lower = user_message.lower()
        
        for trigger in ['find', 'search', 'look for', 'show me']:
            if trigger in user_message_lower:
                idx = user_message_lower.index(trigger)
                search_terms = user_message[idx + len(trigger):].strip()
                break
        
        if len(search_terms) > 2:
            results = self.service.search_memories(query=search_terms, limit=5)
            return {
                'type': 'search_results',
                'query': search_terms,
                'results': results,
                'count': len(results)
            }
        else:
            return {
                'type': 'error',
                'message': "Please specify what you'd like to search for."
            }
    
    def _handle_get_statistics(self, user_message: str) -> Dict[str, Any]:
        """Handle statistics requests"""
        stats = self.service.get_statistics()
        return {
            'type': 'statistics',
            'stats': stats
        }
    
    def _handle_summarize_memories(self, user_message: str) -> Dict[str, Any]:
        """Handle memory summary requests"""
        results = self.service.search_memories(limit=20)
        if results:
            # Group by category and project
            categories = {}
            projects = set()
            
            for memory in results:
                category = memory.get('category', 'general')
                project = memory.get('project', 'general')
                projects.add(project)
                
                if category not in categories:
                    categories[category] = []
                categories[category].append(memory['content'][:100] + '...' if len(memory['content']) > 100 else memory['content'])
            
            summary = f"You have {len(results)} memories across {len(projects)} projects:\n\n"
            
            for category, memories in categories.items():
                summary += f"**{category.title()}** ({len(memories)}):\n"
                for i, memory in enumerate(memories[:3], 1):
                    summary += f"  {i}. {memory}\n"
                if len(memories) > 3:
                    summary += f"  ... and {len(memories) - 3} more\n"
                summary += "\n"
            
            summary += f"**Projects**: {', '.join(sorted(projects))}"
            
            return {
                'type': 'memory_summary',
                'summary': summary,
                'total_count': len(results)
            }
        else:
            return {
                'type': 'memory_summary',
                'summary': "You don't have any memories stored yet. Start by saying 'Remember that...' to store your first insight!",
                'total_count': 0
            }
    
    def _handle_get_context(self, user_message: str) -> Dict[str, Any]:
        """Handle context generation requests"""
        # Extract topic
        topic = user_message
        user_message_lower = user_message.lower()
        
        for trigger in ['context', 'background', 'what do you know about']:
            if trigger in user_message_lower:
                idx = user_message_lower.index(trigger)
                topic = user_message[idx + len(trigger):].strip()
                break
        
        if len(topic) > 2:
            context_text = self.service.get_context(relevant_to=topic, max_tokens=2000)
            return {
                'type': 'context_generated',
                'topic': topic,
                'context': context_text
            }
        else:
            return {
                'type': 'error',
                'message': "Please specify what topic you'd like context for."
            }
    
    def _handle_general_help(self, user_message: str) -> Dict[str, Any]:
        """Handle general help requests"""
        return {
            'type': 'general_help',
            'message': """I'm your AI Memory Librarian! I can help you with:

• **Storing memories**: "Remember that React hooks are better than classes"
• **Finding information**: "Find memories about authentication" 
• **Getting context**: "What do you know about database optimization"
• **System stats**: "How many memories do I have?"
• **Summarizing**: "Summarize my memories so far"

What would you like to do?""",
            'suggestions': [
                "Remember that JWT auth is working perfectly",
                "Find memories about React", 
                "Summarize my memories so far",
                "How many memories do I have?",
                "What do you know about databases?"
            ]
        }

# Global librarian agent
librarian: Optional[LibrarianAgent] = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global memory_service, librarian
    
    try:
        memory_service = get_memory_service()
        librarian = LibrarianAgent(memory_service)
        print("✅ Memory service and librarian initialized")
    except Exception as e:
        print(f"❌ Failed to initialize services: {e}")
        sys.exit(1)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main librarian interface"""
    return templates.TemplateResponse("librarian.html", {
        "request": request,
        "title": "Universal AI Memory Librarian"
    })

@app.get("/api/stats")
async def get_stats():
    """Get system statistics"""
    try:
        stats = memory_service.get_statistics()
        health = memory_service.health_check()
        return {
            "stats": stats,
            "health": health,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects")
async def get_projects():
    """Get all projects"""
    try:
        projects = memory_service.get_projects()
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search")
async def search_memories(q: str = "", project: str = None, category: str = None, limit: int = 10):
    """Search memories via REST API"""
    try:
        results = memory_service.search_memories(
            query=q if q else None,
            project=project,
            category=category,
            limit=limit
        )
        return {
            "query": q,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/store")
async def store_memory(request: Request):
    """Store a new memory"""
    try:
        data = await request.json()
        result = memory_service.store_memory(**data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/context")
async def get_context(request: Request):
    """Generate context"""
    try:
        data = await request.json()
        context = memory_service.get_context(**data)
        return {"context": context}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket for real-time chat
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for chat interface"""
    await websocket.accept()
    
    try:
        # Send welcome message
        welcome = {
            "type": "system",
            "message": "👋 Hello! I'm your AI Memory Librarian. How can I help you today?",
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(welcome))
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            user_message = message_data.get("message", "")
            
            # Generate response using librarian agent
            response = librarian.generate_response(user_message)
            response["timestamp"] = datetime.now().isoformat()
            
            # Send response back to client
            await websocket.send_text(json.dumps(response))
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        error_response = {
            "type": "error",
            "message": f"Error processing message: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(error_response))

if __name__ == "__main__":
    # Run the web server
    import argparse
    
    parser = argparse.ArgumentParser(description="Universal AI Memory Librarian GUI")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8092, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    print(f"🧠 Starting Universal AI Memory Librarian on http://{args.host}:{args.port}")
    print("📚 Web interface will be available at the URL above")
    
    uvicorn.run(
        "librarian_gui:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )