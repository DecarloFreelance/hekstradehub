#!/bin/bash
# Seamless Setup & Launch Script for Crypto Trading Dashboard
# Handles everything: venv creation, dependencies, credentials, dashboard

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "🚀 Crypto Trading Dashboard - Auto Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 1: Check/Create Virtual Environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        echo "   Please ensure python3-venv is installed:"
        echo "   sudo apt install python3-venv"
        exit 1
    fi
    echo "✓ Virtual environment created"
    echo ""
else
    echo "✓ Virtual environment found"
    echo ""
fi

# Step 2: Activate Virtual Environment
echo "🔌 Activating virtual environment..."
source .venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Step 3: Check/Install Dependencies
echo "📚 Checking dependencies..."
if ! python -c "import ccxt" 2>/dev/null; then
    echo "📥 Installing required packages..."
    echo "   (This may take a minute on first run)"
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    if [ $? -eq 0 ]; then
        echo "✓ All dependencies installed"
    else
        echo "❌ Failed to install dependencies"
        exit 1
    fi
else
    echo "✓ Dependencies already installed"
fi
echo ""

# Step 4: Launch Dashboard (will handle .env setup if needed)
echo "🎛️  Launching dashboard..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
sleep 1

python dashboard.py

# Deactivate venv on exit
deactivate 2>/dev/null || true
