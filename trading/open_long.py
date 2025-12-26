#!/usr/bin/env python3
"""Execute LONG position with auto-trailing stop"""
import ccxt
from dotenv import load_dotenv
import os
import sys
import subprocess
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

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BOLD = '\033[1m'
RESET = '\033[0m'

def open_long_position(symbol, leverage=10, risk_percent=5):
    """Open LONG position with proper risk management"""
    
    exchange = ccxt.kucoinfutures({
        'apiKey': os.getenv('KUCOIN_API_KEY'),
        'secret': os.getenv('KUCOIN_API_SECRET'),
        'password': os.getenv('KUCOIN_API_PASSPHRASE'),
        'enableRateLimit': True,
    })
    
    try:
        # Get account balance
        balance = exchange.fetch_balance()
        available = float(balance['USDT']['free'])
        
        print(f"\n{BOLD}{'='*60}{RESET}")
        print(f"{BOLD}OPENING LONG POSITION ON {symbol}{RESET}")
        print(f"{'='*60}\n")
        
        print(f"Available Balance: ${available:.2f} USDT")
        
        if available < 1:
            print(f"{RED}Insufficient balance for trade!{RESET}")
            return False
        
        # Get current price and market info
        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        
        # Load market to get contract size
        market = exchange.market(symbol)
        contract_size = market.get('contractSize', 1)
        
        print(f"Current Price: ${current_price:.6f}")
        print(f"Contract Size: {contract_size}")
        print(f"Leverage: {leverage}x")
        
        # Calculate position size using contract size
        # Use 95% of available balance to leave room for fees
        margin = available * 0.95
        notional = margin * leverage
        
        # Calculate contracts accounting for contract size
        contracts = int(notional / (current_price * contract_size))
        
        # Recalculate actual values with integer contracts
        actual_notional = contracts * current_price * contract_size
        actual_margin = actual_notional / leverage
        
        print(f"\nPosition Details:")
        print(f"  Margin: ${actual_margin:.2f}")
        print(f"  Notional Value: ${actual_notional:.2f}")
        print(f"  Contracts: {contracts} (each = {contract_size} {symbol.split('/')[0]})")
        print(f"  Total Exposure: {contracts * contract_size:.2f} {symbol.split('/')[0]}")
        
        # Calculate stop loss and take profits
        stop_loss_price = current_price * (1 - risk_percent/100)
        tp1_price = current_price * (1 + risk_percent/100)
        tp2_price = current_price * (1 + risk_percent*2/100)
        
        print(f"\nRisk Management:")
        print(f"  Entry: ${current_price:.6f}")
        print(f"  Stop Loss (-{risk_percent}%): ${stop_loss_price:.6f}")
        print(f"  TP1 (+{risk_percent}%): ${tp1_price:.6f}")
        print(f"  TP2 (+{risk_percent*2}%): ${tp2_price:.6f}")
        
        # Confirm trade
        print(f"\n{YELLOW}Execute LONG trade? (yes/no): {RESET}", end='')
        confirmation = input().strip().lower()
        
        if confirmation != 'yes':
            print(f"{YELLOW}Trade cancelled.{RESET}")
            return False
        
        # Set leverage with cross margin mode (skip if already set)
        try:
            print(f"\n{BOLD}Setting leverage to {leverage}x...{RESET}")
            exchange.set_leverage(leverage, symbol, params={'marginMode': 'cross'})
        except Exception as lev_error:
            if '330006' in str(lev_error):
                print(f"{YELLOW}  (Already in isolated mode, continuing...){RESET}")
            else:
                print(f"{YELLOW}  Warning: {lev_error}{RESET}")
                print(f"  Continuing with current leverage settings...")
        
        # Place LONG market order (BUY) with leverage in params
        print(f"{BOLD}Placing LONG market order...{RESET}")
        
        order = exchange.create_market_buy_order(
            symbol=symbol,
            amount=contracts,
            params={'leverage': leverage}  # Pass leverage in params like SHORT does
        )
        
        print(f"\n{GREEN}✓ LONG Position Opened!{RESET}")
        print(f"Order ID: {order['id']}")
        print(f"Filled: {order.get('filled', contracts)} contracts")
        
        # Get actual fill price
        fill_price = order.get('average') or current_price
        
        # Place stop loss order
        print(f"\n{BOLD}Setting stop loss...{RESET}")
        try:
            sl_order = exchange.create_order(
                symbol=symbol,
                type='stop',
                side='sell',  # SELL to close LONG
                amount=contracts,
                price=None,
                params={
                    'stopPrice': stop_loss_price,
                    'stop': 'down',
                    'closeOrder': True,
                    'leverage': leverage
                }
            )
            print(f"{GREEN}✓ Stop loss set at ${stop_loss_price:.6f}{RESET}")
        except Exception as e:
            print(f"{YELLOW}⚠ Could not set stop loss automatically: {e}{RESET}")
            print(f"{YELLOW}⚠ MANUALLY set stop loss at ${stop_loss_price:.6f}{RESET}")
        
        # Place take profit order
        print(f"\n{BOLD}Setting take profit...{RESET}")
        try:
            tp_order = exchange.create_order(
                symbol=symbol,
                type='limit',
                side='sell',  # SELL to close LONG
                amount=contracts,
                price=tp1_price,
                params={
                    'stopPrice': tp1_price,
                    'stop': 'up',
                    'closeOrder': True,
                    'leverage': leverage
                }
            )
            print(f"{GREEN}✓ Take profit set at ${tp1_price:.6f}{RESET}")
        except Exception as e:
            print(f"{YELLOW}⚠ Could not set TP automatically: {e}{RESET}")
            print(f"{YELLOW}⚠ MANUALLY set take profit at ${tp1_price:.6f}{RESET}")
        
        # Start auto-trailing manager as backup/enhancement
        print(f"\n{BOLD}Starting auto-trailing stop manager...{RESET}")
        
        trailing_cmd = [
            'python3',
            'auto_trailing_manager.py',
            symbol,
            'LONG',
            str(fill_price),
            str(tp1_price),
            str(tp2_price)
        ]
        
        # Start in background with logging
        timestamp = int(datetime.now().timestamp())
        log_file = f"auto_trailing_{symbol.replace('/', '_')}_{timestamp}.log"
        
        with open(log_file, 'w') as f:
            subprocess.Popen(
                trailing_cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                start_new_session=True
            )
        
        print(f"{GREEN}✓ Auto-trailing manager started{RESET}")
        print(f"  Log file: {log_file}")
        
        print(f"\n{BOLD}{GREEN}{'='*60}{RESET}")
        print(f"{BOLD}{GREEN}LONG POSITION ACTIVE ON {symbol.split('/')[0]}{RESET}")
        print(f"{BOLD}{GREEN}{'='*60}{RESET}\n")
        
        print(f"{YELLOW}Position Summary:{RESET}")
        print(f"  Entry: ${fill_price:.6f} | Contracts: {contracts} | Leverage: {leverage}x")
        print(f"  Stop Loss: ${stop_loss_price:.6f} (-{risk_percent}%)")
        print(f"  TP1: ${tp1_price:.6f} (+{risk_percent}%)")
        print(f"  TP2: ${tp2_price:.6f} (+{risk_percent*2}%)")
        print(f"\n{YELLOW}⚠️  Auto-trailing will activate after TP1!{RESET}")
        
        return True
        
    except Exception as e:
        print(f"\n{RED}Error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Default: ATOM/USDT with 10x leverage
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'ATOM/USDT:USDT'
    leverage = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    risk = float(sys.argv[3]) if len(sys.argv) > 3 else 5
    
    success = open_long_position(symbol, leverage, risk)
    
    if success:
        print(f"\n{GREEN}{'='*60}")
        print(f"TRADE EXECUTED SUCCESSFULLY")
        print(f"{'='*60}{RESET}\n")
    else:
        print(f"\n{RED}Trade execution failed{RESET}\n")
        sys.exit(1)
