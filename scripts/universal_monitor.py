#!/usr/bin/env python3
"""
Universal Crypto Futures Monitor
Monitors any open position or analyzes any coin
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

def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_ema(data, period):
    """Calculate Exponential Moving Average"""
    return data.ewm(span=period, adjust=False).mean()

def calculate_macd(data):
    """Calculate MACD (12, 26, 9)"""
    ema12 = calculate_ema(data, 12)
    ema26 = calculate_ema(data, 26)
    macd_line = ema12 - ema26
    signal_line = calculate_ema(macd_line, 9)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_stochastic_rsi(data, period=14, smooth_k=3, smooth_d=3):
    """Calculate Stochastic RSI"""
    rsi = calculate_rsi(data, period)
    stoch_rsi = (rsi - rsi.rolling(window=period).min()) / (rsi.rolling(window=period).max() - rsi.rolling(window=period).min()) * 100
    k = stoch_rsi.rolling(window=smooth_k).mean()
    d = k.rolling(window=smooth_d).mean()
    return k, d

def calculate_adx(df, period=14):
    """Calculate ADX (Average Directional Index)"""
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
    """Calculate ATR (Average True Range)"""
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
    """Calculate Bollinger Bands"""
    sma = data.rolling(window=period).mean()
    std = data.rolling(window=period).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    return upper_band, sma, lower_band

def calculate_obv(df):
    """Calculate On-Balance Volume"""
    obv = (df['volume'] * (~df['close'].diff().le(0) * 2 - 1)).cumsum()
    return obv

def calculate_vwap(df):
    """Calculate VWAP (Volume Weighted Average Price)"""
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
    return vwap

def fetch_positions(exchange):
    """Fetch open futures positions using KuCoin Futures API"""
    try:
        api_key = exchange.apiKey
        api_secret = exchange.secret
        api_passphrase = exchange.password
        
        endpoint = '/api/v1/positions'
        url = f'https://api-futures.kucoin.com{endpoint}'
        
        now = int(time.time() * 1000)
        str_to_sign = str(now) + 'GET' + endpoint
        signature = base64.b64encode(
            hmac.new(api_secret.encode('utf-8'), 
                    str_to_sign.encode('utf-8'), 
                    hashlib.sha256).digest()
        )
        passphrase = base64.b64encode(
            hmac.new(api_secret.encode('utf-8'), 
                    api_passphrase.encode('utf-8'), 
                    hashlib.sha256).digest()
        )
        
        headers = {
            'KC-API-KEY': api_key,
            'KC-API-SIGN': signature.decode('utf-8'),
            'KC-API-TIMESTAMP': str(now),
            'KC-API-PASSPHRASE': passphrase.decode('utf-8'),
            'KC-API-KEY-VERSION': '2'
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '200000':
                return data.get('data', [])
        return []
    
    except Exception as e:
        print(f"{RED}Error fetching positions: {e}{RESET}")
        return []

def get_active_positions(exchange):
    """Get all active positions"""
    positions = fetch_positions(exchange)
    active = []
    
    for pos in positions:
        current_qty = float(pos.get('currentQty', 0))
        if current_qty != 0:
            active.append({
                'symbol': pos.get('symbol', ''),
                'side': 'LONG' if current_qty > 0 else 'SHORT',
                'quantity': abs(current_qty),
                'entry_price': float(pos.get('avgEntryPrice', 0)),
                'mark_price': float(pos.get('markPrice', 0)),
                'leverage': float(pos.get('realLeverage', 1)),
                'unrealized_pnl': float(pos.get('unrealisedPnl', 0)),
                'unrealized_roe': float(pos.get('unrealisedRoePcnt', 0)) * 100,
                'liquidation_price': float(pos.get('liquidationPrice', 0)),
                'margin': float(pos.get('maintMargin', 0))
            })
    
    return active

def convert_to_spot_symbol(futures_symbol):
    """Convert futures symbol to spot symbol (e.g., SOLUSDTM -> SOL/USDT)"""
    # Remove M suffix and add slash
    base = futures_symbol.replace('USDTM', '').replace('USDT', '')
    return f"{base}/USDT"

def get_market_data(exchange, symbol):
    """Fetch comprehensive market data with all indicators"""
    try:
        ticker = exchange.fetch_ticker(symbol)
        ohlcv_15m = exchange.fetch_ohlcv(symbol, '15m', limit=100)
        ohlcv_1h = exchange.fetch_ohlcv(symbol, '1h', limit=100)
        ohlcv_4h = exchange.fetch_ohlcv(symbol, '4h', limit=50)
        
        df_15m = pd.DataFrame(ohlcv_15m, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df_1h = pd.DataFrame(ohlcv_1h, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df_4h = pd.DataFrame(ohlcv_4h, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # 15M indicators
        rsi_15m = calculate_rsi(df_15m['close']).iloc[-1]
        ema20_15m = calculate_ema(df_15m['close'], 20).iloc[-1]
        ema50_15m = calculate_ema(df_15m['close'], 50).iloc[-1]
        macd_15m, signal_15m, hist_15m = calculate_macd(df_15m['close'])
        stoch_k_15m, stoch_d_15m = calculate_stochastic_rsi(df_15m['close'])
        adx_15m, plus_di_15m, minus_di_15m = calculate_adx(df_15m)
        atr_15m = calculate_atr(df_15m).iloc[-1]
        bb_upper_15m, bb_mid_15m, bb_lower_15m = calculate_bollinger_bands(df_15m['close'])
        obv_15m = calculate_obv(df_15m)
        vwap_15m = calculate_vwap(df_15m).iloc[-1]
        
        # 1H indicators
        rsi_1h = calculate_rsi(df_1h['close']).iloc[-1]
        ema20_1h = calculate_ema(df_1h['close'], 20).iloc[-1]
        ema50_1h = calculate_ema(df_1h['close'], 50).iloc[-1]
        macd_1h, signal_1h, hist_1h = calculate_macd(df_1h['close'])
        adx_1h, plus_di_1h, minus_di_1h = calculate_adx(df_1h)
        
        # 4H indicators
        rsi_4h = calculate_rsi(df_4h['close']).iloc[-1]
        ema20_4h = calculate_ema(df_4h['close'], 20).iloc[-1]
        ema50_4h = calculate_ema(df_4h['close'], 50).iloc[-1]
        adx_4h, plus_di_4h, minus_di_4h = calculate_adx(df_4h)
        
        # Volume analysis
        vol_ma = df_15m['volume'].rolling(window=20).mean().iloc[-1]
        vol_ratio = df_15m['volume'].iloc[-1] / vol_ma if vol_ma > 0 else 1
        obv_slope = (obv_15m.iloc[-1] - obv_15m.iloc[-10]) / 10  # OBV trend
        
        return {
            'price': ticker['last'],
            'change_24h': ticker['percentage'],
            'high_24h': ticker['high'],
            'low_24h': ticker['low'],
            'volume': ticker['quoteVolume'],
            
            # 15M
            'rsi_15m': rsi_15m,
            'ema20_15m': ema20_15m,
            'ema50_15m': ema50_15m,
            'macd_15m': macd_15m.iloc[-1],
            'macd_signal_15m': signal_15m.iloc[-1],
            'macd_hist_15m': hist_15m.iloc[-1],
            'stoch_k_15m': stoch_k_15m.iloc[-1],
            'stoch_d_15m': stoch_d_15m.iloc[-1],
            'adx_15m': adx_15m.iloc[-1],
            'atr_15m': atr_15m,
            'bb_upper_15m': bb_upper_15m.iloc[-1],
            'bb_mid_15m': bb_mid_15m.iloc[-1],
            'bb_lower_15m': bb_lower_15m.iloc[-1],
            'vwap_15m': vwap_15m,
            'trend_15m': 'UP' if ema20_15m > ema50_15m else 'DOWN',
            
            # 1H
            'rsi_1h': rsi_1h,
            'ema20_1h': ema20_1h,
            'ema50_1h': ema50_1h,
            'macd_hist_1h': hist_1h.iloc[-1],
            'adx_1h': adx_1h.iloc[-1],
            'trend_1h': 'UP' if ema20_1h > ema50_1h else 'DOWN',
            
            # 4H
            'rsi_4h': rsi_4h,
            'ema20_4h': ema20_4h,
            'ema50_4h': ema50_4h,
            'adx_4h': adx_4h.iloc[-1],
            'trend_4h': 'UP' if ema20_4h > ema50_4h else 'DOWN',
            
            # Volume
            'vol_ratio': vol_ratio,
            'obv_slope': obv_slope
        }
    except Exception as e:
        print(f"{RED}Error fetching market data: {e}{RESET}")
        return None

def calculate_signal_score(market, position=None):
    """
    Institutional-grade weighted signal score (0-100)
    
    Breakdown:
    - Trend alignment (15m/1h/4h): 30 pts
    - Momentum (RSI + MACD + Stoch): 25 pts
    - Volume confirmation: 20 pts
    - Volatility favorable (ATR/BB): 15 pts
    - Level proximity (VWAP): 10 pts
    """
    score = 0
    details = []
    
    # 1. TREND ALIGNMENT (30 pts max)
    trend_score = 0
    if market['trend_4h'] == 'UP':
        trend_score += 12
        details.append("✅ 4H trend UP (+12)")
    else:
        details.append("❌ 4H trend DOWN (0)")
    
    if market['trend_1h'] == 'UP':
        trend_score += 10
        details.append("✅ 1H trend UP (+10)")
    else:
        details.append("❌ 1H trend DOWN (0)")
    
    if market['trend_15m'] == 'UP':
        trend_score += 8
        details.append("✅ 15M trend UP (+8)")
    else:
        details.append("❌ 15M trend DOWN (0)")
    
    score += trend_score
    
    # 2. MOMENTUM (25 pts max)
    momentum_score = 0
    
    # RSI momentum
    if 50 < market['rsi_15m'] < 70:
        momentum_score += 8
        details.append(f"✅ RSI bullish zone ({market['rsi_15m']:.1f}) (+8)")
    elif 30 < market['rsi_15m'] <= 50:
        momentum_score += 5
        details.append(f"⚠️  RSI neutral ({market['rsi_15m']:.1f}) (+5)")
    else:
        details.append(f"❌ RSI extreme ({market['rsi_15m']:.1f}) (0)")
    
    # MACD confirmation
    if market['macd_hist_15m'] > 0:
        momentum_score += 9
        details.append("✅ MACD histogram positive (+9)")
    else:
        details.append("❌ MACD histogram negative (0)")
    
    # Stochastic RSI
    if 20 < market.get('stoch_k_15m', 50) < 80:
        momentum_score += 8
        details.append("✅ Stoch RSI good range (+8)")
    else:
        details.append("⚠️  Stoch RSI extreme (0)")
    
    score += momentum_score
    
    # 3. VOLUME CONFIRMATION (20 pts max)
    volume_score = 0
    
    if market['vol_ratio'] > 1.5:
        volume_score += 12
        details.append(f"✅ Volume spike ({market['vol_ratio']:.1f}x) (+12)")
    elif market['vol_ratio'] > 1.0:
        volume_score += 8
        details.append(f"✅ Volume above average ({market['vol_ratio']:.1f}x) (+8)")
    else:
        details.append(f"⚠️  Low volume ({market['vol_ratio']:.1f}x) (0)")
    
    # OBV confirmation
    if market['obv_slope'] > 0:
        volume_score += 8
        details.append("✅ OBV trending up (+8)")
    else:
        details.append("❌ OBV trending down (0)")
    
    score += volume_score
    
    # 4. VOLATILITY FAVORABLE (15 pts max)
    volatility_score = 0
    
    # ADX strength
    if market['adx_15m'] > 25:
        volatility_score += 8
        details.append(f"✅ Strong trend (ADX {market['adx_15m']:.1f}) (+8)")
    elif market['adx_15m'] > 20:
        volatility_score += 4
        details.append(f"⚠️  Moderate trend (ADX {market['adx_15m']:.1f}) (+4)")
    else:
        details.append(f"❌ Choppy (ADX {market['adx_15m']:.1f}) (0)")
    
    # Bollinger Bands
    price = market['price']
    bb_position = (price - market['bb_lower_15m']) / (market['bb_upper_15m'] - market['bb_lower_15m'])
    if 0.3 < bb_position < 0.7:
        volatility_score += 7
        details.append("✅ BB mid-range (+7)")
    else:
        details.append("⚠️  BB extreme (0)")
    
    score += volatility_score
    
    # 5. LEVEL PROXIMITY - VWAP (10 pts max)
    level_score = 0
    
    if price > market['vwap_15m']:
        level_score += 10
        details.append("✅ Above VWAP - bullish control (+10)")
    else:
        details.append("❌ Below VWAP - bearish control (0)")
    
    score += level_score
    
    return score, details

def check_alerts(position, market):
    """Enhanced alert system using institutional indicators"""
    alerts = []
    
    # CRITICAL ALERTS - Position-specific
    if position:
        side = position.get('side', 'LONG').upper()
        liq_distance = position.get('liquidation_distance', 100)
        
        if liq_distance < 5:
            alerts.append(f"🚨 CRITICAL: {liq_distance:.2f}% from liquidation!")
        elif liq_distance < 10:
            alerts.append(f"⚠️  WARNING: {liq_distance:.2f}% from liquidation")
        
        # VWAP alerts - position aware
        if side == 'LONG' and market['price'] < market['vwap_15m']:
            alerts.append("⚠️  LONG: Price broke below VWAP - consider exit")
        elif side == 'SHORT' and market['price'] > market['vwap_15m']:
            alerts.append("⚠️  SHORT: Price broke above VWAP - consider exit")
        
        # ADX dropping = trend weakening
        if market['adx_15m'] < 20:
            alerts.append(f"⚠️  Weak trend (ADX {market['adx_15m']:.1f}) - choppy conditions")
    
    # SIGNAL ALERTS - Everyone
    
    # MACD crossover detection
    if abs(market['macd_hist_15m']) < 0.1:  # Near zero = potential crossover
        alerts.append("📊 MACD near crossover - momentum shift possible")
    
    # RSI + MACD divergence - position aware
    if position:
        side = position.get('side', 'LONG').upper()
        if market['rsi_15m'] > 70 and market['macd_hist_15m'] < 0:
            if side == 'SHORT':
                alerts.append("✅ SHORT: Bearish divergence - position favored")
            else:
                alerts.append("⚠️  LONG: Bearish divergence - consider exit")
        elif market['rsi_15m'] < 30 and market['macd_hist_15m'] > 0:
            if side == 'LONG':
                alerts.append("✅ LONG: Bullish divergence - position favored")
            else:
                alerts.append("⚠️  SHORT: Bullish divergence - consider exit")
    
    # ADX trend confirmation - position aware  
    if market['adx_15m'] > 25:
        if position:
            side = position.get('side', 'LONG').upper()
            if market['trend_15m'] == 'UP':
                symbol = "✅" if side == 'LONG' else "⚠️ "
                alerts.append(f"{symbol} STRONG UPTREND (ADX {market['adx_15m']:.1f})")
            else:
                symbol = "✅" if side == 'SHORT' else "⚠️ "
                alerts.append(f"{symbol} STRONG DOWNTREND (ADX {market['adx_15m']:.1f})")
        else:
            if market['trend_15m'] == 'UP':
                alerts.append(f"🚀 STRONG UPTREND (ADX {market['adx_15m']:.1f})")
            else:
                alerts.append(f"📉 STRONG DOWNTREND (ADX {market['adx_15m']:.1f})")
    
    # OBV divergence (price up but OBV down = bearish)
    if market['obv_slope'] < -0.5 and market['trend_15m'] == 'UP':
        alerts.append("⚠️  OBV DIVERGENCE: Price up but volume declining")
    
    # Bollinger Band extremes - position aware
    price = market['price']
    bb_position = (price - market['bb_lower_15m']) / (market['bb_upper_15m'] - market['bb_lower_15m'])
    
    if position:
        side = position.get('side', 'LONG').upper()
        if bb_position > 0.95:
            if side == 'LONG':
                alerts.append("⚠️  LONG: BB upper band - take profit zone")
            else:
                alerts.append("✅ SHORT: BB upper band - strong entry zone")
        elif bb_position < 0.05:
            if side == 'LONG':
                alerts.append("✅ LONG: BB lower band - strong entry zone")
            else:
                alerts.append("⚠️  SHORT: BB lower band - take profit zone")
    else:
        if bb_position > 0.95:
            alerts.append("⚠️  Price at BB upper band - potential reversal")
        elif bb_position < 0.05:
            alerts.append("✅ Price at BB lower band - potential bounce")
    
    # Multi-timeframe misalignment warning
    if market['trend_4h'] != market['trend_1h']:
        alerts.append(f"⚠️  TIMEFRAME CONFLICT: 4H {market['trend_4h']} vs 1H {market['trend_1h']}")
    
    # Volume spike
    if market['vol_ratio'] > 2.0:
        alerts.append(f"📊 VOLUME SPIKE: {market['vol_ratio']:.1f}x average")
    
    return alerts


def display_position_monitor(position, market, alerts, symbol_name):
    """Display position monitoring dashboard with institutional indicators"""
    clear_screen()
    
    print(f"{BOLD}{BLUE}{'='*75}{RESET}")
    print(f"{BOLD}{BLUE}{f'{symbol_name} FUTURES POSITION MONITOR':^75}{RESET}")
    print(f"{BOLD}{BLUE}{'='*75}{RESET}\n")
    
    price = market['price']
    entry = position['entry_price']
    liq = position.get('liquidation_price', 0)
    roe = position['unrealized_roe']
    upnl = position['unrealized_pnl']
    
    # Position info
    print(f"{BOLD}Position: {position['symbol']}{RESET}")
    print(f"  Side:           {position['side']} {position['leverage']:.2f}x")
    print(f"  Quantity:       {position['quantity']} contracts")
    print(f"  Margin:         ${position['margin']:.2f} USDT")
    print(f"\n  Entry Price:    ${entry:.4f}")
    print(f"  Mark Price:     ${price:.4f}")
    
    # PNL
    pnl_color = GREEN if roe >= 0 else RED
    print(f"\n  {BOLD}Unrealized PNL: {pnl_color}${upnl:+.2f} ({roe:+.2f}%){RESET}")
    
    # Liquidation
    if liq > 0:
        dist_to_liq = abs((price - liq) / price * 100)
        liq_color = RED if dist_to_liq < 5 else YELLOW if dist_to_liq < 10 else GREEN
        print(f"  Liquidation:    {liq_color}${liq:.4f} ({dist_to_liq:.2f}% away){RESET}")
    
    # Calculate and display signal score (position-aware)
    score, score_details = calculate_signal_score(market, position)
    
    # Interpret score based on position side
    side = position.get('side', 'LONG').upper()
    if side == 'SHORT':
        # For shorts: LOW score = good (bearish conditions)
        if score <= 30:
            score_state = f"{GREEN}STRONG BEARISH{RESET}"
            score_color = GREEN
        elif score <= 50:
            score_state = f"{YELLOW}WEAK BEARISH{RESET}"
            score_color = YELLOW
        else:
            score_state = f"{RED}BULLISH - EXIT{RESET}"
            score_color = RED
    else:
        # For longs: HIGH score = good (bullish conditions)
        if score >= 70:
            score_state = f"{GREEN}STRONG BULLISH{RESET}"
            score_color = GREEN
        elif score >= 50:
            score_state = f"{YELLOW}WEAK BULLISH{RESET}"
            score_color = YELLOW
        else:
            score_state = f"{RED}BEARISH - EXIT{RESET}"
            score_color = RED
    
    print(f"\n{BOLD}Signal Score: {score_color}{score}/100{RESET} {score_state}")
    print(f"  ({side} position - {'Lower' if side == 'SHORT' else 'Higher'} = better)")
    
    # Market data
    print(f"\n{BOLD}Market Data:{RESET}")
    print(f"  24h Change:     {market['change_24h']:+.2f}%")
    print(f"  24h High/Low:   ${market['high_24h']:.4f} / ${market['low_24h']:.4f}")
    print(f"  Volume:         ${market['volume']:,.0f} ({market['vol_ratio']:.1f}x avg)")
    
    # Multi-timeframe trend hierarchy
    print(f"\n{BOLD}Trend Hierarchy (4H → 1H → 15M):{RESET}")
    t4h_color = GREEN if market['trend_4h'] == 'UP' else RED
    t1h_color = GREEN if market['trend_1h'] == 'UP' else RED
    t15_color = GREEN if market['trend_15m'] == 'UP' else RED
    print(f"  4H Bias:        {t4h_color}{market['trend_4h']:^4}{RESET}  (Directional bias)")
    print(f"  1H Confirm:     {t1h_color}{market['trend_1h']:^4}{RESET}  (Trend confirmation)")
    print(f"  15M Entry:      {t15_color}{market['trend_15m']:^4}{RESET}  (Entry timing)")
    
    # Momentum indicators
    print(f"\n{BOLD}Momentum Indicators:{RESET}")
    print(f"  RSI (15M):      {market['rsi_15m']:.1f}")
    macd_color = GREEN if market['macd_hist_15m'] > 0 else RED
    print(f"  MACD Hist:      {macd_color}{market['macd_hist_15m']:+.2f}{RESET}")
    stoch_color = GREEN if 20 < market.get('stoch_k_15m', 50) < 80 else YELLOW
    print(f"  Stoch RSI:      {stoch_color}{market.get('stoch_k_15m', 50):.1f}{RESET}")
    
    # Trend strength
    print(f"\n{BOLD}Trend Strength:{RESET}")
    adx_val = market['adx_15m']
    if adx_val > 25:
        adx_label = f"{GREEN}STRONG{RESET}"
    elif adx_val > 20:
        adx_label = f"{YELLOW}MODERATE{RESET}"
    else:
        adx_label = f"{RED}WEAK/CHOPPY{RESET}"
    print(f"  ADX (15M):      {adx_val:.1f} ({adx_label})")
    print(f"  EMA20/50:       ${market['ema20_15m']:.4f} / ${market['ema50_15m']:.4f}")
    
    # Volatility & levels
    print(f"\n{BOLD}Volatility & Key Levels:{RESET}")
    print(f"  ATR (15M):      ${market['atr_15m']:.4f} (Stop guidance)")
    bb_upper = market['bb_upper_15m']
    bb_lower = market['bb_lower_15m']
    bb_pos = (price - bb_lower) / (bb_upper - bb_lower) * 100
    print(f"  BB Upper:       ${bb_upper:.4f}")
    print(f"  BB Lower:       ${bb_lower:.4f}")
    print(f"  BB Position:    {bb_pos:.0f}% from bottom")
    
    vwap_relation = "ABOVE" if price > market['vwap_15m'] else "BELOW"
    vwap_color = GREEN if vwap_relation == "ABOVE" else RED
    print(f"  VWAP:           ${market['vwap_15m']:.4f} ({vwap_color}{vwap_relation}{RESET})")
    
    # Volume analysis
    print(f"\n{BOLD}Volume Analysis:{RESET}")
    obv_trend = "UP ✓" if market['obv_slope'] > 0 else "DOWN ✗"
    obv_color = GREEN if market['obv_slope'] > 0 else RED
    print(f"  OBV Trend:      {obv_color}{obv_trend}{RESET}")
    print(f"  Vol Ratio:      {market['vol_ratio']:.2f}x average")
    
    # ATR-based stop suggestion
    if position['side'] == 'LONG':
        atr_stop = price - (market['atr_15m'] * 2)
        print(f"\n{BOLD}Risk Management:{RESET}")
        print(f"  ATR Stop (2x):  ${atr_stop:.4f} ({((atr_stop - price) / price * 100):.2f}%)")
    else:
        atr_stop = price + (market['atr_15m'] * 2)
        print(f"\n{BOLD}Risk Management:{RESET}")
        print(f"  ATR Stop (2x):  ${atr_stop:.4f} ({((atr_stop - price) / price * 100):.2f}%)")
    
    # Alerts
    if alerts:
        print(f"\n{BOLD}{RED}{'='*75}{RESET}")
        print(f"{BOLD}⚠️  ALERTS:{RESET}")
        for alert in alerts:
            print(f"  {alert}")
        print(f"{BOLD}{RED}{'='*75}{RESET}")
    
    print(f"\n{CYAN}Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    print(f"{CYAN}Press Ctrl+C to exit{RESET}")


def display_analysis_only(symbol_name, market):
    """Display institutional-grade technical analysis without position"""
    clear_screen()
    
    print(f"{BOLD}{BLUE}{'='*75}{RESET}")
    print(f"{BOLD}{BLUE}{f'{symbol_name} INSTITUTIONAL SIGNAL ENGINE':^75}{RESET}")
    print(f"{BOLD}{BLUE}{'='*75}{RESET}\n")
    
    price = market['price']
    
    # Calculate signal score
    score, score_details = calculate_signal_score(market)
    score_color = GREEN if score >= 70 else YELLOW if score >= 50 else RED
    
    # Trading recommendation
    if score >= 70:
        recommendation = f"{GREEN}{BOLD}🟢 STRONG BUY SIGNAL{RESET}"
    elif score >= 50:
        recommendation = f"{YELLOW}{BOLD}⚠️  NEUTRAL - Wait for confirmation{RESET}"
    else:
        recommendation = f"{RED}{BOLD}🔴 WEAK SIGNAL - Stay out{RESET}"
    
    print(f"{BOLD}Signal Score: {score_color}{score}/100{RESET}")
    print(f"{recommendation}\n")
    
    # Score breakdown
    print(f"{BOLD}Score Breakdown:{RESET}")
    for detail in score_details[:5]:  # Show first 5 components
        print(f"  {detail}")
    
    print(f"\n{BOLD}Market Data:{RESET}")
    print(f"  Current Price:  ${price:.4f}")
    print(f"  24h Change:     {market['change_24h']:+.2f}%")
    print(f"  24h High:       ${market['high_24h']:.4f}")
    print(f"  24h Low:        ${market['low_24h']:.4f}")
    print(f"  Volume:         ${market['volume']:,.0f} ({market['vol_ratio']:.1f}x avg)")
    
    # Multi-timeframe analysis
    print(f"\n{BOLD}Multi-Timeframe Trend:{RESET}")
    t4h_color = GREEN if market['trend_4h'] == 'UP' else RED
    t1h_color = GREEN if market['trend_1h'] == 'UP' else RED
    t15_color = GREEN if market['trend_15m'] == 'UP' else RED
    
    alignment = "✓ ALIGNED" if (market['trend_4h'] == market['trend_1h'] == market['trend_15m']) else "✗ MISALIGNED"
    align_color = GREEN if "ALIGNED" in alignment else YELLOW
    
    print(f"  4H (Bias):      {t4h_color}{market['trend_4h']:^4}{RESET}")
    print(f"  1H (Confirm):   {t1h_color}{market['trend_1h']:^4}{RESET}")
    print(f"  15M (Entry):    {t15_color}{market['trend_15m']:^4}{RESET}")
    print(f"  Status:         {align_color}{alignment}{RESET}")
    
    # Momentum
    print(f"\n{BOLD}Momentum Indicators:{RESET}")
    rsi = market['rsi_15m']
    if rsi > 70:
        rsi_state = f"{RED}OVERBOUGHT{RESET}"
    elif rsi > 50:
        rsi_state = f"{GREEN}BULLISH{RESET}"
    elif rsi > 30:
        rsi_state = f"{YELLOW}NEUTRAL{RESET}"
    else:
        rsi_state = f"{GREEN}OVERSOLD{RESET}"
    print(f"  RSI (15M):      {rsi:.1f} ({rsi_state})")
    
    macd_color = GREEN if market['macd_hist_15m'] > 0 else RED
    macd_state = "BULLISH" if market['macd_hist_15m'] > 0 else "BEARISH"
    print(f"  MACD:           {macd_color}{market['macd_hist_15m']:+.2f} ({macd_state}){RESET}")
    
    stoch_val = market.get('stoch_k_15m', 50)
    if stoch_val > 80:
        stoch_state = f"{RED}OVERBOUGHT{RESET}"
    elif stoch_val < 20:
        stoch_state = f"{GREEN}OVERSOLD{RESET}"
    else:
        stoch_state = f"{GREEN}NEUTRAL{RESET}"
    print(f"  Stoch RSI:      {stoch_val:.1f} ({stoch_state})")
    
    # Trend strength
    print(f"\n{BOLD}Trend Strength:{RESET}")
    adx_val = market['adx_15m']
    if adx_val > 25:
        adx_label = f"{GREEN}STRONG TREND{RESET}"
        advice = "✓ Safe to trade"
    elif adx_val > 20:
        adx_label = f"{YELLOW}MODERATE TREND{RESET}"
        advice = "⚠️  Caution advised"
    else:
        adx_label = f"{RED}WEAK/CHOPPY{RESET}"
        advice = "✗ DO NOT TRADE"
    print(f"  ADX:            {adx_val:.1f} ({adx_label})")
    print(f"  Advice:         {advice}")
    
    # Volatility
    print(f"\n{BOLD}Volatility & Levels:{RESET}")
    print(f"  ATR (15M):      ${market['atr_15m']:.4f}")
    
    bb_upper = market['bb_upper_15m']
    bb_lower = market['bb_lower_15m']
    bb_pos = (price - bb_lower) / (bb_upper - bb_lower) * 100
    if bb_pos > 80:
        bb_state = f"{YELLOW}Near upper band{RESET}"
    elif bb_pos < 20:
        bb_state = f"{GREEN}Near lower band{RESET}"
    else:
        bb_state = "Mid-range"
    print(f"  Bollinger:      {bb_pos:.0f}% from bottom ({bb_state})")
    
    vwap_diff = ((price - market['vwap_15m']) / market['vwap_15m']) * 100
    vwap_relation = "ABOVE" if vwap_diff > 0 else "BELOW"
    vwap_color = GREEN if vwap_diff > 0 else RED
    print(f"  VWAP:           ${market['vwap_15m']:.4f} ({vwap_color}{vwap_diff:+.2f}%{RESET})")
    
    # Volume
    print(f"\n{BOLD}Volume Analysis:{RESET}")
    obv_trend = "ACCUMULATION ✓" if market['obv_slope'] > 0 else "DISTRIBUTION ✗"
    obv_color = GREEN if market['obv_slope'] > 0 else RED
    print(f"  OBV:            {obv_color}{obv_trend}{RESET}")
    
    if market['vol_ratio'] > 2:
        vol_state = f"{GREEN}SPIKE{RESET}"
    elif market['vol_ratio'] > 1:
        vol_state = f"{GREEN}ABOVE AVG{RESET}"
    else:
        vol_state = f"{YELLOW}BELOW AVG{RESET}"
    print(f"  Volume:         {market['vol_ratio']:.2f}x ({vol_state})")
    
    # Entry suggestion
    print(f"\n{BOLD}Entry Guidance:{RESET}")
    if score >= 70:
        entry_type = "MARKET" if adx_val > 25 else "LIMIT"
        atr_stop = price - (market['atr_15m'] * 2)
        atr_target = price + (market['atr_15m'] * 3)
        print(f"  Type:           {GREEN}{entry_type} ENTRY{RESET}")
        print(f"  Stop Loss:      ${atr_stop:.4f} (2x ATR)")
        print(f"  Take Profit:    ${atr_target:.4f} (3x ATR)")
        print(f"  Risk/Reward:    1:1.5")
    else:
        print(f"  {YELLOW}Wait for score ≥70 before entering{RESET}")

    print(f"  MA50 (1H):      ${market['ma50_1h']:.4f}")
    
    # Trading suggestions
    print(f"\n{BOLD}Trading Suggestions:{RESET}")
    
    score = 0
    signals = []
    
    if 40 <= market['rsi_15m'] <= 65:
        score += 2
        signals.append("✅ 15M RSI in good range")
    elif market['rsi_15m'] > 70:
        signals.append("⚠️  15M RSI overbought - wait for pullback")
    elif market['rsi_15m'] < 30:
        signals.append("✅ 15M RSI oversold - potential bounce")
        score += 1
    
    if market['trend_15m'] == 'UP' and market['trend_1h'] == 'UP':
        score += 3
        signals.append("✅ Both trends UP - bullish")
    elif market['trend_15m'] == 'UP':
        score += 1
        signals.append("⚠️  15M up but 1H down - mixed signals")
    
    if market['change_24h'] > 0:
        score += 1
        signals.append("✅ Positive 24h momentum")
    
    print(f"\n  Entry Score: {score}/6")
    for sig in signals:
        print(f"  {sig}")
    
    if score >= 5:
        print(f"\n  {GREEN}{BOLD}🟢 STRONG ENTRY OPPORTUNITY{RESET}")
    elif score >= 3:
        print(f"\n  {YELLOW}🟡 MODERATE ENTRY - Be cautious{RESET}")
    else:
        print(f"\n  {RED}🔴 WAIT FOR BETTER SETUP{RESET}")
    
    # Suggested trade
    print(f"\n{BOLD}Suggested Trade Setup:{RESET}")
    print(f"  Entry:          ${price:.4f}")
    print(f"  Stop Loss:      ${price * 0.97:.4f} (-3%)")
    print(f"  Take Profit 1:  ${price * 1.03:.4f} (+3%)")
    print(f"  Take Profit 2:  ${price * 1.05:.4f} (+5%)")
    
    print(f"\n{CYAN}Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    print(f"{CYAN}Press Ctrl+C to exit{RESET}")

def quick_score_coin(exchange, symbol):
    """Quick institutional score for opportunity ranking (0-100)"""
    try:
        # Fetch minimal data for quick scoring
        ticker = exchange.fetch_ticker(symbol)
        ohlcv_15m = exchange.fetch_ohlcv(symbol, '15m', limit=100)
        ohlcv_1h = exchange.fetch_ohlcv(symbol, '1h', limit=100)
        ohlcv_4h = exchange.fetch_ohlcv(symbol, '4h', limit=50)
        
        df_15m = pd.DataFrame(ohlcv_15m, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df_1h = pd.DataFrame(ohlcv_1h, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df_4h = pd.DataFrame(ohlcv_4h, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Calculate key indicators
        rsi_15m = calculate_rsi(df_15m['close']).iloc[-1]
        ema20_15m = calculate_ema(df_15m['close'], 20).iloc[-1]
        ema50_15m = calculate_ema(df_15m['close'], 50).iloc[-1]
        
        ema20_1h = calculate_ema(df_1h['close'], 20).iloc[-1]
        ema50_1h = calculate_ema(df_1h['close'], 50).iloc[-1]
        
        ema20_4h = calculate_ema(df_4h['close'], 20).iloc[-1]
        ema50_4h = calculate_ema(df_4h['close'], 50).iloc[-1]
        
        macd_line, signal_line, hist = calculate_macd(df_15m['close'])
        macd_hist = hist.iloc[-1]
        
        adx = calculate_adx(df_15m).iloc[-1]
        
        # Volume ratio
        vol_avg = df_15m['volume'].rolling(window=20).mean().iloc[-1]
        vol_current = df_15m['volume'].iloc[-1]
        vol_ratio = vol_current / vol_avg if vol_avg > 0 else 1
        
        score = 0
        
        # Trend alignment (30 pts)
        trend_4h = 'UP' if ema20_4h > ema50_4h else 'DOWN'
        trend_1h = 'UP' if ema20_1h > ema50_1h else 'DOWN'
        trend_15m = 'UP' if ema20_15m > ema50_15m else 'DOWN'
        
        if trend_4h == 'UP':
            score += 12
        if trend_1h == 'UP':
            score += 10
        if trend_15m == 'UP':
            score += 8
        
        # Momentum (25 pts)
        if 50 < rsi_15m < 70:
            score += 8
        elif 30 < rsi_15m <= 50:
            score += 5
        
        if macd_hist > 0:
            score += 9
        
        # Assume neutral stoch for quick scoring
        score += 4
        
        # Volume (20 pts)
        if vol_ratio > 1.5:
            score += 12
        elif vol_ratio > 1.0:
            score += 8
        
        # Assume positive OBV for quick scoring
        score += 4
        
        # Volatility (15 pts)
        if adx > 25:
            score += 8
        elif adx > 20:
            score += 4
        
        # Assume mid-BB for quick scoring
        score += 3
        
        # Level (10 pts) - price above EMAs
        price = df_15m['close'].iloc[-1]
        if price > ema20_15m and price > ema50_15m:
            score += 10
        
        return min(score, 100)
    except Exception as e:
        return 0


def get_available_coins():
    """Return list of popular USDT futures coins"""
    return [
        'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'ADA/USDT',
        'DOGE/USDT', 'DOT/USDT', 'AVAX/USDT', 'LINK/USDT', 'UNI/USDT',
        'ATOM/USDT', 'LTC/USDT', 'NEAR/USDT', 'APT/USDT', 'ARB/USDT',
        'OP/USDT', 'INJ/USDT', 'SUI/USDT', 'TIA/USDT', 'FET/USDT',
        'RENDER/USDT', 'GRT/USDT', 'ALGO/USDT', 'HBAR/USDT', 'PEPE/USDT'
    ]

def main():
    exchange = ccxt.kucoin({
        'apiKey': os.getenv('KUCOIN_API_KEY'),
        'secret': os.getenv('KUCOIN_API_SECRET'),
        'password': os.getenv('KUCOIN_API_PASSPHRASE'),
        'enableRateLimit': True
    })
    
    print(f"{BOLD}{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{CYAN}{'UNIVERSAL CRYPTO FUTURES MONITOR':^60}{RESET}")
    print(f"{BOLD}{CYAN}{'='*60}{RESET}\n")
    
    print("Checking for open positions...\n")
    
    active_positions = get_active_positions(exchange)
    
    if active_positions:
        print(f"{GREEN}Found {len(active_positions)} open position(s):{RESET}\n")
        
        for idx, pos in enumerate(active_positions, 1):
            pnl_color = GREEN if pos['unrealized_roe'] >= 0 else RED
            print(f"  {idx}. {pos['symbol']} - {pos['side']} {pos['leverage']:.1f}x - "
                  f"{pnl_color}PNL: {pos['unrealized_roe']:+.2f}%{RESET}")
        
        print(f"\nDo you want to monitor a position? (y/n): ", end='')
        choice = input().strip().lower()
        
        if choice == 'y':
            if len(active_positions) == 1:
                selected_pos = active_positions[0]
                print(f"\nMonitoring {selected_pos['symbol']}...\n")
            else:
                print(f"Select position to monitor (1-{len(active_positions)}): ", end='')
                sel = input().strip()
                try:
                    selected_pos = active_positions[int(sel) - 1]
                except:
                    print(f"{RED}Invalid selection. Exiting.{RESET}")
                    return
            
            # Monitor selected position
            symbol = convert_to_spot_symbol(selected_pos['symbol'])
            print(f"Starting monitor for {symbol}...\n")
            time.sleep(2)
            
            try:
                while True:
                    # Refresh position data
                    positions = get_active_positions(exchange)
                    current_pos = None
                    for p in positions:
                        if p['symbol'] == selected_pos['symbol']:
                            current_pos = p
                            break
                    
                    if not current_pos:
                        print(f"{YELLOW}Position closed. Exiting monitor.{RESET}")
                        break
                    
                    market = get_market_data(exchange, symbol)
                    if not market:
                        time.sleep(10)
                        continue
                    
                    alerts = check_alerts(current_pos, market)
                    display_position_monitor(current_pos, market, alerts, symbol)
                    time.sleep(10)
                    
            except KeyboardInterrupt:
                print(f"\n\n{YELLOW}Monitor stopped{RESET}")
                return
        else:
            print(f"{YELLOW}Exiting.{RESET}")
            return
    
    # No positions - offer coin analysis
    print(f"{YELLOW}No open positions found.{RESET}\n")
    print("Would you like technical analysis for a coin? (y/n): ", end='')
    choice = input().strip().lower()
    
    if choice != 'y':
        print(f"{YELLOW}Exiting.{RESET}")
        return
    
    coins = get_available_coins()
    print(f"\n{BOLD}Available Coins:{RESET}")
    
    # Quick score all coins
    print(f"{CYAN}Analyzing coins for opportunities...{RESET}")
    coin_scores = []
    
    for idx, coin in enumerate(coins, 1):
        score = quick_score_coin(exchange, coin)
        coin_scores.append((idx, coin, score))
        print(f"  {idx:2}. {coin}")
    
    # Find best opportunities (score >= 6)
    best_opportunities = [idx for idx, coin, score in coin_scores if score >= 6]
    
    if best_opportunities:
        best_str = ', '.join([f"#{num}" for num in best_opportunities])
        print(f"\n{GREEN}{BOLD}Script analysis says {best_str} present the best opportunities for trading currently.{RESET}")
    else:
        print(f"\n{YELLOW}Market conditions mixed - no strong opportunities detected at this time.{RESET}")
    
    print(f"\nSelect coin number (1-{len(coins)}): ", end='')
    sel = input().strip()
    
    try:
        selected_coin = coins[int(sel) - 1]
    except:
        print(f"{RED}Invalid selection. Exiting.{RESET}")
        return
    
    print(f"\nAnalyzing {selected_coin}...\n")
    time.sleep(2)
    
    try:
        while True:
            market = get_market_data(exchange, selected_coin)
            if not market:
                time.sleep(10)
                continue
            
            display_analysis_only(selected_coin, market)
            time.sleep(10)
            
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Analysis stopped{RESET}")

if __name__ == "__main__":
    main()
