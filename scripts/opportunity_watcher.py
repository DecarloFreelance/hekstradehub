#!/usr/bin/env python3
"""
Live Opportunity Watcher
Monitors market conditions and alerts when institutional-grade setups appear
"""
import os
import time
import ccxt
from dotenv import load_dotenv
from datetime import datetime
import sys

sys.path.insert(0, os.path.dirname(__file__))
from universal_monitor import get_market_data, calculate_signal_score

load_dotenv()

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
BOLD = '\033[1m'
RESET = '\033[0m'

def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')

def scan_market(exchange, coins):
    """Scan all coins and return scores"""
    results = []
    
    for coin in coins:
        try:
            market = get_market_data(exchange, coin)
            if not market:
                continue
            
            score, details = calculate_signal_score(market)
            
            # Also calculate short score
            short_score = 0
            if market['trend_4h'] == 'DOWN': short_score += 12
            if market['trend_1h'] == 'DOWN': short_score += 10
            if market['trend_15m'] == 'DOWN': short_score += 8
            if market['rsi_15m'] > 70: short_score += 8
            elif market['rsi_15m'] > 60: short_score += 5
            if market['macd_hist_15m'] < 0: short_score += 9
            if market['adx_15m'] > 25: short_score += 8
            elif market['adx_15m'] > 20: short_score += 4
            if market['price'] < market['vwap_15m']: short_score += 10
            if market['obv_slope'] < 0: short_score += 8
            if market['vol_ratio'] > 1.5: short_score += 12
            elif market['vol_ratio'] > 1.0: short_score += 8
            
            results.append({
                'coin': coin.split('/')[0],
                'symbol': coin,
                'long_score': score,
                'short_score': short_score,
                'trend_4h': market['trend_4h'],
                'trend_1h': market['trend_1h'],
                'trend_15m': market['trend_15m'],
                'rsi': market['rsi_15m'],
                'adx': market['adx_15m'],
                'price': market['price'],
                'vol_ratio': market['vol_ratio'],
                'change_24h': market['change_24h']
            })
        except:
            continue
    
    return results

def display_dashboard(results, last_alert_time):
    """Display live dashboard with clean professional layout"""
    clear_screen()
    
    print(f"{BOLD}{CYAN}═══════════════════════════════════════════════════════════{RESET}")
    print(f"{BOLD}{CYAN}        LIVE OPPORTUNITY SCANNER - TOP 5 RANKED{RESET}")
    print(f"{BOLD}{CYAN}═══════════════════════════════════════════════════════════{RESET}")
    
    # Sort by best overall score (long or short)
    sorted_results = sorted(results, key=lambda x: max(x['long_score'], x['short_score']), reverse=True)
    top_5 = sorted_results[:5]
    
    # Check if any meet threshold
    trade_ready = any(r['long_score'] >= 70 or r['short_score'] >= 70 for r in top_5)
    
    if trade_ready:
        print(f"\n{GREEN}{BOLD}  🔔 TRADEABLE SETUPS DETECTED{RESET}")
    else:
        print(f"\n{YELLOW}  ⏳ Waiting for score ≥70...{RESET}")
    
    print()
    # Clean table with better spacing
    print(f"{BOLD}  #  COIN    L    S   TRENDS  ADX   VOL  {RESET}")
    print(f"  ─────────────────────────────────────────")
    
    # Display top 5
    for idx, r in enumerate(top_5, 1):
        trends = f"{r['trend_4h'][0]}{r['trend_1h'][0]}{r['trend_15m'][0]}"
        
        # Long score
        if r['long_score'] >= 70:
            long_str = f"{GREEN}{BOLD}{r['long_score']:>2}{RESET}"
        elif r['long_score'] >= 50:
            long_str = f"{YELLOW}{r['long_score']:>2}{RESET}"
        else:
            long_str = f"{r['long_score']:>2}"
        
        # Short score
        if r['short_score'] >= 70:
            short_str = f"{RED}{BOLD}{r['short_score']:>2}{RESET}"
        elif r['short_score'] >= 50:
            short_str = f"{YELLOW}{r['short_score']:>2}{RESET}"
        else:
            short_str = f"{r['short_score']:>2}"
        
        # ADX coloring
        if r['adx'] > 25:
            adx_str = f"{GREEN}{r['adx']:>3.0f}{RESET}"
        elif r['adx'] > 20:
            adx_str = f"{YELLOW}{r['adx']:>3.0f}{RESET}"
        else:
            adx_str = f"{RED}{r['adx']:>3.0f}{RESET}"
        
        # Volume coloring
        if r['vol_ratio'] > 1.5:
            vol_str = f"{GREEN}{r['vol_ratio']:>3.1f}{RESET}"
        elif r['vol_ratio'] > 1.0:
            vol_str = f"{YELLOW}{r['vol_ratio']:>3.1f}{RESET}"
        else:
            vol_str = f"{RED}{r['vol_ratio']:>3.1f}{RESET}"
        
        print(f"  {idx}  {r['coin']:<6} {long_str}   {short_str}   {trends:<6}  {adx_str}   {vol_str}x")
    
    print(f"  ─────────────────────────────────────────")
    
    # Market health summary
    avg_long = sum(r['long_score'] for r in results) / len(results) if results else 0
    avg_short = sum(r['short_score'] for r in results) / len(results) if results else 0
    avg_adx = sum(r['adx'] for r in results) / len(results) if results else 0
    avg_vol = sum(r['vol_ratio'] for r in results) / len(results) if results else 0
    
    health = f"{'✓' if avg_adx > 20 else '✗'}"
    vol_check = f"{'✓' if avg_vol > 1.0 else '✗'}"
    
    print(f"\n  Market: L:{avg_long:.0f} S:{avg_short:.0f} | ADX:{avg_adx:.0f}{health} | Vol:{avg_vol:.1f}x{vol_check}")
    
    # Trading recommendation
    best_long = max(results, key=lambda x: x['long_score'])
    best_short = max(results, key=lambda x: x['short_score'])
    
    if best_long['long_score'] >= 70:
        print(f"\n  {GREEN}→ LONG {best_long['coin']} ({best_long['long_score']}){RESET}")
    elif best_short['short_score'] >= 70:
        print(f"\n  {RED}→ SHORT {best_short['coin']} ({best_short['short_score']}){RESET}")
    else:
        print(f"\n  {YELLOW}→ HOLD - Best: {best_long['coin']}({best_long['long_score']}) {best_short['coin']}({best_short['short_score']}){RESET}")
    
    print(f"\n  {CYAN}{datetime.now().strftime('%H:%M:%S')} | {len(results)} coins | Next scan in: {RESET}", end='')
    print()

