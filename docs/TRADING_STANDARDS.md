# Trading Standards & Best Practices
**Last Updated**: 2025-12-25 06:05 EST

## Critical Rules - NEVER DEVIATE

### 1. LEVERAGE CONFIGURATION ⚡
**MANDATORY**: Always pass leverage in order parameters

```python
# ✅ CORRECT - Leverage in params
order = exchange.create_market_buy_order(
    symbol=symbol,
    amount=contracts,
    params={'leverage': 10}  # MUST BE HERE
)

# ❌ WRONG - Relying on set_leverage() alone
exchange.set_leverage(10, symbol)  # This fails on isolated margin
order = exchange.create_market_buy_order(symbol, contracts)
```

**Lesson Learned**: 2025-12-25 - ATOM position opened at 1x instead of 10x because leverage wasn't in order params. Cost us 2 position closes/reopens.

---

### 2. CONTRACT SIZE CALCULATION 📐
**CRITICAL**: Must account for contract size when calculating position

```python
# ✅ CORRECT - Account for contract size
market = exchange.market(symbol)
contract_size = market.get('contractSize', 1)  # e.g., 0.1 for ATOM
current_price = ticker['last']

margin = available * 0.95
notional = margin * leverage
contracts = int(notional / (current_price * contract_size))

# Verify actual exposure
actual_notional = contracts * current_price * contract_size
print(f"Notional: ${actual_notional:.2f}")  # Should be ~$60 with $6 capital @ 10x

# ❌ WRONG - Ignoring contract size
contracts = int(notional / current_price)  # This gives 10x fewer contracts!
```

**Why This Matters:**
- **ATOM contract size = 0.1**: Each contract = 0.1 ATOM, not 1 ATOM
- **Without contract size**: 29 contracts calculated → only $5.77 notional (WRONG)
- **With contract size**: 290 contracts calculated → $57.74 notional (CORRECT)
- **Impact**: 10x difference in position size and profit potential!

**Example Calculation:**
```
Capital: $6
Leverage: 10x
Target Notional: $60
ATOM Price: $1.99
Contract Size: 0.1

WRONG way:
contracts = 60 / 1.99 = 30 contracts
actual = 30 × 1.99 × 0.1 = $5.97 ❌ (10x too small!)

CORRECT way:
contracts = 60 / (1.99 × 0.1) = 301 contracts
actual = 301 × 1.99 × 0.1 = $59.90 ✅
```

**Verification After Opening:**
```python
# Always check actual notional vs expected
expected_notional = (available * 0.95) * leverage
actual_notional = contracts * price * contract_size

if abs(expected_notional - actual_notional) > 5:
    print("⚠️ WARNING: Position size mismatch!")
    print(f"Expected: ${expected_notional:.2f}")
    print(f"Actual: ${actual_notional:.2f}")
```

**Lesson Learned**: 2025-12-25 - First ATOM position was 10x too small (29 contracts vs 290) because contract size wasn't factored into calculation. Potential profit was $0.28 instead of $2.89.

---

### 3. TRADING FEES 💰
**MANDATORY**: Set BOTH exchange orders AND auto-trailing

#### A. Exchange Orders (Primary Protection)
```python
# For LONG positions
sl_order = exchange.create_order(
    symbol=symbol,
    type='market',
    side='sell',
    amount=contracts,
    params={
        'stopPrice': str(stop_loss_price),
        'stop': 'down',
        'closeOrder': True,
        'reduceOnly': True
    }
)

tp_order = exchange.create_order(
    symbol=symbol,
    type='limit',
    side='sell',
    amount=contracts,
    price=tp_price,
    params={
        'closeOrder': True,
        'reduceOnly': True
    }
)
```

#### B. Auto-Trailing Manager (Secondary/Enhancement)
```bash
python3 auto_trailing_manager.py SYMBOL SIDE ENTRY TP1 TP2 &
```

**Why Both?**
- Exchange orders work even if script crashes
- Auto-trailing provides dynamic stop movement after TP1
- Belt + Suspenders = Maximum safety

---

### 3. TRADING FEES 💰
**CRITICAL**: Always account for fees in P&L calculations

