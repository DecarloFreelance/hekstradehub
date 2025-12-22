#!/usr/bin/env python3
"""
Smart Trailing Stop with Institutional Indicators
Uses RSI, MACD, ADX, Stochastic RSI, VWAP, OBV, and BB to dynamically adjust stop
Updates every 5 seconds
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

# ============================================================================
# INDICATOR CALCULATIONS (from universal_monitor.py)
# ============================================================================

def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_ema(data, period):
    return data.ewm(span=period, adjust=False).mean()

def calculate_macd(data):
    ema12 = calculate_ema(data, 12)
    ema26 = calculate_ema(data, 26)
    macd_line = ema12 - ema26
    signal_line = calculate_ema(macd_line, 9)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_stochastic_rsi(data, period=14, smooth_k=3, smooth_d=3):
    rsi = calculate_rsi(data, period)
    stoch_rsi = (rsi - rsi.rolling(window=period).min()) / (rsi.rolling(window=period).max() - rsi.rolling(window=period).min()) * 100
    k = stoch_rsi.rolling(window=smooth_k).mean()
    d = k.rolling(window=smooth_d).mean()
    return k, d

def calculate_adx(df, period=14):
    high = df['high']
    low = df['low']
    close = df['close']
    
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
    
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=period).mean()
    
    return adx, plus_di, minus_di

def calculate_atr(df, period=14):
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr

def calculate_bollinger_bands(data, period=20, std_dev=2):
    sma = data.rolling(window=period).mean()
    std = data.rolling(window=period).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    return upper_band, sma, lower_band

def calculate_obv(df):
    obv = (df['volume'] * (~df['close'].diff().le(0) * 2 - 1)).cumsum()
    return obv

def calculate_vwap(df):
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
    return vwap

# ============================================================================
# POSITION & MARKET DATA FETCHING
# ============================================================================

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

def get_market_indicators(exchange, symbol):
    """Fetch all indicators for smart stop calculation"""
    try:
        spot_symbol = symbol.replace('USDTM', '').replace('USDT', '')
        spot_symbol = f"{spot_symbol}/USDT"
        
        # Fetch OHLCV data
        ohlcv_15m = exchange.fetch_ohlcv(spot_symbol, '15m', limit=100)
        df_15m = pd.DataFrame(ohlcv_15m, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Calculate all indicators
        rsi = calculate_rsi(df_15m['close']).iloc[-1]
        ema20 = calculate_ema(df_15m['close'], 20).iloc[-1]
        ema50 = calculate_ema(df_15m['close'], 50).iloc[-1]
        macd, signal, hist = calculate_macd(df_15m['close'])
        stoch_k, stoch_d = calculate_stochastic_rsi(df_15m['close'])
        adx, plus_di, minus_di = calculate_adx(df_15m)
        atr = calculate_atr(df_15m).iloc[-1]
        bb_upper, bb_mid, bb_lower = calculate_bollinger_bands(df_15m['close'])
        obv = calculate_obv(df_15m)
        vwap = calculate_vwap(df_15m).iloc[-1]
        
        # OBV slope (trend)
        obv_slope = (obv.iloc[-1] - obv.iloc[-10]) / 10
        
        price = df_15m['close'].iloc[-1]
        
        return {
            'price': price,
            'rsi': rsi,
            'ema20': ema20,
            'ema50': ema50,
            'macd_hist': hist.iloc[-1],
            'macd_line': macd.iloc[-1],
            'macd_signal': signal.iloc[-1],
            'stoch_k': stoch_k.iloc[-1],
            'stoch_d': stoch_d.iloc[-1],
            'adx': adx.iloc[-1],
            'plus_di': plus_di.iloc[-1],
            'minus_di': minus_di.iloc[-1],
            'atr': atr,
            'bb_upper': bb_upper.iloc[-1],
            'bb_mid': bb_mid.iloc[-1],
            'bb_lower': bb_lower.iloc[-1],
            'vwap': vwap,
            'obv_slope': obv_slope,
            'trend': 'UP' if ema20 > ema50 else 'DOWN'
        }
    
    except Exception as e:
        print(f"{RED}Error fetching indicators: {e}{RESET}")
        return None

# ============================================================================
# SMART STOP CALCULATION
# ============================================================================

def calculate_smart_stop_distance(indicators, position, base_atr):
    """
    Calculate dynamic stop distance based on institutional indicators
    
    For LONG positions:
    - Tighten when bearish signals appear
    - Widen when trend is strong bullish
    
    For SHORT positions:
    - Tighten when bullish signals appear
    - Widen when trend is strong bearish
    
    Returns: (multiplier, reasons)
    """
    multiplier = 2.0  # Base multiplier
    reasons = []
    
    side = position['side']
    
    # 1. ADX - Trend strength (strong trend = wider stop)
    if indicators['adx'] > 30:
        multiplier += 0.5
        reasons.append(f"✓ ADX {indicators['adx']:.1f} - strong trend (+0.5x)")
    elif indicators['adx'] < 20:
        multiplier -= 0.5
        reasons.append(f"⚠ ADX {indicators['adx']:.1f} - weak trend (-0.5x)")
    
    if side == 'LONG':
        # LONG position - watching for bearish signals to tighten
        
        # 2. RSI warnings
        if indicators['rsi'] > 70:
            multiplier -= 0.5
            reasons.append(f"⚠ RSI overbought {indicators['rsi']:.1f} (-0.5x)")
        elif indicators['rsi'] > 60:
            multiplier -= 0.3
            reasons.append(f"⚠ RSI high {indicators['rsi']:.1f} (-0.3x)")
        
        # 3. MACD bearish crossover warning
        if indicators['macd_hist'] < 0:
            multiplier -= 0.4
            reasons.append(f"⚠ MACD bearish (-0.4x)")
        elif abs(indicators['macd_hist']) < 0.05:
            multiplier -= 0.2
            reasons.append(f"⚠ MACD near crossover (-0.2x)")
        
        # 4. Stochastic RSI overbought
        if indicators['stoch_k'] > 80:
            multiplier -= 0.3
            reasons.append(f"⚠ Stoch RSI overbought (-0.3x)")
        
        # 5. Price vs VWAP (below VWAP = bearish)
        if indicators['price'] < indicators['vwap']:
            multiplier -= 0.4
            reasons.append(f"⚠ Below VWAP (-0.4x)")
        
        # 6. OBV divergence (price up but volume down)
        if indicators['obv_slope'] < 0:
            multiplier -= 0.3
            reasons.append(f"⚠ OBV declining (-0.3x)")
        
        # 7. Trend reversal
        if indicators['trend'] == 'DOWN':
            multiplier -= 0.6
            reasons.append(f"⚠ Trend flipped DOWN (-0.6x)")
    
    else:  # SHORT position - watching for bullish signals to tighten
        
        # 2. RSI warnings
        if indicators['rsi'] < 30:
            multiplier -= 0.5
            reasons.append(f"⚠ RSI oversold {indicators['rsi']:.1f} (-0.5x)")
        elif indicators['rsi'] < 40:
            multiplier -= 0.3
            reasons.append(f"⚠ RSI low {indicators['rsi']:.1f} (-0.3x)")
        
        # 3. MACD bullish crossover warning
        if indicators['macd_hist'] > 0:
            multiplier -= 0.4
            reasons.append(f"⚠ MACD bullish (-0.4x)")
        elif abs(indicators['macd_hist']) < 0.05:
            multiplier -= 0.2
            reasons.append(f"⚠ MACD near crossover (-0.2x)")
        
        # 4. Stochastic RSI oversold (bounce risk)
        if indicators['stoch_k'] < 20:
            multiplier -= 0.3
            reasons.append(f"⚠ Stoch RSI oversold (-0.3x)")
        
        # 5. Price vs VWAP (above VWAP = bullish)
        if indicators['price'] > indicators['vwap']:
            multiplier -= 0.4
            reasons.append(f"⚠ Above VWAP (-0.4x)")
        
        # 6. OBV divergence (price down but volume up)
        if indicators['obv_slope'] > 0:
            multiplier -= 0.3
            reasons.append(f"⚠ OBV rising (-0.3x)")
        
        # 7. Trend reversal
        if indicators['trend'] == 'UP':
            multiplier -= 0.6
            reasons.append(f"⚠ Trend flipped UP (-0.6x)")
    
    # Keep multiplier in safe range
    multiplier = max(0.8, min(3.5, multiplier))
    
    if not reasons:
        reasons.append(f"✓ No warnings - base {multiplier:.1f}x ATR")
    
    return multiplier, reasons

def close_position(exchange, position):
    """Close position via market order"""
    try:
        credentials = {
            'apiKey': os.getenv('KUCOIN_API_KEY'),
            'secret': os.getenv('KUCOIN_API_SECRET'),
            'password': os.getenv('KUCOIN_API_PASSPHRASE')
        }
        
        symbol = position['symbol']
        quantity = int(position['quantity'])
        close_side = 'sell' if position['side'] == 'LONG' else 'buy'
        
        order_data = {
            'clientOid': f"close_{int(time.time() * 1000)}",
            'side': close_side,
            'symbol': symbol,
            'type': 'market',
            'size': quantity,
            'reduceOnly': True
        }
        
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

# ============================================================================
# DISPLAY
# ============================================================================

def display_smart_trailing_stop(position, indicators, stop_price, multiplier, reasons, highest_profit):
    """Display smart trailing stop dashboard"""
    clear_screen()
    
    symbol_name = position['symbol'].replace('USDTM', '/USDT')
    price = indicators['price']
    
    print(f"{BOLD}{BLUE}{'='*75}{RESET}")
    print(f"{BOLD}{BLUE}{f'{symbol_name} SMART TRAILING STOP':^75}{RESET}")
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
    print(f"  Mark Price:     ${price:.4f}")
    print(f"  Unrealized PNL: {pnl_color}${position['unrealized_pnl']:+.2f} ({position['unrealized_roe']:+.2f}%){RESET}")
    print(f"  Peak Profit:    {GREEN}+{highest_profit:.2f}%{RESET}")
    
    # Smart stop info
    print(f"\n{BOLD}Smart Trailing Stop:{RESET}")
    print(f"  Stop Price:     {YELLOW}${stop_price:.4f}{RESET}")
    print(f"  ATR Multiplier: {CYAN}{multiplier:.1f}x{RESET} (dynamic)")
    
    # Distance to stop
    if position['side'] == 'LONG':
        distance = ((price - stop_price) / price) * 100
    else:
        distance = ((stop_price - price) / price) * 100
    
    distance_color = GREEN if distance > 2 else YELLOW if distance > 1 else RED
    print(f"  Distance:       {distance_color}{distance:.2f}%{RESET}")
    
    # Key indicators
    print(f"\n{BOLD}Key Indicators:{RESET}")
    print(f"  RSI (15M):      {indicators['rsi']:.1f}")
    macd_color = GREEN if indicators['macd_hist'] > 0 else RED
    print(f"  MACD Hist:      {macd_color}{indicators['macd_hist']:+.4f}{RESET}")
    print(f"  Stoch RSI:      {indicators['stoch_k']:.1f}")
    print(f"  ADX:            {indicators['adx']:.1f}")
    vwap_rel = "ABOVE" if price > indicators['vwap'] else "BELOW"
    vwap_color = GREEN if (position['side'] == 'LONG' and vwap_rel == 'ABOVE') or (position['side'] == 'SHORT' and vwap_rel == 'BELOW') else RED
    print(f"  VWAP:           {vwap_color}{vwap_rel}{RESET}")
    print(f"  Trend:          {indicators['trend']}")
    
    # Stop adjustment reasons
    print(f"\n{BOLD}Stop Adjustments:{RESET}")
    for reason in reasons[:5]:  # Show top 5 reasons
        print(f"  {reason}")
    
    # Risk info
    print(f"\n{BOLD}Risk Info:{RESET}")
    print(f"  Base ATR:       ${indicators['atr']:.4f}")
    print(f"  Liquidation:    ${position['liquidation_price']:.4f}")
    
    # Status bar
    print(f"\n{BOLD}{CYAN}{'='*75}{RESET}")
    print(f"{CYAN}Status: MONITORING - Updates every 5 seconds{RESET}")
    print(f"{CYAN}Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    print(f"\n{YELLOW}Press Ctrl+C to cancel and exit{RESET}")

# ============================================================================
# MAIN LOOP
# ============================================================================

def run_smart_trailing_stop(exchange, symbol=None):
    """Main smart trailing stop loop"""
    print(f"{CYAN}Initializing smart trailing stop...{RESET}\n")
    
    # Get initial position
    position = get_active_position(exchange, symbol)
    if not position:
        print(f"{RED}No active position found!{RESET}")
        return
    
    print(f"{GREEN}Position found: {position['symbol']} {position['side']}{RESET}")
    print(f"{CYAN}Calculating indicators and initial stop...{RESET}\n")
    
    # Get initial indicators
    indicators = get_market_indicators(exchange, position['symbol'])
    if not indicators:
        print(f"{RED}Could not fetch market indicators!{RESET}")
        return
    
    # Calculate initial smart stop
    multiplier, reasons = calculate_smart_stop_distance(indicators, position, indicators['atr'])
    stop_distance = indicators['atr'] * multiplier
    
    if position['side'] == 'LONG':
        stop_price = indicators['price'] - stop_distance
        highest_price = indicators['price']
    else:
        stop_price = indicators['price'] + stop_distance
        lowest_price = indicators['price']
    
    highest_profit = position['unrealized_roe']
    
    print(f"{GREEN}✓ Smart stop set at ${stop_price:.4f} ({multiplier:.1f}x ATR){RESET}")
    print(f"{CYAN}Starting live monitoring...{RESET}\n")
    
    time.sleep(2)
    
    try:
        while True:
            # Refresh position
            position = get_active_position(exchange, symbol)
            
            if not position:
                print(f"\n{YELLOW}Position closed or not found. Exiting.{RESET}")
                break
            
            # Get fresh indicators
            indicators = get_market_indicators(exchange, position['symbol'])
            if not indicators:
                print(f"{RED}Error fetching indicators, retrying...{RESET}")
                time.sleep(5)
                continue
            
            price = indicators['price']
            
            # Recalculate smart stop multiplier
            multiplier, reasons = calculate_smart_stop_distance(indicators, position, indicators['atr'])
            stop_distance = indicators['atr'] * multiplier
            
            # Update trailing stop
            if position['side'] == 'LONG':
                if price > highest_price:
                    highest_price = price
                    new_stop = highest_price - stop_distance
                    if new_stop > stop_price:
                        stop_price = new_stop
                
                # Check if stop hit
                if price <= stop_price:
                    display_smart_trailing_stop(position, indicators, stop_price, multiplier, reasons, highest_profit)
                    print(f"\n{RED}{BOLD}🚨 SMART STOP TRIGGERED! 🚨{RESET}")
                    print(f"{RED}Price ${price:.4f} hit stop ${stop_price:.4f}{RESET}")
                    print(f"\n{YELLOW}Closing position...{RESET}")
                    
                    if close_position(exchange, position):
                        print(f"\n{GREEN}✅ Position closed! Final PNL: {position['unrealized_roe']:+.2f}%{RESET}")
                    else:
                        print(f"\n{RED}❌ Close failed - please close manually!{RESET}")
                    break
            
            else:  # SHORT
                if price < lowest_price:
                    lowest_price = price
                    new_stop = lowest_price + stop_distance
                    if new_stop < stop_price:
                        stop_price = new_stop
                
                # Check if stop hit
                if price >= stop_price:
                    display_smart_trailing_stop(position, indicators, stop_price, multiplier, reasons, highest_profit)
                    print(f"\n{RED}{BOLD}🚨 SMART STOP TRIGGERED! 🚨{RESET}")
                    print(f"{RED}Price ${price:.4f} hit stop ${stop_price:.4f}{RESET}")
                    print(f"\n{YELLOW}Closing position...{RESET}")
                    
                    if close_position(exchange, position):
                        print(f"\n{GREEN}✅ Position closed! Final PNL: {position['unrealized_roe']:+.2f}%{RESET}")
                    else:
                        print(f"\n{RED}❌ Close failed - please close manually!{RESET}")
                    break
            
            # Track highest profit
            if position['unrealized_roe'] > highest_profit:
                highest_profit = position['unrealized_roe']
            
            # Display dashboard
            display_smart_trailing_stop(position, indicators, stop_price, multiplier, reasons, highest_profit)
            
            # Wait 5 seconds
            time.sleep(5)
    
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Smart trailing stop cancelled{RESET}")
        print(f"{CYAN}Position remains open{RESET}")

def main():
    """Main entry point"""
    print(f"\n{BOLD}{BLUE}{'='*75}{RESET}")
    print(f"{BOLD}{BLUE}{'SMART TRAILING STOP WITH INSTITUTIONAL INDICATORS':^75}{RESET}")
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
    
    print(f"{BOLD}Smart Trailing Stop Features:{RESET}")
    print(f"  • Dynamic stop adjustment based on 8 indicators")
    print(f"  • Tightens when reversal signals appear")
    print(f"  • Widens when strong trend confirmed")
    print(f"  • Updates every 5 seconds\n")
    
    # Symbol selection
    print(f"{BOLD}Monitor:{RESET}")
    print(f"1. First active position")
    print(f"2. Specify symbol (e.g., TIA, SOL, XRP)")
    choice = input(f"\nSelect option (1-2): ").strip()
    
    symbol = None
    if choice == '2':
        symbol = input("Enter symbol (e.g., TIA): ").strip().upper()
    
    print(f"\n{CYAN}{'='*75}{RESET}")
    input(f"\n{YELLOW}Press Enter to start smart trailing stop...{RESET}")
    
    # Run smart trailing stop
    run_smart_trailing_stop(exchange, symbol)

if __name__ == "__main__":
    main()
