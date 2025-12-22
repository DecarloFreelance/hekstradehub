#!/bin/bash
# Seamless Setup & Launch Script for Crypto Trading Dashboard
# Handles everything: venv creation, dependencies, credentials, dashboard

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR=".venv"
PYTHON="$VENV_DIR/bin/python"
PIP="$VENV_DIR/bin/pip"

echo ""
echo "🚀 Crypto Trading Dashboard - Auto Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 1: Check/Create Virtual Environment
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
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

# Step 2: Verify Virtual Environment
if [ ! -f "$PYTHON" ]; then
    echo "❌ Virtual environment is corrupted"
    echo "   Please remove .venv and try again:"
    echo "   rm -rf .venv && ./start.sh"
    exit 1
fi
echo "✓ Virtual environment verified"
echo ""

# Step 3: Check/Install Dependencies
echo "📚 Checking dependencies..."
if ! "$PYTHON" -c "import ccxt" 2>/dev/null; then
    echo "📥 Installing required packages..."
    echo "   (This may take a minute on first run)"
    "$PIP" install -q --upgrade pip
    "$PIP" install -q -r requirements.txt
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

"$PYTHON" dashboard.py