#### KuCoin Futures Fee Structure
- **Maker Fee**: 0.02% (when you add liquidity - limit orders)
- **Taker Fee**: 0.06% (when you remove liquidity - market orders)
- **Typical Trade**: 2 market orders = 0.12% total fees (entry + exit)

#### Fee Calculation
```python
# For a $57 position with 10x leverage
notional = 57.74
entry_fee = notional * 0.0006  # $0.035
exit_fee = notional * 0.0006   # $0.035
total_fees = 0.07  # Round up for safety

# Example: ADA trade
gross_pnl = 0.31
fees = 0.04  # Estimated
net_pnl = 0.27  # What you actually keep
```

#### Important Notes
- Fees are charged on NOTIONAL value, not margin
- 10x leverage = 10x fees compared to spot
- Multiple entries/exits = multiple fee charges
- Use limit orders when possible to reduce fees (0.02% vs 0.06%)

#### Fee Optimization Strategies
1. **Use limit orders** instead of market when time permits (-66% fees)
2. **Don't over-trade** - each round trip costs 0.12%
3. **Let positions run** - trailing stops are free, closing/reopening costs fees
4. **5% profit target** easily covers 0.12% fees with room for profit

**Example**: 
- Target: +5% profit = +$2.89 on $57 position
- Fees: -0.12% = -$0.07
- Net: +$2.82 (still 4.88% return)

---

### 6. POSITION VERIFICATION ✓
**MANDATORY**: Always verify after opening position

```bash
python3 check_position.py
```

**Check For:**
- ✅ Correct leverage (10x, not 1x)
- ✅ Correct contract amount (verify with contract size calculation)
- ✅ **Correct notional value** (should be ~95% of capital × leverage)
- ✅ Liquidation price is reasonable
- ✅ P&L tracking works

**If ANY issues**: Close and reopen immediately, don't wait.

**Critical Check - Notional Verification:**
```bash
# Expected notional should be close to: (balance × 0.95) × leverage
# Example: $6 × 0.95 × 10 = $57
# If position shows $5.77 notional instead of $57, CONTRACT SIZE ERROR!
```

---

### 7. ORDER VERIFICATION 📋
**MANDATORY**: Verify SL/TP are on exchange

```bash
python3 -c "
import ccxt, os
from dotenv import load_dotenv
load_dotenv()
exchange = ccxt.kucoinfutures({
    'apiKey': os.getenv('KUCOIN_API_KEY'),
    'secret': os.getenv('KUCOIN_API_SECRET'),
    'password': os.getenv('KUCOIN_API_PASSPHRASE'),
    'enableRateLimit': True,
})
orders = exchange.fetch_open_orders('SYMBOL')
print(f'Open orders: {len(orders)}')
for o in orders:
    print(f\"{o['type']} {o['side']} @ {o.get('price') or o.get('stopPrice')}\")
"
```

**Expected Result**: At least 1-2 orders (SL and/or TP)
**If Zero Orders**: Run `python3 set_stop_and_tp.py SYMBOL` immediately

---

## Standard Trading Workflow 📝

### Opening a Position

```bash
# 1. Find opportunity
python3 find_opportunity.py

# 2. Open position (LONG or SHORT)
python3 open_long.py SYMBOL LEVERAGE RISK
# OR
python3 open_short.py SYMBOL LEVERAGE RISK

# 3. IMMEDIATELY verify position
python3 check_position.py

# 4. IMMEDIATELY verify orders
python3 -c "exchange.fetch_open_orders('SYMBOL')"

# 5. If ANYTHING wrong, fix IMMEDIATELY
python3 set_stop_and_tp.py SYMBOL  # If orders missing
python3 fix_leverage.py            # If leverage wrong

# 6. Log the trade
python3 -c "
from datetime import datetime
with open('trade_log.txt', 'a') as f:
    f.write(f'{datetime.now()} - Opened SYMBOL SIDE @ PRICE\\n')
"
```

### Monitoring Position

```bash
# Check position status
python3 check_position.py

# Check auto-trailing log
tail -f auto_trailing_SYMBOL_*.log

# Check open orders
python3 -c "exchange.fetch_open_orders('SYMBOL')"
```

### Closing Position

