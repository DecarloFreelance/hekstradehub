#!/data/data/com.termux/files/usr/bin/bash
# HekTradeHub Termux Setup Script
# Installation wizard for Android/Termux users

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Clear screen and show banner
clear
echo -e "${CYAN}${BOLD}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║         📱 HEK TRADE HUB - TERMUX SETUP 📱                     ║"
echo "║                                                                ║"
echo "║         Professional Crypto Trading on Android                 ║"
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

print_info() {
    echo -e "${CYAN}ℹ${NC}  $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC}  $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Welcome
print_info "Welcome to HekTradeHub Termux Setup!"
print_info "This will configure your Android device for crypto trading."
echo ""
read -p "Press Enter to continue..."

# Step 1: Termux Environment Check
print_header "STEP 1: Termux Environment Check"

# Verify we're in Termux
if [[ ! "$PREFIX" == *"com.termux"* ]]; then
    print_error "This script must be run in Termux!"
    print_info "Download Termux from F-Droid: https://f-droid.org/en/packages/com.termux/"
    exit 1
fi
print_success "Running in Termux environment"

# Check storage permission
if [ ! -d "$HOME/storage" ]; then
    print_warning "Storage access not configured"
    print_info "Setting up storage access..."
    termux-setup-storage
    echo ""
    print_info "Please grant storage permission in the popup"
    sleep 3
fi

print_success "Termux environment ready"
echo ""
read -p "Press Enter to continue..."

# Step 2: Install System Packages
print_header "STEP 2: Installing Required Packages"

print_info "Updating package lists..."
pkg update -y

print_info "Installing required packages..."
print_info "This may take 5-10 minutes depending on your connection..."

# Core packages
pkg install -y python python-pip git clang make cmake binutils

# TA-Lib dependencies (needed for technical analysis)
print_info "Installing TA-Lib dependencies..."
pkg install -y wget

# Build TA-Lib from source for Termux
if ! python -c "import talib" 2>/dev/null; then
    print_info "Building TA-Lib (this may take a few minutes)..."
    
    # Download TA-Lib
    cd "$HOME"
    wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
    tar -xzf ta-lib-0.4.0-src.tar.gz
    cd ta-lib
    
    # Configure and build for Termux
    ./configure --prefix=$PREFIX
    make
    make install
    
    # Cleanup
    cd "$HOME"
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz
    
    print_success "TA-Lib installed"
else
    print_success "TA-Lib already installed"
fi

print_success "System packages installed"
echo ""
read -p "Press Enter to continue..."

# Step 3: Python Virtual Environment
print_header "STEP 3: Python Virtual Environment"

cd "$HOME/hekstradehub" || {
    print_error "hekstradehub directory not found!"
    print_info "Clone the repository first:"
    print_info "  git clone https://github.com/DecarloFreelance/hekstradehub.git"
    print_info "  cd hekstradehub"
    exit 1
}

if [ -d ".venv" ]; then
    print_info "Virtual environment exists"
    read -p "Recreate it? (y/N): " recreate
    if [[ $recreate =~ ^[Yy]$ ]]; then
        rm -rf .venv
        print_info "Creating new virtual environment..."
        python -m venv .venv
        print_success "Virtual environment created"
    fi
else
    print_info "Creating virtual environment..."
    python -m venv .venv
    print_success "Virtual environment created"
fi

print_info "Activating virtual environment..."
source .venv/bin/activate
print_success "Virtual environment activated"

echo ""
read -p "Press Enter to continue..."

# Step 4: Install Python Dependencies
print_header "STEP 4: Installing Python Packages"

print_info "Upgrading pip..."
pip install --upgrade pip

print_info "Installing core dependencies..."
pip install ccxt pandas numpy python-dotenv requests

print_info "Installing TA-Lib Python wrapper..."
pip install TA-Lib

print_info "Installing optional packages..."
pip install colorama tabulate

print_success "Python packages installed"

# Verify installations
print_info "Verifying installations..."
python -c "import ccxt; print('✓ ccxt:', ccxt.__version__)" || print_error "ccxt failed"
python -c "import pandas; print('✓ pandas:', pandas.__version__)" || print_error "pandas failed"
python -c "import talib; print('✓ TA-Lib: OK')" || print_error "TA-Lib failed"

echo ""
read -p "Press Enter to continue..."

# Step 5: API Configuration
print_header "STEP 5: KuCoin API Configuration"

if [ -f ".env" ]; then
    print_warning ".env file already exists"
    read -p "Reconfigure API credentials? (y/N): " reconfig
    if [[ ! $reconfig =~ ^[Yy]$ ]]; then
        print_info "Keeping existing configuration"
    else
        configure_api=true
    fi
else
    configure_api=true
fi

if [ "$configure_api" = true ]; then
    print_info "You'll need KuCoin API credentials with Futures trading enabled"
    echo ""
    
    read -p "Enter your KuCoin API Key: " api_key
    read -p "Enter your KuCoin API Secret: " api_secret
    read -p "Enter your KuCoin API Passphrase: " api_passphrase
    
    # Create .env file
    cat > .env << EOF
# KuCoin API Credentials
KUCOIN_API_KEY=$api_key
KUCOIN_API_SECRET=$api_secret
KUCOIN_API_PASSPHRASE=$api_passphrase
KUCOIN_API_URL=https://api-futures.kucoin.com

# Trading Settings
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
EOF
    
    chmod 600 .env
    print_success "API credentials saved to .env"
fi

echo ""
read -p "Press Enter to continue..."

# Step 6: Termux Auto-Activation
print_header "STEP 6: Termux Configuration"

print_info "Setting up auto-activation for convenience..."

# Add to .bashrc if not already there
if ! grep -q "hekstradehub/.venv" ~/.bashrc 2>/dev/null; then
    cat >> ~/.bashrc << 'EOF'

# HekTradeHub auto-activation
if [[ "$PWD" == "$HOME/hekstradehub"* ]] && [ -f "$HOME/hekstradehub/.venv/bin/activate" ]; then
    source "$HOME/hekstradehub/.venv/bin/activate"
fi
EOF
    print_success "Auto-activation added to .bashrc"
else
    print_info "Auto-activation already configured"
fi

# Create convenience aliases
if ! grep -q "alias trade=" ~/.bashrc 2>/dev/null; then
    cat >> ~/.bashrc << 'EOF'

# Trading aliases
alias trade='cd $HOME/hekstradehub && ./trade'
alias status='cd $HOME/hekstradehub && ./status'
alias tradehub='cd $HOME/hekstradehub'
EOF
    print_success "Convenience aliases added"
fi

echo ""
read -p "Press Enter to continue..."

# Step 7: Quick Tutorial
print_header "STEP 7: Quick Start Guide"

echo -e "${BOLD}${GREEN}Setup Complete! 🎉${NC}\n"

print_info "Quick Commands:"
echo -e "  ${CYAN}tradehub${NC}     - Navigate to trading directory"
echo -e "  ${CYAN}./trade${NC}      - Open main trading dashboard"
echo -e "  ${CYAN}./status${NC}     - Check current positions"
echo ""

print_info "First Steps:"
echo -e "  1. Test your connection:"
echo -e "     ${CYAN}python monitoring/check_position.py${NC}"
echo ""
echo -e "  2. Find trading opportunities:"
echo -e "     ${CYAN}python analysis/find_opportunity.py${NC}"
echo ""
echo -e "  3. Open the main dashboard:"
echo -e "     ${CYAN}./trade${NC}"
echo ""

print_warning "Termux Tips:"
echo -e "  • Keep Termux running with ${CYAN}termux-wake-lock${NC}"
echo -e "  • Install Termux:Widget for home screen shortcuts"
echo -e "  • Use ${CYAN}pkg install tmux${NC} to run multiple sessions"
echo -e "  • Enable notifications: ${CYAN}pkg install termux-api${NC}"
echo ""

print_info "Background Trading:"
echo -e "  To keep auto-trailing running when screen is off:"
echo -e "    ${CYAN}termux-wake-lock${NC}"
echo -e "    ${CYAN}nohup python automation/auto_trailing_stop.py &${NC}"
echo ""

# Test connection
print_header "Connection Test"
print_info "Testing KuCoin API connection..."

if python -c "import ccxt; from dotenv import load_dotenv; import os; load_dotenv(); e=ccxt.kucoinfutures({'apiKey':os.getenv('KUCOIN_API_KEY'),'secret':os.getenv('KUCOIN_API_SECRET'),'password':os.getenv('KUCOIN_API_PASSPHRASE'),'enableRateLimit':True}); print('✓ Connected to KuCoin Futures')" 2>/dev/null; then
    print_success "KuCoin API connection successful!"
else
    print_warning "Could not connect to KuCoin API"
    print_info "Please verify your API credentials in .env"
fi

echo ""
echo -e "${BOLD}${CYAN}Ready to trade! Type 'tradehub' to get started.${NC}"
echo ""
print_info "For help: ./trade (option 9 for documentation)"
echo ""
