#!/usr/bin/env python3
"""
Live Dashboard - Real-time Position Monitor
Run this while position is open for live updates every 5 seconds
"""

import ccxt
import pandas as pd
from datetime import datetime
import os
import time
import sys
from dotenv import load_dotenv

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

# Add parent directory for core imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from core.indicators import calculate_rsi, calculate_ema, calculate_macd

load_dotenv()

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
BOLD = '\033[1m'
RESET = '\033[0m'

def display_live_dashboard(exchange):
    """Live position monitoring with 5-second updates"""
    
    print("\n🚀 Starting Live Dashboard...")
    print("Press Ctrl+C to exit\n")
    time.sleep(2)
    
    while True:
        try:
            os.system('clear')
            
            # Fetch positions
            positions = exchange.fetch_positions()
            active_positions = [p for p in positions if float(p.get('contracts', 0)) != 0]
            
            if not active_positions:
                print("=" * 70)
                print(f"{'LIVE POSITION MONITOR':^70}")
                print("=" * 70)
                print(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"\n{YELLOW}No active positions{RESET}")
                print("\nPress Ctrl+C to exit")
                time.sleep(5)
                continue
            
            # Display header
            print("=" * 70)
            print(f"{'LIVE POSITION MONITOR':^70}")
            print("=" * 70)
            print(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            for pos in active_positions:
                symbol = pos.get('symbol', 'N/A')
                side = (pos.get('side') or 'N/A').upper()
                contracts = abs(float(pos.get('contracts') or 0))
                entry = float(pos.get('entryPrice') or 0)
                current = float(pos.get('markPrice') or 0)
                leverage = float(pos.get('leverage') or 0)
                pnl = float(pos.get('unrealizedPnl') or 0)
                margin = float(pos.get('initialMargin') or 0)
                liq_price = float(pos.get('liquidationPrice') or 0)
                
                # Calculate P&L percentage
                if margin > 0:
                    pnl_pct = (pnl / margin) * 100
                else:
                    pnl_pct = 0
                
                # Fetch 15m data for quick indicators
                try:
                    ohlcv = exchange.fetch_ohlcv(symbol, '15m', limit=100)
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    
                    rsi = calculate_rsi(df['close'], period=14).iloc[-1]
                    ema20 = calculate_ema(df['close'], period=20).iloc[-1]
                    macd_line, signal_line, histogram = calculate_macd(df['close'])
                    macd_current = histogram.iloc[-1]
                    
                    # Price vs EMA
                    ema_diff_pct = ((current - ema20) / ema20) * 100
                    
                except Exception as e:
                    rsi = 0
                    ema20 = 0
                    macd_current = 0
                    ema_diff_pct = 0
                
                # Color based on P&L
                pnl_color = GREEN if pnl > 0 else RED
                
                # Display position info
                print(f"{BOLD}{'═' * 70}{RESET}")
                print(f"{BOLD}{CYAN}{symbol}{RESET}")
                print(f"{'─' * 70}")
                print(f"Position:      {side} {leverage}x")
                print(f"Contracts:     {contracts}")
                print(f"Margin:        ${margin:.2f}")
                print(f"Entry:         ${entry:.4f}")
                print(f"Current:       ${current:.4f}")
                print(f"{pnl_color}P&L:           ${pnl:+.2f} ({pnl_pct:+.2f}% ROE){RESET}")
                print(f"Liquidation:   ${liq_price:.4f}")
                print()
                
                # Indicators
                print(f"{BOLD}INDICATORS (15m){RESET}")
                print(f"RSI(14):       {rsi:.1f}")
                print(f"EMA(20):       ${ema20:.4f} ({ema_diff_pct:+.2f}%)")
                print(f"MACD Hist:     {macd_current:+.4f}")
                print()
                
                # Warnings & Suggestions
                print(f"{BOLD}ALERTS{RESET}")
                
                if side == 'LONG':
                    if current < ema20:
                        print(f"{RED}⚠️  Price below EMA20 - consider partial exit{RESET}")
                    if rsi > 70:
                        print(f"{YELLOW}📊 RSI Overbought ({rsi:.1f}) - watch for reversal{RESET}")
                    if macd_current < 0:
                        print(f"{YELLOW}📉 MACD Histogram negative - momentum weakening{RESET}")
                    
                    # Distance to liquidation
                    liq_distance = ((current - liq_price) / current) * 100
                    if liq_distance < 5:
                        print(f"{RED}🚨 CRITICAL: Only {liq_distance:.1f}% from liquidation!{RESET}")
                    elif liq_distance < 10:
                        print(f"{YELLOW}⚠️  WARNING: {liq_distance:.1f}% from liquidation{RESET}")
                
                elif side == 'SHORT':
                    if current > ema20:
                        print(f"{RED}⚠️  Price above EMA20 - consider partial exit{RESET}")
                    if rsi < 30:
                        print(f"{YELLOW}📊 RSI Oversold ({rsi:.1f}) - watch for reversal{RESET}")
                    if macd_current > 0:
                        print(f"{YELLOW}📈 MACD Histogram positive - momentum shifting{RESET}")
                    
                    # Distance to liquidation
                    liq_distance = ((liq_price - current) / current) * 100
                    if liq_distance < 5:
                        print(f"{RED}🚨 CRITICAL: Only {liq_distance:.1f}% from liquidation!{RESET}")
                    elif liq_distance < 10:
                        print(f"{YELLOW}⚠️  WARNING: {liq_distance:.1f}% from liquidation{RESET}")
                
                # General indicators
                if abs(ema_diff_pct) > 2:
                    print(f"{CYAN}📍 Price {abs(ema_diff_pct):.1f}% from EMA20{RESET}")
                
                print(f"{BOLD}{'═' * 70}{RESET}\n")
            
            print(f"Last update: {datetime.now().strftime('%H:%M:%S')}")
            print("Press Ctrl+C to exit")
            
            # Update every 5 seconds
            time.sleep(5)
            
        except KeyboardInterrupt:
            print(f"\n\n{GREEN}Dashboard stopped by user{RESET}\n")
            break
        except Exception as e:
            print(f"\n{RED}Error: {e}{RESET}")
            print("Retrying in 10 seconds...")
            time.sleep(10)

def main():
    # Initialize exchange
    exchange = ccxt.kucoinfutures({
        'apiKey': os.getenv('KUCOIN_API_KEY'),
        'secret': os.getenv('KUCOIN_API_SECRET'),
        'password': os.getenv('KUCOIN_API_PASSPHRASE'),
        'enableRateLimit': True,
        'options': {
            'defaultType': 'swap',
        }
    })
    
    display_live_dashboard(exchange)

if __name__ == '__main__':
    main()
