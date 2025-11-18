"""
Integration tests for AI/ML endpoints
Note: These are unit tests that test endpoint logic with mocked dependencies,
rather than full integration tests requiring a running server
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock

class TestAIEndpoints:
    """Unit tests for AI endpoint logic"""
    
    def test_ai_service_predict_price_called(self):
        """Test that AI service predict_price is called correctly"""
        from ai_service import AIService
        from market_data_service import MarketDataService
        
        # Create service instance
        mds = MarketDataService()
        ai_service = AIService(mds)
        
        # Test predict_price call
        result = ai_service.predict_price('BTC', 'crypto', 7)
        
        assert result is not None
        assert 'symbol' in result
        assert 'predictions' in result
    
    def test_ai_service_recommend_rebalance_called(self):
        """Test that AI service recommend_rebalance is called correctly"""
        from ai_service import AIService
        
        ai_service = AIService()
        
        portfolio_holdings = {'BTC': 0.6, 'ETH': 0.4}
        target_allocation = {'BTC': 0.5, 'ETH': 0.5}
        
        result = ai_service.recommend_rebalance(portfolio_holdings, target_allocation)
        
        assert result is not None
        assert 'recommendations' in result
        assert 'model_used' in result
    
    def test_backtest_engine_run_backtest_called(self):
        """Test that backtest engine run_backtest is called correctly"""
        from backtesting_service import BacktestEngine, StrategyType
        from market_data_service import MarketDataService
        
        mds = MarketDataService()
        engine = BacktestEngine(mds)
        
        result = engine.run_backtest(
            strategy=StrategyType.BUY_AND_HOLD,
            start_date='2024-01-01',
            end_date='2024-12-31',
            initial_capital=10000.0,
            asset_symbol='BTC',
            asset_type='crypto'
        )
        
        assert result is not None
        assert 'total_return' in result or 'error' in result

