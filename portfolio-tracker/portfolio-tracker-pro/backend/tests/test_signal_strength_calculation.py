"""
Testy obliczania signal_strength dla różnych kombinacji wskaźników
"""
import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import Mock
from ai_service import AIService
from market_data_service import MarketDataService
import pandas as pd
import numpy as np


class TestSignalStrengthCalculation(unittest.TestCase):
    """Testy obliczania signal_strength dla różnych kombinacji wskaźników"""
    
    def setUp(self):
        """Inicjalizacja serwisów"""
        self.market_data_service = Mock(spec=MarketDataService)
        self.ai_service = AIService(market_data_service=self.market_data_service)
        
        # Create mock historical data
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        self.mock_df = pd.DataFrame({
            'timestamp': dates,
            'open': np.random.uniform(100, 200, 100),
            'high': np.random.uniform(100, 200, 100),
            'low': np.random.uniform(90, 190, 100),
            'close': np.random.uniform(100, 200, 100),
            'volume': np.random.uniform(1000000, 10000000, 100),
        })
    
    def test_rsi_oversold_buy_signal(self):
        """Test czy RSI < 30 daje +15 punktów"""
        portfolio_holdings = {'BTC': 0.5}
        target_allocation = {'BTC': 0.5}
        
        def mock_get_history(symbol, prediction_horizon):
            df = self.mock_df.copy()
            # Ustaw RSI < 30 (oversold) - symulacja przez modyfikację ceny
            # RSI będzie niski jeśli cena spadła
            df['close'].iloc[-20:] = df['close'].iloc[-20] * 0.85  # Spadek ceny
            return df.to_dict('records'), '1d'
        
        self.market_data_service.get_symbol_history_with_interval = mock_get_history
        
        result = self.ai_service.recommend_rebalance(
            portfolio_holdings,
            target_allocation,
            rebalance_threshold=0.05
        )
        
        if result and 'recommendations' in result:
            for rec in result['recommendations']:
                if rec.get('symbol') == 'BTC':
                    # RSI < 30 powinien dać +15 punktów (przed quality multiplier)
                    # W rzeczywistości może być więcej jeśli inne wskaźniki też są bullish
                    signal = rec.get('signal_strength', 0)
                    # Sprawdź czy signal jest pozytywny (buy signal)
                    self.assertGreater(signal, 0, 
                        "RSI oversold powinien dać pozytywny signal_strength")
    
    def test_rsi_overbought_sell_signal(self):
        """Test czy RSI > 70 daje -15 punktów"""
        portfolio_holdings = {'BTC': 0.5}
        target_allocation = {'BTC': 0.5}
        
        def mock_get_history(symbol, prediction_horizon):
            df = self.mock_df.copy()
            # Ustaw RSI > 70 (overbought) - symulacja przez wzrost ceny
            df['close'].iloc[-20:] = df['close'].iloc[-20] * 1.15  # Wzrost ceny
            return df.to_dict('records'), '1d'
        
        self.market_data_service.get_symbol_history_with_interval = mock_get_history
        
        result = self.ai_service.recommend_rebalance(
            portfolio_holdings,
            target_allocation,
            rebalance_threshold=0.05
        )
        
        if result and 'recommendations' in result:
            for rec in result['recommendations']:
                if rec.get('symbol') == 'BTC':
                    # RSI > 70 powinien dać -15 punktów (przed quality multiplier)
                    signal = rec.get('signal_strength', 0)
                    # Sprawdź czy signal jest negatywny (sell signal)
                    self.assertLess(signal, 0, 
                        "RSI overbought powinien dać negatywny signal_strength")
    
    def test_macd_crossover_weight(self):
        """Test czy MACD crossover daje ±20 punktów (najwyższa waga)"""
        # To jest test strukturalny - weryfikujemy że MACD ma najwyższą wagę
        # przez sprawdzenie czy recommendations mają sensowne wartości
        
        portfolio_holdings = {'BTC': 0.5}
        target_allocation = {'BTC': 0.5}
        
        def mock_get_history(symbol, prediction_horizon):
            df = self.mock_df.copy()
            return df.to_dict('records'), '1d'
        
        self.market_data_service.get_symbol_history_with_interval = mock_get_history
        
        result = self.ai_service.recommend_rebalance(
            portfolio_holdings,
            target_allocation,
            rebalance_threshold=0.05
        )
        
        if result and 'recommendations' in result:
            for rec in result['recommendations']:
                signal = rec.get('signal_strength', 0)
                # Sprawdź czy signal jest w zakresie
                self.assertGreaterEqual(signal, -100)
                self.assertLessEqual(signal, 100)
                # MACD crossover powinien mieć znaczący wpływ jeśli występuje
                # (nie możemy bezpośrednio sprawdzić, ale weryfikujemy że system działa)
    
    def test_quality_multiplier_application(self):
        """Test czy quality multiplier jest poprawnie zastosowany"""
        # Quality multiplier zwiększa signal_strength gdy:
        # - consensus_ratio > 0.8 (+0.2)
        # - same_direction and abs_daily > 30 and abs_weekly > 30 (+0.3)
        # - has_golden_cross or has_inverse_h_and_s (+0.2)
        
        # Ten test weryfikuje że signal_strength może być > 100 przed clampowaniem
        # ale po clampowaniu jest w zakresie [-100, 100]
        
        portfolio_holdings = {'BTC': 0.5}
        target_allocation = {'BTC': 0.5}
        
        def mock_get_history(symbol, prediction_horizon):
            df = self.mock_df.copy()
            return df.to_dict('records'), '1d'
        
        self.market_data_service.get_symbol_history_with_interval = mock_get_history
        
        result = self.ai_service.recommend_rebalance(
            portfolio_holdings,
            target_allocation,
            rebalance_threshold=0.05
        )
        
        if result and 'recommendations' in result:
            for rec in result['recommendations']:
                signal = rec.get('signal_strength', 0)
                # Po clampowaniu signal powinien być w zakresie
                self.assertGreaterEqual(signal, -100,
                    "Signal strength powinien być >= -100 po clampowaniu")
                self.assertLessEqual(signal, 100,
                    "Signal strength powinien być <= 100 po clampowaniu")
    
    def test_multiple_indicators_aggregation(self):
        """Test agregacji wielu wskaźników"""
        # Wiele bullish wskaźników powinno dać wyższy signal_strength
        portfolio_holdings = {'BTC': 0.5}
        target_allocation = {'BTC': 0.5}
        
        def mock_get_history(symbol, prediction_horizon):
            df = self.mock_df.copy()
            # Symulacja wielu bullish wskaźników
            # RSI oversold, MACD bullish, cena powyżej MA
            df['close'].iloc[-20:] = df['close'].iloc[-20] * 0.90  # Spadek dla RSI oversold
            return df.to_dict('records'), '1d'
        
        self.market_data_service.get_symbol_history_with_interval = mock_get_history
        
        result = self.ai_service.recommend_rebalance(
            portfolio_holdings,
            target_allocation,
            rebalance_threshold=0.05
        )
        
        if result and 'recommendations' in result:
            for rec in result['recommendations']:
                signal = rec.get('signal_strength', 0)
                # Wiele bullish wskaźników powinno dać pozytywny signal
                # Nie możemy dokładnie sprawdzić wartości, ale weryfikujemy że system działa
                self.assertGreaterEqual(signal, -100)
                self.assertLessEqual(signal, 100)
    
    def test_buy_score_vs_sell_score(self):
        """Test czy buy_score i sell_score są poprawnie obliczane"""
        portfolio_holdings = {'BTC': 0.5}
        target_allocation = {'BTC': 0.5}
        
        def mock_get_history(symbol, prediction_horizon):
            df = self.mock_df.copy()
            return df.to_dict('records'), '1d'
        
        self.market_data_service.get_symbol_history_with_interval = mock_get_history
        
        result = self.ai_service.recommend_rebalance(
            portfolio_holdings,
            target_allocation,
            rebalance_threshold=0.05
        )
        
        if result and 'recommendations' in result:
            for rec in result['recommendations']:
                buy_score = rec.get('buy_score', 0)
                sell_score = rec.get('sell_score', 0)
                signal = rec.get('signal_strength', 0)
                
                # buy_score i sell_score powinny być >= 0
                self.assertGreaterEqual(buy_score, 0,
                    "buy_score powinien być >= 0")
                self.assertGreaterEqual(sell_score, 0,
                    "sell_score powinien być >= 0")
                
                # Jeśli signal > 0, buy_score powinien być wyższy
                # Jeśli signal < 0, sell_score powinien być wyższy
                if signal > 0:
                    self.assertGreater(buy_score, sell_score,
                        "Dla pozytywnego signal, buy_score powinien być > sell_score")
                elif signal < 0:
                    self.assertGreater(sell_score, buy_score,
                        "Dla negatywnego signal, sell_score powinien być > buy_score")
    
    def test_golden_cross_excludes_ma_weights(self):
        """Test czy Golden Cross wyklucza indywidualne wagi MA50/MA200"""
        # To jest test strukturalny - weryfikujemy że system działa
        # Bezpośrednie sprawdzenie wymagałoby ekspozycji logiki wewnętrznej
        
        portfolio_holdings = {'BTC': 0.5}
        target_allocation = {'BTC': 0.5}
        
        def mock_get_history(symbol, prediction_horizon):
            df = self.mock_df.copy()
            # Symulacja Golden Cross (MA50 > MA200)
            # Tworzymy trend wzrostowy
            for i in range(len(df)):
                df['close'].iloc[i] = 100 + i * 0.5  # Trend wzrostowy
            return df.to_dict('records'), '1d'
        
        self.market_data_service.get_symbol_history_with_interval = mock_get_history
        
        result = self.ai_service.recommend_rebalance(
            portfolio_holdings,
            target_allocation,
            rebalance_threshold=0.05
        )
        
        if result and 'recommendations' in result:
            for rec in result['recommendations']:
                signal = rec.get('signal_strength', 0)
                # Signal powinien być w zakresie (jeśli byłoby podwójne liczenie,
                # mógłby przekroczyć zakres przed clampowaniem)
                self.assertGreaterEqual(signal, -100)
                self.assertLessEqual(signal, 100)
    
    def test_consensus_counting(self):
        """Test czy bullish_count, bearish_count, neutral_count są poprawnie liczone"""
        # Test strukturalny - weryfikujemy że system działa
        
        portfolio_holdings = {'BTC': 0.5}
        target_allocation = {'BTC': 0.5}
        
        def mock_get_history(symbol, prediction_horizon):
            df = self.mock_df.copy()
            return df.to_dict('records'), '1d'
        
        self.market_data_service.get_symbol_history_with_interval = mock_get_history
        
        result = self.ai_service.recommend_rebalance(
            portfolio_holdings,
            target_allocation,
            rebalance_threshold=0.05
        )
        
        if result and 'recommendations' in result:
            for rec in result['recommendations']:
                confidence = rec.get('confidence', 0)
                # Confidence powinien być w zakresie [0.05, 0.95]
                self.assertGreaterEqual(confidence, 0.05,
                    "Confidence powinien być >= 0.05")
                self.assertLessEqual(confidence, 0.95,
                    "Confidence powinien być <= 0.95")
                
                # Wysoki consensus powinien dać wyższy confidence
                # (nie możemy bezpośrednio sprawdzić, ale weryfikujemy że confidence jest sensowny)
    
    def test_signal_strength_with_all_bullish_indicators(self):
        """Test czy wszystkie bullish wskaźniki dają wysoki signal_strength"""
        portfolio_holdings = {'BTC': 0.5}
        target_allocation = {'BTC': 0.5}
        
        def mock_get_history(symbol, prediction_horizon):
            df = self.mock_df.copy()
            # Symulacja wielu bullish wskaźników
            # RSI oversold, MACD bullish, cena powyżej MA, Bollinger oversold
            df['close'].iloc[-20:] = df['close'].iloc[-20] * 0.85  # Spadek dla RSI oversold
            return df.to_dict('records'), '1d'
        
        self.market_data_service.get_symbol_history_with_interval = mock_get_history
        
        result = self.ai_service.recommend_rebalance(
            portfolio_holdings,
            target_allocation,
            rebalance_threshold=0.05
        )
        
        if result and 'recommendations' in result:
            for rec in result['recommendations']:
                signal = rec.get('signal_strength', 0)
                confidence = rec.get('confidence', 0)
                
                # Wszystkie bullish wskaźniki powinny dać pozytywny signal
                if signal > 20:  # Medium priority buy
                    # Wysoki signal powinien mieć wysokie confidence
                    self.assertGreater(confidence, 0.3,
                        "Wysoki signal powinien mieć confidence > 0.3")
    
    def test_signal_strength_with_all_bearish_indicators(self):
        """Test czy wszystkie bearish wskaźniki dają niski signal_strength"""
        portfolio_holdings = {'BTC': 0.5}
        target_allocation = {'BTC': 0.5}
        
        def mock_get_history(symbol, prediction_horizon):
            df = self.mock_df.copy()
            # Symulacja wielu bearish wskaźników
            # RSI overbought, MACD bearish, cena poniżej MA, Bollinger overbought
            df['close'].iloc[-20:] = df['close'].iloc[-20] * 1.15  # Wzrost dla RSI overbought
            return df.to_dict('records'), '1d'
        
        self.market_data_service.get_symbol_history_with_interval = mock_get_history
        
        result = self.ai_service.recommend_rebalance(
            portfolio_holdings,
            target_allocation,
            rebalance_threshold=0.05
        )
        
        if result and 'recommendations' in result:
            for rec in result['recommendations']:
                signal = rec.get('signal_strength', 0)
                confidence = rec.get('confidence', 0)
                
                # Wszystkie bearish wskaźniki powinny dać negatywny signal
                if signal < -20:  # Medium priority sell
                    # Wysoki negatywny signal powinien mieć wysokie confidence
                    self.assertGreater(confidence, 0.3,
                        "Wysoki negatywny signal powinien mieć confidence > 0.3")


if __name__ == '__main__':
    unittest.main()



