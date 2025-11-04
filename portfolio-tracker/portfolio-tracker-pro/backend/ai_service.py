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
