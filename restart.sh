#!/bin/bash

# Colors for better output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}===== JobHunterAI Debug Launcher =====${NC}"

# Kill any existing Flask processes
echo -e "${GREEN}Stopping any running instances...${NC}"
pkill -f "python debug_app.py" || true
sleep 1

# Function to find an available port starting from the base port
find_available_port() {
    local port=$1
    while netstat -an | grep "LISTEN" | grep -q ":$port "; do
        echo -e "${BLUE}Port $port is in use, trying next port...${NC}"
        port=$((port + 1))
    done
    echo $port
}

# Set default port and find available one
DEFAULT_PORT=8088
PORT=$(find_available_port $DEFAULT_PORT)

# Start the application
echo -e "${BLUE}Starting debug application...${NC}"
echo -e "${GREEN}URL:${NC} http://localhost:$PORT"
echo -e "${BLUE}Press Ctrl+C to stop the application${NC}"
echo -e "${BLUE}=================================${NC}"

# Run with the available port
export FLASK_RUN_PORT=$PORT
python debug_app.py
