#!/bin/bash

# Kill any running instances of the app
pkill -f "python.*standalone_job_search.py" || true

# Change to the project directory
cd "$(dirname "$0")/.." || exit

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Run the standalone application
echo "Starting standalone JobHunterAI application with job search feature..."
python standalone_job_search.py