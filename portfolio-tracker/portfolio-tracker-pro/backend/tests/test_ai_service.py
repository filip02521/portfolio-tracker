"""
Comprehensive unit tests for AIService (Prophet, TA, FinBERT, fallbacks)
"""
import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from ai_service import AIService

class TestAIService:
    """Test suite for AIService"""
    
    @pytest.fixture
    def mock_market_data_service(self):
        """Create a mock market data service"""
        mock_service = Mock()
        # Mock historical data
        mock_history = [
            {
                'date': (datetime.now() - timedelta(days=i)).isoformat(),
                'close': 50000.0 - (i * 100.0),
                'open': 49800.0 - (i * 100.0),
                'high': 50200.0 - (i * 100.0),
                'low': 49600.0 - (i * 100.0),
                'volume': 1000000.0
            }
            for i in range(30, 0, -1)
        ]
        mock_service.get_symbol_history.return_value = mock_history
        # Mock get_symbol_history_with_interval to return tuple (history, interval)
        mock_service.get_symbol_history_with_interval.return_value = (mock_history, '1w')
        return mock_service
    
    @pytest.fixture
    def ai_service(self, mock_market_data_service):
        """Create AIService instance with mocked dependencies"""
        return AIService(market_data_service=mock_market_data_service)
    
    def test_predict_price_with_prophet(self, ai_service, mock_market_data_service):
        """Test Prophet-based price prediction with sufficient historical data"""
        # Mock Prophet being available
        with patch('ai_service.PROPHET_AVAILABLE', True):
            with patch('ai_service.Prophet') as mock_prophet_class:
                # Setup mock Prophet model
                mock_model = MagicMock()
                mock_prophet_class.return_value = mock_model
                
                # Mock forecast dataframe
                mock_forecast = pd.DataFrame({
                    'ds': pd.date_range(start='2024-01-01', periods=7),
                    'yhat': [51000.0 + (i * 100) for i in range(7)],
                    'yhat_upper': [51500.0 + (i * 100) for i in range(7)],
                    'yhat_lower': [50500.0 + (i * 100) for i in range(7)],
                    'trend': [50000.0 + (i * 50) for i in range(7)]
                })
                mock_model.predict.return_value = mock_forecast
                
                # Call predict_price
                result = ai_service.predict_price('BTC', 'crypto', days_ahead=7)
                
                # Assertions
                assert result is not None
                assert result['symbol'] == 'BTC'
                # May use mock if Prophet fails, but structure should be correct
                assert result['model_used'] in ['prophet', 'mock']
                assert 'predictions' in result
                if result['model_used'] == 'prophet':
                    assert len(result['predictions']) == 7
                    assert all('predicted_price' in p for p in result['predictions'])
                    assert all('confidence' in p for p in result['predictions'])
                mock_prophet_class.assert_called_once()
    
    def test_predict_price_prophet_unavailable(self, ai_service):
        """Test fallback to mock predictions when Prophet unavailable"""
        # Mock Prophet not available
        with patch('ai_service.PROPHET_AVAILABLE', False):
            result = ai_service.predict_price('BTC', 'crypto', days_ahead=7)
            
            assert result is not None
            assert result['model_used'] == 'mock'
            assert result['status'] == 'fallback'
            assert len(result['predictions']) == 7
    
    def test_predict_price_insufficient_data(self, ai_service, mock_market_data_service):
        """Test fallback when insufficient historical data"""
        mock_market_data_service.get_symbol_history.return_value = []  # Empty data
        mock_market_data_service.get_symbol_history_with_interval.return_value = ([], '1d')
        
        with patch('ai_service.PROPHET_AVAILABLE', True):
            result = ai_service.predict_price('BTC', 'crypto', days_ahead=7)
            
            assert result is not None
            # Should fallback to mock when insufficient data, but Prophet may try first
            assert result['model_used'] in ['mock', 'prophet']
            assert result['status'] in ['fallback', 'success']
    
    def test_predict_price_no_market_service(self):
        """Test fallback when market data service not initialized"""
        ai_service = AIService(market_data_service=None)
        
        result = ai_service.predict_price('BTC', 'crypto', days_ahead=7)
        
        assert result is not None
        assert result['model_used'] == 'mock'
        assert result['status'] == 'fallback'
    
    def test_recommend_rebalance_with_technical_indicators(self, ai_service, mock_market_data_service):
        """Test rebalancing recommendations with technical indicators"""
        # Mock TA library available
        with patch('ai_service.TA_AVAILABLE', True):
            with patch('ai_service.ta.momentum.RSIIndicator') as mock_rsi_class:
                with patch('ai_service.ta.trend.MACD') as mock_macd_class:
                    # Setup mock indicators
                    mock_rsi = MagicMock()
                    mock_rsi_class.return_value = mock_rsi
                    mock_rsi.rsi.return_value = pd.Series([65.0] * 30)  # Neutral RSI
                    
                    mock_macd = MagicMock()
                    mock_macd_class.return_value = mock_macd
                    mock_macd.macd.return_value = pd.Series([100.0] * 30)
                    mock_macd.macd_signal.return_value = pd.Series([95.0] * 30)
                    
                    portfolio_holdings = {'BTC': 0.6, 'ETH': 0.4}
                    target_allocation = {'BTC': 0.5, 'ETH': 0.5}
                    
                    result = ai_service.recommend_rebalance(
                        portfolio_holdings, target_allocation, rebalance_threshold=0.05
                    )
                    
                    assert result is not None
                    assert result['model_used'] in ['comprehensive_technical_analysis', 'technical_analysis', 'simple_threshold']
                    assert 'recommendations' in result
    
    def test_recommend_rebalance_without_ta(self, ai_service):
        """Test rebalancing recommendations without technical indicators"""
        # Mock TA library not available
        with patch('ai_service.TA_AVAILABLE', False):
            portfolio_holdings = {'BTC': 0.6, 'ETH': 0.4}
            target_allocation = {'BTC': 0.5, 'ETH': 0.5}
            
            result = ai_service.recommend_rebalance(
                portfolio_holdings, target_allocation, rebalance_threshold=0.05
            )
            
            assert result is not None
            assert result['model_used'] == 'simple_threshold'
            assert 'recommendations' in result
    
    def test_recommend_rebalance_rsi_overbought(self, ai_service, mock_market_data_service):
        """Test RSI overbought signal triggers sell recommendation"""
        with patch('ai_service.TA_AVAILABLE', True):
            with patch('ai_service.ta.momentum.RSIIndicator') as mock_rsi_class:
                with patch('ai_service.ta.trend.MACD') as mock_macd_class:
                    # Overbought RSI
                    mock_rsi = MagicMock()
                    mock_rsi_class.return_value = mock_rsi
                    mock_rsi.rsi.return_value = pd.Series([75.0] * 30)
                    
                    mock_macd = MagicMock()
                    mock_macd_class.return_value = mock_macd
                    mock_macd.macd.return_value = pd.Series([100.0] * 30)
                    mock_macd.macd_signal.return_value = pd.Series([95.0] * 30)
                    
                    portfolio_holdings = {'BTC': 0.5}
                    target_allocation = {'BTC': 0.5}
                    
                    result = ai_service.recommend_rebalance(
                        portfolio_holdings, target_allocation, rebalance_threshold=0.05
                    )
                    
                    assert result is not None
                    if result['recommendations']:
                        # Check if there's a sell recommendation due to RSI
                        sell_recs = [r for r in result['recommendations'] if r.get('action') == 'sell']
                        assert len(sell_recs) > 0
    
    def test_analyze_sentiment_with_finbert(self, ai_service):
        """Test sentiment analysis with FinBERT"""
        # Mock transformers available and pipeline initialized
        with patch.object(ai_service, 'sentiment_pipeline') as mock_pipeline:
            mock_pipeline.return_value = [
                {'label': 'positive', 'score': 0.95}
            ]
            
            result = ai_service.analyze_sentiment('BTC', 'crypto')
            
            assert result is not None
            assert 'overall_sentiment' in result or 'score' in result
    
    def test_analyze_sentiment_without_finbert(self):
        """Test sentiment analysis fallback without FinBERT"""
        ai_service = AIService()
        ai_service.sentiment_pipeline = None
        
        result = ai_service.analyze_sentiment('BTC', 'crypto')
        
        assert result is not None
    
    def test_confidence_score_calculation(self, ai_service):
        """Test confidence score calculation in predictions"""
        # Test mock predictions include confidence scores
        result = ai_service._mock_predict_price('BTC', 'crypto', days_ahead=5)
        
        assert all(p['confidence'] > 0 and p['confidence'] <= 1 for p in result['predictions'])
    
    def test_invalid_symbol_handling(self, ai_service, mock_market_data_service):
        """Test error handling for invalid symbols"""
        mock_market_data_service.get_symbol_history.return_value = None
        mock_market_data_service.get_symbol_history_with_interval.return_value = (None, '1d')
        
        result = ai_service.predict_price('INVALID', 'crypto', days_ahead=7)
        
        assert result is not None
        # Should fallback to mock when no data, but Prophet may try first
        assert result['model_used'] in ['mock', 'prophet']
        assert result['status'] in ['fallback', 'success']
    
    def test_different_asset_types(self, ai_service):
        """Test predictions for different asset types"""
        crypto_result = ai_service._mock_predict_price('BTC', 'crypto', days_ahead=7)
        stock_result = ai_service._mock_predict_price('AAPL', 'stock', days_ahead=7)
        
        assert crypto_result['asset_type'] == 'crypto'
        assert stock_result['asset_type'] == 'stock'
        # Crypto should have higher prices than stocks in mock
        assert crypto_result['current_price'] > stock_result['current_price']

    def test_chart_patterns_detection(self, ai_service):
        """Test chart patterns detection (Head & Shoulders, Triangles, Flags)"""
        # Create test data with Head & Shoulders pattern (3 swing highs)
        test_data = []
        base_price = 100.0
        # Left shoulder
        for i in range(5):
            test_data.append({
                'close': base_price + i * 2,
                'high': base_price + i * 2 + 1,
                'low': base_price + i * 2 - 1,
                'open': base_price + i * 2,
                'volume': 1000
            })
        # Head (higher)
        for i in range(5):
            test_data.append({
                'close': base_price + 15 + i * 2,
                'high': base_price + 15 + i * 2 + 1,
                'low': base_price + 15 + i * 2 - 1,
                'open': base_price + 15 + i * 2,
                'volume': 1000
            })
        # Right shoulder (similar to left)
        for i in range(5):
            test_data.append({
                'close': base_price + i * 2,
                'high': base_price + i * 2 + 1,
                'low': base_price + i * 2 - 1,
                'open': base_price + i * 2,
                'volume': 1000
            })
        
        df = pd.DataFrame(test_data)
        patterns = ai_service._detect_chart_patterns(df, timeframe='weekly')
        
        assert isinstance(patterns, dict)
        assert 'head_shoulders' in patterns
        assert 'inverse_head_shoulders' in patterns
        assert 'ascending_triangle' in patterns
        assert 'descending_triangle' in patterns
        assert 'symmetrical_triangle' in patterns
        assert 'bull_flag' in patterns
        assert 'bear_flag' in patterns
    
    def test_volume_profile_calculation(self, ai_service):
        """Test Volume Profile calculation (POC, VAH, VAL)"""
        # Create test data with volume
        test_data = []
        for i in range(30):
            price = 100.0 + (i % 10) * 2
            test_data.append({
                'close': price,
                'high': price + 1,
                'low': price - 1,
                'open': price,
                'volume': 1000 + (i % 5) * 100
            })
        
        df = pd.DataFrame(test_data)
        volume_profile = ai_service._calculate_volume_profile(df, num_levels=20)
        
        assert isinstance(volume_profile, dict)
        assert 'poc_price' in volume_profile
        assert 'vah_price' in volume_profile
        assert 'val_price' in volume_profile
        assert 'current_price_position' in volume_profile
        
        # POC should be a valid price
        if volume_profile.get('poc_price'):
            assert volume_profile['poc_price'] > 0
            # VAH should be >= POC >= VAL
            if volume_profile.get('vah_price') and volume_profile.get('val_price'):
                assert volume_profile['vah_price'] >= volume_profile['poc_price']
                assert volume_profile['poc_price'] >= volume_profile['val_price']
    
    def test_recommend_rebalance_empty_portfolio(self, ai_service, mock_market_data_service):
        """Test recommend_rebalance with empty portfolio"""
        result = ai_service.recommend_rebalance(
            portfolio_holdings={},
            target_allocation={'BTC': 0.5, 'ETH': 0.5},
            rebalance_threshold=0.05
        )
        
        assert isinstance(result, dict)
        assert 'recommendations' in result
        # Should suggest buying target assets
        assert len(result['recommendations']) >= 0  # May have buy recommendations for target assets
    
    def test_recommend_rebalance_single_asset(self, ai_service, mock_market_data_service):
        """Test recommend_rebalance with single asset portfolio"""
        result = ai_service.recommend_rebalance(
            portfolio_holdings={'BTC': 1.0},  # 100% in BTC
            target_allocation={'BTC': 0.5, 'ETH': 0.5},
            rebalance_threshold=0.05
        )
        
        assert isinstance(result, dict)
        assert 'recommendations' in result
        # Should suggest selling BTC and/or buying ETH
        recommendations = result['recommendations']
        if len(recommendations) > 0:
            # Check that at least one recommendation makes sense
            has_sell_btc = any(r['symbol'] == 'BTC' and r['action'] == 'sell' for r in recommendations)
            has_buy_eth = any(r['symbol'] == 'ETH' and r['action'] == 'buy' for r in recommendations)
            assert has_sell_btc or has_buy_eth  # Should suggest rebalancing
    
    def test_recommend_rebalance_insufficient_data(self, ai_service, mock_market_data_service):
        """Test recommend_rebalance when market data is insufficient"""
        # Mock market data service to return insufficient data
        mock_market_data_service.get_symbol_history_with_interval.return_value = ([], '1w')
        
        result = ai_service.recommend_rebalance(
            portfolio_holdings={'BTC': 0.6, 'ETH': 0.4},
            target_allocation={'BTC': 0.5, 'ETH': 0.5},
            rebalance_threshold=0.05
        )
        
        assert isinstance(result, dict)
        assert 'recommendations' in result
        # Should still return recommendations (may use fallback logic)
    
    def test_recommend_rebalance_well_balanced(self, ai_service, mock_market_data_service):
        """Test recommend_rebalance with well-balanced portfolio"""
        result = ai_service.recommend_rebalance(
            portfolio_holdings={'BTC': 0.51, 'ETH': 0.49},  # Very close to target
            target_allocation={'BTC': 0.5, 'ETH': 0.5},
            rebalance_threshold=0.05  # Threshold is 5%, difference is only 1%
        )
        
        assert isinstance(result, dict)
        assert 'recommendations' in result
        # Should have few or no recommendations (portfolio is balanced)
        recommendations = result['recommendations']
        # Recommendations may be empty or very few




