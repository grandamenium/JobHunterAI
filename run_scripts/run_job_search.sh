#!/bin/bash

# Kill any running instances of the app
pkill -f "python.*minimal_app.py" || true

# Change to the project directory
cd "$(dirname "$0")/.." || exit

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Run the application
echo "Starting JobHunterAI with job search feature..."
python minimal_app.py