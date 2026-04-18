#!/usr/bin/env python3
"""
UMS Main API Server
Includes capture endpoints for VADER integration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Import our capture API router
from src.capture_api import router as capture_router
from src.capture_service import get_capture_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="UMS API", version="1.0.0")

# Configure CORS for VADER frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include capture router
app.include_router(capture_router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    service = get_capture_service()
    service.start_worker()
    logger.info("Started capture worker")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "UMS API Server", "version": "1.0.0"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}