#!/usr/bin/env python3
"""
Auto Trailing Stop Manager - Automatically enables trailing after TP1 hits
Set it and forget it - monitors position and activates trailing at the right time
"""

import ccxt
from dotenv import load_dotenv
import os
import sys
import time
import subprocess
from datetime import datetime

# RAM Protection
sys.path.insert(0, '/home/hektic/saddynhektic workspace')
try:
    from Tools.resource_manager import check_ram_before_processing
    check_ram_before_processing(min_free_gb=1.5)
except:
    pass

load_dotenv()

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
BOLD = '\033[1m'
RESET = '\033[0m'

class AutoTrailingManager:
    """Automatically starts trailing stop after TP1 hits"""
    
    def __init__(self, symbol, side, entry, initial_stop, tp1_price, tp2_price, 
                 initial_contracts, trail_activation_r=1.0, trail_distance_atr=1.0):
        self.symbol = symbol
        self.side = side.upper()
        self.entry = entry
        self.initial_stop = initial_stop
        self.tp1_price = tp1_price
        self.tp2_price = tp2_price
        self.initial_contracts = initial_contracts
        self.trail_activation_r = trail_activation_r
        self.trail_distance_atr = trail_distance_atr
        
        self.exchange = ccxt.kucoinfutures({
            'apiKey': os.getenv('KUCOIN_API_KEY'),
            'secret': os.getenv('KUCOIN_API_SECRET'),
            'password': os.getenv('KUCOIN_API_PASSPHRASE'),
            'enableRateLimit': True,
        })
        
        self.tp1_hit = False
        self.trailing_started = False
        self.trailing_process = None
        
        self.log_file = f'auto_trailing_{symbol.replace("/", "_")}_{int(time.time())}.log'
        self._log(f"Auto Trailing Manager initialized for {symbol} {side}")
        self._log(f"Entry: ${entry}, TP1: ${tp1_price}, TP2: ${tp2_price}")
        self._log(f"Will start trailing after TP1 hits")
    
    def _log(self, message):
        """Log to file and console"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        
        with open(self.log_file, 'a') as f:
            f.write(log_msg + '\n')
    
    def get_position(self):
        """Get current position info"""
        try:
            positions = self.exchange.fetch_positions([self.symbol])
            active = [p for p in positions if float(p.get('contracts', 0)) != 0]
            return active[0] if active else None
        except Exception as e:
            self._log(f"Error fetching position: {e}")
            return None
    
    def check_tp1_hit(self):
        """Check if TP1 has been hit by monitoring position size"""
        position = self.get_position()
        
        if not position:
            self._log(f"{YELLOW}Position closed completely{RESET}")
            return True  # Position is gone, TP hit or stopped out
        
        current_contracts = abs(float(position.get('contracts', 0)))
        
        # TP1 is 60% of position
        expected_after_tp1 = self.initial_contracts * 0.4  # 40% remaining
        
        # If contracts reduced to ~40%, TP1 hit
        if current_contracts <= expected_after_tp1 + 1 and current_contracts > 0:
            if not self.tp1_hit:
                self._log(f"{GREEN}✅ TP1 HIT! Position reduced to {current_contracts} contracts{RESET}")
                self.tp1_hit = True
            return True
        
        return False
    
    def start_trailing_stop(self):
        """Launch the trailing stop script in background"""
        if self.trailing_started:
            return
        
        self._log(f"{CYAN}Starting trailing stop for remaining position...{RESET}")
        
        # Build command
        cmd = [
            'python',
            'auto_trailing_stop.py',
            self.symbol,
            self.side,
            str(self.entry),
            str(self.tp1_price),  # New stop is at TP1 level (break-even)
            str(self.trail_activation_r),
            str(self.trail_distance_atr)
        ]
        
        try:
            # Start trailing stop in background
            self.trailing_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            self.trailing_started = True
            self._log(f"{GREEN}✅ Trailing stop started (PID: {self.trailing_process.pid}){RESET}")
            self._log(f"Command: {' '.join(cmd)}")
            self._log(f"Logs: Check trailing_stop_*.log files")
            
        except Exception as e:
            self._log(f"{RED}Failed to start trailing stop: {e}{RESET}")
    
    def monitor(self, check_interval=10):
        """Main monitoring loop"""
        
        self._log(f"\n{BOLD}{'='*70}{RESET}")
        self._log(f"{BOLD}AUTO TRAILING MONITOR ACTIVE{RESET}")
        self._log(f"{BOLD}{'='*70}{RESET}\n")
        
        self._log(f"Monitoring {self.symbol} {self.side} position")
        self._log(f"Check interval: {check_interval} seconds")
        self._log(f"Waiting for TP1 to hit at ${self.tp1_price}...\n")
        
        try:
            while True:
                position = self.get_position()
                
                if not position:
                    self._log(f"{YELLOW}No position found - trade closed{RESET}")
                    break
                
                current_price = float(position.get('markPrice', 0))
                contracts = abs(float(position.get('contracts', 0)))
                pnl = float(position.get('unrealizedPnl', 0))
                
                # Check if TP1 hit
                if self.check_tp1_hit() and not self.trailing_started:
                    self.start_trailing_stop()
                
                # Status update
                if not self.tp1_hit:
                    status = f"⏳ Waiting for TP1 | Price: ${current_price:.4f} | "
                    status += f"Contracts: {contracts} | P&L: ${pnl:+.2f}"
                    
                    # Show distance to TP1
                    if self.side == 'LONG':
                        distance_pct = ((self.tp1_price - current_price) / current_price) * 100
                        status += f" | TP1 in {distance_pct:+.2f}%"
                    else:
                        distance_pct = ((current_price - self.tp1_price) / current_price) * 100
                        status += f" | TP1 in {distance_pct:+.2f}%"
                else:
                    status = f"✅ TP1 Hit! Trailing active | Price: ${current_price:.4f} | "
                    status += f"Remaining: {contracts} contracts | P&L: ${pnl:+.2f}"
                
                print(f"\r{status}", end='', flush=True)
                
                time.sleep(check_interval)
        
        except KeyboardInterrupt:
            self._log(f"\n\n{YELLOW}Monitor stopped by user{RESET}")
            if self.trailing_process:
                self._log(f"Trailing stop still running (PID: {self.trailing_process.pid})")
                self._log(f"To stop it: kill {self.trailing_process.pid}")
        
        except Exception as e:
            self._log(f"\n{RED}Error: {e}{RESET}")


def main():
    """CLI interface"""
    
    if len(sys.argv) < 8:
        print(f"""
{BOLD}Auto Trailing Stop Manager{RESET}

