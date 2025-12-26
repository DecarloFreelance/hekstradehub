#!/usr/bin/env python3
"""
Example: Using the Config module in trading scripts

This demonstrates how to integrate the centralized Config module
into your trading scripts for better configuration management.
"""

# Old way (still works, but duplicated code):
# from dotenv import load_dotenv
# import os
# load_dotenv()
# api_key = os.getenv('KUCOIN_API_KEY')
# api_secret = os.getenv('KUCOIN_API_SECRET')
# api_pass = os.getenv('KUCOIN_API_PASSPHRASE')

# New way (centralized, validated):
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

# Validate configuration before proceeding
is_valid, errors = Config.validate()
if not is_valid:
    print("❌ Configuration errors found:")
    for error in errors:
        print(f"  - {error}")
    print("\nRun './config.guess' to diagnose and fix issues.")
    exit(1)

# Get KuCoin configuration (ready for ccxt)
kucoin_config = Config.get_kucoin_config()

# Access individual settings
print(f"📊 Trading Settings:")
print(f"  • Max Position Size: ${Config.MAX_POSITION_SIZE}")
print(f"  • Default Leverage: {Config.DEFAULT_LEVERAGE}x")
print(f"  • Default Risk: {Config.DEFAULT_RISK_PERCENT}%")
print(f"  • Min Position Size: ${Config.MIN_POSITION_SIZE}")

# Example: Initialize exchange with config
try:
    import ccxt
    
    exchange = ccxt.kucoinfutures(kucoin_config)
    print("\n✓ KuCoin exchange initialized successfully")
    
    # Test connection
    conn_ok, message = Config.test_api_connection()
    if conn_ok:
        print(f"✓ {message}")
    else:
        print(f"❌ {message}")
        
except ImportError:
    print("\n⚠️  ccxt not installed. Install with: pip install ccxt")
except Exception as e:
    print(f"\n❌ Error: {e}")

# Example: Use settings in your trading logic
def calculate_position_size(entry_price, stop_price):
    """Calculate position size based on configured risk"""
    # Use configured risk percent
    risk_pct = Config.DEFAULT_RISK_PERCENT / 100
    
    # Use configured max position size as safety limit
    max_size = Config.MAX_POSITION_SIZE
    
    # Your calculation logic here...
    print(f"\n📈 Position Calculation:")
    print(f"  • Risk per trade: {Config.DEFAULT_RISK_PERCENT}%")
    print(f"  • Max position: ${max_size}")
    
# Example usage
if __name__ == '__main__':
    calculate_position_size(42000, 41000)
