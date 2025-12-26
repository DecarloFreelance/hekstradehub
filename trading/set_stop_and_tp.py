#!/usr/bin/env python3
"""Set stop loss and take profit for existing position"""
import ccxt
from dotenv import load_dotenv
import os
import sys

load_dotenv()

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BOLD = '\033[1m'
RESET = '\033[0m'

def set_sl_tp(symbol='ATOM/USDT:USDT'):
    exchange = ccxt.kucoinfutures({
        'apiKey': os.getenv('KUCOIN_API_KEY'),
        'secret': os.getenv('KUCOIN_API_SECRET'),
        'password': os.getenv('KUCOIN_API_PASSPHRASE'),
        'enableRateLimit': True,
    })
    
    try:
        # Get current position
        positions = exchange.fetch_positions([symbol])
        pos = [p for p in positions if float(p.get('contracts', 0)) != 0]
        
        if not pos:
            print(f"{RED}No open position found for {symbol}{RESET}")
            return
        
        current_pos = pos[0]
        contracts = abs(float(current_pos.get('contracts', 0)))
        entry = float(current_pos.get('entryPrice', 0))
        side = current_pos.get('side', 'long').lower()
        leverage = float(current_pos.get('leverage', 1))
        
        print(f"\n{BOLD}Current Position:{RESET}")
        print(f"  Symbol: {symbol}")
        print(f"  Side: {side.upper()}")
        print(f"  Contracts: {contracts}")
        print(f"  Entry: ${entry:.4f}")
        print(f"  Leverage: {leverage}x")
        
        # Calculate SL/TP (5% for both)
        if side == 'long':
            sl_price = entry * 0.95  # -5%
            tp_price = entry * 1.05  # +5%
            sl_side = 'sell'
            tp_side = 'sell'
        else:  # short
            sl_price = entry * 1.05  # +5%
            tp_price = entry * 0.95  # -5%
            sl_side = 'buy'
            tp_side = 'buy'
        
        print(f"\n{BOLD}Setting Protection:{RESET}")
        print(f"  Stop Loss: ${sl_price:.4f}")
        print(f"  Take Profit: ${tp_price:.4f}")
        
        # Try to place stop loss
        print(f"\n{BOLD}Placing Stop Loss...{RESET}")
        try:
            sl_order = exchange.create_order(
                symbol=symbol,
                type='market',
                side=sl_side,
                amount=contracts,
                params={
                    'stopPrice': str(sl_price),
                    'stop': 'down' if side == 'long' else 'up',
                    'closeOrder': True,
                    'reduceOnly': True
                }
            )
            print(f"{GREEN}✓ Stop Loss placed!{RESET}")
            print(f"  Order ID: {sl_order.get('id')}")
        except Exception as e:
            print(f"{YELLOW}⚠️ SL placement failed: {e}{RESET}")
            print(f"{RED}You MUST manually set SL at ${sl_price:.4f} on KuCoin interface!{RESET}")
        
        # Try to place take profit
        print(f"\n{BOLD}Placing Take Profit...{RESET}")
        try:
            tp_order = exchange.create_order(
                symbol=symbol,
                type='limit',
                side=tp_side,
                amount=contracts,
                price=tp_price,
                params={
                    'closeOrder': True,
                    'reduceOnly': True
                }
            )
            print(f"{GREEN}✓ Take Profit placed!{RESET}")
            print(f"  Order ID: {tp_order.get('id')}")
        except Exception as e:
            print(f"{YELLOW}⚠️ TP placement failed: {e}{RESET}")
            print(f"{RED}You MUST manually set TP at ${tp_price:.4f} on KuCoin interface!{RESET}")
        
        # Verify orders
        print(f"\n{BOLD}Verifying orders...{RESET}")
        orders = exchange.fetch_open_orders(symbol)
        if orders:
            print(f"{GREEN}✓ Found {len(orders)} open orders:{RESET}")
            for order in orders:
                print(f"  - {order.get('type')} {order.get('side')} @ ${order.get('price') or order.get('stopPrice', 0):.4f}")
        else:
            print(f"{YELLOW}⚠️ No open orders found - manual setup required!{RESET}")
        
    except Exception as e:
        print(f"\n{RED}Error: {e}{RESET}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'ATOM/USDT:USDT'
    set_sl_tp(symbol)
