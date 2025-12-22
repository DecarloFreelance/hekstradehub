#!/usr/bin/env python3
"""
Core API Module
KuCoin API interactions - positions, orders, market data
"""
import os
import time
import ccxt
import pandas as pd
from dotenv import load_dotenv
import requests
import hmac
import hashlib
import base64

load_dotenv()

def get_exchange():
    """Create and return KuCoin exchange object"""
    try:
        exchange = ccxt.kucoin({
            'apiKey': os.getenv('KUCOIN_API_KEY'),
            'secret': os.getenv('KUCOIN_API_SECRET'),
            'password': os.getenv('KUCOIN_API_PASSPHRASE'),
            'enableRateLimit': True,
        })
        return exchange
    except Exception as e:
        print(f"Error connecting to KuCoin: {e}")
        return None

def fetch_positions():
    """Fetch all futures positions from KuCoin"""
    try:
        credentials = {
            'apiKey': os.getenv('KUCOIN_API_KEY'),
            'secret': os.getenv('KUCOIN_API_SECRET'),
            'password': os.getenv('KUCOIN_API_PASSPHRASE')
        }
        
        timestamp = str(int(time.time() * 1000))
        endpoint = '/api/v1/positions'
        str_to_sign = timestamp + 'GET' + endpoint
        
        signature = base64.b64encode(
            hmac.new(
                credentials['secret'].encode('utf-8'),
                str_to_sign.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode()
        
        passphrase = base64.b64encode(
            hmac.new(
                credentials['secret'].encode('utf-8'),
                credentials['password'].encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode()
        
        headers = {
            'KC-API-KEY': credentials['apiKey'],
            'KC-API-SIGN': signature,
            'KC-API-TIMESTAMP': timestamp,
            'KC-API-PASSPHRASE': passphrase,
            'KC-API-KEY-VERSION': '2'
        }
        
        url = 'https://api-futures.kucoin.com' + endpoint
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '200000':
                return data.get('data', [])
        return []
    
    except Exception as e:
        print(f"Error fetching positions: {e}")
        return []

def get_active_positions():
    """Get all active positions"""
    positions = fetch_positions()
    active = []
    
    for pos in positions:
        current_qty = float(pos.get('currentQty', 0))
        if current_qty != 0:
            active.append({
                'symbol': pos.get('symbol', ''),
                'side': 'LONG' if current_qty > 0 else 'SHORT',
                'quantity': abs(current_qty),
                'entry_price': float(pos.get('avgEntryPrice', 0)),
                'mark_price': float(pos.get('markPrice', 0)),
                'leverage': float(pos.get('realLeverage', 1)),
                'unrealized_pnl': float(pos.get('unrealisedPnl', 0)),
                'unrealized_roe': float(pos.get('unrealisedRoePcnt', 0)) * 100,
                'liquidation_price': float(pos.get('liquidationPrice', 0)),
                'margin': float(pos.get('maintMargin', 0)),
                'liquidation_distance': abs((float(pos.get('markPrice', 0)) - float(pos.get('liquidationPrice', 0))) / float(pos.get('markPrice', 1))) * 100
            })
    
    return active

def close_position(symbol, quantity, side):
    """
    Close position by placing market order
    
    Args:
        symbol: Futures symbol (e.g., TIAUSDTM)
        quantity: Contract quantity
        side: 'LONG' or 'SHORT'
    
    Returns:
        dict: Order response or None
    """
    try:
        credentials = {
            'apiKey': os.getenv('KUCOIN_API_KEY'),
            'secret': os.getenv('KUCOIN_API_SECRET'),
            'password': os.getenv('KUCOIN_API_PASSPHRASE')
        }
        
        close_side = 'sell' if side == 'LONG' else 'buy'
        
        order_data = {
            'clientOid': f"close_{int(time.time() * 1000)}",
            'side': close_side,
            'symbol': symbol,
            'type': 'market',
            'size': int(quantity),
            'reduceOnly': True
        }
        
        timestamp = str(int(time.time() * 1000))
        endpoint = '/api/v1/orders'
        body = str(order_data).replace("'", '"').replace(' ', '')
        str_to_sign = timestamp + 'POST' + endpoint + body
        
        signature = base64.b64encode(
            hmac.new(
                credentials['secret'].encode('utf-8'),
                str_to_sign.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode()
        
        passphrase = base64.b64encode(
            hmac.new(
                credentials['secret'].encode('utf-8'),
                credentials['password'].encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode()
        
        headers = {
            'KC-API-KEY': credentials['apiKey'],
            'KC-API-SIGN': signature,
            'KC-API-TIMESTAMP': timestamp,
            'KC-API-PASSPHRASE': passphrase,
            'KC-API-KEY-VERSION': '2',
            'Content-Type': 'application/json'
        }
        
        url = 'https://api-futures.kucoin.com' + endpoint
        response = requests.post(url, json=order_data, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '200000':
                return data.get('data', {})
        
        return None
    
    except Exception as e:
        print(f"Error closing position: {e}")
        return None

def get_market_data(exchange, symbol, timeframes=['15m', '1h', '4h']):
    """
    Fetch market data and calculate indicators for multiple timeframes
    
    Args:
        exchange: ccxt exchange object
        symbol: Spot symbol (e.g., 'TIA/USDT')
        timeframes: List of timeframes
    
    Returns:
        dict: Market data with indicators
    """
    from core.indicators import (
        calculate_rsi, calculate_ema, calculate_macd, calculate_stochastic_rsi,
        calculate_adx, calculate_atr, calculate_bollinger_bands, calculate_obv, calculate_vwap
    )
    
    try:
        ticker = exchange.fetch_ticker(symbol)
        
        data = {
            'price': ticker['last'],
            'change_24h': ticker['percentage'],
            'high_24h': ticker['high'],
            'low_24h': ticker['low'],
            'volume': ticker['quoteVolume'],
        }
        
        for tf in timeframes:
            ohlcv = exchange.fetch_ohlcv(symbol, tf, limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Calculate indicators
            rsi = calculate_rsi(df['close']).iloc[-1]
            ema20 = calculate_ema(df['close'], 20).iloc[-1]
            ema50 = calculate_ema(df['close'], 50).iloc[-1]
            macd, signal, hist = calculate_macd(df['close'])
            stoch_k, stoch_d = calculate_stochastic_rsi(df['close'])
            adx, plus_di, minus_di = calculate_adx(df)
            atr = calculate_atr(df).iloc[-1]
            bb_upper, bb_mid, bb_lower = calculate_bollinger_bands(df['close'])
            obv = calculate_obv(df)
            vwap = calculate_vwap(df).iloc[-1]
            
            # Volume analysis
            vol_ma = df['volume'].rolling(window=20).mean().iloc[-1]
            vol_ratio = df['volume'].iloc[-1] / vol_ma if vol_ma > 0 else 1
            obv_slope = (obv.iloc[-1] - obv.iloc[-10]) / 10
            
            # Store with timeframe prefix
            prefix = tf.replace('m', 'M').replace('h', 'H')
            data[f'rsi_{prefix}'] = rsi
            data[f'ema20_{prefix}'] = ema20
            data[f'ema50_{prefix}'] = ema50
            data[f'macd_{prefix}'] = macd.iloc[-1]
            data[f'macd_signal_{prefix}'] = signal.iloc[-1]
            data[f'macd_hist_{prefix}'] = hist.iloc[-1]
            data[f'stoch_k_{prefix}'] = stoch_k.iloc[-1]
            data[f'stoch_d_{prefix}'] = stoch_d.iloc[-1]
            data[f'adx_{prefix}'] = adx.iloc[-1]
            data[f'plus_di_{prefix}'] = plus_di.iloc[-1]
            data[f'minus_di_{prefix}'] = minus_di.iloc[-1]
            data[f'atr_{prefix}'] = atr
            data[f'bb_upper_{prefix}'] = bb_upper.iloc[-1]
            data[f'bb_mid_{prefix}'] = bb_mid.iloc[-1]
            data[f'bb_lower_{prefix}'] = bb_lower.iloc[-1]
            data[f'vwap_{prefix}'] = vwap
            data[f'obv_slope_{prefix}'] = obv_slope
            data[f'vol_ratio_{prefix}'] = vol_ratio
            data[f'trend_{prefix}'] = 'UP' if ema20 > ema50 else 'DOWN'
        
        return data
    
    except Exception as e:
        print(f"Error fetching market data: {e}")
        return None
