#!/usr/bin/env python3
"""
Enhanced Opportunity Finder with Multi-Timeframe Analysis and Risk Management
Systematic, thorough, and precise trading signal detection
"""

import ccxt
import pandas as pd
from dotenv import load_dotenv
import os
import sys

# RAM Protection - Critical for scanning multiple symbols
sys.path.insert(0, '/home/hektic/saddynhektic workspace')
try:
    from Tools.resource_manager import check_ram_before_processing
    check_ram_before_processing(min_free_gb=1.5)
except ImportError:
    print("⚠️  Warning: RAM protection not available")
except MemoryError as e:
    print(f"❌ Insufficient RAM: {e}")
    exit(1)

# Add parent directory to path for core imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.risk_manager import RiskManager
from core.timeframe_analyzer import TimeframeAnalyzer
from core.telegram_alerts import TelegramAlert

load_dotenv()

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
MAGENTA = '\033[95m'
BOLD = '\033[1m'
RESET = '\033[0m'


def analyze_opportunity(exchange, symbol, account_balance, send_alerts=False):
    """
    Comprehensive multi-timeframe analysis with risk management.
    
    Args:
        exchange: ccxt exchange instance
        symbol: Trading pair symbol
        account_balance: Account balance for position sizing
        send_alerts: Whether to send Telegram alerts
        
    Returns:
        Dictionary with complete analysis or None
    """
    try:
        # Initialize modules
        tf_analyzer = TimeframeAnalyzer(exchange)
        risk_manager = RiskManager(account_balance)
        telegram = TelegramAlert() if send_alerts else None
        
        # Fetch multi-timeframe data
        print(f"  {symbol:<25} Fetching data...", end='\r')
        mtf_data = tf_analyzer.fetch_multi_timeframe_data(symbol)
        
        # Analyze each timeframe
        analyses = {}
        for tf, df in mtf_data.items():
            if df is not None:
                analyses[tf] = tf_analyzer.analyze_timeframe(df, tf)
        
        if len(analyses) < 3:  # Need at least 3 timeframes
            return None
        
        # Calculate confluence for both directions
        long_confluence = tf_analyzer.calculate_confluence_score(analyses, 'LONG')
        short_confluence = tf_analyzer.calculate_confluence_score(analyses, 'SHORT')
        
        # Determine best direction
        if long_confluence['score'] > short_confluence['score']:
            best_direction = 'LONG'
            confluence = long_confluence
        else:
            best_direction = 'SHORT'
            confluence = short_confluence
        
        # Only proceed if score is decent
        if confluence['score'] < 45:
            return None
        
        # Get entry zone
        entry_zone = tf_analyzer.find_entry_zone(analyses, best_direction)
        
        if not entry_zone.get('valid'):
            return None
        
        # Get confirmation checklist
        checklist = tf_analyzer.get_confirmation_checklist(analyses, best_direction)
        
        # Calculate position sizing
        position_calc = risk_manager.calculate_position_size(
            entry_price=entry_zone['optimal_entry'],
            stop_loss_price=entry_zone['atr_stop_loss'],
            leverage=10,
            side=best_direction
        )
        
        if not position_calc.get('valid'):
            return None
        
        # Calculate take profits
        tp_levels = risk_manager.calculate_take_profits(
            entry_price=entry_zone['optimal_entry'],
            stop_loss_price=entry_zone['atr_stop_loss'],
            side=best_direction,
            num_targets=3
        )
        
        # Validate trade
        validation = risk_manager.validate_trade(
            entry_price=entry_zone['optimal_entry'],
            stop_loss_price=entry_zone['atr_stop_loss'],
            take_profit_price=tp_levels['targets'][0]['price'],
            side=best_direction
        )
        
        # Send alert if configured and score is high
        if telegram and confluence['score'] >= 60:
            telegram.send_opportunity_alert(
                symbol=symbol,
                score=confluence['score'],
                direction=best_direction,
                entry_zone=entry_zone,
                confluence=confluence,
                checklist=checklist
            )
        
        return {
            'symbol': symbol,
            'direction': best_direction,
            'score': confluence['score'],
            'signal': confluence['signal'],
            'analyses': analyses,
            'confluence': confluence,
            'entry_zone': entry_zone,
            'checklist': checklist,
            'position': position_calc,
            'take_profits': tp_levels,
            'validation': validation
        }
        
    except Exception as e:
        print(f"\nError analyzing {symbol}: {e}")
        return None


