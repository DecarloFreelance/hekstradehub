# HekstTradeHub - Professional Crypto Trading System

A systematic, thorough, and precise crypto trading advisor for KuCoin Futures with advanced risk management and multi-timeframe analysis.

## 🚀 New Features

### 1. **Risk Management System** (`core/risk_manager.py`)
Professional position sizing and risk control:
- **Position Sizing**: Calculate optimal contracts based on account risk (default 2%)
- **ATR-Based Stops**: Volatility-adjusted stop losses
- **Multiple Take Profits**: Automatic TP calculation with R:R ratios (1.5R, 3R, 4.5R)
- **Portfolio Risk**: Track total exposure across multiple positions
- **Position Management**: Trailing stop and partial profit suggestions

### 2. **Multi-Timeframe Analysis** (`core/timeframe_analyzer.py`)
Institutional-grade market analysis:
- **4 Timeframe Analysis**: Daily, 4H, 1H, 15M with weighted scoring
- **Confluence Scoring**: 0-100 score based on trend alignment
- **Market Structure**: Identify uptrends, downtrends, and ranging markets
- **Entry Zones**: Optimal, aggressive, and conservative entry recommendations
- **Confirmation Checklist**: 12-point validation system

### 3. **Telegram Alerts** (`core/telegram_alerts.py`)
Real-time notifications:
- **Opportunity Alerts**: High-score trading setups
- **Position Alerts**: Entry/exit confirmations
- **Risk Alerts**: Stop loss hits, portfolio limits
- **Position Updates**: P&L updates with management suggestions
- **Daily Summaries**: Trading statistics and performance

## 📋 Requirements

```bash
pip install ccxt pandas python-dotenv requests numpy
```

## ⚙️ Configuration

### 1. KuCoin API Setup
Add to `/home/hektic/hekstradehub/.env`:
```env
KUCOIN_API_KEY=your_api_key
KUCOIN_API_SECRET=your_api_secret
KUCOIN_API_PASSPHRASE=your_passphrase
```

For detailed configuration guide, see **[CONFIG.md](CONFIG.md)**.

### Quick Configuration Check
Validate your system setup anytime:
```bash
./config.guess
# or
python config.py
```

### 2. Telegram Setup (Optional but Recommended)

#### Create Bot:
1. Open Telegram, search `@BotFather`
2. Send: `/newbot`
3. Follow instructions, save the bot token

#### Get Chat ID:
1. Search `@userinfobot`
2. Start the bot
3. Copy your chat ID

#### Add to .env:
```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

#### Test:
```bash
python core/telegram_alerts.py
```

## 🎯 Usage

### Advanced Scanner
Comprehensive multi-timeframe opportunity finder:

```bash
# Scan all markets (default min score: 50)
python scripts/advanced_scanner.py

# Only show high-quality setups
python scripts/advanced_scanner.py --min-score 60

# Enable Telegram alerts
python scripts/advanced_scanner.py --min-score 60 --alerts
```

**Output includes:**
- Confluence score (0-100)
- Timeframe trend analysis
- Entry zones (aggressive/optimal/conservative)
- Position sizing with risk management
- Take profit targets with R:R ratios
- Confirmation checklist
- Stop loss recommendations

### Enhanced Position Manager

#### Plan New Position:
```bash
# Plan a LONG position on BTC
python scripts/enhanced_position_manager.py --open --symbol BTC/USDT:USDT --side LONG

# Plan SHORT with custom leverage
python scripts/enhanced_position_manager.py --open --symbol ETH/USDT:USDT --side SHORT --leverage 15
```

**Features:**
- Automatic position sizing based on account balance
- ATR-based stop loss calculation
- 3 take profit targets with optimal R:R
- Risk validation
- Telegram notification (if configured)

#### Monitor Active Position:
```bash
python scripts/enhanced_position_manager.py --monitor \
  --symbol BTC/USDT:USDT \
  --entry 42000 \
  --stop 41000 \
  --side LONG \
  --contracts 10
