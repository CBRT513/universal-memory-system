#!/usr/bin/env python3
"""
Galactica Enhanced API
Adds context-aware retrieval and intelligent triage to UMS
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from galactica_context import ContextDetector, ContextAwareMemory
from galactica_triage import TriageSystem, LearningService

app = FastAPI(title="Galactica Intelligence API")

# Initialize services
context_detector = ContextDetector()
triage_system = TriageSystem()
learning_service = LearningService(triage_system)
context_memory = ContextAwareMemory(context_detector)

# Request/Response models
class ContextRequest(BaseModel):
    path: str

class MemoryRequest(BaseModel):
    content: str
    project: Optional[str] = None
    tags: Optional[List[str]] = []
    importance: Optional[float] = 5.0

class RecallRequest(BaseModel):
    query: str
    project: Optional[str] = None
    context_path: Optional[str] = None
    limit: int = 20
    min_relevance: float = 3.0

# Context endpoints
@app.post("/context/detect")
async def detect_context(request: ContextRequest):
    """Detect project context from path"""
    try:
        context = context_detector.detect_context(request.path)
        return {
            "status": "success",
            "context": context.to_dict(),
            "related_projects": [
                c.name for c in context_detector.find_related_projects(context)
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/context/all")
async def get_all_contexts():
    """Get all known project contexts"""
    contexts = context_detector.get_all_contexts()
    return {
        "total": len(contexts),
        "contexts": [c.to_dict() for c in contexts]
    }

@app.post("/context/suggest")
async def suggest_keywords(request: ContextRequest):
    """Suggest keywords for a project"""
    context = context_detector.detect_context(request.path)
    suggestions = context_detector.suggest_keywords(context)
    return {
        "project": context.name,
        "current_keywords": context.keywords,
        "suggestions": suggestions
    }

# Triage endpoints
@app.post("/triage/score")
async def score_memory(memory: MemoryRequest):
    """Score a memory's relevance and importance"""
    memory_id = f"mem_{memory.content[:20]}_{hash(memory.content)}"
    score = triage_system.score_memory(memory_id, memory.content, memory.project)
    
    return {
        "memory_id": memory_id,
        "relevance": score.relevance,
        "importance": score.importance,
        "priority": score.compute_priority(),
        "decay_rate": score.decay_rate
    }

@app.post("/triage/decay")
async def apply_decay():
    """Apply time-based decay to all memories"""
    triage_system.apply_decay()
    return {"status": "decay applied"}

@app.get("/triage/top")
async def get_top_memories(context: Optional[str] = None, limit: int = 20):
    """Get highest priority memories"""
    memories = triage_system.get_top_memories(context, limit)
    return {
        "context": context,
        "total": len(memories),
        "memories": [
            {"id": mem_id, "priority": priority}
            for mem_id, priority in memories
        ]
    }

# Learning endpoints
@app.post("/learn/patterns")
async def extract_patterns(memories: List[Dict]):
    """Extract patterns from memories"""
    patterns = learning_service.extract_patterns(memories)
    return {
        "patterns_found": len(patterns),
        "patterns": patterns
    }

@app.get("/learn/insights")
async def get_insights():
    """Get cross-project insights"""
    insights = learning_service.identify_insights()
    return {
        "total_insights": len(insights),
        "insights": insights
    }

@app.get("/learn/suggestions")
async def get_improvement_suggestions():
    """Get suggestions for improving memory usage"""
    suggestions = learning_service.suggest_improvements()
    return {
        "suggestions": suggestions
    }

# Context-aware memory operations
@app.post("/memory/store")
async def store_contextual_memory(memory: MemoryRequest):
    """Store memory with context-aware scoring"""
    # Detect context if path provided
    if memory.project:
        context = context_detector.detect_context(memory.project)
        memory.tags = memory.tags or []
        memory.tags.append(f"project:{context.name}")
        memory.tags.extend(context.keywords[:3])  # Add top keywords
        
    # Score the memory
    memory_id = f"mem_{hash(memory.content)}_{len(memory.content)}"
    score = triage_system.score_memory(memory_id, memory.content, memory.project)
    
    return {
        "status": "stored",
        "memory_id": memory_id,
        "relevance": score.relevance,
        "importance": score.importance,
        "tags": memory.tags
    }

@app.post("/memory/recall")
async def recall_contextual_memories(request: RecallRequest):
    """Recall memories with context-aware filtering"""
    # Set context if provided
    if request.context_path:
        context = context_memory.set_context(request.context_path)
        project_filter = f"project:{context.name}"
    else:
        project_filter = None
        
    # This would integrate with existing UMS search
    # For now, return mock data showing the concept
    mock_memories = [
        {
            "id": "mem_123",
            "content": "Architecture decision: Use hnswlib for vector storage",
            "tags": ["galactica", "architecture"],
            "relevance": 9.0
        },
        {
            "id": "mem_456", 
            "content": "TODO: Implement context detection service",
            "tags": ["galactica", "todo"],
            "relevance": 8.0
        }
    ]
    
    # Apply context filtering
    if request.context_path:
        filtered = context_memory.filter_memories(
            mock_memories, 
            request.min_relevance
        )
    else:
        filtered = mock_memories
        
    return {
        "query": request.query,
        "context": request.context_path,
        "total": len(filtered),
        "memories": filtered[:request.limit]
    }

# Health check
@app.get("/health")
async def health_check():
    """Check Galactica services health"""
    return {
        "status": "healthy",
        "services": {
            "context_detector": "active",
            "triage_system": "active", 
            "learning_service": "active"
        },
        "total_contexts": len(context_detector.contexts),
    }

# Run the API
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("GALACTICA_PORT", 8093))
    uvicorn.run(app, host="0.0.0.0", port=port)