#!/usr/bin/env python3
"""
Dynamic Trailing Stop Loss
Uses technical indicators to intelligently trail stop loss on open positions
"""
import os
import sys
import time
import ccxt
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime

# Import indicator functions
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.indicators import (
    calculate_atr,
    calculate_bollinger_bands,
    calculate_ema,
    calculate_adx
)

load_dotenv()

# Terminal colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
BOLD = '\033[1m'
RESET = '\033[0m'

class DynamicTrailingStop:
    def __init__(self):
        self.exchange = ccxt.kucoinfutures({
            'apiKey': os.getenv('KUCOIN_API_KEY'),
            'secret': os.getenv('KUCOIN_API_SECRET'),
            'password': os.getenv('KUCOIN_API_PASSPHRASE'),
            'enableRateLimit': True,
        })
        
        self.stop_price = None
        self.highest_profit = 0
        self.trailing_activated = False
        
    def clear_screen(self):
        os.system('clear' if os.name != 'nt' else 'cls')
    
    def get_position(self, symbol=None):
        """Get current position for symbol"""
        positions = self.exchange.fetch_positions()
        active = [p for p in positions if float(p.get('contracts') or 0) != 0]
        
        if symbol:
            for pos in active:
                if pos['symbol'] == symbol:
                    return pos
            return None
        
        return active[0] if active else None
    
    def get_ohlcv(self, symbol, timeframe='15m', limit=100):
        """Fetch OHLCV data"""
        ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        return df
    
    def calculate_dynamic_stop(self, df, position, current_price):
        """Calculate stop loss using multiple indicators"""
        
        side = position['side'].upper()
        entry_price = float(position['entryPrice'])
        
        # Get indicators - pass close prices as Series
        close_prices = df['close']
        
        atr = calculate_atr(df)
        bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(close_prices)
        ema20 = calculate_ema(close_prices, 20)
        adx = calculate_adx(df)
        
        current_atr = atr.iloc[-1]
        current_bb_upper = bb_upper.iloc[-1]
        current_bb_lower = bb_lower.iloc[-1]
        current_bb_middle = bb_middle.iloc[-1]
        current_ema20 = ema20.iloc[-1]
        current_adx = adx.iloc[-1]
        
        # Calculate dynamic multiplier based on volatility and trend strength
        if current_adx > 25:  # Strong trend
            atr_multiplier = 1.5
        elif current_adx > 20:  # Moderate trend
            atr_multiplier = 2.0
        else:  # Weak trend
            atr_multiplier = 2.5
        
        if side == 'SHORT':
            # For shorts, stop goes above current price
            # Use multiple levels and take the closest safe one
            stops = [
                current_price + (current_atr * atr_multiplier),  # ATR-based
                current_bb_upper,  # Bollinger upper band
                current_ema20 + (current_atr * 0.5)  # EMA + buffer
            ]
            suggested_stop = min(stops)
            
            # Ensure stop is above entry for trailing to work
            if suggested_stop <= current_price:
                suggested_stop = current_price + (current_atr * 1.0)
                
        else:  # LONG
            # For longs, stop goes below current price
            stops = [
                current_price - (current_atr * atr_multiplier),  # ATR-based
                current_bb_lower,  # Bollinger lower band
                current_ema20 - (current_atr * 0.5)  # EMA - buffer
            ]
            suggested_stop = max(stops)
            
            # Ensure stop is below entry for trailing to work
            if suggested_stop >= current_price:
                suggested_stop = current_price - (current_atr * 1.0)
        
        return suggested_stop, {
            'atr': current_atr,
            'atr_multiplier': atr_multiplier,
            'bb_upper': current_bb_upper,
            'bb_lower': current_bb_lower,
            'bb_middle': current_bb_middle,
            'ema20': current_ema20,
            'adx': current_adx
        }
    
    def close_position(self, position):
        """Close position at market"""
        symbol = position['symbol']
        contracts = abs(float(position['contracts']))
        side = 'sell' if position['side'].upper() == 'LONG' else 'buy'
        
        try:
            print(f"\n{YELLOW}Executing stop loss - closing position at market...{RESET}")
            
            order = self.exchange.create_order(
                symbol=symbol,
                type='market',
                side=side,
                amount=contracts,
                params={'reduceOnly': True}
            )
            
            print(f"{GREEN}✓ Position closed successfully{RESET}")
            print(f"Order ID: {order['id']}")
            return True
            
        except Exception as e:
            print(f"{RED}✗ Error closing position: {e}{RESET}")
            return False
    
    def run(self, activation_profit_pct=0.5, min_trail_distance_pct=0.3):
        """
        Main loop for trailing stop
        
        Args:
            activation_profit_pct: Activate trailing after this % profit
            min_trail_distance_pct: Minimum distance to trail (% from current price)
        """
        
        print(f"{BOLD}{BLUE}╔══════════════════════════════════════════════════════╗{RESET}")
        print(f"{BOLD}{BLUE}║      DYNAMIC TRAILING STOP - PROFESSIONAL MODE       ║{RESET}")
        print(f"{BOLD}{BLUE}╚══════════════════════════════════════════════════════╝{RESET}\n")
        
        # Get initial position
        position = self.get_position()
        
        if not position:
            print(f"{RED}No open positions found{RESET}")
            return
        
        symbol = position['symbol']
        side = position['side'].upper()
        entry_price = float(position['entryPrice'])
        
        print(f"Monitoring: {BOLD}{symbol}{RESET}")
        print(f"Side: {side}")
        print(f"Entry: ${entry_price:.2f}")
        print(f"Activation: {activation_profit_pct}% profit")
        print(f"Trail Distance: {min_trail_distance_pct}%\n")
        print(f"{CYAN}Press Ctrl+C to stop{RESET}\n")
        print("=" * 60)
        
        try:
            while True:
                # Refresh position
                position = self.get_position(symbol)
                
                if not position:
                    print(f"\n{YELLOW}Position closed externally{RESET}")
                    break
                
                current_price = float(position['markPrice'])
                unrealized_pnl = float(position['unrealizedPnl'] or 0)
                margin = float(position['initialMargin'] or 1)
                
                # Calculate ROE percentage properly
                pnl_pct = (unrealized_pnl / margin) * 100 if margin > 0 else 0
                
                # Get market data
                df = self.get_ohlcv(symbol, '15m', 100)
                
                # Calculate dynamic stop
                suggested_stop, indicators = self.calculate_dynamic_stop(df, position, current_price)
                
                # Check if trailing should be activated
                if not self.trailing_activated and pnl_pct >= activation_profit_pct:
                    self.trailing_activated = True
                    self.stop_price = suggested_stop
                    print(f"\n{GREEN}✓ Trailing activated at {pnl_pct:.2f}% profit{RESET}")
                    print(f"Initial stop: ${self.stop_price:.2f}\n")
                
                # Update stop if in profit and trailing is active
                if self.trailing_activated:
                    if side == 'SHORT':
                        # For shorts, lower the stop as price drops
                        if suggested_stop < self.stop_price:
                            # Only move stop if it's meaningful
                            improvement = ((self.stop_price - suggested_stop) / self.stop_price) * 100
                            if improvement >= min_trail_distance_pct:
                                old_stop = self.stop_price
                                self.stop_price = suggested_stop
                                print(f"{GREEN}↓ Stop lowered: ${old_stop:.2f} → ${self.stop_price:.2f} ({improvement:.2f}%){RESET}")
                        
                        # Check if stop is hit
                        if current_price >= self.stop_price:
                            print(f"\n{RED}✗ STOP LOSS TRIGGERED{RESET}")
                            print(f"Price: ${current_price:.2f} >= Stop: ${self.stop_price:.2f}")
                            if self.close_position(position):
                                break
                    
                    else:  # LONG
                        # For longs, raise the stop as price rises
                        if suggested_stop > self.stop_price:
                            improvement = ((suggested_stop - self.stop_price) / self.stop_price) * 100
                            if improvement >= min_trail_distance_pct:
                                old_stop = self.stop_price
                                self.stop_price = suggested_stop
                                print(f"{GREEN}↑ Stop raised: ${old_stop:.2f} → ${self.stop_price:.2f} ({improvement:.2f}%){RESET}")
                        
                        # Check if stop is hit
                        if current_price <= self.stop_price:
                            print(f"\n{RED}✗ STOP LOSS TRIGGERED{RESET}")
                            print(f"Price: ${current_price:.2f} <= Stop: ${self.stop_price:.2f}")
                            if self.close_position(position):
                                break
                
                # Display status
                self.clear_screen()
                print(f"{BOLD}{BLUE}╔══════════════════════════════════════════════════════╗{RESET}")
                print(f"{BOLD}{BLUE}║      DYNAMIC TRAILING STOP - PROFESSIONAL MODE       ║{RESET}")
                print(f"{BOLD}{BLUE}╚══════════════════════════════════════════════════════╝{RESET}\n")
                
                print(f"{BOLD}Position: {symbol} {side}{RESET}")
                print(f"Entry:        ${entry_price:.2f}")
                print(f"Current:      ${current_price:.2f}")
                
                color = GREEN if unrealized_pnl > 0 else RED
                print(f"{color}PNL:          ${unrealized_pnl:.2f} ({pnl_pct:.2f}%){RESET}")
                
                if self.trailing_activated:
                    print(f"{BOLD}Stop Loss:    ${self.stop_price:.2f}{RESET}")
                    distance = abs(current_price - self.stop_price)
                    distance_pct = (distance / current_price) * 100
                    print(f"Distance:     ${distance:.2f} ({distance_pct:.2f}%)")
                else:
                    print(f"{YELLOW}Waiting for {activation_profit_pct}% profit to activate trailing{RESET}")
                
                print(f"\n{BOLD}Technical Indicators:{RESET}")
                print(f"ATR:          ${indicators['atr']:.2f} (x{indicators['atr_multiplier']})")
                print(f"ADX:          {indicators['adx']:.2f}")
                print(f"EMA20:        ${indicators['ema20']:.2f}")
                print(f"BB Upper:     ${indicators['bb_upper']:.2f}")
                print(f"BB Lower:     ${indicators['bb_lower']:.2f}")
                
                print(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Monitoring...")
                print(f"{CYAN}Press Ctrl+C to stop{RESET}")
                
                time.sleep(5)  # Update every 5 seconds
                
        except KeyboardInterrupt:
            print(f"\n\n{YELLOW}Trailing stop monitor stopped by user{RESET}")
        except Exception as e:
            print(f"\n{RED}Error: {e}{RESET}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Dynamic Trailing Stop Loss')
    parser.add_argument('--activate', type=float, default=0.5, 
                       help='Activate trailing after X%% profit (default: 0.5)')
    parser.add_argument('--trail', type=float, default=0.3,
                       help='Minimum trail distance %% (default: 0.3)')
    
    args = parser.parse_args()
    
    monitor = DynamicTrailingStop()
    monitor.run(activation_profit_pct=args.activate, min_trail_distance_pct=args.trail)
