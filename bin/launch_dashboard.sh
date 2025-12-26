#!/bin/bash
# Launch script for Live Trading Dashboard
# Activates venv and runs the dashboard in a terminal

cd /home/hektic/hekstradehub
source .venv/bin/activate

# Run the live dashboard
python monitoring/live_dashboard.py

# Keep terminal open if there's an error
if [ $? -ne 0 ]; then
    echo ""
    echo "Press Enter to close..."
    read
fi
