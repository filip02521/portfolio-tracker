"""
Confluence Strategy Service - Advanced trading strategy based on signal confluence
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from logging_config import get_logger

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None
    np = None

try:
    import ta
    TA_AVAILABLE = True
except ImportError:
    TA_AVAILABLE = False

logger = get_logger(__name__)


class ConfluenceStrategyService:
    """Service for confluence-based trading strategy"""
    
    def __init__(self, market_data_service):
        """
        Initialize the confluence strategy service
        
        Args:
            market_data_service: Instance of MarketDataService for fetching market data
        """
        self.market_data_service = market_data_service
        self.logger = logger
        
        # Cache for calculated indicators
        self._indicators_cache = {}
        self._cache_ttl = 300  # 5 minutes
        
    def _get_from_cache(self, cache: Dict, key: str) -> Optional[Dict]:
        """Get value from cache if not expired"""
        if key in cache:
            entry = cache[key]
            if datetime.now().timestamp() - entry['timestamp'] < self._cache_ttl:
                return entry['data']
            else:
                del cache[key]
        return None
    
    def _save_to_cache(self, cache: Dict, key: str, data: Dict):
        """Save value to cache"""
        cache[key] = {
            'data': data,
            'timestamp': datetime.now().timestamp()
        }
    
    def _detect_pin_bar(self, df) -> Dict:
        """
        Detect Pin Bar patterns (bullish/bearish)
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            Dict with pin bar detection results
        """
        try:
            if not PANDAS_AVAILABLE or df is None or len(df) < 2:
                return {}
            
            patterns = {}
            
            # Get last candle
            curr_candle = df.iloc[-1]
            prev_candle = df.iloc[-2] if len(df) >= 2 else None
            
            # Calculate body and wicks
            curr_body = abs(curr_candle['close'] - curr_candle['open'])
            curr_range = curr_candle['high'] - curr_candle['low']
            
            if curr_range == 0:
                return {}
            
            body_ratio = curr_body / curr_range if curr_range > 0 else 0
            lower_wick = curr_candle['low'] - min(curr_candle['open'], curr_candle['close'])
            upper_wick = curr_candle['high'] - max(curr_candle['open'], curr_candle['close'])
            
            # Bullish Pin Bar: small body, long lower wick, small upper wick
            # Body ratio < 0.3, lower wick > 2x body, upper wick < body
            if body_ratio < 0.3 and lower_wick > 2 * curr_body and upper_wick < curr_body:
                # Check if it's at support (price near recent low)
                if prev_candle is not None:
                    recent_low = df['low'].tail(10).min()
                    if abs(curr_candle['low'] - recent_low) / recent_low < 0.02:  # Within 2% of recent low
                        patterns['bullish_pin_bar'] = {
                            'signal': 'buy',
                            'strength': 0.8,
                            'confidence': 0.75,
                            'price': float(curr_candle['close']),
                            'pattern': 'Bullish Pin Bar at support'
                        }
            
            # Bearish Pin Bar: small body, long upper wick, small lower wick
            # Body ratio < 0.3, upper wick > 2x body, lower wick < body
            if body_ratio < 0.3 and upper_wick > 2 * curr_body and lower_wick < curr_body:
                # Check if it's at resistance (price near recent high)
                if prev_candle is not None:
                    recent_high = df['high'].tail(10).max()
                    if abs(curr_candle['high'] - recent_high) / recent_high < 0.02:  # Within 2% of recent high
                        patterns['bearish_pin_bar'] = {
                            'signal': 'sell',
                            'strength': 0.8,
                            'confidence': 0.75,
                            'price': float(curr_candle['close']),
                            'pattern': 'Bearish Pin Bar at resistance'
                        }
            
            return patterns
        except Exception as e:
            self.logger.debug(f"Error detecting pin bar: {e}")
            return {}
    
    def _detect_market_structure(self, df) -> Dict:
        """
        Detect market structure (Higher High / Lower Low)
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            Dict with market structure analysis
        """
        try:
            if not PANDAS_AVAILABLE or df is None or len(df) < 20:
                return {}
            
            highs = df['high'].values
            lows = df['low'].values
            
            # Detect swing highs and lows (similar to _detect_chart_patterns)
            swing_highs = []
            swing_lows = []
            lookback = min(5, len(df) // 4)
            
            for i in range(lookback, len(df) - lookback):
                # Check if current high is a swing high
                if all(highs[i] >= highs[i-j] for j in range(1, lookback+1)) and \
                   all(highs[i] >= highs[i+j] for j in range(1, lookback+1)):
                    swing_highs.append((i, highs[i]))
                
                # Check if current low is a swing low
                if all(lows[i] <= lows[i-j] for j in range(1, lookback+1)) and \
                   all(lows[i] <= lows[i+j] for j in range(1, lookback+1)):
                    swing_lows.append((i, lows[i]))
            
            # Analyze structure
            higher_highs = False
            lower_lows = False
            structure = 'sideways'
            
            if len(swing_highs) >= 2:
                # Check if we have Higher Highs
                last_two_highs = swing_highs[-2:]
                if last_two_highs[1][1] > last_two_highs[0][1]:
                    higher_highs = True
            
            if len(swing_lows) >= 2:
                # Check if we have Lower Lows
                last_two_lows = swing_lows[-2:]
                if last_two_lows[1][1] < last_two_lows[0][1]:
                    lower_lows = True
            
            # Determine structure
            if higher_highs and not lower_lows:
                structure = 'uptrend'
            elif lower_lows and not higher_highs:
                structure = 'downtrend'
            elif higher_highs and lower_lows:
                structure = 'volatile'  # Mixed signals
            else:
                structure = 'sideways'
            
            return {
                'structure': structure,
                'higher_highs': higher_highs,
                'lower_lows': lower_lows,
                'swing_highs': swing_highs[-3:] if len(swing_highs) >= 3 else swing_highs,
                'swing_lows': swing_lows[-3:] if len(swing_lows) >= 3 else swing_lows
            }
        except Exception as e:
            self.logger.debug(f"Error detecting market structure: {e}")
            return {}
    
    def _analyze_ema_confluence(self, df) -> Dict:
        """
        Analyze EMA confluence (EMA 10, 20, 50, 200)
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            Dict with EMA analysis results
        """
        try:
            if not PANDAS_AVAILABLE or df is None:
                return {}
            
            # Reduce minimum requirement - work with available data
            if len(df) < 50:
                return {}
            
            close = df['close'].values
            current_price = close[-1]
            
            # Calculate EMAs using ta library
            if not TA_AVAILABLE:
                self.logger.warning("ta library not available for EMA calculation")
                return {}
            
            # Adjust EMA windows based on available data
            max_period = len(df)
            ema10_period = min(10, max_period // 5) if max_period < 50 else 10
            ema20_period = min(20, max_period // 3) if max_period < 60 else 20
            ema50_period = min(50, max_period // 2) if max_period < 100 else 50
            ema200_period = min(200, max_period - 10) if max_period < 210 else 200
            
            ema10_series = ta.trend.EMAIndicator(pd.Series(close), window=ema10_period).ema_indicator()
            ema20_series = ta.trend.EMAIndicator(pd.Series(close), window=ema20_period).ema_indicator()
            ema50_series = ta.trend.EMAIndicator(pd.Series(close), window=ema50_period).ema_indicator() if ema50_period >= 50 else None
            ema200_series = ta.trend.EMAIndicator(pd.Series(close), window=ema200_period).ema_indicator() if ema200_period >= 200 else None
            
            ema10 = ema10_series.iloc[-1] if ema10_series is not None and not pd.isna(ema10_series.iloc[-1]) else None
            ema20 = ema20_series.iloc[-1] if ema20_series is not None and not pd.isna(ema20_series.iloc[-1]) else None
            ema50 = ema50_series.iloc[-1] if ema50_series is not None and not pd.isna(ema50_series.iloc[-1]) else None
            ema200 = ema200_series.iloc[-1] if ema200_series is not None and not pd.isna(ema200_series.iloc[-1]) else None
            
            # Allow partial EMA data - at least need EMA10 and EMA20
            if ema10 is None or ema20 is None:
                return {}
            
            # If EMA50 or EMA200 are missing, use EMA20/EMA50 as fallback
            if ema50 is None:
                ema50 = ema20
            if ema200 is None:
                ema200 = ema50
            
            # Golden Cross: EMA 50 > EMA 200
            golden_cross = ema50 > ema200
            
            # Death Cross: EMA 50 < EMA 200
            death_cross = ema50 < ema200
            
            # Price position relative to EMAs
            price_above_ema10 = current_price > ema10
            price_above_ema20 = current_price > ema20
            price_above_ema50 = current_price > ema50
            price_above_ema200 = current_price > ema200
            
            # Support test: price pulls back to EMA 50 in uptrend
            # Check if price was above EMA 50 recently and now is near EMA 50
            support_test = False
            ema_pullback_and_bounce = False  # NEW: EMA 10/20 cofa się do EMA 50 i odbija
            
            if golden_cross and price_above_ema200:
                # Check if price is within 2% of EMA 50
                if abs(current_price - ema50) / ema50 < 0.02:
                    # Check if price was above EMA 50 in recent candles
                    recent_prices = close[-5:]
                    recent_above_ema50 = sum([p > ema50 for p in recent_prices]) >= 3
                    if recent_above_ema50:
                        support_test = True
                
                # NEW: Check if EMA 10/20 cofa się do EMA 50 i odbija w górę
                # This is a more precise condition from the report
                if len(close) >= 10:
                    # Get EMA values for last 5-10 candles to see if they pulled back
                    try:
                        ema10_history = ema10_series.iloc[-10:].values
                        ema20_history = ema20_series.iloc[-10:].values
                        
                        # Check if EMA 10/20 were above EMA 50 in the past (5-10 candles ago)
                        # and now are closer to or below EMA 50 (recent candles)
                        if len(ema10_history) >= 5 and len(ema20_history) >= 5:
                            # Past: EMA 10/20 were above EMA 50
                            past_ema10_above = ema10_history[-5] > ema50
                            past_ema20_above = ema20_history[-5] > ema50
                            
                            # Recent: EMA 10/20 are closer to EMA 50 (within 3% or below)
                            recent_ema10_near = abs(ema10 - ema50) / ema50 < 0.03 or ema10 <= ema50
                            recent_ema20_near = abs(ema20 - ema50) / ema50 < 0.03 or ema20 <= ema50
                            
                            # Price bounced up (last candle is higher than previous)
                            price_bounced = len(close) >= 2 and close[-1] > close[-2]
                            
                            # All conditions met: EMA 10/20 pulled back to EMA 50 and price bounced
                            if (past_ema10_above or past_ema20_above) and \
                               (recent_ema10_near or recent_ema20_near) and \
                               price_bounced:
                                ema_pullback_and_bounce = True
                    except Exception as e:
                        self.logger.debug(f"Error checking EMA pullback: {e}")
                        pass
            
            # Trend strength: how many EMAs are aligned
            trend_strength = 0.0
            if golden_cross:
                if price_above_ema10 and price_above_ema20 and price_above_ema50 and price_above_ema200:
                    trend_strength = 1.0  # Perfect uptrend alignment
                elif price_above_ema50 and price_above_ema200:
                    trend_strength = 0.7  # Strong uptrend
                elif price_above_ema200:
                    trend_strength = 0.5  # Moderate uptrend
            elif death_cross:
                if not price_above_ema10 and not price_above_ema20 and not price_above_ema50 and not price_above_ema200:
                    trend_strength = -1.0  # Perfect downtrend alignment
                elif not price_above_ema50 and not price_above_ema200:
                    trend_strength = -0.7  # Strong downtrend
                elif not price_above_ema200:
                    trend_strength = -0.5  # Moderate downtrend
            
            return {
                'ema10': float(ema10),
                'ema20': float(ema20),
                'ema50': float(ema50),
                'ema200': float(ema200),
                'golden_cross': golden_cross,
                'death_cross': death_cross,
                'support_test': support_test,
                'ema_pullback_and_bounce': ema_pullback_and_bounce,  # NEW
                'price_above_ema10': price_above_ema10,
                'price_above_ema20': price_above_ema20,
                'price_above_ema50': price_above_ema50,
                'price_above_ema200': price_above_ema200,
                'trend_strength': trend_strength
            }
        except Exception as e:
            self.logger.debug(f"Error analyzing EMA confluence: {e}")
            return {}
    
    def _analyze_volume_breakout(self, df) -> Dict:
        """
        Analyze volume for breakout signals
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            Dict with volume analysis results
        """
        try:
            if not PANDAS_AVAILABLE or df is None or len(df) < 20:
                return {}
            
            if 'volume' not in df.columns:
                return {}
            
            volume = df['volume'].values
            close = df['close'].values
            
            # Calculate average volume over last 20 periods
            avg_volume = np.mean(volume[-20:])
            current_volume = volume[-1]
            
            # Volume ratio
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            # Breakout detection: high volume with price movement
            breakout = False
            signal = 'neutral'
            
            if volume_ratio > 1.5:  # Volume > 1.5x average
                # Check if price is breaking out (above recent high or below recent low)
                recent_high = np.max(close[-20:])
                recent_low = np.min(close[-20:])
                current_price = close[-1]
                
                # Bullish breakout: price breaks above recent high with high volume
                if current_price > recent_high * 0.98:  # Within 2% of recent high
                    breakout = True
                    signal = 'buy'
                # Bearish breakout: price breaks below recent low with high volume
                elif current_price < recent_low * 1.02:  # Within 2% of recent low
                    breakout = True
                    signal = 'sell'
            
            return {
                'volume_ratio': float(volume_ratio),
                'breakout': breakout,
                'signal': signal,
                'current_volume': float(current_volume),
                'avg_volume': float(avg_volume)
            }
        except Exception as e:
            self.logger.debug(f"Error analyzing volume breakout: {e}")
            return {}
    
    def _get_indicators_from_ai_service(self, df, symbol: str) -> Dict:
        """
        Get technical indicators using methods from ai_service.py
        
        This method reuses existing indicator calculation logic
        Uses lazy import to avoid circular dependencies
        """
        try:
            if not PANDAS_AVAILABLE or df is None:
                return {}
            
            # Lazy import to avoid circular dependencies
            from ai_service import AIService
            
            # Create temporary AIService instance (we only need its methods)
            temp_ai = AIService(self.market_data_service)
            
            # Get indicators
            indicators = temp_ai._calculate_technical_indicators(df, symbol)
            
            return indicators
        except ImportError as e:
            self.logger.debug(f"AIService not available: {e}")
            return {}
        except Exception as e:
            self.logger.debug(f"Error getting indicators from ai_service: {e}")
            return {}
    
    def _get_candlestick_patterns(self, df) -> Dict:
        """
        Get candlestick patterns using methods from ai_service.py
        Uses lazy import to avoid circular dependencies
        """
        try:
            if not PANDAS_AVAILABLE or df is None:
                return {}
            
            # Lazy import to avoid circular dependencies
            from ai_service import AIService
            temp_ai = AIService(self.market_data_service)
            patterns = temp_ai._detect_candlestick_patterns(df)
            return patterns
        except ImportError as e:
            self.logger.debug(f"AIService not available: {e}")
            return {}
        except Exception as e:
            self.logger.debug(f"Error getting candlestick patterns: {e}")
            return {}
    
    def analyze_entry_signals(
        self,
        symbol: str,
        interval: str = '4h',
        timeframe: str = '4h'
    ) -> Dict:
        """
        Analyze entry signals based on confluence of multiple indicators
        
        Args:
            symbol: Trading symbol (e.g., 'BTC', 'ETH')
            interval: Data interval ('1h', '4h', '1d')
            timeframe: Timeframe for analysis (same as interval for now)
            
        Returns:
            Dict with entry signal analysis
        """
        try:
            # Get historical data
            # Map interval to prediction_horizon for market_data_service
            # Need more data for EMA 200 calculation (200 candles)
            interval_map = {
                '1h': 30,   # 30 days for hourly data (~720 candles)
                '4h': 120,  # 120 days for 4h data (~720 candles)
                '1w': 240,  # 240 days for weekly data (~240 candles)
                '1d': 300   # 300 days for daily data (~300 candles)
            }
            prediction_horizon = interval_map.get(interval, 120)
            
            historical_data, data_interval = self.market_data_service.get_symbol_history_with_interval(
                symbol, prediction_horizon
            )
            
            # Reduce minimum data requirement - EMA 200 needs 200 candles, but we can work with less
            min_required = 50 if interval == '1d' else 100
            if not historical_data or len(historical_data) < min_required:
                return {
                    'entry_signal': 'hold',
                    'confidence': 0.0,
                    'confluence_score': 0,
                    'entry_price': 0.0,
                    'entry_reasons': [],
                    'error': f'Insufficient historical data ({len(historical_data) if historical_data else 0} candles, need {min_required})'
                }
            
            # Convert to DataFrame
            df = pd.DataFrame(historical_data)
            
            # Ensure required columns exist
            required_cols = ['close', 'open', 'high', 'low']
            for col in required_cols:
                if col not in df.columns:
                    # Try capitalized version
                    if col.capitalize() in df.columns:
                        df[col] = df[col.capitalize()]
                    else:
                        return {
                            'entry_signal': 'hold',
                            'confidence': 0.0,
                            'confluence_score': 0,
                            'entry_price': 0.0,
                            'entry_reasons': [],
                            'error': f'Missing required column: {col}'
                        }
            
            # Get current price
            entry_price = float(df['close'].iloc[-1])
            
            # Calculate all indicators and patterns
            indicators = self._get_indicators_from_ai_service(df, symbol)
            candlestick_patterns = self._get_candlestick_patterns(df)
            pin_bar = self._detect_pin_bar(df)
            market_structure = self._detect_market_structure(df)
            ema_analysis = self._analyze_ema_confluence(df)
            volume_analysis = self._analyze_volume_breakout(df)
            
            # Analyze confluence - 6 conditions
            confluence_conditions = []
            confluence_score = 0
            
            # Condition 1: Uptrend (EMA 50 > EMA 200) OR Golden Cross
            condition1_met = False
            if ema_analysis:
                if ema_analysis.get('golden_cross', False) or ema_analysis.get('trend_strength', 0) > 0.5:
                    condition1_met = True
                    confluence_conditions.append("✅ Uptrend confirmed (EMA 50 > EMA 200 or Golden Cross)")
                    confluence_score += 1
                else:
                    confluence_conditions.append("❌ No uptrend (EMA 50 < EMA 200)")
            
            # Condition 2: Pullback to EMA 50 in uptrend OR price above EMA 50/200
            # NEW: Also check EMA 10/20 pullback and bounce (from report)
            condition2_met = False
            if ema_analysis:
                if ema_analysis.get('ema_pullback_and_bounce', False):
                    # NEW: EMA 10/20 cofa się do EMA 50 i odbija (precise requirement from report)
                    condition2_met = True
                    confluence_conditions.append("✅ EMA 10/20 pulled back to EMA 50 and bounced")
                    confluence_score += 1
                elif ema_analysis.get('support_test', False):
                    condition2_met = True
                    confluence_conditions.append("✅ Pullback to EMA 50 support in uptrend")
                    confluence_score += 1
                elif ema_analysis.get('price_above_ema50', False) and ema_analysis.get('price_above_ema200', False):
                    condition2_met = True
                    confluence_conditions.append("✅ Price above EMA 50 and EMA 200")
                    confluence_score += 1
                else:
                    confluence_conditions.append("❌ Price not in optimal position relative to EMAs")
            
            # Condition 3: RSI in range 40-50 (not overbought) OR RSI recovering from oversold (>30)
            condition3_met = False
            if indicators and 'rsi' in indicators:
                rsi_value = indicators['rsi'].get('value', 50)
                if 40 <= rsi_value <= 50:
                    condition3_met = True
                    confluence_conditions.append(f"✅ RSI in optimal range ({rsi_value:.1f})")
                    confluence_score += 1
                elif rsi_value > 30 and rsi_value < 40:
                    # RSI recovering from oversold
                    condition3_met = True
                    confluence_conditions.append(f"✅ RSI recovering from oversold ({rsi_value:.1f})")
                    confluence_score += 1
                else:
                    confluence_conditions.append(f"❌ RSI not optimal ({rsi_value:.1f})")
            else:
                confluence_conditions.append("❌ RSI data unavailable")
            
            # Condition 4: Bullish Pin Bar OR Engulfing Pattern at support
            condition4_met = False
            if pin_bar and 'bullish_pin_bar' in pin_bar:
                condition4_met = True
                confluence_conditions.append("✅ Bullish Pin Bar detected at support")
                confluence_score += 1
            elif candlestick_patterns and 'bullish_engulfing' in candlestick_patterns:
                condition4_met = True
                confluence_conditions.append("✅ Bullish Engulfing Pattern detected")
                confluence_score += 1
            else:
                confluence_conditions.append("❌ No bullish reversal pattern detected")
            
            # Condition 5: Volume > 1.5x average on breakout
            condition5_met = False
            if volume_analysis and volume_analysis.get('breakout', False) and volume_analysis.get('signal') == 'buy':
                condition5_met = True
                volume_ratio = volume_analysis.get('volume_ratio', 1.0)
                confluence_conditions.append(f"✅ High volume breakout ({(volume_ratio):.2f}x average)")
                confluence_score += 1
            else:
                confluence_conditions.append("❌ No volume confirmation")
            
            # Condition 6: Higher High confirming uptrend
            condition6_met = False
            if market_structure and market_structure.get('higher_highs', False) and market_structure.get('structure') == 'uptrend':
                condition6_met = True
                confluence_conditions.append("✅ Higher High pattern confirming uptrend")
                confluence_score += 1
            else:
                confluence_conditions.append("❌ No Higher High confirmation")
            
            # Determine entry signal and confidence
            entry_signal = 'hold'
            confidence = 0.0
            risk_level = 'high'
            
            if confluence_score >= 4:
                # Strong confluence - buy signal
                entry_signal = 'buy'
                confidence = min(0.9, 0.5 + (confluence_score * 0.1))
                risk_level = 'low' if confluence_score >= 5 else 'medium'
            elif confluence_score >= 3:
                # Moderate confluence - weak buy signal
                entry_signal = 'buy'
                confidence = 0.4 + (confluence_score * 0.1)
                risk_level = 'medium'
            else:
                # Weak confluence - hold
                entry_signal = 'hold'
                confidence = confluence_score * 0.1
                risk_level = 'high'
            
            # Compile reasons
            entry_reasons = [c for c in confluence_conditions if c.startswith('✅')]
            
            return {
                'entry_signal': entry_signal,
                'confidence': round(confidence, 3),
                'confluence_score': confluence_score,
                'entry_price': entry_price,
                'entry_reasons': entry_reasons,
                'confluence_conditions': confluence_conditions,
                'indicators': {
                    'rsi': indicators.get('rsi') if indicators else None,
                    'macd': indicators.get('macd') if indicators else None,
                    'bollinger_bands': indicators.get('bollinger_bands') if indicators else None,
                    'stochastic': indicators.get('stochastic') if indicators else None
                },
                'patterns': {
                    'pin_bar': pin_bar,
                    'candlestick': candlestick_patterns,
                    'market_structure': market_structure
                },
                'ema_analysis': ema_analysis,
                'volume_analysis': volume_analysis,
                'risk_level': risk_level,
                'interval': interval,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error analyzing entry signals for {symbol}: {e}", exc_info=True)
            return {
                'entry_signal': 'hold',
                'confidence': 0.0,
                'confluence_score': 0,
                'entry_price': 0.0,
                'entry_reasons': [],
                'error': str(e)
            }
    
    def analyze_exit_signals(
        self,
        symbol: str,
        entry_price: float,
        entry_date: str,
        current_price: float,
        current_date: str,
        interval: str = '4h',
        portfolio_value: float = 10000.0,
        risk_per_trade: float = 0.02
    ) -> Dict:
        """
        Analyze exit signals with position management (SL/TP/Trailing Stop)
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price of the position
            entry_date: Entry date (ISO format)
            current_price: Current market price
            current_date: Current date (ISO format)
            interval: Data interval ('1h', '4h', '1d')
            portfolio_value: Total portfolio value
            risk_per_trade: Risk per trade as fraction (default 0.02 = 2%)
            
        Returns:
            Dict with exit signal analysis
        """
        try:
            # Get historical data for ATR and EMA calculation
            interval_map = {
                '1h': 30,
                '4h': 120,
                '1w': 240,
                '1d': 300
            }
            prediction_horizon = interval_map.get(interval, 120)
            
            historical_data, _ = self.market_data_service.get_symbol_history_with_interval(
                symbol, prediction_horizon
            )
            
            if not historical_data or len(historical_data) < 50:
                return {
                    'exit_signal': 'hold',
                    'exit_reason': 'insufficient_data',
                    'error': 'Insufficient historical data for exit analysis'
                }
            
            df = pd.DataFrame(historical_data)
            close = df['close'].values
            high = df['high'].values if 'high' in df.columns else close
            low = df['low'].values if 'low' in df.columns else close
            
            # Calculate ATR for Stop Loss
            atr_value = None
            if TA_AVAILABLE:
                try:
                    atr_indicator = ta.volatility.AverageTrueRange(
                        high=pd.Series(high),
                        low=pd.Series(low),
                        close=pd.Series(close),
                        window=14
                    )
                    atr_value = atr_indicator.average_true_range().iloc[-1]
                    if pd.isna(atr_value):
                        atr_value = None
                except Exception as e:
                    self.logger.debug(f"ATR calculation failed: {e}")
            
            # Calculate Stop Loss: entry_price - (2 * ATR) for long position
            if entry_price is None or entry_price <= 0:
                return {
                    'exit_signal': 'hold',
                    'exit_reason': 'invalid_entry_price',
                    'error': 'Invalid entry price'
                }
            
            if atr_value is not None and atr_value > 0:
                stop_loss = entry_price - (2 * atr_value)
            else:
                # Fallback: 5% stop loss for crypto
                stop_loss = entry_price * 0.95
            
            # Ensure stop loss doesn't exceed max risk (1-2% of portfolio)
            max_risk_amount = portfolio_value * risk_per_trade
            max_loss_per_share = entry_price - stop_loss
            if max_loss_per_share > 0:
                max_position_size = max_risk_amount / max_loss_per_share
                # Adjust stop loss if needed
                if max_loss_per_share * (portfolio_value / entry_price) > max_risk_amount:
                    stop_loss = entry_price - (max_risk_amount / (portfolio_value / entry_price))
            
            # Calculate current return
            current_return = (current_price - entry_price) / entry_price if entry_price > 0 else 0
            
            # Calculate Take Profit levels based on R:R
            risk_amount = entry_price - stop_loss
            take_profit_1 = entry_price + (2 * risk_amount)  # R:R 1:2
            take_profit_2 = entry_price + (3 * risk_amount)  # R:R 1:3 (optional)
            
            # Calculate position size based on risk
            if risk_amount > 0:
                position_size = max_risk_amount / risk_amount
                position_value = position_size * entry_price
            else:
                position_size = 0
                position_value = 0
            
            # Calculate EMA 20 for trailing stop
            ema20 = None
            if TA_AVAILABLE and len(df) >= 20:
                try:
                    ema20_series = ta.trend.EMAIndicator(pd.Series(close), window=20).ema_indicator()
                    ema20 = ema20_series.iloc[-1] if not pd.isna(ema20_series.iloc[-1]) else None
                except Exception:
                    pass
            
            # Calculate swing low for trailing stop
            swing_low = None
            if len(df) >= 20:
                try:
                    lookback = min(5, len(df) // 4)
                    recent_lows = []
                    for i in range(max(0, len(df) - 20), len(df) - lookback):
                        if all(low[i] <= low[i-j] for j in range(1, min(lookback+1, i+1))) and \
                           all(low[i] <= low[i+j] for j in range(1, lookback+1)):
                            recent_lows.append(low[i])
                    if recent_lows:
                        swing_low = min(recent_lows)
                except Exception:
                    pass
            
            # Determine trailing stop
            trailing_stop = None
            if current_return > 0.01:  # Only if position is in profit (>1%)
                # Trailing stop: 7% below highest price since entry
                # Or use EMA 20, or swing low
                highest_since_entry = max([h for h in high if h >= entry_price], default=entry_price)
                trailing_stop_7pct = highest_since_entry * 0.93
                
                # Use the most conservative (highest) trailing stop
                trailing_stop_candidates = [trailing_stop_7pct]
                if ema20 and ema20 < current_price:
                    trailing_stop_candidates.append(ema20)
                if swing_low and swing_low < current_price:
                    trailing_stop_candidates.append(swing_low)
                
                if trailing_stop_candidates:
                    trailing_stop = max(trailing_stop_candidates)
            
            # Get current indicators for exit signals
            indicators = self._get_indicators_from_ai_service(df, symbol)
            
            # Check exit conditions
            exit_signal = 'hold'
            exit_reason = None
            
            # Exit condition 1: Take Profit 1 (R:R 1:2) - sell 50%
            if current_price >= take_profit_1:
                exit_signal = 'sell_50%'
                exit_reason = 'take_profit_1'
            
            # Exit condition 2: Take Profit 2 (R:R 1:3) - sell additional 25%
            elif current_price >= take_profit_2:
                exit_signal = 'sell_25%'
                exit_reason = 'take_profit_2'
            
            # Exit condition 3: Trailing Stop hit
            elif trailing_stop and current_price <= trailing_stop:
                exit_signal = 'sell_100%'
                exit_reason = 'trailing_stop'
            
            # Exit condition 4: Stop Loss hit
            elif current_price <= stop_loss:
                exit_signal = 'sell_100%'
                exit_reason = 'stop_loss'
            
            # Exit condition 5: RSI reversal (RSI > 70 and dropping) - IMPROVED
            elif indicators and 'rsi' in indicators:
                rsi_value = indicators['rsi'].get('value', 50)
                if rsi_value > 70:
                    # NEW: Check if RSI is dropping (reversal signal from report)
                    # Get previous RSI values to detect reversal
                    rsi_reversal = False
                    try:
                        # Try to get RSI history from indicators if available
                        if 'rsi_history' in indicators.get('rsi', {}):
                            rsi_history = indicators['rsi']['rsi_history']
                            if len(rsi_history) >= 2:
                                # RSI was above 70 and now dropping (reversal)
                                if rsi_history[-2] > 70 and rsi_value < rsi_history[-2]:
                                    rsi_reversal = True
                        else:
                            # Fallback: if current RSI > 70 and we're in overbought, consider reversal
                            # For more accuracy in backtest, we'd need to track RSI history
                            # In backtest, we'll track RSI history in the loop
                            rsi_reversal = True  # Simplified: if RSI > 70, consider it a reversal signal
                    except Exception:
                        # If we can't check reversal, use simple RSI > 70 as signal
                        rsi_reversal = True
                    
                    if rsi_reversal:
                        exit_signal = 'sell_50%'
                        exit_reason = 'rsi_overbought_reversal'
            
            # Exit condition 6: Price closes below EMA 10/20
            if exit_signal == 'hold' and TA_AVAILABLE and len(df) >= 20:
                try:
                    ema10_series = ta.trend.EMAIndicator(pd.Series(close), window=10).ema_indicator()
                    ema10 = ema10_series.iloc[-1] if not pd.isna(ema10_series.iloc[-1]) else None
                    
                    if ema10 and current_price < ema10:
                        if ema20 and current_price < ema20:
                            exit_signal = 'sell_50%'
                            exit_reason = 'price_below_ema'
                except Exception:
                    pass
            
            # Calculate risk/reward ratio
            risk_reward_ratio = 0.0
            if risk_amount > 0:
                potential_profit = take_profit_1 - entry_price
                risk_reward_ratio = potential_profit / risk_amount
            
            return {
                'exit_signal': exit_signal,
                'exit_reason': exit_reason,
                'stop_loss': round(stop_loss, 4),
                'take_profit_1': round(take_profit_1, 4),
                'take_profit_2': round(take_profit_2, 4),
                'trailing_stop': round(trailing_stop, 4) if trailing_stop else None,
                'current_return': round(current_return * 100, 2),  # Percentage
                'risk_reward_ratio': round(risk_reward_ratio, 2),
                'position_size': round(position_size, 4),
                'position_value': round(position_value, 2),
                'risk_amount': round(max_risk_amount, 2),
                'entry_price': entry_price,
                'current_price': current_price,
                'atr': round(atr_value, 4) if atr_value else None,
                'ema20': round(ema20, 4) if ema20 else None,
                'swing_low': round(swing_low, 4) if swing_low else None,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error analyzing exit signals for {symbol}: {e}", exc_info=True)
            return {
                'exit_signal': 'hold',
                'exit_reason': 'error',
                'error': str(e)
            }
    
    def backtest_confluence_strategy(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        initial_capital: float,
        interval: str = '4h',
        risk_per_trade: float = 0.02,
        min_confluence_score: int = 4,
        min_confidence: float = 0.7
    ) -> Dict:
        """
        Backtest the confluence strategy on historical data
        
        Args:
            symbol: Trading symbol
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            initial_capital: Initial capital
            interval: Data interval ('1h', '4h', '1d')
            risk_per_trade: Risk per trade (default 0.02 = 2%)
            min_confluence_score: Minimum confluence score to enter (default 4)
            min_confidence: Minimum confidence to enter (default 0.7)
            
        Returns:
            Dict with backtest results
        """
        try:
            # Parse dates
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            # Get historical data
            interval_map = {
                '1h': 30,
                '4h': 120,
                '1w': 240,
                '1d': 300
            }
            prediction_horizon = interval_map.get(interval, 120)
            
            historical_data, _ = self.market_data_service.get_symbol_history_with_interval(
                symbol, prediction_horizon
            )
            
            if not historical_data:
                return {
                    'error': 'No historical data available',
                    'status': 'error'
                }
            
            # Filter data by date range
            filtered_data = []
            for candle in historical_data:
                candle_date_str = candle.get('timestamp', candle.get('date', ''))
                if candle_date_str:
                    try:
                        candle_dt = datetime.fromisoformat(candle_date_str.replace('Z', '+00:00'))
                        if start_dt <= candle_dt <= end_dt:
                            filtered_data.append(candle)
                    except Exception:
                        continue
            
            if len(filtered_data) < 50:
                return {
                    'error': f'Insufficient data in date range ({len(filtered_data)} candles)',
                    'status': 'error'
                }
            
            # Sort by date
            filtered_data.sort(key=lambda x: x.get('timestamp', x.get('date', '')))
            
            # Initialize backtest state
            cash = initial_capital
            position_shares = 0.0
            position_entry_price = None
            position_entry_date = None
            position_stop_loss = 0.0  # Initialize to 0.0 instead of None
            position_tp1 = None
            position_tp2 = None
            position_tp1_sold = False
            position_tp2_sold = False
            position_high_price = None
            
            equity_curve = [initial_capital]
            trade_history = []
            
            # Process each candle
            for i, candle in enumerate(filtered_data):
                candle_date_str = candle.get('timestamp', candle.get('date', ''))
                current_price = float(candle.get('close', 0))
                
                if current_price == 0:
                    continue
                
                # If no position, check for entry signal
                if position_shares == 0:
                    # Get data up to current candle for analysis
                    data_up_to_current = filtered_data[:i+1]
                    # Reduce minimum requirement - we can work with less data
                    min_required_for_analysis = 50 if interval == '1d' else 100
                    if len(data_up_to_current) < min_required_for_analysis:
                        equity_curve.append(cash)
                        continue
                    
                    # Analyze entry signal
                    temp_df = pd.DataFrame(data_up_to_current)
                    entry_analysis = self._analyze_entry_for_backtest(temp_df, symbol, min_confluence_score, min_confidence)
                    
                    # NEW: Track RSI for reversal detection
                    if entry_analysis.get('indicators') and 'rsi' in entry_analysis.get('indicators', {}):
                        rsi_val = entry_analysis['indicators']['rsi'].get('value')
                        if rsi_val is not None:
                            rsi_history.append(rsi_val)
                            # Keep only last 10 RSI values
                            if len(rsi_history) > 10:
                                rsi_history.pop(0)
                    
                    # Log signal generation for debugging
                    if i % 50 == 0 or entry_analysis.get('confluence_score', 0) >= 3:
                        self.logger.debug(
                            f"Backtest {symbol} [{i}/{len(filtered_data)}]: "
                            f"signal={entry_analysis.get('entry_signal')}, "
                            f"confluence={entry_analysis.get('confluence_score')}/6, "
                            f"confidence={entry_analysis.get('confidence', 0):.2f}, "
                            f"thresholds: min_conf={min_confluence_score}, min_conf={min_confidence}"
                        )
                    
                    if entry_analysis.get('entry_signal') == 'buy':
                        self.logger.info(
                            f"✅ ENTRY SIGNAL for {symbol} at candle {i}: "
                            f"price=${current_price:.2f}, "
                            f"confluence={entry_analysis.get('confluence_score')}, "
                            f"confidence={entry_analysis.get('confidence', 0):.2f}"
                        )
                        entry_price = entry_analysis.get('entry_price', current_price)
                        
                        # Calculate position size based on risk
                        exit_analysis = self.analyze_exit_signals(
                            symbol=symbol,
                            entry_price=entry_price,
                            entry_date=candle_date_str,
                            current_price=entry_price,
                            current_date=candle_date_str,
                            interval=interval,
                            portfolio_value=cash,
                            risk_per_trade=risk_per_trade
                        )
                        
                        stop_loss = exit_analysis.get('stop_loss')
                        if stop_loss is None or stop_loss <= 0:
                            # Fallback to 5% stop loss if not set
                            stop_loss = entry_price * 0.95
                        
                        risk_amount = entry_price - stop_loss
                        
                        if risk_amount > 0 and stop_loss > 0:
                            max_risk = cash * risk_per_trade
                            position_shares = max_risk / risk_amount
                            position_value = position_shares * entry_price
                            
                            if position_value <= cash and stop_loss > 0:
                                position_entry_price = entry_price
                                position_entry_date = candle_date_str
                                position_stop_loss = stop_loss  # Already validated above
                                position_initial_sl = stop_loss  # NEW: Store initial SL for BE logic
                                position_tp1 = exit_analysis.get('take_profit_1') if exit_analysis.get('take_profit_1') else entry_price * 1.10
                                position_tp2 = exit_analysis.get('take_profit_2') if exit_analysis.get('take_profit_2') else entry_price * 1.15
                                position_tp1_sold = False
                                position_tp2_sold = False
                                position_high_price = entry_price
                                cash -= position_value
                                
                                # NEW: Log TP/SL levels for debugging
                                risk_pct = ((entry_price - stop_loss) / entry_price * 100) if entry_price > 0 else 0
                                self.logger.info(
                                    f"✅ POSITION OPENED: {symbol} @ ${entry_price:.2f}, "
                                    f"shares={position_shares:.4f}, value=${position_value:.2f}, "
                                    f"SL=${stop_loss:.2f} ({risk_pct:.2f}%), "
                                    f"TP1=${position_tp1:.2f} (R:R 1:2), TP2=${position_tp2:.2f} (R:R 1:3)"
                                )
                                
                                trade_history.append({
                                    'date': candle_date_str,
                                    'action': 'buy',
                                    'price': entry_price,
                                    'shares': position_shares,
                                    'value': position_value,
                                    'confluence_score': entry_analysis.get('confluence_score', 0),
                                    'confidence': entry_analysis.get('confidence', 0),
                                    'stop_loss': stop_loss,
                                    'take_profit_1': position_tp1,
                                    'take_profit_2': position_tp2
                                })
                
                # If position exists, check for exit signals
                else:
                    if position_high_price is None or current_price > position_high_price:
                        position_high_price = current_price
                    
                    # NEW: Move SL to BE (Break Even) when R:R 1:1 is reached (from report)
                    if position_entry_price and position_initial_sl:
                        risk_amount_initial = position_entry_price - position_initial_sl
                        if risk_amount_initial > 0:
                            current_return_pct = ((current_price - position_entry_price) / position_entry_price) * 100
                            rr_1_1_pct = (risk_amount_initial / position_entry_price) * 100
                            
                            # If we've reached R:R 1:1 (profit = initial risk), move SL to BE
                            if current_return_pct >= rr_1_1_pct and position_stop_loss < position_entry_price:
                                position_stop_loss = position_entry_price
                                self.logger.info(
                                    f"🔒 SL MOVED TO BE: {symbol} @ ${current_price:.2f}, "
                                    f"return={current_return_pct:.2f}% (R:R 1:1 reached, threshold={rr_1_1_pct:.2f}%), "
                                    f"SL moved from ${position_initial_sl:.2f} to ${position_entry_price:.2f} (BE)"
                                )
                    
                    # NEW: Track RSI for reversal detection (when position is open)
                    temp_df_exit = pd.DataFrame(data_up_to_current)
                    indicators_exit = self._get_indicators_from_ai_service(temp_df_exit, symbol)
                    if indicators_exit and 'rsi' in indicators_exit:
                        rsi_val = indicators_exit['rsi'].get('value')
                        if rsi_val is not None:
                            rsi_history.append(rsi_val)
                            # Keep only last 10 RSI values
                            if len(rsi_history) > 10:
                                rsi_history.pop(0)
                    
                    exit_analysis = self.analyze_exit_signals(
                        symbol=symbol,
                        entry_price=position_entry_price,
                        entry_date=position_entry_date,
                        current_price=current_price,
                        current_date=candle_date_str,
                        interval=interval,
                        portfolio_value=cash + (position_shares * current_price),
                        risk_per_trade=risk_per_trade
                    )
                    
                    # NEW: Pass RSI history to exit_analysis for reversal detection
                    if rsi_history and len(rsi_history) >= 2 and 'indicators' in exit_analysis:
                        if 'rsi' in exit_analysis['indicators']:
                            exit_analysis['indicators']['rsi']['rsi_history'] = rsi_history
                    
                    exit_signal = exit_analysis.get('exit_signal', 'hold')
                    exit_reason = exit_analysis.get('exit_reason')
                    
                    # CRITICAL: Check TP/SL levels directly from price (more reliable than exit_analysis)
                    # This ensures we catch TP/SL hits even if exit_analysis doesn't return correct signal
                    
                    # Check Take Profit 1 (R:R 1:2) - sell 50%
                    if not position_tp1_sold and position_tp1 is not None and position_tp1 > 0 and current_price >= position_tp1:
                        shares_to_sell = position_shares * 0.5
                        sell_value = shares_to_sell * current_price
                        cash += sell_value
                        position_shares -= shares_to_sell
                        position_tp1_sold = True
                        
                        trade_history.append({
                            'date': candle_date_str,
                            'action': 'sell_50%',
                            'price': current_price,
                            'shares': shares_to_sell,
                            'value': sell_value,
                            'reason': 'take_profit_1',
                            'return_pct': ((current_price - position_entry_price) / position_entry_price) * 100
                        })
                        
                        self.logger.info(
                            f"✅ TAKE PROFIT 1 HIT: {symbol} @ ${current_price:.2f}, "
                            f"TP1=${position_tp1:.2f}, sold 50%, return={((current_price - position_entry_price) / position_entry_price) * 100:.2f}%"
                        )
                        continue  # Skip other exit checks for this iteration
                    
                    # Check Take Profit 2 (R:R 1:3) - sell additional 25%
                    elif position_tp1_sold and not position_tp2_sold and position_tp2 is not None and position_tp2 > 0 and current_price >= position_tp2:
                        shares_to_sell = position_shares * 0.5  # 50% of remaining = 25% of original
                        sell_value = shares_to_sell * current_price
                        cash += sell_value
                        position_shares -= shares_to_sell
                        position_tp2_sold = True
                        
                        trade_history.append({
                            'date': candle_date_str,
                            'action': 'sell_25%',
                            'price': current_price,
                            'shares': shares_to_sell,
                            'value': sell_value,
                            'reason': 'take_profit_2',
                            'return_pct': ((current_price - position_entry_price) / position_entry_price) * 100
                        })
                        
                        self.logger.info(
                            f"✅ TAKE PROFIT 2 HIT: {symbol} @ ${current_price:.2f}, "
                            f"TP2=${position_tp2:.2f}, sold 25%, return={((current_price - position_entry_price) / position_entry_price) * 100:.2f}%"
                        )
                        continue  # Skip other exit checks for this iteration
                    
                    # Check Stop Loss directly
                    if position_stop_loss and position_stop_loss > 0 and current_price <= position_stop_loss:
                        sell_value = position_shares * current_price
                        cash += sell_value
                        return_pct = ((current_price - position_entry_price) / position_entry_price) * 100 if position_entry_price else 0
                        
                        # Determine if this was initial SL or BE
                        sl_type = "BE (Break Even)" if position_stop_loss >= position_entry_price else "Initial SL"
                        
                        trade_history.append({
                            'date': candle_date_str,
                            'action': 'sell',
                            'price': current_price,
                            'shares': position_shares,
                            'value': sell_value,
                            'reason': 'stop_loss',
                            'return_pct': return_pct,
                            'sl_type': sl_type
                        })
                        
                        self.logger.info(
                            f"🛑 STOP LOSS HIT ({sl_type}): {symbol} @ ${current_price:.2f}, "
                            f"SL=${position_stop_loss:.2f}, entry=${position_entry_price:.2f}, return={return_pct:.2f}%"
                        )
                        
                        position_shares = 0
                        position_entry_price = None
                        position_entry_date = None
                        position_stop_loss = 0.0
                        position_initial_sl = None
                        position_tp1 = None
                        position_tp2 = None
                        position_tp1_sold = False
                        position_tp2_sold = False
                        position_high_price = None
                        continue  # Skip trailing stop check
                    
                    # Update trailing stop based on highest price
                    if position_high_price is not None and position_entry_price is not None and position_high_price > position_entry_price:
                        # Trailing stop: 7% below highest price (only if in profit)
                        current_return = ((position_high_price - position_entry_price) / position_entry_price) * 100 if position_entry_price else 0
                        if current_return > 1.0:  # Only if in >1% profit
                            trailing_stop_price = position_high_price * 0.93  # 7% below high
                            
                            # Check trailing stop
                            if current_price <= trailing_stop_price:
                                sell_value = position_shares * current_price
                                cash += sell_value
                                return_pct = ((current_price - position_entry_price) / position_entry_price) * 100 if position_entry_price else 0
                                
                                trade_history.append({
                                    'date': candle_date_str,
                                    'action': 'sell',
                                    'price': current_price,
                                    'shares': position_shares,
                                    'value': sell_value,
                                    'reason': 'trailing_stop',
                                    'return_pct': return_pct
                                })
                                
                                self.logger.info(
                                    f"📉 TRAILING STOP HIT: {symbol} @ ${current_price:.2f}, "
                                    f"trailing=${trailing_stop_price:.2f}, high=${position_high_price:.2f}, return={return_pct:.2f}%"
                                )
                                
                                position_shares = 0
                                position_entry_price = None
                                position_entry_date = None
                                position_stop_loss = 0.0
                                position_tp1 = None
                                position_tp2 = None
                                position_tp1_sold = False
                                position_tp2_sold = False
                                position_high_price = None
                                continue
                    
                    # Handle exit signals from exit_analysis (fallback)
                    if exit_signal == 'sell_50%' and not position_tp1_sold:
                        shares_to_sell = position_shares * 0.5
                        sell_value = shares_to_sell * current_price
                        cash += sell_value
                        position_shares -= shares_to_sell
                        position_tp1_sold = True
                        
                        trade_history.append({
                            'date': candle_date_str,
                            'action': 'sell_50%',
                            'price': current_price,
                            'shares': shares_to_sell,
                            'value': sell_value,
                            'reason': exit_reason,
                            'return_pct': ((current_price - position_entry_price) / position_entry_price) * 100
                        })
                    
                    elif exit_signal == 'sell_25%' and position_tp1_sold and not position_tp2_sold:
                        shares_to_sell = position_shares * 0.5
                        sell_value = shares_to_sell * current_price
                        cash += sell_value
                        position_shares -= shares_to_sell
                        position_tp2_sold = True
                        
                        trade_history.append({
                            'date': candle_date_str,
                            'action': 'sell_25%',
                            'price': current_price,
                            'shares': shares_to_sell,
                            'value': sell_value,
                            'reason': exit_reason,
                            'return_pct': ((current_price - position_entry_price) / position_entry_price) * 100
                        })
                    
                    # Check stop loss and trailing stop
                    trailing_stop = exit_analysis.get('trailing_stop')
                    
                    # Ensure stop loss is valid (should be set, but double-check)
                    if position_stop_loss is None or position_stop_loss <= 0:
                        # Fallback to 5% stop loss if not set
                        position_stop_loss = position_entry_price * 0.95 if position_entry_price else current_price * 0.95
                    
                    # Only check stop loss if we have a valid position
                    if position_stop_loss and position_stop_loss > 0 and current_price <= position_stop_loss:
                        sell_value = position_shares * current_price
                        cash += sell_value
                        
                        trade_history.append({
                            'date': candle_date_str,
                            'action': 'sell',
                            'price': current_price,
                            'shares': position_shares,
                            'value': sell_value,
                            'reason': 'stop_loss',
                            'return_pct': ((current_price - position_entry_price) / position_entry_price) * 100
                        })
                        
                        position_shares = 0
                        position_entry_price = None
                        position_entry_date = None
                        position_stop_loss = 0.0
                        position_initial_sl = None
                        position_tp1 = None
                        position_tp2 = None
                        position_tp1_sold = False
                        position_tp2_sold = False
                        position_high_price = None
                    
                    elif trailing_stop and current_price <= trailing_stop:
                        sell_value = position_shares * current_price
                        cash += sell_value
                        
                        trade_history.append({
                            'date': candle_date_str,
                            'action': 'sell',
                            'price': current_price,
                            'shares': position_shares,
                            'value': sell_value,
                            'reason': 'trailing_stop',
                            'return_pct': ((current_price - position_entry_price) / position_entry_price) * 100
                        })
                        
                        position_shares = 0
                        position_entry_price = None
                        position_entry_date = None
                        position_stop_loss = 0.0
                        position_initial_sl = None
                        position_tp1 = None
                        position_tp2 = None
                        position_tp1_sold = False
                        position_tp2_sold = False
                        position_high_price = None
                
                current_equity = cash + (position_shares * current_price if position_shares > 0 else 0)
                equity_curve.append(current_equity)
            
            # Close remaining position
            if position_shares > 0:
                last_candle = filtered_data[-1]
                final_price = float(last_candle.get('close', 0))
                final_date = last_candle.get('timestamp', last_candle.get('date', ''))
                
                sell_value = position_shares * final_price
                cash += sell_value
                
                return_pct = ((final_price - position_entry_price) / position_entry_price) * 100 if position_entry_price else 0
                
                trade_history.append({
                    'date': final_date,
                    'action': 'sell',
                    'price': final_price,
                    'shares': position_shares,
                    'value': sell_value,
                    'reason': 'end_of_backtest',
                    'return_pct': return_pct
                })
                
                self.logger.info(
                    f"🔚 CLOSING POSITION at end: {symbol} @ ${final_price:.2f}, "
                    f"shares={position_shares:.4f}, return={return_pct:.2f}%"
                )
                
                equity_curve[-1] = cash
            
            # Calculate metrics
            final_value = equity_curve[-1] if equity_curve else initial_capital
            total_return = (final_value - initial_capital) / initial_capital if initial_capital > 0 else 0
            
            returns = []
            for i in range(1, len(equity_curve)):
                if equity_curve[i-1] > 0:
                    period_return = (equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1]
                    returns.append(period_return)
            
            sharpe_ratio = 0.0
            if returns:
                avg_return = np.mean(returns)
                std_return = np.std(returns)
                sharpe_ratio = (avg_return / std_return) if std_return > 0 else 0
            
            # CAGR
            num_periods = len(equity_curve) - 1
            if interval == '1h':
                periods_per_year = 365 * 24
            elif interval == '4h':
                periods_per_year = 365 * 6
            else:
                periods_per_year = 365
            
            num_years = num_periods / periods_per_year
            cagr = ((final_value / initial_capital) ** (1.0 / num_years) - 1) * 100 if num_years > 0 and final_value > 0 else 0
            
            # Max drawdown
            peak = equity_curve[0]
            max_drawdown = 0.0
            for value in equity_curve:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak if peak > 0 else 0
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            # Win rate and profit factor
            # Group trades by entry/exit pairs
            winning_trades = 0
            losing_trades = 0
            total_profit = 0.0
            total_loss = 0.0
            
            # Track open positions
            open_positions = {}  # {entry_idx: {shares: float, entry_value: float, entry_price: float}}
            
            for i, trade in enumerate(trade_history):
                if trade['action'] == 'buy':
                    # Open new position
                    entry_idx = i
                    open_positions[entry_idx] = {
                        'shares': trade['shares'],
                        'entry_value': trade['value'],
                        'entry_price': trade['price'],
                        'entry_date': trade['date']
                    }
                elif trade['action'] in ['sell', 'sell_50%', 'sell_25%']:
                    # Close positions (FIFO)
                    shares_to_close = trade['shares']
                    sell_price = trade['price']
                    sell_value = trade['value']
                    
                    # Find matching buy positions
                    for entry_idx in sorted(open_positions.keys()):
                        if shares_to_close <= 0:
                            break
                        
                        pos = open_positions[entry_idx]
                        if pos['shares'] <= 0:
                            continue
                        
                        # Calculate how many shares to close from this position
                        shares_from_this_pos = min(shares_to_close, pos['shares'])
                        entry_value_portion = (shares_from_this_pos / pos['shares']) * pos['entry_value']
                        
                        # Calculate P&L
                        sell_value_portion = (shares_from_this_pos / trade['shares']) * sell_value if trade['shares'] > 0 else 0
                        pnl = sell_value_portion - entry_value_portion
                        
                        if pnl > 0:
                            winning_trades += 1
                            total_profit += pnl
                        elif pnl < 0:
                            losing_trades += 1
                            total_loss += abs(pnl)
                        # If pnl == 0, it's a breakeven trade (don't count as win or loss)
                        
                        # Update position
                        pos['shares'] -= shares_from_this_pos
                        shares_to_close -= shares_from_this_pos
                        
                        # Remove position if fully closed
                        if pos['shares'] <= 0:
                            del open_positions[entry_idx]
            
            # Handle any remaining open positions (closed at end of backtest)
            # These are already counted in final_value, so we don't double-count them
            
            total_trades = winning_trades + losing_trades
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            profit_factor = (total_profit / total_loss) if total_loss > 0 else (total_profit if total_profit > 0 else 0)
            
            return {
                'status': 'success',
                'total_return': round(total_return * 100, 2),
                'cagr': round(cagr, 2),
                'sharpe_ratio': round(sharpe_ratio, 3),
                'max_drawdown': round(max_drawdown * 100, 2),
                'win_rate': round(win_rate, 2),
                'profit_factor': round(profit_factor, 2),
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'initial_capital': initial_capital,
                'final_value': round(final_value, 2),
                'equity_curve': [
                    {'date': filtered_data[min(i, len(filtered_data)-1)].get('timestamp', filtered_data[min(i, len(filtered_data)-1)].get('date', '')),
                     'value': value}
                    for i, value in enumerate(equity_curve)
                ],
                'trade_history': trade_history,
                'symbol': symbol,
                'interval': interval,
                'start_date': start_date,
                'end_date': end_date
            }
        except Exception as e:
            self.logger.error(f"Error in backtest for {symbol}: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _analyze_entry_for_backtest(self, df, symbol: str, min_confluence_score: int, min_confidence: float) -> Dict:
        """Helper method for backtesting"""
        try:
            indicators = self._get_indicators_from_ai_service(df, symbol)
            candlestick_patterns = self._get_candlestick_patterns(df)
            pin_bar = self._detect_pin_bar(df)
            market_structure = self._detect_market_structure(df)
            ema_analysis = self._analyze_ema_confluence(df)
            volume_analysis = self._analyze_volume_breakout(df)
            
            confluence_score = 0
            
            if ema_analysis and (ema_analysis.get('golden_cross', False) or ema_analysis.get('trend_strength', 0) > 0.5):
                confluence_score += 1
            
            if ema_analysis:
                # NEW: Check EMA pullback and bounce first (more precise from report)
                if ema_analysis.get('ema_pullback_and_bounce', False):
                    confluence_score += 1
                elif ema_analysis.get('support_test', False) or \
                   (ema_analysis.get('price_above_ema50', False) and ema_analysis.get('price_above_ema200', False)):
                    confluence_score += 1
            
            if indicators and 'rsi' in indicators:
                rsi_value = indicators['rsi'].get('value', 50)
                if 40 <= rsi_value <= 50 or (rsi_value > 30 and rsi_value < 40):
                    confluence_score += 1
            
            if (pin_bar and 'bullish_pin_bar' in pin_bar) or \
               (candlestick_patterns and 'bullish_engulfing' in candlestick_patterns):
                confluence_score += 1
            
            if volume_analysis and volume_analysis.get('breakout', False) and volume_analysis.get('signal') == 'buy':
                confluence_score += 1
            
            if market_structure and market_structure.get('higher_highs', False) and market_structure.get('structure') == 'uptrend':
                confluence_score += 1
            
            confidence = min(0.9, 0.5 + (confluence_score * 0.1))
            
            entry_signal = 'hold'
            if confluence_score >= min_confluence_score and confidence >= min_confidence:
                entry_signal = 'buy'
                self.logger.debug(
                    f"✅ Backtest BUY signal: {symbol}, "
                    f"confluence={confluence_score}/{min_confluence_score}, "
                    f"confidence={confidence:.2f}/{min_confidence}, "
                    f"EMA: golden_cross={ema_analysis.get('golden_cross') if ema_analysis else False}, "
                    f"RSI_ok={indicators.get('rsi', {}).get('value') if indicators and 'rsi' in indicators else 'N/A'}"
                )
            else:
                # Log why signal was rejected
                if confluence_score < min_confluence_score:
                    self.logger.debug(
                        f"❌ Signal rejected: {symbol}, "
                        f"confluence={confluence_score} < {min_confluence_score}"
                    )
                elif confidence < min_confidence:
                    self.logger.debug(
                        f"❌ Signal rejected: {symbol}, "
                        f"confidence={confidence:.2f} < {min_confidence}"
                    )
            
            entry_price = float(df['close'].iloc[-1]) if 'close' in df.columns else 0.0
            
            return {
                'entry_signal': entry_signal,
                'confidence': confidence,
                'confluence_score': confluence_score,
                'entry_price': entry_price
            }
        except Exception as e:
            self.logger.debug(f"Error in _analyze_entry_for_backtest: {e}")
            return {
                'entry_signal': 'hold',
                'confidence': 0.0,
                'confluence_score': 0,
                'entry_price': 0.0
            }

