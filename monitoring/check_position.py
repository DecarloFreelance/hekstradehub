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

# Modern colors
PURPLE = '\033[95m'
BLUE = '\033[94m'
CYAN = '\033[96m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
ORANGE = '\033[38;5;208m'
LIME = '\033[38;5;154m'
TEAL = '\033[38;5;51m'
LAVENDER = '\033[38;5;183m'
BOLD = '\033[1m'
DIM = '\033[2m'
RESET = '\033[0m'

def check_api_credentials():
    """Check if API credentials are configured"""
    if not os.path.exists('.env'):
        print(f"\n{RED}{'─' * 70}{RESET}")
        print(f"{BOLD}{RED}  ❌ No .env file found!{RESET}")
        print(f"\n{YELLOW}  📋 To use trading features, configure your API credentials:{RESET}")
        print(f"{LIME}     1.{RESET} Copy .env.example to .env")
        print(f"{LIME}     2.{RESET} Add your KuCoin API credentials")
        print(f"{LIME}     3.{RESET} Or run: {BOLD}./setup.sh{RESET}")
        print(f"\n{RED}{'─' * 70}{RESET}\n")
        return False
    
    api_key = os.getenv('KUCOIN_API_KEY')
    api_secret = os.getenv('KUCOIN_API_SECRET')
    api_pass = os.getenv('KUCOIN_API_PASSPHRASE')
    
    if not api_key or not api_secret or not api_pass:
        print(f"\n{RED}{'─' * 70}{RESET}")
        print(f"{BOLD}{RED}  ❌ API credentials not configured in .env!{RESET}")
        print(f"\n{YELLOW}  📋 Add your KuCoin API credentials:{RESET}")
        print(f"{DIM}     KUCOIN_API_KEY=your_key{RESET}")
        print(f"{DIM}     KUCOIN_API_SECRET=your_secret{RESET}")
        print(f"{DIM}     KUCOIN_API_PASSPHRASE=your_passphrase{RESET}")
        print(f"\n{RED}{'─' * 70}{RESET}\n")
        return False
    
    return True

def check_positions():
    # Check credentials first
    if not check_api_credentials():
        return
    
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
            print(f"\n{TEAL}{'═' * 70}{RESET}")
            print(f"{BOLD}{GREEN}  ✓ No open positions found{RESET}")
            print(f"{TEAL}{'═' * 70}{RESET}\n")
            return
        
        # Header
        print(f"\n{TEAL}{'═' * 70}{RESET}")
        print(f"{BOLD}{LAVENDER}         📊 KUCOIN FUTURES - POSITION MONITOR 📊{RESET}")
        print(f"{TEAL}{'═' * 70}{RESET}")
        print(f"{DIM}Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}\n")
        
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
            
            # Color based on PnL and side
            pnl_color = GREEN if pnl > 0 else RED
            side_color = LIME if side == 'LONG' else ORANGE
            
            # Position card
            print(f"{PURPLE}╭{'─' * 68}╮{RESET}")
            print(f"{PURPLE}│{RESET} {BOLD}{side_color}{symbol}{RESET}{' ' * (66 - len(symbol))}│")
            print(f"{PURPLE}├{'─' * 68}┤{RESET}")
            
            print(f"{PURPLE}│{RESET}  {BOLD}Position:{RESET} {side_color}{side}{RESET} {YELLOW}{leverage}x{RESET}{' ' * (48 - len(side) - len(str(leverage)))}│")
            print(f"{PURPLE}│{RESET}  {BOLD}Contracts:{RESET} {CYAN}{contracts:.1f}{RESET}{' ' * (52 - len(f'{contracts:.1f}'))}│")
            print(f"{PURPLE}│{RESET}  {BOLD}Notional:{RESET} {CYAN}${notional:.2f}{RESET}{' ' * (53 - len(f'${notional:.2f}'))}│")
            print(f"{PURPLE}│{RESET}  {BOLD}Margin:{RESET} {CYAN}${margin:.2f}{RESET}{' ' * (56 - len(f'${margin:.2f}'))}│")
            print(f"{PURPLE}│{RESET}{' ' * 68}│")
            
            print(f"{PURPLE}│{RESET}  {BOLD}Entry Price:{RESET} {LAVENDER}${entry:.4f}{RESET}{' ' * (49 - len(f'${entry:.4f}'))}│")
            print(f"{PURPLE}│{RESET}  {BOLD}Mark Price:{RESET} {LAVENDER}${current:.4f}{RESET}{' ' * (50 - len(f'${current:.4f}'))}│")
            print(f"{PURPLE}│{RESET}  {BOLD}Price Move:{RESET} {pnl_color}{price_change_pct:+.2f}%{RESET}{' ' * (50 - len(f'{price_change_pct:+.2f}%'))}│")
            print(f"{PURPLE}│{RESET}{' ' * 68}│")
            
            print(f"{PURPLE}│{RESET}  {BOLD}Unrealized P&L:{RESET} {pnl_color}${pnl:+.4f} ({pnl_pct:+.2f}% ROE){RESET}{' ' * (34 - len(f'${pnl:+.4f} ({pnl_pct:+.2f}% ROE)'))}│")
            print(f"{PURPLE}│{RESET}  {BOLD}Liquidation:{RESET} {RED}${liq:.4f}{RESET}{' ' * (49 - len(f'${liq:.4f}'))}│")
            print(f"{PURPLE}╰{'─' * 68}╯{RESET}\n")
        
        # Summary footer
        total_pnl = sum(float(p.get('unrealizedPnl', 0)) for p in active_positions)
        total_margin = sum(float(p.get('initialMargin', 0)) for p in active_positions)
        total_pnl_pct = (total_pnl / total_margin * 100) if total_margin > 0 else 0
        summary_color = GREEN if total_pnl > 0 else RED
        
        print(f"{TEAL}{'─' * 70}{RESET}")
        print(f"{BOLD}Total Unrealized P&L:{RESET} {summary_color}${total_pnl:+.4f} ({total_pnl_pct:+.2f}%){RESET}")
        print(f"{TEAL}{'═' * 70}{RESET}\n")
                
    except Exception as e:
        print(f"Error fetching positions: {e}")
        print("\nMake sure your .env file has:")
        print("  KUCOIN_API_KEY")
        print("  KUCOIN_API_SECRET")
        print("  KUCOIN_API_PASSPHRASE")

if __name__ == '__main__':
    check_positions()
