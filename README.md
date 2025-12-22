# Professional Crypto Trading Dashboard

Unified institutional-grade crypto trading system for KuCoin with interactive dashboard, 8 technical indicators, and intelligent automation.

## Quick Start

**For New Users (First Time):**
```bash
git clone <your-repo-url>
cd Trade_Advice
./start.sh
```

The script automatically:
1. ✓ Creates Python virtual environment
2. ✓ Installs all dependencies
3. ✓ Prompts for KuCoin API credentials (optional - can skip)
4. ✓ Tests connection (if credentials provided)
5. ✓ Launches dashboard

**For Existing Users:**
```bash
./start.sh
```

Automatically activates your environment and launches the dashboard - no prompts!

**Running Without API Credentials (Limited Mode):**

You can explore the dashboard without KuCoin credentials:

**Available without API:**
- ✓ Help documentation and usage guides
- ✓ System information and configuration
- ✓ View trading strategies and indicators

**Requires API credentials:**
- Market scanning and analysis
- Position monitoring and tracking  
- Trailing stops and risk management
- All trading operations

*You can add credentials later via the System Information menu (option 8)*

## Dashboard Features

Interactive menu system with 6 core tools:

### Market Analysis
1. **Live Opportunity Watcher** - Real-time scanner with auto-alerts (60s updates)
2. **Institutional Scan** - One-time comprehensive market snapshot
3. **Coin Analyzer** - Deep dive on any specific symbol

### Position Management
4. **Position Monitor** - Track open positions with live indicators
5. **All Positions View** - Quick overview of all active trades

### Risk Management
6. **Smart Trailing Stop** - Dynamic indicator-based stop (adapts to market)
7. **Basic Trailing Stop** - Simple ATR or % based stop

### ⚙️ Utilities
8. **System Info** - Connection status and environment check
9. **Help Guide** - Usage tips and best practices

---

## Project Structure

```
Trade_Advice/
├── dashboard.py              # Main unified dashboard
├── start.sh                  # Quick launch script
├── core/                     # Shared modules
│   ├── api.py               # KuCoin API interactions
│   ├── indicators.py        # All technical indicators
│   └── display.py           # UI utilities
├── scripts/                  # Individual tools
│   ├── opportunity_watcher.py
│   ├── universal_monitor.py
│   ├── institutional_scan.py
│   ├── smart_trailing_stop.py
│   └── trailing_stop.py
├── .env                      # API credentials
└── requirements.txt
```

---

## Installation Flow

### First-Time Setup (New Users)

When you clone from GitHub and run `./start.sh`, here's what happens:

**Step 1: Environment Setup**
```
> Creating virtual environment...
✓ Virtual environment created
> Activating virtual environment...
✓ Virtual environment activated
```

**Step 2: Dependencies**
```
> Checking dependencies...
> Installing required packages...
   (This may take a minute on first run)
✓ All dependencies installed
```

**Step 3: API Credentials (Optional)**
```
═══════════════════════════════════════════════════════════
FIRST TIME SETUP - KUCOIN API CREDENTIALS
═══════════════════════════════════════════════════════════

Set up credentials now? (y/n): [you choose]

If 'n' - Dashboard runs in LIMITED MODE:
  ✓ Help and documentation available
  ✓ Can add credentials later
  ✗ Trading features disabled

If 'y':
Enter your KUCOIN_API_KEY: [you enter here]
Enter your KUCOIN_API_SECRET: [you enter here]
Enter your KUCOIN_API_PASSPHRASE: [you enter here]

✅ .env file created successfully!
> Testing connection to KuCoin...
✅ Connection successful!
```

**Step 4: Dashboard Launch**
```
> Launching dashboard...
===========================================

[INTERACTIVE MENU APPEARS]
```

### Existing User Flow

If you already have `.venv` and `.env`:
```
✓ Virtual environment found
✓ Virtual environment activated  
✓ Dependencies already installed
> Launching dashboard...
```

**No prompts - straight to trading!**

### What Gets Protected (.gitignore)

Your personal setup stays private:
- `.venv/` - Your Python environment
- `.env` - Your API credentials
- `__pycache__/` - Python cache files

These never get uploaded to GitHub!

---

## 🔧 Manual Setup (Optional)

If you prefer manual control:

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API
Create `.env` file:
```env
KUCOIN_API_KEY=your_api_key
KUCOIN_API_SECRET=your_api_secret
KUCOIN_API_PASSPHRASE=your_passphrase
```

### 3. Launch Dashboard
```bash
./start.sh
# OR
python dashboard.py
```

---

## 📖 Tool Guide

### 🔍 Live Opportunity Watcher
**Purpose:** Find new trading opportunities
```bash
python scripts/opportunity_watcher.py
# OR use dashboard option 1
```
- Scans 18+ coins every 60 seconds
- Ranks top 5 by signal score
- Auto-alerts when score ≥70
- Live countdown timer
- Best for: Finding your next trade

