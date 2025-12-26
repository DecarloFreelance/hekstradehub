#!/usr/bin/env python3
"""
Quick Scalp Finder - Optimized for small accounts and short-term trades
Focus: 15m and 5m timeframes for quick entries/exits
"""

import ccxt
import pandas as pd
from dotenv import load_dotenv
import os
import sys
import argparse

# RAM Protection
sys.path.insert(0, '/home/hektic/saddynhektic workspace')
try:
    from Tools.resource_manager import check_ram_before_processing
    check_ram_before_processing(min_free_gb=1.5)
except:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from core.indicators import (
    calculate_ema, calculate_rsi, calculate_macd,
    calculate_adx, calculate_atr, calculate_stochastic_rsi
)

load_dotenv()

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
BOLD = '\033[1m'
RESET = '\033[0m'

def analyze_scalp_setup(exchange, symbol):
    """
    Analyze for quick scalp opportunities
    Criteria:
    - Strong short-term momentum
    - Clear direction on 5m and 15m
    - Low noise / high probability
    """
    
    try:
        # Fetch 5m and 15m data
        ohlcv_5m = exchange.fetch_ohlcv(symbol, '5m', limit=100)
        ohlcv_15m = exchange.fetch_ohlcv(symbol, '15m', limit=100)
        ohlcv_1h = exchange.fetch_ohlcv(symbol, '1h', limit=50)
        
        df_5m = pd.DataFrame(ohlcv_5m, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df_15m = pd.DataFrame(ohlcv_15m, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df_1h = pd.DataFrame(ohlcv_1h, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        current_price = df_5m['close'].iloc[-1]
        
        # === 5M ANALYSIS ===
        rsi_5m = calculate_rsi(df_5m['close'], 14).iloc[-1]
        ema9_5m = calculate_ema(df_5m['close'], 9).iloc[-1]
        ema21_5m = calculate_ema(df_5m['close'], 21).iloc[-1]
        macd_5m, signal_5m, hist_5m = calculate_macd(df_5m['close'])
        
        # === 15M ANALYSIS ===
        rsi_15m = calculate_rsi(df_15m['close'], 14).iloc[-1]
        ema9_15m = calculate_ema(df_15m['close'], 9).iloc[-1]
        ema21_15m = calculate_ema(df_15m['close'], 21).iloc[-1]
        adx_15m = calculate_adx(df_15m, 14).iloc[-1]
        atr_15m = calculate_atr(df_15m, 14).iloc[-1]
        macd_15m, signal_15m, hist_15m = calculate_macd(df_15m['close'])
        
        # === 1H TREND ===
        ema50_1h = calculate_ema(df_1h['close'], 50).iloc[-1]
        trend_1h = 'BULLISH' if current_price > ema50_1h else 'BEARISH'
        
        # === SCORING ===
        long_score = 0
        short_score = 0
        
        # 5m momentum
        if current_price > ema9_5m > ema21_5m:
            long_score += 15
        elif current_price < ema9_5m < ema21_5m:
            short_score += 15
        
        # 15m momentum
        if current_price > ema9_15m > ema21_15m:
            long_score += 20
        elif current_price < ema9_15m < ema21_15m:
            short_score += 20
        
        # RSI scalp zones (5m)
        if 45 < rsi_5m < 65:  # Healthy uptrend zone
            long_score += 10
        elif 35 < rsi_5m < 55:  # Healthy downtrend zone
            short_score += 10
        
        # RSI extremes for reversals
        if rsi_5m < 30 and hist_5m.iloc[-1] > hist_5m.iloc[-2]:
            long_score += 15  # Oversold bounce
        elif rsi_5m > 70 and hist_5m.iloc[-1] < hist_5m.iloc[-2]:
            short_score += 15  # Overbought rejection
        
        # MACD agreement
        if hist_5m.iloc[-1] > 0 and hist_15m.iloc[-1] > 0:
            long_score += 15
        elif hist_5m.iloc[-1] < 0 and hist_15m.iloc[-1] < 0:
            short_score += 15
        
        # ADX strength (15m)
        if adx_15m > 25:
            if current_price > ema21_15m:
                long_score += 10
            else:
                short_score += 10
        
        # 1H trend alignment
        if trend_1h == 'BULLISH':
            long_score += 10
        else:
            short_score += 10
        
        # Volume surge on 5m
        avg_volume = df_5m['volume'].tail(20).mean()
        current_volume = df_5m['volume'].iloc[-1]
        if current_volume > avg_volume * 1.3:
            if current_price > df_5m['open'].iloc[-1]:
                long_score += 10
            else:
                short_score += 10
        
        # Determine signal
        if long_score >= 60 and long_score > short_score + 15:
            signal = 'LONG'
            score = long_score
        elif short_score >= 60 and short_score > long_score + 15:
            signal = 'SHORT'
            score = short_score
        else:
            signal = 'NEUTRAL'
            score = max(long_score, short_score)
        
        # Calculate entry and stops
        if signal == 'LONG':
            entry = current_price
            stop = current_price - (atr_15m * 1.2)  # Tight stop for scalp
            tp1 = current_price + (atr_15m * 2.5)
            tp2 = current_price + (atr_15m * 4.0)
        elif signal == 'SHORT':
            entry = current_price
            stop = current_price + (atr_15m * 1.2)
            tp1 = current_price - (atr_15m * 2.5)
            tp2 = current_price - (atr_15m * 4.0)
        else:
            entry = stop = tp1 = tp2 = 0
        
        return {
            'symbol': symbol,
            'signal': signal,
            'score': score,
            'long_score': long_score,
            'short_score': short_score,
            'current_price': current_price,
            'entry': entry,
            'stop': stop,
            'tp1': tp1,
            'tp2': tp2,
            'atr_15m': atr_15m,
            'rsi_5m': rsi_5m,
            'rsi_15m': rsi_15m,
            'adx_15m': adx_15m,
            'trend_1h': trend_1h,
            'volume_surge': current_volume > avg_volume * 1.3
        }
    
    except Exception as e:
        return {
            'symbol': symbol,
            'error': str(e)
        }


def print_scalp_analysis(analysis):
    """Pretty print scalp analysis"""
    
    if 'error' in analysis:
        print(f"{RED}✗ {analysis['symbol']}: {analysis['error']}{RESET}")
        return
    
    signal = analysis['signal']
    score = analysis['score']
    
    # Color coding
    if signal == 'LONG':
        signal_color = GREEN
        signal_icon = '↑'
    elif signal == 'SHORT':
        signal_color = RED
        signal_icon = '↓'
    else:
        signal_color = YELLOW
        signal_icon = '•'
    
    print(f"\n{BOLD}{'=' * 70}{RESET}")
    print(f"{BOLD}{analysis['symbol']}{RESET}")
    print(f"{'=' * 70}")
    
    print(f"\n{BOLD}SIGNAL:{RESET} {signal_color}{signal} {signal_icon} ({score}/100){RESET}")
    print(f"Current Price: ${analysis['current_price']:.4f}")
    
    if signal != 'NEUTRAL':
        print(f"\n{BOLD}ENTRY PLAN{RESET}")
        print(f"Entry:  ${analysis['entry']:.4f}")
        print(f"Stop:   ${analysis['stop']:.4f}")
        print(f"TP1:    ${analysis['tp1']:.4f} (2.5R) - Close 60%")
        print(f"TP2:    ${analysis['tp2']:.4f} (4.0R) - Close 40%")
        
        risk_pct = abs((analysis['entry'] - analysis['stop']) / analysis['entry'] * 100)
        print(f"Risk:   {risk_pct:.2f}%")
    
    print(f"\n{BOLD}INDICATORS{RESET}")
    print(f"RSI 5m:   {analysis['rsi_5m']:.1f}")
    print(f"RSI 15m:  {analysis['rsi_15m']:.1f}")
    print(f"ADX 15m:  {analysis['adx_15m']:.1f}")
    print(f"ATR 15m:  ${analysis['atr_15m']:.2f}")
    print(f"1H Trend: {analysis['trend_1h']}")
    print(f"Volume:   {'🔥 SURGE' if analysis['volume_surge'] else 'Normal'}")
    
    print(f"\n{BOLD}SCORES{RESET}")
    print(f"Long:  {GREEN}{analysis['long_score']}/100{RESET}")
    print(f"Short: {RED}{analysis['short_score']}/100{RESET}")
    
    print(f"{BOLD}{'=' * 70}{RESET}\n")


def scan_multiple(exchange, symbols, min_score=60):
    """Scan multiple symbols for scalp opportunities"""
    
    opportunities = []
    
    print(f"\n{BOLD}{CYAN}Scanning {len(symbols)} symbols for scalp setups...{RESET}\n")
    
    for symbol in symbols:
        print(f"Analyzing {symbol}...", end=' ', flush=True)
        analysis = analyze_scalp_setup(exchange, symbol)
        
        if 'error' not in analysis and analysis['signal'] != 'NEUTRAL' and analysis['score'] >= min_score:
            opportunities.append(analysis)
            print(f"{GREEN}✓ {analysis['signal']} ({analysis['score']}){RESET}")
        else:
            print(f"{YELLOW}○{RESET}")
        
        time.sleep(0.5)  # Rate limit
    
    return opportunities


def main():
    parser = argparse.ArgumentParser(description='Quick Scalp Finder for Small Accounts')
    parser.add_argument('--symbol', type=str, help='Specific symbol to analyze')
    parser.add_argument('--scan', action='store_true', help='Scan multiple symbols')
    parser.add_argument('--min-score', type=int, default=60, help='Minimum score for signals')
    
    args = parser.parse_args()
    
    # Initialize exchange
    exchange = ccxt.kucoinfutures({
        'apiKey': os.getenv('KUCOIN_API_KEY'),
        'secret': os.getenv('KUCOIN_API_SECRET'),
        'password': os.getenv('KUCOIN_API_PASSPHRASE'),
        'enableRateLimit': True,
    })
    
    if args.scan:
        # Popular liquid futures for scalping
        symbols = [
            'BTC/USDT:USDT',
            'ETH/USDT:USDT',
            'SOL/USDT:USDT',
            'DOGE/USDT:USDT',
            'PEPE/USDT:USDT',
            'XRP/USDT:USDT',
            'BNB/USDT:USDT',
            'ADA/USDT:USDT',
        ]
        
        opportunities = scan_multiple(exchange, symbols, args.min_score)
        
        if opportunities:
            print(f"\n{BOLD}{GREEN}Found {len(opportunities)} scalp opportunities:{RESET}\n")
            for opp in sorted(opportunities, key=lambda x: x['score'], reverse=True):
                print_scalp_analysis(opp)
        else:
            print(f"\n{YELLOW}No opportunities found above {args.min_score} score.{RESET}\n")
    
    elif args.symbol:
        analysis = analyze_scalp_setup(exchange, args.symbol)
        print_scalp_analysis(analysis)
    
    else:
        # Default: analyze BTC
        analysis = analyze_scalp_setup(exchange, 'BTC/USDT:USDT')
        print_scalp_analysis(analysis)
        
        print(f"\n{CYAN}Usage:{RESET}")
        print(f"  python quick_scalp_finder.py --symbol BTC/USDT:USDT")
        print(f"  python quick_scalp_finder.py --scan --min-score 65\n")


if __name__ == '__main__':
    import time
    main()
