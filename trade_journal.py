#!/usr/bin/env python3
"""
Trade Journal - Automatic logging for continuous improvement
Logs all trades with full context for analysis
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

class TradeJournal:
    def __init__(self, filepath='trade_journal.json'):
        self.filepath = filepath
        self.load_journal()
    
    def load_journal(self):
        """Load existing journal or create new"""
        try:
            with open(self.filepath, 'r') as f:
                self.trades = json.load(f)
        except FileNotFoundError:
            self.trades = []
            self.save_journal()
    
    def log_trade(self, trade_data):
        """
        Log completed trade with full context
        
        Required fields in trade_data:
            - symbol: Trading pair (e.g., 'BTC/USDT:USDT')
            - side: 'LONG' or 'SHORT'
            - entry: Entry price
            - exit: Exit price
            - stop: Stop loss price
            - pnl_usd: Profit/Loss in USD
            - pnl_pct: P&L percentage
        
        Optional fields:
            - tp_hit: Which TP level was hit (1, 2, 3, or None)
            - hold_time: Duration position was held
            - score: Entry score (0-100)
            - trend_4h: 4H trend direction
            - adx: ADX value at entry
            - volatility: Market volatility
            - notes: Any additional notes
        """
        entry = {
            'id': len(self.trades) + 1,
            'timestamp': datetime.now().isoformat(),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'symbol': trade_data['symbol'],
            'side': trade_data['side'],
            'entry_price': round(float(trade_data['entry']), 4),
            'exit_price': round(float(trade_data['exit']), 4),
            'stop_loss': round(float(trade_data['stop']), 4),
            'take_profit_hit': trade_data.get('tp_hit', None),
            'pnl_usd': round(float(trade_data['pnl_usd']), 2),
            'pnl_pct': round(float(trade_data['pnl_pct']), 2),
            'hold_time': trade_data.get('hold_time', 'N/A'),
            'entry_score': trade_data.get('score', 0),
            'market_conditions': {
                'trend_4h': trade_data.get('trend_4h', 'UNKNOWN'),
                'adx': trade_data.get('adx', 0),
                'volatility': trade_data.get('volatility', 'UNKNOWN')
            },
            'notes': trade_data.get('notes', '')
        }
        
        self.trades.append(entry)
        self.save_journal()
        
        # Print confirmation
        result = '✅ WIN' if entry['pnl_usd'] > 0 else '❌ LOSS'
        print(f"\n{result} - Trade #{entry['id']} logged to journal")
        print(f"   {entry['symbol']} {entry['side']}: ${entry['pnl_usd']:+.2f} ({entry['pnl_pct']:+.2f}%)")
    
    def save_journal(self):
        """Save journal to file"""
        with open(self.filepath, 'w') as f:
            json.dump(self.trades, f, indent=2)
    
    def get_stats(self, days=30):
        """
        Get performance stats for last N days
        
        Returns dict with:
            - total_trades
            - winners/losers
            - win_rate
            - total_pnl
            - avg_win/avg_loss
            - best_trade/worst_trade
            - avg_hold_time
        """
        if not self.trades:
            return None
        
        # Filter recent trades
        cutoff = datetime.now() - timedelta(days=days)
        recent = [t for t in self.trades 
                  if datetime.fromisoformat(t['timestamp']) > cutoff]
        
        if not recent:
            return None
        
        winners = [t for t in recent if t['pnl_usd'] > 0]
        losers = [t for t in recent if t['pnl_usd'] < 0]
        
        stats = {
            'period_days': days,
            'total_trades': len(recent),
            'winners': len(winners),
            'losers': len(losers),
            'win_rate': round((len(winners) / len(recent) * 100), 2) if recent else 0,
            'total_pnl': round(sum(t['pnl_usd'] for t in recent), 2),
            'avg_win': round(sum(t['pnl_usd'] for t in winners) / len(winners), 2) if winners else 0,
            'avg_loss': round(sum(t['pnl_usd'] for t in losers) / len(losers), 2) if losers else 0,
            'best_trade': max(recent, key=lambda x: x['pnl_usd']),
            'worst_trade': min(recent, key=lambda x: x['pnl_usd']),
            'avg_score': round(sum(t['entry_score'] for t in recent) / len(recent), 1),
        }
        
        # Calculate profit factor
        total_wins = sum(t['pnl_usd'] for t in winners)
        total_losses = abs(sum(t['pnl_usd'] for t in losers))
        stats['profit_factor'] = round(total_wins / total_losses, 2) if total_losses > 0 else 0
        
        return stats
    
    def print_stats(self, days=30):
        """Print formatted statistics"""
        stats = self.get_stats(days)
        
        if not stats:
            print(f"\nNo trades found in the last {days} days")
            return
        
        print("\n" + "=" * 70)
        print(f"{'TRADING PERFORMANCE':^70}")
        print(f"{'Last ' + str(days) + ' Days':^70}")
        print("=" * 70)
        print(f"\nTotal Trades:    {stats['total_trades']}")
        print(f"Winners:         {stats['winners']} ({stats['win_rate']:.1f}%)")
        print(f"Losers:          {stats['losers']}")
        print(f"\nTotal P&L:       ${stats['total_pnl']:+.2f}")
        print(f"Avg Win:         ${stats['avg_win']:.2f}")
        print(f"Avg Loss:        ${stats['avg_loss']:.2f}")
        print(f"Profit Factor:   {stats['profit_factor']:.2f}")
        print(f"\nAvg Entry Score: {stats['avg_score']:.1f}/100")
        print(f"\nBest Trade:      {stats['best_trade']['symbol']} ${stats['best_trade']['pnl_usd']:+.2f}")
        print(f"Worst Trade:     {stats['worst_trade']['symbol']} ${stats['worst_trade']['pnl_usd']:+.2f}")
        print("=" * 70 + "\n")
    
    def get_all_trades(self):
        """Return all trades"""
        return self.trades
    
    def export_csv(self, filepath='trade_journal.csv'):
        """Export journal to CSV for Excel analysis"""
        import csv
        
        if not self.trades:
            print("No trades to export")
            return
        
        with open(filepath, 'w', newline='') as f:
            # Get all field names
            fieldnames = [
                'id', 'timestamp', 'date', 'symbol', 'side', 
                'entry_price', 'exit_price', 'stop_loss', 'take_profit_hit',
                'pnl_usd', 'pnl_pct', 'hold_time', 'entry_score', 
                'trend_4h', 'adx', 'volatility', 'notes'
            ]
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for trade in self.trades:
                # Flatten nested market_conditions
                row = {k: v for k, v in trade.items() if k != 'market_conditions'}
                if 'market_conditions' in trade:
                    row.update({
                        'trend_4h': trade['market_conditions'].get('trend_4h'),
                        'adx': trade['market_conditions'].get('adx'),
                        'volatility': trade['market_conditions'].get('volatility')
                    })
                writer.writerow(row)
        
        print(f"✅ Exported {len(self.trades)} trades to {filepath}")


# CLI Interface
if __name__ == '__main__':
    import sys
    
    journal = TradeJournal()
    
    if len(sys.argv) == 1:
        # No arguments - show stats
        journal.print_stats(days=30)
    
    elif sys.argv[1] == 'stats':
        # Show stats for specific period
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        journal.print_stats(days=days)
    
    elif sys.argv[1] == 'export':
        # Export to CSV
        filepath = sys.argv[2] if len(sys.argv) > 2 else 'trade_journal.csv'
        journal.export_csv(filepath)
    
    elif sys.argv[1] == 'log':
        # Quick manual logging
        print("\n=== Manual Trade Entry ===")
        
        trade_data = {
            'symbol': input("Symbol (e.g., BTC/USDT:USDT): "),
            'side': input("Side (LONG/SHORT): ").upper(),
            'entry': float(input("Entry Price: ")),
            'exit': float(input("Exit Price: ")),
            'stop': float(input("Stop Loss: ")),
            'pnl_usd': float(input("P&L USD: ")),
            'pnl_pct': float(input("P&L %: ")),
            'score': int(input("Entry Score (0-100): ") or 0),
            'notes': input("Notes (optional): ")
        }
        
        journal.log_trade(trade_data)
    
    else:
        print("Usage:")
        print("  python trade_journal.py              - Show 30-day stats")
        print("  python trade_journal.py stats [days] - Show stats for N days")
        print("  python trade_journal.py export [file]- Export to CSV")
        print("  python trade_journal.py log          - Manually log a trade")