### 📊 Institutional Scan
**Purpose:** Full market snapshot
```bash
python scripts/institutional_scan.py
# OR use dashboard option 2
```
- One-time scan of all 20 major coins
- Detailed score breakdown
- See everything at once
- Best for: Market overview right now

### 🔬 Coin Analyzer (Universal Monitor)
**Purpose:** Deep dive on specific symbol
```bash
python scripts/universal_monitor.py TIA
# OR use dashboard option 3
```
- All 8 indicators across 3 timeframes
- Multi-timeframe trend analysis
- Volume and volatility metrics
- Best for: Research before entering

### 📈 Position Monitor
**Purpose:** Track open positions
```bash
python scripts/universal_monitor.py
# OR use dashboard option 4
```
- Auto-detects your open positions
- Live P&L and liquidation distance
- Real-time indicator updates (10s)
- Position-aware scoring (LONG vs SHORT)
- ATR-based stop suggestions
- Best for: Monitoring active trades

### 🛡️ Smart Trailing Stop
**Purpose:** Dynamic profit protection
```bash
python scripts/smart_trailing_stop.py
# OR use dashboard option 6
```
- Adjusts stop based on 8 indicators
- Tightens when reversal signals appear
- Widens when trend is strong
- Auto-closes position when triggered
- Updates every 5 seconds
- Best for: Protecting profits intelligently

### 🔒 Basic Trailing Stop
**Purpose:** Simple fixed trailing
```bash
python scripts/trailing_stop.py
# OR use dashboard option 7
```
- ATR-based or percentage-based
- Fixed distance trailing
- Auto-closes when hit
- Updates every 5 seconds
- Best for: Simple set-and-forget stops

**When to use:** Monitor an active position or do deep analysis on a specific coin

---

## 🎯 Institutional Indicator System

### Weighted Scoring (0-100)
| Component | Max Points | What It Measures |
|-----------|------------|------------------|
| **Trend Alignment** | 30 pts | 4H/1H/15M timeframes aligned |
| **Momentum** | 25 pts | RSI + MACD + Stochastic RSI |
| **Volume** | 20 pts | Volume ratio + OBV direction |
| **Volatility** | 15 pts | ADX strength + Bollinger position |
| **Key Levels** | 10 pts | Price vs VWAP |

**Score ≥70 = TRADEABLE SETUP**

### Multi-Timeframe Hierarchy
- **4H Trend:** Directional bias (where is the market going?)
- **1H Trend:** Confirmation (is the move real?)
- **15M Trend:** Entry timing (when to get in?)

All three must align for highest scores!

### Key Indicators Explained

**ADX (Average Directional Index)**
- <20: Choppy, don't trade ❌
- 20-25: Moderate trend ⚠️
- >25: Strong trend, safe to trade ✅

**MACD Histogram**
- Positive: Bullish momentum [+]
- Negative: Bearish momentum [-]
- Near zero: Momentum shift incoming

**OBV (On-Balance Volume)**
- Rising: Accumulation (smart money buying) [UP]
- Falling: Distribution (smart money selling) [DOWN]
- Divergence from price: Warning sign [!]

**VWAP (Volume Weighted Average Price)**
- Price above: Bullish control [+]
- Price below: Bearish control [-]
- Institutional pivot level

**ATR (Average True Range)**
- Used for dynamic stop losses
- 2x ATR = typical stop distance
- Adapts to volatility automatically

---

## 📖 Common Usage Scenarios

### Scenario 1: "Find me a trade"
```bash
# Option A: Wait for alert (best)
python opportunity_watcher.py
# Leave running, it will alert when score ≥70

# Option B: Quick scan now
python institutional_scan.py
# Shows best opportunities immediately
```

### Scenario 2: "I have an open position"
```bash
python universal_monitor.py
# Select your position from the list
# Get real-time analysis with:
# - Current PNL
# - Liquidation distance
# - Signal score
# - ATR stop suggestions
# - Multi-timeframe trends
```

### Scenario 3: "Analyze a specific coin"
```bash
python universal_monitor.py
# Select 'n' for no position
# Select 'y' for analysis
# Choose your coin from the list
# Get full institutional breakdown
```

---

## 🎨 Understanding the Live Scanner Display

```
═══════════════════════════════════════════════════════════
        LIVE OPPORTUNITY SCANNER - TOP 5 RANKED
═══════════════════════════════════════════════════════════

  ⏳ Waiting for score ≥70...

  #  COIN    L    S   TRENDS  ADX   VOL  
  ─────────────────────────────────────────
  1  DOT     8   65   DDD      33   0.3x
  2  OP     30   67   DUD      29   2.9x
  3  SOL    26   63   DUD      27   1.1x
  4  TIA     8   65   DDD      26   0.5x
  5  XRP    10   47   DUD      16   0.6x
  ─────────────────────────────────────────

  Market: L:23 S:46 | ADX:26✓ | Vol:0.8x✗

  → HOLD - Best: APT(44) OP(67)

  12:37:01 | 18 coins | Next scan in: 58s
```

