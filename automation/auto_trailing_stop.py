#!/usr/bin/env python3
"""
Automated Trailing Stop - Runs in background monitoring position
Automatically adjusts stop loss to lock in profits
"""

import ccxt
from dotenv import load_dotenv
import os
import sys
import time
import json
from datetime import datetime

# RAM Protection
sys.path.insert(0, '/home/hektic/saddynhektic workspace')
try:
    from Tools.resource_manager import check_ram_before_processing
    check_ram_before_processing(min_free_gb=1.5)
except:
    pass

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from core.indicators import calculate_atr

load_dotenv()

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
BOLD = '\033[1m'
RESET = '\033[0m'

class AutoTrailingStop:
    """
    Automated trailing stop that runs in background
    Updates stop loss as price moves in your favor
    """
    
    def __init__(self, symbol, side, entry_price, initial_stop, 
                 trail_activation_r=1.5, trail_distance_atr=1.0):
        """
        Args:
            symbol: Trading pair
            side: 'LONG' or 'SHORT'
            entry_price: Entry price
            initial_stop: Initial stop loss
            trail_activation_r: Start trailing after this R (default 1.5R = break even + fees)
            trail_distance_atr: Trail distance in ATR multiples (default 1.0 ATR)
        """
        self.symbol = symbol
        self.side = side.upper()
        self.entry = entry_price
        self.initial_stop = initial_stop
        self.current_stop = initial_stop
        
        self.trail_activation_r = trail_activation_r
        self.trail_distance_atr = trail_distance_atr
        
        # Calculate initial risk
        if self.side == 'LONG':
            self.risk = entry_price - initial_stop
        else:
            self.risk = initial_stop - entry_price
        
        self.activation_price = self._calculate_activation_price()
        self.trailing_active = False
        self.highest_price = entry_price if side == 'LONG' else entry_price
        self.lowest_price = entry_price if side == 'SHORT' else entry_price
        
        # Initialize exchange
        self.exchange = ccxt.kucoinfutures({
            'apiKey': os.getenv('KUCOIN_API_KEY'),
            'secret': os.getenv('KUCOIN_API_SECRET'),
            'password': os.getenv('KUCOIN_API_PASSPHRASE'),
            'enableRateLimit': True,
        })
        
        # Logging - save to logs directory
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, f'trailing_stop_{symbol.replace("/", "_")}_{int(time.time())}.log')
        self._log(f"Initialized trailing stop for {symbol} {side}")
        self._log(f"Entry: ${entry_price:.4f}, Initial Stop: ${initial_stop:.4f}")
        self._log(f"Will activate at: ${self.activation_price:.4f} ({trail_activation_r}R)")
    
    def _calculate_activation_price(self):
        """Calculate price where trailing begins"""
        if self.side == 'LONG':
            return self.entry + (self.risk * self.trail_activation_r)
        else:
            return self.entry - (self.risk * self.trail_activation_r)
    
    def _log(self, message):
        """Log to file and console"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        
        with open(self.log_file, 'a') as f:
            f.write(log_msg + '\n')
    
    def _get_atr(self):
        """Fetch current ATR for trail distance"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, '15m', limit=100)
            import pandas as pd
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            atr = calculate_atr(df, period=14).iloc[-1]
            return atr
        except Exception as e:
            self._log(f"Error fetching ATR: {e}")
            return None
    
    def update_stop(self, current_price):
        """
        Update trailing stop based on current price
        Returns: (new_stop, stop_moved)
        """
        
        # Update price extremes
        if self.side == 'LONG':
            if current_price > self.highest_price:
                self.highest_price = current_price
        else:
            if current_price < self.lowest_price:
                self.lowest_price = current_price
        
        # Check if trailing should activate
        if not self.trailing_active:
            if self.side == 'LONG' and current_price >= self.activation_price:
                self.trailing_active = True
                self._log(f"{GREEN}✓ TRAILING ACTIVATED at ${current_price:.4f}{RESET}")
            elif self.side == 'SHORT' and current_price <= self.activation_price:
                self.trailing_active = True
                self._log(f"{GREEN}✓ TRAILING ACTIVATED at ${current_price:.4f}{RESET}")
        
        # If not active yet, keep initial stop
        if not self.trailing_active:
            return self.current_stop, False
        
        # Calculate new trailing stop
        atr = self._get_atr()
        if atr is None:
            return self.current_stop, False
        
        trail_distance = atr * self.trail_distance_atr
        
        if self.side == 'LONG':
            # Trail below highest price
            new_stop = self.highest_price - trail_distance
            
            # Only move stop up, never down
            if new_stop > self.current_stop:
                old_stop = self.current_stop
                self.current_stop = new_stop
                self._log(f"{CYAN}↑ Stop moved: ${old_stop:.4f} -> ${new_stop:.4f} (ATR: {atr:.2f}){RESET}")
                return new_stop, True
        
        else:  # SHORT
            # Trail above lowest price
            new_stop = self.lowest_price + trail_distance
            
            # Only move stop down, never up
            if new_stop < self.current_stop:
                old_stop = self.current_stop
                self.current_stop = new_stop
                self._log(f"{CYAN}↓ Stop moved: ${old_stop:.4f} -> ${new_stop:.4f} (ATR: {atr:.2f}){RESET}")
                return new_stop, True
        
        return self.current_stop, False
    
    def check_stop_hit(self, current_price):
        """Check if current stop has been hit"""
        if self.side == 'LONG':
            if current_price <= self.current_stop:
                self._log(f"{RED}✗ STOP HIT! Price: ${current_price:.4f}, Stop: ${self.current_stop:.4f}{RESET}")
                return True
        else:
            if current_price >= self.current_stop:
                self._log(f"{RED}✗ STOP HIT! Price: ${current_price:.4f}, Stop: ${self.current_stop:.4f}{RESET}")
                return True
        return False
    
    def monitor(self, update_interval=10):
        """
        Main monitoring loop - runs until position closes or stop hits
        
        Args:
            update_interval: Seconds between checks (default 10)
        """
        self._log(f"\n{BOLD}Starting automated trailing stop monitor...{RESET}")
        self._log(f"Update interval: {update_interval} seconds\n")
        
        try:
            while True:
                # Fetch current position
                positions = self.exchange.fetch_positions([self.symbol])
                active_pos = [p for p in positions if float(p.get('contracts', 0)) != 0]
                
                if not active_pos:
                    self._log(f"{YELLOW}Position closed - stopping monitor{RESET}")
                    break
                
                pos = active_pos[0]
                current_price = float(pos.get('markPrice', 0))
                
                # Update stop
                new_stop, moved = self.update_stop(current_price)
                
                # Check if hit
                if self.check_stop_hit(current_price):
                    self._log(f"{RED}STOP HIT - Consider manual exit!{RESET}")
                    # Could auto-close here, but keeping manual for safety
                    break
                
                # Status update
                if self.side == 'LONG':
                    profit = ((current_price - self.entry) / self.entry) * 100
                    distance_to_stop = ((current_price - self.current_stop) / current_price) * 100
                else:
                    profit = ((self.entry - current_price) / self.entry) * 100
                    distance_to_stop = ((self.current_stop - current_price) / current_price) * 100
                
                status = f"Price: ${current_price:.4f} | P&L: {profit:+.2f}% | "
                status += f"Stop: ${self.current_stop:.4f} ({distance_to_stop:.2f}% away)"
                
                if not self.trailing_active:
                    status += f" | Waiting for ${self.activation_price:.4f}"
                
                print(f"\r{status}", end='', flush=True)
                
                time.sleep(update_interval)
        
        except KeyboardInterrupt:
            self._log(f"\n{YELLOW}Monitor stopped by user{RESET}")
        except Exception as e:
            self._log(f"{RED}Error: {e}{RESET}")
    
    def get_status(self):
        """Return current trailing stop status"""
        return {
            'symbol': self.symbol,
            'side': self.side,
            'entry': self.entry,
            'initial_stop': self.initial_stop,
            'current_stop': self.current_stop,
            'activation_price': self.activation_price,
            'trailing_active': self.trailing_active,
            'highest_price': self.highest_price if self.side == 'LONG' else None,
            'lowest_price': self.lowest_price if self.side == 'SHORT' else None
        }


