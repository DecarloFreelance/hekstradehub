#!/usr/bin/env python3
"""
HekTradeHub - Unified Crypto Trading Dashboard
Professional trading interface for KuCoin Futures
"""
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Modern color palette
PURPLE = '\033[95m'
BLUE = '\033[94m'
CYAN = '\033[96m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
ORANGE = '\033[38;5;208m'
PINK = '\033[38;5;213m'
LIME = '\033[38;5;154m'
TEAL = '\033[38;5;51m'
LAVENDER = '\033[38;5;183m'

# Styles
BOLD = '\033[1m'
DIM = '\033[2m'
ITALIC = '\033[3m'
UNDERLINE = '\033[4m'
RESET = '\033[0m'

# Gradient colors for banner
GRAD1 = '\033[38;5;51m'   # Bright cyan
GRAD2 = '\033[38;5;87m'   # Light cyan
GRAD3 = '\033[38;5;123m'  # Sky blue
GRAD4 = '\033[38;5;159m'  # Pale blue

def check_api_configured():
    """Check if API credentials are configured"""
    if not os.path.exists('.env'):
        return False
    api_key = os.getenv('KUCOIN_API_KEY')
    api_secret = os.getenv('KUCOIN_API_SECRET')
    api_pass = os.getenv('KUCOIN_API_PASSPHRASE')
    return bool(api_key and api_secret and api_pass)

def print_banner():
    """Display modern gradient banner"""
    print(f"\n{GRAD1}{'═' * 70}{RESET}")
    print(f"{GRAD1}║{RESET}{BOLD}{TEAL}                    🚀 HEK TRADE HUB 🚀                        {RESET}{GRAD1}║{RESET}")
    print(f"{GRAD2}║{RESET}          {LAVENDER}Professional Crypto Trading System{RESET}                  {GRAD2}║{RESET}")
    print(f"{GRAD3}║{RESET}            {DIM}Powered by KuCoin Futures API{RESET}                   {GRAD3}║{RESET}")
    print(f"{GRAD4}{'═' * 70}{RESET}\n")

