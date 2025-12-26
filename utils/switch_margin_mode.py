#!/usr/bin/env python3
"""Switch from isolated to cross margin mode for proper leverage"""
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, '/home/hektic/hekstradehub/kucoin-universal-sdk/sdk/python')

from kucoin_universal_sdk.api import DefaultClient
from kucoin_universal_sdk.model import ClientOptionBuilder, GLOBAL_FUTURES_API_ENDPOINT, TransportOptionBuilder
from kucoin_universal_sdk.generate.futures.positions.model_switch_margin_mode_req import SwitchMarginModeReq

load_dotenv()

GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BOLD = '\033[1m'
RESET = '\033[0m'

def switch_to_cross_margin(symbol='ATOMUSDTM'):
    """Switch symbol from isolated to cross margin mode"""
    
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
        print(f"\n{BOLD}=== Switching {symbol} to CROSS MARGIN mode ==={RESET}\n")
        print(f"{YELLOW}⚠️  NOTE: You must close all positions on this symbol first!{RESET}\n")
        
        # Switch to cross margin
        req = SwitchMarginModeReq(symbol=symbol, marginMode='CROSSED')
        response = positions_api.switch_margin_mode(req)
        
        print(f"{GREEN}✓ Successfully switched to CROSS MARGIN mode!{RESET}")
        print(f"Response: {response}")
        print(f"\n{BOLD}Now you can set leverage properly before opening positions.{RESET}")
        
        return True
        
    except Exception as e:
        error_str = str(e)
        print(f"{RED}Error: {e}{RESET}\n")
        
        if '300000' in error_str:
            print(f"{YELLOW}You must close all open positions on {symbol} before switching margin modes.{RESET}")
        elif '330007' in error_str:
            print(f"{YELLOW}Already in cross margin mode!{RESET}")
        
        return False

if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'ATOMUSDTM'
    
    success = switch_to_cross_margin(symbol)
    sys.exit(0 if success else 1)
