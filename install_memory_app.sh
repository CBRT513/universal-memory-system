#!/bin/bash

# Universal Memory System App Installer
# This script installs the Universal Memory System as a macOS application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Paths
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="Universal Memory System"
APP_BUNDLE="$APP_NAME.app"
INSTALL_DIR="/Applications"
APP_SUPPORT_DIR="$HOME/Library/Application Support/UniversalMemorySystem"
PYTHON_ENV_DIR="$APP_SUPPORT_DIR/venv"

echo -e "${GREEN}Universal Memory System Installer${NC}"
echo "===================================="
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}Error: This installer is for macOS only${NC}"
    exit 1
fi

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required but not installed${NC}"
    echo "Please install Python 3 from https://python.org or via Homebrew"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Create Application Support directory
echo -e "\n${YELLOW}Setting up application support directory...${NC}"
mkdir -p "$APP_SUPPORT_DIR"
mkdir -p "$APP_SUPPORT_DIR/logs"
mkdir -p "$APP_SUPPORT_DIR/data"

# Copy source files to Application Support
echo -e "\n${YELLOW}Copying memory system files...${NC}"
cp -r "$SCRIPT_DIR/src" "$APP_SUPPORT_DIR/"
cp -r "$SCRIPT_DIR/templates" "$APP_SUPPORT_DIR/" 2>/dev/null || true
cp -r "$SCRIPT_DIR/static" "$APP_SUPPORT_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR/requirements.txt" "$APP_SUPPORT_DIR/"

# Create Python virtual environment
echo -e "\n${YELLOW}Creating Python virtual environment...${NC}"
python3 -m venv "$PYTHON_ENV_DIR"

# Activate virtual environment and install dependencies
echo -e "\n${YELLOW}Installing Python dependencies...${NC}"
source "$PYTHON_ENV_DIR/bin/activate"

# Upgrade pip first
pip install --upgrade pip

# Install requirements
pip install -r "$APP_SUPPORT_DIR/requirements.txt"

# Deactivate virtual environment
deactivate

# Update the launcher script to use the virtual environment
echo -e "\n${YELLOW}Updating launcher script...${NC}"
cat > "$SCRIPT_DIR/$APP_BUNDLE/Contents/MacOS/UniversalMemorySystem" << 'EOF'
#!/bin/bash

# Universal Memory System Launcher
# This script starts the memory system API service and manages its lifecycle

# Get the app bundle path
APP_PATH="$(dirname "$(dirname "$(dirname "$0")")")"
APP_SUPPORT_DIR="$HOME/Library/Application Support/UniversalMemorySystem"
PYTHON_ENV="$APP_SUPPORT_DIR/venv"
PYTHON_PATH="$PYTHON_ENV/bin/python3"
LOG_DIR="$HOME/Library/Logs/UniversalMemorySystem"
PID_FILE="$APP_SUPPORT_DIR/memory.pid"

# Create necessary directories
mkdir -p "$LOG_DIR"
mkdir -p "$APP_SUPPORT_DIR"

# Function to check if memory service is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# Function to start the memory service
start_service() {
    if is_running; then
        echo "Memory System is already running"
        open -a Safari "http://localhost:8091/dashboard"
        exit 0
    fi
    
    echo "Starting Universal Memory System..."
    
    # Change to the app support directory
    cd "$APP_SUPPORT_DIR"
    
    # Set up environment
    export PYTHONPATH="$APP_SUPPORT_DIR/src:$PYTHONPATH"
    export MEMORY_API_PORT=8091
    export MEMORY_DB_PATH="$APP_SUPPORT_DIR/data/memories.db"
    export MEMORY_ENABLE_DEBUG=false
    
    # Activate virtual environment and start the API service
    source "$PYTHON_ENV/bin/activate"
    
    # Start the API service in the background
    nohup $PYTHON_PATH "$APP_SUPPORT_DIR/src/api_service.py" --port 8091 \
        > "$LOG_DIR/memory_service.log" 2>&1 &
    
    # Save PID
    echo $! > "$PID_FILE"
    
    # Wait a moment for the service to start
    sleep 3
    
    # Check if service started successfully
    if is_running; then
        echo "Memory System started successfully"
        
        # Wait a bit more for the service to be fully ready
        sleep 2
        
        # Open dashboard in browser
        open "http://localhost:8091/dashboard"
        
        # Show notification
        osascript -e 'display notification "Memory System is now running on port 8091" with title "Universal Memory System" sound name "Glass"'
    else
        echo "Failed to start Memory System"
        echo "Check logs at: $LOG_DIR/memory_service.log"
        rm -f "$PID_FILE"
        
        # Show error notification
        osascript -e 'display notification "Failed to start Memory System. Check logs." with title "Universal Memory System" sound name "Basso"'
        exit 1
    fi
}

