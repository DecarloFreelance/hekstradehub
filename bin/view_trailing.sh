#!/bin/bash
# View active trailing stop log
echo "📊 Active Trailing Stop Logs:"
echo ""
cd /home/hektic/hekstradehub/logs
ls -t trailing_stop_*.log 2>/dev/null | head -1 | while read log; do
    echo "Latest: $log"
    echo ""
    tail -f "$log"
done
