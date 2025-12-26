#!/usr/bin/env python3
"""Adjust leverage using KuCoin Universal SDK"""
import os
import sys
from dotenv import load_dotenv

# Add SDK to path
sys.path.insert(0, '/home/hektic/hekstradehub/kucoin-universal-sdk/sdk/python')

from kucoin_universal_sdk.api import DefaultClient
from kucoin_universal_sdk.model import ClientOptionBuilder, GLOBAL_FUTURES_API_ENDPOINT, TransportOptionBuilder
from kucoin_universal_sdk.generate.futures.positions.model_modify_margin_leverage_req import ModifyMarginLeverageReq
from kucoin_universal_sdk.generate.futures.positions.model_add_isolated_margin_req import AddIsolatedMarginReq

load_dotenv()

def adjust_leverage_sdk(symbol='ATOMUSDTM', leverage='10'):
    """Try to adjust leverage using the official SDK"""
    
    key = os.getenv("KUCOIN_API_KEY")
    secret = os.getenv("KUCOIN_API_SECRET")
    passphrase = os.getenv("KUCOIN_API_PASSPHRASE")
    
    # Create transport option
    http_transport_option = (
        TransportOptionBuilder()
        .set_keep_alive(True)
        .build()
    )
    
    # Create client
    client_option = (
        ClientOptionBuilder()
        .set_key(key)
        .set_secret(secret)
        .set_passphrase(passphrase)
        .set_futures_endpoint(GLOBAL_FUTURES_API_ENDPOINT)
        .set_transport_option(http_transport_option)
        .build()
    )
    client = DefaultClient(client_option)
    
    # Get futures service
    kucoin_rest = client.rest_service()
    futures_api = kucoin_rest.get_futures_service()
    positions_api = futures_api.get_positions_api()
    
    try:
        print(f"\n=== Attempting to modify leverage for {symbol} to {leverage}x ===\n")
        
        # Try modify_margin_leverage (for cross margin)
        req = ModifyMarginLeverageReq(symbol=symbol, leverage=leverage)
        response = positions_api.modify_margin_leverage(req)
        
        print(f"✓ Success!")
        print(f"Response: {response}")
        
    except Exception as e:
        print(f"Cross margin leverage failed: {e}")
        print(f"\nThis is expected for isolated margin positions.")
        print(f"\nFor isolated margin:")
        print(f"  1. You need to manually add/remove margin")
        print(f"  2. Leverage is effectively adjusted by position size vs margin")
        print(f"  3. Or switch to cross margin mode first")
        
        return False
    
    return True

if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'ATOMUSDTM'
    leverage = sys.argv[2] if len(sys.argv) > 2 else '10'
    
    adjust_leverage_sdk(symbol, leverage)
