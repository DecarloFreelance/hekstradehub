#!/usr/bin/env python3
"""
HekTradeHub - Configuration Management and Validation
Centralized configuration with validation and error reporting
"""
import os
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple
import platform

# Try to load dotenv, but don't fail if not available
try:
    from dotenv import load_dotenv
    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    # If dotenv not available, still try to read .env manually
    if Path('.env').exists():
        with open('.env') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

class ConfigError(Exception):
    """Configuration validation error"""
    pass

class Config:
    """Centralized configuration management"""
    
    # Required API credentials
    KUCOIN_API_KEY = os.getenv('KUCOIN_API_KEY', '')
    KUCOIN_API_SECRET = os.getenv('KUCOIN_API_SECRET', '')
    KUCOIN_API_PASSPHRASE = os.getenv('KUCOIN_API_PASSPHRASE', '')
    KUCOIN_API_URL = os.getenv('KUCOIN_API_URL', 'https://api-futures.kucoin.com')
    
    # Optional safety settings
    MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', '1000'))
    DEFAULT_LEVERAGE = int(os.getenv('DEFAULT_LEVERAGE', '10'))
    MAX_LEVERAGE = int(os.getenv('MAX_LEVERAGE', '100'))
    
    # Trading parameters
    DEFAULT_RISK_PERCENT = float(os.getenv('DEFAULT_RISK_PERCENT', '1.0'))
    MIN_POSITION_SIZE = float(os.getenv('MIN_POSITION_SIZE', '10'))
    
    # Telegram alerts (optional)
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    
    @classmethod
    def validate(cls) -> Tuple[bool, list]:
        """
        Validate configuration
        
        Returns:
            Tuple of (is_valid, errors_list)
        """
        errors = []
        
        # Check .env file exists
        if not Path('.env').exists():
            errors.append(".env file not found. Copy .env.example to .env and configure it.")
        
        # Check required API credentials
        if not cls.KUCOIN_API_KEY:
            errors.append("KUCOIN_API_KEY not set in .env")
        elif cls.KUCOIN_API_KEY == 'your_api_key_here':
            errors.append("KUCOIN_API_KEY is still set to placeholder value")
            
        if not cls.KUCOIN_API_SECRET:
            errors.append("KUCOIN_API_SECRET not set in .env")
        elif cls.KUCOIN_API_SECRET == 'your_api_secret_here':
            errors.append("KUCOIN_API_SECRET is still set to placeholder value")
            
        if not cls.KUCOIN_API_PASSPHRASE:
            errors.append("KUCOIN_API_PASSPHRASE not set in .env")
        elif cls.KUCOIN_API_PASSPHRASE == 'your_api_passphrase_here':
            errors.append("KUCOIN_API_PASSPHRASE is still set to placeholder value")
        
        # Validate numeric settings
        if cls.DEFAULT_LEVERAGE < 1 or cls.DEFAULT_LEVERAGE > cls.MAX_LEVERAGE:
            errors.append(f"DEFAULT_LEVERAGE must be between 1 and {cls.MAX_LEVERAGE}")
            
        if cls.DEFAULT_RISK_PERCENT <= 0 or cls.DEFAULT_RISK_PERCENT > 100:
            errors.append("DEFAULT_RISK_PERCENT must be between 0 and 100")
            
        if cls.MIN_POSITION_SIZE <= 0:
            errors.append("MIN_POSITION_SIZE must be greater than 0")
        
        return (len(errors) == 0, errors)
    
    @classmethod
    def get_system_info(cls) -> Dict[str, str]:
        """Get system information for diagnostics"""
        return {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'architecture': platform.machine(),
            'system': platform.system(),
            'release': platform.release(),
        }
    
    @classmethod
    def check_dependencies(cls) -> Tuple[bool, list]:
        """Check if required Python packages are installed"""
        missing = []
        required_packages = [
            'ccxt',
            'pandas',
            'numpy',
            'dotenv',
        ]
        
        for package in required_packages:
            try:
                if package == 'dotenv':
                    __import__('dotenv')
                else:
                    __import__(package)
            except ImportError:
                missing.append(package)
        
        return (len(missing) == 0, missing)
    
    @classmethod
    def get_kucoin_config(cls) -> Dict[str, str]:
        """Get KuCoin API configuration for ccxt"""
        return {
            'apiKey': cls.KUCOIN_API_KEY,
            'secret': cls.KUCOIN_API_SECRET,
            'password': cls.KUCOIN_API_PASSPHRASE,
            'timeout': 30000,
        }
    
    @classmethod
    def test_api_connection(cls) -> Tuple[bool, str]:
        """Test KuCoin API connection"""
        try:
            import ccxt
            
            exchange = ccxt.kucoinfutures(cls.get_kucoin_config())
            balance = exchange.fetch_balance()
            
            return (True, "API connection successful")
        except ImportError:
            return (False, "ccxt package not installed")
        except Exception as e:
            return (False, f"API connection failed: {str(e)}")
    
    @classmethod
    def print_diagnostics(cls):
        """Print comprehensive system diagnostics"""
        print("\n" + "="*70)
        print("HekTradeHub Configuration Diagnostics")
        print("="*70 + "\n")
        
        # System information
        print("📋 System Information:")
        sys_info = cls.get_system_info()
        for key, value in sys_info.items():
            print(f"  • {key.replace('_', ' ').title()}: {value}")
        print()
        
        # Configuration validation
        print("🔧 Configuration Status:")
        is_valid, errors = cls.validate()
        if is_valid:
            print("  ✓ Configuration is valid")
        else:
            print("  ✗ Configuration errors found:")
            for error in errors:
                print(f"    - {error}")
        print()
        
        # Dependencies check
        print("📦 Python Dependencies:")
        deps_ok, missing = cls.check_dependencies()
        if deps_ok:
            print("  ✓ All required packages installed")
        else:
            print("  ✗ Missing packages:")
            for pkg in missing:
                print(f"    - {pkg}")
            print(f"\n  Install with: pip install {' '.join(missing)}")
        print()
        
        # API connection test
        if is_valid and deps_ok:
            print("📡 API Connection Test:")
            conn_ok, message = cls.test_api_connection()
            if conn_ok:
                print(f"  ✓ {message}")
            else:
                print(f"  ✗ {message}")
            print()
        
        # Configuration values
        print("⚙️  Current Configuration:")
        print(f"  • API URL: {cls.KUCOIN_API_URL}")
        print(f"  • Default Leverage: {cls.DEFAULT_LEVERAGE}x")
        print(f"  • Max Leverage: {cls.MAX_LEVERAGE}x")
        print(f"  • Max Position Size: ${cls.MAX_POSITION_SIZE}")
        print(f"  • Default Risk: {cls.DEFAULT_RISK_PERCENT}%")
        print(f"  • Min Position Size: ${cls.MIN_POSITION_SIZE}")
        
        if cls.TELEGRAM_BOT_TOKEN and cls.TELEGRAM_CHAT_ID:
            print("  • Telegram Alerts: Enabled")
        else:
            print("  • Telegram Alerts: Disabled")
        print()
        
        print("="*70)
        
        # Overall status
        if is_valid and deps_ok:
            print("✓ System ready for trading")
        else:
            print("✗ Please fix the errors above before trading")
        print("="*70 + "\n")
        
        return is_valid and deps_ok

def main():
    """Run configuration diagnostics"""
    config = Config()
    is_ready = config.print_diagnostics()
    
    # Exit with appropriate code
    sys.exit(0 if is_ready else 1)

if __name__ == '__main__':
    main()
