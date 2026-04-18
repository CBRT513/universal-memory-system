#!/usr/bin/env python3
"""
Article Capture API Endpoints - Milestone A
Adds capture functionality to the UMS API
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from capture_service import get_capture_service
from capture_metrics import get_metrics_service

logger = logging.getLogger(__name__)

# Create router for capture endpoints
capture_router = APIRouter(prefix="/api", tags=["capture"])

# Pydantic models
class CaptureRequest(BaseModel):
    url: Optional[str] = Field(None, description="URL to capture")
    text: Optional[str] = Field(None, description="Raw text to capture")
    notes: Optional[str] = Field(None, description="User notes about this capture")
    project: Optional[str] = Field("vader-lab", description="Project name")

class ClientCaptureRequest(BaseModel):
    url: str = Field(..., description="Source URL")
    title: str = Field(..., description="Page title from client")
    text: str = Field(..., description="Extracted text from client")
    notes: Optional[str] = Field(None, description="User notes")
    project: Optional[str] = Field("vader-lab", description="Project name")

class CaptureResponse(BaseModel):
    job_id: str

# Initialize service
capture_service = get_capture_service()

@capture_router.on_event("startup")
async def startup_event():
    """Start the capture worker on API startup"""
    capture_service.start_worker()
    logger.info("Capture worker started")

@capture_router.post("/capture", response_model=CaptureResponse, status_code=202)
async def create_capture(request: CaptureRequest):
    """
    Submit content for capture and processing
    Returns 202 with job_id for status tracking
    """
    
    # Validate input
    if not request.url and not request.text:
        raise HTTPException(status_code=400, detail="Must provide either URL or text")
    
    # Enqueue the capture job
    job_id = await capture_service.enqueue_capture(
        url=request.url,
        text=request.text,
        notes=request.notes,
        project=request.project
    )
    
    return CaptureResponse(job_id=job_id)

@capture_router.get("/capture/stats")
async def get_capture_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    project: Optional[str] = None
):
    """
    Get capture statistics and analytics
    
    Query params:
    - start_date: ISO format date (defaults to 7 days ago)
    - end_date: ISO format date (defaults to now)
    - project: Filter by project name
    
    Returns comprehensive metrics including:
    - Summary counts and success rates
    - Performance percentiles
    - Top domains
    - Failure breakdown
    - Time series data
    """
    metrics_service = get_metrics_service()
    
    try:
        stats = metrics_service.get_stats(
            start_date=start_date,
            end_date=end_date,
            project=project
        )
        return stats
    except Exception as e:
        logger.error(f"Failed to get capture stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

@capture_router.get("/capture/stats/realtime")
async def get_realtime_stats():
    """
    Get real-time capture statistics for the last hour
    Useful for monitoring dashboards
    """
    metrics_service = get_metrics_service()
    
    try:
        stats = metrics_service.get_realtime_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get realtime stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve realtime statistics")

@capture_router.post("/capture/from_client", response_model=CaptureResponse)
async def capture_from_client(request: ClientCaptureRequest):
    """
    Accept client-supplied DOM content (from browser extension or bookmarklet).
    Bypasses server fetch, stores the provided text directly.
    """
    
    # Initialize capture service  
    capture_service = get_capture_service()
    
    # Enqueue the capture job with client-provided content
    # This will skip fetch since we have text, but still run dedup/summarize
    job_id = await capture_service.enqueue_capture_from_client(
        url=request.url,
        title=request.title,
        text=request.text,
        notes=request.notes,
        project=request.project
    )
    
    return CaptureResponse(job_id=job_id)

@capture_router.get("/capture/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of a capture job"""
    
    status = capture_service.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Format response
    response = {
        "status": status.get("state", "unknown"),
        "message": status.get("msg", ""),
        "cached": status.get("cached", False),
        "http_status": status.get("http_status"),
        "cause": status.get("cause"),
        "timings": status.get("timings")
    }
    
    # If done, include the result
    if status.get("state") == "done" and status.get("capture_id"):
        capture = capture_service.get_capture(status["capture_id"])
        if capture:
            response["result"] = {
                "id": capture["id"],
                "created_at": capture["created_at"],
                "source": {
                    "url": capture.get("source_url"),
                    "domain": capture.get("source_domain"),
                    "title": capture.get("source_title"),
                    "author": capture.get("source_author")
                },
                "summary": capture.get("summary", ""),
                "notes": capture.get("notes", ""),
                "project": capture.get("project", "vader-lab")
            }
    
    # If error, include error message
    if status.get("state") == "error":
        response["error"] = status.get("error", "Processing failed")
    
    return response

