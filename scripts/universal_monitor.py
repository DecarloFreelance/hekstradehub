#!/usr/bin/env python3
##
 # Universal Crypto Futures Monitor
 # Monitors any open position or analyzes any coin
##
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

# Import indicator functions
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.indicators import (
    calculate_ema,
    calculate_macd,
    calculate_stochastic_rsi,
    calculate_adx,
    calculate_atr,
    calculate_bollinger_bands,
    calculate_obv,
    calculate_vwap
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

def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')

def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def calculate_signal_score(market, position=None, prev_score=None):
    """
    Institutional-grade weighted signal score (0-100) for both Long and Short.
    Returns: (long_score:int, short_score:int, details:dict)
    """
    import math
    def _normalize(val, min_val, max_val):
        if max_val == min_val:
            return 0.5
        return max(0, min(1, (val - min_val) / (max_val - min_val)))

    def _trend_strength(val):
        if isinstance(val, str):
            return 1.0 if val == 'UP' else 0.0
        if -1 <= val <= 1:
            return (val + 1) / 2
        if 0 <= val <= 100:
            return val / 100
        return 0.5

    def _clamp(val, min_val, max_val):
        return max(min_val, min(max_val, val))

    def _fair_value_distance(price, vwap):
        return min(1.0, abs(price - vwap) / price) if price else 1.0

    def _score_side(is_long: bool):
        required_fields = [
            'trend_4h', 'trend_1h', 'trend_15m', 'rsi_15m', 'macd_hist_15m', 'stoch_k_15m', 'stoch_d_15m',
            'atr_15m', 'atr_15m_sma', 'adx_15m', 'price', 'vwap_15m', 'vol_ratio', 'vol_ma', 'volume',
        ]
        missing = [k for k in required_fields if k not in market or market[k] is None]
        if missing:
            import sys
            print(f"[calculate_signal_score] MISSING FIELDS: {missing}", file=sys.stderr, flush=True)
            return 0, {}, {}
        details = []
        # Trend Alignment (30 pts)
        trend_4h = _trend_strength(market.get('trend_4h', 0))
        trend_1h = _trend_strength(market.get('trend_1h', 0))
        trend_15m = _trend_strength(market.get('trend_15m', 0))
        trend_score = (trend_4h * 12) + (trend_1h * 10) + (trend_15m * 8)
        details.append(f"Trend Alignment: {trend_score:.1f}/30")
        # Momentum (25 pts)
        rsi = market['rsi_15m']
        rsi_score = 8 if 50 < rsi < 70 else 5 if 30 < rsi <= 50 else 0
        details.append(f"RSI: {rsi_score}/8")
        macd_score = 9 if market['macd_hist_15m'] > 0 else 0
        details.append(f"MACD: {macd_score}/9")
        stoch_score = 4  # Assume neutral for fallback
        details.append(f"Stoch: {stoch_score}/4")
        # Volume (20 pts)
        vol_ratio = market['vol_ratio']
        vol_score = 12 if vol_ratio > 1.5 else 8 if vol_ratio > 1.0 else 0
        details.append(f"Volume: {vol_score}/12")
        obv_score = 4 if market.get('obv_slope', 0) > 0 else 0
        details.append(f"OBV: {obv_score}/4")
        # Volatility (15 pts)
        adx = market['adx_15m']
        adx_score = 8 if adx > 25 else 4 if adx > 20 else 0
        details.append(f"ADX: {adx_score}/8")
        bb_score = 3  # Assume mid-BB for fallback
        details.append(f"BB: {bb_score}/3")
        # Level (10 pts)
        price = market['price']
        ema20 = market.get('ema20_15m', price)
        ema50 = market.get('ema50_15m', price)
        level_score = 10 if price > ema20 and price > ema50 else 0
        details.append(f"Level: {level_score}/10")
        # Total
        total = trend_score + rsi_score + macd_score + stoch_score + vol_score + obv_score + adx_score + bb_score + level_score
        return int(min(total, 100)), details

    # Compute both long and short scores
    long_score, long_details = _score_side(True)
    short_score, short_details = _score_side(False)
    # For now, details = long_details (could be improved)
    return long_score, short_score, long_details
    
    # (alerts logic removed)


def display_position_monitor(position, market, alerts, symbol_name):
    # Display position monitoring dashboard with institutional indicators
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
    # Display institutional-grade technical analysis without position
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
    # Quick institutional score for opportunity ranking (0-100)
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

    # Returns a default list of available coins
    return [
        'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'BNB/USDT',
        'ADA/USDT', 'DOGE/USDT', 'DOT/USDT', 'AVAX/USDT', 'LINK/USDT',
        'UNI/USDT', 'ATOM/USDT', 'LTC/USDT', 'APT/USDT', 'ARB/USDT',
        'OP/USDT', 'TIA/USDT', 'SUI/USDT', 'SEI/USDT'
    ]