def main():
    """CLI interface for trailing stop"""
    
    if len(sys.argv) < 2:
        print(f"\n{BOLD}Automated Trailing Stop Monitor{RESET}")
        print(f"\nUsage:")
        print(f"  python auto_trailing_stop.py <symbol> <side> <entry> <stop> [activation_r] [trail_atr]")
        print(f"\nExample:")
        print(f"  python auto_trailing_stop.py BTC/USDT:USDT LONG 95000 94500")
        print(f"  python auto_trailing_stop.py BTC/USDT:USDT LONG 95000 94500 2.0 1.5")
        print(f"\nDefaults:")
        print(f"  activation_r: 1.5  (start trailing after 1.5R profit)")
        print(f"  trail_atr:    1.0  (trail 1.0 ATR behind price)\n")
        exit(1)
    
    symbol = sys.argv[1]
    side = sys.argv[2].upper()
    entry = float(sys.argv[3])
    stop = float(sys.argv[4])
    activation_r = float(sys.argv[5]) if len(sys.argv) > 5 else 1.5
    trail_atr = float(sys.argv[6]) if len(sys.argv) > 6 else 1.0
    
    # Create and run trailing stop
    trailing = AutoTrailingStop(
        symbol=symbol,
        side=side,
        entry_price=entry,
        initial_stop=stop,
        trail_activation_r=activation_r,
        trail_distance_atr=trail_atr
    )
    
    trailing.monitor(update_interval=10)


if __name__ == '__main__':
    main()
