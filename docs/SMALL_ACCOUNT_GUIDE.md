# Small Account Trading System - $5.85 Test Fund

## 🎯 Mission: Grow $5.85 → $50+ Through Smart Scalping

**Current Balance:** $5.85  
**Risk Per Trade:** 3% ($0.18)  
**Fee Awareness:** 0.12% round trip  
**Target:** Short-term trades (30min - 4 hours)  
**Approach:** One trade at a time, automated helpers, CLI monitoring

---

## 🛠️ New Tools for Small Accounts

### 1. Small Account Manager
**File:** `small_account_manager.py`

Calculates optimal position sizing for $5.85 account:
- Fee-aware position sizing
- Aggressive but controlled 3% risk
- Minimum 2.5R targets to beat fees
- Sweet spot: 10x leverage

**Usage:**
```bash
# Interactive calculator
python small_account_manager.py calc

# Example calculation
python small_account_manager.py
```

**Features:**
- ✅ Accounts for 0.12% fees in profit calculations
- ✅ Shows exact contracts, margin, risk
- ✅ Net profit after fees for each TP
- ✅ Warns about fee drag on small accounts

---

### 2. Automated Trailing Stop
**File:** `auto_trailing_stop.py`

Runs in BACKGROUND - automatically moves stop to lock in profits:
- Activates at 1.5R (break-even + fees)
- Trails 1.0 ATR behind price
- Never moves against you
- Logs all movements
- CLI monitoring

**Usage:**
```bash
# Start trailing stop in background
nohup python auto_trailing_stop.py BTC/USDT:USDT LONG 95000 94500 > trail.log 2>&1 &

# Monitor in real-time
tail -f trail.log

# Custom settings (activate at 2R, trail 1.5 ATR)
python auto_trailing_stop.py BTC/USDT:USDT LONG 95000 94500 2.0 1.5
```

**Why It's Critical:**
- Small accounts MUST lock in wins quickly
- You can't watch charts 24/7
- Automates the hardest part (taking profits)

---

### 3. Quick Scalp Finder
**File:** `quick_scalp_finder.py`

Finds short-term opportunities (5m + 15m focused):
- Quick momentum plays
- 2.5R - 4R targets
- Tight stops (1.2 ATR)
- High-probability setups only

**Usage:**
```bash
# Analyze single symbol
python quick_scalp_finder.py --symbol BTC/USDT:USDT

# Scan top 8 symbols for setups
python quick_scalp_finder.py --scan

# Only show 70+ scores
python quick_scalp_finder.py --scan --min-score 70
```

**Output:**
- Clear LONG/SHORT signal
- Entry, stop, TP1, TP2 prices
- 5m/15m RSI, ADX, volume surge
- Net profit after fees

---

## 📋 Small Account Workflow

### Step 1: Find Opportunity
```bash
cd /home/hektic/hekstradehub

# Scan for best scalp setup
python quick_scalp_finder.py --scan --min-score 65
```

### Step 2: Calculate Position
```bash
# Use interactive calculator
python small_account_manager.py calc

# Enter:
# - Balance: 5.85
# - Symbol: BTC/USDT:USDT
# - Side: LONG or SHORT
# - Entry: [from scalp finder]
# - Stop: [from scalp finder]
# - Leverage: 10
```

**Review:**
- Margin required (should be <$4.50 = 80% of account)
- Fee cost (should be <$0.05)
- Net profit if TPs hit
- Risk/Reward ratio

### Step 3: Enter Trade Manually
```bash
# Check current position
python check_position.py

# Use KuCoin interface to:
# 1. Set leverage (10x)
# 2. Place LIMIT order at entry price
# 3. Set initial stop loss
# 4. Set TP1 and TP2 orders
```

### Step 4: Start Automation
```bash
# In separate terminal - start trailing stop
python auto_trailing_stop.py BTC/USDT:USDT LONG 95000 94500 &

# Start live dashboard
python live_dashboard.py
```

### Step 5: Monitor
```bash
# Watch live dashboard (updates every 5s)
# - Price movement
# - P&L in real-time
# - RSI, EMA, MACD
# - Distance to liquidation
# - Smart alerts

# Let trailing stop run in background
# - Will activate at 1.5R
# - Automatically protects profits
# - You just need to manually adjust stop when it tells you
```