def print_menu():
    """Display modern colorful menu with API status"""
    api_ok = check_api_configured()
    
    # Status badge
    if api_ok:
        status_badge = f"{BOLD}{GREEN}✓ CONNECTED{RESET}"
        status_icon = f"{GREEN}●{RESET}"
    else:
        status_badge = f"{BOLD}{RED}✗ NOT CONFIGURED{RESET}"
        status_icon = f"{RED}●{RESET}"
    
    # Header
    print(f"{PURPLE}╭{'─' * 68}╮{RESET}")
    print(f"{PURPLE}│{RESET} {BOLD}STATUS:{RESET} {status_icon} {status_badge}{' ' * (54 - len('STATUS:  NOT CONFIGURED'))}│")
    print(f"{PURPLE}├{'─' * 68}┤{RESET}")
    
    # Menu sections
    print(f"{PURPLE}│{RESET}  {BOLD}{TEAL}📊 MONITORING{RESET}{' ' * 54}│")
    
    disabled = f" {DIM}{RED}[API Required]{RESET}" if not api_ok else ""
    
    print(f"{PURPLE}│{RESET}   {LIME}1{RESET} → Check Positions & Account{disabled}{' ' * (33 - len(disabled))}│")
    print(f"{PURPLE}│{RESET}   {LIME}7{RESET} → View Trade History{disabled}{' ' * (40 - len(disabled))}│")
    print(f"{PURPLE}│{RESET}   {LIME}9{RESET} → Live Dashboard{disabled}{' ' * (43 - len(disabled))}│")
    print(f"{PURPLE}│{RESET}{' ' * 68}│")
    
    print(f"{PURPLE}│{RESET}  {BOLD}{CYAN}🔍 ANALYSIS{RESET}{' ' * 56}│")
    print(f"{PURPLE}│{RESET}   {LIME}2{RESET} → Find Trading Opportunities{disabled}{' ' * (31 - len(disabled))}│")
    print(f"{PURPLE}│{RESET}   {LIME}8{RESET} → Quick Scalp Finder{disabled}{' ' * (39 - len(disabled))}│")
    print(f"{PURPLE}│{RESET}{' ' * 68}│")
    
    print(f"{PURPLE}│{RESET}  {BOLD}{ORANGE}📈 TRADING{RESET}{' ' * 57}│")
    print(f"{PURPLE}│{RESET}   {LIME}3{RESET} → Open LONG Position{disabled}{' ' * (39 - len(disabled))}│")
    print(f"{PURPLE}│{RESET}   {LIME}4{RESET} → Open SHORT Position{disabled}{' ' * (38 - len(disabled))}│")
    print(f"{PURPLE}│{RESET}   {LIME}5{RESET} → Set Stop Loss & Take Profit{disabled}{' ' * (30 - len(disabled))}│")
    print(f"{PURPLE}│{RESET}   {LIME}6{RESET} → Start Auto-Trailing Stop{disabled}{' ' * (33 - len(disabled))}│")
    print(f"{PURPLE}│{RESET}{' ' * 68}│")
    
    # Additional options when not configured
    if not api_ok:
        print(f"{PURPLE}│{RESET}  {BOLD}{YELLOW}⚙️  SETUP{RESET}{' ' * 59}│")
        print(f"{PURPLE}│{RESET}   {GREEN}S{RESET} → Setup API Credentials                                     │")
        print(f"{PURPLE}│{RESET}   {GREEN}D{RESET} → View Documentation                                        │")
        print(f"{PURPLE}│{RESET}{' ' * 68}│")
    
    # Footer
    print(f"{PURPLE}│{RESET}   {YELLOW}0{RESET} → Exit Application{' ' * 45}│")
    print(f"{PURPLE}╰{'─' * 68}╯{RESET}\n")

def run_script(script_path):
    """Run a Python script"""
    import subprocess
    python_path = os.path.join(os.path.dirname(__file__), '.venv', 'bin', 'python')
    result = subprocess.run([python_path, script_path])
    return result.returncode

def run_shell_script(script_path):
    """Run a shell script"""
    import subprocess
    # Scripts are now in bin/
    script_path = os.path.join('bin', script_path)
    result = subprocess.run(['bash', script_path])
    return result.returncode

