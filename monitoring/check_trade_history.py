#!/usr/bin/env python3
"""Check recent trade history and P&L"""
import ccxt
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

load_dotenv()

def check_recent_trades():
    exchange = ccxt.kucoinfutures({
        'apiKey': os.getenv('KUCOIN_API_KEY'),
        'secret': os.getenv('KUCOIN_API_SECRET'),
        'password': os.getenv('KUCOIN_API_PASSPHRASE'),
        'enableRateLimit': True,
        'options': {
            'defaultType': 'swap',
        }
    })
    
    try:
        # Get recent closed orders (last 24 hours)
        since = int((datetime.now() - timedelta(hours=24)).timestamp() * 1000)
        
        # Fetch recent orders for ADA (use fetchClosedOrders for KuCoin Futures)
        orders = exchange.fetch_closed_orders('ADA/USDT:USDT', since=since)
        
        # Get account history
        balance = exchange.fetch_balance()
        
        print("\n╔═══════════════════════════════════════════════════════╗")
        print("║           ADA SHORT TRADE - FINAL RESULTS             ║")
        print("╚═══════════════════════════════════════════════════════╝\n")
        
        # Filter for closed orders
        closed_orders = [o for o in orders if o.get('status') in ['closed', 'canceled']]
        
        if closed_orders:
            print(f"Recent Orders (Last 24h):\n")
            for order in closed_orders[-5:]:  # Last 5 orders
                oid = order.get('id', 'N/A')
                timestamp = datetime.fromtimestamp(order.get('timestamp', 0) / 1000)
                side = order.get('side', 'N/A').upper()
                otype = order.get('type', 'N/A')
                price = order.get('price') or order.get('average', 0)
                filled = order.get('filled', 0)
                status = order.get('status', 'N/A')
                
                print(f"  [{timestamp.strftime('%H:%M:%S')}] {side} {otype}")
                if price:
                    print(f"    Price: ${price:.4f}, Filled: {filled}, Status: {status}")
                else:
                    print(f"    Market order, Filled: {filled}, Status: {status}")
                print(f"    Order ID: {oid[:16]}...")
                print()
        
        # Show account balance
        usdt = balance.get('USDT', {})
        total = usdt.get('total', 0)
        free = usdt.get('free', 0)
        used = usdt.get('used', 0)
        
        print(f"\nAccount Balance:")
        print(f"  Total USDT: ${total:.2f}")
        print(f"  Available:  ${free:.2f}")
        print(f"  In Use:     ${used:.2f}")
        
        # Check for position history
        try:
            # Get account statements/transactions
            print("\n\nFetching transaction history...")
            # Note: This might not be available in all API versions
            # We'll try to get it from the balance changes
            
        except Exception as e:
            print(f"  (Transaction history not available: {e})")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_recent_trades()
