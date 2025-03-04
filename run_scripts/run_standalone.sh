#!/bin/bash

# Colors for better output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}===== JobHunterAI Standalone Launcher =====${NC}"

# Kill any running instances of the app
echo -e "${GREEN}Stopping any running instances...${NC}"
pkill -f "python.*standalone_job_search.py" || true
# Make sure we wait for processes to fully terminate
sleep 1

# Change to the project directory
cd "$(dirname "$0")/.." || exit

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo -e "${GREEN}Activating virtual environment...${NC}"
    source venv/bin/activate
fi

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
DEFAULT_PORT=9091
PORT=$(find_available_port $DEFAULT_PORT)

# Run the standalone application
echo -e "${BLUE}Starting standalone JobHunterAI application...${NC}"
echo -e "${GREEN}Test user:${NC} email=test@example.com, password=password"
echo -e "${GREEN}URL:${NC} http://localhost:$PORT"
echo -e "${BLUE}Press Ctrl+C to stop the application${NC}"
echo -e "${BLUE}=================================${NC}"

# Run with the available port
export FLASK_RUN_PORT=$PORT
python standalone_job_search.py