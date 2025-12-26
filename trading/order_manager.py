#!/usr/bin/env python3
"""
Order Manager - Correctly place stop loss and take profit orders on KuCoin
Handles the quirks of KuCoin Futures API
"""

import ccxt
from dotenv import load_dotenv
import os
import sys

# RAM Protection
sys.path.insert(0, '/home/hektic/saddynhektic workspace')
try:
    from Tools.resource_manager import check_ram_before_processing
    check_ram_before_processing(min_free_gb=1.5)
except:
    pass

load_dotenv()

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
BOLD = '\033[1m'
RESET = '\033[0m'


class KuCoinOrderManager:
    """Manages orders on KuCoin Futures with proper stop loss/TP handling"""
    
    def __init__(self):
        self.exchange = ccxt.kucoinfutures({
            'apiKey': os.getenv('KUCOIN_API_KEY'),
            'secret': os.getenv('KUCOIN_API_SECRET'),
            'password': os.getenv('KUCOIN_API_PASSPHRASE'),
            'enableRateLimit': True,
        })
    
    def get_position(self, symbol):
        """Get current position for symbol"""
        try:
            positions = self.exchange.fetch_positions([symbol])
            active = [p for p in positions if float(p.get('contracts', 0)) != 0]
            return active[0] if active else None
        except Exception as e:
            print(f"{RED}Error fetching position: {e}{RESET}")
            return None
    
    def place_stop_loss(self, symbol, stop_price, position_side=None, contracts=None):
        """
        Place stop loss order for existing position
        
        Args:
            symbol: Trading pair (e.g., 'DOGE/USDT:USDT')
            stop_price: Price to trigger stop
            position_side: 'LONG' or 'SHORT' (auto-detected if None)
            contracts: Number of contracts (auto-uses full position if None)
        """
        
        # Auto-detect position if not provided
        if position_side is None or contracts is None:
            position = self.get_position(symbol)
            if not position:
                print(f"{RED}No position found for {symbol}{RESET}")
                return None
            
            position_side = position.get('side', '').upper()
            contracts = abs(float(position.get('contracts', 0)))
        
        # Determine order side (opposite of position)
        if position_side == 'LONG':
            order_side = 'sell'  # Sell to close long
        elif position_side == 'SHORT':
            order_side = 'buy'   # Buy to close short
        else:
            print(f"{RED}Invalid position side: {position_side}{RESET}")
            return None
        
        print(f"\n{CYAN}Placing stop loss...{RESET}")
        print(f"Symbol: {symbol}")
        print(f"Position: {position_side}")
        print(f"Stop Price: ${stop_price:.4f}")
        print(f"Contracts: {contracts}")
        
        try:
            order = self.exchange.create_order(
                symbol=symbol,
                type='stop',  # Stop market order
                side=order_side,
                amount=contracts,
                price=None,  # Market order when triggered
                params={
                    'stop': 'down' if position_side == 'LONG' else 'up',  # Trigger direction
                    'stopPrice': stop_price,
                    'stopPriceType': 'TP',  # TP = last price, MP = mark price
                    'reduceOnly': True,     # Only close position, don't open new
                    'closeOrder': True      # This is a closing order
                }
            )
            
            print(f"{GREEN}✅ Stop loss placed successfully!{RESET}")
            print(f"Order ID: {order.get('id')}")
            return order
            
        except Exception as e:
            print(f"{RED}❌ Failed to place stop loss: {e}{RESET}")
            
            # Try alternative format
            print(f"{YELLOW}Trying alternative format...{RESET}")
            try:
                order = self.exchange.create_order(
                    symbol=symbol,
                    type='market',
                    side=order_side,
                    amount=contracts,
                    params={
                        'stopPrice': stop_price,
                        'stopPriceType': 'TP',
                        'stop': 'loss',
                        'reduceOnly': True
                    }
                )
                print(f"{GREEN}✅ Stop loss placed (alternative format)!{RESET}")
                return order
            except Exception as e2:
                print(f"{RED}❌ Alternative format also failed: {e2}{RESET}")
                return None
    
    def place_take_profit(self, symbol, tp_price, contracts, position_side=None):
        """
        Place take profit order
        
        Args:
            symbol: Trading pair
            tp_price: Price to take profit
            contracts: Number of contracts to close
            position_side: 'LONG' or 'SHORT' (auto-detected if None)
        """
        
        # Auto-detect position if not provided
        if position_side is None:
            position = self.get_position(symbol)
            if not position:
                print(f"{RED}No position found for {symbol}{RESET}")
                return None
            position_side = position.get('side', '').upper()
        
        # Determine order side
        if position_side == 'LONG':
            order_side = 'sell'
        else:
            order_side = 'buy'
        
        print(f"\n{CYAN}Placing take profit...{RESET}")
        print(f"Symbol: {symbol}")
        print(f"TP Price: ${tp_price:.4f}")
        print(f"Contracts: {contracts}")
        
        try:
            order = self.exchange.create_order(
                symbol=symbol,
                type='stop',
                side=order_side,
                amount=contracts,
                price=None,
                params={
                    'stop': 'up' if position_side == 'LONG' else 'down',
                    'stopPrice': tp_price,
                    'stopPriceType': 'TP',
                    'reduceOnly': True,
                    'closeOrder': True
                }
            )
            
            print(f"{GREEN}✅ Take profit placed!{RESET}")
            print(f"Order ID: {order.get('id')}")
            return order
            
        except Exception as e:
            print(f"{RED}❌ Failed to place take profit: {e}{RESET}")
            return None
    
    def place_full_trade(self, symbol, side, entry_price, stop_price, tp_prices, contracts, leverage=10):
        """
        Place complete trade: entry + stop + multiple TPs
        
        Args:
            symbol: Trading pair
            side: 'LONG' or 'SHORT'
            entry_price: Entry limit order price
            stop_price: Stop loss price
            tp_prices: List of TP prices [tp1, tp2, tp3]
            contracts: Total contracts
            leverage: Leverage to use
        """
        
        print(f"\n{BOLD}{CYAN}{'='*70}{RESET}")
        print(f"{BOLD}PLACING COMPLETE TRADE{RESET}")
        print(f"{BOLD}{CYAN}{'='*70}{RESET}\n")
        
        # Set leverage
        try:
            self.exchange.set_leverage(leverage, symbol)
            print(f"{GREEN}✅ Leverage set to {leverage}x{RESET}")
        except Exception as e:
            print(f"{YELLOW}⚠️  Leverage setting: {e}{RESET}")
        
        # 1. Place entry order
        print(f"\n{BOLD}1. ENTRY ORDER{RESET}")
        order_side = 'buy' if side == 'LONG' else 'sell'
        
        try:
            entry_order = self.exchange.create_limit_order(
                symbol=symbol,
                side=order_side,
                amount=contracts,
                price=entry_price
            )
            print(f"{GREEN}✅ Entry order placed: {order_side.upper()} {contracts} @ ${entry_price:.4f}{RESET}")
            print(f"Order ID: {entry_order.get('id')}")
        except Exception as e:
            print(f"{RED}❌ Entry order failed: {e}{RESET}")
            return
        
        print(f"\n{YELLOW}⏳ Waiting for entry to fill before placing stop/TPs...{RESET}")
        print(f"{YELLOW}   (KuCoin requires position to exist before stop orders){RESET}")
        print(f"\n{BOLD}Once filled, run:{RESET}")
        print(f"  python order_manager.py set-stops {symbol} {stop_price} {' '.join(map(str, tp_prices))}")
        
        return entry_order
    
    def set_stops_and_tps(self, symbol, stop_price, tp_prices, tp_sizes=None):
        """
        Set stop loss and take profits for existing position
        
        Args:
            symbol: Trading pair
            stop_price: Stop loss price
            tp_prices: List of TP prices [tp1, tp2, ...]
            tp_sizes: List of % sizes for each TP [50, 30, 20] (default if None)
        """
        
        # Get current position
        position = self.get_position(symbol)
        if not position:
            print(f"{RED}No position found for {symbol}{RESET}")
            return
        
        total_contracts = abs(float(position.get('contracts', 0)))
        position_side = position.get('side', '').upper()
        
        print(f"\n{BOLD}Setting stops for {total_contracts} contracts ({position_side}){RESET}\n")
        
        # Default TP sizes
        if tp_sizes is None:
            if len(tp_prices) == 1:
                tp_sizes = [100]
            elif len(tp_prices) == 2:
                tp_sizes = [60, 40]
            elif len(tp_prices) == 3:
                tp_sizes = [50, 30, 20]
            else:
                # Distribute evenly
                size = 100 / len(tp_prices)
                tp_sizes = [size] * len(tp_prices)
        
        # Place stop loss for full position
        self.place_stop_loss(symbol, stop_price, position_side, total_contracts)
        
        # Place TPs
        for i, (tp_price, tp_pct) in enumerate(zip(tp_prices, tp_sizes), 1):
            tp_contracts = int((total_contracts * tp_pct) / 100)
            if tp_contracts > 0:
                print(f"\n{BOLD}TP{i} ({tp_pct}%){RESET}")
                self.place_take_profit(symbol, tp_price, tp_contracts, position_side)
        
        print(f"\n{GREEN}{BOLD}✅ All orders placed!{RESET}")


