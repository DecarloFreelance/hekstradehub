#!/bin/bash
# startup.sh - KuCoin Futures Trading Bot Initializer
# This script sets up the .env file and displays account and open futures trades info using the KuCoin Universal SDK.

set -e

ENV_FILE=".env"

# 1. Prompt for API keys if .env does not exist
if [ ! -f "$ENV_FILE" ]; then
  echo "No .env file found. Please paste your KuCoin API credentials."
  read -p "KUCOIN_API_KEY: " KUCOIN_API_KEY
  read -p "KUCOIN_API_SECRET: " KUCOIN_API_SECRET
  read -p "KUCOIN_API_PASSPHRASE: " KUCOIN_API_PASSPHRASE
  read -p "KUCOIN_API_URL [default: https://api-futures.kucoin.com]: " KUCOIN_API_URL
  KUCOIN_API_URL=${KUCOIN_API_URL:-https://api-futures.kucoin.com}
  echo "KUCOIN_API_KEY=$KUCOIN_API_KEY" > $ENV_FILE
  echo "KUCOIN_API_SECRET=$KUCOIN_API_SECRET" >> $ENV_FILE
  echo "KUCOIN_API_PASSPHRASE=$KUCOIN_API_PASSPHRASE" >> $ENV_FILE
  echo "KUCOIN_API_URL=$KUCOIN_API_URL" >> $ENV_FILE
  echo ".env file created."
else
  echo ".env file already exists. Skipping creation."
fi

# 2. Activate venv if present
if [ -d ".venv" ]; then
  source .venv/bin/activate
fi

# 3. Install kucoin-universal-sdk if not present
pip show kucoin-universal-sdk > /dev/null 2>&1 || pip install kucoin-universal-sdk

PYTHON_BIN="python3"
if [ -d ".venv" ] && [ -x ".venv/bin/python" ]; then
  PYTHON_BIN=".venv/bin/python"
fi

# 4. Run Python script to fetch and display futures account info and open trades
$PYTHON_BIN <<EOF
import os
from dotenv import load_dotenv
import os
try:
    from kucoin_universal_sdk.api.client import DefaultClient
    from kucoin_universal_sdk.model.client_option import ClientOptionBuilder
except ImportError:
    print('kucoin-universal-sdk not installed or not found in venv.')
    exit(1)

from pathlib import Path
dotenv_path = Path('.env').resolve()
load_dotenv(dotenv_path=dotenv_path)
api_key = os.getenv('KUCOIN_API_KEY')
api_secret = os.getenv('KUCOIN_API_SECRET')
api_passphrase = os.getenv('KUCOIN_API_PASSPHRASE')
futures_endpoint = os.getenv('KUCOIN_API_URL', 'https://api-futures.kucoin.com')

if not all([api_key, api_secret, api_passphrase]):
    print('Missing API credentials in .env. Exiting.')
    exit(1)

from kucoin_universal_sdk.model.transport_option import TransportOptionBuilder
transport_option = TransportOptionBuilder().build()
options = (
    ClientOptionBuilder()
    .set_key(api_key)
    .set_secret(api_secret)
    .set_passphrase(api_passphrase)
    .set_futures_endpoint(futures_endpoint)
    .set_transport_option(transport_option)
    .build()
)
client = DefaultClient(options)

print("\nFetching Futures Account Info...")
try:
    # This will show all futures accounts (wallets)
    account_service = client.rest_service().get_account_service()
    accounts = account_service.get_account_api().list_accounts()
    print("Accounts:")
    for acc in accounts.data:
        print(acc)
except Exception as e:
    print(f"Error fetching accounts: {e}")

print("\nFetching Open Futures Positions...")
try:
    futures_service = client.rest_service().get_futures_service()
    positions_api = futures_service.get_positions_api()
    from kucoin_universal_sdk.generate.futures.positions.model_get_position_list_req import GetPositionListReq
    req = GetPositionListReq()
    positions = positions_api.get_position_list(req)
    if hasattr(positions, 'data') and positions.data:
        for pos in positions.data:
            print(pos)
    else:
        print("No open futures positions.")
except Exception as e:
    print(f"Error fetching positions: {e}")
EOF
