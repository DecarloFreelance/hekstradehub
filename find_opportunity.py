#!/usr/bin/env python3
"""Find best trading opportunities on KuCoin Futures"""
import ccxt
import pandas as pd
from dotenv import load_dotenv
import os
import sys

# RAM Protection - Prevent system crashes during analysis
sys.path.insert(0, '/home/hektic/saddynhektic workspace')
try:
    from Tools.resource_manager import check_ram_before_processing
    check_ram_before_processing(min_free_gb=1.5)
except ImportError:
    print("⚠️  Warning: RAM protection not available")
except MemoryError as e:
    print(f"❌ Insufficient RAM: {e}")
    print("Close some applications and try again.")
    exit(1)

sys.path.insert(0, os.path.dirname(__file__))
from core.indicators import (
    calculate_ema, calculate_macd, calculate_rsi,
    calculate_stochastic_rsi, calculate_adx, calculate_atr,
    calculate_bollinger_bands, calculate_obv
)

load_dotenv()

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
BOLD = '\033[1m'
RESET = '\033[0m'

def analyze_coin(exchange, symbol):
    """Deep analysis of a single coin"""
    try:
        # Fetch multi-timeframe data
        ohlcv_15m = exchange.fetch_ohlcv(symbol, '15m', limit=100)
        ohlcv_1h = exchange.fetch_ohlcv(symbol, '1h', limit=100)
        ohlcv_4h = exchange.fetch_ohlcv(symbol, '4h', limit=50)
        
        df_15m = pd.DataFrame(ohlcv_15m, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df_1h = pd.DataFrame(ohlcv_1h, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df_4h = pd.DataFrame(ohlcv_4h, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Current price
        price = df_15m['close'].iloc[-1]
        
        # Indicators
        rsi_15m = calculate_rsi(df_15m['close']).iloc[-1]
        rsi_1h = calculate_rsi(df_1h['close']).iloc[-1]
        
        ema20_15m = calculate_ema(df_15m['close'], 20).iloc[-1]
        ema50_15m = calculate_ema(df_15m['close'], 50).iloc[-1]
        ema20_1h = calculate_ema(df_1h['close'], 20).iloc[-1]
        ema50_1h = calculate_ema(df_1h['close'], 50).iloc[-1]
        ema20_4h = calculate_ema(df_4h['close'], 20).iloc[-1]
        ema50_4h = calculate_ema(df_4h['close'], 50).iloc[-1]
        
        macd_line, signal_line, hist = calculate_macd(df_15m['close'])
        macd_hist = hist.iloc[-1]
        
        stoch_k, stoch_d = calculate_stochastic_rsi(df_15m['close'])
        stoch_k_val = stoch_k.iloc[-1]
        
        adx = calculate_adx(df_15m).iloc[-1]
        
        bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(df_15m['close'])
        bb_position = (price - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1]) * 100
        
        obv = calculate_obv(df_15m)
        obv_slope = obv.diff().iloc[-1]
        
        # Volume
        vol_avg = df_15m['volume'].rolling(window=20).mean().iloc[-1]
        vol_current = df_15m['volume'].iloc[-1]
        vol_ratio = vol_current / vol_avg if vol_avg > 0 else 1
        
        # Trend
        trend_4h = 'UP' if ema20_4h > ema50_4h else 'DOWN'
        trend_1h = 'UP' if ema20_1h > ema50_1h else 'DOWN'
        trend_15m = 'UP' if ema20_15m > ema50_15m else 'DOWN'
        
        # Calculate score
        score = 0
        
        # Trend alignment (30 pts)
        if trend_4h == 'UP': score += 12
        if trend_1h == 'UP': score += 10
        if trend_15m == 'UP': score += 8
        
        # Momentum (25 pts)
        if 50 < rsi_15m < 70: score += 8
        elif 30 < rsi_15m <= 50: score += 5
        if macd_hist > 0: score += 9
        if 20 < stoch_k_val < 80: score += 4
        elif stoch_k_val < 20: score += 6  # Oversold can be opportunity
        
        # Volume (20 pts)
        if vol_ratio > 1.5: score += 12
        elif vol_ratio > 1.0: score += 8
        if obv_slope > 0: score += 4
        
        # Volatility (15 pts)
        if adx > 25: score += 8
        elif adx > 20: score += 4
        if 30 < bb_position < 70: score += 3
        
        # Level (10 pts)
        if price > ema20_15m and price > ema50_15m: score += 10
        
        return {
            'symbol': symbol,
            'price': price,
            'score': score,
            'trend_4h': trend_4h,
            'trend_1h': trend_1h,
            'trend_15m': trend_15m,
            'rsi_15m': rsi_15m,
            'rsi_1h': rsi_1h,
            'macd_hist': macd_hist,
            'stoch_k': stoch_k_val,
            'adx': adx,
            'vol_ratio': vol_ratio,
            'obv_slope': obv_slope,
            'bb_position': bb_position,
        }
        
    except Exception as e:
        return None

def find_opportunities():
    """Scan multiple coins for best opportunities"""
    exchange = ccxt.kucoinfutures({
        'apiKey': os.getenv('KUCOIN_API_KEY'),
        'secret': os.getenv('KUCOIN_API_SECRET'),
        'password': os.getenv('KUCOIN_API_PASSPHRASE'),
        'enableRateLimit': True,
    })
    
    # Top liquid coins on KuCoin Futures
    symbols = [
        'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 
        'XRP/USDT:USDT', 'BNB/USDT:USDT', 'DOGE/USDT:USDT',
        'ADA/USDT:USDT', 'LINK/USDT:USDT', 'AVAX/USDT:USDT',
        'DOT/USDT:USDT', 'MATIC/USDT:USDT', 'UNI/USDT:USDT',
        'ATOM/USDT:USDT', 'LTC/USDT:USDT', 'APT/USDT:USDT',
        'ARB/USDT:USDT', 'OP/USDT:USDT', 'SUI/USDT:USDT',
        'TIA/USDT:USDT', 'SEI/USDT:USDT', 'FTM/USDT:USDT',
        'INJ/USDT:USDT', 'NEAR/USDT:USDT', 'AAVE/USDT:USDT'
    ]
    
    print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}{BLUE}{'SCANNING FOR BEST OPPORTUNITIES':^70}{RESET}")
    print(f"{BOLD}{BLUE}{'='*70}{RESET}\n")
    print(f"{CYAN}Analyzing {len(symbols)} coins...{RESET}\n")
    
    results = []
    for symbol in symbols:
        print(f"  Analyzing {symbol}...", end='\r')
        result = analyze_coin(exchange, symbol)
        if result:
            results.append(result)
    
    print(" " * 50, end='\r')  # Clear line
    
    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # Display top 10
    print(f"\n{BOLD}{'='*70}{RESET}")
    print(f"{BOLD}TOP 10 OPPORTUNITIES (Sorted by Score){RESET}")
    print(f"{'='*70}\n")
    
    for i, r in enumerate(results[:10], 1):
        symbol = r['symbol'].replace('/USDT:USDT', '')
        score = r['score']
        
        # Color based on score
        if score >= 70:
            score_color = GREEN
            signal = "STRONG BUY"
        elif score >= 60:
            score_color = YELLOW
            signal = "BUY"
        elif score >= 50:
            score_color = YELLOW
            signal = "WEAK BUY"
        else:
            score_color = RED
            signal = "WAIT"
        
        trend_str = f"{r['trend_4h'][0]}/{r['trend_1h'][0]}/{r['trend_15m'][0]}"
        
        print(f"{BOLD}#{i}. {symbol:<8}{RESET} | Score: {score_color}{score:>3}/100{RESET} | {signal}")
        print(f"     Price: ${r['price']:.6f}")
        print(f"     Trends: {trend_str} | RSI: {r['rsi_15m']:.1f} | ADX: {r['adx']:.1f} | Vol: {r['vol_ratio']:.2f}x")
        print(f"     MACD: {r['macd_hist']:.6f} | Stoch: {r['stoch_k']:.1f} | BB: {r['bb_position']:.1f}%")
        print()
    
    # Highlight THE BEST
    if results:
        best = results[0]
        print(f"\n{BOLD}{GREEN}{'='*70}{RESET}")
        print(f"{BOLD}{GREEN}🎯 BEST OPPORTUNITY: {best['symbol'].replace('/USDT:USDT', '')}{RESET}")
        print(f"{BOLD}{GREEN}{'='*70}{RESET}\n")
        
        symbol_clean = best['symbol'].replace('/USDT:USDT', '')
        print(f"{BOLD}Score: {best['score']}/100{RESET}")
        print(f"Price: ${best['price']:.6f}")
        print(f"\nTrend Alignment:")
        print(f"  4H:  {GREEN if best['trend_4h']=='UP' else RED}{best['trend_4h']}{RESET}")
        print(f"  1H:  {GREEN if best['trend_1h']=='UP' else RED}{best['trend_1h']}{RESET}")
        print(f"  15M: {GREEN if best['trend_15m']=='UP' else RED}{best['trend_15m']}{RESET}")
        
        print(f"\nMomentum:")
        print(f"  RSI (15M): {best['rsi_15m']:.2f}")
        print(f"  MACD Hist: {best['macd_hist']:.6f}")
        print(f"  Stoch K: {best['stoch_k']:.2f}")
        
        print(f"\nStrength & Volume:")
        print(f"  ADX: {best['adx']:.2f}")
        print(f"  Volume Ratio: {best['vol_ratio']:.2f}x")
        print(f"  OBV Slope: {best['obv_slope']:+.2f}")
        
        print(f"\n{BOLD}Suggested Setup:{RESET}")
        entry = best['price']
        print(f"  Entry: ${entry:.6f}")
        print(f"  Stop Loss (-5%): ${entry * 0.95:.6f}")
        print(f"  TP1 (+5%): ${entry * 1.05:.6f}")
        print(f"  TP2 (+10%): ${entry * 1.10:.6f}")
        print(f"  TP3 (+15%): ${entry * 1.15:.6f}")
        
        print(f"\n{YELLOW}⚠️  With $5-6 capital, consider 10-15x leverage for meaningful returns{RESET}")
        print(f"{YELLOW}⚠️  BUT: Higher leverage = higher risk. Use tight stops!{RESET}")
        
        print(f"\n{BOLD}{GREEN}{'='*70}{RESET}\n")

if __name__ == '__main__':
    find_opportunities()