# Function to stop the memory service
stop_service() {
    if is_running; then
        PID=$(cat "$PID_FILE")
        echo "Stopping Memory System (PID: $PID)..."
        kill $PID
        rm -f "$PID_FILE"
        
        # Show notification
        osascript -e 'display notification "Memory System has been stopped" with title "Universal Memory System"'
    else
        echo "Memory System is not running"
    fi
}

# Check if running from Finder (no arguments)
if [ $# -eq 0 ]; then
    # If service is running, open dashboard; otherwise start service
    if is_running; then
        open "http://localhost:8091/dashboard"
    else
        start_service
    fi
else
    # Handle command line arguments
    case "$1" in
        start)
            start_service
            ;;
        stop)
            stop_service
            ;;
        restart)
            stop_service
            sleep 2
            start_service
            ;;
        status)
            if is_running; then
                PID=$(cat "$PID_FILE")
                echo "Memory System is running (PID: $PID)"
                echo "Dashboard: http://localhost:8091/dashboard"
            else
                echo "Memory System is not running"
            fi
            ;;
        *)
            echo "Usage: $0 {start|stop|restart|status}"
            exit 1
            ;;
    esac
fi
EOF

# Make launcher executable
chmod +x "$SCRIPT_DIR/$APP_BUNDLE/Contents/MacOS/UniversalMemorySystem"

# Copy app to Applications folder
echo -e "\n${YELLOW}Installing app to Applications folder...${NC}"
if [ -d "$INSTALL_DIR/$APP_BUNDLE" ]; then
    echo -e "${YELLOW}Existing app found. Backing up...${NC}"
    mv "$INSTALL_DIR/$APP_BUNDLE" "$INSTALL_DIR/$APP_BUNDLE.backup.$(date +%Y%m%d_%H%M%S)"
fi

cp -R "$SCRIPT_DIR/$APP_BUNDLE" "$INSTALL_DIR/"

# Create command-line symlink
echo -e "\n${YELLOW}Creating command-line interface...${NC}"
SYMLINK_PATH="/usr/local/bin/memory-cli"
sudo mkdir -p /usr/local/bin

# Create CLI wrapper script
cat > /tmp/memory-cli << EOF
#!/bin/bash
# Universal Memory System CLI wrapper
source "$PYTHON_ENV_DIR/bin/activate"
python3 "$APP_SUPPORT_DIR/src/memory_cli.py" "\$@"
EOF

sudo mv /tmp/memory-cli "$SYMLINK_PATH"
sudo chmod +x "$SYMLINK_PATH"

echo -e "\n${GREEN}✓ Installation complete!${NC}"
echo ""
echo "The Universal Memory System has been installed to:"
echo "  • App: $INSTALL_DIR/$APP_BUNDLE"
echo "  • Data: $APP_SUPPORT_DIR"
echo "  • CLI: $SYMLINK_PATH"
echo ""
echo "You can now:"
echo "  1. Launch the app from Applications folder"
echo "  2. Use 'memory-cli' command in Terminal"
echo "  3. Open the dashboard at http://localhost:8091/dashboard"
echo ""
echo -e "${YELLOW}Starting the Memory System now...${NC}"

# Start the service
"$INSTALL_DIR/$APP_BUNDLE/Contents/MacOS/UniversalMemorySystem" start

echo ""
echo -e "${GREEN}Installation and startup complete!${NC}"