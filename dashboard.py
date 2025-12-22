#!/usr/bin/env python3
"""
Crypto Trading Dashboard
Unified interface for all trading tools
"""
import sys
import os
from pathlib import Path
from core.display import *
from core.api import get_exchange, get_active_positions

def setup_env_file():
    """Check for .env file and create if missing - returns connection status"""
    env_path = Path('.env')
    
    if env_path.exists():
        return True  # Has credentials
    
    clear_screen()
    print_header("FIRST TIME SETUP - KUCOIN API CREDENTIALS", color=YELLOW)
    
    print(f"{BOLD}Welcome to Crypto Trading Dashboard!{RESET}\n")
    print(f"No .env file found. Let's set up your KuCoin API credentials.\n")
    print(f"{CYAN}To get your API credentials:{RESET}")
    print(f"  1. Log in to KuCoin")
    print(f"  2. Go to Account > API Management")
    print(f"  3. Create a new API key with trading permissions")
    print(f"  4. Save your credentials securely\n")
    print(f"{YELLOW}{'─'*75}{RESET}\n")
    print(f"{BOLD}Or skip for now:{RESET}")
    print(f"  • You can explore the dashboard in demo mode")
    print(f"  • Trading features will be unavailable")
    print(f"  • Add credentials later via System Info menu\n")
    print(f"{YELLOW}{'─'*75}{RESET}\n")
    
    # Ask if user wants to set up now or skip
    setup_now = input(f"{CYAN}Set up credentials now? (y/n): {RESET}").strip().lower()
    
    if setup_now != 'y':
        print(f"\n{YELLOW}Skipping credential setup...{RESET}")
        print(f"{CYAN}Dashboard will run in LIMITED MODE{RESET}")
        print(f"\n{BOLD}Available features without credentials:{RESET}")
        print(f"  ✓ View help and documentation")
        print(f"  ✓ View system information")
        print(f"\n{BOLD}Unavailable features (require API):{RESET}")
        print(f"  ✗ Live market scanning")
        print(f"  ✗ Position monitoring")
        print(f"  ✗ Trailing stops")
        print(f"  ✗ Any trading operations")
        input(f"\n{CYAN}Press Enter to continue to dashboard...{RESET}")
        return False  # No credentials
    
    # Prompt for credentials
    api_key = input(f"\n{CYAN}Enter your KUCOIN_API_KEY: {RESET}").strip()
    api_secret = input(f"{CYAN}Enter your KUCOIN_API_SECRET: {RESET}").strip()
    api_passphrase = input(f"{CYAN}Enter your KUCOIN_API_PASSPHRASE: {RESET}").strip()
    
    # Validate inputs
    if not all([api_key, api_secret, api_passphrase]):
        print(f"\n{YELLOW}⚠️  Incomplete credentials - running in LIMITED MODE{RESET}")
        input(f"{CYAN}Press Enter to continue...{RESET}")
        return False  # No credentials
    
    # Create .env file
    try:
        with open('.env', 'w') as f:
            f.write(f"KUCOIN_API_KEY={api_key}\n")
            f.write(f"KUCOIN_API_SECRET={api_secret}\n")
            f.write(f"KUCOIN_API_PASSPHRASE={api_passphrase}\n")
        
        print(f"\n{GREEN}✅ .env file created successfully!{RESET}")
        print(f"{GREEN}Your credentials have been saved securely.{RESET}\n")
        
        # Test connection
        print(f"{CYAN}Testing connection to KuCoin...{RESET}")
        os.environ['KUCOIN_API_KEY'] = api_key
        os.environ['KUCOIN_API_SECRET'] = api_secret
        os.environ['KUCOIN_API_PASSPHRASE'] = api_passphrase
        
        exchange = get_exchange()
        if exchange:
            print(f"{GREEN}✅ Connection successful!{RESET}\n")
            input(f"{CYAN}Press Enter to continue to dashboard...{RESET}")
            return True
        else:
            print(f"\n{YELLOW}⚠️  Credentials saved but connection failed.{RESET}")
            print(f"{YELLOW}Please verify your API credentials are correct.{RESET}")
            print(f"{YELLOW}You can still access limited features.{RESET}\n")
            input(f"{CYAN}Press Enter to continue...{RESET}")
            return False  # Failed connection = limited mode
    
    except Exception as e:
        print(f"\n{RED}❌ Error creating .env file: {e}{RESET}")
        print(f"{YELLOW}Continuing in LIMITED MODE...{RESET}")
        input(f"{CYAN}Press Enter to continue...{RESET}")
        return False

