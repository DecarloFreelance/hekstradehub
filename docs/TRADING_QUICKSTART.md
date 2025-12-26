# 🚀 KuCoin Futures Trading - Quick Start Guide

**Account Balance:** $5.83 USDT  
**Strategy:** 5m/15m scalping with automated stops & trailing  
**Status:** Test phase (manual observation → future automation)

---

## 📊 Daily Workflow

### 1. Find Opportunity
```bash
cd ~/hekstradehub
source .venv/bin/activate
python quick_scalp_finder.py --scan
```
- Look for **70+ score** (green)
- Checks 5m/15m momentum, RSI, MACD, ADX, volume
- Shows LONG or SHORT direction

### 2. Calculate Position Size
```bash
python small_account_manager.py --symbol ADA/USDT:USDT --price 0.3568 --direction SHORT
```
- Shows max contracts for $5.83 account
- Calculates margin needed (max 80% of balance)
- Displays projected profit after 0.12% fees

### 3. Execute Trade
```bash
python order_manager.py full-trade ADA/USDT:USDT SHORT 0.3568 10
```
- Places entry at market price
- Sets stop loss (0.33% away)
- Sets TP1 at 2R (60% close)
- Sets TP2 at 4R (40% close)
- Auto-trailing activates when TP1 hits

### 4. Monitor Position
**Option A:** Desktop launcher
- Double-click `Trading Dashboard` icon on desktop
- Updates every 5 seconds

**Option B:** Terminal
```bash
python live_dashboard.py
```

### 5. After Position Closes
```bash
python trade_journal.py log
```
- Records entry/exit prices, P&L, hold time
- Tracks lessons learned
- Builds performance history

---

## 🛡️ Safety Features

**Active Protection:**
- ✅ Stop loss auto-placed (0.33% away = 3.3x max risk buffer)
- ✅ Take profits at 2R and 4R
- ✅ Auto-trailing starts after TP1 (locks in profits)
- ✅ All orders use `reduceOnly=True` (can't open new positions by accident)

**Position Limits:**
- Max risk: 3% per trade ($0.17)
- Max margin: 80% of balance ($4.66)
- Leverage: 10x (safe for small account)

**Monitoring:**
- Auto-trailing manager runs in background
- Checks position every 10 seconds
- Logs all activity to `auto_trail.log`

---

## 🔧 Troubleshooting

### Check if auto-trailing is running
```bash
ps aux | grep auto_trailing_manager
tail -f auto_trail.log
```

### Restart auto-trailing (if stopped)
```bash
cd ~/hekstradehub
source .venv/bin/activate
nohup python auto_trailing_manager.py ADA/USDT:USDT SHORT 0.3568 0.3580 0.3540 0.3524 10 > /dev/null 2>&1 &
```

### Check KuCoin connection
```bash
python test_kucoin_orders.py
```

### View current position
```bash
python -c "
import ccxt, os
from dotenv import load_dotenv
load_dotenv()
exchange = ccxt.kucoinfutures({
    'apiKey': os.getenv('KUCOIN_API_KEY'),
    'secret': os.getenv('KUCOIN_SECRET'),
    'password': os.getenv('KUCOIN_PASSPHRASE')
})
positions = exchange.fetch_positions()
for p in positions:
    if p['contracts'] and p['contracts'] > 0:
        print(f\"{p['symbol']}: {p['side']} {p['contracts']} contracts @ {p['entryPrice']}, PnL: ${p['unrealizedPnl']:.3f}\")
"
```

---

## 📁 File Reference

### Core Trading Tools
- `quick_scalp_finder.py` - Scans for 70+ score setups
- `small_account_manager.py` - Position sizing calculator
- `order_manager.py` - Places entry/stops/TPs with correct KuCoin format
- `auto_trailing_manager.py` - Monitors position, auto-starts trailing
- `auto_trailing_stop.py` - Executes trailing stop logic (ATR-based)
- `live_dashboard.py` - Real-time position monitoring
- `trade_journal.py` - Performance tracking and notes

### Configuration
- `.env` - KuCoin API credentials
- `auto_trail.log` - Auto-trailing activity log

### Desktop
- `~/Desktop/Trading-Dashboard.desktop` - Double-click launcher
- `launch_dashboard.sh` - Wrapper script (activates venv)
- `dashboard_icon.png` - Custom icon

---

## 🎯 Current Trade

**Symbol:** ADA/USDT SHORT  
**Entry:** $0.3568 (10 contracts)  
**Stop Loss:** $0.3580 (-$0.12 max loss)  
**TP1:** $0.3540 (+$0.17 on 60% close) ← Auto-trailing activates here  
**TP2:** $0.3524 (+$0.11 on 40% close)  

**Risk/Reward:** 1:5 (risking $0.12 to make $0.28)  
**Margin Used:** $4.64 / $5.83 (79.6%)  
**Auto-Trailing:** Active (PID varies, check with `ps aux | grep auto_trailing`)

---

## 🚀 Next Steps (After Test Phase)

Once 5-10 trades are logged and 60%+ win rate validated:

### Automated Trading Bot
```bash
python automated_trading_bot.py
```

**Features:**
- Continuous scanning for opportunities
- Auto-executes trades when 70+ score found
- Logs all trades automatically
- Telegram alerts for entries/exits
- Daily loss circuit breaker
- Max trades per day limit

**Prerequisites:**
- Proven strategy (60%+ wins)
- Balance > $20 (for sustainability)
- Telegram bot configured
- Emergency stop mechanism tested

---

## 📝 Trading Notes Template

After each trade closes, document:

1. **Setup Quality:** Was the 70+ score accurate?
2. **Entry Timing:** Did price move immediately or chop first?
3. **Stop Placement:** Was stop hit or avoided?
4. **TP Levels:** Did TP1 hit? TP2? Trailing work?
5. **Hold Time:** How long until close?
6. **Lessons:** What would you do differently?
7. **P&L:** Net profit after 0.12% fees

Save in trade journal: `python trade_journal.py log`

---

**Created:** Dec 25, 2025  
**Version:** 1.0 - Test Phase  
**Location:** ~/hekstradehub/
