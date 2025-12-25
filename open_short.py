#!/usr/bin/env python3
"""Execute SHORT position on OP/USDT"""
import ccxt
from dotenv import load_dotenv
import os
import sys

# RAM Protection - Critical for trade execution
sys.path.insert(0, '/home/hektic/saddynhektic workspace')
try:
    from Tools.resource_manager import check_ram_before_processing
    check_ram_before_processing(min_free_gb=1.5)
except ImportError:
    print("⚠️  Warning: RAM protection not available")
except MemoryError as e:
    print(f"❌ Insufficient RAM: {e}")
    print("DO NOT execute trades with low RAM!")
    exit(1)

load_dotenv()

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BOLD = '\033[1m'
RESET = '\033[0m'

def open_short_position():
    """Open SHORT position on OP with proper risk management"""
    
    exchange = ccxt.kucoinfutures({
        'apiKey': os.getenv('KUCOIN_API_KEY'),
        'secret': os.getenv('KUCOIN_API_SECRET'),
        'password': os.getenv('KUCOIN_API_PASSPHRASE'),
        'enableRateLimit': True,
    })
    
    symbol = 'OP/USDT:USDT'
    
    try:
        # Get account balance
        balance = exchange.fetch_balance()
        available = float(balance['USDT']['free'])
        
        print(f"\n{BOLD}{'='*60}{RESET}")
        print(f"{BOLD}OPENING SHORT POSITION ON OP{RESET}")
        print(f"{'='*60}\n")
        
        print(f"Available Balance: ${available:.2f} USDT")
        
        if available < 1:
            print(f"{RED}Insufficient balance to open position{RESET}")
            return
        
        # Get current market price
        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        
        print(f"Current OP Price: ${current_price:.6f}")
        
        # Get market info for min contract size
        market = exchange.market(symbol)
        min_contract = market['limits']['amount']['min']
        contract_size = market['contractSize']
        
        # Calculate position
        # Use 80% of available balance for safety (keep some for fees)
        margin = available * 0.80
        leverage = 10  # 10x leverage
        
        # Calculate contracts
        notional = margin * leverage
        contracts = int(notional / current_price)
        
        # Ensure we meet minimum
        if contracts < min_contract:
            contracts = int(min_contract)
            margin = (contracts * current_price) / leverage
        
        actual_notional = contracts * current_price
        
        print(f"\n{BOLD}Position Details:{RESET}")
        print(f"  Side: SHORT")
        print(f"  Leverage: {leverage}x")
        print(f"  Margin: ${margin:.2f}")
        print(f"  Contracts: {contracts}")
        print(f"  Notional: ${actual_notional:.2f}")
        
        # Calculate stops
        stop_loss_price = current_price * 1.05  # +5% (loss for short)
        take_profit_1 = current_price * 0.95    # -5% (profit for short)
        take_profit_2 = current_price * 0.90    # -10%
        
        print(f"\n{BOLD}Risk Management:{RESET}")
        print(f"  Entry: ${current_price:.6f}")
        print(f"  Stop Loss (+5%): ${stop_loss_price:.6f}")
        print(f"  Take Profit 1 (-5%): ${take_profit_1:.6f}")
        print(f"  Take Profit 2 (-10%): ${take_profit_2:.6f}")
        
        # Calculate potential P&L
        potential_loss = (stop_loss_price - current_price) * contracts * leverage
        potential_profit_1 = (current_price - take_profit_1) * contracts * leverage
        
        print(f"\n{BOLD}Potential Outcomes:{RESET}")
        print(f"  {RED}Max Loss (if SL hit): $-{abs(potential_loss):.2f}{RESET}")
        print(f"  {GREEN}Profit at TP1: $+{potential_profit_1:.2f}{RESET}")
        
        # Ask for confirmation
        print(f"\n{YELLOW}{'='*60}{RESET}")
        response = input(f"{YELLOW}Confirm SHORT position? (yes/no): {RESET}")
        
        if response.lower() != 'yes':
            print(f"{RED}Trade cancelled.{RESET}")
            return
        
        # Set leverage first
        print(f"\n{BOLD}Setting leverage to {leverage}x...{RESET}")
        try:
            exchange.set_leverage(leverage, symbol)
            print(f"{GREEN}✓ Leverage set{RESET}")
        except Exception as e:
            print(f"{YELLOW}Leverage setting: {e}{RESET}")
        
        # Place market order to open SHORT
        print(f"\n{BOLD}Placing SHORT market order...{RESET}")
        
        order = exchange.create_market_order(
            symbol=symbol,
            side='sell',  # SELL = SHORT
            amount=contracts,
            params={'leverage': leverage}
        )
        
        print(f"{GREEN}✓ SHORT position opened!{RESET}")
        print(f"\nOrder ID: {order['id']}")
        print(f"Status: {order['status']}")
        print(f"Filled: {order['filled']} contracts")
        
        # Place stop loss order
        print(f"\n{BOLD}Setting stop loss...{RESET}")
        try:
            sl_order = exchange.create_order(
                symbol=symbol,
                type='stop',
                side='buy',  # BUY to close SHORT
                amount=contracts,
                price=None,
                params={
                    'stopPrice': stop_loss_price,
                    'stop': 'up',
                    'closeOrder': True
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
                side='buy',  # BUY to close SHORT
                amount=contracts,
                price=take_profit_1,
                params={
                    'stopPrice': take_profit_1,
                    'stop': 'down',
                    'closeOrder': True
                }
            )
            print(f"{GREEN}✓ Take profit set at ${take_profit_1:.6f}{RESET}")
        except Exception as e:
            print(f"{YELLOW}⚠ Could not set TP automatically: {e}{RESET}")
            print(f"{YELLOW}⚠ MANUALLY set take profit at ${take_profit_1:.6f}{RESET}")
        
        print(f"\n{BOLD}{GREEN}{'='*60}{RESET}")
        print(f"{BOLD}{GREEN}SHORT POSITION ACTIVE ON OP{RESET}")
        print(f"{BOLD}{GREEN}{'='*60}{RESET}\n")
        
        print(f"{YELLOW}⚠️  Monitor your position closely!{RESET}")
        print(f"{YELLOW}⚠️  All trends are DOWN which favors SHORT{RESET}")
        print(f"{YELLOW}⚠️  But price is overbought - could bounce first{RESET}")
        
    except Exception as e:
        print(f"\n{RED}Error opening position: {e}{RESET}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    open_short_position()