def show_main_menu(has_credentials=False):
    """Display main menu with feature availability"""
    clear_screen()
    print_header("CRYPTO TRADING DASHBOARD", color=CYAN)
    
    if not has_credentials:
        print(f"{YELLOW}⚠️  LIMITED MODE - No API credentials configured{RESET}")
        print(f"{CYAN}   Add credentials via option 8 to unlock trading features{RESET}\n")
    
    lock = f" {YELLOW}[API Required]{RESET}" if not has_credentials else ""
    
    print(f"{BOLD}📊 MARKET ANALYSIS{RESET}")
    print(f"  {CYAN}1{RESET}. Live Opportunity Watcher - Monitor market for trading setups{lock}")
    print(f"  {CYAN}2{RESET}. Institutional Scan - One-time comprehensive market analysis{lock}")
    print(f"  {CYAN}3{RESET}. Analyze Specific Coin - Deep dive on any symbol{lock}")
    
    print(f"\n{BOLD}📈 POSITION MANAGEMENT{RESET}")
    print(f"  {CYAN}4{RESET}. Monitor Position - Track open position with indicators{lock}")
    print(f"  {CYAN}5{RESET}. View All Positions - Quick overview of all open positions{lock}")
    
    print(f"\n{BOLD}🛡️  RISK MANAGEMENT{RESET}")
    print(f"  {CYAN}6{RESET}. Smart Trailing Stop - Dynamic indicator-based trailing stop{lock}")
    print(f"  {CYAN}7{RESET}. Basic Trailing Stop - Simple ATR or % based trailing stop{lock}")
    
    print(f"\n{BOLD}⚙️  SETTINGS & INFO{RESET}")
    print(f"  {CYAN}8{RESET}. System Information - Check connection and environment")
    print(f"  {CYAN}9{RESET}. Help - Usage guide and tips")
    
    print(f"\n  {RED}0{RESET}. Exit")
    
    print(f"\n{CYAN}{'─'*75}{RESET}")

def check_connection():
    """Check API connection"""
    exchange = get_exchange()
    if not exchange:
        print(f"\n{RED}❌ Error: Could not connect to KuCoin{RESET}")
        print(f"{YELLOW}Please check your .env file has valid credentials{RESET}")
        return False
    return True

def show_positions():
    """Show all active positions"""
    clear_screen()
    print_header("ACTIVE POSITIONS", color=GREEN)
    
    positions = get_active_positions()
    
    if not positions:
        print(f"{YELLOW}No active positions found{RESET}\n")
        input(f"\n{CYAN}Press Enter to return to menu...{RESET}")
        return
    
    for i, pos in enumerate(positions, 1):
        side_color = GREEN if pos['side'] == 'LONG' else RED
        pnl_color = GREEN if pos['unrealized_roe'] >= 0 else RED
        
        print(f"{BOLD}[{i}] {pos['symbol'].replace('USDTM', '/USDT')}{RESET}")
        print(f"  Side:      {side_color}{pos['side']}{RESET} {pos['leverage']:.1f}x")
        print(f"  Entry:     {format_price(pos['entry_price'])}")
        print(f"  Current:   {format_price(pos['mark_price'])}")
        print(f"  PNL:       {pnl_color}{format_percent(pos['unrealized_roe'])}{RESET}")
        print(f"  Quantity:  {pos['quantity']} contracts")
        
        liq_color = RED if pos['liquidation_distance'] < 5 else YELLOW if pos['liquidation_distance'] < 10 else GREEN
        print(f"  Liq:       {liq_color}{pos['liquidation_distance']:.1f}% away{RESET}")
        print()
    
    input(f"\n{CYAN}Press Enter to return to menu...{RESET}")

