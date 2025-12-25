#!/usr/bin/env python3
"""
Small Account Manager - Optimized for $5-50 accounts
Focus: Quick wins, fee-aware, maximum capital efficiency
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

class SmallAccountManager:
    """Optimized for accounts under $50"""
    
    def __init__(self, balance_usd=5.85):
        self.balance = balance_usd
        
        # KuCoin Futures Fees
        self.maker_fee = 0.0002  # 0.02% maker
        self.taker_fee = 0.0006  # 0.06% taker
        self.round_trip_fee = (self.taker_fee * 2) * 100  # 0.12% total
        
        # Small account settings
        self.max_risk_pct = 3.0  # 3% max risk per trade (aggressive but needed for small accounts)
        self.min_risk_reward = 2.5  # Minimum 2.5:1 to overcome fees
        self.max_leverage = 20  # Conservative max
        self.preferred_leverage = 10  # Sweet spot for small accounts
        
    def calculate_position_size(self, entry_price, stop_loss, leverage=None):
        """
        Calculate optimal position size for small account
        
        Returns:
            contracts: Number of contracts to trade
            margin_required: USDT margin needed
            risk_amount: USDT at risk
            fee_cost: Total fees for round trip
        """
        if leverage is None:
            leverage = self.preferred_leverage
        
        # Risk amount (3% of account)
        risk_usd = self.balance * (self.max_risk_pct / 100)
        
        # Stop loss distance
        if stop_loss > entry_price:  # SHORT position
            stop_distance = stop_loss - entry_price
        else:  # LONG position
            stop_distance = entry_price - stop_loss
        
        stop_pct = (stop_distance / entry_price) * 100
        
        # For small accounts, use margin-first approach
        # Start with 80% of balance as max margin
        max_margin = self.balance * 0.80
        
        # Calculate max contracts from margin
        max_contracts = int((max_margin * leverage) / entry_price)
        
        # Calculate contracts from risk (traditional way)
        risk_contracts = int(risk_usd / stop_distance)
        
        # Use the smaller of the two (safer)
        contracts = min(max_contracts, risk_contracts)
        
        # Ensure at least 1 contract for very small accounts
        if contracts < 1:
            contracts = 1
        
        # Recalculate based on actual contracts
        notional_value = contracts * entry_price
        margin_required = notional_value / leverage
        actual_risk = contracts * stop_distance
        
        # Calculate fees
        fee_cost = notional_value * (self.taker_fee * 2)  # Round trip
        
        return {
            'contracts': contracts,
            'margin_required': round(margin_required, 2),
            'risk_amount': round(actual_risk, 2),
            'fee_cost': round(fee_cost, 4),
            'notional_value': round(notional_value, 2),
            'leverage': leverage,
            'stop_pct': round(stop_pct, 2),
            'actual_risk_pct': round((actual_risk / self.balance) * 100, 2)
        }
    
    def calculate_take_profits(self, entry_price, stop_loss, side='LONG'):
        """
        Calculate take profit levels optimized for fees
        
        For small accounts, we need wins to significantly exceed fees
        Minimum 2.5R to make fees worthwhile
        """
        if side == 'LONG':
            risk = entry_price - stop_loss
            targets = [
                {
                    'level': 1,
                    'price': round(entry_price + (risk * 2.5), 4),
                    'rr': 2.5,
                    'size_pct': 50,  # Take 50% at 2.5R
                    'profit_after_fees': self._calc_net_profit(entry_price, entry_price + (risk * 2.5), 50)
                },
                {
                    'level': 2,
                    'price': round(entry_price + (risk * 4.0), 4),
                    'rr': 4.0,
                    'size_pct': 30,  # Take 30% at 4R
                    'profit_after_fees': self._calc_net_profit(entry_price, entry_price + (risk * 4.0), 30)
                },
                {
                    'level': 3,
                    'price': round(entry_price + (risk * 6.0), 4),
                    'rr': 6.0,
                    'size_pct': 20,  # Let 20% run to 6R
                    'profit_after_fees': self._calc_net_profit(entry_price, entry_price + (risk * 6.0), 20)
                }
            ]
        else:  # SHORT
            risk = stop_loss - entry_price
            targets = [
                {
                    'level': 1,
                    'price': round(entry_price - (risk * 2.5), 4),
                    'rr': 2.5,
                    'size_pct': 50,
                    'profit_after_fees': self._calc_net_profit(entry_price, entry_price - (risk * 2.5), 50)
                },
                {
                    'level': 2,
                    'price': round(entry_price - (risk * 4.0), 4),
                    'rr': 4.0,
                    'size_pct': 30,
                    'profit_after_fees': self._calc_net_profit(entry_price, entry_price - (risk * 4.0), 30)
                },
                {
                    'level': 3,
                    'price': round(entry_price - (risk * 6.0), 4),
                    'rr': 6.0,
                    'size_pct': 20,
                    'profit_after_fees': self._calc_net_profit(entry_price, entry_price - (risk * 6.0), 20)
                }
            ]
        
        return targets
    
    def _calc_net_profit(self, entry, exit_price, size_pct):
        """Calculate profit after fees for given exit"""
        # Simplified - just account for round trip fees
        gross_profit_pct = abs(((exit_price - entry) / entry) * 100)
        net_profit_pct = gross_profit_pct - self.round_trip_fee
        return round(net_profit_pct * (size_pct / 100), 2)
    
    def print_trade_plan(self, symbol, side, entry, stop, leverage=None):
        """Print complete trade plan for small account"""
        
        position = self.calculate_position_size(entry, stop, leverage)
        targets = self.calculate_take_profits(entry, stop, side)
        
        print("\n" + "=" * 70)
        print(f"{BOLD}{CYAN}SMALL ACCOUNT TRADE PLAN{RESET}")
        print(f"{BOLD}Account: ${self.balance:.2f} | Max Risk: {self.max_risk_pct}%{RESET}")
        print("=" * 70)
        
        print(f"\n{BOLD}POSITION{RESET}")
        print(f"Symbol:        {symbol}")
        print(f"Side:          {GREEN if side == 'LONG' else RED}{side}{RESET}")
        print(f"Entry:         ${entry:.4f}")
        print(f"Stop Loss:     ${stop:.4f} ({position['stop_pct']:.2f}%)")
        print(f"Leverage:      {position['leverage']}x")
        
        print(f"\n{BOLD}SIZE{RESET}")
        print(f"Contracts:     {position['contracts']}")
        print(f"Notional:      ${position['notional_value']:.2f}")
        print(f"Margin:        ${position['margin_required']:.2f} ({(position['margin_required']/self.balance*100):.1f}% of account)")
        print(f"Risk Amount:   ${position['risk_amount']:.2f}")
        print(f"Fees:          ${position['fee_cost']:.4f}")
        
        print(f"\n{BOLD}TAKE PROFITS{RESET}")
        for tp in targets:
            print(f"TP{tp['level']}: ${tp['price']:.4f} ({tp['rr']:.1f}R) - Close {tp['size_pct']}% | Net: +{tp['profit_after_fees']:.2f}%")
        
        # Calculate total potential
        total_potential = sum(t['profit_after_fees'] for t in targets)
        total_potential_usd = (total_potential / 100) * position['margin_required'] * position['leverage']
        
        print(f"\n{BOLD}POTENTIAL{RESET}")
        print(f"If all TPs hit: +{total_potential:.2f}% = ${total_potential_usd:.2f}")
        print(f"If stopped out:  -{self.max_risk_pct:.1f}% = -${position['risk_amount']:.2f}")
        print(f"Risk/Reward:     1:{total_potential/self.max_risk_pct:.2f}")
        
        # Warnings
        print(f"\n{BOLD}{YELLOW}SMALL ACCOUNT WARNINGS{RESET}")
        print(f"• Fees eat {self.round_trip_fee:.2f}% - need {self.round_trip_fee:.2f}% move just to break even")
        print(f"• Minimum target: {self.min_risk_reward}R to overcome fee drag")
        print(f"• Keep trades SHORT - under 4 hours ideal for small accounts")
        print(f"• One trade at a time - don't spread risk too thin")
        
        print("=" * 70 + "\n")
        
        return position, targets


def quick_calc():
    """Interactive calculator for trade planning"""
    
    print(f"\n{BOLD}{CYAN}=== SMALL ACCOUNT TRADE CALCULATOR ==={RESET}\n")
    
    balance = float(input(f"Account Balance [$5.85]: ") or 5.85)
    symbol = input("Symbol [BTC/USDT:USDT]: ") or "BTC/USDT:USDT"
    side = input("Side (LONG/SHORT): ").upper()
    entry = float(input("Entry Price: "))
    stop = float(input("Stop Loss: "))
    leverage = int(input(f"Leverage [10]: ") or 10)
    
    manager = SmallAccountManager(balance)
    manager.print_trade_plan(symbol, side, entry, stop, leverage)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'calc':
        quick_calc()
    else:
        # Example with current balance - use cheaper coin for small account
        manager = SmallAccountManager(5.85)
        
        print(f"\n{BOLD}Example: DOGE LONG Setup (Realistic for $5.85 account){RESET}")
        manager.print_trade_plan(
            symbol='DOGE/USDT:USDT',
            side='LONG',
            entry=0.3150,  # ~$0.31 per DOGE
            stop=0.3100,   # 50 points stop
            leverage=10
        )
        
        print(f"\n{YELLOW}💡 For small accounts, trade lower-priced coins:{RESET}")
        print(f"   ✅ DOGE, PEPE, XRP - affordable contract sizes")
        print(f"   ❌ BTC, ETH - too expensive per contract")
        print(f"\n{GREEN}Run with 'calc' argument for interactive mode:{RESET}")
        print(f"  python small_account_manager.py calc\n")
