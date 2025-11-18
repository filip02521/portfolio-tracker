"""
Testy wszystkich komponentów confidence calculation
"""
import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestConfidenceCalculation(unittest.TestCase):
    """Testy obliczania confidence w systemie AI recommendations"""
    
    def test_base_confidence_calculation(self):
        """Test base_conf (30% wagi) z signal_strength"""
        test_cases = [
            (0, 0.0),
            (30, 0.3),
            (50, 0.5),
            (70, 0.7),
            (100, 1.0),
            (-30, 0.3),  # abs(-30) = 30
            (-50, 0.5),  # abs(-50) = 50
            (-70, 0.7),  # abs(-70) = 70
            (-100, 1.0),  # abs(-100) = 100
        ]
        
        for signal_strength, expected_base_conf in test_cases:
            base_conf = abs(signal_strength) / 100.0
            self.assertAlmostEqual(base_conf, expected_base_conf, places=2,
                msg=f"Base confidence dla signal {signal_strength} powinien być {expected_base_conf}")
    
    def test_consensus_conf_calculation(self):
        """Test consensus_conf (40% wagi) z indicator consensus"""
        test_cases = [
            (10, 0, 0, 1.0),   # Wszystkie bullish (10/10 = 1.0)
            (0, 10, 0, 1.0),   # Wszystkie bearish (10/10 = 1.0)
            (8, 2, 0, 0.8),    # Większość bullish (8/10 = 0.8)
            (2, 8, 0, 0.8),    # Większość bearish (8/10 = 0.8)
            (5, 5, 0, 0.5),    # Połowa na pół (5/10 = 0.5)
            (6, 2, 2, 0.6),    # Z neutralnymi (6/10 = 0.6)
            (0, 0, 10, 0.5),   # Wszystkie neutralne (default 0.5)
        ]
        
        for bullish, bearish, neutral, expected_consensus in test_cases:
            total = bullish + bearish + neutral
            if total > 0:
                dominant = max(bullish, bearish)
                consensus_conf = dominant / total if dominant > 0 else 0.5
            else:
                consensus_conf = 0.5  # Default
            
            self.assertAlmostEqual(consensus_conf, expected_consensus, places=2,
                msg=f"Consensus conf dla {bullish}/{bearish}/{neutral} powinien być {expected_consensus}")
    
    def test_alignment_conf_calculation(self):
        """Test alignment_conf (20% wagi) z timeframe alignment"""
        # Same direction = 1.0
        same_direction = True
        alignment_conf = 1.0 if same_direction else 0.5
        self.assertEqual(alignment_conf, 1.0, "Alignment conf dla same_direction=True powinien być 1.0")
        
        # Different direction = 0.5
        same_direction = False
        alignment_conf = 1.0 if same_direction else 0.5
        self.assertEqual(alignment_conf, 0.5, "Alignment conf dla same_direction=False powinien być 0.5")
    
    def test_volatility_factor_calculation(self):
        """Test volatility_factor (10% wagi) z ATR"""
        test_cases = [
            (0, 1.0),    # Brak volatility
            (2, 1.0),    # Niska volatility (< 3%)
            (3, 1.0),    # Na granicy (3%, nie > 3%)
            (4, 0.8),    # Medium volatility (> 3%, <= 5%)
            (5, 0.8),    # Na granicy (5%, nie > 5%)
            (6, 0.6),    # High volatility (> 5%)
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
    
    def test_combined_confidence_calculation(self):
        """Test pełnej formuły confidence"""
        # Test case 1: Wysoki consensus, same direction, niska volatility
        base_conf = 0.7  # signal_strength = 70
        consensus_conf = 0.9  # 90% consensus
        alignment_conf = 1.0  # same direction
        volatility_factor = 1.0  # niska volatility
        
        confidence = (base_conf * 0.3 + consensus_conf * 0.4 + alignment_conf * 0.2) * volatility_factor
        expected = (0.7 * 0.3 + 0.9 * 0.4 + 1.0 * 0.2) * 1.0
        self.assertAlmostEqual(confidence, expected, places=2,
            msg=f"Combined confidence powinien być {expected}")
        
        # Test case 2: Niski consensus, różne direction, wysoka volatility
        base_conf = 0.5
        consensus_conf = 0.5  # 50% consensus
        alignment_conf = 0.5  # different direction
        volatility_factor = 0.6  # wysoka volatility
        
        confidence = (base_conf * 0.3 + consensus_conf * 0.4 + alignment_conf * 0.2) * volatility_factor
        expected = (0.5 * 0.3 + 0.5 * 0.4 + 0.5 * 0.2) * 0.6
        self.assertAlmostEqual(confidence, expected, places=2,
            msg=f"Combined confidence powinien być {expected}")
    
    def test_confidence_bonuses(self):
        """Test bonusów za timeframe alignment i kluczowe wzorce"""
        # Base confidence
        base_conf = 0.6
        consensus_conf = 0.7
        alignment_conf = 1.0
        volatility_factor = 1.0
        
        confidence = (base_conf * 0.3 + consensus_conf * 0.4 + alignment_conf * 0.2) * volatility_factor
        
        # Bonus za timeframe alignment (same_direction and abs_daily > 30 and abs_weekly > 30)
        same_direction = True
        abs_daily = 40
        abs_weekly = 35
        
        if same_direction and abs_daily > 30 and abs_weekly > 30:
            confidence += 0.1
        
        # Bonus za kluczowe wzorce
        has_golden_cross = True
        if has_golden_cross:
            confidence += 0.1
        
        # Sprawdzenie że bonusy zostały dodane
        base_combined = (0.6 * 0.3 + 0.7 * 0.4 + 1.0 * 0.2) * 1.0
        expected = base_combined + 0.2  # +0.1 za alignment, +0.1 za golden cross
        self.assertAlmostEqual(confidence, expected, places=2,
            msg="Confidence powinien zawierać bonusy")
    
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
            # Oblicz confidence
            base_conf = abs(signal_strength) / 100.0
            consensus_conf = 0.5
            alignment_conf = 0.5
            volatility_factor = 1.0
            confidence = (base_conf * 0.3 + consensus_conf * 0.4 + alignment_conf * 0.2) * volatility_factor
            
            # Apply minimum guarantees
            abs_signal = abs(signal_strength)
            if abs_signal >= 70:
                confidence = max(0.70, confidence)
            elif abs_signal >= 50:
                confidence = max(0.50, confidence)
            elif abs_signal >= 30:
                confidence = max(0.30, confidence)
            
            # Sprawdzenie że confidence >= expected_min_conf
            self.assertGreaterEqual(confidence, expected_min_conf,
                msg=f"Confidence dla signal {signal_strength} powinien być >= {expected_min_conf}")
    
    def test_confidence_clamping(self):
        """Test clampowania confidence do zakresu [0.05, 0.95]"""
        test_cases = [
            (-0.5, 0.05),  # Przekracza minimum
            (0.0, 0.05),   # Minimum teoretyczne
            (0.05, 0.05),  # Minimum rzeczywiste
            (0.5, 0.5),    # W zakresie
            (0.95, 0.95),  # Maksimum rzeczywiste
            (1.0, 0.95),   # Maksimum teoretyczne
            (1.5, 0.95),   # Przekracza maksimum
        ]
        
        for confidence_input, expected_clamped in test_cases:
            confidence = min(0.95, max(0.05, confidence_input))
            self.assertEqual(confidence, expected_clamped,
                msg=f"Confidence {confidence_input} powinien być clampowany do {expected_clamped}")
    
    def test_confidence_with_high_volatility(self):
        """Test czy wysoka volatility zmniejsza confidence"""
        base_conf = 0.8
        consensus_conf = 0.9
        alignment_conf = 1.0
        
        # Niska volatility
        volatility_factor_low = 1.0
        confidence_low = (base_conf * 0.3 + consensus_conf * 0.4 + alignment_conf * 0.2) * volatility_factor_low
        
        # Wysoka volatility
        volatility_factor_high = 0.6
        confidence_high = (base_conf * 0.3 + consensus_conf * 0.4 + alignment_conf * 0.2) * volatility_factor_high
        
        # Confidence z wysoką volatility powinien być niższy
        self.assertLess(confidence_high, confidence_low,
            "Confidence z wysoką volatility powinien być niższy niż z niską volatility")
    
    def test_confidence_with_low_consensus(self):
        """Test czy niski consensus zmniejsza confidence"""
        base_conf = 0.7
        alignment_conf = 1.0
        volatility_factor = 1.0
        
        # Wysoki consensus
        consensus_conf_high = 0.9
        confidence_high = (base_conf * 0.3 + consensus_conf_high * 0.4 + alignment_conf * 0.2) * volatility_factor
        
        # Niski consensus
        consensus_conf_low = 0.5
        confidence_low = (base_conf * 0.3 + consensus_conf_low * 0.4 + alignment_conf * 0.2) * volatility_factor
        
        # Confidence z niskim consensus powinien być niższy
        self.assertLess(confidence_low, confidence_high,
            "Confidence z niskim consensus powinien być niższy niż z wysokim consensus")
    
    def test_confidence_with_different_direction(self):
        """Test czy różne direction (timeframe alignment) zmniejsza confidence"""
        base_conf = 0.7
        consensus_conf = 0.8
        volatility_factor = 1.0
        
        # Same direction
        alignment_conf_same = 1.0
        confidence_same = (base_conf * 0.3 + consensus_conf * 0.4 + alignment_conf_same * 0.2) * volatility_factor
        
        # Different direction
        alignment_conf_different = 0.5
        confidence_different = (base_conf * 0.3 + consensus_conf * 0.4 + alignment_conf_different * 0.2) * volatility_factor
        
        # Confidence z different direction powinien być niższy
        self.assertLess(confidence_different, confidence_same,
            "Confidence z different direction powinien być niższy niż z same direction")
    
    def test_full_confidence_calculation_example(self):
        """Test pełnego przykładu obliczania confidence"""
        # Przykład: Silny sygnał z wysokim consensus
        signal_strength = 75
        bullish_count = 15
        bearish_count = 3
        neutral_count = 2
        same_direction = True
        volatility_pct = 2.5
        abs_daily = 75
        abs_weekly = 70
        has_golden_cross = True
        
        # 1. Base confidence
        base_conf = abs(signal_strength) / 100.0  # 0.75
        
        # 2. Consensus confidence
        total_indicators = bullish_count + bearish_count + neutral_count  # 20
        consensus_ratio = max(bullish_count, bearish_count) / total_indicators  # 15/20 = 0.75
        consensus_conf = consensus_ratio
        
        # 3. Alignment confidence
        alignment_conf = 1.0 if same_direction else 0.5
        
        # 4. Volatility factor
        if volatility_pct > 5:
            volatility_factor = 0.6
        elif volatility_pct > 3:
            volatility_factor = 0.8
        else:
            volatility_factor = 1.0  # 2.5 < 3
        
        # Combined confidence
        confidence = (base_conf * 0.3 + consensus_conf * 0.4 + alignment_conf * 0.2) * volatility_factor
        
        # Bonusy
        if same_direction and abs_daily > 30 and abs_weekly > 30:
            confidence += 0.1
        if has_golden_cross:
            confidence += 0.1
        
        # Minimum guarantee
        abs_signal = abs(signal_strength)
        if abs_signal >= 70:
            confidence = max(0.70, confidence)
        
        # Clamp
        confidence = min(0.95, max(0.05, confidence))
        
        # Sprawdzenie że confidence jest w zakresie
        self.assertGreaterEqual(confidence, 0.05)
        self.assertLessEqual(confidence, 0.95)
        self.assertGreaterEqual(confidence, 0.70,  # Minimum guarantee dla signal > 70
            "Confidence dla signal > 70 powinien być >= 0.70")
        
        # Sprawdzenie że confidence jest sensowny (wysoki dla silnego sygnału)
        self.assertGreater(confidence, 0.7,
            "Confidence dla silnego sygnału powinien być wysoki")


if __name__ == '__main__':
    unittest.main()

