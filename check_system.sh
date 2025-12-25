#!/bin/bash
# Quick system health check for trading setup

echo "🔍 KuCoin Trading System Health Check"
echo "========================================"
echo ""

cd /home/hektic/hekstradehub
source .venv/bin/activate 2>/dev/null

# Check auto-trailing manager
echo "📊 Auto-Trailing Manager:"
if ps aux | grep -q "[a]uto_trailing_manager"; then
    PID=$(ps aux | grep "[a]uto_trailing_manager" | awk '{print $2}')
    echo "  ✅ Running (PID: $PID)"
    if [ -f auto_trail.log ]; then
        echo "  📝 Last activity:"
        tail -2 auto_trail.log | sed 's/^/     /'
    fi
else
    echo "  ❌ NOT RUNNING"
    echo "  ℹ️  Start with: nohup python auto_trailing_manager.py ... &"
fi
echo ""

# Check .env file
echo "🔑 API Configuration:"
if [ -f .env ]; then
    if grep -q "KUCOIN_API_KEY" .env && [ -n "$(grep KUCOIN_API_KEY .env | cut -d'=' -f2)" ]; then
        echo "  ✅ KuCoin credentials configured"
    else
        echo "  ⚠️  .env exists but KuCoin keys missing"
    fi
else
    echo "  ❌ .env file not found"
fi
echo ""

# Check Python environment
echo "🐍 Python Environment:"
if [ -d .venv ]; then
    echo "  ✅ Virtual environment exists"
    python --version 2>&1 | sed 's/^/     /'
    
    # Check critical packages
    if python -c "import ccxt" 2>/dev/null; then
        echo "  ✅ ccxt installed ($(python -c 'import ccxt; print(ccxt.__version__)' 2>/dev/null))"
    else
        echo "  ❌ ccxt not installed"
    fi
    
    if python -c "import pandas" 2>/dev/null; then
        echo "  ✅ pandas installed"
    else
        echo "  ⚠️  pandas not installed"
    fi
else
    echo "  ❌ Virtual environment not found"
fi
echo ""

# Check KuCoin connection
echo "📡 KuCoin Connection:"
python -c "
import ccxt, os
from dotenv import load_dotenv
load_dotenv()
try:
    exchange = ccxt.kucoinfutures({
        'apiKey': os.getenv('KUCOIN_API_KEY'),
        'secret': os.getenv('KUCOIN_SECRET'),
        'password': os.getenv('KUCOIN_PASSPHRASE'),
        'timeout': 10000
    })
    balance = exchange.fetch_balance()
    usdt = balance['USDT']['free']
    print(f'  ✅ Connected')
    print(f'  💰 Balance: \${usdt:.2f} USDT')
    
    # Check for open positions
    positions = exchange.fetch_positions()
    active = [p for p in positions if p.get('contracts', 0) > 0]
    if active:
        print(f'  📊 Open Positions: {len(active)}')
        for p in active:
            pnl = p.get('unrealizedPnl', 0)
            pnl_color = '🟢' if pnl >= 0 else '🔴'
            print(f'     {pnl_color} {p[\"symbol\"]}: {p[\"side\"]} {p[\"contracts\"]} contracts @ \${p[\"entryPrice\"]}, PnL: \${pnl:.3f}')
    else:
        print('  📊 No open positions')
except Exception as e:
    print(f'  ❌ Connection failed: {e}')
" 2>&1
echo ""

# Check desktop launcher
echo "🖥️  Desktop Launcher:"
if [ -f ~/Desktop/Trading-Dashboard.desktop ]; then
    echo "  ✅ Desktop icon installed"
else
    echo "  ⚠️  Desktop icon missing"
    echo "  ℹ️  Run: bash install_desktop_icon.sh"
fi
echo ""

# Check trade journal
echo "📔 Trade Journal:"
if [ -f trade_journal.json ]; then
    TRADES=$(python -c "import json; print(len(json.load(open('trade_journal.json'))))" 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "  ✅ $TRADES trades recorded"
    else
        echo "  ✅ Journal exists (empty)"
    fi
else
    echo "  ℹ️  No trades logged yet"
    echo "  ℹ️  Log first trade: python trade_journal.py log"
fi
echo ""

# Check log files
echo "📝 Recent Logs:"
for log in auto_trail.log trading.log; do
    if [ -f $log ]; then
        SIZE=$(du -h $log | cut -f1)
        echo "  📄 $log ($SIZE)"
    fi
done
echo ""

echo "========================================"
echo "✅ System check complete"
echo ""
echo "Quick commands:"
echo "  • Monitor position: python live_dashboard.py"
echo "  • Find opportunity: python quick_scalp_finder.py --scan"
echo "  • Log trade: python trade_journal.py log"
echo "  • View logs: tail -f auto_trail.log"
echo ""
