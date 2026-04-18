#!/bin/bash

# Start Galactica Intelligence Services
echo "🌌 Starting Galactica Intelligence Services..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Check if UMS is running
if ! curl -s http://127.0.0.1:8091/api/health > /dev/null 2>&1; then
    echo -e "${YELLOW}Starting UMS base service...${NC}"
    cd /usr/local/share/universal-memory-system
    source venv/bin/activate
    python src/api_service.py --port 8091 &
    sleep 3
fi

# Start Galactica Intelligence API  
if ! curl -s http://127.0.0.1:8092/health > /dev/null 2>&1; then
    echo -e "${CYAN}Starting Galactica Intelligence API