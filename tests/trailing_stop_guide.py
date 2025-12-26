#!/usr/bin/env python3
"""
Smart Trailing Stop Strategy Guide for Small Accounts
Shows when and how to use trailing stops effectively
"""

print("""
╔════════════════════════════════════════════════════════════════════════╗
║           TRAILING STOP STRATEGY - SMALL ACCOUNT GUIDE                 ║
╔════════════════════════════════════════════════════════════════════════╗

## 🎯 WHEN TO USE TRAILING STOPS

### ✅ BEST TIME: After TP1 Hits (RECOMMENDED)

WHY: You've already locked in 60% of position at profit. Now protect the 
     remaining 40% while giving it room to run.

STRATEGY:
  1. Wait for TP1 to hit ($0.3540 for current ADA SHORT)
  2. Start trailing stop for remaining 4 contracts
  3. Trail distance: 1.0 ATR (~$0.0025 for ADA)
  4. Let it run to TP2 or trail out

COMMAND (after TP1 hits):
  python auto_trailing_stop.py ADA/USDT:USDT SHORT 0.3568 0.3540 1.0 1.0 &
  
  Explanation:
    - Entry was 0.3568
    - New stop at 0.3540 (TP1 price = break-even on remaining position)
    - Activate immediately (1.0R since we're already in profit)
    - Trail 1.0 ATR behind


### ⚡ AGGRESSIVE: Immediate Trailing (Higher Risk)

WHY: Maximize profit on full position, but might get stopped early.

STRATEGY:
  1. Start trailing immediately after entry
  2. Activate at 1.5R profit (covers fees + small win)
  3. Trail 1.5 ATR to avoid noise

COMMAND (start now):
  python auto_trailing_stop.py ADA/USDT:USDT SHORT 0.3568 0.3580 1.5 1.5 &
  
  Explanation:
    - Entry: 0.3568, Initial stop: 0.3580
    - Activates after 1.5R profit (~$0.3550 price)
    - Trails 1.5 ATR to avoid premature stops


### 🛡️ CONSERVATIVE: Manual Until TP2 (Safest)

WHY: Fixed TPs ensure you take profits at targets. Use trailing only for 
     bonus runners.

STRATEGY:
  1. Let TP1 and TP2 hit as planned
  2. If price keeps moving, manually trail remaining position
  3. Or just close at TP2 (nothing wrong with taking profit!)

NO COMMAND NEEDED - Just monitor and close manually


## 📊 CURRENT ADA SHORT RECOMMENDATION

Position: SHORT 10 ADA @ $0.3568
Stop: $0.3580
TP1: $0.3540 (6 contracts)
TP2: $0.3524 (4 contracts)

### RECOMMENDED APPROACH: Hybrid Strategy

PHASE 1 - NOW → TP1 hits:
  ✓ No trailing yet
  ✓ Let fixed stops work
  ✓ Monitor price action
  ✓ If TP1 hits, move to Phase 2

PHASE 2 - AFTER TP1 hits:
  ✓ 60% already banked (6 contracts @ $0.3540)
  ✓ Start trailing stop for remaining 4 contracts:
  
  python auto_trailing_stop.py ADA/USDT:USDT SHORT 0.3568 0.3540 1.0 1.0 &
  
  ✓ This protects profits while giving room for TP2
  ✓ If TP2 hits, great! If trailed out, still profitable

PHASE 3 - IF going beyond TP2:
  ✓ Trail continues automatically
  ✓ Locks in more profit as price drops
  ✓ Will exit when momentum shifts


## 🔧 TRAILING STOP PARAMETERS EXPLAINED

python auto_trailing_stop.py SYMBOL SIDE ENTRY STOP [ACTIVATION_R] [TRAIL_ATR]

SYMBOL: Trading pair (e.g., ADA/USDT:USDT)
SIDE: LONG or SHORT
ENTRY: Your entry price
STOP: Initial/current stop price
ACTIVATION_R: Start trailing after this R profit (default: 1.5)
TRAIL_ATR: Distance to trail in ATR multiples (default: 1.0)


## 💡 SMALL ACCOUNT TIPS

1. DON'T trail immediately on first trade
   → You're learning the system, stick to fixed TPs

2. START trailing after TP1 hits
   → Risk is off the table, now optimize

3. USE wider trails (1.5 ATR) for volatile coins
   → Prevents getting shaken out by noise

4. TIGHTER trails (1.0 ATR) for strong trends
   → Locks in profits faster

5. MONITOR the trailing stop logs
   → Watch how it moves, learn the behavior


## 📈 EXAMPLE SCENARIOS

### Scenario 1: TP1 Hits, Start Trailing
Price drops to $0.3540 → TP1 hits, 6 contracts close (+$0.17)

Start trailing:
  python auto_trailing_stop.py ADA/USDT:USDT SHORT 0.3568 0.3540 1.0 1.0 &

Price continues to $0.3524 → TP2 hits, 4 contracts close (+$0.11)
Total profit: $0.28 ✅


### Scenario 2: Strong Move, Trail Beyond TP2
Price drops to $0.3540 → TP1 hits (+$0.17)
Start trailing...
Price drops to $0.3524 → TP2 hits (+$0.11)
Trail continues...
Price drops to $0.3500 → Lowest point
Trail is now at $0.3525 (1.0 ATR = ~$0.0025 above)
Price bounces to $0.3526 → Trailing stop triggers
Final 4 contracts close at ~$0.3526 (+$0.17 instead of +$0.11!)
Total profit: $0.34 instead of $0.28 ✅✅


### Scenario 3: Gets Stopped Early (Learning Experience)
Price drops to $0.3545
Start trailing too early at 1.0 ATR...
Small bounce to $0.3548 → Stopped out
You made less than planned, but learned:
  → Wait for TP1 next time
  → Use wider trail (1.5 ATR) for ADA's volatility


## ⚠️ IMPORTANT WARNINGS

1. Trailing stop runs in BACKGROUND
   → Check it's running: ps aux | grep trailing

2. Logs everything to a file
   → Check logs: tail -f trailing_stop_*.log

3. DOES NOT auto-execute on exchange
   → It monitors and TELLS you when to move stop
   → You still manually adjust the stop loss order
   → (Future version will auto-execute)

4. If system crashes/restarts
   → Trailing stop process stops
   → Your position is NOT protected!
   → Always have exchange-side stops as backup


## 🚀 QUICK START FOR CURRENT TRADE

OPTION A - Conservative (Recommended for first trade):
  → Do nothing now
  → Let TP1 and TP2 hit naturally
  → Learn how the system works
  → Use trailing on 2nd or 3rd trade

OPTION B - Semi-Aggressive (Good learning):
  → Wait for TP1 to hit
  → Then run: python auto_trailing_stop.py ADA/USDT:USDT SHORT 0.3568 0.3540 1.0 1.0 &
  → Monitor how it behaves

OPTION C - Full Automation (Advanced):
  → Run now: python auto_trailing_stop.py ADA/USDT:USDT SHORT 0.3568 0.3580 1.5 1.5 &
  → Might get stopped before TP1
  → But you'll learn fast!


## 📝 MY RECOMMENDATION FOR YOU

Since this is your FIRST trade with $5.83:

1. DON'T use trailing yet
2. Let the fixed TPs work (TP1: $0.3540, TP2: $0.3524)
3. WATCH the price action
4. LEARN how ADA moves
5. AFTER this trade closes, review the chart
6. DECIDE: "Would trailing have helped or hurt?"

For SECOND trade:
- Try trailing after TP1 hits
- Compare results to fixed TPs
- Build confidence in the system

═══════════════════════════════════════════════════════════════════════

Bottom line: WAIT for TP1, THEN trail. Don't over-optimize your first trade!

═══════════════════════════════════════════════════════════════════════
""")
