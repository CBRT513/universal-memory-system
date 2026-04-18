#!/bin/bash

# UMS Global Capture startup script
echo "Starting UMS Global Capture..."

# Set development mode environment
export DEV_MODE=true
export NODE_ENV=development

# Start the global capture process
# Adjust this command based on your actual global capture implementation
if [ -f "/Users/equillabs/Desktop/UMS-Browser-Extension/global_capture.js" ]; then
    /usr/local/bin/node /Users/equillabs/Desktop/UMS-Browser-Extension/global_capture.js
elif [ -f "/Users/equillabs/Desktop/UMS-Browser-Extension/global-capture/index.js" ]; then
    /usr/local/bin/node /Users/equillabs/Desktop/UMS-Browser-Extension/global-capture/index.js
else
    echo "Global capture script not found. Please configure the correct path."
    # Keep the process alive to prevent constant restart attempts
    while true; do
        sleep 3600
    done
fi