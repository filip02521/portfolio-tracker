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

    # ==================== CACHE HELPER METHODS ====================
    
    def _get_from_cache(self, cache_dict: Dict, cache_key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if cache_key not in cache_dict:
            return None
        
        cached = cache_dict[cache_key]
        if time.time() - cached['timestamp'] > self._cache_ttl:
            # Expired, remove from cache
            del cache_dict[cache_key]
            return None
        
        return cached['data']
    
    def _save_to_cache(self, cache_dict: Dict, cache_key: str, data: Any):
        """Save value to cache with timestamp"""
        cache_dict[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }
    
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

    # ==================== HELPER ANALYSIS METHODS ====================
    
    def _calculate_volume_profile(self, df: pd.DataFrame, num_levels: int = 20) -> Dict:
        """Calculate Volume Profile (POC, VAH, VAL)."""
        try:
            if df is None or len(df) < 5 or 'volume' not in df.columns:
                return {}
            min_price = df['low'].min()
            max_price = df['high'].max()
            if min_price >= max_price or min_price <= 0:
                return {}
            price_levels = np.linspace(min_price, max_price, num_levels)
            volume_at_price = np.zeros(num_levels)
            for idx, row in df.iterrows():
                low, high, volume = row['low'], row['high'], row.get('volume', 0)
                if volume > 0 and high > low:
                    for i, level in enumerate(price_levels):
                        if low <= level <= high:
                            volume_at_price[i] += volume
            poc_idx = np.argmax(volume_at_price)
            poc_price = float(price_levels[poc_idx])
            total_volume = volume_at_price.sum()
            if total_volume == 0:
                return {}
            sorted_indices = np.argsort(volume_at_price)[::-1]
            cumulative_volume = 0
            value_area_indices = []
            for idx in sorted_indices:
                cumulative_volume += volume_at_price[idx]
                value_area_indices.append(idx)
                if cumulative_volume >= total_volume * 0.70:
                    break
            if value_area_indices:
                value_area_prices = [price_levels[i] for i in value_area_indices]
                vah_price = float(max(value_area_prices))
                val_price = float(min(value_area_prices))
            else:
                vah_price = poc_price
                val_price = poc_price
            current_price = float(df['close'].iloc[-1])
            current_price_position = 'neutral'
            if current_price < val_price:
                    current_price_position = 'below_val'
            elif current_price > vah_price:
                current_price_position = 'above_vah'
            elif abs(current_price - poc_price) / poc_price < 0.02:
                    current_price_position = 'at_poc'
            else:
                current_price_position = 'within_va'
            return {'poc_price': poc_price, 'vah_price': vah_price, 'val_price': val_price, 'current_price_position': current_price_position, 'total_volume': float(total_volume)}
        except Exception as e:
            self.logger.debug(f"Error calculating volume profile: {e}")
            return {}
    
    def _detect_candlestick_patterns(self, df: pd.DataFrame) -> Dict:
        """Detect candlestick patterns."""
        try:
            if df is None or len(df) < 2:
                return {}
            patterns = {}
            prev_candle = df.iloc[-2]
            curr_candle = df.iloc[-1]
            curr_body = abs(curr_candle['close'] - curr_candle['open'])
            curr_range = curr_candle['high'] - curr_candle['low']
            if curr_range == 0:
                return {}
            body_ratio = curr_body / curr_range if curr_range > 0 else 0
            if body_ratio < 0.1:
                patterns['doji'] = {'signal': 'neutral', 'weight': 0, 'confidence': 0.7}
            lower_wick = curr_candle['low'] - min(curr_candle['open'], curr_candle['close'])
            upper_wick = curr_candle['high'] - max(curr_candle['open'], curr_candle['close'])
            if body_ratio < 0.3 and lower_wick > 2 * curr_body and upper_wick < curr_body:
                patterns['hammer'] = {'signal': 'buy', 'weight': 8, 'confidence': 0.7}
            if body_ratio < 0.3 and upper_wick > 2 * curr_body and lower_wick < curr_body:
                patterns['shooting_star'] = {'signal': 'sell', 'weight': 8, 'confidence': 0.7}
            prev_is_bullish = prev_candle['close'] > prev_candle['open']
            curr_is_bullish = curr_candle['close'] > curr_candle['open']
            if (not prev_is_bullish and curr_is_bullish and curr_candle['open'] < prev_candle['close'] and curr_candle['close'] > prev_candle['open']):
                patterns['bullish_engulfing'] = {'signal': 'buy', 'weight': 10, 'confidence': 0.75}
            if (prev_is_bullish and not curr_is_bullish and curr_candle['open'] > prev_candle['close'] and curr_candle['close'] < prev_candle['open']):
                patterns['bearish_engulfing'] = {'signal': 'sell', 'weight': 10, 'confidence': 0.75}
            return patterns
        except Exception as e:
            self.logger.debug(f"Error detecting candlestick patterns: {e}")
            return {}
    
    def _detect_chart_patterns(self, df: pd.DataFrame) -> Dict:
        """Detect chart patterns."""
        try:
            if df is None or len(df) < 20:
                return {}
            patterns = {}
            closes = df['close'].values
            highs = df['high'].values
            lows = df['low'].values
            swing_highs = []
            swing_lows = []
            lookback = min(5, len(df) // 4)
            for i in range(lookback, len(df) - lookback):
                if all(highs[i] >= highs[i-j] for j in range(1, lookback+1)) and all(highs[i] >= highs[i+j] for j in range(1, lookback+1)):
                    swing_highs.append((i, highs[i]))
                if all(lows[i] <= lows[i-j] for j in range(1, lookback+1)) and all(lows[i] <= lows[i+j] for j in range(1, lookback+1)):
                    swing_lows.append((i, lows[i]))
            if len(swing_highs) >= 3:
                last_three = swing_highs[-3:]
                if (last_three[0][1] < last_three[1][1] > last_three[2][1] and abs(last_three[0][1] - last_three[2][1]) / last_three[1][1] < 0.1):
                    patterns['head_and_shoulders'] = {'signal': 'sell', 'weight': 15, 'confidence': 0.6}
            if len(swing_lows) >= 3:
                last_three = swing_lows[-3:]
                if (last_three[0][1] > last_three[1][1] < last_three[2][1] and abs(last_three[0][1] - last_three[2][1]) / last_three[1][1] < 0.1):
                    patterns['inverse_head_and_shoulders'] = {'signal': 'buy', 'weight': 15, 'confidence': 0.6}
            if len(swing_highs) >= 2 and len(swing_lows) >= 2:
                recent_highs = [h[1] for h in swing_highs[-3:]]
                recent_lows = [l[1] for l in swing_lows[-3:]]
                if len(recent_highs) >= 2 and len(recent_lows) >= 2:
                    high_std = np.std(recent_highs)
                    low_trend = (recent_lows[-1] - recent_lows[0]) / max(recent_lows) if recent_lows else 0
                    if high_std / np.mean(recent_highs) < 0.02 and low_trend > 0.05:
                        patterns['ascending_triangle'] = {'signal': 'buy', 'weight': 10, 'confidence': 0.65}
                    low_std = np.std(recent_lows)
                    high_trend = (recent_highs[-1] - recent_highs[0]) / max(recent_highs) if recent_highs else 0
                    if low_std / np.mean(recent_lows) < 0.02 and high_trend < -0.05:
                        patterns['descending_triangle'] = {'signal': 'sell', 'weight': 10, 'confidence': 0.65}
            if len(df) >= 15:
                first_half = closes[:len(closes)//2]
                second_half = closes[len(closes)//2:]
                first_trend = (first_half[-1] - first_half[0]) / first_half[0] if first_half[0] > 0 else 0
                second_volatility = np.std(second_half) / np.mean(second_half) if len(second_half) > 0 else 0
                if abs(first_trend) > 0.1 and second_volatility < 0.05:
                    if first_trend > 0:
                        patterns['bull_flag'] = {'signal': 'buy', 'weight': 12, 'confidence': 0.6}
                else:
                        patterns['bear_flag'] = {'signal': 'sell', 'weight': 12, 'confidence': 0.6}
            return patterns
        except Exception as e:
            self.logger.debug(f"Error detecting chart patterns: {e}")
            return {}
    
    def _detect_support_resistance(self, df: pd.DataFrame, threshold: float = 0.02) -> Dict:
        """Detect support and resistance levels."""
        try:
            if df is None or len(df) < 10:
                return {}
            highs = df['high'].values
            lows = df['low'].values
            closes = df['close'].values
            current_price = closes[-1]
            lookback = min(5, len(df) // 4)
            swing_highs = []
            swing_lows = []
            for i in range(lookback, len(df) - lookback):
                if all(highs[i] >= highs[i-j] for j in range(1, lookback+1)) and all(highs[i] >= highs[i+j] for j in range(1, lookback+1)):
                    swing_highs.append(highs[i])
                if all(lows[i] <= lows[i-j] for j in range(1, lookback+1)) and all(lows[i] <= lows[i+j] for j in range(1, lookback+1)):
                    swing_lows.append(lows[i])
            support_levels = sorted(swing_lows, reverse=True)[:3]
            resistance_levels = sorted(swing_highs)[-3:]
            near_support = False
            near_resistance = False
            if support_levels:
                nearest_support = max([s for s in support_levels if s < current_price], default=None)
                if nearest_support and abs(current_price - nearest_support) / current_price < threshold:
                    near_support = True
            if resistance_levels:
                nearest_resistance = min([r for r in resistance_levels if r > current_price], default=None)
                if nearest_resistance and abs(nearest_resistance - current_price) / current_price < threshold:
                    near_resistance = True
            return {'near_support': near_support, 'near_resistance': near_resistance, 'support_levels': [float(s) for s in support_levels] if support_levels else [], 'resistance_levels': [float(r) for r in resistance_levels] if resistance_levels else []}
        except Exception as e:
            self.logger.debug(f"Error detecting support/resistance: {e}")
            return {}
    
    def _calculate_correlation_and_beta(self, df: pd.DataFrame, symbol: str, benchmark: str = 'BTC') -> Dict:
        """Calculate correlation and beta relative to benchmark."""
        try:
            if df is None or len(df) < 10 or not self.market_data_service:
                return {}
            try:
                benchmark_data, _ = self.market_data_service.get_symbol_history_with_interval(benchmark, 30)
                if not benchmark_data or len(benchmark_data) < 10:
                    return {}
                except:
                return {}
            asset_returns = df['close'].pct_change().dropna().values
            benchmark_returns = pd.Series([d.get('close', 0) for d in benchmark_data]).pct_change().dropna().values
            min_len = min(len(asset_returns), len(benchmark_returns))
            if min_len < 10:
                return {}
            asset_returns = asset_returns[-min_len:]
            benchmark_returns = benchmark_returns[-min_len:]
            if len(asset_returns) > 1 and len(benchmark_returns) > 1:
                correlation = np.corrcoef(asset_returns, benchmark_returns)[0, 1]
                if np.isnan(correlation):
                    correlation = 0.0
            else:
                correlation = 0.0
            if len(benchmark_returns) > 1 and np.var(benchmark_returns) > 0:
                beta = np.cov(asset_returns, benchmark_returns)[0, 1] / np.var(benchmark_returns)
                if np.isnan(beta):
                    beta = 1.0
                        else:
                beta = 1.0
            asset_total_return = (asset_returns + 1).prod() - 1
            benchmark_total_return = (benchmark_returns + 1).prod() - 1
            outperforming = False
            underperforming = False
            if asset_total_return > benchmark_total_return * 1.1:
                outperforming = True
            elif asset_total_return < benchmark_total_return * 0.9:
                underperforming = True
            return {'correlation': float(correlation), 'beta': float(beta), 'outperforming': outperforming, 'underperforming': underperforming, 'asset_return': float(asset_total_return), 'benchmark_return': float(benchmark_total_return)}
        except Exception as e:
            self.logger.debug(f"Error calculating correlation/beta: {e}")
            return {}

    # ==================== HELPER ANALYSIS METHODS ====================        def _calculate_volume_profile(self, df: pd.DataFrame, num_levels: int = 20) -> Dict:        """Calculate Volume Profile (POC, VAH, VAL)."""        try:            if df is None or len(df) < 5 or 'volume' not in df.columns:                return {}            min_price = df['low'].min()            max_price = df['high'].max()            if min_price >= max_price or min_price <= 0:                return {}            price_levels = np.linspace(min_price, max_price, num_levels)            volume_at_price = np.zeros(num_levels)            for idx, row in df.iterrows():                low, high, volume = row['low'], row['high'], row.get('volume', 0)                if volume > 0 and high > low:                    for i, level in enumerate(price_levels):                        if low <= level <= high:                            volume_at_price[i] += volume            poc_idx = np.argmax(volume_at_price)            poc_price = float(price_levels[poc_idx])            total_volume = volume_at_price.sum()            if total_volume == 0:                return {}            sorted_indices = np.argsort(volume_at_price)[::-1]            cumulative_volume = 0            value_area_indices = []            for idx in sorted_indices:                cumulative_volume += volume_at_price[idx]                value_area_indices.append(idx)                if cumulative_volume >= total_volume * 0.70:                    break            if value_area_indices:                value_area_prices = [price_levels[i] for i in value_area_indices]                vah_price = float(max(value_area_prices))                val_price = float(min(value_area_prices))            else:                vah_price = poc_price                val_price = poc_price            current_price = float(df['close'].iloc[-1])            current_price_position = 'neutral'            if current_price < val_price:                current_price_position = 'below_val'            elif current_price > vah_price:                current_price_position = 'above_vah'            elif abs(current_price - poc_price) / poc_price < 0.02:                current_price_position = 'at_poc'            else:                current_price_position = 'within_va'            return {'poc_price': poc_price, 'vah_price': vah_price, 'val_price': val_price, 'current_price_position': current_price_position, 'total_volume': float(total_volume)}        except Exception as e:            self.logger.debug(f"Error calculating volume profile: {e}")            return {}        def _detect_candlestick_patterns(self, df: pd.DataFrame) -> Dict:        """Detect candlestick patterns."""        try:            if df is None or len(df) < 2:                return {}            patterns = {}            prev_candle = df.iloc[-2]            curr_candle = df.iloc[-1]            curr_body = abs(curr_candle['close'] - curr_candle['open'])            curr_range = curr_candle['high'] - curr_candle['low']            if curr_range == 0:                return {}            body_ratio = curr_body / curr_range if curr_range > 0 else 0            if body_ratio < 0.1:                patterns['doji'] = {'signal': 'neutral', 'weight': 0, 'confidence': 0.7}            lower_wick = curr_candle['low'] - min(curr_candle['open'], curr_candle['close'])            upper_wick = curr_candle['high'] - max(curr_candle['open'], curr_candle['close'])            if body_ratio < 0.3 and lower_wick > 2 * curr_body and upper_wick < curr_body:                patterns['hammer'] = {'signal': 'buy', 'weight': 8, 'confidence': 0.7}            if body_ratio < 0.3 and upper_wick > 2 * curr_body and lower_wick < curr_body:                patterns['shooting_star'] = {'signal': 'sell', 'weight': 8, 'confidence': 0.7}            prev_is_bullish = prev_candle['close'] > prev_candle['open']            curr_is_bullish = curr_candle['close'] > curr_candle['open']            if (not prev_is_bullish and curr_is_bullish and curr_candle['open'] < prev_candle['close'] and curr_candle['close'] > prev_candle['open']):                patterns['bullish_engulfing'] = {'signal': 'buy', 'weight': 10, 'confidence': 0.75}            if (prev_is_bullish and not curr_is_bullish and curr_candle['open'] > prev_candle['close'] and curr_candle['close'] < prev_candle['open']):                patterns['bearish_engulfing'] = {'signal': 'sell', 'weight': 10, 'confidence': 0.75}            return patterns        except Exception as e:            self.logger.debug(f"Error detecting candlestick patterns: {e}")            return {}        def _detect_chart_patterns(self, df: pd.DataFrame) -> Dict:        """Detect chart patterns."""        try:            if df is None or len(df) < 20:                return {}            patterns = {}            closes = df['close'].values            highs = df['high'].values            lows = df['low'].values            swing_highs = []            swing_lows = []            lookback = min(5, len(df) // 4)            for i in range(lookback, len(df) - lookback):                if all(highs[i] >= highs[i-j] for j in range(1, lookback+1)) and all(highs[i] >= highs[i+j] for j in range(1, lookback+1)):                    swing_highs.append((i, highs[i]))                if all(lows[i] <= lows[i-j] for j in range(1, lookback+1)) and all(lows[i] <= lows[i+j] for j in range(1, lookback+1)):                    swing_lows.append((i, lows[i]))            if len(swing_highs) >= 3:                last_three = swing_highs[-3:]                if (last_three[0][1] < last_three[1][1] > last_three[2][1] and abs(last_three[0][1] - last_three[2][1]) / last_three[1][1] < 0.1):                    patterns['head_and_shoulders'] = {'signal': 'sell', 'weight': 15, 'confidence': 0.6}            if len(swing_lows) >= 3:                last_three = swing_lows[-3:]                if (last_three[0][1] > last_three[1][1] < last_three[2][1] and abs(last_three[0][1] - last_three[2][1]) / last_three[1][1] < 0.1):                    patterns['inverse_head_and_shoulders'] = {'signal': 'buy', 'weight': 15, 'confidence': 0.6}            if len(swing_highs) >= 2 and len(swing_lows) >= 2:                recent_highs = [h[1] for h in swing_highs[-3:]]                recent_lows = [l[1] for l in swing_lows[-3:]]                if len(recent_highs) >= 2 and len(recent_lows) >= 2:                    high_std = np.std(recent_highs)                    low_trend = (recent_lows[-1] - recent_lows[0]) / max(recent_lows) if recent_lows else 0                    if high_std / np.mean(recent_highs) < 0.02 and low_trend > 0.05:                        patterns['ascending_triangle'] = {'signal': 'buy', 'weight': 10, 'confidence': 0.65}                    low_std = np.std(recent_lows)                    high_trend = (recent_highs[-1] - recent_highs[0]) / max(recent_highs) if recent_highs else 0                    if low_std / np.mean(recent_lows) < 0.02 and high_trend < -0.05:                        patterns['descending_triangle'] = {'signal': 'sell', 'weight': 10, 'confidence': 0.65}            if len(df) >= 15:                first_half = closes[:len(closes)//2]                second_half = closes[len(closes)//2:]                first_trend = (first_half[-1] - first_half[0]) / first_half[0] if first_half[0] > 0 else 0                second_volatility = np.std(second_half) / np.mean(second_half) if len(second_half) > 0 else 0                if abs(first_trend) > 0.1 and second_volatility < 0.05:                    if first_trend > 0:                        patterns['bull_flag'] = {'signal': 'buy', 'weight': 12, 'confidence': 0.6}                    else:                        patterns['bear_flag'] = {'signal': 'sell', 'weight': 12, 'confidence': 0.6}            return patterns        except Exception as e:            self.logger.debug(f"Error detecting chart patterns: {e}")            return {}        def _detect_support_resistance(self, df: pd.DataFrame, threshold: float = 0.02) -> Dict:        """Detect support and resistance levels."""        try:            if df is None or len(df) < 10:                return {}            highs = df['high'].values            lows = df['low'].values            closes = df['close'].values            current_price = closes[-1]            lookback = min(5, len(df) // 4)            swing_highs = []            swing_lows = []            for i in range(lookback, len(df) - lookback):                if all(highs[i] >= highs[i-j] for j in range(1, lookback+1)) and all(highs[i] >= highs[i+j] for j in range(1, lookback+1)):                    swing_highs.append(highs[i])                if all(lows[i] <= lows[i-j] for j in range(1, lookback+1)) and all(lows[i] <= lows[i+j] for j in range(1, lookback+1)):                    swing_lows.append(lows[i])            support_levels = sorted(swing_lows, reverse=True)[:3]            resistance_levels = sorted(swing_highs)[-3:]            near_support = False            near_resistance = False            if support_levels:                nearest_support = max([s for s in support_levels if s < current_price], default=None)                if nearest_support and abs(current_price - nearest_support) / current_price < threshold:                    near_support = True            if resistance_levels:                nearest_resistance = min([r for r in resistance_levels if r > current_price], default=None)                if nearest_resistance and abs(nearest_resistance - current_price) / current_price < threshold:                    near_resistance = True            return {'near_support': near_support, 'near_resistance': near_resistance, 'support_levels': [float(s) for s in support_levels] if support_levels else [], 'resistance_levels': [float(r) for r in resistance_levels] if resistance_levels else []}        except Exception as e:            self.logger.debug(f"Error detecting support/resistance: {e}")            return {}        def _calculate_correlation_and_beta(self, df: pd.DataFrame, symbol: str, benchmark: str = 'BTC') -> Dict:        """Calculate correlation and beta relative to benchmark."""        try:            if df is None or len(df) < 10 or not self.market_data_service:                return {}            try:                benchmark_data, _ = self.market_data_service.get_symbol_history_with_interval(benchmark, 'crypto', '1d')                if not benchmark_data or len(benchmark_data) < 10:                    return {}            except:                return {}            asset_returns = df['close'].pct_change().dropna().values            benchmark_returns = pd.Series([d.get('close', 0) for d in benchmark_data]).pct_change().dropna().values            min_len = min(len(asset_returns), len(benchmark_returns))            if min_len < 10:                return {}            asset_returns = asset_returns[-min_len:]            benchmark_returns = benchmark_returns[-min_len:]            if len(asset_returns) > 1 and len(benchmark_returns) > 1:                correlation = np.corrcoef(asset_returns, benchmark_returns)[0, 1]                if np.isnan(correlation):                    correlation = 0.0            else:                correlation = 0.0            if len(benchmark_returns) > 1 and np.var(benchmark_returns) > 0:                beta = np.cov(asset_returns, benchmark_returns)[0, 1] / np.var(benchmark_returns)                if np.isnan(beta):                    beta = 1.0            else:                beta = 1.0            asset_total_return = (asset_returns + 1).prod() - 1            benchmark_total_return = (benchmark_returns + 1).prod() - 1            outperforming = False            underperforming = False            if asset_total_return > benchmark_total_return * 1.1:                outperforming = True            elif asset_total_return < benchmark_total_return * 0.9:                underperforming = True            return {'correlation': float(correlation), 'beta': float(beta), 'outperforming': outperforming, 'underperforming': underperforming, 'asset_return': float(asset_total_return), 'benchmark_return': float(benchmark_total_return)}        except Exception as e:            self.logger.debug(f"Error calculating correlation/beta: {e}")            return {}        # ==================== MAIN AI METHODS ====================
    
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
                
                # Track indicator consensus for quality scoring
                bullish_count = 0
                bearish_count = 0
                neutral_count = 0
                has_golden_cross = False
                has_inverse_h_and_s = False
                
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
                        # Get historical data for multiple timeframes to determine recommendation timeframe
                        # Daily data for short-term analysis
                        daily_data, daily_interval = self.market_data_service.get_symbol_history_with_interval(
                            symbol, 30
                        )
                        # Weekly data for long-term analysis
                        weekly_data, weekly_interval = self.market_data_service.get_symbol_history_with_interval(
                            symbol, 90  # Gets weekly data (prediction_horizon > 60)
                        )
                        
                        # Use daily data as primary for calculations
                        historical_data = daily_data
                        interval = daily_interval
                        
                        # Calculate signals for both timeframes
                        daily_signal = 0.0
                        weekly_signal = 0.0
                        timeframe_info = "krótkoterminowe"  # Default - gdy brak danych technicznych
                        same_direction = False  # Default
                        
                        if historical_data and len(historical_data) >= 50:
                            df = pd.DataFrame(historical_data)
                            
                            # Calculate technical indicators
                            indicators = self._calculate_technical_indicators(df, symbol)
                            
                            if indicators is not None and len(indicators) > 0:
                                model_used = "comprehensive_technical_analysis"
                                
                                # Debug: Log indicators for troubleshooting
                                self.logger.debug(f"Calculated {len(indicators)} indicators for {symbol}: {list(indicators.keys())}")
                                
                                # Calculate scoring based on indicators
                                # RSI
                                if 'rsi' in indicators:
                                    rsi_val = indicators['rsi'].get('value', 50)
                                    if rsi_val < 30:
                                signal_strength += 15
                                        buy_score += 15
                                        bullish_count += 1
                                        key_indicators_list.append({"name": "RSI", "value": rsi_val, "signal": "buy", "weight": "high"})
                                        strengths_list.append("RSI indicates oversold condition")
                                    elif rsi_val > 70:
                                signal_strength -= 15
                                        sell_score += 15
                                        bearish_count += 1
                                        key_indicators_list.append({"name": "RSI", "value": rsi_val, "signal": "sell", "weight": "high"})
                                        concerns_list.append("RSI indicates overbought condition")
                                    else:
                                        neutral_count += 1
                                
                                # MACD
                                if 'macd' in indicators:
                                    macd_data = indicators['macd']
                                    macd_crossover = macd_data.get('crossover')
                                    macd_trend = macd_data.get('trend')
                                    
                                    if macd_crossover == 'bullish':
                                    signal_strength += 20
                                        buy_score += 20
                                        bullish_count += 1
                                        key_indicators_list.append({"name": "MACD", "value": macd_data.get('histogram', 0), "signal": "buy", "weight": "very_high"})
                                        strengths_list.append("MACD bullish crossover detected")
                                    elif macd_crossover == 'bearish':
                                    signal_strength -= 20
                                        sell_score += 20
                                        bearish_count += 1
                                        key_indicators_list.append({"name": "MACD", "value": macd_data.get('histogram', 0), "signal": "sell", "weight": "very_high"})
                                        concerns_list.append("MACD bearish crossover detected")
                                    elif macd_trend == 'bullish' and not macd_crossover:
                                    signal_strength += 5
                                        buy_score += 5
                                        bullish_count += 1
                                    elif macd_trend == 'bearish' and not macd_crossover:
                                    signal_strength -= 5
                                        sell_score += 5
                                        bearish_count += 1
                                    else:
                                        neutral_count += 1
                                
                                # Golden/Death Cross (check first to avoid double-counting with MA weights)
                                golden_cross_active = False
                                if 'ma_cross' in indicators:
                                    ma_cross = indicators['ma_cross']
                                    if ma_cross.get('golden_cross'):
                                        signal_strength += 10
                                        buy_score += 10
                                        golden_cross_active = True
                                        strengths_list.append("Golden Cross pattern (MA50 > MA200)")
                                    elif ma_cross.get('death_cross'):
                                        signal_strength -= 10
                                        sell_score += 10
                                        golden_cross_active = True
                                        concerns_list.append("Death Cross pattern (MA50 < MA200)")
                                
                                # Moving Averages (only add weights if Golden/Death Cross is not active)
                                if not golden_cross_active:
                                    if 'ma50' in indicators:
                                        ma50_signal = indicators['ma50'].get('signal', 'neutral')
                                        if ma50_signal == 'buy':
                                signal_strength += 5
                                            buy_score += 5
                                            bullish_count += 1
                                        elif ma50_signal == 'sell':
                                signal_strength -= 5
                                            sell_score += 5
                                            bearish_count += 1
                                        else:
                                            neutral_count += 1
                                    
                                    if 'ma200' in indicators:
                                        ma200_signal = indicators['ma200'].get('signal', 'neutral')
                                        if ma200_signal == 'buy':
                                signal_strength += 8
                                            buy_score += 8
                                            bullish_count += 1
                                        elif ma200_signal == 'sell':
                                signal_strength -= 8
                                            sell_score += 8
                                            bearish_count += 1
                            else:
                                            neutral_count += 1
                                
                                # Bollinger Bands
                                if 'bollinger_bands' in indicators:
                                    bb = indicators['bollinger_bands']
                                    bb_signal = bb.get('signal', 'neutral')
                                    if bb_signal == 'buy':
                                        signal_strength += 12
                                        buy_score += 12
                                        bullish_count += 1
                                        key_indicators_list.append({"name": "Bollinger", "value": bb.get('position', 50), "signal": "buy", "weight": "high"})
                                    elif bb_signal == 'sell':
                                        signal_strength -= 12
                                        sell_score += 12
                                        bearish_count += 1
                                        key_indicators_list.append({"name": "Bollinger", "value": bb.get('position', 50), "signal": "sell", "weight": "high"})
                            else:
                                        neutral_count += 1
                                
                                # Stochastic
                                if 'stochastic' in indicators:
                                    stoch = indicators['stochastic']
                                    stoch_k = stoch.get('k', 50)
                                    stoch_d = stoch.get('d', 50)
                                    if stoch_k < 20:
                                    signal_strength += 8
                                        buy_score += 8
                                        bullish_count += 1
                                    elif stoch_k > 80:
                                signal_strength -= 8
                                        sell_score += 8
                                        bearish_count += 1
                                    elif stoch_k > stoch_d:
                                        signal_strength += 6
                                        buy_score += 6
                                        bullish_count += 1
                                    elif stoch_k < stoch_d:
                                        signal_strength -= 6
                                        sell_score += 6
                                        bearish_count += 1
                                    else:
                                        neutral_count += 1
                                
                                # Williams %R
                                if 'williams_r' in indicators:
                                    willr = indicators['williams_r']
                                    willr_signal = willr.get('signal', 'neutral')
                                    if willr_signal == 'buy':
                                        signal_strength += 4
                                        buy_score += 4
                                        bullish_count += 1
                                    elif willr_signal == 'sell':
                                        signal_strength -= 4
                                        sell_score += 4
                                        bearish_count += 1
                                    else:
                                        neutral_count += 1
                                
                                # MFI
                                if 'mfi' in indicators:
                                    mfi = indicators['mfi']
                                    mfi_signal = mfi.get('signal', 'neutral')
                                    if mfi_signal == 'buy':
                                        signal_strength += 7
                                        buy_score += 7
                                        bullish_count += 1
                                    elif mfi_signal == 'sell':
                                        signal_strength -= 7
                                        sell_score += 7
                                        bearish_count += 1
                                    else:
                                        neutral_count += 1
                                
                                # CCI (with stricter thresholds)
                                if 'cci' in indicators:
                                    cci_val = indicators['cci'].get('value', 0)
                                    if cci_val > 150:
                                    signal_strength += 8
                                        buy_score += 8
                                        bullish_count += 1
                                    elif cci_val < -150:
                                        signal_strength -= 8
                                        sell_score += 8
                                        bearish_count += 1
                                    elif cci_val > 100:
                                        signal_strength += 4
                                        buy_score += 4
                                        bullish_count += 1
                                    elif cci_val < -100:
                                        signal_strength -= 4
                                        sell_score += 4
                                        bearish_count += 1
                                else:
                                        neutral_count += 1
                                
                                # ADX
                                if 'adx' in indicators:
                                    adx = indicators['adx']
                                    if adx.get('strength') == 'strong' and adx.get('direction') == 'bullish':
                                        signal_strength += 8
                                        buy_score += 8
                                        bullish_count += 1
                                    elif adx.get('strength') == 'strong' and adx.get('direction') == 'bearish':
                                    signal_strength -= 8
                                        sell_score += 8
                                        bearish_count += 1
                                    else:
                                        neutral_count += 1
                                
                                # Volume indicators
                                if 'obv' in indicators:
                                    obv_signal = indicators['obv'].get('signal', 'neutral')
                                    if obv_signal == 'buy':
                                        signal_strength += 5
                                        buy_score += 5
                                        bullish_count += 1
                                    elif obv_signal == 'sell':
                                        signal_strength -= 5
                                        sell_score += 5
                                        bearish_count += 1
                                    else:
                                        neutral_count += 1
                                
                                if 'cmf' in indicators:
                                    cmf = indicators['cmf']
                                    cmf_signal = cmf.get('signal', 'neutral')
                                    if cmf_signal == 'buy':
                                        signal_strength += 7
                                        buy_score += 7
                                        bullish_count += 1
                                    elif cmf_signal == 'sell':
                                        signal_strength -= 7
                                        sell_score += 7
                                        bearish_count += 1
                                    else:
                                        neutral_count += 1
                                
                                # VWAP
                                if 'vwap' in indicators:
                                    vwap_signal = indicators['vwap'].get('signal', 'neutral')
                                    if vwap_signal == 'buy':
                                        signal_strength += 6
                                        buy_score += 6
                                        bullish_count += 1
                                    elif vwap_signal == 'sell':
                                        signal_strength -= 6
                                        sell_score += 6
                                        bearish_count += 1
                                    else:
                                        neutral_count += 1
                                
                                # Momentum
                                if 'momentum' in indicators:
                                    momentum = indicators['momentum']
                                    if momentum.get('short_term') == 'bullish':
                                signal_strength += 5
                                        buy_score += 5
                                        bullish_count += 1
                                    elif momentum.get('short_term') == 'bearish':
                                signal_strength -= 5
                                        sell_score += 5
                                        bearish_count += 1
                                    else:
                                        neutral_count += 1
                                
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
                                    volatility_pct = 0  # Default for volatility factor calculation
                                
                                # Support/Resistance
                                support_resistance = self._detect_support_resistance(df)
                                if support_resistance:
                                    if support_resistance.get('near_support'):
                                        signal_strength += 8
                                        buy_score += 8
                                        bullish_count += 1
                                        strengths_list.append("Price near support level")
                                    elif support_resistance.get('near_resistance'):
                                        signal_strength -= 8
                                        sell_score += 8
                                        bearish_count += 1
                                        concerns_list.append("Price near resistance level")
                            else:
                                        neutral_count += 1
                                
                                # Volume Profile
                                volume_profile = self._calculate_volume_profile(df)
                                if volume_profile:
                                    position = volume_profile.get('current_price_position', '')
                                    if position == 'below_val':
                                        signal_strength += 8
                                        buy_score += 8
                                        bullish_count += 1
                                    elif position == 'above_vah':
                                        signal_strength -= 8
                                        sell_score += 8
                                        bearish_count += 1
                                    else:
                                        neutral_count += 1
                                
                                # Chart Patterns
                                chart_patterns = self._detect_chart_patterns(df)
                                for pattern_name, pattern_data in chart_patterns.items():
                                    pattern_signal = pattern_data.get('signal', 'neutral')
                                    pattern_weight = pattern_data.get('weight', 0)
                                    if pattern_signal == 'buy':
                                        signal_strength += pattern_weight
                                        buy_score += pattern_weight
                                        bullish_count += 1
                                        if 'inverse_head_and_shoulders' in pattern_name:
                                            has_inverse_h_and_s = True
                                        strengths_list.append(f"{pattern_name.replace('_', ' ').title()} pattern detected")
                                    elif pattern_signal == 'sell':
                                        signal_strength -= pattern_weight
                                        sell_score += pattern_weight
                                        bearish_count += 1
                                        concerns_list.append(f"{pattern_name.replace('_', ' ').title()} pattern detected")
                                    else:
                                        neutral_count += 1
                                
                                # Candlestick Patterns
                                candlestick_patterns = self._detect_candlestick_patterns(df)
                                for pattern_name, pattern_data in candlestick_patterns.items():
                                    pattern_signal = pattern_data.get('signal', 'neutral')
                                    if pattern_signal == 'buy':
                                        signal_strength += 10
                                        buy_score += 10
                                        bullish_count += 1
                                    elif pattern_signal == 'sell':
                                        signal_strength -= 10
                                        sell_score += 10
                                        bearish_count += 1
                                    else:
                                        neutral_count += 1
                                
                                # Correlation/Beta
                                correlation_beta = self._calculate_correlation_and_beta(df, symbol, 'BTC')
                                if correlation_beta:
                                    if correlation_beta.get('outperforming'):
                                signal_strength += 3
                                        buy_score += 3
                                        bullish_count += 1
                                    elif correlation_beta.get('underperforming'):
                                signal_strength -= 3
                                        sell_score += 3
                                        bearish_count += 1
                                    else:
                                        neutral_count += 1
                                
                                # Calculate indicator consensus for quality scoring
                                total_indicators = bullish_count + bearish_count + neutral_count
                                if total_indicators > 0:
                                    consensus_ratio = max(bullish_count, bearish_count) / total_indicators
                                else:
                                    consensus_ratio = 0.5
                                
                                # Calculate quality multiplier for signal_strength
                                quality_multiplier = 1.0
                                
                                # Bonus za zgodność wskaźników (>80% consensus)
                                if consensus_ratio > 0.8:
                                    quality_multiplier += 0.2
                                
                                # Apply quality multiplier before clamping
                                raw_signal_strength = signal_strength
                                signal_strength = signal_strength * quality_multiplier
                                
                                # Clamp signal_strength to [-100, 100]
                                signal_strength = max(-100, min(100, signal_strength))
                                
                                # Store daily signal for timeframe analysis
                                daily_signal = signal_strength
                                
                                # Calculate weekly timeframe signal for timeframe determination
                                if weekly_data and len(weekly_data) >= 20:
                                    try:
                                        weekly_df = pd.DataFrame(weekly_data)
                                        weekly_indicators = self._calculate_technical_indicators(weekly_df, symbol)
                                        
                                        if weekly_indicators and len(weekly_indicators) > 0:
                                            weekly_signal_temp = 0.0
                                            
                                            # Quick calculation of weekly signal (simplified version focusing on key indicators)
                                            if 'rsi' in weekly_indicators:
                                                rsi_w = weekly_indicators['rsi'].get('value', 50)
                                                if rsi_w < 30:
                                                    weekly_signal_temp += 15
                                                elif rsi_w > 70:
                                                    weekly_signal_temp -= 15
                                            
                                            if 'macd' in weekly_indicators:
                                                macd_w = weekly_indicators['macd']
                                                if macd_w.get('crossover') == 'bullish':
                                                    weekly_signal_temp += 20
                                                elif macd_w.get('crossover') == 'bearish':
                                                    weekly_signal_temp -= 20
                                                elif macd_w.get('trend') == 'bullish':
                                                    weekly_signal_temp += 5
                                                elif macd_w.get('trend') == 'bearish':
                                                    weekly_signal_temp -= 5
                                            
                                            if 'ma_cross' in weekly_indicators:
                                                ma_cross_w = weekly_indicators['ma_cross']
                                                if ma_cross_w.get('golden_cross'):
                                                    weekly_signal_temp += 10
                                                elif ma_cross_w.get('death_cross'):
                                                    weekly_signal_temp -= 10
                                            
                                            if 'bollinger_bands' in weekly_indicators:
                                                bb_w = weekly_indicators['bollinger_bands']
                                                if bb_w.get('signal') == 'buy':
                                                    weekly_signal_temp += 12
                                                elif bb_w.get('signal') == 'sell':
                                                    weekly_signal_temp -= 12
                                            
                                            weekly_signal = max(-100, min(100, weekly_signal_temp))
                            else:
                                            weekly_signal = 0.0
                                    except Exception as e:
                                        self.logger.debug(f"Error calculating weekly indicators for {symbol}: {e}")
                                        weekly_signal = 0.0
                                else:
                                    weekly_signal = 0.0
                                
                                # Determine timeframe based on alignment of daily and weekly signals
                                # Strong buy/sell on both = długoterminowe+
                                # Strong on one = średnioterminowe
                                # Weak signals = krótkoterminowe
                                abs_daily = abs(daily_signal)
                                abs_weekly = abs(weekly_signal)
                                same_direction = (daily_signal > 0 and weekly_signal > 0) or (daily_signal < 0 and weekly_signal < 0)
                                
                                if same_direction and abs_daily > 30 and abs_weekly > 30:
                                    # Both timeframes show strong signal in same direction = długoterminowe+
                                    timeframe_info = "długoterminowe+"
                                    if abs_daily > 50 and abs_weekly > 50:
                                        timeframe_info = "długoterminowe+ (mocny sygnał)"
                                elif same_direction and (abs_daily > 20 or abs_weekly > 20):
                                    # Some alignment with moderate signals = średnioterminowe
                                    timeframe_info = "średnioterminowe"
                                elif abs_daily > 20 or abs_weekly > 20:
                                    # Strong signal on one timeframe = średnioterminowe
                                    timeframe_info = "średnioterminowe"
                            else:
                                    # Weak signals or no clear trend = krótkoterminowe
                                    timeframe_info = "krótkoterminowe"
                                
                                # Debug: Log signal_strength calculation
                                self.logger.debug(f"{symbol}: daily_signal={daily_signal:.2f}, weekly_signal={weekly_signal:.2f}, timeframe={timeframe_info}")
                                
                                # If key_indicators_list is still empty, add top indicators anyway (always show most important ones)
                                if len(key_indicators_list) == 0:
                                    # Add RSI if available (always important)
                                    if 'rsi' in indicators:
                                        rsi_val = indicators['rsi'].get('value', 50)
                                        rsi_signal = 'buy' if rsi_val < 50 else 'sell' if rsi_val > 50 else 'neutral'
                                        key_indicators_list.append({"name": "RSI", "value": rsi_val, "signal": rsi_signal, "weight": "high"})
                                    
                                    # Add MACD if available (always important)
                                    if 'macd' in indicators:
                                        macd_data = indicators['macd']
                                        macd_hist = macd_data.get('histogram', 0)
                                        macd_signal = 'buy' if macd_hist > 0 else 'sell' if macd_hist < 0 else 'neutral'
                                        key_indicators_list.append({"name": "MACD", "value": macd_hist, "signal": macd_signal, "weight": "very_high"})
                                    
                                    # Add Moving Averages if available
                                    if 'ma50' in indicators:
                                        ma50_data = indicators['ma50']
                                        ma50_signal = ma50_data.get('signal', 'neutral')
                                        ma50_val = ma50_data.get('value', 0)
                                        key_indicators_list.append({"name": "MA50", "value": ma50_val, "signal": ma50_signal, "weight": "medium"})
                                    
                                    # Add Bollinger Bands if available
                                    if 'bollinger_bands' in indicators:
                                        bb = indicators['bollinger_bands']
                                        bb_position = bb.get('position', 50)
                                        bb_signal = bb.get('signal', 'neutral')
                                        key_indicators_list.append({"name": "Bollinger", "value": bb_position, "signal": bb_signal, "weight": "high"})
                                    
                                    # Add Stochastic if available
                                    if 'stochastic' in indicators:
                                        stoch = indicators['stochastic']
                                        stoch_k = stoch.get('k', 50)
                                        stoch_signal = stoch.get('signal', 'neutral')
                                        key_indicators_list.append({"name": "Stochastic", "value": stoch_k, "signal": stoch_signal, "weight": "medium"})
                                
                                # Multi-factor confidence calculation
                                # 1. Base confidence from signal_strength (30% weight)
                                base_conf = abs(signal_strength) / 100.0
                                
                                # 2. Indicator consensus (40% weight)
                                if total_indicators > 0:
                                    consensus_conf = consensus_ratio
                                else:
                                    consensus_conf = 0.5
                                
                                # 3. Timeframe alignment (20% weight)
                                if same_direction:
                                    alignment_conf = 1.0
                                    else:
                                    alignment_conf = 0.5
                                
                                # 4. Volatility adjustment (10% weight) - proportional reduction
                                if volatility_pct > 5:
                                    volatility_factor = 0.6  # High volatility
                                elif volatility_pct > 3:
                                    volatility_factor = 0.8  # Medium volatility
                                else:
                                    volatility_factor = 1.0  # Low volatility
                                
                                # Combined confidence
                                confidence = (base_conf * 0.3 + consensus_conf * 0.4 + alignment_conf * 0.2) * volatility_factor
                                
                                # Bonus za timeframe alignment i kluczowe wzorce (dodatkowy boost)
                                if same_direction and abs_daily > 30 and abs_weekly > 30:
                                    confidence += 0.1
                                if has_golden_cross or has_inverse_h_and_s:
                                    confidence += 0.1
                                
                                # Guarantee minimum confidence for strong signals
                                abs_signal = abs(signal_strength)
                                if abs_signal > 70:
                                    confidence = max(0.70, confidence)  # Min 70% for signal>70
                                elif abs_signal > 50:
                                    confidence = max(0.50, confidence)  # Min 50% for signal>50
                                elif abs_signal > 30:
                                    confidence = max(0.30, confidence)  # Min 30% for signal>30
                                
                                # Clamp final confidence to reasonable range
                                confidence = min(0.95, max(0.05, confidence))
                                
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
                                        "timeframe": timeframe_info,
                                        "timeframe_analysis": {
                                            "daily_signal": round(daily_signal, 2),
                                            "weekly_signal": round(weekly_signal, 2) if weekly_signal != 0.0 else None,
                                            "alignment": "aligned" if same_direction else "diverging"
                                        }
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


    def predict_price(
        self,
        symbol: str,
        asset_type: str = "crypto",
        days_ahead: int = 7
    ) -> Optional[Dict]:
        """
        Predict future price using Prophet (if available) or fallback to mock predictions.
        
        Args:
            symbol: Asset symbol (e.g., 'BTC', 'AAPL')
            asset_type: 'crypto' or 'stock'
            days_ahead: Number of days to predict (7-90)
        
        Returns:
            Dictionary with predictions and confidence
        """
        if not symbol or days_ahead < 1 or days_ahead > 90:
            return None
        
        try:
            # Get historical data
            if not self.market_data_service:
                return self._mock_predict_price(symbol, asset_type, days_ahead)
            
            historical_data, interval = self.market_data_service.get_symbol_history_with_interval(
                symbol, days_ahead
            )
            
            if not historical_data or len(historical_data) < 50:
                self.logger.warning(f"Insufficient data for {symbol}, using mock predictions")
                return self._mock_predict_price(symbol, asset_type, days_ahead)
            
            # Use Prophet if available
            if PROPHET_AVAILABLE:
                try:
                    df = pd.DataFrame(historical_data)
                    df['ds'] = pd.to_datetime(df['timestamp'] if 'timestamp' in df.columns else df.index)
                    df['y'] = df['close'].values
                    
                    # Prepare Prophet dataframe
                    prophet_df = df[['ds', 'y']].copy()
                    
                    # Initialize and fit Prophet model
                    model = Prophet(
                        daily_seasonality=True,
                        weekly_seasonality=True,
                        yearly_seasonality=False,
                        changepoint_prior_scale=0.05
                    )
                    model.fit(prophet_df)
                    
                    # Make future predictions
                    future = model.make_future_dataframe(periods=days_ahead)
                    forecast = model.predict(future)
                    
                    # Extract predictions
                    predictions = []
                    current_price = df['close'].iloc[-1]
                    
                    for i in range(len(df), len(forecast)):
                        pred_row = forecast.iloc[i]
                        predicted_price = max(current_price * 0.01, min(pred_row['yhat'], current_price * 10))
                        upper_bound = max(predicted_price, min(pred_row['yhat_upper'], current_price * 10))
                        lower_bound = max(current_price * 0.01, pred_row['yhat_lower'])
                        
                        predictions.append({
                            'date': pred_row['ds'].isoformat(),
                            'predicted_price': float(predicted_price),
                            'upper_bound': float(upper_bound),
                            'lower_bound': float(lower_bound)
                        })
                    
                    # Calculate confidence based on prediction interval width
                    avg_interval_width = np.mean([p['upper_bound'] - p['lower_bound'] for p in predictions]) / current_price
                    confidence = max(0.5, min(0.95, 1.0 - (avg_interval_width / 2)))
                    
                    return {
                        'symbol': symbol,
                        'model_used': 'prophet',
                        'status': 'success',
                        'predictions': predictions,
                        'confidence': float(confidence),
                        'current_price': float(current_price)
                    }
                
                except Exception as e:
                    self.logger.warning(f"Prophet prediction failed for {symbol}: {e}, using mock")
                    return self._mock_predict_price(symbol, asset_type, days_ahead)
                                    else:
                return self._mock_predict_price(symbol, asset_type, days_ahead)
        
        except Exception as e:
            self.logger.error(f"Error in predict_price for {symbol}: {e}", exc_info=True)
            return self._mock_predict_price(symbol, asset_type, days_ahead)

    def _fetch_real_news(self, symbol: str, max_articles: int = 10) -> List[str]:
        """Fetch real news articles using NewsAPI"""
        headlines = []
        
        if not NEWSAPI_AVAILABLE or not hasattr(self, 'newsapi_client') or not self.newsapi_client:
            return self._get_mock_news_headlines(symbol)
        
        try:
            # Search for news about the symbol
            query = f"{symbol} cryptocurrency" if symbol in ['BTC', 'ETH', 'SOL'] else f"{symbol} stock"
            articles = self.newsapi_client.get_everything(
                q=query,
                language='en',
                sort_by='relevancy',
                page_size=max_articles
            )
            
            if articles and 'articles' in articles:
                for article in articles['articles']:
                    if article.get('title'):
                        headlines.append(article['title'])
            
            if not headlines:
                return self._get_mock_news_headlines(symbol)
            
            return headlines[:max_articles]
        
        except Exception as e:
            self.logger.warning(f"Error fetching news for {symbol}: {e}")
            return self._get_mock_news_headlines(symbol)

    def analyze_sentiment(
        self,
        symbol: str,
        asset_type: str = "crypto"
    ) -> Optional[Dict]:
        """
        Analyze sentiment from news articles using FinBERT (if available).
        
        Args:
            symbol: Asset symbol
            asset_type: 'crypto' or 'stock'
        
        Returns:
            Dictionary with sentiment analysis results
        """
        if not symbol:
            return None
        
        try:
            # Fetch news headlines
            headlines = self._fetch_real_news(symbol, max_articles=10)
            
            if not headlines:
                return {
                    'symbol': symbol,
                    'sentiment': 'neutral',
                    'score': 0.0,
                    'confidence': 0.5,
                    'model_used': 'fallback',
                    'status': 'no_data'
                }
            
            # Use FinBERT if available
            if TRANSFORMERS_AVAILABLE and self.sentiment_pipeline:
                try:
                    # Analyze sentiment for each headline
                    sentiments = []
                    scores = []
                    
                    for headline in headlines:
                        result = self.sentiment_pipeline(headline)
                        if isinstance(result, list) and len(result) > 0:
                            result = result[0]
                        
                        label = result.get('label', 'neutral')
                        score = result.get('score', 0.5)
                        
                        # Map FinBERT labels to our sentiment scale
                        if 'positive' in label.lower():
                            sentiments.append('positive')
                            scores.append(score)
                        elif 'negative' in label.lower():
                            sentiments.append('negative')
                            scores.append(-score)
                                        else:
                            sentiments.append('neutral')
                            scores.append(0.0)
                    
                    # Aggregate sentiment
                    if scores:
                        avg_score = np.mean(scores)
                        positive_count = sum(1 for s in sentiments if s == 'positive')
                        negative_count = sum(1 for s in sentiments if s == 'negative')
                        
                        if avg_score > 0.1:
                            sentiment = 'positive'
                        elif avg_score < -0.1:
                            sentiment = 'negative'
                                else:
                            sentiment = 'neutral'
                        
                        confidence = min(0.95, abs(avg_score) * 2 + 0.5)
                        
                        return {
                            'symbol': symbol,
                            'sentiment': sentiment,
                            'score': float(avg_score),
                            'confidence': float(confidence),
                            'model_used': 'finbert',
                            'status': 'success',
                            'positive_articles': positive_count,
                            'negative_articles': negative_count,
                            'total_articles': len(headlines)
                        }
                    else:
                        return {
                            'symbol': symbol,
                            'sentiment': 'neutral',
                            'score': 0.0,
                            'confidence': 0.5,
                            'model_used': 'fallback',
                            'status': 'no_results'
                                }
                                
                            except Exception as e:
                    self.logger.warning(f"FinBERT sentiment analysis failed for {symbol}: {e}")
                    return {
                        'symbol': symbol,
                        'sentiment': 'neutral',
                        'score': 0.0,
                        'confidence': 0.5,
                        'model_used': 'fallback',
                        'status': 'error'
                    }
            else:
                # Fallback: simple keyword-based sentiment
                positive_keywords = ['up', 'rise', 'gain', 'bullish', 'surge', 'rally', 'soar', 'climb']
                negative_keywords = ['down', 'fall', 'drop', 'bearish', 'plunge', 'crash', 'decline', 'slide']
                
                positive_count = sum(1 for h in headlines if any(kw in h.lower() for kw in positive_keywords))
                negative_count = sum(1 for h in headlines if any(kw in h.lower() for kw in negative_keywords))
                
                if positive_count > negative_count:
                    sentiment = 'positive'
                    score = 0.3
                elif negative_count > positive_count:
                    sentiment = 'negative'
                    score = -0.3
                else:
                    sentiment = 'neutral'
                    score = 0.0
                
                return {
                    'symbol': symbol,
                    'sentiment': sentiment,
                    'score': score,
                    'confidence': 0.6,
                    'model_used': 'keyword_based',
                    'status': 'success',
                    'positive_articles': positive_count,
                    'negative_articles': negative_count,
                    'total_articles': len(headlines)
                }
        
                        except Exception as e:
            self.logger.error(f"Error in analyze_sentiment for {symbol}: {e}", exc_info=True)
            return {
                'symbol': symbol,
                'sentiment': 'neutral',
                'score': 0.0,
                'confidence': 0.5,
                'model_used': 'fallback',
                'status': 'error',
                'error': str(e)
            }

    def detect_anomalies(
        self,
        portfolio_holdings: Dict[str, float],
        target_allocation: Dict[str, float] = None
    ) -> Optional[Dict]:
        """
        Detect anomalies in portfolio data using statistical methods.
        
        Args:
            portfolio_holdings: Current portfolio allocation {symbol: percentage}
            target_allocation: Optional target allocation for drift detection
        
        Returns:
            Dictionary with detected anomalies and their severity
        """
        if not portfolio_holdings:
            return {
                'anomalies': [],
                'total_anomalies': 0,
                'severity': 'none'
            }
        
        anomalies = []
        
        try:
            # 1. Price Z-score anomalies
            if self.market_data_service:
                for symbol in portfolio_holdings.keys():
                    if portfolio_holdings[symbol] <= 0:
                        continue
                    
                    try:
                        # Get historical data (30 days for anomaly detection)
                        asset_type = 'crypto' if symbol in ['BTC', 'ETH', 'SOL', 'USDT', 'USDC'] else 'stock'
                        historical_data, _ = self.market_data_service.get_symbol_history_with_interval(
                            symbol, 30
                        )
                        
                        if historical_data and len(historical_data) >= 30:
                            df = pd.DataFrame(historical_data)
                            if 'close' in df.columns:
                                prices = df['close'].values
                                current_price = prices[-1]
                                
                                # Calculate Z-score
                                mean_price = np.mean(prices)
                                std_price = np.std(prices)
                                
                                if std_price > 0:
                                    z_score = abs((current_price - mean_price) / std_price)
                                    
                                    if z_score > 3:
                                        anomalies.append({
                                            'type': 'price_zscore',
                                            'symbol': symbol,
                                            'severity': 'critical',
                                            'z_score': float(z_score),
                                            'message': f'{symbol} price is {z_score:.2f} standard deviations from mean'
                                        })
                                    elif z_score > 2:
                                        anomalies.append({
                                            'type': 'price_zscore',
                                            'symbol': symbol,
                                            'severity': 'warning',
                                            'z_score': float(z_score),
                                            'message': f'{symbol} price is {z_score:.2f} standard deviations from mean'
                                        })
                            
                            # Volume anomalies
                            if 'volume' in df.columns:
                                volumes = df['volume'].values
                                recent_volume = np.mean(volumes[-5:]) if len(volumes) >= 5 else volumes[-1]
                                avg_volume = np.mean(volumes[:-5]) if len(volumes) > 5 else np.mean(volumes)
                                
                                if avg_volume > 0:
                                    volume_ratio = recent_volume / avg_volume
                                    
                                    if volume_ratio > 3.0:
                                        anomalies.append({
                                            'type': 'volume_spike',
                                            'symbol': symbol,
                                            'severity': 'warning',
                                            'volume_ratio': float(volume_ratio),
                                            'message': f'{symbol} has {volume_ratio:.1f}x average volume spike'
                                        })
                                    elif volume_ratio < 0.3:
                                        anomalies.append({
                                            'type': 'volume_drop',
                                            'symbol': symbol,
                                            'severity': 'info',
                                            'volume_ratio': float(volume_ratio),
                                            'message': f'{symbol} has {volume_ratio:.1f}x average volume drop'
                                        })
                    
                    except Exception as e:
                        self.logger.debug(f"Error detecting anomalies for {symbol}: {e}")
            
            # 2. Allocation drift anomalies
            if target_allocation:
                total_current = sum(portfolio_holdings.values())
                total_target = sum(target_allocation.values())
                
                if total_current > 0 and total_target > 0:
                    for symbol in set(portfolio_holdings.keys()) | set(target_allocation.keys()):
                        current_pct = portfolio_holdings.get(symbol, 0.0) / total_current
                        target_pct = target_allocation.get(symbol, 0.0) / total_target
                        
                        drift = abs(current_pct - target_pct)
                        if drift > 0.15:  # 15% drift threshold
                            anomalies.append({
                                'type': 'allocation_drift',
                                'symbol': symbol,
                                'severity': 'warning' if drift > 0.25 else 'info',
                                'current_allocation': float(current_pct),
                                'target_allocation': float(target_pct),
                                'drift': float(drift),
                                'message': f'{symbol} allocation drift: {drift*100:.1f}%'
                            })
            
            # 3. Correlation break anomalies
            # This would require multiple symbols - simplified version
            if len(portfolio_holdings) >= 2 and self.market_data_service:
                symbols_list = list(portfolio_holdings.keys())[:5]  # Limit to 5 symbols
                try:
                    correlations = []
                    for i, sym1 in enumerate(symbols_list):
                        for sym2 in symbols_list[i+1:]:
                            try:
                                asset_type1 = 'crypto' if sym1 in ['BTC', 'ETH', 'SOL', 'USDT', 'USDC'] else 'stock'
                                asset_type2 = 'crypto' if sym2 in ['BTC', 'ETH', 'SOL', 'USDT', 'USDC'] else 'stock'
                                
                                data1, _ = self.market_data_service.get_symbol_history_with_interval(sym1, 30)
                                data2, _ = self.market_data_service.get_symbol_history_with_interval(sym2, 30)
                                
                                if data1 and data2 and len(data1) >= 30 and len(data2) >= 30:
                                    df1 = pd.DataFrame(data1)
                                    df2 = pd.DataFrame(data2)
                                    
                                    if 'close' in df1.columns and 'close' in df2.columns:
                                        min_len = min(len(df1), len(df2))
                                        returns1 = df1['close'].iloc[:min_len].pct_change().dropna()
                                        returns2 = df2['close'].iloc[:min_len].pct_change().dropna()
                                        
                                        if len(returns1) == len(returns2) and len(returns1) > 10:
                                            corr = np.corrcoef(returns1, returns2)[0, 1]
                                            if not np.isnan(corr):
                                                correlations.append({
                                                    'pair': f'{sym1}-{sym2}',
                                                    'correlation': float(corr)
                                                })
                            except Exception:
                                continue
                    
                    # Check for unexpected low correlations (would need historical baseline)
                    # Simplified: flag if correlation is unexpectedly low for crypto pairs
                    for corr_data in correlations:
                        if abs(corr_data['correlation']) < 0.3 and '-' in corr_data['pair']:
                            sym1, sym2 = corr_data['pair'].split('-')
                            if sym1 in ['BTC', 'ETH'] and sym2 in ['BTC', 'ETH']:
                                anomalies.append({
                                    'type': 'correlation_break',
                                    'symbols': [sym1, sym2],
                                    'severity': 'info',
                                    'correlation': corr_data['correlation'],
                                    'message': f'Low correlation between {sym1} and {sym2}: {corr_data["correlation"]:.2f}'
                                })
                
                except Exception as e:
                    self.logger.debug(f"Error detecting correlation anomalies: {e}")
            
            # Determine overall severity
            critical_count = sum(1 for a in anomalies if a.get('severity') == 'critical')
            warning_count = sum(1 for a in anomalies if a.get('severity') == 'warning')
            
            if critical_count > 0:
                overall_severity = 'critical'
            elif warning_count > 2:
                overall_severity = 'warning'
            elif len(anomalies) > 0:
                overall_severity = 'info'
                else:
                overall_severity = 'none'
            
            return {
                'anomalies': anomalies,
                'total_anomalies': len(anomalies),
                'severity': overall_severity,
                'critical_count': critical_count,
                'warning_count': warning_count
            }
        
        except Exception as e:
            self.logger.error(f"Error in detect_anomalies: {e}", exc_info=True)
        return {
                'anomalies': [],
                'total_anomalies': 0,
                'severity': 'error',
                'error': str(e)
            }

    def suggest_holdings_optimization(
        self,
        current_holdings: Dict[str, float],
        risk_tolerance: str = "moderate"
    ) -> Optional[Dict]:
        """
        Suggest optimal holdings allocation using Modern Portfolio Theory (MPT).
        
        Args:
            current_holdings: Current portfolio allocation {symbol: percentage}
            risk_tolerance: 'conservative', 'moderate', or 'aggressive'
            
        Returns:
            Dictionary with optimized allocation suggestions
        """
        if not current_holdings:
            return None
        
        try:
            symbols = list(current_holdings.keys())
            
            if not self.market_data_service:
                return {
                    'suggested_allocation': current_holdings,
                    'optimization_method': 'none',
                    'status': 'no_data_service'
                }
            
            # Get historical returns for all symbols
            returns_data = {}
            for symbol in symbols:
                try:
                    asset_type = 'crypto' if symbol in ['BTC', 'ETH', 'SOL', 'USDT', 'USDC'] else 'stock'
                    historical_data, _ = self.market_data_service.get_symbol_history_with_interval(
                        symbol, 90
                    )
                    
                    if historical_data and len(historical_data) >= 90:
                        df = pd.DataFrame(historical_data)
                        if 'close' in df.columns:
                            returns = df['close'].pct_change().dropna()
                            if len(returns) >= 30:
                                returns_data[symbol] = returns.values
                except Exception as e:
                self.logger.debug(f"Error getting returns for {symbol}: {e}")
            
            if len(returns_data) < 2:
                # Fallback: simple equal-weight or risk-based allocation
                num_assets = len(symbols)
                equal_weight = 1.0 / num_assets
                suggested_allocation = {symbol: equal_weight for symbol in symbols}
                
                return {
                    'suggested_allocation': suggested_allocation,
                    'optimization_method': 'equal_weight_fallback',
                    'status': 'insufficient_data',
                    'current_holdings': current_holdings,
                    'risk_tolerance': risk_tolerance
                }
            
            # Calculate expected returns and covariance matrix
            expected_returns = {}
            returns_list = []
            valid_symbols = []
            
            for symbol, returns in returns_data.items():
                expected_returns[symbol] = np.mean(returns) * 252  # Annualized
                returns_list.append(returns[:min(len(r) for r in returns_data.values())])
                valid_symbols.append(symbol)
            
            if len(returns_list) < 2:
            return {
                    'suggested_allocation': current_holdings,
                    'optimization_method': 'none',
                    'status': 'insufficient_data'
                }
            
            # Align returns to same length
            min_length = min(len(r) for r in returns_list)
            returns_matrix = np.array([r[:min_length] for r in returns_list])
            
            # Calculate covariance matrix (annualized)
            cov_matrix = np.cov(returns_matrix) * 252
            
            # Expected returns vector
            mu = np.array([expected_returns[symbol] for symbol in valid_symbols])
            
            # Risk tolerance weights
            risk_weights = {
                'conservative': 0.2,  # Lower risk, more stable assets
                'moderate': 0.5,
                'aggressive': 0.8  # Higher risk, more volatile assets
            }
            risk_weight = risk_weights.get(risk_tolerance, 0.5)
            
            # Simple optimization: maximize Sharpe-like ratio
            # For simplicity, use mean-variance optimization
            # Portfolio return = w^T * mu
            # Portfolio variance = w^T * Cov * w
            # We want to maximize (return - risk_penalty * variance)
            
            from scipy.optimize import minimize
            
            # Objective function: minimize negative Sharpe-like ratio
            def objective(weights):
                portfolio_return = np.dot(weights, mu)
                portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
                portfolio_std = np.sqrt(portfolio_variance)
                
                # Risk-adjusted return
                if portfolio_std > 0:
                    sharpe_like = portfolio_return / portfolio_std
            else:
                    sharpe_like = 0
                
                return -sharpe_like * (1 - risk_weight) + portfolio_variance * risk_weight
            
            # Constraints: weights sum to 1, each weight between 0 and 1
            constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}
            bounds = tuple((0, 1) for _ in range(len(valid_symbols)))
            
            # Initial guess: equal weights
            initial_weights = np.array([1.0 / len(valid_symbols)] * len(valid_symbols))
            
            try:
                result = minimize(objective, initial_weights, method='SLSQP',
                                bounds=bounds, constraints=constraints)
                
                if result.success:
                    optimized_weights = result.x
                    suggested_allocation = {
                        valid_symbols[i]: float(optimized_weights[i])
                        for i in range(len(valid_symbols))
                    }
                    
                    # Normalize to sum to 1
                    total = sum(suggested_allocation.values())
                    if total > 0:
                        suggested_allocation = {k: v / total for k, v in suggested_allocation.items()}
                    
                    # Calculate expected portfolio metrics
                    portfolio_return = np.dot(optimized_weights, mu)
                    portfolio_variance = np.dot(optimized_weights.T, np.dot(cov_matrix, optimized_weights))
                    portfolio_std = np.sqrt(portfolio_variance)
                    sharpe_ratio = portfolio_return / portfolio_std if portfolio_std > 0 else 0
                    
                    return {
                        'suggested_allocation': suggested_allocation,
                        'optimization_method': 'mpt_mean_variance',
                        'status': 'success',
                        'current_holdings': current_holdings,
                        'risk_tolerance': risk_tolerance,
                        'expected_return': float(portfolio_return),
                        'expected_volatility': float(portfolio_std),
                        'expected_sharpe_ratio': float(sharpe_ratio)
                    }
                else:
                    # Fallback to equal weights
                    equal_weight = 1.0 / len(valid_symbols)
                    suggested_allocation = {symbol: equal_weight for symbol in valid_symbols}
                    
                    return {
                        'suggested_allocation': suggested_allocation,
                        'optimization_method': 'equal_weight_fallback',
                        'status': 'optimization_failed',
                        'current_holdings': current_holdings
                    }
            
            except ImportError:
                # scipy not available, use simple heuristic
                equal_weight = 1.0 / len(valid_symbols)
                suggested_allocation = {symbol: equal_weight for symbol in valid_symbols}
                
                return {
                    'suggested_allocation': suggested_allocation,
                    'optimization_method': 'equal_weight_fallback',
                    'status': 'scipy_unavailable',
                    'current_holdings': current_holdings
                }
        
        except Exception as e:
            self.logger.error(f"Error in suggest_holdings_optimization: {e}", exc_info=True)
        return {
                'suggested_allocation': current_holdings,
                'optimization_method': 'none',
                'status': 'error',
                'error': str(e)
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
                    # Use prediction_horizon > 60 to get weekly data
                    data, interval = self.market_data_service.get_symbol_history_with_interval(
                        symbol, 90  # Weekly data (prediction_horizon > 60 returns weekly)
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
