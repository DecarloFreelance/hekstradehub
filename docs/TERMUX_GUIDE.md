# 📱 Termux (Android) Installation Guide

Run your crypto trading system directly from your Android phone using Termux!

## Prerequisites

### 1. Install Termux
Download Termux from **F-Droid** (NOT Google Play - it's outdated):
- 🔗 https://f-droid.org/en/packages/com.termux/

### 2. Initial Termux Setup
```bash
# Update packages
pkg update && pkg upgrade

# Grant storage access (for logs and data)
termux-setup-storage
```

## Quick Installation

### One-Line Install
```bash
pkg install -y git && \
git clone https://github.com/DecarloFreelance/hekstradehub.git && \
cd hekstradehub && \
bash setup-termux.sh
```

### Manual Installation
```bash
# Install git
pkg install git

# Clone repository
git clone https://github.com/DecarloFreelance/hekstradehub.git
cd hekstradehub

# Run setup wizard
bash setup-termux.sh
```

## What Gets Installed

The setup script automatically handles:
- ✅ Python 3.x and pip
- ✅ Build tools (clang, make, cmake)
- ✅ TA-Lib (compiled from source for ARM)
- ✅ Virtual environment
- ✅ All Python dependencies (ccxt, pandas, numpy, etc.)
- ✅ API configuration (.env setup)
- ✅ Convenience aliases

## Setup Process

The wizard walks you through 7 steps:

1. **Environment Check** - Verifies Termux installation
2. **System Packages** - Installs Python, build tools, TA-Lib
3. **Virtual Environment** - Creates isolated Python environment
4. **Dependencies** - Installs ccxt, pandas, numpy, TA-Lib wrapper
5. **API Configuration** - Sets up KuCoin credentials
6. **Termux Config** - Adds auto-activation and aliases
7. **Tutorial** - Quick start guide and connection test

**Estimated time:** 10-15 minutes (depends on connection speed)

## After Installation

### Quick Commands
```bash
tradehub     # Navigate to trading directory
./trade      # Open main dashboard
./status     # Check positions
```

### Test Your Setup
```bash
# Check connection
python monitoring/check_position.py

# Find opportunities
python analysis/find_opportunity.py

# Open dashboard
./trade
```

## Running in Background

### Keep Processes Running When Screen Off

1. **Install wake lock** (prevents phone sleep):
```bash
termux-wake-lock
```

2. **Run auto-trailing in background**:
```bash
nohup python automation/auto_trailing_stop.py > /dev/null 2>&1 &
```

3. **Check running processes**:
```bash
ps aux | grep python
```

### Using tmux for Multiple Sessions
```bash
# Install tmux
pkg install tmux

# Start new session
tmux new -s trading

# Create splits
Ctrl+B then "    # Horizontal split
Ctrl+B then %    # Vertical split

# Detach (keeps running)
Ctrl+B then D

# Reattach
tmux attach -t trading
```

## Phone Optimization Tips

### 1. Battery Management
```bash
# Enable wake lock for important processes
termux-wake-lock

# When done trading, release it
termux-wake-unlock
```

### 2. Notifications
```bash
# Install Termux:API for notifications
pkg install termux-api

# Test notification
termux-notification -t "Trade Alert" -c "Position closed at +5%"
```

### 3. Home Screen Shortcuts (Termux:Widget)
Install **Termux:Widget** from F-Droid, then create shortcuts:

```bash
# Create shortcuts directory
mkdir -p ~/.shortcuts

# Quick status check
cat > ~/.shortcuts/check-status.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/hekstradehub
source .venv/bin/activate
python monitoring/check_position.py
EOF

# Find opportunities
cat > ~/.shortcuts/find-trades.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/hekstradehub
source .venv/bin/activate
python analysis/find_opportunity.py
EOF

chmod +x ~/.shortcuts/*.sh
```

Now add widgets to your home screen!

### 4. Data Usage
```bash
# Install nethogs to monitor data usage
pkg install nethogs
nethogs
```

## Troubleshooting

### Build Errors During TA-Lib Installation
```bash
# Ensure build tools are installed
pkg install clang make cmake binutils

# Try manual TA-Lib build
cd ~
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib
./configure --prefix=$PREFIX
make
make install
pip install TA-Lib
```

### Python Import Errors
```bash
# Verify virtual environment is activated
source ~/hekstradehub/.venv/bin/activate

# Check installed packages
pip list

# Reinstall dependencies
pip install -r requirements.txt
```

### Connection Issues
```bash
# Test internet
ping -c 3 api-futures.kucoin.com

# Verify API credentials
cat .env

# Test connection
python -c "import ccxt; from dotenv import load_dotenv; import os; load_dotenv(); e=ccxt.kucoinfutures({'apiKey':os.getenv('KUCOIN_API_KEY'),'secret':os.getenv('KUCOIN_API_SECRET'),'password':os.getenv('KUCOIN_API_PASSPHRASE'),'enableRateLimit':True}); print(e.fetch_balance())"
```

### Permission Denied Errors
```bash
# Fix script permissions
chmod +x trade status
chmod +x bin/*.sh
chmod +x setup-termux.sh
```

### Low Storage Space
```bash
# Check available space
df -h

# Clean package cache
pkg clean

# Remove build artifacts
cd ~/hekstradehub
rm -rf ta-lib/ *.tar.gz
```

## Performance Considerations

### Phone Specs Recommendations
- **Minimum:** 2GB RAM, Quad-core CPU
- **Recommended:** 4GB+ RAM, Octa-core CPU
- **Storage:** 2GB free space for installation

### Expected Performance
- Position checks: ~1-2 seconds
- Opportunity scanning: ~5-10 seconds
- Auto-trailing: Negligible CPU usage
- RAM usage: ~150-200MB

## Security on Mobile

### 1. Lock Your Phone
Always use screen lock when running trading bot!

### 2. Secure Your .env File
```bash
chmod 600 ~/hekstradehub/.env
```

### 3. Use API Restrictions
In KuCoin API settings:
- ✅ Enable "Restrict access to trusted IPs" (use your home IP)
- ✅ Enable "Futures trading only"
- ✅ Disable "Withdrawals"
- ✅ Set passphrase

### 4. Regular Backups
```bash
# Backup .env to secure location
cp ~/hekstradehub/.env ~/storage/shared/Documents/kucoin-backup.env.txt
```

## Updating

```bash
cd ~/hekstradehub

# Pull latest changes
git pull origin main

# Update dependencies
source .venv/bin/activate
pip install --upgrade ccxt pandas numpy
```

## Uninstallation

```bash
# Remove directory
rm -rf ~/hekstradehub

# Remove aliases from .bashrc
nano ~/.bashrc  # Delete HekTradeHub section
```

## Advanced: Running 24/7

### Using VNC for GUI Dashboard
```bash
# Install VNC server
pkg install tigervnc

# Start VNC
vncserver :1

# Connect with VNC client app
# Address: localhost:5901
```

### Cloud Alternative
For 24/7 trading, consider running on:
- 🖥️ Raspberry Pi ($35)
- ☁️ VPS (AWS, DigitalOcean, Vultr)
- 💻 Old laptop/desktop

## Support

- 📖 Main docs: [README.md](../README.md)
- 🐛 Issues: https://github.com/DecarloFreelance/hekstradehub/issues
- 💬 Discussions: https://github.com/DecarloFreelance/hekstradehub/discussions

---

**Happy Mobile Trading! 📱📈**
