"""
AI/ML Service for Portfolio Tracker Pro
Advanced AI-powered features including price predictions with Prophet,
portfolio rebalancing with technical indicators, and sentiment analysis
"""
import logging
import time
import math
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

try:
    from prophet import Prophet  # type: ignore
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False

try:
    import ta  # type: ignore
    TA_AVAILABLE = True
except ImportError:
    TA_AVAILABLE = False

try:
    from transformers import pipeline  # type: ignore
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    import joblib
    import os
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    from newsapi import NewsApiClient  # type: ignore
    NEWSAPI_AVAILABLE = True
except ImportError:
    NEWSAPI_AVAILABLE = False

import os

logger = logging.getLogger(__name__)

# Import recommendations history tracking
try:
    from ai_recommendations_history import AIRecommendationsHistory
    RECOMMENDATIONS_HISTORY_AVAILABLE = True
except ImportError:
    RECOMMENDATIONS_HISTORY_AVAILABLE = False


class AIService:
    """AI service for portfolio insights and predictions"""
    
    def __init__(self, market_data_service=None):
        """Initialize AI service"""
        self.logger = logging.getLogger(__name__)
        self.model_cache = {}
        self.market_data_service = market_data_service
        
        # Performance optimization: Cache for technical indicators, chart patterns, and volume profile
        # Cache structure: {cache_key: {'data': result, 'timestamp': time.time()}}
        # TTL: 1 hour (3600 seconds) for technical calculations
        self._technical_indicators_cache = {}
        self._chart_patterns_cache = {}
        self._volume_profile_cache = {}
        self._cache_ttl = 3600  # 1 hour
        
        # ML model cache for pattern recognition
        self._ml_pattern_model = None
        self._ml_model_path = 'models/pattern_classifier.pkl'
        self._ml_model_trained = False
        
        # Ensure models directory exists
        if SKLEARN_AVAILABLE:
            os.makedirs(os.path.dirname(self._ml_model_path) if os.path.dirname(self._ml_model_path) else '.', exist_ok=True)
        
        # Initialize recommendations history tracking
        if RECOMMENDATIONS_HISTORY_AVAILABLE:
            self.recommendations_history = AIRecommendationsHistory()
            self.logger.info("AI Recommendations History tracking initialized")
        else:
            self.recommendations_history = None
        
        # Initialize risk analytics service if available
        try:
            from risk_analytics_service import RiskAnalyticsService
            self.risk_analytics_service = RiskAnalyticsService()
            self.logger.info("Risk Analytics Service initialized")
        except ImportError:
            self.risk_analytics_service = None
            self.logger.debug("Risk Analytics Service not available")
        
        # Initialize sentiment pipeline if transformers available
        self.sentiment_pipeline = None
        if TRANSFORMERS_AVAILABLE:
            try:
                self.sentiment_pipeline = pipeline("sentiment-analysis", 
                                                   model="ProsusAI/finbert",
                                                   device=-1)  # CPU
                self.logger.info("FinBERT sentiment pipeline initialized")
            except Exception as e:
                self.logger.warning(f"Could not initialize FinBERT: {e}")
                self.sentiment_pipeline = None
        
        # Initialize NewsAPI client
        self.newsapi_client = None
        if NEWSAPI_AVAILABLE:
            newsapi_key = os.getenv('NEWSAPI_KEY')
            if newsapi_key:
                try:
                    self.newsapi_client = NewsApiClient(api_key=newsapi_key)
                    self.logger.info("NewsAPI client initialized")
                except Exception as e:
                    self.logger.warning(f"Could not initialize NewsAPI: {e}")
                    self.newsapi_client = None
            else:
                self.logger.info("NEWSAPI_KEY not set, using mock news data")

    def _get_mock_news_headlines(self, symbol: str) -> List[str]:
        """Fallback mock news headlines"""
        mock_headlines = {
            'BTC': ["Bitcoin reaches new milestone", "Institutional adoption of Bitcoin increases"],
            'ETH': ["Ethereum network upgrades show promise", "DeFi activity on Ethereum remains strong"],
            'AAPL': ["Apple announces new product line", "Apple stock shows steady growth"]
        }
        return mock_headlines.get(symbol.upper(), [f"{symbol} shows market activity"])

    # ==================== HELPER METHODS ====================
    
    def _safe_isna(self, value: Any) -> bool:
        """Safely check if value is NaN/None"""
        if value is None:
            return True
        if isinstance(value, (float, int)):
            return np.isnan(value) or np.isinf(value)
        return False
    
    def _safe_bool_extract(self, value: Any, default: bool = False) -> bool:
        """Safely extract boolean value"""
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return default
    
    def _normalize_indicator(self, value: float, min_val: float, max_val: float) -> float:
        """Normalize indicator value to [0, 100] range"""
        if self._safe_isna(value) or max_val == min_val:
            return 50.0
        normalized = ((value - min_val) / (max_val - min_val)) * 100
        return max(0.0, min(100.0, normalized))
    
    def _sanitize_for_json(self, value: Any) -> Any:
        """Sanitize value for JSON serialization"""
        if self._safe_isna(value):
            return None
        if isinstance(value, (np.integer, np.floating)):
            return float(value)
        if isinstance(value, np.ndarray):
            return value.tolist()
        return value
    
    def _get_cache_key(self, prefix: str, *args) -> str:
        """Generate cache key"""
        key_parts = [prefix] + [str(arg) for arg in args]
        return "_".join(key_parts)
    
    def _get_from_cache(self, cache: Dict, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key not in cache:
            return None
        cached_item = cache[key]
        if time.time() - cached_item.get('timestamp', 0) > self._cache_ttl:
            del cache[key]
            return None
        return cached_item.get('data')
    
    def _save_to_cache(self, cache: Dict, key: str, value: Any) -> None:
        """Save value to cache"""
        cache[key] = {
            'data': value,
            'timestamp': time.time()
        }
    
    def _mock_predict_price(self, symbol: str, asset_type: str, days_ahead: int) -> Dict:
        """Mock price prediction fallback (only used when Prophet unavailable)"""
        return {
            'symbol': symbol,
            'model_used': 'mock',
            'status': 'fallback',
            'predictions': [
                {
                    'date': (datetime.now() + timedelta(days=i)).isoformat(),
                    'predicted_price': 100.0 * (1.01 ** i),
                    'upper_bound': 100.0 * (1.02 ** i),
                    'lower_bound': 100.0 * (1.0 ** i)
                }
                for i in range(1, days_ahead + 1)
            ],
            'confidence': 0.5,
            'current_price': 100.0
        }

    # ==================== ANALYSIS METHODS ====================
    
    def _calculate_volume_profile(self, df: pd.DataFrame, num_levels: int = 20) -> Dict:
        """Calculate Volume Profile (POC, VAH, VAL) from real price/volume data"""
        if df is None or len(df) < 20:
            return {}
        
        try:
            if 'close' not in df.columns or 'volume' not in df.columns:
                return {}
            
            cache_key = self._get_cache_key('vol_profile', len(df), num_levels)
            cached_result = self._get_from_cache(self._volume_profile_cache, cache_key)
            if cached_result:
                return cached_result
            
            close = df['close'].values
            volume = df['volume'].values if 'volume' in df.columns else np.ones(len(close))
            current_price = close[-1]
            
            # Create price bins
            min_price = np.min(close)
            max_price = np.max(close)
            price_bins = np.linspace(min_price, max_price, num_levels + 1)
            
            # Calculate volume at each price level
            volume_at_price = np.zeros(num_levels)
            for i in range(len(close)):
                bin_idx = int((close[i] - min_price) / (max_price - min_price) * num_levels)
                bin_idx = max(0, min(num_levels - 1, bin_idx))
                volume_at_price[bin_idx] += volume[i]
            
            # Find POC (Point of Control) - price level with highest volume
            poc_idx = np.argmax(volume_at_price)
            poc_price = (price_bins[poc_idx] + price_bins[poc_idx + 1]) / 2
            
            # Calculate Value Area (70% of volume)
            total_volume = np.sum(volume_at_price)
            value_area_volume = total_volume * 0.70
            
            # Find VAH and VAL
            sorted_indices = np.argsort(volume_at_price)[::-1]
            cumulative_volume = 0
            val_idx = poc_idx
            vah_idx = poc_idx
            
            for idx in sorted_indices:
                cumulative_volume += volume_at_price[idx]
                if idx < poc_idx:
                    val_idx = min(val_idx, idx)
                if idx > poc_idx:
                    vah_idx = max(vah_idx, idx)
                if cumulative_volume >= value_area_volume:
                    break
            
            val_price = (price_bins[val_idx] + price_bins[val_idx + 1]) / 2
            vah_price = (price_bins[vah_idx] + price_bins[vah_idx + 1]) / 2
            
            # Determine current price position
            if current_price < val_price:
                position = 'below_val'
            elif current_price > vah_price:
                position = 'above_vah'
            elif current_price < poc_price:
                position = 'below_poc'
            elif current_price > poc_price:
                position = 'above_poc'
            else:
                position = 'at_poc'
            
            result = {
                'poc_price': float(poc_price),
                'vah_price': float(vah_price),
                'val_price': float(val_price),
                'current_price_position': position
            }
            
            self._save_to_cache(self._volume_profile_cache, cache_key, result)
            return result
            
        except Exception as e:
            self.logger.debug(f"Volume Profile calculation failed: {e}")
            return {}
    
    def _detect_candlestick_patterns(self, df: pd.DataFrame) -> Dict:
        """Detect candlestick patterns from real OHLC data"""
        if df is None or len(df) < 3:
            return {}
        
        try:
            if 'open' not in df.columns or 'high' not in df.columns or 'low' not in df.columns or 'close' not in df.columns:
                return {}
            
            patterns = {}
            open_prices = df['open'].values
            high_prices = df['high'].values
            low_prices = df['low'].values
            close_prices = df['close'].values
            
            # Get last 5 candles for pattern detection
            for i in range(max(1, len(df) - 5), len(df)):
                o = open_prices[i]
                h = high_prices[i]
                l = low_prices[i]
                c = close_prices[i]
                
                body = abs(c - o)
                upper_shadow = h - max(o, c)
                lower_shadow = min(o, c) - l
                total_range = h - l
                
                if total_range == 0:
                    continue
                
                # Doji pattern
                if body / total_range < 0.1:
                    patterns['doji'] = {
                        'signal': 'neutral',
                        'confidence': 0.7,
                        'index': i
                    }
                
                # Hammer pattern (bullish reversal)
                if lower_shadow > 2 * body and upper_shadow < 0.2 * total_range and c > o:
                    patterns['hammer'] = {
                        'signal': 'buy',
                        'confidence': 0.75,
                        'index': i
                    }
                
                # Shooting Star pattern (bearish reversal)
                if upper_shadow > 2 * body and lower_shadow < 0.2 * total_range and c < o:
                    patterns['shooting_star'] = {
                        'signal': 'sell',
                        'confidence': 0.75,
                        'index': i
                    }
                
                # Engulfing patterns (need previous candle)
                if i > 0:
                    prev_o = open_prices[i-1]
                    prev_c = close_prices[i-1]
                    
                    # Bullish Engulfing
                    if prev_c < prev_o and c > o and o < prev_c and c > prev_o:
                        patterns['bullish_engulfing'] = {
                            'signal': 'buy',
                            'confidence': 0.8,
                            'index': i
                        }
                    
                    # Bearish Engulfing
                    if prev_c > prev_o and c < o and o > prev_c and c < prev_o:
                        patterns['bearish_engulfing'] = {
                            'signal': 'sell',
                            'confidence': 0.8,
                            'index': i
                        }
            
            return patterns
            
        except Exception as e:
            self.logger.debug(f"Candlestick pattern detection failed: {e}")
            return {}
    
    def _detect_chart_patterns(self, df: pd.DataFrame, timeframe: str = 'daily') -> Dict:
        """Detect chart patterns from real price data"""
        if df is None or len(df) < 20:
            return {}
        
        try:
            if 'high' not in df.columns or 'low' not in df.columns:
                return {}
            
            patterns = {}
            high = df['high'].values
            low = df['low'].values
            close = df['close'].values
            
            # Use recent 60 days for pattern detection
            lookback = min(60, len(df))
            recent_highs = high[-lookback:]
            recent_lows = low[-lookback:]
            
            # Head & Shoulders pattern
            if lookback >= 20:
                # Find peaks (local maxima)
                peaks = []
                for i in range(2, len(recent_highs) - 2):
                    if recent_highs[i] > recent_highs[i-1] and recent_highs[i] > recent_highs[i+1]:
                        if recent_highs[i] > recent_highs[i-2] and recent_highs[i] > recent_highs[i+2]:
                            peaks.append((i, recent_highs[i]))
                
                if len(peaks) >= 3:
                    peaks.sort(key=lambda x: x[1], reverse=True)
                    head = peaks[0]
                    shoulders = [p for p in peaks[1:] if abs(p[1] - head[1]) / head[1] < 0.15]
                    
                    if len(shoulders) >= 2:
                        # Check if shoulders are on both sides of head
                        left_shoulder = None
                        right_shoulder = None
                        for s in shoulders:
                            if s[0] < head[0]:
                                left_shoulder = s
                            else:
                                right_shoulder = s
                        
                        if left_shoulder and right_shoulder:
                            patterns['head_shoulders'] = {
                                'signal': 'sell',
                                'weight': 15 if timeframe == 'weekly' else 20,
                                'confidence': 0.7
                            }
            
            # Triangle patterns (simplified detection)
            if lookback >= 15:
                recent_closes = close[-lookback:]
                trend = np.polyfit(range(len(recent_closes)), recent_closes, 1)[0]
                volatility = np.std(recent_closes) / np.mean(recent_closes)
                
                # Ascending triangle (rising support, flat resistance)
                max_high = np.max(recent_highs)
                if trend > 0 and volatility < 0.1:
                    patterns['ascending_triangle'] = {
                        'signal': 'buy',
                        'weight': 10 if timeframe == 'weekly' else 15,
                        'confidence': 0.65
                    }
                
                # Descending triangle (falling resistance, flat support)
                min_low = np.min(recent_lows)
                if trend < 0 and volatility < 0.1:
                    patterns['descending_triangle'] = {
                        'signal': 'sell',
                        'weight': 10 if timeframe == 'weekly' else 15,
                        'confidence': 0.65
                    }
            
            # Flag patterns (simplified)
            if lookback >= 10:
                first_half_high = np.max(recent_highs[:lookback//2])
                second_half_high = np.max(recent_highs[lookback//2:])
                first_half_low = np.min(recent_lows[:lookback//2])
                second_half_low = np.min(recent_lows[lookback//2:])
                
                # Bull flag: strong uptrend followed by consolidation
                if first_half_high > second_half_high * 1.05 and abs(second_half_high - second_half_low) / second_half_high < 0.05:
                    patterns['bull_flag'] = {
                        'signal': 'buy',
                        'weight': 12 if timeframe == 'weekly' else 18,
                        'confidence': 0.7
                    }
                
                # Bear flag: strong downtrend followed by consolidation
                if first_half_low < second_half_low * 0.95 and abs(second_half_high - second_half_low) / second_half_high < 0.05:
                    patterns['bear_flag'] = {
                        'signal': 'sell',
                        'weight': 12 if timeframe == 'weekly' else 18,
                        'confidence': 0.7
                    }
            
            return patterns
            
        except Exception as e:
            self.logger.debug(f"Chart pattern detection failed: {e}")
            return {}
    
    def _detect_support_resistance(self, df: pd.DataFrame) -> Dict:
        """Detect support and resistance levels from real price data using swing highs/lows"""
        if df is None or len(df) < 20:
            return {}
        
        try:
            if 'high' not in df.columns or 'low' not in df.columns or 'close' not in df.columns:
                return {}
            
            high = df['high'].values
            low = df['low'].values
            close = df['close'].values
            current_price = close[-1]
            
            # Find swing highs and lows (local extrema)
            swing_highs = []
            swing_lows = []
            
            for i in range(2, len(high) - 2):
                # Swing high
                if high[i] > high[i-1] and high[i] > high[i+1] and high[i] > high[i-2] and high[i] > high[i+2]:
                    swing_highs.append(high[i])
                
                # Swing low
                if low[i] < low[i-1] and low[i] < low[i+1] and low[i] < low[i-2] and low[i] < low[i+2]:
                    swing_lows.append(low[i])
            
            # Calculate support and resistance levels
            support_levels = sorted(swing_lows)[-3:] if swing_lows else []
            resistance_levels = sorted(swing_highs)[-3:] if swing_highs else []
            
            # Check if price is near support/resistance
            near_support = False
            near_resistance = False
            
            price_tolerance = current_price * 0.02  # 2% tolerance
            
            for support in support_levels:
                if abs(current_price - support) < price_tolerance:
                    near_support = True
                    break
            
            for resistance in resistance_levels:
                if abs(current_price - resistance) < price_tolerance:
                    near_resistance = True
                    break
            
            # Calculate Fibonacci retracements
            if len(df) >= 50:
                recent_high = np.max(high[-50:])
                recent_low = np.min(low[-50:])
                fib_range = recent_high - recent_low
                
                fib_levels = {
                    'fib_236': recent_high - fib_range * 0.236,
                    'fib_382': recent_high - fib_range * 0.382,
                    'fib_500': recent_high - fib_range * 0.500,
                    'fib_618': recent_high - fib_range * 0.618
                }
            else:
                fib_levels = {}
            
            return {
                'support_levels': [float(s) for s in support_levels],
                'resistance_levels': [float(r) for r in resistance_levels],
                'near_support': near_support,
                'near_resistance': near_resistance,
                'fibonacci_levels': fib_levels
            }
            
        except Exception as e:
            self.logger.debug(f"Support/Resistance detection failed: {e}")
            return {}
    
    def _calculate_correlation_and_beta(self, df: pd.DataFrame, symbol: str, benchmark_symbol: str = None) -> Dict:
        """Calculate correlation and beta relative to benchmark using real market data"""
        if df is None or len(df) < 50:
            return {}
        
        try:
            if 'close' not in df.columns or not self.market_data_service:
                return {}
            
            # Get benchmark data
            if not benchmark_symbol:
                benchmark_symbol = 'BTC' if symbol not in ['BTC', 'ETH'] else 'SPY'
            
            benchmark_data, _ = self.market_data_service.get_symbol_history_with_interval(
                benchmark_symbol, 'crypto' if benchmark_symbol in ['BTC', 'ETH'] else 'stock', '1d'
            )
            
            if not benchmark_data or len(benchmark_data) < 50:
                return {}
            
            benchmark_df = pd.DataFrame(benchmark_data)
            if 'close' not in benchmark_df.columns:
                return {}
            
            # Align dataframes by date
            df_aligned = df[['close']].copy()
            benchmark_closes = benchmark_df['close'].values[:len(df_aligned)]
            df_aligned['benchmark_close'] = benchmark_closes
            
            # Calculate returns
            df_aligned['returns'] = df_aligned['close'].pct_change()
            df_aligned['benchmark_returns'] = df_aligned['benchmark_close'].pct_change()
            
            # Remove NaN values
            df_aligned = df_aligned.dropna()
            
            if len(df_aligned) < 30:
                return {}
            
            returns = df_aligned['returns'].values
            benchmark_returns = df_aligned['benchmark_returns'].values
            
            # Calculate correlation
            correlation = np.corrcoef(returns, benchmark_returns)[0, 1]
            
            # Calculate beta
            covariance = np.cov(returns, benchmark_returns)[0, 1]
            benchmark_variance = np.var(benchmark_returns)
            beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
            
            # Calculate relative performance
            symbol_total_return = (df_aligned['close'].iloc[-1] / df_aligned['close'].iloc[0] - 1) * 100
            benchmark_total_return = (df_aligned['benchmark_close'].iloc[-1] / df_aligned['benchmark_close'].iloc[0] - 1) * 100
            
            outperforming = symbol_total_return > benchmark_total_return
            
            return {
                'correlation': float(correlation) if not np.isnan(correlation) else 0.0,
                'beta': float(beta) if not np.isnan(beta) else 0.0,
                'outperforming': outperforming,
                'relative_return': float(symbol_total_return - benchmark_total_return)
            }
            
        except Exception as e:
            self.logger.debug(f"Correlation/Beta calculation failed for {symbol}: {e}")
            return {}

    # ==================== TECHNICAL ANALYSIS METHODS ====================
    
    def _calculate_technical_indicators(self, df: pd.DataFrame, symbol: str = None) -> Dict:
        """Calculate comprehensive technical indicators (20+ indicators)"""
        if df is None or len(df) < 50:
            return {}
        
        indicators = {}
        
        try:
            close = df['close'].values
            high = df['high'].values if 'high' in df.columns else close
            low = df['low'].values if 'low' in df.columns else close
            volume = df['volume'].values if 'volume' in df.columns else np.ones(len(close))
            
            # Ensure we have enough data points
            if len(close) < 50:
                return indicators
            
            # Cache key for this calculation
            cache_key = f"{symbol}_{len(df)}_{close[-1]:.2f}" if symbol else f"{len(df)}_{close[-1]:.2f}"
            cached_result = self._get_from_cache(self._technical_indicators_cache, cache_key)
            if cached_result is not None:
                return cached_result
            
            # ========== MOMENTUM/OSCILLATORY INDICATORS ==========
            
            # 1. RSI (Relative Strength Index)
            if TA_AVAILABLE:
                try:
                    rsi_indicator = ta.momentum.RSIIndicator(pd.Series(close), window=14)
                    rsi = rsi_indicator.rsi().values[-1] if not pd.isna(rsi_indicator.rsi().iloc[-1]) else None
                    if rsi is not None:
                        indicators['rsi'] = {
                            'value': float(rsi),
                            'status': 'oversold' if rsi < 30 else 'overbought' if rsi > 70 else 'neutral',
                            'signal': 'buy' if rsi < 30 else 'sell' if rsi > 70 else 'neutral'
                        }
                except Exception as e:
                    self.logger.debug(f"RSI calculation failed: {e}")
            else:
                # Manual RSI calculation
                try:
                    delta = pd.Series(close).diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    rsi = 100 - (100 / (1 + rs))
                    rsi_val = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else None
                    if rsi_val is not None:
                        indicators['rsi'] = {
                            'value': float(rsi_val),
                            'status': 'oversold' if rsi_val < 30 else 'overbought' if rsi_val > 70 else 'neutral',
                            'signal': 'buy' if rsi_val < 30 else 'sell' if rsi_val > 70 else 'neutral'
                        }
                except Exception:
                    pass
            
            # 2. Stochastic Oscillator
            if TA_AVAILABLE:
                try:
                    stoch = ta.momentum.StochasticOscillator(
                        pd.Series(high), pd.Series(low), pd.Series(close),
                        window=14, smooth_window=3
                    )
                    stoch_k = stoch.stoch().values[-1] if not pd.isna(stoch.stoch().iloc[-1]) else None
                    stoch_d = stoch.stoch_signal().values[-1] if not pd.isna(stoch.stoch_signal().iloc[-1]) else None
                    if stoch_k is not None and stoch_d is not None:
                        indicators['stochastic'] = {
                            'k': float(stoch_k),
                            'd': float(stoch_d),
                            'status': 'oversold' if stoch_k < 20 else 'overbought' if stoch_k > 80 else 'neutral',
                            'signal': 'buy' if stoch_k < 20 else 'sell' if stoch_k > 80 else ('buy' if stoch_k > stoch_d else 'sell' if stoch_k < stoch_d else 'neutral')
                        }
                except Exception as e:
                    self.logger.debug(f"Stochastic calculation failed: {e}")
            
            # 3. Williams %R
            if TA_AVAILABLE:
                try:
                    willr = ta.momentum.WilliamsRIndicator(pd.Series(high), pd.Series(low), pd.Series(close), lbp=14)
                    willr_val = willr.williams_r().values[-1] if not pd.isna(willr.williams_r().iloc[-1]) else None
                    if willr_val is not None:
                        indicators['williams_r'] = {
                            'value': float(willr_val),
                            'status': 'oversold' if willr_val < -80 else 'overbought' if willr_val > -20 else 'neutral',
                            'signal': 'buy' if willr_val < -80 else 'sell' if willr_val > -20 else 'neutral'
                        }
                except Exception as e:
                    self.logger.debug(f"Williams %R calculation failed: {e}")
            
            # 4. Money Flow Index (MFI)
            if TA_AVAILABLE:
                try:
                    mfi = ta.volume.MFIIndicator(pd.Series(high), pd.Series(low), pd.Series(close), pd.Series(volume), window=14)
                    mfi_val = mfi.mfi().values[-1] if not pd.isna(mfi.mfi().iloc[-1]) else None
                    if mfi_val is not None:
                        indicators['mfi'] = {
                            'value': float(mfi_val),
                            'status': 'oversold' if mfi_val < 20 else 'overbought' if mfi_val > 80 else 'neutral',
                            'signal': 'buy' if mfi_val < 20 else 'sell' if mfi_val > 80 else 'neutral'
                        }
                except Exception as e:
                    self.logger.debug(f"MFI calculation failed: {e}")
            
            # 5. CCI (Commodity Channel Index)
            if TA_AVAILABLE:
                try:
                    cci = ta.trend.CCIIndicator(pd.Series(high), pd.Series(low), pd.Series(close), window=20)
                    cci_val = cci.cci().values[-1] if not pd.isna(cci.cci().iloc[-1]) else None
                    if cci_val is not None:
                        indicators['cci'] = {
                            'value': float(cci_val),
                            'status': 'strong_bullish' if cci_val > 150 else 'strong_bearish' if cci_val < -150 else ('bullish' if cci_val > 100 else 'bearish' if cci_val < -100 else 'neutral'),
                            'signal': 'buy' if cci_val > 150 else 'sell' if cci_val < -150 else ('buy' if cci_val > 100 else 'sell' if cci_val < -100 else 'neutral')
                        }
                except Exception as e:
                    self.logger.debug(f"CCI calculation failed: {e}")
            
            # ========== TREND INDICATORS ==========
            
            # 6. MACD
            if TA_AVAILABLE:
                try:
                    macd_indicator = ta.trend.MACD(pd.Series(close))
                    macd_line = macd_indicator.macd().values[-1] if not pd.isna(macd_indicator.macd().iloc[-1]) else None
                    signal_line = macd_indicator.macd_signal().values[-1] if not pd.isna(macd_indicator.macd_signal().iloc[-1]) else None
                    histogram = macd_indicator.macd_diff().values[-1] if not pd.isna(macd_indicator.macd_diff().iloc[-1]) else None
                    
                    if macd_line is not None and signal_line is not None:
                        # Detect crossover
                        macd_prev = macd_indicator.macd().values[-2] if len(macd_indicator.macd()) >= 2 else None
                        signal_prev = macd_indicator.macd_signal().values[-2] if len(macd_indicator.macd_signal()) >= 2 else None
                        crossover = None
                        if macd_prev is not None and signal_prev is not None:
                            if macd_prev <= signal_prev and macd_line > signal_line:
                                crossover = 'bullish'
                            elif macd_prev >= signal_prev and macd_line < signal_line:
                                crossover = 'bearish'
                        
                        indicators['macd'] = {
                            'macd': float(macd_line),
                            'signal': float(signal_line),
                            'histogram': float(histogram) if histogram is not None else 0.0,
                            'trend': 'bullish' if macd_line > signal_line else 'bearish',
                            'crossover': crossover
                        }
                except Exception as e:
                    self.logger.debug(f"MACD calculation failed: {e}")
            
            # 7. Moving Averages (MA50, MA200)
            if TA_AVAILABLE:
                try:
                    ma50_indicator = ta.trend.SMAIndicator(pd.Series(close), window=50)
                    ma200_indicator = ta.trend.SMAIndicator(pd.Series(close), window=200)
                    ma50 = ma50_indicator.sma_indicator().values[-1] if not pd.isna(ma50_indicator.sma_indicator().iloc[-1]) else None
                    ma200 = ma200_indicator.sma_indicator().values[-1] if not pd.isna(ma200_indicator.sma_indicator().iloc[-1]) else None
                    current_price = close[-1]
                    
                    if ma50 is not None:
                        indicators['ma50'] = {
                            'value': float(ma50),
                            'position': 'above' if current_price > ma50 else 'below',
                            'signal': 'buy' if current_price > ma50 else 'sell'
                        }
                    
                    if ma200 is not None:
                        indicators['ma200'] = {
                            'value': float(ma200),
                            'position': 'above' if current_price > ma200 else 'below',
                            'signal': 'buy' if current_price > ma200 else 'sell'
                        }
                    
                    # Golden/Death Cross
                    if ma50 is not None and ma200 is not None:
                        indicators['ma_cross'] = {
                            'golden_cross': ma50 > ma200,
                            'death_cross': ma50 < ma200,
                            'signal': 'buy' if ma50 > ma200 else 'sell'
                        }
                except Exception as e:
                    self.logger.debug(f"Moving Averages calculation failed: {e}")
            
            # 8. ADX (Average Directional Index)
            if TA_AVAILABLE:
                try:
                    adx_indicator = ta.trend.ADXIndicator(pd.Series(high), pd.Series(low), pd.Series(close), window=14)
                    adx = adx_indicator.adx().values[-1] if not pd.isna(adx_indicator.adx().iloc[-1]) else None
                    adx_pos = adx_indicator.adx_pos().values[-1] if not pd.isna(adx_indicator.adx_pos().iloc[-1]) else None
                    adx_neg = adx_indicator.adx_neg().values[-1] if not pd.isna(adx_indicator.adx_neg().iloc[-1]) else None
                    
                    if adx is not None and adx_pos is not None and adx_neg is not None:
                        indicators['adx'] = {
                            'value': float(adx),
                            'strength': 'strong' if adx > 25 else 'weak',
                            'direction': 'bullish' if adx_pos > adx_neg else 'bearish',
                            'signal': 'buy' if adx > 25 and adx_pos > adx_neg else 'sell' if adx > 25 and adx_neg > adx_pos else 'neutral'
                        }
                except Exception as e:
                    self.logger.debug(f"ADX calculation failed: {e}")
            
            # 9. Parabolic SAR
            if TA_AVAILABLE:
                try:
                    psar = ta.trend.PSARIndicator(pd.Series(high), pd.Series(low), pd.Series(close))
                    psar_val = psar.psar().values[-1] if not pd.isna(psar.psar().iloc[-1]) else None
                    if psar_val is not None:
                        indicators['psar'] = {
                            'value': float(psar_val),
                            'position': 'below' if current_price > psar_val else 'above',
                            'signal': 'buy' if current_price > psar_val else 'sell'
                        }
                except Exception as e:
                    self.logger.debug(f"Parabolic SAR calculation failed: {e}")
            
            # ========== VOLATILITY INDICATORS ==========
            
            # 10. ATR (Average True Range)
            if TA_AVAILABLE:
                try:
                    atr_indicator = ta.volatility.AverageTrueRange(pd.Series(high), pd.Series(low), pd.Series(close), window=14)
                    atr = atr_indicator.average_true_range().values[-1] if not pd.isna(atr_indicator.average_true_range().iloc[-1]) else None
                    if atr is not None:
                        atr_percent = (atr / current_price) * 100 if current_price > 0 else 0
                        indicators['atr'] = {
                            'value': float(atr),
                            'percent': float(atr_percent),
                            'volatility': 'high' if atr_percent > 3 else 'medium' if atr_percent > 1.5 else 'low'
                        }
                except Exception as e:
                    self.logger.debug(f"ATR calculation failed: {e}")
            
            # 11. Bollinger Bands
            if TA_AVAILABLE:
                try:
                    bb = ta.volatility.BollingerBands(pd.Series(close), window=20, window_dev=2)
                    bb_upper = bb.bollinger_hband().values[-1] if not pd.isna(bb.bollinger_hband().iloc[-1]) else None
                    bb_lower = bb.bollinger_lband().values[-1] if not pd.isna(bb.bollinger_lband().iloc[-1]) else None
                    bb_middle = bb.bollinger_mavg().values[-1] if not pd.isna(bb.bollinger_mavg().iloc[-1]) else None
                    
                    if bb_upper is not None and bb_lower is not None and bb_middle is not None:
                        # Calculate position as percentage between bands
                        if bb_upper != bb_lower:
                            position = ((current_price - bb_lower) / (bb_upper - bb_lower)) * 100
                        else:
                            position = 50.0
                        
                        indicators['bollinger_bands'] = {
                            'upper': float(bb_upper),
                            'lower': float(bb_lower),
                            'middle': float(bb_middle),
                            'position': float(position),
                            'status': 'oversold' if position < 20 else 'overbought' if position > 80 else 'neutral',
                            'signal': 'buy' if position < 20 else 'sell' if position > 80 else 'neutral'
                        }
                except Exception as e:
                    self.logger.debug(f"Bollinger Bands calculation failed: {e}")
            
            # 12. Donchian Channels
            try:
                donchian_high = np.max(high[-20:])
                donchian_low = np.min(low[-20:])
                indicators['donchian'] = {
                    'upper': float(donchian_high),
                    'lower': float(donchian_low),
                    'breakout': 'bullish' if current_price > donchian_high else 'bearish' if current_price < donchian_low else None,
                    'signal': 'buy' if current_price > donchian_high else 'sell' if current_price < donchian_low else 'neutral'
                }
            except Exception as e:
                self.logger.debug(f"Donchian Channels calculation failed: {e}")
            
            # 13. Ichimoku Cloud
            if TA_AVAILABLE:
                try:
                    ichimoku = ta.trend.IchimokuIndicator(pd.Series(high), pd.Series(low), pd.Series(close))
                    ichimoku_conversion = ichimoku.ichimoku_conversion_line().values[-1] if not pd.isna(ichimoku.ichimoku_conversion_line().iloc[-1]) else None
                    ichimoku_base = ichimoku.ichimoku_base_line().values[-1] if not pd.isna(ichimoku.ichimoku_base_line().iloc[-1]) else None
                    ichimoku_a = ichimoku.ichimoku_a().values[-1] if not pd.isna(ichimoku.ichimoku_a().iloc[-1]) else None
                    ichimoku_b = ichimoku.ichimoku_b().values[-1] if not pd.isna(ichimoku.ichimoku_b().iloc[-1]) else None
                    
                    if all(v is not None for v in [ichimoku_conversion, ichimoku_base, ichimoku_a, ichimoku_b]):
                        # Cloud position
                        cloud_top = max(ichimoku_a, ichimoku_b)
                        cloud_bottom = min(ichimoku_a, ichimoku_b)
                        in_cloud = cloud_bottom <= current_price <= cloud_top
                        above_cloud = current_price > cloud_top
                        below_cloud = current_price < cloud_bottom
                        
                        # Signal logic
                        signal = 'neutral'
                        if above_cloud and ichimoku_conversion > ichimoku_base:
                            signal = 'buy'
                        elif below_cloud and ichimoku_conversion < ichimoku_base:
                            signal = 'sell'
                        
                        indicators['ichimoku'] = {
                            'conversion_line': float(ichimoku_conversion),
                            'base_line': float(ichimoku_base),
                            'leading_span_a': float(ichimoku_a),
                            'leading_span_b': float(ichimoku_b),
                            'cloud_top': float(cloud_top),
                            'cloud_bottom': float(cloud_bottom),
                            'position': 'above' if above_cloud else 'below' if below_cloud else 'in_cloud',
                            'signal': signal
                        }
                except Exception as e:
                    self.logger.debug(f"Ichimoku Cloud calculation failed: {e}")
            
            # ========== VOLUME INDICATORS ==========
            
            # 14. OBV (On Balance Volume)
            if TA_AVAILABLE:
                try:
                    obv_indicator = ta.volume.OnBalanceVolumeIndicator(pd.Series(close), pd.Series(volume))
                    obv = obv_indicator.on_balance_volume()
                    obv_val = obv.values[-1] if len(obv) > 0 and not pd.isna(obv.iloc[-1]) else None
                    obv_prev = obv.values[-2] if len(obv) >= 2 and not pd.isna(obv.iloc[-2]) else None
                    
                    if obv_val is not None:
                        trend = 'increasing' if obv_prev is not None and obv_val > obv_prev else 'decreasing' if obv_prev is not None and obv_val < obv_prev else 'neutral'
                        indicators['obv'] = {
                            'value': float(obv_val),
                            'trend': trend,
                            'signal': 'buy' if trend == 'increasing' else 'sell' if trend == 'decreasing' else 'neutral'
                        }
                except Exception as e:
                    self.logger.debug(f"OBV calculation failed: {e}")
            
            # 15. A/D Line (Accumulation/Distribution)
            if TA_AVAILABLE:
                try:
                    ad_indicator = ta.volume.AccDistIndexIndicator(pd.Series(high), pd.Series(low), pd.Series(close), pd.Series(volume))
                    ad_line = ad_indicator.acc_dist_index()
                    ad_val = ad_line.values[-1] if len(ad_line) > 0 and not pd.isna(ad_line.iloc[-1]) else None
                    ad_prev = ad_line.values[-2] if len(ad_line) >= 2 and not pd.isna(ad_line.iloc[-2]) else None
                    
                    if ad_val is not None:
                        trend = 'accumulating' if ad_prev is not None and ad_val > ad_prev else 'distributing' if ad_prev is not None and ad_val < ad_prev else 'neutral'
                        indicators['ad_line'] = {
                            'value': float(ad_val),
                            'trend': trend,
                            'signal': 'buy' if trend == 'accumulating' else 'sell' if trend == 'distributing' else 'neutral'
                        }
                except Exception as e:
                    self.logger.debug(f"A/D Line calculation failed: {e}")
            
            # 16. VWAP (Volume Weighted Average Price)
            try:
                vwap = np.sum(close * volume) / np.sum(volume) if np.sum(volume) > 0 else current_price
                vwap_position = ((current_price - vwap) / vwap) * 100 if vwap > 0 else 0
                indicators['vwap'] = {
                    'value': float(vwap),
                    'position': float(vwap_position),
                    'signal': 'buy' if current_price > vwap else 'sell'
                }
            except Exception as e:
                self.logger.debug(f"VWAP calculation failed: {e}")
            
            # 17. CMF (Chaikin Money Flow)
            if TA_AVAILABLE:
                try:
                    cmf_indicator = ta.volume.ChaikinMoneyFlowIndicator(pd.Series(high), pd.Series(low), pd.Series(close), pd.Series(volume), window=20)
                    cmf = cmf_indicator.chaikin_money_flow().values[-1] if not pd.isna(cmf_indicator.chaikin_money_flow().iloc[-1]) else None
                    if cmf is not None:
                        indicators['cmf'] = {
                            'value': float(cmf),
                            'status': 'accumulation' if cmf > 0.1 else 'distribution' if cmf < -0.1 else 'neutral',
                            'signal': 'buy' if cmf > 0.1 else 'sell' if cmf < -0.1 else 'neutral'
                        }
                except Exception as e:
                    self.logger.debug(f"CMF calculation failed: {e}")
            
            # 18. Volume ROC (Rate of Change)
            try:
                if len(volume) >= 15:
                    volume_roc = ((volume[-1] - volume[-15]) / volume[-15]) * 100 if volume[-15] > 0 else 0
                    indicators['volume_roc'] = {
                        'value': float(volume_roc),
                        'signal': 'buy' if volume_roc > 20 else 'sell' if volume_roc < -20 else 'neutral'
                    }
            except Exception as e:
                self.logger.debug(f"Volume ROC calculation failed: {e}")
            
            # ========== MOMENTUM INDICATORS ==========
            
            # 19-20. Price Momentum (7-day and 30-day)
            try:
                if len(close) >= 30:
                    momentum_7d = ((close[-1] - close[-8]) / close[-8]) * 100 if close[-8] > 0 else 0
                    momentum_30d = ((close[-1] - close[-31]) / close[-31]) * 100 if close[-31] > 0 else 0
                    
                    indicators['momentum'] = {
                        '7d': float(momentum_7d),
                        '30d': float(momentum_30d),
                        'short_term': 'bullish' if momentum_7d > 5 else 'bearish' if momentum_7d < -5 else 'neutral',
                        'long_term': 'bullish' if momentum_30d > 10 else 'bearish' if momentum_30d < -10 else 'neutral'
                    }
            except Exception as e:
                self.logger.debug(f"Momentum calculation failed: {e}")
            
            # Save to cache
            self._save_to_cache(self._technical_indicators_cache, cache_key, indicators)
            
        except Exception as e:
            self.logger.error(f"Error calculating technical indicators: {e}", exc_info=True)
        
        return indicators

    # ==================== MAIN AI METHODS ====================
    
    def recommend_rebalance(
        self,
        portfolio_holdings: Dict[str, float],
        target_allocation: Dict[str, float],
        rebalance_threshold: float = 0.05
    ) -> Optional[Dict]:
        """
        Generate AI-powered rebalancing recommendations using comprehensive technical analysis.
        
        Args:
            portfolio_holdings: Current portfolio allocation {symbol: percentage}
            target_allocation: Target allocation {symbol: target_percentage}
            rebalance_threshold: Minimum drift threshold to trigger recommendation (default 0.05 = 5%)
        
        Returns:
            Dictionary with recommendations list and metadata
        """
        if not portfolio_holdings or not target_allocation:
            return {
                "recommendations": [],
                "total_rebalance_amount": 0,
                "model_used": "none",
                "status": "invalid_input"
            }
        
        recommendations = []
        processed_symbols = set()
        model_used = "simple_threshold"
        diagnostic_info = {}
        
        # Stablecoins to exclude from technical analysis
        stablecoins = {'USDT', 'USDC', 'BUSD', 'DAI', 'TUSD', 'PAX', 'USDP', 'GUSD', 'HUSD'}
        
        try:
            # Get all unique symbols from both holdings and target allocation
            all_symbols = set(portfolio_holdings.keys()) | set(target_allocation.keys())
            
            # Process each symbol
            for symbol in all_symbols:
                if symbol in processed_symbols:
                    continue
                
                current_pct = portfolio_holdings.get(symbol, 0.0)
                target_pct = target_allocation.get(symbol, 0.0)
                allocation_drift = current_pct - target_pct
                
                # Skip if both current and target are 0
                if current_pct == 0 and target_pct == 0:
                    continue
                
                # Determine asset type
                asset_type = 'crypto' if symbol in ['BTC', 'ETH', 'SOL', 'USDT', 'USDC', 'BUSD', 'DAI'] else 'stock'
                
                # Initialize scoring variables
                signal_strength = 0.0
                buy_score = 0.0
                sell_score = 0.0
                confidence = 0.0
                action = "hold"
                priority = "low"
                reason_parts = []
                key_indicators_list = []
                strengths_list = []
                concerns_list = []
                indicators = {}
                
                # For stablecoins, use simple allocation drift logic only
                if symbol in stablecoins:
                    if abs(allocation_drift) >= rebalance_threshold:
                        action = "sell" if allocation_drift > 0 else "buy"
                        priority = "medium" if abs(allocation_drift) >= 0.10 else "low"
                        reason = f"Allocation drift: {allocation_drift*100:.1f}% from target"
                        
                        recommendations.append({
                            "asset": symbol,
                            "symbol": symbol,
                            "action": action,
                            "priority": priority,
                            "reason": reason,
                            "signal_strength": 0.0,
                            "confidence": min(abs(allocation_drift) * 2, 1.0),
                            "buy_score": 0.0,
                            "sell_score": 0.0,
                            "composite_score": min(abs(allocation_drift) * 200, 100),
                            "summary": {
                                "key_indicators": [],
                                "strengths": [],
                                "concerns": [f"Allocation drift of {abs(allocation_drift)*100:.1f}%"],
                                "timeframe": "immediate"
                            },
                            "allocation": {
                                "current": current_pct,
                                "target": target_pct,
                                "difference": allocation_drift
                            },
                            "metrics": {}
                        })
                    processed_symbols.add(symbol)
                    continue
                
                # For non-stablecoins, perform comprehensive technical analysis
                if self.market_data_service:
                    try:
                        # Get historical data
                        historical_data, interval = self.market_data_service.get_symbol_history_with_interval(
                            symbol, asset_type, '1d'
                        )
                        
                        if historical_data and len(historical_data) >= 50:
                            df = pd.DataFrame(historical_data)
                            
                            # Calculate technical indicators
                            indicators = self._calculate_technical_indicators(df, symbol)
                            
                            if indicators:
                                model_used = "comprehensive_technical_analysis"
                                
                                # Calculate scoring based on indicators
                                # RSI
                                if 'rsi' in indicators:
                                    rsi_val = indicators['rsi'].get('value', 50)
                                    if rsi_val < 30:
                                        signal_strength += 15
                                        buy_score += 15
                                        key_indicators_list.append({"name": "RSI", "value": rsi_val, "signal": "buy", "weight": "high"})
                                        strengths_list.append("RSI indicates oversold condition")
                                    elif rsi_val > 70:
                                        signal_strength -= 15
                                        sell_score += 15
                                        key_indicators_list.append({"name": "RSI", "value": rsi_val, "signal": "sell", "weight": "high"})
                                        concerns_list.append("RSI indicates overbought condition")
                                
                                # MACD
                                if 'macd' in indicators:
                                    macd_data = indicators['macd']
                                    macd_crossover = macd_data.get('crossover')
                                    macd_trend = macd_data.get('trend')
                                    
                                    if macd_crossover == 'bullish':
                                        signal_strength += 20
                                        buy_score += 20
                                        key_indicators_list.append({"name": "MACD", "value": macd_data.get('histogram', 0), "signal": "buy", "weight": "very_high"})
                                        strengths_list.append("MACD bullish crossover detected")
                                    elif macd_crossover == 'bearish':
                                        signal_strength -= 20
                                        sell_score += 20
                                        key_indicators_list.append({"name": "MACD", "value": macd_data.get('histogram', 0), "signal": "sell", "weight": "very_high"})
                                        concerns_list.append("MACD bearish crossover detected")
                                    elif macd_trend == 'bullish' and not macd_crossover:
                                        signal_strength += 5
                                        buy_score += 5
                                    elif macd_trend == 'bearish' and not macd_crossover:
                                        signal_strength -= 5
                                        sell_score += 5
                                
                                # Moving Averages
                                if 'ma50' in indicators:
                                    ma50_signal = indicators['ma50'].get('signal', 'neutral')
                                    if ma50_signal == 'buy':
                                        signal_strength += 5
                                        buy_score += 5
                                    elif ma50_signal == 'sell':
                                        signal_strength -= 5
                                        sell_score += 5
                                
                                if 'ma200' in indicators:
                                    ma200_signal = indicators['ma200'].get('signal', 'neutral')
                                    if ma200_signal == 'buy':
                                        signal_strength += 8
                                        buy_score += 8
                                    elif ma200_signal == 'sell':
                                        signal_strength -= 8
                                        sell_score += 8
                                
                                # Golden/Death Cross
                                if 'ma_cross' in indicators:
                                    ma_cross = indicators['ma_cross']
                                    if ma_cross.get('golden_cross'):
                                        signal_strength += 10
                                        buy_score += 10
                                        strengths_list.append("Golden Cross pattern (MA50 > MA200)")
                                    elif ma_cross.get('death_cross'):
                                        signal_strength -= 10
                                        sell_score += 10
                                        concerns_list.append("Death Cross pattern (MA50 < MA200)")
                                
                                # Bollinger Bands
                                if 'bollinger_bands' in indicators:
                                    bb = indicators['bollinger_bands']
                                    bb_signal = bb.get('signal', 'neutral')
                                    if bb_signal == 'buy':
                                        signal_strength += 12
                                        buy_score += 12
                                        key_indicators_list.append({"name": "Bollinger", "value": bb.get('position', 50), "signal": "buy", "weight": "high"})
                                    elif bb_signal == 'sell':
                                        signal_strength -= 12
                                        sell_score += 12
                                        key_indicators_list.append({"name": "Bollinger", "value": bb.get('position', 50), "signal": "sell", "weight": "high"})
                                
                                # Stochastic
                                if 'stochastic' in indicators:
                                    stoch = indicators['stochastic']
                                    stoch_k = stoch.get('k', 50)
                                    if stoch_k < 20:
                                        signal_strength += 8
                                        buy_score += 8
                                    elif stoch_k > 80:
                                        signal_strength -= 8
                                        sell_score += 8
                                
                                # Williams %R
                                if 'williams_r' in indicators:
                                    willr = indicators['williams_r']
                                    willr_signal = willr.get('signal', 'neutral')
                                    if willr_signal == 'buy':
                                        signal_strength += 4
                                        buy_score += 4
                                    elif willr_signal == 'sell':
                                        signal_strength -= 4
                                        sell_score += 4
                                
                                # MFI
                                if 'mfi' in indicators:
                                    mfi = indicators['mfi']
                                    mfi_signal = mfi.get('signal', 'neutral')
                                    if mfi_signal == 'buy':
                                        signal_strength += 7
                                        buy_score += 7
                                    elif mfi_signal == 'sell':
                                        signal_strength -= 7
                                        sell_score += 7
                                
                                # CCI (with stricter thresholds)
                                if 'cci' in indicators:
                                    cci_val = indicators['cci'].get('value', 0)
                                    if cci_val > 150:
                                        signal_strength += 8
                                        buy_score += 8
                                    elif cci_val < -150:
                                        signal_strength -= 8
                                        sell_score += 8
                                    elif cci_val > 100:
                                        signal_strength += 4
                                        buy_score += 4
                                    elif cci_val < -100:
                                        signal_strength -= 4
                                        sell_score += 4
                                
                                # ADX
                                if 'adx' in indicators:
                                    adx = indicators['adx']
                                    if adx.get('strength') == 'strong' and adx.get('direction') == 'bullish':
                                        signal_strength += 8
                                        buy_score += 8
                                    elif adx.get('strength') == 'strong' and adx.get('direction') == 'bearish':
                                        signal_strength -= 8
                                        sell_score += 8
                                
                                # Volume indicators
                                if 'obv' in indicators:
                                    obv_signal = indicators['obv'].get('signal', 'neutral')
                                    if obv_signal == 'buy':
                                        signal_strength += 5
                                        buy_score += 5
                                    elif obv_signal == 'sell':
                                        signal_strength -= 5
                                        sell_score += 5
                                
                                if 'cmf' in indicators:
                                    cmf = indicators['cmf']
                                    cmf_signal = cmf.get('signal', 'neutral')
                                    if cmf_signal == 'buy':
                                        signal_strength += 7
                                        buy_score += 7
                                    elif cmf_signal == 'sell':
                                        signal_strength -= 7
                                        sell_score += 7
                                
                                # VWAP
                                if 'vwap' in indicators:
                                    vwap_signal = indicators['vwap'].get('signal', 'neutral')
                                    if vwap_signal == 'buy':
                                        signal_strength += 6
                                        buy_score += 6
                                    elif vwap_signal == 'sell':
                                        signal_strength -= 6
                                        sell_score += 6
                                
                                # Momentum
                                if 'momentum' in indicators:
                                    momentum = indicators['momentum']
                                    if momentum.get('short_term') == 'bullish':
                                        signal_strength += 5
                                        buy_score += 5
                                    elif momentum.get('short_term') == 'bearish':
                                        signal_strength -= 5
                                        sell_score += 5
                                
                                # ATR-based confidence adjustment (not signal strength)
                                if 'atr' in indicators:
                                    atr = indicators['atr']
                                    volatility_pct = atr.get('percent', 0)
                                    # High volatility reduces confidence
                                    if volatility_pct > 5:
                                        confidence_adjustment = -0.2
                                    elif volatility_pct > 3:
                                        confidence_adjustment = -0.1
                                    else:
                                        confidence_adjustment = 0
                                else:
                                    confidence_adjustment = 0
                                
                                # Support/Resistance
                                support_resistance = self._detect_support_resistance(df)
                                if support_resistance:
                                    if support_resistance.get('near_support'):
                                        signal_strength += 8
                                        buy_score += 8
                                        strengths_list.append("Price near support level")
                                    elif support_resistance.get('near_resistance'):
                                        signal_strength -= 8
                                        sell_score += 8
                                        concerns_list.append("Price near resistance level")
                                
                                # Volume Profile
                                volume_profile = self._calculate_volume_profile(df)
                                if volume_profile:
                                    position = volume_profile.get('current_price_position', '')
                                    if position == 'below_val':
                                        signal_strength += 8
                                        buy_score += 8
                                    elif position == 'above_vah':
                                        signal_strength -= 8
                                        sell_score += 8
                                
                                # Chart Patterns
                                chart_patterns = self._detect_chart_patterns(df)
                                for pattern_name, pattern_data in chart_patterns.items():
                                    pattern_signal = pattern_data.get('signal', 'neutral')
                                    pattern_weight = pattern_data.get('weight', 0)
                                    if pattern_signal == 'buy':
                                        signal_strength += pattern_weight
                                        buy_score += pattern_weight
                                        strengths_list.append(f"{pattern_name.replace('_', ' ').title()} pattern detected")
                                    elif pattern_signal == 'sell':
                                        signal_strength -= pattern_weight
                                        sell_score += pattern_weight
                                        concerns_list.append(f"{pattern_name.replace('_', ' ').title()} pattern detected")
                                
                                # Candlestick Patterns
                                candlestick_patterns = self._detect_candlestick_patterns(df)
                                for pattern_name, pattern_data in candlestick_patterns.items():
                                    pattern_signal = pattern_data.get('signal', 'neutral')
                                    if pattern_signal == 'buy':
                                        signal_strength += 10
                                        buy_score += 10
                                    elif pattern_signal == 'sell':
                                        signal_strength -= 10
                                        sell_score += 10
                                
                                # Correlation/Beta
                                correlation_beta = self._calculate_correlation_and_beta(df, symbol, 'BTC')
                                if correlation_beta:
                                    if correlation_beta.get('outperforming'):
                                        signal_strength += 3
                                        buy_score += 3
                                    elif not correlation_beta.get('outperforming'):
                                        signal_strength -= 3
                                        sell_score += 3
                                
                                # Clamp signal_strength to [-100, 100]
                                signal_strength = max(-100, min(100, signal_strength))
                                
                                # Calculate confidence
                                base_confidence = abs(signal_strength) / 100.0
                                confidence = max(0.0, min(1.0, base_confidence + confidence_adjustment))
                                
                                # Determine action and priority based on signal_strength and allocation drift
                                if signal_strength > 20:
                                    action = "buy"
                                    priority = "high" if signal_strength > 50 else "medium"
                                elif signal_strength < -20:
                                    action = "sell"
                                    priority = "high" if signal_strength < -50 else "medium"
                                elif abs(allocation_drift) >= rebalance_threshold:
                                    action = "sell" if allocation_drift > 0 else "buy"
                                    priority = "medium" if abs(allocation_drift) >= 0.10 else "low"
                                
                                # Build reason
                                if abs(signal_strength) > 20:
                                    reason_parts.append(f"Technical signal: {signal_strength:.1f}")
                                if abs(allocation_drift) >= rebalance_threshold:
                                    reason_parts.append(f"Allocation drift: {allocation_drift*100:.1f}%")
                                
                                reason = "; ".join(reason_parts) if reason_parts else "Portfolio rebalancing recommendation"
                                
                                # Calculate composite score (0-100)
                                composite_score = 0
                                composite_score += (abs(signal_strength) / 100) * 30  # 30% wagi dla signal strength
                                composite_score += (confidence * 100) * 0.25  # 25% wagi dla confidence
                                composite_score += (buy_score if action == "buy" else sell_score) * 0.20  # 20% wagi dla buy/sell score
                                
                                # Risk adjustment (15% wagi)
                                risk_weight = 10  # default medium
                                if confidence > 0.7:
                                    risk_weight = 15
                                elif confidence < 0.4:
                                    risk_weight = 5
                                composite_score += risk_weight * 0.15
                                
                                # Allocation drift component (10% wagi)
                                drift_component = min(100, abs(allocation_drift) * 500)  # 20% drift = 100 points
                                composite_score += drift_component * 0.10
                                
                                # Ensure composite_score is in [0, 100]
                                composite_score = max(0, min(100, composite_score))
                                
                                # Build summary
                                if not strengths_list and signal_strength > 20:
                                    strengths_list.append("Positive technical indicators")
                                if not concerns_list and signal_strength < -20:
                                    concerns_list.append("Negative technical indicators")
                                
                                recommendations.append({
                                    "asset": symbol,
                                    "symbol": symbol,
                                    "action": action,
                                    "priority": priority,
                                    "reason": reason,
                                    "signal_strength": round(signal_strength, 2),
                                    "confidence": round(confidence, 3),
                                    "buy_score": round(min(100, buy_score), 2),
                                    "sell_score": round(min(100, sell_score), 2),
                                    "composite_score": round(composite_score, 2),
                                    "summary": {
                                        "key_indicators": key_indicators_list[:5],  # Top 5 indicators
                                        "strengths": strengths_list[:3],  # Top 3 strengths
                                        "concerns": concerns_list[:3],  # Top 3 concerns
                                        "timeframe": "medium_term"
                                    },
                                    "allocation": {
                                        "current": current_pct,
                                        "target": target_pct,
                                        "difference": allocation_drift
                                    },
                                    "metrics": indicators
                                })
                                
                                processed_symbols.add(symbol)
                                continue
                    
                    except Exception as e:
                        self.logger.warning(f"Error processing {symbol}: {e}")
                        diagnostic_info[symbol] = str(e)
                
                # Fallback: simple allocation drift logic if technical analysis failed
                if symbol not in processed_symbols:
                    if abs(allocation_drift) >= rebalance_threshold:
                        action = "sell" if allocation_drift > 0 else "buy"
                        priority = "medium" if abs(allocation_drift) >= 0.10 else "low"
                        reason = f"Allocation drift: {allocation_drift*100:.1f}% from target"
                        
                        recommendations.append({
                            "asset": symbol,
                            "symbol": symbol,
                            "action": action,
                            "priority": priority,
                            "reason": reason,
                            "signal_strength": 0.0,
                            "confidence": min(abs(allocation_drift) * 2, 1.0),
                            "buy_score": 0.0,
                            "sell_score": 0.0,
                            "composite_score": min(abs(allocation_drift) * 200, 100),
                            "summary": {
                                "key_indicators": [],
                                "strengths": [],
                                "concerns": [f"Allocation drift of {abs(allocation_drift)*100:.1f}%"],
                                "timeframe": "immediate"
                            },
                            "allocation": {
                                "current": current_pct,
                                "target": target_pct,
                                "difference": allocation_drift
                            },
                            "metrics": {}
                        })
                        processed_symbols.add(symbol)
            
            return {
                "recommendations": recommendations,
                "total_rebalance_amount": sum(abs(r.get("allocation", {}).get("difference", 0)) for r in recommendations) / 2,
                "model_used": model_used,
                "status": "success" if recommendations else "no_recommendations",
                "diagnostic": diagnostic_info if diagnostic_info else None
            }
            
        except Exception as e:
            self.logger.error(f"Error in recommend_rebalance: {e}", exc_info=True)
            return {
                "recommendations": [],
                "total_rebalance_amount": 0,
                "model_used": "error",
                "status": "error",
                "error": str(e)
            }

    def backtest_recommendations(
        self,
        start_date: str,
        end_date: str,
        initial_capital: float,
        symbols: List[str],
        strategy: str = "follow_ai",
        signal_threshold: float = 20.0
    ) -> Optional[Dict]:
        """
        Backtest AI recommendations strategies on historical data.
        
        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            initial_capital: Starting capital
            symbols: List of symbols to backtest
            strategy: 'follow_ai', 'high_confidence', 'weighted_allocation', 'buy_and_hold'
            signal_threshold: Signal strength threshold for 'follow_ai' strategy
        
        Returns:
            Dictionary with backtest results including equity curve, metrics, trade history
        """
        if not symbols or initial_capital <= 0:
            return {
                'strategy': strategy,
                'status': 'invalid_input',
                'error': 'Invalid input parameters'
            }
        
        try:
            # Parse dates
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            if end_dt <= start_dt:
                return {
                    'strategy': strategy,
                    'status': 'invalid_dates',
                    'error': 'End date must be after start date'
                }
            
            # Get historical data for all symbols (weekly candles)
            historical_data = {}
            for symbol in symbols:
                try:
                    asset_type = 'crypto' if symbol in ['BTC', 'ETH', 'SOL', 'USDT', 'USDC'] else 'stock'
                    data, interval = self.market_data_service.get_symbol_history_with_interval(
                        symbol, asset_type, '1w'  # Weekly data
                    )
                    
                    if data:
                        # Filter to date range
                        filtered_data = []
                        for candle in data:
                            candle_date = datetime.fromisoformat(
                                candle.get('timestamp', candle.get('date', '')).replace('Z', '+00:00')
                            )
                            if start_dt <= candle_date <= end_dt:
                                filtered_data.append(candle)
                        
                        if filtered_data:
                            historical_data[symbol] = sorted(filtered_data, key=lambda x: x.get('timestamp', x.get('date', '')))
                except Exception as e:
                    self.logger.warning(f"Error getting data for {symbol}: {e}")
            
            if not historical_data:
                return {
                    'strategy': strategy,
                    'status': 'no_data',
                    'error': 'No historical data available'
                }
            
            # Build unified timeline (all symbols, weekly candles)
            all_dates = set()
            for symbol, candles in historical_data.items():
                for candle in candles:
                    date_str = candle.get('timestamp', candle.get('date', ''))
                    all_dates.add(date_str)
            
            sorted_dates = sorted(list(all_dates))
            
            # Initialize portfolio state
            cash = initial_capital
            positions = {symbol: 0.0 for symbol in symbols}  # Amount of each asset held
            equity_curve = [initial_capital]
            trade_history = []
            
            # Backtest loop (weekly rebalancing)
            for date_str in sorted_dates:
                date_dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                
                # Get current prices for all symbols
                current_prices = {}
                for symbol in symbols:
                    if symbol in historical_data:
                        for candle in historical_data[symbol]:
                            candle_date_str = candle.get('timestamp', candle.get('date', ''))
                            if candle_date_str == date_str:
                                current_prices[symbol] = candle.get('close', 0)
                                break
                
                # Calculate current portfolio value
                portfolio_value = cash + sum(positions[symbol] * current_prices.get(symbol, 0) for symbol in symbols)
                
                # Strategy-specific logic
                if strategy == 'buy_and_hold':
                    # Buy and hold: buy at start, hold until end
                    if date_str == sorted_dates[0]:
                        # Initial allocation: equal weight
                        allocation_per_symbol = cash / len(symbols)
                        for symbol in symbols:
                            if symbol in current_prices and current_prices[symbol] > 0:
                                shares = allocation_per_symbol / current_prices[symbol]
                                positions[symbol] += shares
                                cash -= shares * current_prices[symbol]
                                
                                trade_history.append({
                                    'date': date_str,
                                    'symbol': symbol,
                                    'action': 'buy',
                                    'shares': shares,
                                    'price': current_prices[symbol],
                                    'value': shares * current_prices[symbol]
                                })
                
                elif strategy in ['follow_ai', 'high_confidence', 'weighted_allocation']:
                    # Get AI recommendations for this date
                    if self.market_data_service:
                        # Build current holdings dict
                        current_holdings = {}
                        for symbol in symbols:
                            if symbol in current_prices and current_prices[symbol] > 0:
                                value = positions[symbol] * current_prices[symbol]
                                current_holdings[symbol] = value / portfolio_value if portfolio_value > 0 else 0
                            
                            # Build target allocation (equal weight for simplicity)
                            target_allocation = {s: 1.0 / len(symbols) for s in symbols}
                            
                            # Get recommendations
                            recommendations_result = self.recommend_rebalance(
                                current_holdings,
                                target_allocation,
                                rebalance_threshold=0.05
                            )
                            
                            if recommendations_result and 'recommendations' in recommendations_result:
                                recommendations = recommendations_result['recommendations']
                                
                                # Filter recommendations based on strategy
                                filtered_recommendations = []
                                for rec in recommendations:
                                    signal_strength = rec.get('signal_strength', 0)
                                    
                                    if strategy == 'follow_ai':
                                        if signal_strength > signal_threshold or signal_strength < -signal_threshold:
                                            filtered_recommendations.append(rec)
                                    elif strategy == 'high_confidence':
                                        if signal_strength > 50 or signal_strength < -50:
                                            filtered_recommendations.append(rec)
                                    elif strategy == 'weighted_allocation':
                                        filtered_recommendations.append(rec)
                                
                                # Execute trades
                                for rec in filtered_recommendations:
                                    symbol = rec.get('symbol', rec.get('asset', ''))
                                    if symbol not in symbols or symbol not in current_prices:
                                        continue
                                    
                                    action = rec.get('action', 'hold')
                                    price = current_prices[symbol]
                                    
                                    if action == 'buy' and cash > 0:
                                        if strategy == 'weighted_allocation':
                                            # Allocate proportionally to signal strength
                                            signal = rec.get('signal_strength', 0)
                                            allocation_pct = max(0, signal / 100.0) if signal > 0 else 0
                                            trade_value = portfolio_value * allocation_pct
                                        else:
                                            # Allocate equal share per recommendation
                                            trade_value = cash / max(1, len([r for r in filtered_recommendations if r.get('action') == 'buy']))
                                        
                                        trade_value = min(trade_value, cash)
                                        shares = trade_value / price if price > 0 else 0
                                        
                                        if shares > 0:
                                            positions[symbol] += shares
                                            cash -= shares * price
                                            
                                            trade_history.append({
                                                'date': date_str,
                                                'symbol': symbol,
                                                'action': 'buy',
                                                'shares': shares,
                                                'price': price,
                                                'value': shares * price,
                                                'signal_strength': signal_strength
                                            })
                                    
                                    elif action == 'sell' and positions[symbol] > 0:
                                        shares_to_sell = positions[symbol]  # Sell all
                                        
                                        if shares_to_sell > 0:
                                            positions[symbol] = 0
                                            cash += shares_to_sell * price
                                            
                                            trade_history.append({
                                                'date': date_str,
                                                'symbol': symbol,
                                                'action': 'sell',
                                                'shares': shares_to_sell,
                                                'price': price,
                                                'value': shares_to_sell * price,
                                                'signal_strength': signal_strength
                                            })
                
                # Record equity curve
                current_value = cash + sum(positions[symbol] * current_prices.get(symbol, 0) for symbol in symbols)
                equity_curve.append(current_value)
            
            # Calculate final metrics
            final_value = equity_curve[-1] if equity_curve else initial_capital
            total_return = (final_value - initial_capital) / initial_capital if initial_capital > 0 else 0
            
            # Calculate weekly returns for Sharpe ratio
            returns = []
            for i in range(1, len(equity_curve)):
                if equity_curve[i-1] > 0:
                    weekly_return = (equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1]
                    returns.append(weekly_return)
            
            # Sharpe ratio (for weekly returns, no additional annualization needed)
            if returns:
                avg_return = np.mean(returns)
                std_return = np.std(returns)
                sharpe_ratio = (avg_return / std_return) if std_return > 0 else 0
            else:
                sharpe_ratio = 0.0
            
            # CAGR (using actual weekly periods, not calendar days)
            num_periods = len(equity_curve) - 1  # Number of weekly periods
            num_years = num_periods / 52.0  # Convert weeks to years
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
            max_drawdown_pct = max_drawdown * 100
            
            # Win rate
            winning_trades = 0
            total_trades = 0
            
            # Match buy/sell pairs
            for i, buy_trade in enumerate(trade_history):
                if buy_trade.get('action') == 'buy':
                    symbol = buy_trade.get('symbol')
                    buy_price = buy_trade.get('price', 0)
                    
                    # Find corresponding sell
                    for sell_trade in trade_history[i+1:]:
                        if sell_trade.get('symbol') == symbol and sell_trade.get('action') == 'sell':
                            sell_price = sell_trade.get('price', 0)
                            if buy_price > 0:
                                trade_return = (sell_price - buy_price) / buy_price
                                total_trades += 1
                                if trade_return > 0:
                                    winning_trades += 1
                            break
            
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            return {
                'strategy': strategy,
                'start_date': start_date,
                'end_date': end_date,
                'initial_capital': initial_capital,
                'final_value': final_value,
                'total_return': total_return * 100,
                'total_return_usd': final_value - initial_capital,
                'cagr': cagr,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown_pct,
                'win_rate': win_rate,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'equity_curve': [
                    {'date': sorted_dates[i] if i < len(sorted_dates) else end_date, 'value': float(val)}
                    for i, val in enumerate(equity_curve)
                ],
                'trade_history': trade_history,
                'status': 'success'
            }
            
        except Exception as e:
            self.logger.error(f"Error in backtest_recommendations: {e}", exc_info=True)
            return {
                'strategy': strategy,
                'status': 'error',
                'error': str(e)
            }