def main():
    """CLI interface"""
    
    if len(sys.argv) < 2:
        print(f"""
{BOLD}KuCoin Order Manager{RESET}

Usage:
  python order_manager.py test                  - Test API connection
  
  python order_manager.py set-stop SYMBOL PRICE - Place stop loss
  Example: python order_manager.py set-stop DOGE/USDT:USDT 0.31
  
  python order_manager.py set-stops SYMBOL STOP TP1 [TP2] [TP3] - Place stop + TPs
  Example: python order_manager.py set-stops DOGE/USDT:USDT 0.31 0.33 0.35 0.37
  
  python order_manager.py full-trade SYMBOL SIDE ENTRY STOP TP1 TP2 CONTRACTS LEVERAGE
  Example: python order_manager.py full-trade DOGE/USDT:USDT LONG 0.315 0.31 0.33 0.35 35 10
        """)
        return
    
    manager = KuCoinOrderManager()
    command = sys.argv[1]
    
    if command == 'test':
        # Run diagnostics
        os.system('python test_kucoin_orders.py')
    
    elif command == 'set-stop':
        if len(sys.argv) < 4:
            print(f"{RED}Usage: python order_manager.py set-stop SYMBOL STOP_PRICE{RESET}")
            return
        
        symbol = sys.argv[2]
        stop_price = float(sys.argv[3])
        manager.place_stop_loss(symbol, stop_price)
    
    elif command == 'set-stops':
        if len(sys.argv) < 5:
            print(f"{RED}Usage: python order_manager.py set-stops SYMBOL STOP TP1 [TP2] [TP3]{RESET}")
            return
        
        symbol = sys.argv[2]
        stop_price = float(sys.argv[3])
        tp_prices = [float(x) for x in sys.argv[4:]]
        
        manager.set_stops_and_tps(symbol, stop_price, tp_prices)
    
    elif command == 'full-trade':
        if len(sys.argv) < 10:
            print(f"{RED}Usage: python order_manager.py full-trade SYMBOL SIDE ENTRY STOP TP1 TP2 CONTRACTS LEV{RESET}")
            return
        
        symbol = sys.argv[2]
        side = sys.argv[3].upper()
        entry = float(sys.argv[4])
        stop = float(sys.argv[5])
        tp1 = float(sys.argv[6])
        tp2 = float(sys.argv[7])
        contracts = int(sys.argv[8])
        leverage = int(sys.argv[9])
        
        tp3 = float(sys.argv[10]) if len(sys.argv) > 10 else None
        tp_prices = [tp1, tp2] if tp3 is None else [tp1, tp2, tp3]
        
        manager.place_full_trade(symbol, side, entry, stop, tp_prices, contracts, leverage)


if __name__ == '__main__':
    main()