def main():
    """Main trader dashboard"""
    while True:
        print_banner()
        print_menu()
        
        api_ok = check_api_configured()
        
        try:
            choice = input(f"{BOLD}{TEAL}┌─[{PINK}HekTradeHub{TEAL}]─[{LIME}Select Option{TEAL}]{RESET}\n{BOLD}{TEAL}└─▶{RESET} ").strip().upper()
            
            if choice == '0':
                print(f"\n{GRAD1}{'═' * 70}{RESET}")
                print(f"{BOLD}{TEAL}  Thank you for using HekTradeHub!{RESET}")
                print(f"{LAVENDER}  Happy trading and may the profits be with you! 🚀{RESET}")
                print(f"{GRAD4}{'═' * 70}{RESET}\n")
                break
            
            # Non-API options (available without credentials)
            elif choice == 'S' and not api_ok:
                print(f"\n{CYAN}{'─' * 70}{RESET}")
                print(f"{BOLD}{TEAL}🔧 Launching Setup Wizard...{RESET}")
                print(f"{CYAN}{'─' * 70}{RESET}\n")
                run_shell_script('setup.sh')
                input(f"\n{YELLOW}⏎ Press Enter to continue...{RESET}")
                continue
                
            elif choice == 'D' and not api_ok:
                print(f"\n{CYAN}{'─' * 70}{RESET}")
                print(f"{BOLD}{TEAL}📖 Documentation Resources:{RESET}\n")
                print(f"{LIME}  •{RESET} {BOLD}README:{RESET} cat README.md")
                print(f"{LIME}  •{RESET} {BOLD}Quick Start:{RESET} cat docs/TRADING_QUICKSTART.md")
                print(f"{LIME}  •{RESET} {BOLD}Small Account Guide:{RESET} cat docs/SMALL_ACCOUNT_GUIDE.md")
                print(f"{LIME}  •{RESET} {BOLD}Termux Guide:{RESET} cat docs/TERMUX_GUIDE.md")
                print(f"{LIME}  •{RESET} {BOLD}Contributing:{RESET} cat CONTRIBUTING.md")
                print(f"\n{CYAN}{'─' * 70}{RESET}")
                input(f"\n{YELLOW}⏎ Press Enter to continue...{RESET}")
                continue
            
            # API-required options
            elif choice in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
                if not api_ok:
                    print(f"\n{RED}{'─' * 70}{RESET}")
                    print(f"{BOLD}{RED}  ❌ API Credentials Required{RESET}")
                    print(f"{YELLOW}  This feature needs KuCoin API access.{RESET}")
                    print(f"\n{LIME}  → Run setup: {BOLD}./setup.sh{RESET} {LIME}or choose option {BOLD}'S'{RESET}")
                    print(f"{RED}{'─' * 70}{RESET}")
                    input(f"\n{YELLOW}⏎ Press Enter to continue...{RESET}")
                    continue
                    
                if choice == '1':
                    # Check positions
                    run_script('monitoring/check_position.py')
                    
                elif choice == '2':
                    # Find opportunities
                    run_script('analysis/find_opportunity.py')
                    
                elif choice == '3':
                    # Open LONG
                    run_script('trading/open_long.py')
                    
                elif choice == '4':
                    # Open SHORT
                    run_script('trading/open_short.py')
                    
                elif choice == '5':
                    # Set SL/TP
                    run_script('trading/set_stop_and_tp.py')
                    
                elif choice == '6':
                    # Auto-trailing
                    print(f"\n{CYAN}{'─' * 70}{RESET}")
                    print(f"{BOLD}{ORANGE}🔄 Auto-Trailing Stop Configuration{RESET}\n")
                    print(f"{YELLOW}Usage:{RESET}")
                    print(f"  {DIM}python automation/auto_trailing_stop.py SYMBOL SIDE ENTRY STOP TRAIL_R TRAIL_ATR{RESET}")
                    print(f"\n{YELLOW}Quick Start:{RESET}")
                    print(f"  {LIME}bash bin/start_auto_trailing.sh{RESET}")
                    print(f"\n{CYAN}{'─' * 70}{RESET}")
                    input(f"\n{YELLOW}⏎ Press Enter to continue...{RESET}")
                    continue
                    
                elif choice == '7':
                    # Trade history
                    run_script('monitoring/check_trade_history.py')
                    
                elif choice == '8':
                    # Quick scalp finder
                    run_script('analysis/quick_scalp_finder.py')
                    
                elif choice == '9':
                    # Live dashboard
                    run_shell_script('launch_dashboard.sh')
                
            else:
                print(f"\n{RED}❌ Invalid choice. Please select a valid option.{RESET}\n")
                
            input(f"\n{DIM}Press Enter to continue...{RESET}")
            print("\033c", end="")  # Clear screen
            
        except KeyboardInterrupt:
            print(f"\n\n{GRAD1}{'═' * 70}{RESET}")
            print(f"{BOLD}{TEAL}  Interrupted by user{RESET}")
            print(f"{LAVENDER}  Goodbye! 👋{RESET}")
            print(f"{GRAD4}{'═' * 70}{RESET}\n")
            break
        except Exception as e:
            print(f"\n{RED}{'─' * 70}{RESET}")
            print(f"{BOLD}{RED}  ⚠️  Error:{RESET} {e}")
            print(f"{RED}{'─' * 70}{RESET}")
            input(f"\n{YELLOW}⏎ Press Enter to continue...{RESET}")

if __name__ == '__main__':
    main()