```bash
# Manual close if needed
python3 -c "
exchange.create_market_sell_order('SYMBOL', contracts)  # For LONG
# OR
exchange.create_market_buy_order('SYMBOL', contracts)   # For SHORT
"

# Verify closed
python3 check_position.py  # Should show "No open positions"

# Check final P&L10x too small (wrong notional)
**Cause**: Contract size not factored into calculation
**Symptoms**: 
- Expected $57 notional, got $5.77
- Expected $2.89 profit potential, got $0.28
- Contracts seem reasonable but actual exposure is tiny
**Fix**:
```python
# Add contract size to calculation
market = exchange.market(symbol)
contract_size = market.get('contractSize', 1)
contracts = int(notional / (price * contract_size))  # NOT just (notional / price)
```
**Prevention**: Always verify actual notional matches expected (capital × 0.95 × leverage)

### Issue: Position 
python3 check_trade_history.py
```

---

## Common Mistakes & Fixes 🔧

### Issue: Position opened at 1x instead of 10x
**Cause**: Leverage not in order params
**Fix**: 
```python
params={'leverage': 10}  # Add this to create_order call
```
**Prevention**: Use standardized `open_long.py` / `open_short.py` scripts

### Issue: No SL/TP orders on exchange
**Cause**: Order placement failed silently
**Fix**: 
```bash
python3 set_stop_and_tp.py SYMBOL
```
**Prevention**: Always verify orders after opening position

### Issue: Auto-trailing not running
**Cause**: Background process crashed or wasn't started
**Fix**:
```bash
ps aux | grep auto_trailing  # Check if running
python3 auto_trailing_manager.py SYMBOL SIDE ENTRY TP1 TP2 &
```
**Prevention**: Check process ID after opening position

### Issue: Lost track of position
**Cause**: No logging
**Fix**: See "Trade Logging" section below
**Prevention**: Log every trade immediately

---

## Trade Logging 📊

### MANDATORY Log Entry Format

Every trade MUST be logged in `trade_journal.json`:

```json
{
  "timestamp": "2025-12-25 06:00:00",
  "symbol": "ATOM/USDT:USDT",
  "side": "LONG",
  "entry_price": 1.991,
  "contracts": 29,
  "leverage": 10,
  "margin": 0.58,
  "notional": 57.74,
  "stop_loss": 1.8915,
  "take_profit_1": 2.0906,
  "take_profit_2": 2.1900,
  "order_id": "393623892582735872",
  "sl_order_id": "393624563465916416",
  "tp_order_id": "393624564422262784",
  "auto_trailing_pid": "check_pid_file",
  "status": "OPEN",
  "notes": "Triple timeframe alignment, ADX 54"
}
```

### Update on Close:

```json
{
  ...previous fields...,
  "exit_timestamp": "2025-12-25 06:30:00",
  "exit_price": 2.05,
  "exit_reason": "TP1 hit, trailing stopped",
  "price_move_percent": 2.97,
  "gross_pnl": 1.71,
  "estimated_fees": 0.07,
  "net_pnl": 1.64,
  "roi_percent": 283.0,
  "status": "CLOSED",
  "fee_notes": "Entry: ~$0.035 (market), Exit: ~$0.035 (market), Total: ~$0.07"
}
```

---

## Pre-Flight Checklist ✈️

Before opening ANY position:

- [ ] Balance confirmed (at least $5 USDT available)
- [ ] Market analysis complete (trends aligned, RSI checked, volume confirmed)
- [ ] Risk calculated (5% SL = acceptable loss amount)
- [ ] Scripts tested and working (`python3 check_position.py` runs)
- [ ] Auto-trailing manager available (`ls auto_trailing_manager.py`)
- [ ] .env file loaded (API keys present)

After opening position (within 60 seconds):

- [ ] Position verified (`check_position.py` shows correct leverage)
- [ ] Orders verified (at least 1 open order for SL or TP)
- [ ] Auto-trailing started (PID saved, log file created)
- [ ] Trade logged (entry in trade_journal.json)
- [ ] Alert set (if desired - Telegram, Discord, etc.)

---

## Script Standards 💻

All trading scripts MUST follow these patterns:

### 1. Error Handling
```python
try:
    # Trading logic
except Exception as e:
    print(f"❌ Error: {e}")
    # Log error
    # Send alert
    # DO NOT exit silently
```