def display_opportunity(opp):
    """Display opportunity in formatted output."""
    
    symbol_clean = opp['symbol'].replace('/USDT:USDT', '')
    score = opp['score']
    direction = opp['direction']
    signal = opp['signal']
    
    # Color based on score
    if score >= 75:
        score_color = GREEN
        signal_strength = "🔥 STRONG"
    elif score >= 60:
        score_color = YELLOW
        signal_strength = "✅ GOOD"
    elif score >= 50:
        score_color = CYAN
        signal_strength = "⚡ MODERATE"
    else:
        score_color = RESET
        signal_strength = "⚠️  WEAK"
    
    dir_emoji = "🚀" if direction == "LONG" else "🔻"
    
    print(f"\n{BOLD}{score_color}{'='*80}{RESET}")
    print(f"{BOLD}{score_color}{dir_emoji} {symbol_clean} - {direction} {signal_strength}{RESET}")
    print(f"{BOLD}{score_color}{'='*80}{RESET}\n")
    
    # Score breakdown
    print(f"{BOLD}📊 CONFLUENCE SCORE: {score_color}{score:.1f}/100{RESET}\n")
    
    print(f"{BOLD}⏱  TIMEFRAME ANALYSIS:{RESET}")
    for detail in opp['confluence']['timeframe_details']:
        tf = detail['timeframe'].upper()
        trend = detail['trend']
        structure = detail['market_structure']
        tf_score = detail['weighted_score']
        
        trend_color = GREEN if trend == 'BULLISH' else RED if trend == 'BEARISH' else YELLOW
        print(f"  {tf:<6} {trend_color}{trend:<8}{RESET} | {structure:<10} | Score: {tf_score:.1f}")
    
    # Entry zone
    entry = opp['entry_zone']
    print(f"\n{BOLD}💰 ENTRY ZONE:{RESET}")
    print(f"  Current Price:    ${entry['current_price']:.6f}")
    print(f"  {CYAN}Aggressive Entry: ${entry['aggressive_entry']:.6f}{RESET}")
    print(f"  {GREEN}Optimal Entry:    ${entry['optimal_entry']:.6f}{RESET} ⭐")
    print(f"  {YELLOW}Conservative:     ${entry['conservative_entry']:.6f}{RESET}")
    
    # Risk management
    position = opp['position']
    print(f"\n{BOLD}🛡  RISK MANAGEMENT:{RESET}")
    print(f"  Stop Loss:        ${entry['atr_stop_loss']:.6f} ({position['stop_loss_pct']:.2f}%)")
    print(f"  Invalidation:     ${entry['invalidation_level']:.6f}")
    print(f"  ATR:              ${entry['atr']:.6f}")
    
    # Position sizing
    print(f"\n{BOLD}📏 POSITION SIZING:{RESET}")
    print(f"  Contracts:        {position['contracts']}")
    print(f"  Notional Value:   ${position['notional_value']:.2f}")
    print(f"  Required Margin:  ${position['required_margin']:.2f} ({position['margin_pct']:.1f}% of account)")
    print(f"  Risk Amount:      ${position['risk_dollars']:.2f} ({position['risk_pct']:.2f}% of account)")
    print(f"  Leverage:         {position['leverage']}x")
    
    # Take profits
    tps = opp['take_profits']
    print(f"\n{BOLD}🎯 TAKE PROFIT TARGETS:{RESET}")
    for tp in tps['targets']:
        print(f"  TP{tp['level']} ({tp['allocation_pct']:.0f}%):  ${tp['price']:.6f} "
              f"({GREEN}+{tp['profit_pct']:.2f}%{RESET}) | R:R = {tp['rr_ratio']:.1f}")
    
    # Validation
    validation = opp['validation']
    print(f"\n{BOLD}✓ TRADE VALIDATION:{RESET}")
    print(f"  Risk/Reward Ratio: {validation['rr_ratio']:.2f}")
    print(f"  Status: {GREEN if validation['valid'] else RED}{validation['reason']}{RESET}")
    
    # Confirmations
    checklist = opp['checklist']
    pass_rate = checklist['pass_rate']
    passed = checklist['passed']
    total = checklist['total']
    
    print(f"\n{BOLD}✓ CONFIRMATIONS: {passed}/{total} ({pass_rate:.0f}%){RESET}")
    
    # Show passed confirmations
    for item in checklist['checklist']:
        if item['passed']:
            print(f"  {GREEN}✓{RESET} {item['item']}")
    
    # Show failed confirmations (important to know)
    failed = [item for item in checklist['checklist'] if not item['passed']]
    if failed and len(failed) <= 5:
        print(f"\n{YELLOW}  Missing confirmations:{RESET}")
        for item in failed:
            print(f"  {YELLOW}✗{RESET} {item['item']}")
    
    print(f"\n{score_color}{'='*80}{RESET}\n")


