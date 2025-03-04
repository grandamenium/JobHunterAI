#!/bin/bash

# Run the JobHunterAI application using the virtual environment

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Ensure instance directory exists with proper permissions
mkdir -p instance
chmod 777 instance

# Clean up any previous database to ensure a fresh start
if [ -f "instance/job_application_system.db" ]; then
    echo "Removing old database..."
    rm -f instance/job_application_system.db
fi

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Make sure all required packages are installed
pip install -r requirements.txt
pip install python-dotenv

# Run the auth tests to verify database functionality
echo "Running authentication tests..."
python test_auth.py

# Check if the tests passed
if [ $? -eq 0 ]; then
    echo "Authentication tests passed! Starting application..."
    
    # Run the application with maximum verbosity
    echo "Starting JobHunterAI application..."
    python main.py
else
    echo "Authentication tests failed. Please check the logs for details."
    exit 1
fi