### Step 6: Log Trade
```bash
# After closing position
python trade_journal.py log

# Enter all details
# System calculates stats
```

---

## 💡 Small Account Strategy

### DO ✅
- **Trade liquid pairs** (BTC, ETH, SOL) - tight spreads
- **Use 10x leverage** - efficient capital use, manageable risk
- **Target 2.5R minimum** - must beat 0.12% fees
- **Exit within 4 hours** - don't tie up capital
- **Take partial profits** - 60% at TP1, 40% at TP2
- **Use trailing stops** - automate profit protection
- **Log every trade** - data-driven improvement

### DON'T ❌
- **Don't hold overnight** - small accounts can't afford gaps
- **Don't chase** - wait for 65+ score setups
- **Don't over-leverage** - max 20x, prefer 10x
- **Don't ignore fees** - they're 2% of your account!
- **Don't revenge trade** - one trade at a time
- **Don't skip stops** - one bad trade can wipe you out

---

## 🎯 Growth Targets

### Phase 1: $5.85 → $12 (100% gain)
- **Strategy:** Ultra-selective scalps (70+ score only)
- **Target:** 5 wins at 3R each
- **Timeline:** 2-3 weeks
- **Risk:** Never exceed 3% per trade

### Phase 2: $12 → $25 (100% gain)
- **Strategy:** Increase frequency slightly
- **Target:** Mix of scalps + short swings
- **Risk:** Can stay at 3% or reduce to 2.5%

### Phase 3: $25 → $50 (100% gain)
- **Strategy:** Start testing automation
- **Target:** 1-2 trades per day
- **Risk:** Reduce to 2% per trade

### Phase 4: $50+ (Sustainable)
- **Strategy:** Full automation testing
- **Target:** Build consistency
- **Risk:** Professional 1-2% risk management

---

## 📊 Key Metrics to Track

### Daily
- Trades taken
- Win/loss
- Average R achieved
- Fees paid

### Weekly
- Win rate (target: 60%+)
- Profit factor (target: 2.0+)
- Average hold time
- Best/worst trades

### Monthly
- Account growth %
- Total fees vs profits
- Strategy adjustments needed
- Automation progress

---

## 🚀 Automation Roadmap

### Currently Automated ✅
- RAM protection (prevents crashes)
- Trailing stops (locks in profits)
- Live monitoring (real-time P&L)
- Trade logging (performance tracking)

### Next to Automate
1. **Auto Entry** - Place orders when signal hits
2. **Auto TP Management** - Move TPs based on momentum
3. **Auto Risk Calculator** - Suggest position sizes
4. **Alert System** - Telegram notifications

### Future (Full Automation)
1. Signal detection → Auto entry
2. Position management → Auto trailing
3. Exit execution → Auto TPs
4. Performance analysis → Auto adjustments

---

## 🔧 Quick Reference

### Check Balance
```bash
python check_position.py
```

### Find Trade
```bash
python quick_scalp_finder.py --scan
```

### Calculate Size
```bash
python small_account_manager.py calc
```

### Monitor Position
```bash
python live_dashboard.py
```

### Start Trailing Stop
```bash
python auto_trailing_stop.py SYMBOL SIDE ENTRY STOP &
```

### View Stats
```bash
python trade_journal.py stats 7
```

---

## ⚠️ Risk Warnings

1. **$5.85 is SMALL** - One 3% loss = $0.18, three bad trades = -10%
2. **Fees are HUGE** - 0.12% is 2% of your account per round trip
3. **Must win quickly** - Can't afford long drawdowns
4. **Leverage is risky** - 10x means 10% move = account doubled OR wiped
5. **This is aggressive** - Necessary for small accounts, but risky

**Golden Rule:** If you lose 3 trades in a row, STOP and review strategy.

---

## 📈 Success Metrics

### After 10 Trades
- Win rate: >60%
- Average R: >3.0
- Profit factor: >2.0
- Account: >$7.00 (+20%)

### After 30 Trades
- Win rate: >65%
- Average R: >3.5
- Profit factor: >2.5
- Account: >$10.00 (+70%)

### After 60 Trades
- Win rate: >70%
- Average R: >4.0
- Profit factor: >3.0
- Account: >$15.00 (+150%)

---

**Remember:** Every trade is data. Log it. Learn from it. Improve. 🚀
