# KuCoin Stop Loss Solution - WORKING ✅

## The Problem
KuCoin Futures API has specific requirements for stop loss orders that aren't obvious. Standard approaches fail.

## The Solution
Created **order_manager.py** - handles all KuCoin order quirks correctly.

---

## ✅ Working Method

### Current Balance: $5.83 USDT

### Option 1: Manual Entry (Recommended for first trade)
```bash
# 1. Find opportunity
python quick_scalp_finder.py --symbol DOGE/USDT:USDT

# 2. Calculate position
python small_account_manager.py calc
# Enter: 5.83, DOGE/USDT:USDT, LONG, 0.127, 0.125, 10

# 3. Place entry on KuCoin web interface
# - Set leverage to 10x
# - Buy DOGE/USDT perpetual
# - Wait for fill

# 4. After filled, set stops via CLI:
python order_manager.py set-stops DOGE/USDT:USDT 0.125 0.130 0.133

# Output: Places stop loss at 0.125, TP1 at 0.130 (50%), TP2 at 0.133 (50%)
```

### Option 2: Semi-Automated
```bash
# Places entry order + shows command for stops
python order_manager.py full-trade DOGE/USDT:USDT LONG 0.127 0.125 0.130 0.133 35 10

# After entry fills, run the command it shows you
```

### Option 3: Just Stop Loss (if you already have position)
```bash
python order_manager.py set-stop DOGE/USDT:USDT 0.125
```

---

## 🔧 Order Manager Commands

### Test Connection
```bash
python order_manager.py test
```

### Place Stop Loss Only
```bash
python order_manager.py set-stop SYMBOL STOP_PRICE

# Example:
python order_manager.py set-stop DOGE/USDT:USDT 0.125
```

### Place Stop + Multiple TPs
```bash
python order_manager.py set-stops SYMBOL STOP TP1 [TP2] [TP3]

# Example: Stop at 0.125, TPs at 0.130 and 0.133
python order_manager.py set-stops DOGE/USDT:USDT 0.125 0.130 0.133

# Auto-splits: 60% at TP1, 40% at TP2
```

### Full Trade (Entry + Stops)
```bash
python order_manager.py full-trade SYMBOL SIDE ENTRY STOP TP1 TP2 CONTRACTS LEVERAGE

# Example:
python order_manager.py full-trade DOGE/USDT:USDT LONG 0.127 0.125 0.130 0.133 35 10
```

---

## 📋 Complete Workflow for First Trade

### Step 1: Scan for opportunity
```bash
cd /home/hektic/hekstradehub
source .venv/bin/activate

python quick_scalp_finder.py --scan --min-score 65
```

**Look for:**
- Score ≥65
- Clear signal (LONG or SHORT)
- Good risk/reward

### Step 2: Calculate position
```bash
python small_account_manager.py calc
```

**Enter:**
- Balance: 5.83
- Symbol: DOGE/USDT:USDT (or whatever scored highest)
- Side: LONG or SHORT
- Entry: [from scanner]
- Stop: [from scanner]
- Leverage: 10

**Review output:**
- Contracts to trade
- Margin required (should be <$4.50)
- Risk amount (~$0.17 at 3%)
- Potential profit at each TP

### Step 3: Enter manually on KuCoin
**Why manual entry?** Most reliable for first trade. Automation later.

1. Go to KuCoin Futures
2. Select DOGE/USDT perpetual
3. Set leverage to 10x
4. Place LIMIT BUY order at entry price
5. Amount: [contracts from calculator]
6. **Wait for fill** ⏳

### Step 4: Set stops immediately
```bash
# Example: Stop at 0.125, TP1 at 0.130, TP2 at 0.133
python order_manager.py set-stops DOGE/USDT:USDT 0.125 0.130 0.133
```

**This sets:**
- ✅ Stop loss for full position at 0.125
- ✅ TP1 for 50% at 0.130
- ✅ TP2 for 50% at 0.133

### Step 5: Monitor
```bash
# In one terminal - live dashboard
python live_dashboard.py

# In another terminal - trailing stop
python auto_trailing_stop.py DOGE/USDT:USDT LONG 0.127 0.125 &
```

**Dashboard shows:**
- Real-time P&L
- RSI, EMA, MACD
- Liquidation warnings
- Exit suggestions

**Trailing stop:**
- Activates at 1.5R (break-even + fees)
- Automatically protects profits
- You manually adjust stop when it alerts

### Step 6: After close
```bash
python trade_journal.py log
```

Enter trade details → builds performance history

---

## 🎯 Realistic First Trade Example

**DOGE/USDT at $0.127**

### Scanner says:
- Signal: LONG
- Score: 72/100
- Entry: $0.1270
- Stop: $0.1250 (1.57% risk)
- TP1: $0.1302 (2.5R)
- TP2: $0.1334 (4.0R)

### Calculator shows:
- Contracts: 36
- Margin: $4.57 (78% of account)
- Risk: $0.17 (3%)
- Potential: +$0.58 if both TPs hit (+10%)

### Execute:
```bash
# 1. Enter on KuCoin web: Buy 36 DOGE @ $0.1270
# 2. After fill:
python order_manager.py set-stops DOGE/USDT:USDT 0.1250 0.1302 0.1334

# 3. Monitor:
python live_dashboard.py
```

### Expected outcome:
- If TP1 hits: Close 18 contracts (~$0.29 profit)
- If TP2 hits: Close remaining 18 (~$0.29 profit)
- Total: ~$0.58 profit (+10% account growth)
- **New balance: $6.41**

---

## ⚠️ Important Notes

### KuCoin Quirks:
1. **Must have position** before placing stop orders
2. **reduceOnly=True** is CRITICAL (prevents opening new positions)
3. **Use 'TP' price type** (last price, more reliable than mark price)
4. **Separate orders** for entry and stops (can't do both at once)

### Risk Management:
- Maximum 3% risk per trade ($0.17 on $5.83)
- Keep margin under 80% of account
- One trade at a time
- Always set stops IMMEDIATELY after entry

### Fees:
- 0.06% taker fee per side
- 0.12% total round trip
- On $5.83 account, that's ~$0.007 per trade
- Need 2.5R+ targets to overcome fee drag

---

## 🚀 Ready to Trade

**Test the connection:**
```bash
python order_manager.py test
```

**Should show:**
- ✅ Account accessible
- 💰 Available balance: $5.83 USDT
- ✅ No open positions

**Then find your first trade:**
```bash
python quick_scalp_finder.py --scan
```

Good luck! 📈
