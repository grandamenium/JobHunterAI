#!/bin/bash

# Colors for better output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}===== JobHunterAI Launcher =====${NC}"

# Kill any running instances of the app more aggressively
echo -e "${GREEN}Stopping any running instances...${NC}"
pkill -f "python.*standalone_job_search.py" || true
pkill -f "python.*job_search" || true

# Kill any process using our default port
DEFAULT_PORT=9091
PID=$(lsof -ti:$DEFAULT_PORT)
if [ ! -z "$PID" ]; then
    echo -e "${GREEN}Killing process $PID using port $DEFAULT_PORT...${NC}"
    kill -9 $PID || true
fi

# Make sure we wait for processes to fully terminate
sleep 2

# Change to the project directory
cd "$(dirname "$0")/.." || exit

# Display the current directory
echo -e "${GREEN}Project directory:${NC} $(pwd)"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo -e "${GREEN}Activating virtual environment...${NC}"
    source venv/bin/activate
else
    echo -e "${RED}Warning: Virtual environment not found. Using system Python.${NC}"
fi

# Check for .env file and create if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${GREEN}Creating sample .env file...${NC}"
    echo "# JobHunterAI environment variables
OPENAI_API_KEY=your_api_key_here
DATABASE_URL=sqlite:///instance/job_application_system.db
SESSION_SECRET=your_secret_key_for_flask_sessions
NO_BROWSER=false" > .env
    echo -e "${BLUE}Created .env file. Please edit it to add your OpenAI API key.${NC}"
fi

# Make sure config directory exists
if [ ! -d "config" ]; then
    echo -e "${GREEN}Creating config directory...${NC}"
    mkdir -p config
fi

# Check for config_secret.py and create if it doesn't exist
if [ ! -f "config/config_secret.py" ]; then
    echo -e "${GREEN}Creating sample config_secret.py file...${NC}"
    echo '"""
Secret configuration variables for JobHunterAI.
This file should not be committed to version control.
It is listed in .gitignore
"""

# OpenAI API key
OPENAI_API_KEY = "your_openai_api_key_here"

# Database settings
DATABASE_URL = "sqlite:///instance/job_application_system.db"

# Security
SECRET_KEY = "your_long_random_secret_key_here"' > config/config_secret.py
    echo -e "${BLUE}Created config_secret.py file. Please edit it to add your OpenAI API key.${NC}"
fi

# Print API key status
OPENAI_KEY=$(grep -o "OPENAI_API_KEY=.*" .env | cut -d= -f2)
if [[ "$OPENAI_KEY" == "your_api_key_here" || -z "$OPENAI_KEY" ]]; then
    echo -e "${RED}Warning: API key not set in .env file.${NC}"
    echo -e "${RED}Some features may not work. Please update the .env file with your OpenAI API key.${NC}"
else
    echo -e "${GREEN}OpenAI API key detected in .env file.${NC}"
fi

# Function to find an available port starting from the base port
find_available_port() {
    local port=$1
    local max_tries=20
    local try=0
    
    # Try to kill process using the default port first to free it
    PID=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$PID" ]; then
        echo -e "${GREEN}Killing process $PID using port $port...${NC}" >&2
        kill -9 $PID >/dev/null 2>&1 || true
        sleep 1
    fi
    
    # Keep trying ports until we find an available one
    while [ $try -lt $max_tries ]; do
        if ! lsof -i:$port >/dev/null 2>&1; then
            # Port is available
            break
        else
            echo -e "${BLUE}Port $port is still in use, trying next port...${NC}" >&2
            port=$((port + 1))
            try=$((try + 1))
        fi
    done
    
    # Return only the port number, nothing else
    printf "%d" $port
}

# Set default port and find available one (using a different port than the usual)
DEFAULT_PORT=9099  # Changed from 9091 to avoid conflicts
PORT=$(find_available_port $DEFAULT_PORT)

# Run the standalone application
echo -e "${BLUE}Starting JobHunterAI application...${NC}"
echo -e "${GREEN}Test user:${NC} email=test@example.com, password=password"
echo -e "${GREEN}URL:${NC} http://localhost:$PORT"
echo -e "${BLUE}Press Ctrl+C to stop the application${NC}"
echo -e "${BLUE}=================================${NC}"

# Run with the available port
export FLASK_RUN_PORT=$PORT
python standalone_job_search.py