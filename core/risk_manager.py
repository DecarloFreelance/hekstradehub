"""
Professional Risk Management Module
Handles position sizing, stop-loss calculation, and risk/reward analysis
"""

import pandas as pd
from typing import Dict, Tuple, Optional


class RiskManager:
    """
    Comprehensive risk management for crypto futures trading.
    Implements industry-standard risk management practices.
    """
    
    def __init__(self, 
                 account_balance: float,
                 max_risk_per_trade_pct: float = 2.0,
                 max_account_risk_pct: float = 10.0,
                 min_risk_reward_ratio: float = 2.0):
        """
        Initialize Risk Manager.
        
        Args:
            account_balance: Total account balance in USDT
            max_risk_per_trade_pct: Max % of account to risk per trade (default 2%)
            max_account_risk_pct: Max % of account exposed at once (default 10%)
            min_risk_reward_ratio: Minimum R:R ratio to accept (default 2.0)
        """
        self.account_balance = account_balance
        self.max_risk_per_trade_pct = max_risk_per_trade_pct
        self.max_account_risk_pct = max_account_risk_pct
        self.min_risk_reward_ratio = min_risk_reward_ratio
        
    def calculate_position_size(self,
                                entry_price: float,
                                stop_loss_price: float,
                                leverage: int = 10,
                                side: str = 'LONG') -> Dict:
        """
        Calculate optimal position size based on risk parameters.
        
        Args:
            entry_price: Planned entry price
            stop_loss_price: Stop loss price
            leverage: Leverage multiplier
            side: 'LONG' or 'SHORT'
            
        Returns:
            Dictionary with position sizing details
        """
        # Calculate risk per contract
        if side.upper() == 'LONG':
            risk_per_contract = entry_price - stop_loss_price
        else:  # SHORT
            risk_per_contract = stop_loss_price - entry_price
            
        if risk_per_contract <= 0:
            return {
                'error': 'Invalid stop loss - must be below entry for LONG, above for SHORT',
                'valid': False
            }
        
        # Calculate stop loss distance in percentage
        stop_loss_pct = abs(risk_per_contract / entry_price) * 100
        
        # Maximum dollar amount to risk on this trade
        max_risk_dollars = self.account_balance * (self.max_risk_per_trade_pct / 100)
        
        # Calculate position size (number of contracts)
        # Formula: Position Size = (Account Risk $) / (Risk per Contract)
        position_size = max_risk_dollars / risk_per_contract
        
        # Calculate required margin
        notional_value = position_size * entry_price
        required_margin = notional_value / leverage
        
        # Check if we have enough balance
        if required_margin > self.account_balance * 0.9:  # Keep 10% buffer
            # Adjust position size to fit available margin
            max_margin = self.account_balance * 0.9
            notional_value = max_margin * leverage
            position_size = notional_value / entry_price
            required_margin = max_margin
            
        # Calculate actual risk with adjusted position
        actual_risk_dollars = position_size * risk_per_contract
        actual_risk_pct = (actual_risk_dollars / self.account_balance) * 100
        
        # Calculate position value as % of account
        position_pct = (required_margin / self.account_balance) * 100
        
        return {
            'valid': True,
            'contracts': int(position_size),
            'notional_value': notional_value,
            'required_margin': required_margin,
            'margin_pct': position_pct,
            'stop_loss_pct': stop_loss_pct,
            'risk_dollars': actual_risk_dollars,
            'risk_pct': actual_risk_pct,
            'leverage': leverage,
            'entry_price': entry_price,
            'stop_loss_price': stop_loss_price,
            'side': side.upper()
        }
    
    def calculate_take_profits(self,
                              entry_price: float,
                              stop_loss_price: float,
                              side: str = 'LONG',
                              num_targets: int = 3) -> Dict:
        """
        Calculate multiple take-profit targets based on risk/reward.
        
        Args:
            entry_price: Entry price
            stop_loss_price: Stop loss price
            side: 'LONG' or 'SHORT'
            num_targets: Number of TP levels (default 3)
            
        Returns:
            Dictionary with TP levels and R:R ratios
        """
        # Calculate risk distance
        if side.upper() == 'LONG':
            risk_distance = entry_price - stop_loss_price
        else:  # SHORT
            risk_distance = stop_loss_price - entry_price
            
        targets = []
        
        # Generate TP targets with increasing R:R
        for i in range(1, num_targets + 1):
            rr_ratio = i * 1.5  # 1.5R, 3R, 4.5R
            
            if side.upper() == 'LONG':
                tp_price = entry_price + (risk_distance * rr_ratio)
                profit_pct = ((tp_price - entry_price) / entry_price) * 100
            else:  # SHORT
                tp_price = entry_price - (risk_distance * rr_ratio)
                profit_pct = ((entry_price - tp_price) / entry_price) * 100
                
            targets.append({
                'level': i,
                'price': tp_price,
                'rr_ratio': rr_ratio,
                'profit_pct': profit_pct,
                'allocation_pct': 33.33 if i < num_targets else 34  # Split position evenly
            })
            
        return {
            'side': side.upper(),
            'entry': entry_price,
            'stop_loss': stop_loss_price,
            'targets': targets
        }
    
    def validate_trade(self,
                      entry_price: float,
                      stop_loss_price: float,
                      take_profit_price: float,
                      side: str = 'LONG') -> Dict:
        """
        Validate if a trade meets minimum risk/reward criteria.
        
        Args:
            entry_price: Entry price
            stop_loss_price: Stop loss price
            take_profit_price: Take profit price
            side: 'LONG' or 'SHORT'
            
        Returns:
            Dictionary with validation results
        """
        if side.upper() == 'LONG':
            risk = entry_price - stop_loss_price
            reward = take_profit_price - entry_price
        else:  # SHORT
            risk = stop_loss_price - entry_price
            reward = entry_price - take_profit_price
            
        if risk <= 0:
            return {
                'valid': False,
                'reason': 'Invalid stop loss placement',
                'rr_ratio': 0
            }
            
        if reward <= 0:
            return {
                'valid': False,
                'reason': 'Invalid take profit placement',
                'rr_ratio': 0
            }
            
        rr_ratio = reward / risk
        
        if rr_ratio < self.min_risk_reward_ratio:
            return {
                'valid': False,
                'reason': f'R:R ratio {rr_ratio:.2f} below minimum {self.min_risk_reward_ratio}',
                'rr_ratio': rr_ratio
            }
            
        return {
            'valid': True,
            'reason': 'Trade meets risk/reward criteria',
            'rr_ratio': rr_ratio,
            'risk_dollars': risk,
            'reward_dollars': reward
        }
    
    def calculate_atr_stop_loss(self,
                               df: pd.DataFrame,
                               entry_price: float,
                               atr_multiplier: float = 1.5,
                               side: str = 'LONG') -> float:
        """
        Calculate ATR-based stop loss (volatility-adjusted).
        
        Args:
            df: DataFrame with OHLC data
            entry_price: Entry price
            atr_multiplier: ATR multiplier for stop distance (default 1.5)
            side: 'LONG' or 'SHORT'
            
        Returns:
            Stop loss price
        """
        from core.indicators import calculate_atr
        
        atr = calculate_atr(df).iloc[-1]
        stop_distance = atr * atr_multiplier
        
        if side.upper() == 'LONG':
            stop_loss = entry_price - stop_distance
        else:  # SHORT
            stop_loss = entry_price + stop_distance
            
        return stop_loss
    
    def calculate_portfolio_risk(self, open_positions: list) -> Dict:
        """
        Calculate total portfolio risk exposure.
        
        Args:
            open_positions: List of dicts with position details
                           Each dict should have: {margin, risk_dollars, side}
            
        Returns:
            Dictionary with portfolio risk metrics
        """
        total_margin_used = sum(pos.get('margin', 0) for pos in open_positions)
        total_risk = sum(pos.get('risk_dollars', 0) for pos in open_positions)
        
        margin_used_pct = (total_margin_used / self.account_balance) * 100
        total_risk_pct = (total_risk / self.account_balance) * 100
        
        long_positions = sum(1 for pos in open_positions if pos.get('side') == 'LONG')
        short_positions = sum(1 for pos in open_positions if pos.get('side') == 'SHORT')
        
        return {
            'total_positions': len(open_positions),
            'long_positions': long_positions,
            'short_positions': short_positions,
            'total_margin_used': total_margin_used,
            'margin_used_pct': margin_used_pct,
            'total_risk_dollars': total_risk,
            'total_risk_pct': total_risk_pct,
            'account_balance': self.account_balance,
            'available_balance': self.account_balance - total_margin_used,
            'risk_limit_reached': total_risk_pct >= self.max_account_risk_pct
        }
    
    def suggest_position_adjustments(self,
                                    current_price: float,
                                    entry_price: float,
                                    stop_loss_price: float,
                                    side: str = 'LONG') -> Dict:
        """
        Suggest position adjustments (trailing stop, partial profit taking).
        
        Args:
            current_price: Current market price
            entry_price: Original entry price
            stop_loss_price: Current stop loss
            side: 'LONG' or 'SHORT'
            
        Returns:
            Dictionary with adjustment suggestions
        """
        suggestions = []
        
        if side.upper() == 'LONG':
            profit_pct = ((current_price - entry_price) / entry_price) * 100
            
            # Move to breakeven at +5%
            if profit_pct >= 5 and stop_loss_price < entry_price:
                suggestions.append({
                    'action': 'MOVE_TO_BREAKEVEN',
                    'new_stop': entry_price,
                    'reason': 'Move stop to breakeven (risk-free trade)'
                })
            
            # Trail stop at +10%
            if profit_pct >= 10:
                trailing_stop = entry_price + (current_price - entry_price) * 0.5
                if trailing_stop > stop_loss_price:
                    suggestions.append({
                        'action': 'TRAIL_STOP',
                        'new_stop': trailing_stop,
                        'reason': f'Trail stop to lock in {((trailing_stop-entry_price)/entry_price)*100:.1f}% profit'
                    })
            
            # Partial profit suggestions
            if profit_pct >= 5 and profit_pct < 10:
                suggestions.append({
                    'action': 'TAKE_PARTIAL_PROFIT',
                    'percentage': 30,
                    'reason': 'Take 30% profit at +5%'
                })
            elif profit_pct >= 10:
                suggestions.append({
                    'action': 'TAKE_PARTIAL_PROFIT',
                    'percentage': 50,
                    'reason': 'Take 50% profit at +10%'
                })
                
        else:  # SHORT
            profit_pct = ((entry_price - current_price) / entry_price) * 100
            
            # Move to breakeven at +5%
            if profit_pct >= 5 and stop_loss_price > entry_price:
                suggestions.append({
                    'action': 'MOVE_TO_BREAKEVEN',
                    'new_stop': entry_price,
                    'reason': 'Move stop to breakeven (risk-free trade)'
                })
            
            # Trail stop at +10%
            if profit_pct >= 10:
                trailing_stop = entry_price - (entry_price - current_price) * 0.5
                if trailing_stop < stop_loss_price:
                    suggestions.append({
                        'action': 'TRAIL_STOP',
                        'new_stop': trailing_stop,
                        'reason': f'Trail stop to lock in {((entry_price-trailing_stop)/entry_price)*100:.1f}% profit'
                    })
            
            # Partial profit suggestions
            if profit_pct >= 5 and profit_pct < 10:
                suggestions.append({
                    'action': 'TAKE_PARTIAL_PROFIT',
                    'percentage': 30,
                    'reason': 'Take 30% profit at +5%'
                })
            elif profit_pct >= 10:
                suggestions.append({
                    'action': 'TAKE_PARTIAL_PROFIT',
                    'percentage': 50,
                    'reason': 'Take 50% profit at +10%'
                })
        
        return {
            'current_price': current_price,
            'entry_price': entry_price,
            'profit_pct': profit_pct,
            'suggestions': suggestions
        }
