# HekTradeHub - Crypto Trading System

Professional crypto trading advisor for KuCoin Futures with automated risk management.

## 🚀 Quick Start

### Desktop/Linux Setup

```bash
git clone https://github.com/DecarloFreelance/hekstradehub.git
cd hekstradehub
./setup.sh
```

### 📱 Android/Termux Setup

```bash
pkg install -y git && \
git clone https://github.com/DecarloFreelance/hekstradehub.git && \
cd hekstradehub && \
bash setup-termux.sh
```

📖 **[Full Termux Guide](docs/TERMUX_GUIDE.md)** - Run crypto trading on your phone!

The interactive setup wizard will:
- Check system requirements
- Create virtual environment
- Install dependencies (including TA-Lib)
- Configure API credentials
- Guide you through the system

### Already Set Up?

```bash
# Launch unified trading dashboard
./trade

# Quick position check
./status
```

## 📁 Project Structure

```
hekstradehub/
├── trade              # Main entry point - unified dashboard
├── status             # Quick position status check
├── trader.py          # Unified trading interface
├── trade_journal.py   # Trade journal manager
│
├── analysis/          # Market analysis tools
│   ├── find_opportunity.py
│   └── quick_scalp_finder.py
│
├── automation/        # Automated trading features
│   ├── auto_trailing_stop.py
│   └── auto_trailing_manager.py
│
├── monitoring/        # Position & account monitoring
│   ├── check_position.py
│   ├── check_trade_history.py
│   └── live_dashboard.py
│
├── trading/           # Trade execution scripts
│   ├── open_long.py
│   ├── open_short.py
│   ├── set_stop_and_tp.py
│   ├── order_manager.py
│   ├── safe_trade_wrapper.py
│   └── small_account_manager.py
│
├── core/              # Core analysis modules
│   ├── indicators.py
│   ├── risk_manager.py
│   ├── scoring.py
│   └── timeframe_analyzer.py
│
├── scripts/           # Advanced strategies
│   └── (advanced trading scripts)
│
├── utils/             # Utility scripts
│   ├── add_margin.py
│   ├── adjust_leverage.py
│   └── switch_margin_mode.py
│
├── bin/               # Shell scripts
│   ├── start_auto_trailing.sh
│   ├── launch_dashboard.sh
│   └── startup.sh
│
├── docs/              # Documentation
├── logs/              # Log files
├── tests/             # Test scripts
└── archive/           # Old/deprecated files
```

## 💡 Usage

### Unified Dashboard
```bash
./trade
```
Interactive menu with all trading functions:
- Check positions
- Find opportunities
- Execute trades
- Manage stops & targets
- View history

### Quick Commands
```bash
# Check positions
./status

# Or use full paths:
python monitoring/check_position.py
python analysis/find_opportunity.py
python trading/open_long.py
```

### Auto-Trailing Stop
```bash
# Start trailing stop (runs in background)
python automation/auto_trailing_stop.py SYMBOL SIDE ENTRY STOP TRAIL_R TRAIL_ATR

# Example:
python automation/auto_trailing_stop.py ATOM/USDT:USDT LONG 1.9910 1.99 1.5 1.0
```

## 📊 Features

- **Risk Management**: Automatic position sizing based on account balance
- **Auto-Trailing**: Set and forget trailing stop loss
- **Multi-Timeframe Analysis**: 4H/1H/15M trend alignment
- **Technical Indicators**: RSI, MACD, ADX, Bollinger Bands, etc.
- **Trade Journal**: Automatic logging of all trades

## ⚙️ Configuration

1. Copy `.env.example` to `.env` (if exists)
2. Add your KuCoin API credentials:
   ```
   KUCOIN_API_KEY=your_key
   KUCOIN_API_SECRET=your_secret
   KUCOIN_API_PASSPHRASE=your_passphrase
   ```

## 🛡️ Safety Features

- RAM protection to prevent system crashes
- Automatic leverage verification
- Position size limits
- Liquidation price warnings
- Trade journaling for review

## 📝 Trade Journal

All trades are automatically logged in `trade_journal.json` with:
- Entry/exit prices
- P&L and ROI
- Market conditions
- Lessons learned
- Issues encountered

## 🔧 Development

Active development focuses on:
- Small account optimization
- Automated strategy execution
- Enhanced risk management
- Performance tracking

---

**Author**: HekTic
**Platform**: KuCoin Futures
**Status**: Production Ready
