#!/usr/bin/env python3
"""Add margin to isolated position to increase effective leverage"""
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, '/home/hektic/hekstradehub/kucoin-universal-sdk/sdk/python')

from kucoin_universal_sdk.api import DefaultClient
from kucoin_universal_sdk.model import ClientOptionBuilder, GLOBAL_FUTURES_API_ENDPOINT, TransportOptionBuilder
from kucoin_universal_sdk.generate.futures.positions.model_add_isolated_margin_req import AddIsolatedMarginReq

load_dotenv()

GREEN = '\033[92m'
YELLOW = '\033[93m'
BOLD = '\033[1m'
RESET = '\033[0m'

def add_margin_to_position(symbol='ATOMUSDTM', margin_amount='5.0'):
    """Add margin to isolated position to increase leverage"""
    
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
        print(f"\n{BOLD}=== Adding ${margin_amount} margin to {symbol} ==={RESET}\n")
        
        # Add isolated margin
        req = AddIsolatedMarginReq(symbol=symbol, margin=margin_amount, bizNo=None)
        response = positions_api.add_isolated_margin(req)
        
        print(f"{GREEN}✓ Margin added successfully!{RESET}")
        print(f"Response: {response}")
        print(f"\n{BOLD}This increases your position's effective leverage!{RESET}")
        
        return True
        
    except Exception as e:
        print(f"{YELLOW}Error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'ATOMUSDTM'
    margin = sys.argv[2] if len(sys.argv) > 2 else '5.0'
    
    success = add_margin_to_position(symbol, margin)
    sys.exit(0 if success else 1)
