"""
Shared configuration for Universal Memory System
This file defines paths for the shared installation
"""
import os

# Shared paths
SHARED_BASE = "/Users/admin/universal-memory-system"
SHARED_DATA = "/Users/admin/.ai-memory"

# Database paths
DATABASE_PATH = os.path.join(SHARED_DATA, "databases", "memories.db")
LOG_PATH = os.path.join(SHARED_DATA, "logs")

# API configuration
API_HOST = "localhost"
API_PORT = 8091

# Ensure directories exist
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
os.makedirs(LOG_PATH, exist_ok=True)
