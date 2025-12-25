"""
Multi-Timeframe Confirmation System
Analyzes market structure across multiple timeframes for high-probability setups
"""

import pandas as pd
import ccxt
from typing import Dict, Tuple, List, Optional
from core.indicators import (
    calculate_ema, calculate_macd, calculate_rsi,
    calculate_stochastic_rsi, calculate_adx, calculate_atr,
    calculate_bollinger_bands, calculate_obv, calculate_vwap
)


class TimeframeAnalyzer:
    """
    Analyzes market conditions across multiple timeframes.
    Implements institutional-grade confirmation logic.
    """
    
    # Timeframe hierarchy: Higher = more important
    TIMEFRAMES = {
        '1d': {'weight': 40, 'name': 'Daily', 'candles': 100},
        '4h': {'weight': 30, 'name': '4-Hour', 'candles': 150},
        '1h': {'weight': 20, 'name': '1-Hour', 'candles': 200},
        '15m': {'weight': 10, 'name': '15-Minute', 'candles': 200}
    }
    
    def __init__(self, exchange: ccxt.Exchange):
        """
        Initialize Timeframe Analyzer.
        
        Args:
            exchange: ccxt exchange instance
        """
        self.exchange = exchange
    
    def fetch_multi_timeframe_data(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """
        Fetch OHLCV data for all timeframes.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Dictionary of DataFrames by timeframe
        """
        data = {}
        
        for tf, config in self.TIMEFRAMES.items():
            try:
                ohlcv = self.exchange.fetch_ohlcv(
                    symbol, 
                    timeframe=tf, 
                    limit=config['candles']
                )
                df = pd.DataFrame(
                    ohlcv, 
                    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                )
                data[tf] = df
            except Exception as e:
                print(f"Error fetching {tf} data for {symbol}: {e}")
                data[tf] = None
                
        return data
    
    def analyze_timeframe(self, df: pd.DataFrame, timeframe: str) -> Dict:
        """
        Perform comprehensive analysis on a single timeframe.
        
        Args:
            df: OHLCV DataFrame
            timeframe: Timeframe string (e.g., '1h')
            
        Returns:
            Dictionary with analysis results
        """
        if df is None or len(df) < 50:
            return {'valid': False, 'error': 'Insufficient data'}
        
        # Current price
        close = df['close']
        high = df['high']
        low = df['low']
        volume = df['volume']
        current_price = close.iloc[-1]
        
        # === TREND ANALYSIS ===
        ema_20 = calculate_ema(close, 20)
        ema_50 = calculate_ema(close, 50)
        ema_100 = calculate_ema(close, 100)
        ema_200 = calculate_ema(close, 200)
        
        # Trend direction
        trend = 'BULLISH' if ema_20.iloc[-1] > ema_50.iloc[-1] > ema_100.iloc[-1] else \
                'BEARISH' if ema_20.iloc[-1] < ema_50.iloc[-1] < ema_100.iloc[-1] else \
                'NEUTRAL'
        
        # Trend strength (slope of EMA 50)
        ema_50_slope = (ema_50.iloc[-1] - ema_50.iloc[-10]) / ema_50.iloc[-10] * 100
        
        # Price position relative to EMAs
        above_all_emas = current_price > ema_20.iloc[-1] > ema_50.iloc[-1] > ema_100.iloc[-1]
        below_all_emas = current_price < ema_20.iloc[-1] < ema_50.iloc[-1] < ema_100.iloc[-1]
        
        # === MOMENTUM ANALYSIS ===
        rsi = calculate_rsi(close, 14)
        rsi_val = rsi.iloc[-1]
        
        # RSI trend
        rsi_slope = rsi.iloc[-1] - rsi.iloc[-5]
        rsi_oversold = rsi_val < 30
        rsi_overbought = rsi_val > 70
        rsi_bullish_range = 40 < rsi_val < 70
        rsi_bearish_range = 30 < rsi_val < 60
        
        # MACD
        macd_line, signal_line, hist = calculate_macd(close)
        macd_hist = hist.iloc[-1]
        macd_bullish = macd_line.iloc[-1] > signal_line.iloc[-1]
        macd_crossover = (macd_line.iloc[-1] > signal_line.iloc[-1]) and \
                        (macd_line.iloc[-2] <= signal_line.iloc[-2])
        
        # Stochastic RSI
        stoch_k, stoch_d = calculate_stochastic_rsi(close)
        stoch_k_val = stoch_k.iloc[-1]
        stoch_oversold = stoch_k_val < 20
        stoch_overbought = stoch_k_val > 80
        
        # === STRENGTH ANALYSIS ===
        adx = calculate_adx(df, 14)
        adx_val = adx.iloc[-1]
        strong_trend = adx_val > 25
        very_strong_trend = adx_val > 40
        
        # === VOLATILITY ANALYSIS ===
        atr = calculate_atr(df, 14)
        atr_val = atr.iloc[-1]
        atr_pct = (atr_val / current_price) * 100
        
        bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(close)
        bb_width = ((bb_upper.iloc[-1] - bb_lower.iloc[-1]) / bb_middle.iloc[-1]) * 100
        bb_position = ((current_price - bb_lower.iloc[-1]) / 
                      (bb_upper.iloc[-1] - bb_lower.iloc[-1])) * 100
        
        # === VOLUME ANALYSIS ===
        volume_sma = volume.rolling(20).mean()
        volume_ratio = volume.iloc[-1] / volume_sma.iloc[-1] if volume_sma.iloc[-1] > 0 else 1
        
        obv = calculate_obv(df)
        obv_sma = obv.rolling(20).mean()
        obv_trend = 'RISING' if obv.iloc[-1] > obv_sma.iloc[-1] else 'FALLING'
        
        # VWAP
        vwap = calculate_vwap(df)
        vwap_val = vwap.iloc[-1]
        above_vwap = current_price > vwap_val
        
        # === MARKET STRUCTURE ===
        # Identify swing highs and lows
        swing_high_recent = high.rolling(10, center=True).max().iloc[-6]
        swing_low_recent = low.rolling(10, center=True).min().iloc[-6]
        
        # Higher highs / Lower lows
        prev_swing_high = high.rolling(10, center=True).max().iloc[-16]
        prev_swing_low = low.rolling(10, center=True).min().iloc[-16]
        
        higher_high = swing_high_recent > prev_swing_high
        higher_low = swing_low_recent > prev_swing_low
        lower_high = swing_high_recent < prev_swing_high
        lower_low = swing_low_recent < prev_swing_low
        
        # Market structure
        if higher_high and higher_low:
            market_structure = 'UPTREND'
        elif lower_high and lower_low:
            market_structure = 'DOWNTREND'
        else:
            market_structure = 'RANGING'
        
        return {
            'valid': True,
            'timeframe': timeframe,
            'price': current_price,
            
            # Trend
            'trend': trend,
            'trend_strength': abs(ema_50_slope),
            'above_all_emas': above_all_emas,
            'below_all_emas': below_all_emas,
            'ema_20': ema_20.iloc[-1],
            'ema_50': ema_50.iloc[-1],
            'ema_100': ema_100.iloc[-1],
            'ema_200': ema_200.iloc[-1],
            
            # Momentum
            'rsi': rsi_val,
            'rsi_slope': rsi_slope,
            'rsi_oversold': rsi_oversold,
            'rsi_overbought': rsi_overbought,
            'rsi_bullish_range': rsi_bullish_range,
            'rsi_bearish_range': rsi_bearish_range,
            'macd_hist': macd_hist,
            'macd_bullish': macd_bullish,
            'macd_crossover': macd_crossover,
            'stoch_k': stoch_k_val,
            'stoch_oversold': stoch_oversold,
            'stoch_overbought': stoch_overbought,
            
            # Strength
            'adx': adx_val,
            'strong_trend': strong_trend,
            'very_strong_trend': very_strong_trend,
            
            # Volatility
            'atr': atr_val,
            'atr_pct': atr_pct,
            'bb_width': bb_width,
            'bb_position': bb_position,
            
            # Volume
            'volume_ratio': volume_ratio,
            'obv_trend': obv_trend,
            'above_vwap': above_vwap,
            'vwap': vwap_val,
            
            # Market Structure
            'market_structure': market_structure,
            'higher_high': higher_high,
            'higher_low': higher_low,
            'lower_high': lower_high,
            'lower_low': lower_low
        }
    
    def calculate_confluence_score(self, 
                                   analyses: Dict[str, Dict],
                                   direction: str = 'LONG') -> Dict:
        """
        Calculate weighted confluence score across all timeframes.
        
        Args:
            analyses: Dictionary of timeframe analyses
            direction: 'LONG' or 'SHORT'
            
        Returns:
            Dictionary with confluence score and details
        """
        total_score = 0
        max_score = 0
        details = []
        
        for tf, analysis in analyses.items():
            if not analysis.get('valid'):
                continue
                
            tf_weight = self.TIMEFRAMES[tf]['weight']
            tf_score = 0
            tf_max = 100
            
            if direction == 'LONG':
                # Trend alignment (40 pts)
                if analysis['trend'] == 'BULLISH':
                    tf_score += 30
                elif analysis['trend'] == 'NEUTRAL':
                    tf_score += 10
                    
                if analysis['above_all_emas']:
                    tf_score += 10
                    
                # Momentum (30 pts)
                if analysis['rsi_bullish_range']:
                    tf_score += 10
                if analysis['macd_bullish']:
                    tf_score += 10
                if analysis['macd_crossover']:
                    tf_score += 5
                if not analysis['stoch_overbought']:
                    tf_score += 5
                    
                # Strength (15 pts)
                if analysis['strong_trend']:
                    tf_score += 10
                if analysis['very_strong_trend']:
                    tf_score += 5
                    
                # Volume (15 pts)
                if analysis['volume_ratio'] > 1.2:
                    tf_score += 7
                if analysis['obv_trend'] == 'RISING':
                    tf_score += 5
                if analysis['above_vwap']:
                    tf_score += 3
                    
            else:  # SHORT
                # Trend alignment (40 pts)
                if analysis['trend'] == 'BEARISH':
                    tf_score += 30
                elif analysis['trend'] == 'NEUTRAL':
                    tf_score += 10
                    
                if analysis['below_all_emas']:
                    tf_score += 10
                    
                # Momentum (30 pts)
                if analysis['rsi_bearish_range']:
                    tf_score += 10
                if not analysis['macd_bullish']:
                    tf_score += 10
                if not analysis['stoch_oversold']:
                    tf_score += 5
                if analysis['rsi_overbought']:
                    tf_score += 5
                    
                # Strength (15 pts)
                if analysis['strong_trend']:
                    tf_score += 10
                if analysis['very_strong_trend']:
                    tf_score += 5
                    
                # Volume (15 pts)
                if analysis['volume_ratio'] > 1.2:
                    tf_score += 7
                if analysis['obv_trend'] == 'FALLING':
                    tf_score += 5
                if not analysis['above_vwap']:
                    tf_score += 3
            
            # Apply timeframe weight
            weighted_score = (tf_score / tf_max) * tf_weight
            total_score += weighted_score
            max_score += tf_weight
            
            details.append({
                'timeframe': tf,
                'score': tf_score,
                'weighted_score': weighted_score,
                'weight': tf_weight,
                'trend': analysis['trend'],
                'market_structure': analysis['market_structure']
            })
        
        final_score = (total_score / max_score) * 100 if max_score > 0 else 0
        
        # Determine signal strength
        if final_score >= 75:
            signal = 'STRONG_' + direction
        elif final_score >= 60:
            signal = direction
        elif final_score >= 50:
            signal = 'WEAK_' + direction
        else:
            signal = 'NO_SIGNAL'
        
        return {
            'score': round(final_score, 2),
            'signal': signal,
            'direction': direction,
            'timeframe_details': details,
            'timestamp': pd.Timestamp.now()
        }
    
    def find_entry_zone(self, 
                       analyses: Dict[str, Dict],
                       direction: str = 'LONG') -> Dict:
        """
        Identify optimal entry zone based on multiple timeframes.
        
        Args:
            analyses: Dictionary of timeframe analyses
            direction: 'LONG' or 'SHORT'
            
        Returns:
            Dictionary with entry zone recommendations
        """
        # Use 15m for entry timing, higher TFs for bias
        entry_tf = analyses.get('15m')
        bias_tf = analyses.get('4h')
        
        if not entry_tf or not bias_tf:
            return {'valid': False, 'error': 'Missing timeframe data'}
        
        current_price = entry_tf['price']
        
        if direction == 'LONG':
            # Entry zone: between EMA 20 and EMA 50 on 15m
            entry_high = entry_tf['ema_20']
            entry_low = entry_tf['ema_50']
            
            # Aggressive entry: current price
            # Conservative entry: wait for pullback to EMA 20
            aggressive_entry = current_price
            conservative_entry = entry_low
            optimal_entry = (entry_high + entry_low) / 2
            
            # Invalidation: break below EMA 200 on 4h
            invalidation = bias_tf['ema_200']
            
        else:  # SHORT
            # Entry zone: between EMA 20 and EMA 50 on 15m
            entry_low = entry_tf['ema_20']
            entry_high = entry_tf['ema_50']
            
            aggressive_entry = current_price
            conservative_entry = entry_high
            optimal_entry = (entry_high + entry_low) / 2
            
            # Invalidation: break above EMA 200 on 4h
            invalidation = bias_tf['ema_200']
        
        # ATR-based stop loss
        atr = entry_tf['atr']
        if direction == 'LONG':
            atr_stop = optimal_entry - (atr * 1.5)
        else:
            atr_stop = optimal_entry + (atr * 1.5)
        
        return {
            'valid': True,
            'direction': direction,
            'current_price': current_price,
            'aggressive_entry': aggressive_entry,
            'optimal_entry': optimal_entry,
            'conservative_entry': conservative_entry,
            'atr_stop_loss': atr_stop,
            'invalidation_level': invalidation,
            'atr': atr,
            'entry_zone_width': abs(entry_high - entry_low)
        }
    
    def get_confirmation_checklist(self,
                                   analyses: Dict[str, Dict],
                                   direction: str = 'LONG') -> Dict:
        """
        Generate a checklist of confirmations met.
        
        Args:
            analyses: Dictionary of timeframe analyses
            direction: 'LONG' or 'SHORT'
            
        Returns:
            Dictionary with checklist items
        """
        checklist = []
        passed = 0
        total = 0
        
        # Get key timeframes
        daily = analyses.get('1d', {})
        four_h = analyses.get('4h', {})
        one_h = analyses.get('1h', {})
        fifteen_m = analyses.get('15m', {})
        
        if direction == 'LONG':
            checks = [
                ('Daily trend bullish', daily.get('trend') == 'BULLISH'),
                ('4H trend bullish', four_h.get('trend') == 'BULLISH'),
                ('1H trend bullish', one_h.get('trend') == 'BULLISH'),
                ('15M trend bullish', fifteen_m.get('trend') == 'BULLISH'),
                ('Price above all EMAs (4H)', four_h.get('above_all_emas', False)),
                ('RSI in bullish range', fifteen_m.get('rsi_bullish_range', False)),
                ('MACD bullish', fifteen_m.get('macd_bullish', False)),
                ('Strong ADX (>25)', fifteen_m.get('strong_trend', False)),
                ('Above VWAP', fifteen_m.get('above_vwap', False)),
                ('Volume confirmation', fifteen_m.get('volume_ratio', 0) > 1.0),
                ('OBV rising', fifteen_m.get('obv_trend') == 'RISING'),
                ('Market structure uptrend', four_h.get('market_structure') == 'UPTREND')
            ]
        else:  # SHORT
            checks = [
                ('Daily trend bearish', daily.get('trend') == 'BEARISH'),
                ('4H trend bearish', four_h.get('trend') == 'BEARISH'),
                ('1H trend bearish', one_h.get('trend') == 'BEARISH'),
                ('15M trend bearish', fifteen_m.get('trend') == 'BEARISH'),
                ('Price below all EMAs (4H)', four_h.get('below_all_emas', False)),
                ('RSI in bearish range', fifteen_m.get('rsi_bearish_range', False)),
                ('MACD bearish', not fifteen_m.get('macd_bullish', True)),
                ('Strong ADX (>25)', fifteen_m.get('strong_trend', False)),
                ('Below VWAP', not fifteen_m.get('above_vwap', True)),
                ('Volume confirmation', fifteen_m.get('volume_ratio', 0) > 1.0),
                ('OBV falling', fifteen_m.get('obv_trend') == 'FALLING'),
                ('Market structure downtrend', four_h.get('market_structure') == 'DOWNTREND')
            ]
        
        for description, result in checks:
            total += 1
            if result:
                passed += 1
                checklist.append({'item': description, 'passed': True})
            else:
                checklist.append({'item': description, 'passed': False})
        
        return {
            'checklist': checklist,
            'passed': passed,
            'total': total,
            'pass_rate': (passed / total) * 100 if total > 0 else 0
        }
