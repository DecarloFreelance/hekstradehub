#!/usr/bin/env python3
"""Quick TA and social analysis for current position"""
import ccxt
import pandas as pd
from dotenv import load_dotenv
import os
import sys

# RAM Protection
sys.path.insert(0, '/home/hektic/saddynhektic workspace')
try:
    from Tools.resource_manager import check_ram_before_processing
    check_ram_before_processing(min_free_gb=1.5)
except ImportError:
    print("⚠️  Warning: RAM protection not available")
except MemoryError as e:
    print(f"❌ Insufficient RAM: {e}")
    exit(1)

sys.path.insert(0, os.path.dirname(__file__))
from core.indicators import (
    calculate_ema, calculate_macd, calculate_rsi,
    calculate_stochastic_rsi, calculate_adx, calculate_atr,
    calculate_bollinger_bands, calculate_obv
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

def analyze_position():
    # Initialize exchange
    exchange = ccxt.kucoinfutures({
        'apiKey': os.getenv('KUCOIN_API_KEY'),
        'secret': os.getenv('KUCOIN_API_SECRET'),
        'password': os.getenv('KUCOIN_API_PASSPHRASE'),
        'enableRateLimit': True,
    })
    
    try:
        # Get active positions
        positions = exchange.fetch_positions()
        active_positions = [p for p in positions if float(p.get('contracts', 0)) != 0]
        
        if not active_positions:
            print("\n✓ No open positions found.")
            return
        
        for pos in active_positions:
            symbol = pos.get('symbol', 'N/A')
            side = (pos.get('side') or 'N/A').upper()
            leverage = float(pos.get('leverage') or 0)
            entry = float(pos.get('entryPrice') or 0)
            current = float(pos.get('markPrice') or 0)
            pnl = float(pos.get('unrealizedPnl') or 0)
            pnl_pct = float(pos.get('percentage') or 0)
            
            print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
            print(f"{BOLD}{BLUE}{f'{symbol} - TECHNICAL & SOCIAL ANALYSIS':^70}{RESET}")
            print(f"{BOLD}{BLUE}{'='*70}{RESET}\n")
            
            # Position info
            pnl_color = GREEN if pnl > 0 else RED
            print(f"{BOLD}Position:{RESET} {side} {leverage}x | Entry: ${entry:.4f} | Mark: ${current:.4f}")
            print(f"{BOLD}P&L:{RESET} {pnl_color}${pnl:.2f} ({pnl_pct:.2f}%){RESET}\n")
            
            # Fetch OHLCV data for multiple timeframes
            print(f"{CYAN}Fetching market data...{RESET}")
            
            ohlcv_15m = exchange.fetch_ohlcv(symbol, '15m', limit=100)
            ohlcv_1h = exchange.fetch_ohlcv(symbol, '1h', limit=100)
            ohlcv_4h = exchange.fetch_ohlcv(symbol, '4h', limit=50)
            
            df_15m = pd.DataFrame(ohlcv_15m, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df_1h = pd.DataFrame(ohlcv_1h, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df_4h = pd.DataFrame(ohlcv_4h, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Calculate indicators
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
            macd_line_val = macd_line.iloc[-1]
            
            stoch_k, stoch_d = calculate_stochastic_rsi(df_15m['close'])
            stoch_k_val = stoch_k.iloc[-1]
            stoch_d_val = stoch_d.iloc[-1]
            
            adx = calculate_adx(df_15m).iloc[-1]
            atr = calculate_atr(df_15m).iloc[-1]
            
            bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(df_15m['close'])
            bb_position = (current - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1]) * 100
            
            obv = calculate_obv(df_15m)
            obv_slope = obv.diff().iloc[-1]
            
            # Volume analysis
            vol_avg = df_15m['volume'].rolling(window=20).mean().iloc[-1]
            vol_current = df_15m['volume'].iloc[-1]
            vol_ratio = vol_current / vol_avg if vol_avg > 0 else 1
            
            # Trend detection
            trend_4h = 'UP' if ema20_4h > ema50_4h else 'DOWN'
            trend_1h = 'UP' if ema20_1h > ema50_1h else 'DOWN'
            trend_15m = 'UP' if ema20_15m > ema50_15m else 'DOWN'
            
            # Display Technical Analysis
            print(f"\n{BOLD}═══ TECHNICAL ANALYSIS ═══{RESET}")
            
            # Trend
            print(f"\n{BOLD}Trend:{RESET}")
            trend_4h_color = GREEN if trend_4h == 'UP' else RED
            trend_1h_color = GREEN if trend_1h == 'UP' else RED
            trend_15m_color = GREEN if trend_15m == 'UP' else RED
            print(f"  4H:  {trend_4h_color}{trend_4h}{RESET}  (EMA20: ${ema20_4h:.5f}, EMA50: ${ema50_4h:.5f})")
            print(f"  1H:  {trend_1h_color}{trend_1h}{RESET}  (EMA20: ${ema20_1h:.5f}, EMA50: ${ema50_1h:.5f})")
            print(f"  15M: {trend_15m_color}{trend_15m}{RESET}  (EMA20: ${ema20_15m:.5f}, EMA50: ${ema50_15m:.5f})")
            
            # Momentum
            print(f"\n{BOLD}Momentum:{RESET}")
            rsi_color = GREEN if 40 < rsi_15m < 60 else YELLOW if 30 < rsi_15m < 70 else RED
            print(f"  RSI (15M): {rsi_color}{rsi_15m:.2f}{RESET}")
            print(f"  RSI (1H):  {rsi_1h:.2f}")
            
            macd_color = GREEN if macd_hist > 0 else RED
            print(f"  MACD Histogram: {macd_color}{macd_hist:.6f}{RESET}")
            print(f"  MACD Line: {macd_line_val:.6f}")
            
            stoch_color = GREEN if 20 < stoch_k_val < 80 else YELLOW
            print(f"  Stoch RSI K: {stoch_color}{stoch_k_val:.2f}{RESET}")
            print(f"  Stoch RSI D: {stoch_d_val:.2f}")
            
            # Volatility & Strength
            print(f"\n{BOLD}Volatility & Strength:{RESET}")
            adx_color = GREEN if adx > 25 else YELLOW if adx > 20 else RED
            print(f"  ADX: {adx_color}{adx:.2f}{RESET} {'(Strong Trend)' if adx > 25 else '(Weak Trend)' if adx < 20 else '(Moderate)'}")
            print(f"  ATR: ${atr:.6f}")
            
            # Bollinger Bands
            bb_color = GREEN if 30 < bb_position < 70 else YELLOW if 20 < bb_position < 80 else RED
            print(f"  BB Position: {bb_color}{bb_position:.1f}%{RESET}")
            print(f"    Upper: ${bb_upper.iloc[-1]:.5f}")
            print(f"    Mid:   ${bb_middle.iloc[-1]:.5f}")
            print(f"    Lower: ${bb_lower.iloc[-1]:.5f}")
            
            # Volume
            print(f"\n{BOLD}Volume:{RESET}")
            vol_color = GREEN if vol_ratio > 1.5 else YELLOW if vol_ratio > 1.0 else RED
            print(f"  Current/Average: {vol_color}{vol_ratio:.2f}x{RESET}")
            print(f"  OBV Slope: {GREEN if obv_slope > 0 else RED}{obv_slope:+.2f}{RESET}")
            
            # Calculate Signal Score
            score = 0
            
            # Trend (30 pts)
            if trend_4h == 'UP': score += 12
            if trend_1h == 'UP': score += 10
            if trend_15m == 'UP': score += 8
            
            # Momentum (25 pts)
            if 50 < rsi_15m < 70: score += 8
            elif 30 < rsi_15m <= 50: score += 5
            if macd_hist > 0: score += 9
            if 20 < stoch_k_val < 80: score += 4
            elif stoch_k_val < 20: score += 6  # Oversold can be bullish
            
            # Volume (20 pts)
            if vol_ratio > 1.5: score += 12
            elif vol_ratio > 1.0: score += 8
            if obv_slope > 0: score += 4
            
            # Volatility (15 pts)
            if adx > 25: score += 8
            elif adx > 20: score += 4
            if 30 < bb_position < 70: score += 3
            
            # Level (10 pts)
            if current > ema20_15m and current > ema50_15m: score += 10
            
            # Signal interpretation
            print(f"\n{BOLD}═══ SIGNAL SCORE ═══{RESET}")
            
            if side == 'LONG':
                if score >= 70:
                    signal = f"{GREEN}STRONG BULLISH - HOLD/ADD{RESET}"
                elif score >= 50:
                    signal = f"{YELLOW}WEAK BULLISH - MONITOR{RESET}"
                else:
                    signal = f"{RED}BEARISH - CONSIDER EXIT{RESET}"
            else:  # SHORT
                if score <= 30:
                    signal = f"{GREEN}STRONG BEARISH - HOLD/ADD{RESET}"
                elif score <= 50:
                    signal = f"{YELLOW}WEAK BEARISH - MONITOR{RESET}"
                else:
                    signal = f"{RED}BULLISH - CONSIDER EXIT{RESET}"
            
            score_color = GREEN if score >= 70 or score <= 30 else YELLOW if 50 <= score < 70 or 30 < score <= 50 else RED
            print(f"\n  Score: {score_color}{BOLD}{score}/100{RESET}")
            print(f"  Signal: {signal}")
            
            # Social/Sentiment (placeholder - would need API integration)
            print(f"\n{BOLD}═══ SOCIAL & SENTIMENT ═══{RESET}")
            print(f"  {YELLOW}Note: Social sentiment requires additional API integration{RESET}")
            print(f"  Suggested sources:")
            print(f"    • Twitter/X trending")
            print(f"    • CoinGecko sentiment")
            print(f"    • LunarCrush social metrics")
            print(f"    • Reddit activity")
            
            # Risk Management
            print(f"\n{BOLD}═══ RISK MANAGEMENT ═══{RESET}")
            risk_pct = abs((current - entry) / entry) * 100
            print(f"  Current Risk: {risk_pct:.2f}%")
            
            stop_loss = entry * 0.97 if side == 'LONG' else entry * 1.03
            tp1 = entry * 1.03 if side == 'LONG' else entry * 0.97
            tp2 = entry * 1.05 if side == 'LONG' else entry * 0.95
            
            print(f"  Suggested Stop Loss: ${stop_loss:.5f} (3%)")
            print(f"  Take Profit 1: ${tp1:.5f} (3%)")
            print(f"  Take Profit 2: ${tp2:.5f} (5%)")
            
            print(f"\n{BOLD}{BLUE}{'='*70}{RESET}\n")
            
    except Exception as e:
        print(f"{RED}Error: {e}{RESET}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    analyze_position()