def show_help():
    """Show help information"""
    clear_screen()
    print_header("HELP & USAGE GUIDE", color=MAGENTA)
    
    print(f"{BOLD}🎯 WHEN TO USE EACH TOOL:{RESET}\n")
    
    print(f"{CYAN}Live Opportunity Watcher:{RESET}")
    print(f"  • When: Looking for new trading opportunities")
    print(f"  • Shows: Top 5 coins ranked by signal score (0-100)")
    print(f"  • Updates: Every 60 seconds")
    print(f"  • Alert: When score ≥70 (strong setup)")
    
    print(f"\n{CYAN}Institutional Scan:{RESET}")
    print(f"  • When: Want full market snapshot right now")
    print(f"  • Shows: All 20 major coins with detailed scoring")
    print(f"  • Updates: One-time scan (not live)")
    
    print(f"\n{CYAN}Analyze Specific Coin:{RESET}")
    print(f"  • When: Deep dive on one symbol")
    print(f"  • Shows: All 8 indicators across 3 timeframes")
    print(f"  • Best for: Research before entering")
    
    print(f"\n{CYAN}Monitor Position:{RESET}")
    print(f"  • When: Have open position to track")
    print(f"  • Shows: Live P&L, indicators, alerts")
    print(f"  • Updates: Every 10 seconds")
    
    print(f"\n{CYAN}Smart Trailing Stop:{RESET}")
    print(f"  • When: Want to protect profits dynamically")
    print(f"  • How: Adjusts stop based on 8 indicators")
    print(f"  • Tightens: When reversal signals appear")
    print(f"  • Widens: When trend is strong")
    
    print(f"\n{CYAN}Basic Trailing Stop:{RESET}")
    print(f"  • When: Want simple fixed-distance trailing")
    print(f"  • Options: ATR-based or percentage-based")
    print(f"  • Simpler but less adaptive")
    
    print(f"\n{BOLD}📊 SCORING SYSTEM:{RESET}")
    print(f"  {GREEN}70-100{RESET}: Strong signal - tradeable setup")
    print(f"  {YELLOW}50-69{RESET}:  Neutral - wait for confirmation")
    print(f"  {RED}0-49{RESET}:   Weak - stay out")
    
    print(f"\n{BOLD}⚠️  IMPORTANT NOTES:{RESET}")
    print(f"  • For LONGS: Higher score = better")
    print(f"  • For SHORTS: Lower score = better")
    print(f"  • ADX < 20: Choppy market - avoid trading")
    print(f"  • Volume < 1.0x: Low liquidity - use caution")
    
    input(f"\n{CYAN}Press Enter to return to menu...{RESET}")

def show_system_info():
    """Show system information"""
    clear_screen()
    print_header("SYSTEM INFORMATION", color=BLUE)
    
    # Check connection
    print(f"{BOLD}Connection Status:{RESET}")
    exchange = get_exchange()
    if exchange:
        print(f"  {GREEN}✓ Connected to KuCoin{RESET}")
        
        # Check positions
        positions = get_active_positions()
        print(f"  {GREEN}✓ Futures API working{RESET}")
        print(f"  {CYAN}• Active positions: {len(positions)}{RESET}")
    else:
        print(f"  {RED}✗ Connection failed{RESET}")
        print(f"  {YELLOW}Check .env file credentials{RESET}")
    
    print(f"\n{BOLD}Environment:{RESET}")
    print(f"  API Key:     {GREEN}✓ Configured{RESET}" if os.getenv('KUCOIN_API_KEY') else f"  API Key:     {RED}✗ Missing{RESET}")
    print(f"  API Secret:  {GREEN}✓ Configured{RESET}" if os.getenv('KUCOIN_API_SECRET') else f"  API Secret:  {RED}✗ Missing{RESET}")
    print(f"  Passphrase:  {GREEN}✓ Configured{RESET}" if os.getenv('KUCOIN_API_PASSPHRASE') else f"  Passphrase:  {RED}✗ Missing{RESET}")
    
    print(f"\n{BOLD}Available Tools:{RESET}")
    tools = [
        'Live Opportunity Watcher',
        'Institutional Scanner',
        'Coin Analyzer',
        'Position Monitor',
        'Smart Trailing Stop',
        'Basic Trailing Stop'
    ]
    for tool in tools:
        print(f"  {GREEN}✓{RESET} {tool}")
    
    print(f"\n{BOLD}Indicators Enabled:{RESET}")
    indicators = ['RSI', 'MACD', 'Stochastic RSI', 'ADX', 'ATR', 'Bollinger Bands', 'OBV', 'VWAP']
    print(f"  {', '.join(indicators)}")
    
    input(f"\n{CYAN}Press Enter to return to menu...{RESET}")

def run_opportunity_watcher():
    """Launch opportunity watcher"""
    clear_screen()
    print(f"{CYAN}Launching Live Opportunity Watcher...{RESET}\n")
    os.system('python scripts/opportunity_watcher.py')

