#!/usr/bin/env python3
"""
Enhanced Position Manager
Integrates risk management and alerts for active positions
"""

import ccxt
import pandas as pd
from dotenv import load_dotenv
import os
import sys
import time
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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.risk_manager import RiskManager
from core.telegram_alerts import TelegramAlert
from core.indicators import calculate_ema, calculate_rsi, calculate_macd, calculate_atr

load_dotenv()

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
BOLD = '\033[1m'
RESET = '\033[0m'


def monitor_position(exchange, symbol, entry_price, stop_loss, side, contracts, 
                     account_balance, send_alerts=True):
    """
    Monitor an active position and provide management suggestions.
    
    Args:
        exchange: ccxt exchange instance
        symbol: Trading pair
        entry_price: Entry price
        stop_loss: Current stop loss
        side: 'LONG' or 'SHORT'
        contracts: Number of contracts
        account_balance: Account balance
        send_alerts: Send Telegram notifications
    """
    risk_manager = RiskManager(account_balance)
    telegram = TelegramAlert() if send_alerts else None
    
    last_alert_time = 0
    alert_cooldown = 300  # 5 minutes between alerts
    
    print(f"\n{BOLD}{BLUE}{'='*80}{RESET}")
    print(f"{BOLD}{BLUE}{'POSITION MONITOR':^80}{RESET}")
    print(f"{BOLD}{BLUE}{'='*80}{RESET}\n")
    
    print(f"{BOLD}Symbol:{RESET} {symbol}")
    print(f"{BOLD}Side:{RESET} {side}")
    print(f"{BOLD}Entry:{RESET} ${entry_price:.6f}")
    print(f"{BOLD}Stop Loss:{RESET} ${stop_loss:.6f}")
    print(f"{BOLD}Contracts:{RESET} {contracts}")
    
    print(f"\n{CYAN}Monitoring... (Ctrl+C to exit){RESET}\n")
    
    try:
        while True:
            # Fetch current data
            ticker = exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            
            # Fetch OHLCV for indicators
            ohlcv = exchange.fetch_ohlcv(symbol, '15m', limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Calculate P&L
            if side.upper() == 'LONG':
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
                pnl_usd = (current_price - entry_price) * contracts
            else:
                pnl_pct = ((entry_price - current_price) / entry_price) * 100
                pnl_usd = (entry_price - current_price) * contracts
            
            # Get management suggestions
            suggestions_data = risk_manager.suggest_position_adjustments(
                current_price=current_price,
                entry_price=entry_price,
                stop_loss_price=stop_loss,
                side=side
            )
            
            # Calculate indicators
            rsi = calculate_rsi(df['close']).iloc[-1]
            ema_20 = calculate_ema(df['close'], 20).iloc[-1]
            macd_line, signal_line, hist = calculate_macd(df['close'])
            macd_hist = hist.iloc[-1]
            
            # Display current status
            print(f"\r{datetime.now().strftime('%H:%M:%S')} | "
                  f"Price: ${current_price:.6f} | "
                  f"P&L: {GREEN if pnl_pct > 0 else RED}{pnl_pct:+.2f}%{RESET} "
                  f"(${pnl_usd:+.2f}) | "
                  f"RSI: {rsi:.1f} | "
                  f"Suggestions: {len(suggestions_data['suggestions'])}", 
                  end='', flush=True)
            
            # Check for important suggestions
            current_time = time.time()
            if suggestions_data['suggestions'] and (current_time - last_alert_time) > alert_cooldown:
                print(f"\n\n{YELLOW}{'='*80}{RESET}")
                print(f"{BOLD}{YELLOW}⚠️  POSITION MANAGEMENT SUGGESTIONS{RESET}\n")
                
                suggestion_text = ""
                for sugg in suggestions_data['suggestions']:
                    action = sugg['action']
                    reason = sugg['reason']
                    
                    if action == 'MOVE_TO_BREAKEVEN':
                        print(f"{GREEN}✓ {reason}{RESET}")
                        print(f"  New Stop: ${sugg['new_stop']:.6f}\n")
                        suggestion_text += f"• {reason}\n"
                        
                    elif action == 'TRAIL_STOP':
                        print(f"{GREEN}✓ {reason}{RESET}")
                        print(f"  New Stop: ${sugg['new_stop']:.6f}\n")
                        suggestion_text += f"• {reason}\n"
                        
                    elif action == 'TAKE_PARTIAL_PROFIT':
                        print(f"{CYAN}💰 {reason}{RESET}")
                        print(f"  Close: {sugg['percentage']}% of position\n")
                        suggestion_text += f"• {reason}\n"
                
                print(f"{YELLOW}{'='*80}{RESET}\n")
                
                # Send alert
                if telegram and suggestion_text:
                    telegram.send_position_update(
                        symbol=symbol,
                        side=side,
                        entry_price=entry_price,
                        current_price=current_price,
                        pnl_pct=pnl_pct,
                        pnl_usd=pnl_usd,
                        suggestion=suggestion_text
                    )
                    last_alert_time = current_time
            
            # Check if stop loss hit
            if side.upper() == 'LONG' and current_price <= stop_loss:
                print(f"\n\n{RED}{BOLD}🛑 STOP LOSS HIT!{RESET}")
                print(f"Position should be closed at ${current_price:.6f}")
                if telegram:
                    telegram.send_risk_alert(
                        alert_type="STOP LOSS HIT",
                        details=f"{symbol} {side} position hit stop loss at ${current_price:.6f}\nP&L: {pnl_pct:+.2f}%"
                    )
                break
                
            elif side.upper() == 'SHORT' and current_price >= stop_loss:
                print(f"\n\n{RED}{BOLD}🛑 STOP LOSS HIT!{RESET}")
                print(f"Position should be closed at ${current_price:.6f}")
                if telegram:
                    telegram.send_risk_alert(
                        alert_type="STOP LOSS HIT",
                        details=f"{symbol} {side} position hit stop loss at ${current_price:.6f}\nP&L: {pnl_pct:+.2f}%"
                    )
                break
            
            time.sleep(5)  # Update every 5 seconds
            
    except KeyboardInterrupt:
        print(f"\n\n{CYAN}Monitoring stopped.{RESET}")
        print(f"\n{BOLD}Final Status:{RESET}")
        print(f"  Current Price: ${current_price:.6f}")
        print(f"  P&L: {pnl_pct:+.2f}% (${pnl_usd:+.2f})\n")


def open_position_with_risk_management(symbol, direction, leverage=10, send_alerts=True, balance=None):
    """
    Open a position with professional risk management.
    
    Args:
        symbol: Trading pair
        direction: 'LONG' or 'SHORT'
        leverage: Leverage to use
        send_alerts: Send Telegram notifications
        balance: Account balance (if None, will try to fetch from API)
    """
    exchange = ccxt.kucoinfutures({
        'apiKey': os.getenv('KUCOIN_API_KEY'),
        'secret': os.getenv('KUCOIN_API_SECRET'),
        'password': os.getenv('KUCOIN_API_PASSPHRASE'),
        'enableRateLimit': True,
    })
    
    telegram = TelegramAlert() if send_alerts else None
    
    # Get account balance
    if balance is not None:
        account_balance = float(balance)
        print(f"{CYAN}Using provided balance: ${account_balance:.2f}{RESET}\n")
    else:
        try:
            balance_data = exchange.fetch_balance()
            account_balance = float(balance_data['USDT']['free'])
        except Exception as e:
            print(f"{YELLOW}⚠️  Cannot fetch balance (geo-blocked). Using default $10{RESET}")
            print(f"{YELLOW}    Use --balance parameter to specify your actual balance{RESET}\n")
            account_balance = 10.0
    
    # Get current price
    ticker = exchange.fetch_ticker(symbol)
    current_price = ticker['last']
    
    # Get OHLCV for ATR-based stop
    ohlcv = exchange.fetch_ohlcv(symbol, '15m', limit=100)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    # Initialize risk manager
    risk_manager = RiskManager(account_balance, max_risk_per_trade_pct=2.0)
    
    # Calculate ATR-based stop loss
    stop_loss = risk_manager.calculate_atr_stop_loss(
        df=df,
        entry_price=current_price,
        atr_multiplier=1.5,
        side=direction
    )
    
    # Calculate position size
    position = risk_manager.calculate_position_size(
        entry_price=current_price,
        stop_loss_price=stop_loss,
        leverage=leverage,
        side=direction
    )
    
    if not position.get('valid'):
        print(f"{RED}Cannot calculate position: {position.get('error')}{RESET}")
        return
    
    # Calculate take profits
    tp_levels = risk_manager.calculate_take_profits(
        entry_price=current_price,
        stop_loss_price=stop_loss,
        side=direction,
        num_targets=3
    )
    
    # Display plan
    print(f"\n{BOLD}{BLUE}{'='*80}{RESET}")
    print(f"{BOLD}{BLUE}{'POSITION PLAN':^80}{RESET}")
    print(f"{BOLD}{BLUE}{'='*80}{RESET}\n")
    
    print(f"{BOLD}Symbol:{RESET} {symbol}")
    print(f"{BOLD}Direction:{RESET} {direction}")
    print(f"{BOLD}Account Balance:{RESET} ${account_balance:.2f}")
    
    print(f"\n{BOLD}Entry:{RESET}")
    print(f"  Price: ${current_price:.6f}")
    print(f"  Contracts: {position['contracts']}")
    print(f"  Notional: ${position['notional_value']:.2f}")
    print(f"  Margin: ${position['required_margin']:.2f} ({position['margin_pct']:.1f}%)")
    print(f"  Leverage: {leverage}x")
    
    print(f"\n{BOLD}Risk:{RESET}")
    print(f"  Stop Loss: ${stop_loss:.6f} ({position['stop_loss_pct']:.2f}%)")
    print(f"  Risk Amount: ${position['risk_dollars']:.2f} ({position['risk_pct']:.2f}%)")
    
    print(f"\n{BOLD}Take Profits:{RESET}")
    for tp in tp_levels['targets']:
        print(f"  TP{tp['level']} ({tp['allocation_pct']:.0f}%): ${tp['price']:.6f} "
              f"(+{tp['profit_pct']:.2f}%) R:R={tp['rr_ratio']:.1f}")
    
    print(f"\n{BOLD}{YELLOW}{'='*80}{RESET}")
    response = input(f"{YELLOW}Confirm position? (yes/no): {RESET}")
    
    if response.lower() != 'yes':
        print(f"{RED}Position cancelled.{RESET}")
        return
    
    # Send alert if configured
    if telegram:
        telegram.send_position_alert(
            action='OPENED',
            symbol=symbol,
            side=direction,
            contracts=position['contracts'],
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profits=tp_levels['targets'],
            leverage=leverage,
            risk_pct=position['risk_pct']
        )
    
    print(f"\n{GREEN}{'='*80}{RESET}")
    print(f"{BOLD}{GREEN}✅ POSITION PLAN READY - EXECUTE MANUALLY ON KUCOIN{RESET}")
    print(f"{GREEN}{'='*80}{RESET}\n")
    
    print(f"{BOLD}Manual Execution Steps:{RESET}")
    print(f"1. Go to KuCoin Futures: https://www.kucoin.com/futures/trade/{symbol.replace('/USDT:USDT', 'USDTM')}")
    print(f"2. Select {direction} position")
    print(f"3. Set leverage: {leverage}x")
    print(f"4. Enter {position['contracts']} contracts")
    print(f"5. Set stop loss: ${stop_loss:.6f}")
    print(f"6. Set take profits:")
    for tp in tp_levels['targets']:
        print(f"   - TP{tp['level']}: ${tp['price']:.6f}")
    
    print(f"\n{CYAN}After opening, monitor with:{RESET}")
    print(f"python scripts/enhanced_position_manager.py --monitor --symbol {symbol} "
          f"--entry {current_price:.6f} --stop {stop_loss:.6f} --side {direction} "
          f"--contracts {position['contracts']} --balance {account_balance}\n")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Position Manager')
    parser.add_argument('--monitor', action='store_true', help='Monitor existing position')
    parser.add_argument('--open', action='store_true', help='Plan new position')
    parser.add_argument('--symbol', type=str, default='BTC/USDT:USDT', help='Trading pair')
    parser.add_argument('--entry', type=float, help='Entry price (for monitoring)')
    parser.add_argument('--stop', type=float, help='Stop loss price (for monitoring)')
    parser.add_argument('--side', type=str, choices=['LONG', 'SHORT'], help='Position side')
    parser.add_argument('--contracts', type=int, help='Number of contracts (for monitoring)')
    parser.add_argument('--leverage', type=int, default=10, help='Leverage (default: 10)')
    parser.add_argument('--balance', type=float, help='Account balance in USDT (required if geo-blocked)')
    parser.add_argument('--no-alerts', action='store_true', help='Disable Telegram alerts')
    
    args = parser.parse_args()
    
    exchange = ccxt.kucoinfutures({
        'apiKey': os.getenv('KUCOIN_API_KEY'),
        'secret': os.getenv('KUCOIN_API_SECRET'),
        'password': os.getenv('KUCOIN_API_PASSPHRASE'),
        'enableRateLimit': True,
    })
    
    if args.monitor:
        if not all([args.entry, args.stop, args.side, args.contracts]):
            print(f"{RED}Error: --monitor requires --entry, --stop, --side, --contracts{RESET}")
            sys.exit(1)
        
        balance = exchange.fetch_balance()
        account_balance = float(balance['USDT']['free']) if args.balance is None else args.balance
        
        monitor_position(
            exchange=exchange,
            symbol=args.symbol,
            entry_price=args.entry,
            stop_loss=args.stop,
            side=args.side,
            contracts=args.contracts,
            account_balance=account_balance,
            send_alerts=not args.no_alerts
        )
        
    elif args.open:
        if not args.side:
            print(f"{RED}Error: --open requires --side (LONG or SHORT){RESET}")
            sys.exit(1)
        
        open_position_with_risk_management(
            symbol=args.symbol,
            direction=args.side,
            leverage=args.leverage,
            send_alerts=not args.no_alerts
        )
        
    else:
        print(f"{YELLOW}Use --monitor to monitor a position or --open to plan a new position{RESET}")
        print(f"\nExamples:")
        print(f"  Plan: python scripts/enhanced_position_manager.py --open --symbol BTC/USDT:USDT --side LONG")
        print(f"  Monitor: python scripts/enhanced_position_manager.py --monitor --symbol BTC/USDT:USDT --entry 42000 --stop 41000 --side LONG --contracts 10\n")
