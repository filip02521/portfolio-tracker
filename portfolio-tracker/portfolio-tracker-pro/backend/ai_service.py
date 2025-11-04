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

    # ==================== HELPER METHODS ====================
    
    def _safe_isna(self, value) -> bool:
        """Handle pandas Series/numpy arrays for NaN checks"""
        if pd.isna(value):
            return True
        if isinstance(value, (pd.Series, np.ndarray)):
            if len(value) == 0:
                return True
            return pd.isna(value.iloc[-1] if isinstance(value, pd.Series) else value[-1])
        return False
    
    def _safe_bool_extract(self, value, default: bool = False) -> bool:
        """Extract bool from Series or scalar"""
        if isinstance(value, pd.Series):
            if len(value) == 0:
                return default
            return bool(value.iloc[-1])
        if isinstance(value, np.ndarray):
            if len(value) == 0:
                return default
            return bool(value[-1])
        return bool(value) if value is not None else default
    
    def _normalize_indicator(self, series: pd.Series) -> pd.Series:
        """Min-max normalization to [0,1]"""
        if series.empty or series.min() == series.max():
            return pd.Series([0.5] * len(series), index=series.index)
        return (series - series.min()) / (series.max() - series.min())
    
    def _sanitize_for_json(self, obj):
        """Convert numpy/pandas types to native Python"""
        if isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, pd.Series):
            return obj.tolist()
        if isinstance(obj, pd.DataFrame):
            return obj.to_dict('records')
        if isinstance(obj, dict):
            return {k: self._sanitize_for_json(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._sanitize_for_json(item) for item in obj]
        return obj
    
    def _get_cache_key(self, symbol: str, timeframe: str, function_name: str) -> str:
        """Generate cache key"""
        return f"{symbol}_{timeframe}_{function_name}"
    
    def _mock_predict_price(self, symbol: str, asset_type: str, days_ahead: int) -> Dict:
        """Fallback mock predictions"""
        base_prices = {
            'BTC': 50000.0, 'ETH': 3000.0, 'SOL': 150.0,
            'AAPL': 175.0, 'GOOGL': 140.0, 'TSLA': 250.0
        }
        base_price = base_prices.get(symbol.upper(), 100.0)
        predictions = []
        for i in range(1, days_ahead + 1):
            change = np.random.normal(0, 0.02)
            predicted_price = base_price * (1 + change) ** i
            predictions.append({
                'date': (datetime.now() + timedelta(days=i)).isoformat(),
                'predicted_price': predicted_price,
                'upper_bound': predicted_price * 1.1,
                'lower_bound': predicted_price * 0.9
            })
        return {
            'symbol': symbol,
            'model_used': 'mock',
            'status': 'fallback',
            'predictions': predictions,
            'confidence': 0.5
        }

    # ==================== VOLUME PROFILE & PATTERN DETECTION ====================
    
    def _calculate_volume_profile(self, df: pd.DataFrame, num_levels: int = 20) -> Dict:
        """Calculate Volume Profile (POC, VAH, VAL)"""
        if df is None or len(df) < 20 or 'volume' not in df.columns or 'close' not in df.columns:
            return {}
        
        try:
            cache_key = f"vp_{len(df)}_{df['close'].iloc[-1]:.2f}"
            cached_result = self._get_from_cache(self._volume_profile_cache, cache_key)
            if cached_result is not None:
                return cached_result
            
            close = df['close'].values
            volume = df['volume'].values
            high = df['high'].values if 'high' in df.columns else close
            low = df['low'].values if 'low' in df.columns else close
            
            # Create price levels
            price_min = np.min(low)
            price_max = np.max(high)
            price_levels = np.linspace(price_min, price_max, num_levels)
            
            # Calculate volume at each price level
            volume_at_price = np.zeros(num_levels)
            for i in range(len(close)):
                price = close[i]
                vol = volume[i]
                # Find closest price level
                level_idx = np.argmin(np.abs(price_levels - price))
                volume_at_price[level_idx] += vol
            
            # Point of Control (POC) - price level with highest volume
            poc_idx = np.argmax(volume_at_price)
            poc_price = price_levels[poc_idx]
            
            # Value Area (70% of volume)
            total_volume = np.sum(volume_at_price)
            target_volume = total_volume * 0.70
            
            # Find VAH and VAL
            sorted_indices = np.argsort(volume_at_price)[::-1]
            cumulative_volume = 0
            included_levels = set()
            
            for idx in sorted_indices:
                if cumulative_volume >= target_volume:
                    break
                cumulative_volume += volume_at_price[idx]
                included_levels.add(idx)
            
            included_prices = [price_levels[i] for i in included_levels]
            vah_price = max(included_prices) if included_prices else poc_price
            val_price = min(included_prices) if included_prices else poc_price
            
            current_price = close[-1]
            current_position = None
            if current_price < val_price:
                current_position = 'below_val'
            elif current_price > vah_price:
                current_position = 'above_vah'
            elif val_price <= current_price <= poc_price:
                current_position = 'below_poc'
            else:
                current_position = 'above_poc'
            
            result = {
                'poc_price': float(poc_price),
                'vah_price': float(vah_price),
                'val_price': float(val_price),
                'current_price_position': current_position,
                'poc_volume': float(volume_at_price[poc_idx])
            }
            
            self._save_to_cache(self._volume_profile_cache, cache_key, result)
            return result
            
        except Exception as e:
            self.logger.error(f"Error calculating volume profile: {e}", exc_info=True)
            return {}
    
    def _detect_candlestick_patterns(self, df: pd.DataFrame) -> Dict:
        """Detect candlestick patterns (Doji, Hammer, Shooting Star, Engulfing)"""
        if df is None or len(df) < 5:
            return {}
        
        try:
            open_prices = df['open'].values if 'open' in df.columns else df['close'].values
            high = df['high'].values if 'high' in df.columns else df['close'].values
            low = df['low'].values if 'low' in df.columns else df['close'].values
            close = df['close'].values
            
            patterns = {}
            
            # Check last few candles
            for i in range(max(1, len(close) - 5), len(close)):
                body = abs(close[i] - open_prices[i])
                total_range = high[i] - low[i]
                upper_shadow = high[i] - max(close[i], open_prices[i])
                lower_shadow = min(close[i], open_prices[i]) - low[i]
                
                if total_range == 0:
                    continue
                
                body_ratio = body / total_range
                
                # Doji pattern
                if body_ratio < 0.1:
                    patterns[f'doji_{i}'] = {
                        'pattern': 'doji',
                        'index': i,
                        'signal': 'neutral',
                        'strength': 0.5
                    }
                
                # Hammer (bullish reversal)
                if lower_shadow > 2 * body and upper_shadow < 0.1 * total_range and close[i] > open_prices[i] * 0.99:
                    patterns[f'hammer_{i}'] = {
                        'pattern': 'hammer',
                        'index': i,
                        'signal': 'buy',
                        'strength': 0.7
                    }
                
                # Shooting Star (bearish reversal)
                if upper_shadow > 2 * body and lower_shadow < 0.1 * total_range and close[i] < open_prices[i] * 1.01:
                    patterns[f'shooting_star_{i}'] = {
                        'pattern': 'shooting_star',
                        'index': i,
                        'signal': 'sell',
                        'strength': 0.7
                    }
                
                # Engulfing patterns (need previous candle)
                if i > 0:
                    prev_body = abs(close[i-1] - open_prices[i-1])
                    # Bullish Engulfing
                    if (open_prices[i] < close[i-1] and close[i] > open_prices[i-1] and 
                        body > prev_body * 1.5):
                        patterns[f'bullish_engulfing_{i}'] = {
                            'pattern': 'bullish_engulfing',
                            'index': i,
                            'signal': 'buy',
                            'strength': 0.8
                        }
                    # Bearish Engulfing
                    elif (open_prices[i] > close[i-1] and close[i] < open_prices[i-1] and 
                          body > prev_body * 1.5):
                        patterns[f'bearish_engulfing_{i}'] = {
                            'pattern': 'bearish_engulfing',
                            'index': i,
                            'signal': 'sell',
                            'strength': 0.8
                        }
            
            # Return most recent pattern
            if patterns:
                latest_pattern = max(patterns.items(), key=lambda x: x[1]['index'])
                return {latest_pattern[0]: latest_pattern[1]}
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error detecting candlestick patterns: {e}", exc_info=True)
            return {}
    
    def _detect_chart_patterns(self, df: pd.DataFrame, timeframe: str = 'daily') -> Dict:
        """Detect chart patterns (Head & Shoulders, Triangles, Flags)"""
        if df is None or len(df) < 30:
            return {}
        
        try:
            cache_key = f"cp_{timeframe}_{len(df)}_{df['close'].iloc[-1]:.2f}"
            cached_result = self._get_from_cache(self._chart_patterns_cache, cache_key)
            if cached_result is not None:
                return cached_result
            
            high = df['high'].values if 'high' in df.columns else df['close'].values
            low = df['low'].values if 'low' in df.columns else df['close'].values
            close = df['close'].values
            
            patterns = {}
            
            # Find swing highs and lows
            swing_highs = []
            swing_lows = []
            for i in range(2, len(close) - 2):
                if high[i] > high[i-1] and high[i] > high[i-2] and high[i] > high[i+1] and high[i] > high[i+2]:
                    swing_highs.append((i, high[i]))
                if low[i] < low[i-1] and low[i] < low[i-2] and low[i] < low[i+1] and low[i] < low[i+2]:
                    swing_lows.append((i, low[i]))
            
            # Head & Shoulders (bearish reversal) - need 3 peaks
            if len(swing_highs) >= 3:
                recent_highs = swing_highs[-3:]
                if (recent_highs[0][1] < recent_highs[1][1] and 
                    recent_highs[2][1] < recent_highs[1][1] and
                    abs(recent_highs[0][1] - recent_highs[2][1]) / recent_highs[1][1] < 0.05):
                    weight = 20 if timeframe == 'monthly' else 15
                    patterns['head_shoulders'] = {
                        'pattern': 'head_shoulders',
                        'signal': 'sell',
                        'strength': 0.8,
                        'weight': weight
                    }
            
            # Inverse Head & Shoulders (bullish reversal)
            if len(swing_lows) >= 3:
                recent_lows = swing_lows[-3:]
                if (recent_lows[0][1] > recent_lows[1][1] and 
                    recent_lows[2][1] > recent_lows[1][1] and
                    abs(recent_lows[0][1] - recent_lows[2][1]) / recent_lows[1][1] < 0.05):
                    weight = 20 if timeframe == 'monthly' else 15
                    patterns['inverse_head_shoulders'] = {
                        'pattern': 'inverse_head_shoulders',
                        'signal': 'buy',
                        'strength': 0.8,
                        'weight': weight
                    }
            
            # Triangle patterns (need converging trend lines)
            if len(swing_highs) >= 3 and len(swing_lows) >= 3:
                # Check if highs are decreasing and lows are increasing (symmetrical)
                recent_highs_vals = [h[1] for h in swing_highs[-3:]]
                recent_lows_vals = [l[1] for l in swing_lows[-3:]]
                
                highs_decreasing = recent_highs_vals[0] > recent_highs_vals[-1]
                lows_increasing = recent_lows_vals[0] < recent_lows_vals[-1]
                
                if highs_decreasing and lows_increasing:
                    # Symmetrical triangle
                    patterns['symmetrical_triangle'] = {
                        'pattern': 'symmetrical_triangle',
                        'signal': 'neutral',
                        'strength': 0.6,
                        'weight': 5
                    }
                elif highs_decreasing and not lows_increasing:
                    # Descending triangle (bearish)
                    weight = 15 if timeframe == 'monthly' else 10
                    patterns['descending_triangle'] = {
                        'pattern': 'descending_triangle',
                        'signal': 'sell',
                        'strength': 0.7,
                        'weight': weight
                    }
                elif not highs_decreasing and lows_increasing:
                    # Ascending triangle (bullish)
                    weight = 15 if timeframe == 'monthly' else 10
                    patterns['ascending_triangle'] = {
                        'pattern': 'ascending_triangle',
                        'signal': 'buy',
                        'strength': 0.7,
                        'weight': weight
                    }
            
            # Flag patterns (continuation patterns)
            if len(close) >= 20:
                # Bull Flag: strong uptrend + consolidation
                recent_trend = (close[-1] - close[-20]) / close[-20]
                recent_volatility = np.std(close[-10:]) / close[-10]
                
                if recent_trend > 0.10 and recent_volatility < 0.05:
                    weight = 18 if timeframe == 'monthly' else 12
                    patterns['bull_flag'] = {
                        'pattern': 'bull_flag',
                        'signal': 'buy',
                        'strength': 0.75,
                        'weight': weight
                    }
                
                # Bear Flag: strong downtrend + consolidation
                if recent_trend < -0.10 and recent_volatility < 0.05:
                    weight = 18 if timeframe == 'monthly' else 12
                    patterns['bear_flag'] = {
                        'pattern': 'bear_flag',
                        'signal': 'sell',
                        'strength': 0.75,
                        'weight': weight
                    }
            
            self._save_to_cache(self._chart_patterns_cache, cache_key, patterns)
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error detecting chart patterns: {e}", exc_info=True)
            return {}
    
    def _detect_support_resistance(self, df: pd.DataFrame) -> Dict:
        """Detect support and resistance levels using swing highs/lows and Fibonacci"""
        if df is None or len(df) < 20:
            return {}
        
        try:
            high = df['high'].values if 'high' in df.columns else df['close'].values
            low = df['low'].values if 'low' in df.columns else df['close'].values
            close = df['close'].values
            
            # Find swing highs and lows
            swing_highs = []
            swing_lows = []
            for i in range(2, len(close) - 2):
                if high[i] > high[i-1] and high[i] > high[i-2] and high[i] > high[i+1] and high[i] > high[i+2]:
                    swing_highs.append(high[i])
                if low[i] < low[i-1] and low[i] < low[i-2] and low[i] < low[i+1] and low[i] < low[i+2]:
                    swing_lows.append(low[i])
            
            # Statistical support/resistance levels
            resistance_levels = sorted(set(swing_highs))[-3:] if swing_highs else []
            support_levels = sorted(set(swing_lows))[:3] if swing_lows else []
            
            current_price = close[-1]
            
            # Find nearest support and resistance
            nearest_resistance = min([r for r in resistance_levels if r > current_price], default=None)
            nearest_support = max([s for s in support_levels if s < current_price], default=None)
            
            # Calculate distance to nearest levels
            distance_to_resistance = ((nearest_resistance - current_price) / current_price * 100) if nearest_resistance else None
            distance_to_support = ((current_price - nearest_support) / current_price * 100) if nearest_support else None
            
            # Fibonacci Retracements (if we have recent high/low)
            fib_levels = {}
            if len(high) >= 50 and len(low) >= 50:
                recent_high = np.max(high[-50:])
                recent_low = np.min(low[-50:])
                fib_range = recent_high - recent_low
                
                fib_levels = {
                    'fib_23.6': recent_high - (fib_range * 0.236),
                    'fib_38.2': recent_high - (fib_range * 0.382),
                    'fib_50.0': recent_high - (fib_range * 0.500),
                    'fib_61.8': recent_high - (fib_range * 0.618)
                }
            
            # Determine if price is near support or resistance
            near_support = distance_to_support is not None and distance_to_support < 2.0
            near_resistance = distance_to_resistance is not None and distance_to_resistance < 2.0
            
            result = {
                'support_levels': [float(s) for s in support_levels],
                'resistance_levels': [float(r) for r in resistance_levels],
                'nearest_support': float(nearest_support) if nearest_support else None,
                'nearest_resistance': float(nearest_resistance) if nearest_resistance else None,
                'distance_to_support_pct': float(distance_to_support) if distance_to_support else None,
                'distance_to_resistance_pct': float(distance_to_resistance) if distance_to_resistance else None,
                'near_support': near_support,
                'near_resistance': near_resistance,
                'fibonacci_levels': {k: float(v) for k, v in fib_levels.items()} if fib_levels else {}
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error detecting support/resistance: {e}", exc_info=True)
            return {}
    
    def _calculate_correlation_and_beta(self, df: pd.DataFrame, symbol: str, benchmark_symbol: str = None) -> Dict:
        """Calculate correlation and beta relative to benchmark"""
        if df is None or len(df) < 30:
            return {}
        
        try:
            if not self.market_data_service:
                return {}
            
            # Get benchmark data if specified
            benchmark_df = None
            if benchmark_symbol:
                benchmark_data, _ = self.market_data_service.get_symbol_history_with_interval(
                    benchmark_symbol, 'crypto' if benchmark_symbol in ['BTC', 'ETH'] else 'stock', '1d'
                )
                if benchmark_data and len(benchmark_data) >= 30:
                    benchmark_df = pd.DataFrame(benchmark_data)
            
            # Calculate returns
            close = df['close'].values
            returns = pd.Series(close).pct_change().dropna()
            
            if benchmark_df is not None and 'close' in benchmark_df.columns:
                benchmark_close = benchmark_df['close'].values
                benchmark_returns = pd.Series(benchmark_close).pct_change().dropna()
                
                # Align series
                min_len = min(len(returns), len(benchmark_returns))
                if min_len >= 20:
                    returns_aligned = returns[-min_len:]
                    benchmark_aligned = benchmark_returns[-min_len:]
                    
                    # Correlation
                    correlation = returns_aligned.corr(benchmark_aligned)
                    
                    # Beta (covariance / variance of benchmark)
                    covariance = returns_aligned.cov(benchmark_aligned)
                    benchmark_variance = benchmark_aligned.var()
                    beta = covariance / benchmark_variance if benchmark_variance > 0 else 1.0
                    
                    # Relative strength
                    symbol_cumulative = (1 + returns_aligned).prod()
                    benchmark_cumulative = (1 + benchmark_aligned).prod()
                    relative_strength = symbol_cumulative / benchmark_cumulative if benchmark_cumulative > 0 else 1.0
                    
                    return {
                        'correlation': float(correlation) if not pd.isna(correlation) else 0.0,
                        'beta': float(beta) if not pd.isna(beta) else 1.0,
                        'relative_strength': float(relative_strength) if not pd.isna(relative_strength) else 1.0,
                        'outperforming': relative_strength > 1.1,
                        'underperforming': relative_strength < 0.9
                    }
            
            # If no benchmark, return volatility
            volatility = returns.std() * np.sqrt(252)  # Annualized
            return {
                'volatility': float(volatility) if not pd.isna(volatility) else 0.0,
                'correlation': None,
                'beta': None
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating correlation/beta: {e}", exc_info=True)
            return {}