**Reading the display:**
- **L** = LONG score (green ≥70, yellow ≥50, red <50)
- **S** = SHORT score (same coloring)
- **TRENDS** = 4H/1H/15M (U=Up, D=Down)
- **ADX** = Trend strength (green >25, yellow >20, red <20)
- **VOL** = Volume ratio vs average (green >1.5x)

**When to trade:**
- Score ≥70 + ADX >25 + Volume >1.0x = GO ✅
- Score <70 = WAIT ⏸️
- ADX <20 = TOO CHOPPY, STAY OUT ❌

---

## 🛡️ Risk Management Rules

### Before Every Trade
1. ✅ Check signal score ≥70
2. ✅ Verify ADX >20 (preferably >25)
3. ✅ Confirm all 3 timeframes aligned (UUU or DDD)
4. ✅ Check volume >1.0x average
5. ✅ Set stop loss using ATR (2x ATR from entry)

### Position Sizing
- **Conservative:** 1-3x leverage
- **Moderate:** 5-7x leverage
- **Aggressive:** 10-15x leverage
- **Extreme:** 20x+ (only with tight stops and strong signals)

### Exit Strategy
- **20-50% profit:** Take 25% off
- **50-100% profit:** Take 50% off
- **100%+ profit:** Take 75% off
- **Score drops below 50:** Consider full exit
- **ADX drops below 20:** Tighten stops

---

## 📁 File Structure

```
Trade_Advice/
├── dashboard.py              # Main unified dashboard
├── start.sh                  # Quick launch script
├── core/                     # Shared modules
│   ├── api.py               # KuCoin API interactions
│   ├── indicators.py        # All technical indicators
│   └── display.py           # UI utilities
├── scripts/                  # Individual tools
│   ├── opportunity_watcher.py
│   ├── universal_monitor.py
│   ├── institutional_scan.py
│   ├── smart_trailing_stop.py
│   └── trailing_stop.py
├── requirements.txt          # Dependencies
├── .env                      # API credentials (auto-created)
└── README.md                 # This file
```

---

## 🔧 Troubleshooting

### "No module named 'ccxt'" or similar
```bash
source .venv/bin/activate  # Activate venv first
pip install -r requirements.txt
```

### "Authentication Error"
- Check `.env` file has correct KuCoin credentials
- Ensure API key has futures trading enabled
- Verify API key isn't expired

### "No positions found" (but you have positions)
- Ensure you're using KuCoin Futures (not spot)
- Check API key has futures permissions
- Positions must be on the same account as API key

### Scanner shows all low scores
- This is CORRECT behavior during choppy/low-volume markets
- The system is protecting you from bad trades
- Wait for score ≥70 before trading

### Display looks broken/misaligned
- Use a terminal with at least 80 character width
- Some terminals don't support box-drawing characters
- Try a different terminal (iTerm2, Windows Terminal, etc.)

---

## 🎓 Trading Tips

### What the Pros Do
1. **Wait for confluence:** All indicators agreeing (score ≥70)
2. **Respect ADX:** Never trade when ADX <20 (choppy)
3. **Follow the trend:** Don't fight multi-timeframe alignment
4. **Use ATR stops:** Dynamic stops adapt to volatility
5. **Watch OBV:** Volume divergence warns of reversals

### Common Mistakes to Avoid
1. ❌ Trading during low ADX (choppy markets)
2. ❌ Ignoring volume (low volume = unreliable signals)
3. ❌ Fighting trend alignment (shorting UUU, longing DDD)
4. ❌ Using fixed % stops (use ATR instead)
5. ❌ Over-leveraging low-score setups

---

## ⚠️ Disclaimer

**THIS SOFTWARE IS FOR EDUCATIONAL PURPOSES ONLY**

- Cryptocurrency trading involves substantial risk
- Past performance does not guarantee future results
- The authors are not responsible for any financial losses
- Always do your own research (DYOR)
- Never invest more than you can afford to lose
- Technical indicators are not 100% accurate
- No score guarantees profit

---

## Next Steps

1. **Start the live watcher:**
   ```bash
   python opportunity_watcher.py
   ```

2. **Watch how the market scores change over time**

3. **When you see a score ≥70:**
   - Note the coin and direction (LONG/SHORT)
   - Run `python universal_monitor.py` to analyze in detail
   - Check the full breakdown before entering

4. **Learn the patterns:**
   - What scores lead to good trades?
   - What ADX levels work best?
   - How do volume spikes affect outcomes?

---

**Built with:** Python 3.11, ccxt, pandas, KuCoin API  
**License:** MIT  
**Status:** Production Ready ✅  

**Happy Trading!**
