#!/usr/bin/env python3
"""Adjust leverage for existing position"""
import ccxt
from dotenv import load_dotenv
import os
import sys

load_dotenv()

def adjust_leverage(symbol, target_leverage):
    exchange = ccxt.kucoinfutures({
        'apiKey': os.getenv('KUCOIN_API_KEY'),
        'secret': os.getenv('KUCOIN_API_SECRET'),
        'password': os.getenv('KUCOIN_API_PASSPHRASE'),
        'enableRateLimit': True,
    })
    
    try:
        print(f"\nAdjusting leverage for {symbol} to {target_leverage}x...")
        
        # For isolated margin mode - use the correct KuCoin endpoint
        response = exchange.futuresPrivatePostPositionRiskLimitLevel({
            'symbol': symbol.replace('/USDT:USDT', 'USDTM'),
            'leverage': target_leverage
        })
        
        print(f"✓ Leverage adjusted to {target_leverage}x")
        print(f"Response: {response}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'ATOM/USDT:USDT'
    leverage = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    adjust_leverage(symbol, leverage)