def scan_markets(min_score=50, send_alerts=False):
    """
    Scan multiple markets for opportunities.
    
    Args:
        min_score: Minimum score to display (default 50)
        send_alerts: Send Telegram alerts for high-score opportunities
    """
    # Primary exchange (KuCoin Futures)
    exchange = ccxt.kucoinfutures({
        'apiKey': os.getenv('KUCOIN_API_KEY'),
        'secret': os.getenv('KUCOIN_API_SECRET'),
        'password': os.getenv('KUCOIN_API_PASSPHRASE'),
        'enableRateLimit': True,
    })
    
    # Get account balance
    try:
        balance = exchange.fetch_balance()
        account_balance = float(balance['USDT']['free'])
    except:
        account_balance = 10.0  # Default if can't fetch
    
    # Top liquid pairs on KuCoin Futures only
    symbols = [
        'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT',
        'XRP/USDT:USDT', 'BNB/USDT:USDT', 'DOGE/USDT:USDT',
        'ADA/USDT:USDT', 'LINK/USDT:USDT', 'AVAX/USDT:USDT',
        'DOT/USDT:USDT', 'UNI/USDT:USDT', 'ATOM/USDT:USDT',
        'LTC/USDT:USDT', 'APT/USDT:USDT', 'ARB/USDT:USDT',
        'OP/USDT:USDT', 'SUI/USDT:USDT', 'TIA/USDT:USDT',
        'SEI/USDT:USDT'
    ]
    
    print(f"\n{BOLD}{BLUE}{'='*80}{RESET}")
    print(f"{BOLD}{BLUE}{'PROFESSIONAL OPPORTUNITY SCANNER':^80}{RESET}")
    print(f"{BOLD}{BLUE}{'Multi-Timeframe Analysis with Risk Management':^80}{RESET}")
    print(f"{BOLD}{BLUE}{'='*80}{RESET}\n")
    print(f"{CYAN}Account Balance: ${account_balance:.2f}{RESET}")
    print(f"{CYAN}Scanning {len(symbols)} markets...{RESET}\n")
    
    opportunities = []
    
    for i, symbol in enumerate(symbols, 1):
        print(f"  [{i}/{len(symbols)}] {symbol:<25} Analyzing...", end='\r')
        
        opp = analyze_opportunity(exchange, symbol, account_balance, send_alerts)
        
        if opp and opp['score'] >= min_score:
            opportunities.append(opp)
    
    print(" " * 80, end='\r')  # Clear line
    
    if not opportunities:
        print(f"\n{YELLOW}No opportunities found with score >= {min_score}{RESET}")
        print(f"{YELLOW}Try lowering the minimum score threshold.{RESET}\n")
        return
    
    print(f"\n{BOLD}{GREEN}Found {len(opportunities)} opportunities!{RESET}\n")
    
    # Display all opportunities
    for i, opp in enumerate(opportunities, 1):
        print(f"{BOLD}#{i}{RESET}")
        display_opportunity(opp)
        
        # Separator between opportunities
        if i < len(opportunities):
            print(f"\n{BLUE}{'─' * 80}{RESET}\n")
    
    # Summary
    print(f"\n{BOLD}{MAGENTA}{'='*80}{RESET}")
    print(f"{BOLD}{MAGENTA}{'SCAN COMPLETE':^80}{RESET}")
    print(f"{BOLD}{MAGENTA}{'='*80}{RESET}\n")
    
    if opportunities:
        best = opportunities[0]
        print(f"{BOLD}🏆 BEST OPPORTUNITY: {best['symbol'].replace('/USDT:USDT', '')} "
              f"({best['direction']}) - Score: {best['score']:.1f}/100{RESET}")
        
        strong_count = sum(1 for o in opportunities if o['score'] >= 75)
        good_count = sum(1 for o in opportunities if 60 <= o['score'] < 75)
        moderate_count = sum(1 for o in opportunities if 50 <= o['score'] < 60)
        
        print(f"\n{GREEN}🔥 Strong signals:   {strong_count}{RESET}")
        print(f"{YELLOW}✅ Good signals:     {good_count}{RESET}")
        print(f"{CYAN}⚡ Moderate signals: {moderate_count}{RESET}")
    
    print(f"\n{BOLD}{MAGENTA}{'='*80}{RESET}\n")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Professional Trading Opportunity Scanner')
    parser.add_argument('--min-score', type=int, default=50, 
                       help='Minimum score to display (default: 50)')
    parser.add_argument('--alerts', action='store_true',
                       help='Send Telegram alerts for high-score opportunities')
    
    args = parser.parse_args()
    
    scan_markets(min_score=args.min_score, send_alerts=args.alerts)
