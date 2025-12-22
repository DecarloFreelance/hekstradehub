#!/usr/bin/env python3
"""
Institutional-Grade Opportunity Scanner
Finds high-probability setups using weighted 0-100 scoring system
"""
import os
import ccxt
import pandas as pd
from dotenv import load_dotenv
import sys

# Import calculation functions from universal_monitor
sys.path.insert(0, os.path.dirname(__file__))
from universal_monitor import (
    calculate_rsi, calculate_ema, calculate_macd, calculate_stochastic_rsi,
    calculate_adx, calculate_atr, calculate_bollinger_bands, calculate_obv,
    calculate_vwap
)

load_dotenv()

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
BOLD = '\033[1m'
RESET = '\033[0m'

def calculate_institutional_score(symbol, exchange):
    """Calculate full institutional score (0-100) for a coin"""
    try:
        # Fetch all timeframes
        ohlcv_15m = exchange.fetch_ohlcv(symbol, '15m', limit=100)
        ohlcv_1h = exchange.fetch_ohlcv(symbol, '1h', limit=100)
        ohlcv_4h = exchange.fetch_ohlcv(symbol, '4h', limit=50)
        
        df_15m = pd.DataFrame(ohlcv_15m, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df_1h = pd.DataFrame(ohlcv_1h, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df_4h = pd.DataFrame(ohlcv_4h, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Calculate all indicators
        price = df_15m['close'].iloc[-1]
        
        # RSI
        rsi_15m = calculate_rsi(df_15m['close']).iloc[-1]
        
        # EMAs for trend
        ema20_15m = calculate_ema(df_15m['close'], 20).iloc[-1]
        ema50_15m = calculate_ema(df_15m['close'], 50).iloc[-1]
        ema20_1h = calculate_ema(df_1h['close'], 20).iloc[-1]
        ema50_1h = calculate_ema(df_1h['close'], 50).iloc[-1]
        ema20_4h = calculate_ema(df_4h['close'], 20).iloc[-1]
        ema50_4h = calculate_ema(df_4h['close'], 50).iloc[-1]
        
        # MACD
        macd_line, signal_line, hist = calculate_macd(df_15m['close'])
        macd_hist = hist.iloc[-1]
        
        # Stochastic RSI
        stoch_k, stoch_d = calculate_stochastic_rsi(df_15m['close'])
        stoch_k_val = stoch_k.iloc[-1]
        
        # ADX
        adx, plus_di, minus_di = calculate_adx(df_15m)
        adx_val = adx.iloc[-1]
        
        # Volume
        vol_avg = df_15m['volume'].rolling(window=20).mean().iloc[-1]
        vol_current = df_15m['volume'].iloc[-1]
        vol_ratio = vol_current / vol_avg if vol_avg > 0 else 1
        
        # OBV
        obv = calculate_obv(df_15m)
        obv_slope = (obv.iloc[-1] - obv.iloc[-5]) / obv.iloc[-5] if obv.iloc[-5] != 0 else 0
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(df_15m['close'])
        bb_upper_val = bb_upper.iloc[-1]
        bb_lower_val = bb_lower.iloc[-1]
        
        # VWAP
        vwap = calculate_vwap(df_15m)
        vwap_val = vwap.iloc[-1]
        
        # SCORING SYSTEM
        score = 0
        breakdown = []
        
        # 1. TREND ALIGNMENT (30 pts)
        trend_4h = 'UP' if ema20_4h > ema50_4h else 'DOWN'
        trend_1h = 'UP' if ema20_1h > ema50_1h else 'DOWN'
        trend_15m = 'UP' if ema20_15m > ema50_15m else 'DOWN'
        
        if trend_4h == 'UP':
            score += 12
            breakdown.append("✅ 4H UP (+12)")
        else:
            breakdown.append("❌ 4H DOWN (0)")
            
        if trend_1h == 'UP':
            score += 10
            breakdown.append("✅ 1H UP (+10)")
        else:
            breakdown.append("❌ 1H DOWN (0)")
            
        if trend_15m == 'UP':
            score += 8
            breakdown.append("✅ 15M UP (+8)")
        else:
            breakdown.append("❌ 15M DOWN (0)")
        
        # 2. MOMENTUM (25 pts)
        if 50 < rsi_15m < 70:
            score += 8
            breakdown.append(f"✅ RSI bullish ({rsi_15m:.0f}) (+8)")
        elif 30 < rsi_15m <= 50:
            score += 5
            breakdown.append(f"⚠️  RSI neutral ({rsi_15m:.0f}) (+5)")
        else:
            breakdown.append(f"❌ RSI extreme ({rsi_15m:.0f}) (0)")
        
        if macd_hist > 0:
            score += 9
            breakdown.append("✅ MACD+ (+9)")
        else:
            breakdown.append("❌ MACD- (0)")
        
        if 20 < stoch_k_val < 80:
            score += 8
            breakdown.append("✅ Stoch OK (+8)")
        else:
            breakdown.append("⚠️  Stoch extreme (0)")
        
        # 3. VOLUME (20 pts)
        if vol_ratio > 1.5:
            score += 12
            breakdown.append(f"✅ Vol spike {vol_ratio:.1f}x (+12)")
        elif vol_ratio > 1.0:
            score += 8
            breakdown.append(f"✅ Vol above avg {vol_ratio:.1f}x (+8)")
        else:
            breakdown.append(f"⚠️  Vol low {vol_ratio:.1f}x (0)")
        
        if obv_slope > 0:
            score += 8
            breakdown.append("✅ OBV up (+8)")
        else:
            breakdown.append("❌ OBV down (0)")
        
        # 4. VOLATILITY (15 pts)
        if adx_val > 25:
            score += 8
            breakdown.append(f"✅ ADX strong {adx_val:.0f} (+8)")
        elif adx_val > 20:
            score += 4
            breakdown.append(f"⚠️  ADX moderate {adx_val:.0f} (+4)")
        else:
            breakdown.append(f"❌ ADX weak {adx_val:.0f} (0)")
        
        bb_position = (price - bb_lower_val) / (bb_upper_val - bb_lower_val)
        if 0.3 < bb_position < 0.7:
            score += 7
            breakdown.append("✅ BB mid (+7)")
        else:
            breakdown.append("⚠️  BB extreme (0)")
        
        # 5. LEVELS (10 pts)
        if price > vwap_val:
            score += 10
            breakdown.append("✅ Above VWAP (+10)")
        else:
            breakdown.append("❌ Below VWAP (0)")
        
        return {
            'score': score,
            'breakdown': breakdown,
            'trend_4h': trend_4h,
            'trend_1h': trend_1h,
            'trend_15m': trend_15m,
            'rsi': rsi_15m,
            'adx': adx_val,
            'macd_hist': macd_hist,
            'vol_ratio': vol_ratio,
            'price': price
        }
        
    except Exception as e:
        print(f"\nError processing coin: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print(f"{BOLD}{BLUE}{'='*80}{RESET}")
    print(f"{BOLD}{BLUE}{'INSTITUTIONAL-GRADE OPPORTUNITY SCANNER':^80}{RESET}")
    print(f"{BOLD}{BLUE}{'='*80}{RESET}\n")
    
    # Initialize exchange
    exchange = ccxt.kucoin({
        'enableRateLimit': True,
        'options': {'defaultType': 'future'}
    })
    
    # Coin list - KuCoin futures format
    coins = [
        'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT',
        'BNB/USDT', 'ADA/USDT', 'DOGE/USDT', 'MATIC/USDT',
        'DOT/USDT', 'AVAX/USDT', 'LINK/USDT', 'UNI/USDT',
        'ATOM/USDT', 'LTC/USDT', 'APT/USDT', 'ARB/USDT',
        'OP/USDT', 'TIA/USDT', 'SUI/USDT', 'SEI/USDT'
    ]
    
    print(f"{CYAN}Scanning {len(coins)} coins with institutional indicators...{RESET}\n")
    
    results = []
    for idx, coin in enumerate(coins, 1):
        coin_name = coin.split('/')[0]
        print(f"  [{idx:2}/{len(coins)}] Analyzing {coin_name}...", end='\r')
        
        result = calculate_institutional_score(coin, exchange)
        if result:
            results.append({
                'coin': coin_name,
                'symbol': coin,
                **result
            })
        else:
            print(f"  [{idx:2}/{len(coins)}] {coin_name} - ERROR          ", end='\r')
    
    print(" " * 80, end='\r')  # Clear progress line
    
    print(f"\n{GREEN}✓ Analysis complete{RESET}\n")
    
    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"{CYAN}Found {len(results)} coins with data{RESET}\n")
    
    # Display results
    print(f"{BOLD}{'='*75}{RESET}")
    print(f"{BOLD}{'RANK':<6} {'COIN':<8} {'SCORE':<10} {'TRENDS':<12} {'ADX':<7} {'SIGNAL'}{RESET}")
    print(f"{BOLD}{'='*75}{RESET}")
    
    for idx, r in enumerate(results, 1):
        # Score color
        if r['score'] >= 70:
            score_color = f"{GREEN}{BOLD}"
            signal = "🟢 STRONG BUY"
        elif r['score'] >= 50:
            score_color = YELLOW
            signal = "⚠️  NEUTRAL"
        else:
            score_color = RED
            signal = "🔴 WEAK"
        
        # Trend alignment
        trends = f"{r['trend_4h'][0]}{r['trend_1h'][0]}{r['trend_15m'][0]}"
        
        print(f"{idx:<6} {r['coin']:<8} {score_color}{r['score']:>3}/100{RESET}    "
              f"{trends:<12} {r['adx']:>4.0f}    {signal}")
    
    print(f"{BOLD}{'='*75}{RESET}\n")
    
    # Show top opportunities
    top_opportunities = [r for r in results if r['score'] >= 70]
    
    if top_opportunities:
        print(f"{GREEN}{BOLD}🎯 STRONG BUY SIGNALS (Score ≥70):{RESET}")
        for r in top_opportunities:
            print(f"\n{BOLD}{r['coin']}{RESET} - Score: {GREEN}{BOLD}{r['score']}/100{RESET}")
            print(f"  Trends: 4H {r['trend_4h']} | 1H {r['trend_1h']} | 15M {r['trend_15m']}")
            print(f"  ADX: {r['adx']:.1f} | RSI: {r['rsi']:.1f} | MACD: {r['macd_hist']:+.2f}")
            print(f"  Price: ${r['price']:.4f} | Vol: {r['vol_ratio']:.1f}x")
            print(f"\n  Score Breakdown:")
            for detail in r['breakdown'][:8]:
                print(f"    {detail}")
    else:
        print(f"{YELLOW}⚠️  NO STRONG SIGNALS - Market conditions not favorable{RESET}")
        print(f"{YELLOW}No coins scored ≥70. Best available:{RESET}\n")
        
        for r in results[:3]:
            print(f"{r['coin']}: {r['score']}/100 - {r['trend_4h']}{r['trend_1h']}{r['trend_15m']} trends")
    
    print(f"\n{CYAN}Use: python universal_monitor.py{RESET}")
    print(f"{CYAN}Then select 'n' for no position, 'y' for analysis, and choose your coin{RESET}\n")

if __name__ == "__main__":
    main()
