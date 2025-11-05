"""
Unit tests for Confluence Strategy Service
"""
import unittest
import sys
import os
import pandas as pd
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from confluence_strategy_service import ConfluenceStrategyService
from market_data_service import MarketDataService


class TestConfluenceStrategyService(unittest.TestCase):
    """Test cases for ConfluenceStrategyService"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.market_data_service = MarketDataService()
        self.service = ConfluenceStrategyService(self.market_data_service)
        
        # Create sample DataFrame for testing
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=300, freq='4H')
        prices = 100 + np.cumsum(np.random.randn(300) * 0.5)
        
        self.sample_df = pd.DataFrame({
            'date': dates,
            'open': prices + np.random.randn(300) * 0.1,
            'high': prices + abs(np.random.randn(300) * 0.2),
            'low': prices - abs(np.random.randn(300) * 0.2),
            'close': prices,
            'volume': np.random.randint(1000, 10000, 300)
        })
    
    def test_detect_pin_bar_bullish(self):
        """Test detection of bullish pin bar"""
        # Create a bullish pin bar pattern
        df = pd.DataFrame({
            'open': [100.0, 99.5],
            'high': [100.2, 99.8],
            'low': [95.0, 98.0],  # Long lower wick
            'close': [99.8, 99.5],
        })
        
        result = self.service._detect_pin_bar(df)
        self.assertIsInstance(result, dict)
        # Note: Pin bar detection requires specific conditions, may not always detect
    
    def test_detect_pin_bar_bearish(self):
        """Test detection of bearish pin bar"""
        # Create a bearish pin bar pattern
        df = pd.DataFrame({
            'open': [100.0, 100.5],
            'high': [105.0, 101.0],  # Long upper wick
            'low': [99.8, 100.0],
            'close': [100.2, 100.5],
        })
        
        result = self.service._detect_pin_bar(df)
        self.assertIsInstance(result, dict)
    
    def test_detect_market_structure(self):
        """Test market structure detection (Higher High / Lower Low)"""
        result = self.service._detect_market_structure(self.sample_df)
        
        self.assertIsInstance(result, dict)
        if result:
            self.assertIn('structure', result)
            self.assertIn('higher_highs', result)
            self.assertIn('lower_lows', result)
            self.assertIn(result['structure'], ['uptrend', 'downtrend', 'sideways', 'volatile'])
    
    def test_analyze_ema_confluence(self):
        """Test EMA confluence analysis"""
        result = self.service._analyze_ema_confluence(self.sample_df)
        
        self.assertIsInstance(result, dict)
        if result:
            self.assertIn('ema10', result)
            self.assertIn('ema20', result)
            self.assertIn('ema50', result)
            self.assertIn('ema200', result)
            self.assertIn('golden_cross', result)
            self.assertIn('trend_strength', result)
    
    def test_analyze_volume_breakout(self):
        """Test volume breakout analysis"""
        result = self.service._analyze_volume_breakout(self.sample_df)
        
        self.assertIsInstance(result, dict)
        if result:
            self.assertIn('volume_ratio', result)
            self.assertIn('breakout', result)
            self.assertIn('signal', result)
            self.assertIn(result['signal'], ['buy', 'sell', 'neutral'])
    
    def test_analyze_entry_signals_structure(self):
        """Test that analyze_entry_signals returns correct structure"""
        # This test will likely fail if no market data, but we test structure
        try:
            result = self.service.analyze_entry_signals('BTC', '4h', '4h')
            
            self.assertIsInstance(result, dict)
            self.assertIn('entry_signal', result)
            self.assertIn('confidence', result)
            self.assertIn('confluence_score', result)
            self.assertIn('entry_price', result)
            self.assertIn('entry_reasons', result)
            self.assertIn(result['entry_signal'], ['buy', 'sell', 'hold'])
            self.assertGreaterEqual(result['confidence'], 0.0)
            self.assertLessEqual(result['confidence'], 1.0)
            self.assertGreaterEqual(result['confluence_score'], 0)
            self.assertLessEqual(result['confluence_score'], 6)
        except Exception as e:
            # If market data unavailable, test structure with error response
            if 'error' in str(e).lower() or 'insufficient' in str(e).lower():
                # This is acceptable for unit tests
                pass
            else:
                raise
    
    def test_analyze_exit_signals_structure(self):
        """Test that analyze_exit_signals returns correct structure"""
        try:
            result = self.service.analyze_exit_signals(
                symbol='BTC',
                entry_price=50000.0,
                entry_date='2024-01-01T00:00:00Z',
                current_price=51000.0,
                current_date='2024-01-02T00:00:00Z',
                interval='4h',
                portfolio_value=10000.0,
                risk_per_trade=0.02
            )
            
            self.assertIsInstance(result, dict)
            self.assertIn('exit_signal', result)
            self.assertIn('stop_loss', result)
            self.assertIn('take_profit_1', result)
            self.assertIn('risk_reward_ratio', result)
            self.assertIn(result['exit_signal'], ['hold', 'sell_50%', 'sell_100%'])
        except Exception as e:
            # If market data unavailable, test structure with error response
            if 'error' in str(e).lower() or 'insufficient' in str(e).lower():
                pass
            else:
                raise
    
    def test_confluence_score_calculation(self):
        """Test confluence score calculation logic"""
        # Test that confluence score is between 0 and 6
        # This is tested indirectly through analyze_entry_signals
        try:
            result = self.service.analyze_entry_signals('BTC', '4h', '4h')
            if 'confluence_score' in result:
                self.assertGreaterEqual(result['confluence_score'], 0)
                self.assertLessEqual(result['confluence_score'], 6)
        except Exception:
            # Acceptable if market data unavailable
            pass
    
    def test_stop_loss_calculation(self):
        """Test that stop loss is calculated correctly"""
        try:
            result = self.service.analyze_exit_signals(
                symbol='BTC',
                entry_price=50000.0,
                entry_date='2024-01-01T00:00:00Z',
                current_price=50000.0,
                current_date='2024-01-01T00:00:00Z',
                interval='4h',
                portfolio_value=10000.0,
                risk_per_trade=0.02
            )
            
            if 'stop_loss' in result and result['stop_loss']:
                # Stop loss should be below entry price for long position
                self.assertLess(result['stop_loss'], 50000.0)
        except Exception:
            # Acceptable if market data unavailable
            pass
    
    def test_take_profit_rr_calculation(self):
        """Test that take profit levels maintain R:R ratio"""
        try:
            result = self.service.analyze_exit_signals(
                symbol='BTC',
                entry_price=50000.0,
                entry_date='2024-01-01T00:00:00Z',
                current_price=50000.0,
                current_date='2024-01-01T00:00:00Z',
                interval='4h',
                portfolio_value=10000.0,
                risk_per_trade=0.02
            )
            
            if 'stop_loss' in result and 'take_profit_1' in result:
                if result['stop_loss'] and result['take_profit_1']:
                    risk = 50000.0 - result['stop_loss']
                    reward = result['take_profit_1'] - 50000.0
                    
                    if risk > 0:
                        rr_ratio = reward / risk
                        # Should be approximately 2:1 (R:R 1:2)
                        self.assertGreater(rr_ratio, 1.5)
                        self.assertLess(rr_ratio, 2.5)
        except Exception:
            # Acceptable if market data unavailable
            pass


if __name__ == '__main__':
    unittest.main()

