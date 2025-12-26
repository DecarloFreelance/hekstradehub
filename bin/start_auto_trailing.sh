#!/bin/bash
# Start auto-trailing manager with venv activated

cd /home/hektic/hekstradehub
source .venv/bin/activate

# Start auto-trailing in background
nohup python automation/auto_trailing_manager.py "$@" > logs/auto_trail.log 2>&1 &

PID=$!
echo "✅ Auto-trailing manager started (PID: $PID)"
echo "📋 Monitor with: tail -f logs/auto_trail.log"
echo "🛑 Stop with: kill $PID"
