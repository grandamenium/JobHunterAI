#\!/bin/bash

# Kill any existing Flask processes
pkill -f "python debug_app.py" || true
sleep 1

# Start the application
python debug_app.py
