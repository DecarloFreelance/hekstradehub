# Configuration Management

## Overview

HekTradeHub uses a centralized configuration system for managing API credentials, trading parameters, and safety settings.

## Quick Configuration Check

Run the configuration validator at any time:

```bash
./config.guess
```

Or directly with Python:

```bash
python config.py
```

## What Gets Validated

The configuration system checks:

1. **System Information**
   - Operating system and version
   - Python version
   - System architecture

2. **Configuration Files**
   - `.env` file exists
   - Required API credentials are set
   - Credentials are not placeholder values

3. **Python Dependencies**
   - ccxt (KuCoin API client)
   - pandas (data analysis)
   - numpy (numerical computing)
   - python-dotenv (environment management)

4. **API Connection**
   - Tests actual connection to KuCoin
   - Verifies credentials work

5. **Safety Settings**
   - Leverage limits
   - Position size limits
   - Risk parameters

## Configuration File (.env)

### Required Settings

```bash
# KuCoin API Credentials (REQUIRED)
KUCOIN_API_KEY=your_api_key_here
KUCOIN_API_SECRET=your_api_secret_here
KUCOIN_API_PASSPHRASE=your_api_passphrase_here
```

### Optional Settings

```bash
# API URL (default: https://api-futures.kucoin.com)
KUCOIN_API_URL=https://api-futures.kucoin.com

# Safety Settings
MAX_POSITION_SIZE=1000      # Maximum position size in USDT
DEFAULT_LEVERAGE=10         # Default leverage (1-100)
MAX_LEVERAGE=100           # Maximum allowed leverage
DEFAULT_RISK_PERCENT=1.0   # Default risk per trade (%)
MIN_POSITION_SIZE=10       # Minimum position size in USDT

# Telegram Alerts (optional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## Using Config in Your Scripts

Import the centralized configuration in your trading scripts:

```python
from config import Config

# Get KuCoin API configuration
kucoin_config = Config.get_kucoin_config()

# Access individual settings
max_leverage = Config.MAX_LEVERAGE
risk_percent = Config.DEFAULT_RISK_PERCENT

# Validate configuration
is_valid, errors = Config.validate()
if not is_valid:
    for error in errors:
        print(f"Error: {error}")
    exit(1)

# Test API connection
conn_ok, message = Config.test_api_connection()
if not conn_ok:
    print(f"Connection failed: {message}")
    exit(1)
```

## Troubleshooting

### "Module not found" errors

Install dependencies:
```bash
source .venv/bin/activate  # If using virtual environment
pip install ccxt pandas numpy python-dotenv
```

### ".env file not found"

Create configuration file:
```bash
cp .env.example .env
# Then edit .env with your API credentials
```

### "API connection failed"

1. Verify credentials are correct in `.env`
2. Check API permissions on KuCoin:
   - General (Read)
   - Futures (Read + Trade)
3. Ensure API is not IP-restricted
4. Check internet connection

### "Configuration errors found"

Run `./config.guess` to see detailed error messages and follow the recommendations.

## Security Best Practices

1. **Never commit `.env` to git**
   - Already in `.gitignore`
   - Contains sensitive API credentials

2. **Set restrictive permissions**
   ```bash
   chmod 600 .env
   ```

3. **Use API key restrictions**
   - Enable only necessary permissions
   - Consider IP whitelisting
   - Use separate keys for testing

4. **Monitor API usage**
   - Regularly check KuCoin API logs
   - Look for unexpected activity

## Integration with Setup Script

The setup script (`setup.sh`) automatically:
1. Creates `.env` from template
2. Prompts for API credentials
3. Tests configuration with `config.py`
4. Reports any issues

## Advanced Usage

### Print Full Diagnostics

```python
from config import Config

# Print comprehensive system report
Config.print_diagnostics()
```

### Get System Info

```python
from config import Config

sys_info = Config.get_system_info()
print(f"Platform: {sys_info['platform']}")
print(f"Python: {sys_info['python_version']}")
```

### Check Dependencies Programmatically

```python
from config import Config

deps_ok, missing = Config.check_dependencies()
if not deps_ok:
    print(f"Missing: {', '.join(missing)}")
```

## See Also

- [Setup Guide](VENV_SETUP.md) - Virtual environment setup
- [Trading Standards](TRADING_STANDARDS.md) - Trading guidelines
- [Termux Guide](TERMUX_GUIDE.md) - Android setup
