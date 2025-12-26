#!/bin/bash
# ADA SHORT Trade - Auto-setup stops after entry fills

echo "🎯 Waiting for ADA SHORT entry to fill..."
echo "Order ID: 393603231181234176"
echo "Entry: \$0.3567 | Stop: \$0.3580"
echo ""

cd /home/hektic/hekstradehub
source .venv/bin/activate

# Monitor for position
while true; do
    # Check for position
    HAS_POSITION=$(python -c "
import ccxt, os
from dotenv import load_dotenv
load_dotenv()
ex = ccxt.kucoinfutures({'apiKey': os.getenv('KUCOIN_API_KEY'), 'secret': os.getenv('KUCOIN_API_SECRET'), 'password': os.getenv('KUCOIN_API_PASSPHRASE'), 'enableRateLimit': True})
pos = ex.fetch_positions(['ADA/USDT:USDT'])
active = [p for p in pos if float(p.get('contracts', 0)) != 0]
print('yes' if active else 'no')
" 2>/dev/null)
    
    if [ "$HAS_POSITION" == "yes" ]; then
        echo ""
        echo "✅ ENTRY FILLED! Setting stops now..."
        echo ""
        
        # Place stop loss and take profits
        python order_manager.py set-stops ADA/USDT:USDT 0.3580 0.3540 0.3524
        
        echo ""
        echo "🎯 Trade fully configured!"
        echo ""
        echo "Start monitoring:"
        echo "  python live_dashboard.py"
        echo ""
        break
    else
        echo -ne "\r⏳ Waiting for fill... (checking every 10s)"
        sleep 10
    fi
done
