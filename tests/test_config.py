#!/usr/bin/env python3
"""
Test suite for config.py module
Tests configuration validation and system checks
"""
import os
import sys
import tempfile
from pathlib import Path

# Test the config module
def test_config_module():
    """Test basic config module functionality"""
    print("Testing Config Module")
    print("=" * 50)
    
    # Save original directory
    original_dir = os.getcwd()
    
    try:
        # Create temporary directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            
            # Test 1: No .env file
            print("\n1. Testing without .env file...")
            sys.path.insert(0, original_dir)
            from config import Config
            
            is_valid, errors = Config.validate()
            assert not is_valid, "Should fail without .env"
            assert any('.env file not found' in e for e in errors), "Should report missing .env"
            print("   ✓ Correctly detects missing .env")
            
            # Test 2: .env with placeholder values
            print("\n2. Testing with placeholder values...")
            with open('.env', 'w') as f:
                f.write('KUCOIN_API_KEY=your_api_key_here\n')
                f.write('KUCOIN_API_SECRET=your_api_secret_here\n')
                f.write('KUCOIN_API_PASSPHRASE=your_api_passphrase_here\n')
            
            # Reload the module
            if 'config' in sys.modules:
                del sys.modules['config']
            from config import Config
            
            is_valid, errors = Config.validate()
            assert not is_valid, "Should fail with placeholders"
            assert any('placeholder' in e for e in errors), "Should detect placeholders"
            print("   ✓ Correctly detects placeholder values")
            
            # Test 3: Valid configuration
            print("\n3. Testing with valid values...")
            with open('.env', 'w') as f:
                f.write('KUCOIN_API_KEY=test_key_123\n')
                f.write('KUCOIN_API_SECRET=test_secret_456\n')
                f.write('KUCOIN_API_PASSPHRASE=test_pass_789\n')
                f.write('DEFAULT_LEVERAGE=20\n')
                f.write('MAX_POSITION_SIZE=2000\n')
            
            # Reload the module
            if 'config' in sys.modules:
                del sys.modules['config']
            from config import Config
            
            is_valid, errors = Config.validate()
            assert is_valid, f"Should be valid, but got errors: {errors}"
            assert Config.DEFAULT_LEVERAGE == 20, "Should read custom leverage"
            assert Config.MAX_POSITION_SIZE == 2000, "Should read custom position size"
            print("   ✓ Correctly validates proper configuration")
            print(f"   ✓ Custom settings loaded (leverage: {Config.DEFAULT_LEVERAGE}x)")
            
            # Test 4: Invalid leverage
            print("\n4. Testing with invalid leverage...")
            with open('.env', 'w') as f:
                f.write('KUCOIN_API_KEY=test_key_123\n')
                f.write('KUCOIN_API_SECRET=test_secret_456\n')
                f.write('KUCOIN_API_PASSPHRASE=test_pass_789\n')
                f.write('DEFAULT_LEVERAGE=150\n')  # > MAX_LEVERAGE
            
            # Reload the module
            if 'config' in sys.modules:
                del sys.modules['config']
            from config import Config
            
            is_valid, errors = Config.validate()
            assert not is_valid, "Should fail with invalid leverage"
            assert any('DEFAULT_LEVERAGE' in e for e in errors), "Should report leverage error"
            print("   ✓ Correctly detects invalid leverage")
            
            # Test 5: System info
            print("\n5. Testing system info...")
            sys_info = Config.get_system_info()
            assert 'platform' in sys_info, "Should have platform info"
            assert 'python_version' in sys_info, "Should have Python version"
            print(f"   ✓ System info: {sys_info['platform']}")
            print(f"   ✓ Python: {sys_info['python_version']}")
            
            # Test 6: KuCoin config
            print("\n6. Testing KuCoin config extraction...")
            kucoin_cfg = Config.get_kucoin_config()
            assert 'apiKey' in kucoin_cfg, "Should have apiKey"
            assert 'secret' in kucoin_cfg, "Should have secret"
            assert 'password' in kucoin_cfg, "Should have password"
            assert kucoin_cfg['timeout'] == 30000, "Should have timeout"
            print("   ✓ KuCoin config properly formatted")
            
            print("\n" + "=" * 50)
            print("✓ All tests passed!")
            print("=" * 50)
            
    finally:
        # Restore original directory
        os.chdir(original_dir)

if __name__ == '__main__':
    try:
        test_config_module()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
