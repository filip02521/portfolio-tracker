"""
Tests for BacktestEngine backtesting service
"""
import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from backtesting_service import BacktestEngine, StrategyType

class TestBacktestEngine:
    """Test suite for BacktestEngine"""
    
    @pytest.fixture
    def mock_market_data_service(self):
        """Create a mock market data service"""
        mock_service = Mock()
        # Mock historical data - 90 days of daily data
        base_date = datetime.now() - timedelta(days=90)
        mock_history = []
        for i in range(90, 0, -1):
            mock_history.append({
                'date': (base_date + timedelta(days=90-i)).isoformat(),
                'close': 50000.0 + (i * 50.0),  # Increasing trend
                'open': 49800.0 + (i * 50.0),
                'high': 50200.0 + (i * 50.0),
                'low': 49600.0 + (i * 50.0),
                'volume': 1000000.0
            })
        mock_service.get_symbol_history.return_value = mock_history
        return mock_service
    
    @pytest.fixture
    def backtest_engine(self, mock_market_data_service):
        """Create BacktestEngine instance with mocked dependencies"""
        return BacktestEngine(market_data_service=mock_market_data_service)
    
    def test_backtest_buy_and_hold_with_real_data(self, backtest_engine):
        """Test buy-and-hold strategy with real historical data"""
        result = backtest_engine._backtest_buy_and_hold(
            start_date=(datetime.now() - timedelta(days=30)).isoformat(),
            end_date=datetime.now().isoformat(),
            initial_capital=10000.0,
            asset_symbol='BTC',
            asset_type='crypto'
        )
        
        assert result is not None
        assert result['strategy'] == 'buy_and_hold'
        assert result['status'] == 'success'
        assert 'total_return' in result
        assert 'cagr' in result
        assert 'sharpe_ratio' in result
        assert 'max_drawdown' in result
        assert 'volatility' in result
        assert 'equity_curve' in result
        assert len(result['equity_curve']) > 0
    
    def test_backtest_buy_and_hold_insufficient_data(self, backtest_engine, mock_market_data_service):
        """Test buy-and-hold with insufficient historical data falls back to mock"""
        mock_market_data_service.get_symbol_history.return_value = []  # Empty data
        
        result = backtest_engine._backtest_buy_and_hold(
            start_date=(datetime.now() - timedelta(days=30)).isoformat(),
            end_date=datetime.now().isoformat(),
            initial_capital=10000.0,
            asset_symbol='BTC',
            asset_type='crypto'
        )
        
        assert result is not None
        assert result['status'] == 'fallback'
        assert result['total_return'] == 0.25  # Mock return
    
    def test_calculate_buy_hold_metrics(self, backtest_engine):
        """Test buy-and-hold metrics calculation"""
        # Create sample historical data
        base_date = datetime.now() - timedelta(days=10)
        history = [
            {
                'date': (base_date + timedelta(days=i)).isoformat(),
                'close': 50000.0 + (i * 100.0),  # Increasing trend
                'open': 49800.0,
                'high': 50200.0,
                'low': 49600.0,
                'volume': 1000000.0
            }
            for i in range(11)
        ]
        
        result = backtest_engine._calculate_buy_hold_metrics(
            history, 10000.0, 'BTC'
        )
        
        assert result is not None
        assert result['strategy'] == 'buy_and_hold'
        assert result['initial_capital'] == 10000.0
        assert result['final_value'] > 0
        assert result['total_return'] > 0  # Positive return due to increasing trend
        assert result['cagr'] > 0
        assert 'sharpe_ratio' in result
        assert 'max_drawdown' in result
        assert 'volatility' in result
        assert len(result['equity_curve']) == 11
    
    def test_calculate_buy_hold_metrics_single_point(self, backtest_engine):
        """Test metrics calculation with only one data point"""
        history = [
            {
                'date': datetime.now().isoformat(),
                'close': 50000.0,
                'open': 49800.0,
                'high': 50200.0,
                'low': 49600.0,
                'volume': 1000000.0
            }
        ]
        
        result = backtest_engine._calculate_buy_hold_metrics(
            history, 10000.0, 'BTC'
        )
        
        assert result is not None
        assert result['final_value'] == 10000.0  # No change with single point
        assert result['total_return'] == 0.0
        assert result['cagr'] == 0.0
        assert result['max_drawdown'] == 0.0
    
    def test_run_backtest_buy_and_hold(self, backtest_engine):
        """Test run_backtest dispatches to buy_and_hold correctly"""
        result = backtest_engine.run_backtest(
            strategy='buy_and_hold',
            start_date=(datetime.now() - timedelta(days=30)).isoformat(),
            end_date=datetime.now().isoformat(),
            initial_capital=10000.0,
            asset_symbol='BTC',
            asset_type='crypto'
        )
        
        assert result is not None
        assert result['strategy'] == 'buy_and_hold'
    
    def test_run_backtest_dca(self, backtest_engine):
        """Test run_backtest dispatches to DCA correctly"""
        result = backtest_engine.run_backtest(
            strategy='dca',
            start_date=(datetime.now() - timedelta(days=30)).isoformat(),
            end_date=datetime.now().isoformat(),
            initial_capital=10000.0,
            asset_symbol='BTC',
            asset_type='crypto',
            strategy_params={'frequency': 'weekly'}
        )
        
        assert result is not None
        assert result['strategy'] == 'dca'
        assert result['frequency'] == 'weekly'
    
    def test_run_backtest_momentum(self, backtest_engine):
        """Test run_backtest dispatches to momentum correctly"""
        result = backtest_engine.run_backtest(
            strategy='momentum',
            start_date=(datetime.now() - timedelta(days=30)).isoformat(),
            end_date=datetime.now().isoformat(),
            initial_capital=10000.0,
            asset_symbol='BTC',
            asset_type='crypto',
            strategy_params={'lookback_days': 20}
        )
        
        assert result is not None
        assert result['strategy'] == 'momentum'
    
    def test_run_backtest_mean_reversion(self, backtest_engine):
        """Test run_backtest dispatches to mean_reversion correctly"""
        result = backtest_engine.run_backtest(
            strategy='mean_reversion',
            start_date=(datetime.now() - timedelta(days=30)).isoformat(),
            end_date=datetime.now().isoformat(),
            initial_capital=10000.0,
            asset_symbol='BTC',
            asset_type='crypto',
            strategy_params={'period': 20}
        )
        
        assert result is not None
        assert result['strategy'] == 'mean_reversion'
    
    def test_run_backtest_unknown_strategy(self, backtest_engine):
        """Test run_backtest raises ValueError for unknown strategy"""
        with pytest.raises(ValueError):
            backtest_engine.run_backtest(
                strategy='unknown_strategy',
                start_date=(datetime.now() - timedelta(days=30)).isoformat(),
                end_date=datetime.now().isoformat(),
                initial_capital=10000.0,
                asset_symbol='BTC',
                asset_type='crypto'
            )
    
    def test_no_market_data_service(self):
        """Test backtest engine works without market data service"""
        engine = BacktestEngine(market_data_service=None)
        
        result = engine._backtest_buy_and_hold(
            start_date=(datetime.now() - timedelta(days=30)).isoformat(),
            end_date=datetime.now().isoformat(),
            initial_capital=10000.0,
            asset_symbol='BTC',
            asset_type='crypto'
        )
        
        assert result is not None
        assert result['status'] == 'fallback'
    
    def test_edge_case_empty_history(self, backtest_engine, mock_market_data_service):
        """Test handling of empty history"""
        mock_market_data_service.get_symbol_history.return_value = []
        
        result = backtest_engine._backtest_buy_and_hold(
            start_date='2024-01-01',
            end_date='2024-12-31',
            initial_capital=10000.0,
            asset_symbol='INVALID',
            asset_type='crypto'
        )
        
        assert result is not None
        assert result['status'] == 'fallback'
    
    def test_backtest_metrics_calculation(self, backtest_engine):
        """Test that backtest metrics are calculated correctly"""
        # Test equity curve with known values
        equity_curve = [10000, 10500, 11000, 10800, 11200, 11500, 11300, 12000]
        metrics = backtest_engine.calculate_metrics(equity_curve)
        
        assert 'total_return' in metrics
        assert 'cagr' in metrics
        assert 'volatility' in metrics
        assert 'sharpe_ratio' in metrics
        assert 'max_drawdown' in metrics
        
        # Total return should be positive (12000/10000 - 1 = 0.2 = 20%)
        assert metrics['total_return'] > 0
        assert metrics['max_drawdown'] >= 0  # Should be non-negative
    
    def test_backtest_metrics_edge_cases(self, backtest_engine):
        """Test backtest metrics with edge cases"""
        # Empty equity curve
        metrics_empty = backtest_engine.calculate_metrics([])
        assert metrics_empty['total_return'] == 0.0
        
        # Single value
        metrics_single = backtest_engine.calculate_metrics([10000])
        assert metrics_single['total_return'] == 0.0
        
        # Decreasing equity curve (loss)
        equity_loss = [10000, 9500, 9000, 8500]
        metrics_loss = backtest_engine.calculate_metrics(equity_loss)
        assert metrics_loss['total_return'] < 0
        assert metrics_loss['max_drawdown'] > 0
    
    def test_backtest_different_asset_types(self, backtest_engine):
        """Test backtesting with different asset types (crypto vs stocks)"""
        # Test crypto
        crypto_result = backtest_engine._backtest_buy_and_hold(
            start_date=(datetime.now() - timedelta(days=30)).isoformat(),
            end_date=datetime.now().isoformat(),
            initial_capital=10000.0,
            asset_symbol='BTC',
            asset_type='crypto'
        )
        
        # Test stock
        stock_result = backtest_engine._backtest_buy_and_hold(
            start_date=(datetime.now() - timedelta(days=30)).isoformat(),
            end_date=datetime.now().isoformat(),
            initial_capital=10000.0,
            asset_symbol='AAPL',
            asset_type='stock'
        )
        
        assert crypto_result is not None
        assert stock_result is not None
        assert 'total_return' in crypto_result
        assert 'total_return' in stock_result
    
    def test_backtest_very_short_period(self, backtest_engine):
        """Test backtesting with very short period (1 day)"""
        result = backtest_engine._backtest_buy_and_hold(
            start_date=(datetime.now() - timedelta(days=1)).isoformat(),
            end_date=datetime.now().isoformat(),
            initial_capital=10000.0,
            asset_symbol='BTC',
            asset_type='crypto'
        )
        
        assert result is not None
        # Should handle short periods gracefully
    
    def test_backtest_very_long_period(self, backtest_engine, mock_market_data_service):
        """Test backtesting with very long period (1 year)"""
        # Mock longer history
        base_date = datetime.now() - timedelta(days=365)
        long_history = []
        for i in range(365, 0, -1):
            long_history.append({
                'date': (base_date + timedelta(days=365-i)).isoformat(),
                'close': 50000.0 + (i * 10.0),
                'open': 49800.0 + (i * 10.0),
                'high': 50200.0 + (i * 10.0),
                'low': 49600.0 + (i * 10.0),
                'volume': 1000000.0
            })
        mock_market_data_service.get_symbol_history.return_value = long_history
        
        result = backtest_engine._backtest_buy_and_hold(
            start_date=(datetime.now() - timedelta(days=365)).isoformat(),
            end_date=datetime.now().isoformat(),
            initial_capital=10000.0,
            asset_symbol='BTC',
            asset_type='crypto'
        )
        
        assert result is not None
        assert 'total_return' in result