Automatically starts trailing stop after TP1 hits.

Usage:
  python auto_trailing_manager.py SYMBOL SIDE ENTRY STOP TP1 TP2 CONTRACTS [TRAIL_R] [TRAIL_ATR]

Arguments:
  SYMBOL       Trading pair (e.g., ADA/USDT:USDT)
  SIDE         LONG or SHORT
  ENTRY        Entry price
  STOP         Initial stop loss
  TP1          First take profit (60% exits here)
  TP2          Second take profit (40% target)
  CONTRACTS    Initial position size
  TRAIL_R      Trail activation in R (default: 1.0 = immediate after TP1)
  TRAIL_ATR    Trail distance in ATR (default: 1.0)

Example (for current ADA SHORT):
  python auto_trailing_manager.py ADA/USDT:USDT SHORT 0.3568 0.3580 0.3540 0.3524 10

What it does:
  1. Monitors your position
  2. Waits for TP1 to hit (position reduces to 40%)
  3. Automatically starts trailing stop for remaining 40%
  4. Runs in background - you can close terminal
  5. Logs everything to file

To run in background:
  nohup python auto_trailing_manager.py ADA/USDT:USDT SHORT 0.3568 0.3580 0.3540 0.3524 10 > auto_trail.log 2>&1 &
        """)
        return
    
    symbol = sys.argv[1]
    side = sys.argv[2].upper()
    entry = float(sys.argv[3])
    stop = float(sys.argv[4])
    tp1 = float(sys.argv[5])
    tp2 = float(sys.argv[6])
    contracts = int(sys.argv[7])
    trail_r = float(sys.argv[8]) if len(sys.argv) > 8 else 1.0
    trail_atr = float(sys.argv[9]) if len(sys.argv) > 9 else 1.0
    
    manager = AutoTrailingManager(
        symbol=symbol,
        side=side,
        entry=entry,
        initial_stop=stop,
        tp1_price=tp1,
        tp2_price=tp2,
        initial_contracts=contracts,
        trail_activation_r=trail_r,
        trail_distance_atr=trail_atr
    )
    
    manager.monitor(check_interval=10)


if __name__ == '__main__':
    main()
