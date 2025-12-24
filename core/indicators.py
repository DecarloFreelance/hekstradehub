"""
Technical indicators module for crypto trading analysis.
Provides common indicators like EMA, MACD, RSI, ADX, ATR, Bollinger Bands, OBV, and VWAP.
"""

import pandas as pd
import numpy as np


def calculate_ema(series, period):
    """
    Calculate Exponential Moving Average.
    
    Args:
        series: pandas Series of prices
        period: EMA period
        
    Returns:
        pandas Series with EMA values
    """
    return series.ewm(span=period, adjust=False).mean()


def calculate_macd(series, fast=12, slow=26, signal=9):
    """
    Calculate MACD (Moving Average Convergence Divergence).
    
    Args:
        series: pandas Series of prices
        fast: fast EMA period (default 12)
        slow: slow EMA period (default 26)
        signal: signal line period (default 9)
        
    Returns:
        tuple: (macd_line, signal_line, histogram)
    """
    ema_fast = calculate_ema(series, fast)
    ema_slow = calculate_ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def calculate_rsi(series, period=14):
    """
    Calculate Relative Strength Index.
    
    Args:
        series: pandas Series of prices
        period: RSI period (default 14)
        
    Returns:
        pandas Series with RSI values
    """
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / (loss + 1e-9)
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_stochastic_rsi(series, period=14, smooth_k=3, smooth_d=3):
    """
    Calculate Stochastic RSI.
    
    Args:
        series: pandas Series of prices
        period: RSI period (default 14)
        smooth_k: K smoothing period (default 3)
        smooth_d: D smoothing period (default 3)
        
    Returns:
        tuple: (stoch_k, stoch_d)
    """
    rsi = calculate_rsi(series, period)
    
    # Calculate stochastic of RSI
    min_rsi = rsi.rolling(window=period).min()
    max_rsi = rsi.rolling(window=period).max()
    
    stoch_rsi = (rsi - min_rsi) / (max_rsi - min_rsi + 1e-9) * 100
    
    # Smooth K and D
    stoch_k = stoch_rsi.rolling(window=smooth_k).mean()
    stoch_d = stoch_k.rolling(window=smooth_d).mean()
    
    return stoch_k, stoch_d


def calculate_adx(df, period=14):
    """
    Calculate Average Directional Index (ADX).
    
    Args:
        df: DataFrame with 'high', 'low', 'close' columns
        period: ADX period (default 14)
        
    Returns:
        pandas Series with ADX values
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    # True Range
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Directional Movement
    dm_plus = high.diff()
    dm_minus = -low.diff()
    
    dm_plus[dm_plus < 0] = 0
    dm_minus[dm_minus < 0] = 0
    dm_plus[(dm_plus < dm_minus)] = 0
    dm_minus[(dm_minus < dm_plus)] = 0
    
    # Smoothed TR and DM
    tr_smooth = tr.rolling(window=period).sum()
    dm_plus_smooth = dm_plus.rolling(window=period).sum()
    dm_minus_smooth = dm_minus.rolling(window=period).sum()
    
    # Directional Indicators
    di_plus = (dm_plus_smooth / (tr_smooth + 1e-9)) * 100
    di_minus = (dm_minus_smooth / (tr_smooth + 1e-9)) * 100
    
    # DX and ADX
    dx = abs(di_plus - di_minus) / (di_plus + di_minus + 1e-9) * 100
    adx = dx.rolling(window=period).mean()
    
    return adx


def calculate_atr(df, period=14):
    """
    Calculate Average True Range.
    
    Args:
        df: DataFrame with 'high', 'low', 'close' columns
        period: ATR period (default 14)
        
    Returns:
        pandas Series with ATR values
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    # True Range
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Average True Range
    atr = tr.rolling(window=period).mean()
    
    return atr


def calculate_bollinger_bands(series, period=20, std_dev=2):
    """
    Calculate Bollinger Bands.
    
    Args:
        series: pandas Series of prices
        period: Moving average period (default 20)
        std_dev: Standard deviation multiplier (default 2)
        
    Returns:
        tuple: (upper_band, middle_band, lower_band)
    """
    middle_band = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    
    upper_band = middle_band + (std * std_dev)
    lower_band = middle_band - (std * std_dev)
    
    return upper_band, middle_band, lower_band


def calculate_obv(df):
    """
    Calculate On-Balance Volume.
    
    Args:
        df: DataFrame with 'close' and 'volume' columns
        
    Returns:
        pandas Series with OBV values
    """
    close = df['close']
    volume = df['volume']
    
    obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
    
    return obv


def calculate_vwap(df):
    """
    Calculate Volume Weighted Average Price.
    
    Args:
        df: DataFrame with 'high', 'low', 'close', 'volume' columns
        
    Returns:
        pandas Series with VWAP values
    """
    high = df['high']
    low = df['low']
    close = df['close']
    volume = df['volume']
    
    # Typical price
    typical_price = (high + low + close) / 3
    
    # VWAP calculation
    vwap = (typical_price * volume).cumsum() / volume.cumsum()
    
    return vwap


def calculate_sma(series, period):
    """
    Calculate Simple Moving Average.
    
    Args:
        series: pandas Series of prices
        period: SMA period
        
    Returns:
        pandas Series with SMA values
    """
    return series.rolling(window=period).mean()


def calculate_volume_ratio(df, period=20):
    """
    Calculate current volume ratio vs average.
    
    Args:
        df: DataFrame with 'volume' column
        period: lookback period for average (default 20)
        
    Returns:
        float: current volume / average volume
    """
    volume = df['volume']
    vol_avg = volume.rolling(window=period).mean().iloc[-1]
    vol_current = volume.iloc[-1]
    
    return vol_current / vol_avg if vol_avg > 0 else 1.0


def calculate_obv_slope(df, period=5):
    """
    Calculate OBV slope (rate of change).
    
    Args:
        df: DataFrame with 'close' and 'volume' columns
        period: period for slope calculation (default 5)
        
    Returns:
        float: OBV slope
    """
    obv = calculate_obv(df)
    obv_slope = obv.diff(period).iloc[-1]
    
    return obv_slope
