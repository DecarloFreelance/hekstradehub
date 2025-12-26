#!/usr/bin/env python3
"""
HekTradeHub - Unified Crypto Trading Dashboard
Professional trading interface for KuCoin Futures
"""
import sys
import os
from dotenv import load_dotenv

load_dotenv()

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
BOLD = '\033[1m'
RESET = '\033[0m'

def check_api_configured():
    """Check if API credentials are configured"""
    if not os.path.exists('.env'):
        return False
    api_key = os.getenv('KUCOIN_API_KEY')
    api_secret = os.getenv('KUCOIN_API_SECRET')
    api_pass = os.getenv('KUCOIN_API_PASSPHRASE')
    return bool(api_key and api_secret and api_pass)

def print_banner():
    """Display main banner"""
    print(f"\n{CYAN}{BOLD}╔══════════════════════════════════════════════════════╗")
    print(f"║           HEK TRADE HUB - CRYPTO ADVISOR             ║")
    print(f"║              KuCoin Futures Trading                  ║")
    print(f"╚══════════════════════════════════════════════════════╝{RESET}\n")

def print_menu():
    """Display main menu with API status"""
    api_ok = check_api_configured()
    status = f"{GREEN}● API Configured{RESET}" if api_ok else f"{RED}● API Not Configured{RESET}"
    
    print(f"{BOLD}┌─ MAIN MENU ─────────────────────────────────────────┐{RESET}")
    print(f"│ Status: {status}                        │")
    print(f"│                                                      │")
    
    # Mark unavailable options if no API
    disabled = "" if api_ok else f" {RED}(needs API){RESET}"
    
    print(f"│  {CYAN}1.{RESET} 📊 Check Positions & Account{disabled}           │")
    print(f"│  {CYAN}2.{RESET} 🔍 Find Trading Opportunities{disabled}         │")
    print(f"│  {CYAN}3.{RESET} 📈 Open LONG Position{disabled}                 │")
    print(f"│  {CYAN}4.{RESET} 📉 Open SHORT Position{disabled}                │")
    print(f"│  {CYAN}5.{RESET} 🎯 Set Stop Loss & Take Profit{disabled}        │")
    print(f"│  {CYAN}6.{RESET} 🔄 Start Auto-Trailing Stop{disabled}           │")
    print(f"│  {CYAN}7.{RESET} 📜 View Trade History{disabled}                 │")
    print(f"│  {CYAN}8.{RESET} 🎯 Quick Scalp Finder{disabled}                 │")
    print(f"│  {CYAN}9.{RESET} 📊 Live Dashboard{disabled}                     │")
    print(f"│                                                      │")
    
    if not api_ok:
        print(f"│  {GREEN}S.{RESET} 🔧 Setup API Credentials (run setup.sh)      │")
        print(f"│  {GREEN}D.{RESET} 📖 View Documentation                         │")
        print(f"│                                                      │")
    
    print(f"│  {YELLOW}0.{RESET} Exit                                          │")
    print(f"│                                                      │")
    print(f"{BOLD}└──────────────────────────────────────────────────────┘{RESET}\n")

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
            choice = input(f"{CYAN}Enter your choice:{RESET} ").strip().upper()
            
            if choice == '0':
                print(f"\n{GREEN}Thank you for using HekTradeHub! Happy trading! 🚀{RESET}\n")
                break
            
            # Non-API options (available without credentials)
            elif choice == 'S' and not api_ok:
                print(f"\n{CYAN}Running setup wizard...{RESET}\n")
                run_shell_script('setup.sh')
                input(f"\n{YELLOW}Press Enter to continue...{RESET}")
                continue
                
            elif choice == 'D' and not api_ok:
                print(f"\n{CYAN}📖 Documentation:{RESET}")
                print(f"  • README: cat README.md")
                print(f"  • Quick Start: cat docs/TRADING_QUICKSTART.md")
                print(f"  • Small Account Guide: cat docs/SMALL_ACCOUNT_GUIDE.md")
                print(f"  • Termux Guide: cat docs/TERMUX_GUIDE.md")
                print(f"  • Contributing: cat CONTRIBUTING.md")
                input(f"\n{YELLOW}Press Enter to continue...{RESET}")
                continue
            
            # API-required options
            elif choice in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
                if not api_ok:
                    print(f"\n{RED}❌ This feature requires API credentials!{RESET}")
                    print(f"\n{YELLOW}Run setup: ./setup.sh or choose option 'S'{RESET}\n")
                    input(f"{YELLOW}Press Enter to continue...{RESET}")
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
                    print(f"\n{YELLOW}Usage: python automation/auto_trailing_stop.py SYMBOL SIDE ENTRY STOP TRAIL_R TRAIL_ATR{RESET}")
                    print(f"{YELLOW}Or use: bash bin/start_auto_trailing.sh{RESET}\n")
                    input(f"{YELLOW}Press Enter to continue...{RESET}")
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
                print(f"\n{RED}Invalid choice. Please try again.{RESET}\n")
                
            input(f"\n{YELLOW}Press Enter to continue...{RESET}")
            print("\033c", end="")  # Clear screen
            
        except KeyboardInterrupt:
            print(f"\n\n{GREEN}Goodbye! 👋{RESET}\n")
            break
        except Exception as e:
            print(f"\n{RED}Error: {e}{RESET}\n")
            input(f"{YELLOW}Press Enter to continue...{RESET}")

if __name__ == '__main__':
    main()
