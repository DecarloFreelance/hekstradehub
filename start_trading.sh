#!/bin/bash
# Small Account Trading Startup Script
# Always run this before trading to ensure proper environment

cd /home/hektic/hekstradehub

# Activate virtual environment
echo "🔧 Activating Python environment..."
source .venv/bin/activate

# Check critical dependencies
echo "✅ Checking dependencies..."
python -c "import ccxt; import pandas; from dotenv import load_dotenv" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Missing dependencies! Installing..."
    pip install -q ccxt pandas python-dotenv ta-lib
fi

# Check RAM protection
echo "🛡️  Checking RAM protection..."
if [ -f "/home/hektic/saddynhektic workspace/Tools/resource_manager.py" ]; then
    echo "✅ RAM protection available"
else
    echo "⚠️  RAM protection not found at expected location"
fi

# Check API credentials
echo "🔑 Checking API credentials..."
if [ -f ".env" ]; then
    if grep -q "KUCOIN_API_KEY" .env && grep -q "KUCOIN_API_SECRET" .env; then
        echo "✅ KuCoin API credentials configured"
    else
        echo "⚠️  KuCoin API credentials missing in .env"
    fi
else
    echo "❌ .env file not found!"
fi

# Show account balance
echo ""
echo "💰 Fetching account balance..."
python check_position.py 2>/dev/null

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 SMALL ACCOUNT TRADING SYSTEM READY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Quick Commands:"
echo "  📊 Find trades:      python quick_scalp_finder.py --scan"
echo "  🧮 Calculate size:   python small_account_manager.py calc"
echo "  👀 Monitor position: python live_dashboard.py"
echo "  📝 Log trade:        python trade_journal.py log"
echo "  📈 View stats:       python trade_journal.py stats 7"
echo ""
echo "Full guide: cat SMALL_ACCOUNT_GUIDE.md"
echo ""
