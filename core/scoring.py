import numpy as np
import pandas as pd

# ============================================================
# HELPERS
# ============================================================

def normalize(value, min_v, max_v):
    """Normalize a value to the 0–100 range safely."""
    return float(np.clip((value - min_v) / (max_v - min_v + 1e-9), 0, 1) * 100)


def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()


def rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))


# ============================================================
# MAIN MODEL
# ============================================================

def score_asset(df):
    """
    Score an asset based on multiple technical factors.
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        dict with scores and signal
    """
    # Convert to float
    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    volume = df["volume"].astype(float)
    
    # STRUCTURE (placeholder)
    structure_score = 50

    # --------------------------------------------------------
    # TREND FACTOR
    # --------------------------------------------------------
    ema20 = ema(close, 20)
    ema50 = ema(close, 50)

    slope_short = ema20.diff().iloc[-1]
    slope_mid = ema50.diff().iloc[-1]
    slope_score = normalize(slope_short + slope_mid, -0.02, 0.02)

    tr = high - low
    dm_up = np.maximum(high.diff(), 0)
    dm_down = np.maximum(-low.diff(), 0)
    tr14 = tr.rolling(14).sum()

    plus_di = (dm_up.rolling(14).sum() / (tr14 + 1e-9)) * 100
    minus_di = (dm_down.rolling(14).sum() / (tr14 + 1e-9)) * 100

    adx_raw = abs(plus_di - minus_di).iloc[-1]
    adx_score = normalize(adx_raw, 0, 40)

    trend_score = 0.4 * slope_score + 0.6 * adx_score

    # --------------------------------------------------------
    # MOMENTUM
    # --------------------------------------------------------
    roc = ((close.iloc[-1] - close.iloc[-10]) / close.iloc[-10]) * 100

    macd_line = ema(close, 12) - ema(close, 26)
    macd_hist = macd_line - ema(macd_line, 9)

    momentum_score = (
        normalize(roc, -5, 5) * 0.4 +
        normalize(macd_hist.iloc[-1], -1, 1) * 0.6
    )

    # --------------------------------------------------------
    # VOLATILITY
    # --------------------------------------------------------
    atr = (high - low).rolling(14).mean()
    atr_pct = atr.iloc[-1] / close.iloc[-1]

    volatility_score = normalize(atr_pct, 0.005, 0.04)

    # --------------------------------------------------------
    # VOLUME
    # --------------------------------------------------------
    obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
    obv_slope = obv.diff().iloc[-1]

    vol_z = (
        (volume.iloc[-1] - volume.rolling(50).mean().iloc[-1]) /
        (volume.rolling(50).std().iloc[-1] + 1e-9)
    )

    volume_score = (
        normalize(obv_slope, -1e6, 1e6) * 0.5 +
        normalize(vol_z, -3, 3) * 0.5
    )

    # --------------------------------------------------------
    # MEAN REVERSION / REVERSAL
    # --------------------------------------------------------
    r = rsi(close).iloc[-1]
    
    # Reversal scores for long and short
    rev_long = 100 if r < 30 else 0
    rev_short = 100 if r > 70 else 0

    mr_long = (
        normalize(70 - r, 0, 40) * 0.6 +
        normalize((close.mean() - close.iloc[-1]) / close.iloc[-1], -0.03, 0.03) * 0.4
    )

    mr_short = (
        normalize(r - 30, 0, 40) * 0.6 +
        normalize((close.iloc[-1] - close.mean()) / close.iloc[-1], -0.03, 0.03) * 0.4
    )

    # --------------------------------------------------------
    # BREAKOUT
    # --------------------------------------------------------
    donchian_high = high.rolling(20).max().iloc[-1]
    donchian_low = low.rolling(20).min().iloc[-1]

    # Normalize final scores to 0-100
    long_score_raw = (
        0.30 * trend_score +
        0.20 * momentum_score +
        0.10 * (100 - volatility_score) +
        0.15 * volume_score +
        0.15 * structure_score +
        0.10 * rev_long
    )
    short_score_raw = (
        0.30 * (100 - trend_score) +
        0.20 * (100 - momentum_score) +
        0.10 * volatility_score +
        0.15 * volume_score +
        0.15 * (100 - structure_score) +
        0.10 * rev_short
    )
    long_score = max(0, min(100, long_score_raw))
    short_score = max(0, min(100, short_score_raw))

    signal = "NEUTRAL"
    if long_score >= 70 and long_score - short_score >= 15:
        signal = "LONG"
    elif short_score >= 70 and short_score - long_score >= 15:
        signal = "SHORT"

    return {
        "long_score": round(long_score, 2),
        "short_score": round(short_score, 2),
        "trend_score": round(trend_score, 2),
        "momentum_score": round(momentum_score, 2),
        "volatility_score": round(volatility_score, 2),
        "volume_score": round(volume_score, 2),
        "signal": signal
    }
