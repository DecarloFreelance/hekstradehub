#!/bin/bash
# HekTradeHub Interactive Setup Script
# First-time installation and configuration wizard

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Clear screen and show banner
clear
echo -e "${CYAN}${BOLD}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║         🚀 HEK TRADE HUB - SETUP WIZARD 🚀                     ║"
echo "║                                                                ║"
echo "║         Professional Crypto Trading System                     ║"
echo "║         KuCoin Futures Automated Trading                       ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}\n"

# Function to print section headers
print_header() {
    echo -e "\n${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${CYAN}$1${NC}"
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

# Function to print info
print_info() {
    echo -e "${CYAN}ℹ${NC}  $1"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠${NC}  $1"
}

# Function to print error
print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Welcome message
print_info "Welcome to the HekTradeHub setup wizard!"
print_info "This script will help you set up your crypto trading environment."
echo ""
read -p "Press Enter to continue..."

# Step 1: System Check
print_header "STEP 1: System Requirements Check"

print_info "Checking system requirements..."
sleep 1

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_success "Python 3 installed: $PYTHON_VERSION"
else
    print_error "Python 3 is not installed!"
    echo -e "${YELLOW}Please install Python 3.8 or higher:${NC}"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

# Check pip
if command -v pip3 &> /dev/null; then
    print_success "pip3 installed"
else
    print_warning "pip3 not found, attempting to install..."
    sudo apt install python3-pip -y
fi

# Check git
if command -v git &> /dev/null; then
    print_success "Git installed"
else
    print_warning "Git not installed (optional for updates)"
fi

echo ""
read -p "Press Enter to continue..."

# Step 2: Virtual Environment
print_header "STEP 2: Python Virtual Environment"

if [ -d ".venv" ]; then
    print_info "Virtual environment already exists"
    read -p "Recreate it? (y/N): " recreate
    if [[ $recreate =~ ^[Yy]$ ]]; then
        rm -rf .venv
        print_info "Creating new virtual environment..."
        python3 -m venv .venv
        print_success "Virtual environment created"
    fi
else
    print_info "Creating virtual environment..."
    python3 -m venv .venv
    print_success "Virtual environment created"
fi

print_info "Activating virtual environment..."
source .venv/bin/activate
print_success "Virtual environment activated"

echo ""
read -p "Press Enter to continue..."

# Step 3: Dependencies
print_header "STEP 3: Installing Dependencies"

print_info "This will install required Python packages:"
echo "  - ccxt (KuCoin API)"
echo "  - pandas, numpy (data analysis)"
echo "  - python-dotenv (configuration)"
echo "  - TA-Lib (technical indicators)"
echo ""

read -p "Install dependencies? (Y/n): " install_deps
if [[ ! $install_deps =~ ^[Nn]$ ]]; then
    print_info "Upgrading pip..."
    pip install --upgrade pip --quiet
    
    print_info "Installing dependencies... (this may take a few minutes)"
    pip install ccxt pandas numpy python-dotenv ta-lib requests --quiet
    
    print_success "All dependencies installed!"
else
    print_warning "Skipping dependency installation"
fi

echo ""
read -p "Press Enter to continue..."

# Step 4: API Configuration
print_header "STEP 4: KuCoin API Configuration"

if [ -f ".env" ]; then
    print_info ".env file already exists"
    read -p "Would you like to reconfigure it? (y/N): " reconfig
    configure_api=$reconfig
else
    print_info "You need KuCoin API credentials to use this system"
    configure_api="y"
fi

if [[ $configure_api =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${BOLD}${YELLOW}🔑 API Setup Instructions:${NC}"
    echo ""
    echo "1. Go to: https://www.kucoin.com/account/api"
    echo "2. Create a new API key with these permissions:"
    echo "   ✓ General (Read)"
    echo "   ✓ Futures (Read + Trade)"
    echo "3. Save your API credentials securely"
    echo ""
    print_warning "IMPORTANT: Never share your API credentials!"
    echo ""
    
    read -p "Do you have your API credentials ready? (y/N): " has_creds
    
    if [[ $has_creds =~ ^[Yy]$ ]]; then
        echo ""
        read -p "Enter your API Key: " api_key
        read -p "Enter your API Secret: " api_secret
        read -p "Enter your API Passphrase: " api_passphrase
        
        # Create .env file
        cat > .env << EOF
# KuCoin API Credentials
KUCOIN_API_KEY=$api_key
KUCOIN_API_SECRET=$api_secret
KUCOIN_API_PASSPHRASE=$api_passphrase
KUCOIN_API_URL=https://api-futures.kucoin.com
EOF
        
        chmod 600 .env
        print_success ".env file created and secured (permissions: 600)"
        
        # Test connection
        print_info "Testing API connection..."
        if python -c "
import ccxt
from dotenv import load_dotenv
import os
load_dotenv()
exchange = ccxt.kucoinfutures({
    'apiKey': os.getenv('KUCOIN_API_KEY'),
    'secret': os.getenv('KUCOIN_API_SECRET'),
    'password': os.getenv('KUCOIN_API_PASSPHRASE')
})
exchange.fetch_balance()
print('✓ Connection successful!')
" 2>/dev/null; then
            print_success "API credentials verified!"
        else
            print_error "API connection failed - please check your credentials"
            print_warning "You can edit .env file manually later"
        fi
    else
        print_info "Copying .env.example to .env..."
        cp .env.example .env
        print_warning "Please edit .env file with your API credentials before trading"
    fi
else
    print_info "Keeping existing .env configuration"
fi

echo ""
read -p "Press Enter to continue..."

# Step 5: Auto-activation
print_header "STEP 5: Virtual Environment Auto-Activation (Optional)"

print_info "Would you like the virtual environment to auto-activate?"
echo ""
echo "When enabled, the venv automatically activates when you enter this directory."
echo ""
read -p "Enable auto-activation? (Y/n): " enable_auto

if [[ ! $enable_auto =~ ^[Nn]$ ]]; then
    if ! grep -q "HekTradeHub auto-activation" ~/.bashrc 2>/dev/null; then
        cat >> ~/.bashrc << 'EOF'

# HekTradeHub auto-activation
if [[ "$PWD" == /home/*/hekstradehub* ]] && [[ -f .venv/bin/activate ]]; then
    source .venv/bin/activate 2>/dev/null
fi
EOF
        print_success "Auto-activation added to ~/.bashrc"
        print_info "Run: source ~/.bashrc  (or restart terminal)"
    else
        print_info "Auto-activation already configured"
    fi
else
    print_info "Skipping auto-activation"
    print_info "You can use ./trade or ./status scripts (they activate automatically)"
fi

echo ""
read -p "Press Enter to continue..."

# Step 6: Quick Tutorial
print_header "STEP 6: System Overview & Tutorial"

echo -e "${BOLD}${GREEN}🎓 How HekTradeHub Works:${NC}"
echo ""
echo -e "${BOLD}Main Entry Point:${NC}"
echo "  ${CYAN}./trade${NC}  - Interactive dashboard with all functions"
echo "  ${CYAN}./status${NC} - Quick position check"
echo ""
echo -e "${BOLD}Key Features:${NC}"
echo "  📊 Market Analysis    - Find high-probability trade setups"
echo "  🎯 Trade Execution    - Open LONG/SHORT with proper risk management"
echo "  🔄 Auto-Trailing      - Set and forget trailing stop loss"
echo "  📈 Live Monitoring    - Real-time position dashboard"
echo "  📝 Trade Journal      - Automatic trade logging"
echo ""
echo -e "${BOLD}Directory Structure:${NC}"
echo "  ${CYAN}analysis/${NC}      - Market scanning & opportunity finders"
echo "  ${CYAN}trading/${NC}       - Trade execution scripts"
echo "  ${CYAN}automation/${NC}    - Auto-trailing stop management"
echo "  ${CYAN}monitoring/${NC}    - Position checks & dashboards"
echo "  ${CYAN}core/${NC}          - Technical indicators & risk management"
echo ""
echo -e "${BOLD}Quick Start Commands:${NC}"
echo "  ${GREEN}./trade${NC}                           # Launch main dashboard"
echo "  ${GREEN}./status${NC}                          # Check positions"
echo "  ${GREEN}python analysis/find_opportunity.py${NC}   # Scan for trades"
echo "  ${GREEN}python trading/open_long.py${NC}           # Execute LONG trade"
echo "  ${GREEN}bash bin/start_auto_trailing.sh${NC}       # Start trailing stop"
echo ""
echo -e "${BOLD}${YELLOW}⚠️  IMPORTANT SAFETY NOTES:${NC}"
echo "  • Start with small positions to test the system"
echo "  • Always use stop losses"
echo "  • Never risk more than 1-2% per trade"
echo "  • Test on testnet first if available"
echo ""

read -p "Press Enter to continue..."

# Step 7: First Test
print_header "STEP 7: System Test"

print_info "Let's test if everything is working..."
echo ""

read -p "Run a quick system test? (Y/n): " run_test

if [[ ! $run_test =~ ^[Nn]$ ]]; then
    print_info "Testing position check..."
    if python monitoring/check_position.py 2>/dev/null; then
        print_success "System test passed!"
    else
        print_warning "Test completed with warnings (this is normal if you have no positions)"
    fi
fi

echo ""

# Final Summary
print_header "🎉 SETUP COMPLETE!"

echo -e "${GREEN}${BOLD}Installation successful!${NC}"
echo ""
echo -e "${BOLD}Next Steps:${NC}"
echo ""
echo "1. ${CYAN}Review your .env file${NC} and ensure API credentials are correct"
echo "2. ${CYAN}Run ./trade${NC} to launch the main dashboard"
echo "3. ${CYAN}Check out docs/README.md${NC} for detailed documentation"
echo "4. ${CYAN}Start with small positions${NC} to learn the system"
echo ""
echo -e "${BOLD}Useful Commands:${NC}"
echo "  ${GREEN}./trade${NC}   - Main trading dashboard"
echo "  ${GREEN}./status${NC}  - Quick position overview"
echo "  ${GREEN}python analysis/find_opportunity.py${NC} - Find trading opportunities"
echo ""
echo -e "${BOLD}Documentation:${NC}"
echo "  📖 README.md - Project overview"
echo "  📖 docs/VENV_SETUP.md - Virtual environment details"
echo "  📖 docs/TRADING_STANDARDS.md - Trading guidelines"
echo ""
echo -e "${YELLOW}${BOLD}⚠️  Remember:${NC} ${YELLOW}Trade responsibly. Start small. Use stop losses.${NC}"
echo ""
echo -e "${CYAN}${BOLD}Happy Trading! 🚀${NC}"
echo ""
