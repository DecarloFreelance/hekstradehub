#!/usr/bin/env python3
"""
Safe Trade Wrapper - RAM Protection for All Trading Scripts
Prevents system crashes during live trading
"""
import sys
import os

# Add workspace path for resource manager
sys.path.insert(0, '/home/hektic/saddynhektic workspace')

try:
    from Tools.resource_manager import check_ram_before_processing
except ImportError:
    print("❌ ERROR: resource_manager.py not found!")
    print("Expected location: /home/hektic/saddynhektic workspace/Tools/resource_manager.py")
    exit(1)

def safe_execute(script_path, *args):
    """Safely execute trading script with RAM protection"""
    try:
        # Check RAM before running (require 1.5GB free)
        check_ram_before_processing(min_free_gb=1.5)
        print(f"✅ RAM OK - Running {os.path.basename(script_path)}...")
        
        # Build command with arguments
        cmd = f"python3 {script_path}"
        if args:
            cmd += " " + " ".join(args)
        
        # Execute
        os.system(cmd)
        
    except MemoryError as e:
        print(f"\n❌ INSUFFICIENT RAM: {e}")
        print("\n🔧 SOLUTIONS:")
        print("   1. Close unnecessary applications")
        print("   2. Stop other Python processes")
        print("   3. Restart your system if needed")
        print("\n⚠️  DO NOT run trading scripts with low RAM!")
        print("   System crashes during live trades can cause losses.\n")
        exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python safe_trade_wrapper.py <script.py> [args...]")
        print("\nExamples:")
        print("  python safe_trade_wrapper.py find_opportunity.py")
        print("  python safe_trade_wrapper.py scripts/advanced_scanner.py --min-score 60")
        print("  python safe_trade_wrapper.py check_position.py")
        exit(1)
    
    script = sys.argv[1]
    args = sys.argv[2:]
    safe_execute(script, *args)