### 2. Confirmation
```python
print(f"\nPosition Details:")
print(f"  Leverage: {leverage}x")
print(f"  Entry: ${price}")
print(f"  SL: ${sl_price}")
print(f"  TP: ${tp_price}")

response = input("Confirm? (yes/no): ")
if response != 'yes':
    return False
```

### 3. Verification
```python
# After any critical operation
result = exchange.fetch_positions()
if not result:
    raise Exception("Position not found - operation may have failed")
```

---

## Quick Reference Commands 🚀

```bash
# Open long with 10x leverage, 5% risk
python3 open_long.py ATOM/USDT:USDT 10 5

# Check position
python3 check_position.py

# Set/fix SL and TP
python3 set_stop_and_tp.py ATOM/USDT:USDT

# Check open orders
python3 -c "import ccxt; from dotenv import load_dotenv; import os; load_dotenv(); e=ccxt.kucoinfutures({'apiKey':os.getenv('KUCOIN_API_KEY'),'secret':os.getenv('KUCOIN_API_SECRET'),'password':os.getenv('KUCOIN_API_PASSPHRASE'),'enableRateLimit':True}); print(e.fetch_open_orders('ATOM/USDT:USDT'))"

# Close position manually
python3 -c "import ccxt; from dotenv import load_dotenv; import os; load_dotenv(); e=ccxt.kucoinfutures({'apiKey':os.getenv('KUCOIN_API_KEY'),'secret':os.getenv('KUCOIN_API_SECRET'),'password':os.getenv('KUCOIN_API_PASSPHRASE'),'enableRateLimit':True}); pos=e.fetch_positions(['ATOM/USDT:USDT'])[0]; e.create_market_sell_order('ATOM/USDT:USDT', abs(float(pos['contracts'])))"

# View trade history
python3 check_trade_history.py

# Monitor auto-trailing
tail -f auto_trailing_*.log
```

---

## Lessons Learned 📚

### 2025-12-25: Leverage Configuration Issue
- **Problem**: ATOM opened at 1x instead of 10x
- **Root Cause**: Leverage not passed in order params
- **Solution**: Always use `params={'leverage': X}` in create_order
- **Prevention**: Updated all scripts, created this SOP

### 2025-12-25: Missing SL/TP Orders
- **Problem**: Orders not on exchange after opening position
- **Root Cause**: Silent API failures in order placement
- **Solution**: Created `set_stop_and_tp.py` to add orders post-facto
- **Prevention**: Always verify orders after opening position

### 2025-12-25: ADA SHORT Success
- **Win**: 0.87% profit in 56 minutes
- **What Worked**: Auto-trailing manager caught the reversal perfectly
- **Takeaway**: Combined exchange orders + auto-trailing = best protection

---

## Emergency Procedures 🚨

### If Script Crashes
1. Check position: `python3 check_position.py`
2. Check orders: `fetch_open_orders()`
3. If no orders: `python3 set_stop_and_tp.py` immediately
4. If no auto-trailing: Restart manually
5. DO NOT leave unprotected position

### If Position Goes Against You
1. Don't panic
2. Check if SL is in place
3. If SL missing: Place immediately
4. Let the stop loss work - don't move it
5. Log the loss and learn

### If You're Unsure
1. Check position
2. Close if uncertain
3. Small loss is better than big loss
4. Can always re-enter with better info

---

##**Win rate** (target: >50%)
- **Average gain on wins** (target: >5% gross, >4.8% net after fees)
- **Average loss on losses** (target: <5.2% including fees)
- **Risk/Reward ratio** (target: ≥1:1 after fees)
- **Execution quality** (all rules followed?)
- **Fee efficiency** (limit orders vs market orders ratio)

### Monthly Performance Tracking
```
Total trades: X
Wins: X (X%)
Losses: X (X%)
Gross P&L: $X
Total fees paid: $X
Net P&L: $X
Average fee per trade: $X
ROI: X%
```

---

**Remember**: 
- Following these standards is MORE IMPORTANT than any single trade
- Consistency and discipline beat occasional big wins
- **Fees compound over time** - 0.12% per round trip × 100 trades = 12% of capital
- A small edge executed consistently beats big wins with poor discipline
---

**Remember**: Following these standards is MORE IMPORTANT than any single trade. Consistency and discipline beat occasional big wins.
