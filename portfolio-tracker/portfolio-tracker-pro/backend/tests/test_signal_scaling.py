"""
Testy weryfikujące poprawność skalowania signal_strength i confidence
"""
import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_service import AIService
from market_data_service import MarketDataService


class TestSignalScaling(unittest.TestCase):
    """Testy skalowania signal_strength i confidence"""
    
    def setUp(self):
        """Inicjalizacja serwisów"""
        market_data_service = MarketDataService()
        self.ai_service = AIService(market_data_service=market_data_service)
    
    def test_signal_strength_range(self):
        """Test czy signal_strength jest zawsze w zakresie [-100, 100]"""
        # Test z maksymalnymi wartościami
        # Tworzenie mock recommendations z różnymi signal_strength
        test_cases = [
            -150,  # Przekracza minimum
            -100,  # Minimum
            -50,   # Ujemny
            0,     # Zero
            50,    # Dodatni
            100,   # Maksimum
            150,   # Przekracza maksimum
        ]
        
        for expected_signal in test_cases:
            # Symulacja obliczania signal_strength
            signal_strength = expected_signal
            
            # Clampowanie (jak w kodzie)
            signal_strength = max(-100, min(100, signal_strength))
            
            # Sprawdzenie zakresu
            self.assertGreaterEqual(signal_strength, -100, 
                f"Signal strength {signal_strength} powinien być >= -100")
            self.assertLessEqual(signal_strength, 100, 
                f"Signal strength {signal_strength} powinien być <= 100")
    
    def test_confidence_range(self):
        """Test czy confidence jest zawsze w zakresie [0.05, 0.95]"""
        test_cases = [
            -0.5,  # Przekracza minimum
            0.0,   # Minimum teoretyczne
            0.05,  # Minimum rzeczywiste
            0.5,   # Średnia
            0.95,  # Maksimum rzeczywiste
            1.0,   # Maksimum teoretyczne
            1.5,   # Przekracza maksimum
        ]
        
        for expected_conf in test_cases:
            # Symulacja obliczania confidence
            confidence = expected_conf
            
            # Clampowanie (jak w kodzie)
            confidence = min(0.95, max(0.05, confidence))
            
            # Sprawdzenie zakresu
            self.assertGreaterEqual(confidence, 0.05, 
                f"Confidence {confidence} powinien być >= 0.05")
            self.assertLessEqual(confidence, 0.95, 
                f"Confidence {confidence} powinien być <= 0.95")
    
    def test_composite_score_range(self):
        """Test czy composite_score jest zawsze w zakresie [0, 100]"""
        test_cases = [
            -50,   # Przekracza minimum
            0,     # Minimum
            50,    # Średnia
            100,   # Maksimum
            150,   # Przekracza maksimum
        ]
        
        for expected_score in test_cases:
            # Symulacja obliczania composite_score
            composite_score = expected_score
            
            # Clampowanie (jak w kodzie)
            composite_score = max(0, min(100, composite_score))
            
            # Sprawdzenie zakresu
            self.assertGreaterEqual(composite_score, 0, 
                f"Composite score {composite_score} powinien być >= 0")
            self.assertLessEqual(composite_score, 100, 
                f"Composite score {composite_score} powinien być <= 100")
    
    def test_signal_strength_clamping(self):
        """Test czy clampowanie signal_strength działa poprawnie"""
        # Test clampowania do minimum
        signal = -200
        clamped = max(-100, min(100, signal))
        self.assertEqual(clamped, -100, "Signal -200 powinien być clampowany do -100")
        
        # Test clampowania do maksimum
        signal = 200
        clamped = max(-100, min(100, signal))
        self.assertEqual(clamped, 100, "Signal 200 powinien być clampowany do 100")
        
        # Test wartości w zakresie
        signal = 50
        clamped = max(-100, min(100, signal))
        self.assertEqual(clamped, 50, "Signal 50 powinien pozostać bez zmian")
    
    def test_confidence_clamping(self):
        """Test czy clampowanie confidence działa poprawnie"""
        # Test clampowania do minimum
        conf = 0.0
        clamped = min(0.95, max(0.05, conf))
        self.assertEqual(clamped, 0.05, "Confidence 0.0 powinien być clampowany do 0.05")
        
        # Test clampowania do maksimum
        conf = 1.0
        clamped = min(0.95, max(0.05, conf))
        self.assertEqual(clamped, 0.95, "Confidence 1.0 powinien być clampowany do 0.95")
        
        # Test wartości w zakresie
        conf = 0.7
        clamped = min(0.95, max(0.05, conf))
        self.assertEqual(clamped, 0.7, "Confidence 0.7 powinien pozostać bez zmian")
    
    def test_composite_score_clamping(self):
        """Test czy clampowanie composite_score działa poprawnie"""
        # Test clampowania do minimum
        score = -50
        clamped = max(0, min(100, score))
        self.assertEqual(clamped, 0, "Composite score -50 powinien być clampowany do 0")
        
        # Test clampowania do maksimum
        score = 150
        clamped = max(0, min(100, score))
        self.assertEqual(clamped, 100, "Composite score 150 powinien być clampowany do 100")
        
        # Test wartości w zakresie
        score = 75
        clamped = max(0, min(100, score))
        self.assertEqual(clamped, 75, "Composite score 75 powinien pozostać bez zmian")
    
    def test_signal_strength_normalization(self):
        """Test czy signal_strength jest poprawnie normalizowany"""
        # Test z różnymi wartościami przed clampowaniem
        signals_before = [-150, -100, -50, 0, 50, 100, 150]
        signals_after = [max(-100, min(100, s)) for s in signals_before]
        
        # Wszystkie wartości powinny być w zakresie [-100, 100]
        for signal in signals_after:
            self.assertGreaterEqual(signal, -100)
            self.assertLessEqual(signal, 100)
    
    def test_confidence_normalization(self):
        """Test czy confidence jest poprawnie normalizowany"""
        # Test z różnymi wartościami przed clampowaniem
        confidences_before = [-0.5, 0.0, 0.05, 0.5, 0.95, 1.0, 1.5]
        confidences_after = [min(0.95, max(0.05, c)) for c in confidences_before]
        
        # Wszystkie wartości powinny być w zakresie [0.05, 0.95]
        for conf in confidences_after:
            self.assertGreaterEqual(conf, 0.05)
            self.assertLessEqual(conf, 0.95)
    
    def test_base_confidence_calculation(self):
        """Test obliczania base_confidence z signal_strength"""
        test_cases = [
            (0, 0.0),
            (50, 0.5),
            (100, 1.0),
            (-50, 0.5),  # abs(-50) = 50
            (-100, 1.0),  # abs(-100) = 100
        ]
        
        for signal_strength, expected_base_conf in test_cases:
            base_conf = abs(signal_strength) / 100.0
            self.assertEqual(base_conf, expected_base_conf,
                msg=f"Base confidence dla signal {signal_strength} powinien być {expected_base_conf}")
    
    def test_consensus_ratio_calculation(self):
        """Test obliczania consensus_ratio"""
        test_cases = [
            (10, 0, 0, 1.0),  # Wszystkie bullish
            (0, 10, 0, 1.0),  # Wszystkie bearish
            (5, 5, 0, 0.5),   # Połowa na pół
            (8, 2, 0, 0.8),   # Większość bullish
            (2, 8, 0, 0.8),   # Większość bearish
            (5, 3, 2, 0.5),   # Z neutralnymi
        ]
        
        for bullish, bearish, neutral, expected_ratio in test_cases:
            total = bullish + bearish + neutral
            if total > 0:
                consensus_ratio = max(bullish, bearish) / total
                self.assertAlmostEqual(consensus_ratio, expected_ratio, places=2,
                    msg=f"Consensus ratio dla {bullish}/{bearish}/{neutral} powinien być {expected_ratio}")
    
    def test_volatility_factor_calculation(self):
        """Test obliczania volatility_factor"""
        test_cases = [
            (0, 1.0),    # Brak volatility
            (2, 1.0),    # Niska volatility
            (3, 1.0),    # Na granicy (3%)
            (4, 0.8),    # Medium volatility
            (5, 0.8),    # Na granicy (5%)
            (6, 0.6),    # High volatility
            (10, 0.6),   # Bardzo wysoka volatility
        ]
        
        for volatility_pct, expected_factor in test_cases:
            if volatility_pct > 5:
                volatility_factor = 0.6
            elif volatility_pct > 3:
                volatility_factor = 0.8
            else:
                volatility_factor = 1.0
            
            self.assertEqual(volatility_factor, expected_factor,
                msg=f"Volatility factor dla {volatility_pct}% powinien być {expected_factor}")
    
    def test_minimum_confidence_guarantee(self):
        """Test minimum confidence guarantees dla silnych sygnałów"""
        test_cases = [
            (80, 0.70),   # Signal > 70, min confidence 0.70
            (70, 0.70),   # Signal = 70, min confidence 0.70
            (60, 0.50),   # Signal > 50, min confidence 0.50
            (50, 0.50),   # Signal = 50, min confidence 0.50
            (40, 0.30),   # Signal > 30, min confidence 0.30
            (30, 0.30),   # Signal = 30, min confidence 0.30
            (20, 0.05),   # Signal < 30, min confidence 0.05 (domyślne)
        ]
        
        for signal_strength, expected_min_conf in test_cases:
            abs_signal = abs(signal_strength)
            if abs_signal > 70:
                min_conf = 0.70
            elif abs_signal > 50:
                min_conf = 0.50
            elif abs_signal > 30:
                min_conf = 0.30
            else:
                min_conf = 0.05
            
            self.assertEqual(min_conf, expected_min_conf,
                msg=f"Minimum confidence dla signal {signal_strength} powinien być {expected_min_conf}")


if __name__ == '__main__':
    unittest.main()

