# Configuration Examples

This directory contains examples of how to use the HekTradeHub configuration system.

## Files

### config_usage_example.py

Demonstrates how to use the centralized `Config` module in your trading scripts.

**Features shown:**
- Configuration validation before running
- Accessing configured settings
- Initializing KuCoin exchange with config
- Using config values in trading logic

**Run:**
```bash
python examples/config_usage_example.py
```

**Note:** You need a valid `.env` file with API credentials for this example to complete successfully.

## Integration Guide

### Old Pattern (Still Works)
```python
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('KUCOIN_API_KEY')
api_secret = os.getenv('KUCOIN_API_SECRET')
api_pass = os.getenv('KUCOIN_API_PASSPHRASE')
```

### New Pattern (Recommended)
```python
from config import Config

# Validate first
is_valid, errors = Config.validate()
if not is_valid:
    print(f"Config errors: {errors}")
    exit(1)

# Use centralized config
kucoin_config = Config.get_kucoin_config()
leverage = Config.DEFAULT_LEVERAGE
```

## Benefits of Using Config Module

1. **Validation**: Automatic validation of all settings
2. **Type Safety**: Proper type conversion (int, float, etc.)
3. **Defaults**: Sensible defaults for optional settings
4. **Centralized**: Single source of truth for configuration
5. **Error Handling**: Clear error messages for misconfigurations
6. **Testing**: Easy to test with different configs

## See Also

- [CONFIG.md](../docs/CONFIG.md) - Full configuration guide
- [config.py](../config.py) - Config module source
