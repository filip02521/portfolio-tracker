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
                                    elif correlation_beta.get('underperforming'):
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