def run_institutional_scan():
    """Launch institutional scan"""
    clear_screen()
    print(f"{CYAN}Running Institutional Market Scan...{RESET}\n")
    os.system('python scripts/institutional_scan.py')

def run_coin_analyzer():
    """Launch coin analyzer"""
    clear_screen()
    symbol = input(f"{CYAN}Enter symbol to analyze (e.g., TIA, SOL, XRP): {RESET}").strip().upper()
    if symbol:
        print(f"\n{CYAN}Analyzing {symbol}...{RESET}\n")
        os.system(f'python scripts/universal_monitor.py {symbol}')

def run_position_monitor():
    """Launch position monitor"""
    clear_screen()
    
    positions = get_active_positions()
    if not positions:
        print(f"{YELLOW}No active positions found{RESET}\n")
        input(f"{CYAN}Press Enter to continue...{RESET}")
        return
    
    if len(positions) == 1:
        print(f"{CYAN}Monitoring position: {positions[0]['symbol']}{RESET}\n")
        os.system('python scripts/universal_monitor.py')
    else:
        print(f"{BOLD}Select position to monitor:{RESET}\n")
        for i, pos in enumerate(positions, 1):
            side_color = GREEN if pos['side'] == 'LONG' else RED
            print(f"  {i}. {pos['symbol'].replace('USDTM', '/USDT')} - {side_color}{pos['side']}{RESET}")
        
        print(f"  0. Monitor all (auto-select first)")
        
        choice = input(f"\n{CYAN}Select (0-{len(positions)}): {RESET}").strip()
        
        if choice == '0' or choice == '':
            os.system('python scripts/universal_monitor.py')
        elif choice.isdigit() and 1 <= int(choice) <= len(positions):
            symbol = positions[int(choice)-1]['symbol'].replace('USDTM', '')
            os.system(f'python scripts/universal_monitor.py {symbol}')

def run_smart_trailing_stop():
    """Launch smart trailing stop"""
    clear_screen()
    print(f"{CYAN}Launching Smart Trailing Stop...{RESET}\n")
    os.system('python scripts/smart_trailing_stop.py')

def run_basic_trailing_stop():
    """Launch basic trailing stop"""
    clear_screen()
    print(f"{CYAN}Launching Basic Trailing Stop...{RESET}\n")
    os.system('python scripts/trailing_stop.py')

def main():
    """Main dashboard loop"""
    # First time setup - check for .env file
    has_credentials = setup_env_file()
    
    # Only check connection if we have credentials
    if has_credentials and not check_connection():
        print(f"\n{YELLOW}Connection failed - running in LIMITED MODE{RESET}")
        print(f"{CYAN}You can still access Help and System Info{RESET}")
        input(f"\n{CYAN}Press Enter to continue...{RESET}")
        has_credentials = False  # Treat as no credentials
    
    while True:
        show_main_menu(has_credentials)
        
        choice = input(f"{CYAN}Select option (0-9): {RESET}").strip()
        
        if choice == '0':
            clear_screen()
            print(f"\n{GREEN}Thanks for using Crypto Trading Dashboard!{RESET}\n")
            break
        
        # API-required features (1-7)
        elif choice in ['1', '2', '3', '4', '5', '6', '7']:
            if not has_credentials:
                print(f"\n{RED}❌ This feature requires API credentials{RESET}")
                print(f"{YELLOW}Set up credentials via option 8 (System Information){RESET}")
                input(f"\n{CYAN}Press Enter to continue...{RESET}")
                continue
            
            if choice == '1':
                run_opportunity_watcher()
            elif choice == '2':
                run_institutional_scan()
            elif choice == '3':
                run_coin_analyzer()
            elif choice == '4':
                run_position_monitor()
            elif choice == '5':
                show_positions()
            elif choice == '6':
                run_smart_trailing_stop()
            elif choice == '7':
                run_basic_trailing_stop()
        
        # Non-API features (8-9)
        elif choice == '8':
            show_system_info()
            # Refresh credential status after system info
            if not has_credentials and os.path.exists('.env'):
                has_credentials = check_connection()
        
        elif choice == '9':
            show_help()
        
        else:
            print(f"\n{RED}Invalid option. Please try again.{RESET}")
            input(f"{CYAN}Press Enter to continue...{RESET}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear_screen()
        print(f"\n{YELLOW}Dashboard closed{RESET}\n")
        sys.exit(0)