def countdown_timer(seconds):
    """Display countdown timer"""
    for remaining in range(seconds, 0, -1):
        print(f"\r  {CYAN}Next scan in: {remaining}s  {RESET}", end='', flush=True)
        time.sleep(1)
    print(f"\r  {CYAN}Scanning...        {RESET}", end='', flush=True)

def main():
    print(f"{BOLD}{CYAN}Starting Live Opportunity Watcher...{RESET}\n")
    
    # Initialize exchange
    exchange = ccxt.kucoin({
        'enableRateLimit': True,
        'options': {'defaultType': 'future'}
    })
    
    # Coin list
    coins = [
        'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'BNB/USDT',
        'ADA/USDT', 'DOGE/USDT', 'DOT/USDT', 'AVAX/USDT', 'LINK/USDT',
        'UNI/USDT', 'ATOM/USDT', 'LTC/USDT', 'APT/USDT', 'ARB/USDT',
        'OP/USDT', 'TIA/USDT', 'SUI/USDT', 'SEI/USDT'
    ]
    
    last_alert_time = None
    previous_opportunities = set()
    
    try:
        while True:
            print(f"{CYAN}Scanning market...{RESET}")
            results = scan_market(exchange, coins)
            
            # Check for new opportunities
            current_long_opps = {r['coin'] for r in results if r['long_score'] >= 70}
            current_short_opps = {r['coin'] for r in results if r['short_score'] >= 70}
            current_opportunities = current_long_opps | current_short_opps
            
            # Alert on new opportunities
            new_opportunities = current_opportunities - previous_opportunities
            if new_opportunities:
                last_alert_time = datetime.now().strftime('%H:%M:%S')
                # System beep (if terminal supports it)
                print('\a')
            
            previous_opportunities = current_opportunities
            
            # Display dashboard
            display_dashboard(results, last_alert_time)
            
            # Countdown to next scan
            countdown_timer(60)
            
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Opportunity Watcher stopped{RESET}")
        print(f"{CYAN}Final Summary:{RESET}")
        if results:
            best_long = max(results, key=lambda x: x['long_score'])
            best_short = max(results, key=lambda x: x['short_score'])
            print(f"  Best LONG:  {best_long['coin']} ({best_long['long_score']}/100)")
            print(f"  Best SHORT: {best_short['coin']} ({best_short['short_score']}/100)")
        print(f"\n{CYAN}Use: python universal_monitor.py{RESET}")
        print(f"{CYAN}To analyze specific coins in detail{RESET}\n")

if __name__ == "__main__":
    main()
