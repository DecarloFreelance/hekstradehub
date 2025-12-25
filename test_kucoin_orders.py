#!/usr/bin/env python3
"""
Test KuCoin order placement - specifically stop losses
Diagnose what's going wrong and show correct format
"""

import ccxt
from dotenv import load_dotenv
import os
import json

load_dotenv()

def test_kucoin_api():
    """Test KuCoin API capabilities and requirements"""
    
    exchange = ccxt.kucoinfutures({
        'apiKey': os.getenv('KUCOIN_API_KEY'),
        'secret': os.getenv('KUCOIN_API_SECRET'),
        'password': os.getenv('KUCOIN_API_PASSPHRASE'),
        'enableRateLimit': True,
    })
    
    print("\n" + "="*70)
    print("KUCOIN FUTURES API TESTING")
    print("="*70)
    
    # Test 1: Check if we can access account
    print("\n1. Testing account access...")
    try:
        balance = exchange.fetch_balance()
        futures_balance = balance.get('USDT', {}).get('free', 0)
        print(f"   ✅ Account accessible")
        print(f"   💰 Available balance: ${futures_balance:.2f} USDT")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return
    
    # Test 2: Check current positions
    print("\n2. Checking for open positions...")
    try:
        positions = exchange.fetch_positions()
        active = [p for p in positions if float(p.get('contracts', 0)) != 0]
        
        if active:
            print(f"   ⚠️  Found {len(active)} open position(s)")
            for pos in active:
                symbol = pos.get('symbol')
                side = pos.get('side')
                contracts = pos.get('contracts')
                entry = pos.get('entryPrice')
                print(f"      - {symbol} {side}: {contracts} contracts @ ${entry}")
        else:
            print(f"   ✅ No open positions")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Test 3: Check market data access
    print("\n3. Testing market data...")
    try:
        ticker = exchange.fetch_ticker('DOGE/USDT:USDT')
        print(f"   ✅ Market data accessible")
        print(f"   📊 DOGE/USDT: ${ticker['last']:.4f}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Test 4: Check what order types are supported
    print("\n4. Checking supported order types...")
    try:
        markets = exchange.load_markets()
        doge_market = markets.get('DOGE/USDT:USDT', {})
        
        print(f"   Order types: {doge_market.get('info', {}).get('orderTypes', 'N/A')}")
        print(f"   Stop orders: {doge_market.get('info', {}).get('supportStopOrder', 'N/A')}")
        
        # Show the raw market info for DOGE
        print("\n   Raw market info for DOGE/USDT:USDT:")
        print(f"   {json.dumps(doge_market.get('info', {}), indent=2)[:500]}...")
        
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Test 5: Show correct order format
    print("\n5. KuCoin order format requirements:")
    print("""
   For STOP LOSS orders on KuCoin Futures:
   
   exchange.create_order(
       symbol='DOGE/USDT:USDT',
       type='stop',              # 'stop' for stop market
       side='sell',              # 'sell' to close long, 'buy' to close short
       amount=contracts,         # Number of contracts
       price=None,               # None for market order when triggered
       params={
           'stopPrice': stop_price,     # Trigger price
           'stopPriceType': 'TP',       # 'TP' (last price) or 'MP' (mark price)
           'reduceOnly': True,          # CRITICAL: Close position only
           'closeOrder': True           # Indicates this closes a position
       }
   )
   
   For TAKE PROFIT orders:
   Same format, just change stopPrice to your TP level
   
   For LIMIT entry orders:
   exchange.create_limit_order(
       symbol='DOGE/USDT:USDT',
       side='buy',  # or 'sell' for short
       amount=contracts,
       price=entry_price
   )
    """)
    
    print("\n" + "="*70)
    print("DIAGNOSIS COMPLETE")
    print("="*70)
    print("\n💡 Next step: Use the order_manager.py tool to place orders correctly\n")

if __name__ == '__main__':
    test_kucoin_api()
