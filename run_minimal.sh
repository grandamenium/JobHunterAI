#\!/bin/bash

# Kill all running Python processes to free up ports
pkill -f "python .*_app.py" || true
sleep 1

# Run the minimal app
python minimal_app.py
