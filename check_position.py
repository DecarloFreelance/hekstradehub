#!/usr/bin/env python3
"""Quick script to check current KuCoin futures positions"""
import ccxt
from dotenv import load_dotenv
import os
import sys
from datetime import datetime

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

load_dotenv()

def check_positions():
    # Initialize KuCoin Futures
    exchange = ccxt.kucoinfutures({
        'apiKey': os.getenv('KUCOIN_API_KEY'),
        'secret': os.getenv('KUCOIN_API_SECRET'),
        'password': os.getenv('KUCOIN_API_PASSPHRASE'),
        'enableRateLimit': True,
        'options': {
            'defaultType': 'swap',
        }
    })
    
    try:
        # Fetch all positions (force fresh data)
        positions = exchange.fetch_positions()
        
        # Also get account info for P&L
        account = exchange.fetch_balance()
        
        # Filter for active positions
        active_positions = [p for p in positions if float(p.get('contracts', 0)) != 0]
        
        if not active_positions:
            print("\n✓ No open positions found.")
            return
        
        print("\n╔═══════════════════════════════════════════════════════╗")
        print("║         KUCOIN FUTURES - PROFESSIONAL ADVISOR         ║")
        print("╚═══════════════════════════════════════════════════════╝\n")
        print(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        for pos in active_positions:
            symbol = pos.get('symbol', 'N/A')
            side = (pos.get('side') or 'N/A').upper()
            contracts = abs(float(pos.get('contracts') or 0))
            notional = abs(float(pos.get('notional') or 0))
            entry = float(pos.get('entryPrice') or 0)
            current = float(pos.get('markPrice') or 0)
            leverage = float(pos.get('leverage') or 0)
            pnl = float(pos.get('unrealizedPnl') or 0)
            margin = float(pos.get('initialMargin') or 0)
            liq = float(pos.get('liquidationPrice') or 0)
            
            # Calculate ROE percentage properly
            if margin > 0:
                pnl_pct = (pnl / margin) * 100
            else:
                pnl_pct = 0
            
            # Calculate price movement
            if entry > 0:
                price_change_pct = ((current - entry) / entry) * 100
            else:
                price_change_pct = 0
            
            # Color based on PnL
            color = '\033[92m' if pnl > 0 else '\033[91m'
            reset = '\033[0m'
            bold = '\033[1m'
            
            print(f"{bold}═══ {symbol} ═══{reset}")
            print(f"Position:     {side} {leverage}x")
            print(f"Contracts:    {contracts}")
            print(f"Notional:     ${notional:.2f}")
            print(f"Margin:       ${margin:.2f}")
            print(f"Entry:        ${entry:.4f}")
            print(f"Mark Price:   ${current:.4f}")
            print(f"Price Move:   {price_change_pct:+.2f}%")
            print(f"{color}Unrealized:   ${pnl:+.4f} ({pnl_pct:+.2f}% ROE){reset}")
            print(f"Liquidation:  ${liq:.4f}")
            print("-" * 55)
                
    except Exception as e:
        print(f"Error fetching positions: {e}")
        print("\nMake sure your .env file has:")
        print("  KUCOIN_API_KEY")
        print("  KUCOIN_API_SECRET")
        print("  KUCOIN_API_PASSPHRASE")

if __name__ == '__main__':
    check_positions()
