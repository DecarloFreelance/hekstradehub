#!/usr/bin/env python3
"""
Trailing Stop System
Monitors position live and executes stop loss when triggered
Updates every 5 seconds to catch big moves
"""
import os
import time
import ccxt
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
import requests
import hmac
import hashlib
import base64
import sys

load_dotenv()

# Terminal colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
BOLD = '\033[1m'
RESET = '\033[0m'

def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')

def fetch_positions(exchange):
    """Fetch all futures positions from KuCoin"""
    try:
        credentials = {
            'apiKey': os.getenv('KUCOIN_API_KEY'),
            'secret': os.getenv('KUCOIN_API_SECRET'),
            'password': os.getenv('KUCOIN_API_PASSPHRASE')
        }
        
        timestamp = str(int(time.time() * 1000))
        endpoint = '/api/v1/positions'
        str_to_sign = timestamp + 'GET' + endpoint
        
        signature = base64.b64encode(
            hmac.new(
                credentials['secret'].encode('utf-8'),
                str_to_sign.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode()
        
        passphrase = base64.b64encode(
            hmac.new(
                credentials['secret'].encode('utf-8'),
                credentials['password'].encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode()
        
        headers = {
            'KC-API-KEY': credentials['apiKey'],
            'KC-API-SIGN': signature,
            'KC-API-TIMESTAMP': timestamp,
            'KC-API-PASSPHRASE': passphrase,
            'KC-API-KEY-VERSION': '2'
        }
        
        url = 'https://api-futures.kucoin.com' + endpoint
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '200000':
                return data.get('data', [])
        return []
    
    except Exception as e:
        print(f"{RED}Error fetching positions: {e}{RESET}")
        return []

def get_active_position(exchange, symbol=None):
    """Get specific active position or first active position"""
    positions = fetch_positions(exchange)
    
    for pos in positions:
        current_qty = float(pos.get('currentQty', 0))
        if current_qty != 0:
            pos_symbol = pos.get('symbol', '')
            
            # If symbol specified, match it
            if symbol and symbol.upper() != pos_symbol.replace('USDTM', ''):
                continue
            
            return {
                'symbol': pos_symbol,
                'side': 'LONG' if current_qty > 0 else 'SHORT',
                'quantity': abs(current_qty),
                'entry_price': float(pos.get('avgEntryPrice', 0)),
                'mark_price': float(pos.get('markPrice', 0)),
                'leverage': float(pos.get('realLeverage', 1)),
                'unrealized_pnl': float(pos.get('unrealisedPnl', 0)),
                'unrealized_roe': float(pos.get('unrealisedRoePcnt', 0)) * 100,
                'liquidation_price': float(pos.get('liquidationPrice', 0)),
                'margin': float(pos.get('maintMargin', 0))
            }
    
    return None

def close_position(exchange, position):
    """
    Close position by placing market order in opposite direction
    
    Args:
        exchange: ccxt exchange object
        position: position dict with symbol, side, quantity
    
    Returns:
        bool: True if order placed successfully
    """
    try:
        credentials = {
            'apiKey': os.getenv('KUCOIN_API_KEY'),
            'secret': os.getenv('KUCOIN_API_SECRET'),
            'password': os.getenv('KUCOIN_API_PASSPHRASE')
        }
        
        # Prepare order parameters
        symbol = position['symbol']
        quantity = int(position['quantity'])
        
        # Opposite side to close
        close_side = 'sell' if position['side'] == 'LONG' else 'buy'
        
        # Build order payload
        order_data = {
            'clientOid': f"close_{int(time.time() * 1000)}",
            'side': close_side,
            'symbol': symbol,
            'type': 'market',
            'size': quantity,
            'reduceOnly': True  # Important: only close position, don't open opposite
        }
        
        # Create signature
        timestamp = str(int(time.time() * 1000))
        endpoint = '/api/v1/orders'
        body = str(order_data).replace("'", '"').replace(' ', '')
        str_to_sign = timestamp + 'POST' + endpoint + body
        
        signature = base64.b64encode(
            hmac.new(
                credentials['secret'].encode('utf-8'),
                str_to_sign.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode()
        
        passphrase = base64.b64encode(
            hmac.new(
                credentials['secret'].encode('utf-8'),
                credentials['password'].encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode()
        
        headers = {
            'KC-API-KEY': credentials['apiKey'],
            'KC-API-SIGN': signature,
            'KC-API-TIMESTAMP': timestamp,
            'KC-API-PASSPHRASE': passphrase,
            'KC-API-KEY-VERSION': '2',
            'Content-Type': 'application/json'
        }
        
        url = 'https://api-futures.kucoin.com' + endpoint
        response = requests.post(url, json=order_data, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '200000':
                print(f"\n{GREEN}{BOLD}✅ POSITION CLOSED SUCCESSFULLY{RESET}")
                print(f"{GREEN}Order ID: {data.get('data', {}).get('orderId', 'N/A')}{RESET}")
                return True
            else:
                print(f"\n{RED}❌ Order failed: {data.get('msg', 'Unknown error')}{RESET}")
                return False
        else:
            print(f"\n{RED}❌ API Error: {response.status_code}{RESET}")
            return False
    
    except Exception as e:
        print(f"\n{RED}❌ Error closing position: {e}{RESET}")
        return False

def get_current_price(exchange, symbol):
    """Get current mark price for symbol"""
    try:
        # Convert SOLUSDTM to SOL/USDT
        spot_symbol = symbol.replace('USDTM', '').replace('USDT', '')
        spot_symbol = f"{spot_symbol}/USDT"
        
        ticker = exchange.fetch_ticker(spot_symbol)
        return ticker['last']
    except Exception as e:
        print(f"{RED}Error fetching price: {e}{RESET}")
        return None

def calculate_atr(exchange, symbol, period=14):
    """Calculate ATR for stop distance"""
    try:
        spot_symbol = symbol.replace('USDTM', '').replace('USDT', '')
        spot_symbol = f"{spot_symbol}/USDT"
        
        ohlcv = exchange.fetch_ohlcv(spot_symbol, '15m', limit=50)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean().iloc[-1]
        
        return atr
    except:
        return 0.0

def display_trailing_stop_monitor(position, current_price, stop_price, stop_type, highest_profit, atr):
    """Display live trailing stop dashboard"""
    clear_screen()
    
    symbol_name = position['symbol'].replace('USDTM', '/USDT')
    
    print(f"{BOLD}{BLUE}{'='*75}{RESET}")
    print(f"{BOLD}{BLUE}{f'{symbol_name} TRAILING STOP MONITOR':^75}{RESET}")
    print(f"{BOLD}{BLUE}{'='*75}{RESET}\n")
    
    # Position info
    side_color = GREEN if position['side'] == 'LONG' else RED
    print(f"{BOLD}Position:{RESET}")
    print(f"  Symbol:         {position['symbol']}")
    print(f"  Side:           {side_color}{position['side']}{RESET} {position['leverage']:.2f}x")
    print(f"  Quantity:       {position['quantity']} contracts")
    print(f"  Entry Price:    ${position['entry_price']:.4f}")
    
    # Current status
    pnl_color = GREEN if position['unrealized_roe'] >= 0 else RED
    print(f"\n{BOLD}Current Status:{RESET}")
    print(f"  Mark Price:     ${current_price:.4f}")
    print(f"  Unrealized PNL: {pnl_color}${position['unrealized_pnl']:+.2f} ({position['unrealized_roe']:+.2f}%){RESET}")
    print(f"  Peak Profit:    {GREEN}+{highest_profit:.2f}%{RESET}")
    
    # Trailing stop info
    print(f"\n{BOLD}Trailing Stop Configuration:{RESET}")
    print(f"  Type:           {stop_type}")
    print(f"  Stop Price:     {YELLOW}${stop_price:.4f}{RESET}")
    
    # Calculate distance to stop
    if position['side'] == 'LONG':
        distance = ((current_price - stop_price) / current_price) * 100
    else:
        distance = ((stop_price - current_price) / current_price) * 100
    
    distance_color = GREEN if distance > 2 else YELLOW if distance > 1 else RED
    print(f"  Distance:       {distance_color}{distance:.2f}%{RESET}")
    
    # Risk info
    print(f"\n{BOLD}Risk Management:{RESET}")
    if position['side'] == 'LONG':
        potential_loss = ((stop_price - position['entry_price']) / position['entry_price']) * 100
    else:
        potential_loss = ((position['entry_price'] - stop_price) / position['entry_price']) * 100
    
    loss_color = GREEN if potential_loss >= 0 else RED
    print(f"  Stop vs Entry:  {loss_color}{potential_loss:+.2f}%{RESET}")
    print(f"  ATR (15M):      ${atr:.4f}")
    print(f"  Liquidation:    ${position['liquidation_price']:.4f}")
    
    # Status bar
    print(f"\n{BOLD}{CYAN}{'='*75}{RESET}")
    print(f"{CYAN}Status: MONITORING - Updates every 5 seconds{RESET}")
    print(f"{CYAN}Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    print(f"\n{YELLOW}Press Ctrl+C to cancel and exit{RESET}")

def run_trailing_stop(exchange, symbol=None, stop_type='ATR', atr_multiplier=2.0, percent_trail=2.0):
    """
    Main trailing stop loop
    
    Args:
        exchange: ccxt exchange object
        symbol: Symbol to monitor (None = first active position)
        stop_type: 'ATR' or 'PERCENT'
        atr_multiplier: ATR multiplier for stop distance (default 2.0)
        percent_trail: Percentage trail for PERCENT type (default 2.0%)
    """
    print(f"{CYAN}Initializing trailing stop monitor...{RESET}\n")
    
    # Get initial position
    position = get_active_position(exchange, symbol)
    if not position:
        print(f"{RED}No active position found!{RESET}")
        return
    
    print(f"{GREEN}Position found: {position['symbol']} {position['side']}{RESET}")
    print(f"{CYAN}Calculating initial stop level...{RESET}\n")
    
    # Calculate ATR
    atr = calculate_atr(exchange, position['symbol'])
    if atr == 0:
        print(f"{YELLOW}Warning: Could not calculate ATR, using 1% default{RESET}")
        atr = position['entry_price'] * 0.01
    
    # Initialize stop price
    current_price = get_current_price(exchange, position['symbol'])
    if not current_price:
        print(f"{RED}Could not fetch current price!{RESET}")
        return
    
    if stop_type == 'ATR':
        stop_distance = atr * atr_multiplier
    else:
        stop_distance = current_price * (percent_trail / 100)
    
    if position['side'] == 'LONG':
        stop_price = current_price - stop_distance
        highest_price = current_price
    else:
        stop_price = current_price + stop_distance
        lowest_price = current_price
    
    highest_profit = position['unrealized_roe']
    
    print(f"{GREEN}✓ Initial stop set at ${stop_price:.4f}{RESET}")
    print(f"{CYAN}Starting live monitoring...{RESET}\n")
    
    time.sleep(2)
    
    try:
        while True:
            # Refresh position data
            position = get_active_position(exchange, symbol)
            
            # Check if position still exists
            if not position:
                print(f"\n{YELLOW}Position closed or not found. Exiting monitor.{RESET}")
                break
            
            # Get current price
            current_price = get_current_price(exchange, position['symbol'])
            if not current_price:
                print(f"{RED}Error fetching price, retrying...{RESET}")
                time.sleep(5)
                continue
            
            # Update highest/lowest and trailing stop
            if position['side'] == 'LONG':
                if current_price > highest_price:
                    highest_price = current_price
                    
                    # Recalculate stop distance if ATR
                    if stop_type == 'ATR':
                        atr = calculate_atr(exchange, position['symbol'])
                        stop_distance = atr * atr_multiplier
                    
                    # Update trailing stop
                    new_stop = highest_price - stop_distance
                    if new_stop > stop_price:
                        stop_price = new_stop
                
                # Check if stop hit
                if current_price <= stop_price:
                    display_trailing_stop_monitor(position, current_price, stop_price, stop_type, highest_profit, atr)
                    print(f"\n{RED}{BOLD}🚨 TRAILING STOP TRIGGERED! 🚨{RESET}")
                    print(f"{RED}Current price ${current_price:.4f} hit stop ${stop_price:.4f}{RESET}")
                    print(f"\n{YELLOW}Closing position...{RESET}")
                    
                    if close_position(exchange, position):
                        print(f"\n{GREEN}✅ Position closed successfully!{RESET}")
                        print(f"{GREEN}Final PNL: {position['unrealized_roe']:+.2f}%{RESET}")
                    else:
                        print(f"\n{RED}❌ Failed to close position - please close manually!{RESET}")
                    break
            
            else:  # SHORT
                if current_price < lowest_price:
                    lowest_price = current_price
                    
                    # Recalculate stop distance if ATR
                    if stop_type == 'ATR':
                        atr = calculate_atr(exchange, position['symbol'])
                        stop_distance = atr * atr_multiplier
                    
                    # Update trailing stop
                    new_stop = lowest_price + stop_distance
                    if new_stop < stop_price:
                        stop_price = new_stop
                
                # Check if stop hit
                if current_price >= stop_price:
                    display_trailing_stop_monitor(position, current_price, stop_price, stop_type, highest_profit, atr)
                    print(f"\n{RED}{BOLD}🚨 TRAILING STOP TRIGGERED! 🚨{RESET}")
                    print(f"{RED}Current price ${current_price:.4f} hit stop ${stop_price:.4f}{RESET}")
                    print(f"\n{YELLOW}Closing position...{RESET}")
                    
                    if close_position(exchange, position):
                        print(f"\n{GREEN}✅ Position closed successfully!{RESET}")
                        print(f"{GREEN}Final PNL: {position['unrealized_roe']:+.2f}%{RESET}")
                    else:
                        print(f"\n{RED}❌ Failed to close position - please close manually!{RESET}")
                    break
            
            # Track highest profit
            if position['unrealized_roe'] > highest_profit:
                highest_profit = position['unrealized_roe']
            
            # Display dashboard
            display_trailing_stop_monitor(position, current_price, stop_price, stop_type, highest_profit, atr)
            
            # Wait 5 seconds
            time.sleep(5)
    
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Trailing stop cancelled by user{RESET}")
        print(f"{CYAN}Position remains open{RESET}")

def main():
    """Main entry point"""
    print(f"\n{BOLD}{BLUE}{'='*75}{RESET}")
    print(f"{BOLD}{BLUE}{'TRAILING STOP SYSTEM':^75}{RESET}")
    print(f"{BOLD}{BLUE}{'='*75}{RESET}\n")
    
    # Setup exchange
    try:
        exchange = ccxt.kucoin({
            'apiKey': os.getenv('KUCOIN_API_KEY'),
            'secret': os.getenv('KUCOIN_API_SECRET'),
            'password': os.getenv('KUCOIN_API_PASSPHRASE'),
            'enableRateLimit': True,
        })
    except Exception as e:
        print(f"{RED}Error connecting to KuCoin: {e}{RESET}")
        return
    
    # Get user preferences
    print(f"{BOLD}Trailing Stop Configuration:{RESET}\n")
    
    # Symbol selection
    print(f"1. Monitor first active position")
    print(f"2. Specify symbol (e.g., TIA, SOL, XRP)")
    choice = input(f"\nSelect option (1-2): ").strip()
    
    symbol = None
    if choice == '2':
        symbol = input("Enter symbol (e.g., TIA): ").strip().upper()
    
    # Stop type
    print(f"\n{BOLD}Stop Type:{RESET}")
    print(f"1. ATR-based (adapts to volatility)")
    print(f"2. Percentage-based (fixed %)")
    stop_choice = input(f"\nSelect type (1-2): ").strip()
    
    if stop_choice == '1':
        stop_type = 'ATR'
        multiplier = input(f"ATR multiplier (default 2.0): ").strip()
        atr_multiplier = float(multiplier) if multiplier else 2.0
        percent_trail = 0
        
        print(f"\n{GREEN}Using ATR trailing stop with {atr_multiplier}x multiplier{RESET}")
    else:
        stop_type = 'PERCENT'
        percent = input(f"Trail percentage (default 2.0%): ").strip()
        percent_trail = float(percent) if percent else 2.0
        atr_multiplier = 0
        
        print(f"\n{GREEN}Using {percent_trail}% trailing stop{RESET}")
    
    print(f"\n{CYAN}{'='*75}{RESET}")
    input(f"\n{YELLOW}Press Enter to start trailing stop monitor...{RESET}")
    
    # Run trailing stop
    run_trailing_stop(exchange, symbol, stop_type, atr_multiplier, percent_trail)

if __name__ == "__main__":
    main()