@capture_router.get("/capture/{job_id}/stream")
async def stream_job_status(job_id: str, request: Request):
    """
    Stream job status updates via Server-Sent Events (SSE)
    """
    
    async def event_generator():
        """Generate SSE events for job status"""
        
        # Check if job exists
        initial_status = capture_service.get_job_status(job_id)
        if not initial_status:
            yield {
                "event": "error",
                "data": json.dumps({"error": "Job not found"})
            }
            return
        
        # Stream updates
        last_state = None
        error_count = 0
        max_errors = 100  # Prevent infinite loops
        
        while error_count < max_errors:
            # Check if client disconnected
            if await request.is_disconnected():
                break
            
            # Get current state
            if job_id in capture_service.job_states:
                current = capture_service.job_states[job_id]
                current_state = current.get("state")
                
                # Send update if state changed
                if current_state != last_state:
                    event_data = {
                        "state": current_state,
                        "msg": current.get("msg", ""),
                        "stage": current.get("stage")
                    }
                    yield {
                        "event": "progress",
                        "data": json.dumps(event_data)
                    }
                    last_state = current_state
                
                # If done or error, send final event and close
                if current_state in ["done", "error"]:
                    if current_state == "done":
                        # Get the full capture result
                        capture_id = current.get("capture_id")
                        if capture_id:
                            capture = capture_service.get_capture(capture_id)
                            if capture:
                                yield {
                                    "event": "done",
                                    "data": json.dumps({
                                        "id": capture["id"],
                                        "summary": capture.get("summary", ""),
                                        "cached": current.get("cached", False),
                                        "http_status": current.get("http_status"),
                                        "cause": current.get("cause"),
                                        "timings": current.get("timings")
                                    })
                                }
                    else:
                        yield {
                            "event": "error",
                            "data": json.dumps({
                                "error": current.get("msg", "Processing failed"),
                                "http_status": current.get("http_status"),
                                "cause": current.get("cause"),
                                "timings": current.get("timings")
                            })
                        }
                    break
            else:
                # Job might be done already (from cache)
                status = capture_service.get_job_status(job_id)
                if status and status.get("state") == "done":
                    yield {
                        "event": "done",
                        "data": json.dumps({
                            "cached": True,
                            "msg": "Retrieved from cache"
                        })
                    }
                    break
                error_count += 1
            
            # Wait before next check
            await asyncio.sleep(0.5)
    
    return EventSourceResponse(event_generator())

@capture_router.get("/capture/detail/{capture_id}")
async def get_capture_detail(capture_id: str):
    """Get full details of a capture"""
    
    capture = capture_service.get_capture(capture_id)
    if not capture:
        raise HTTPException(status_code=404, detail="Capture not found")
    
    return {
        "id": capture["id"],
        "created_at": capture["created_at"],
        "source": {
            "url": capture.get("source_url"),
            "domain": capture.get("source_domain"),
            "title": capture.get("source_title"),
            "author": capture.get("source_author")
        },
        "content": {
            "text": capture.get("text", ""),
            "summary": capture.get("summary", ""),
            "length_tokens": capture.get("length_tokens", 0)
        },
        "notes": capture.get("notes", ""),
        "project": capture.get("project", "vader-lab"),
        "status": capture.get("status", "done")
    }