```

**Real-time monitoring:**
- Live P&L tracking
- RSI and MACD updates
- Breakeven and trailing stop suggestions
- Partial profit recommendations
- Stop loss alerts
- Auto Telegram updates

## 📊 How It Works

### Scoring System

The system analyzes multiple factors across 4 timeframes:

1. **Trend Alignment (40%)**: Daily → 4H → 1H → 15M trend agreement
2. **Momentum (30%)**: RSI, MACD, Stochastic RSI strength
3. **Strength (15%)**: ADX for trend strength
4. **Volume (15%)**: Volume ratio, OBV, VWAP position

Each timeframe has a weight:
- Daily: 40%
- 4-Hour: 30%
- 1-Hour: 20%
- 15-Minute: 10%

**Final Score:**
- 75-100: 🔥 STRONG signal
- 60-74: ✅ GOOD signal
- 50-59: ⚡ MODERATE signal
- <50: Not shown

### Risk Management

- **Default Risk**: 2% of account per trade
- **ATR Stops**: 1.5x ATR from entry (volatility-adjusted)
- **Position Sizing**: Automatically calculated for exact risk
- **Take Profits**: Scaled exits at 1.5R, 3R, 4.5R
- **Leverage**: Configurable (default 10x)

### Confirmation Checklist

12 key confirmations:
1. Daily trend alignment
2. 4H trend alignment
3. 1H trend alignment
4. 15M trend alignment
5. Price above/below all EMAs
6. RSI in optimal range
7. MACD bullish/bearish
8. Strong ADX (>25)
9. VWAP position
10. Volume confirmation
11. OBV trend
12. Market structure

## 🔧 Module API

### RiskManager

```python
from core.risk_manager import RiskManager

rm = RiskManager(account_balance=1000, max_risk_per_trade_pct=2.0)

# Calculate position size
position = rm.calculate_position_size(
    entry_price=42000,
    stop_loss_price=41000,
    leverage=10,
    side='LONG'
)

# Get take profit levels
tps = rm.calculate_take_profits(
    entry_price=42000,
    stop_loss_price=41000,
    side='LONG',
    num_targets=3
)

# Get management suggestions
suggestions = rm.suggest_position_adjustments(
    current_price=43000,
    entry_price=42000,
    stop_loss_price=41000,
    side='LONG'
)
```

### TimeframeAnalyzer

```python
from core.timeframe_analyzer import TimeframeAnalyzer

analyzer = TimeframeAnalyzer(exchange)

# Fetch multi-timeframe data
data = analyzer.fetch_multi_timeframe_data('BTC/USDT:USDT')

# Analyze each timeframe
analyses = {}
for tf, df in data.items():
    analyses[tf] = analyzer.analyze_timeframe(df, tf)

# Calculate confluence
confluence = analyzer.calculate_confluence_score(analyses, 'LONG')

# Find entry zone
entry_zone = analyzer.find_entry_zone(analyses, 'LONG')

# Get confirmation checklist
checklist = analyzer.get_confirmation_checklist(analyses, 'LONG')
```

### TelegramAlert

```python
from core.telegram_alerts import TelegramAlert

telegram = TelegramAlert()

# Send opportunity alert
telegram.send_opportunity_alert(
    symbol='BTC/USDT:USDT',
    score=75,
    direction='LONG',
    entry_zone=entry_zone,
    confluence=confluence,
    checklist=checklist
)

# Send position alert
telegram.send_position_alert(
    action='OPENED',
    symbol='BTC/USDT:USDT',
    side='LONG',
    contracts=10,
    entry_price=42000,
    stop_loss=41000,
    take_profits=tp_levels,
    leverage=10,
    risk_pct=2.0
)
```

## 📁 Project Structure

```
hekstradehub/
├── core/
│   ├── indicators.py           # Technical indicators
│   ├── risk_manager.py         # NEW: Risk management system
│   ├── timeframe_analyzer.py   # NEW: Multi-timeframe analysis
│   └── telegram_alerts.py      # NEW: Alert system
├── scripts/
│   ├── advanced_scanner.py            # NEW: Enhanced opportunity finder
│   ├── enhanced_position_manager.py   # NEW: Position management
│   ├── opportunity_finder.py          # Legacy scanner
│   └── universal_monitor.py           # Legacy monitor
├── .env                        # API credentials
└── README.md                   # This file
```

## 🎓 Best Practices

1. **Start Small**: Test with minimum position sizes
2. **Use Alerts**: Enable Telegram to catch opportunities
3. **Follow Confirmations**: Higher pass rate = better trade
4. **Respect Stops**: Never move stop loss against you
5. **Take Partials**: Scale out at multiple TPs
6. **Track Trades**: Monitor performance over time
7. **Min Score 60+**: Focus on high-quality setups

## ⚠️ Disclaimer

This is a trading tool, not financial advice. Crypto trading involves significant risk. Always:
- Use proper risk management
- Never risk more than you can afford to lose
- Test thoroughly before live trading
- Understand leverage risks

## 🔄 Updates

### v2.0 (December 2025)
- ✅ Professional risk management system
- ✅ Multi-timeframe confluence analysis
- ✅ Telegram alert integration
- ✅ Advanced position manager
- ✅ Enhanced opportunity scanner
- ✅ Systematic scoring system

## 📞 Support

For setup help, see module docstrings or run:
```bash
python core/telegram_alerts.py  # Telegram setup guide
python scripts/advanced_scanner.py --help
python scripts/enhanced_position_manager.py --help
```
