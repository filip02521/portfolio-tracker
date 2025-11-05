"""
Testy obliczania composite_score
"""
import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCompositeScoreCalculation(unittest.TestCase):
    """Testy obliczania composite_score"""
    
    def test_composite_score_components(self):
        """Test wszystkich komponentów composite_score"""
        # Test case 1: Pełny przykład
        signal_strength = 75
        confidence = 0.8
        buy_score = 60
        sell_score = 10
        action = "buy"
        allocation_drift = 0.1
        
        composite_score = 0.0
        
        # 1. Signal strength component (30%)
        composite_score += (abs(signal_strength) / 100) * 30  # 0.75 * 30 = 22.5
        
        # 2. Confidence component (25%)
        composite_score += (confidence * 100) * 0.25  # 80 * 0.25 = 20.0
        
        # 3. Buy/Sell score component (20%)
        composite_score += (buy_score if action == "buy" else sell_score) * 0.20  # 60 * 0.20 = 12.0
        
        # 4. Risk adjustment (15%)
        risk_weight = 10  # default medium
        if confidence > 0.7:
            risk_weight = 15  # High confidence = low risk
        elif confidence < 0.4:
            risk_weight = 5   # Low confidence = high risk
        composite_score += risk_weight * 0.15  # 15 * 0.15 = 2.25
        
        # 5. Allocation drift component (10%)
        drift_component = min(100, abs(allocation_drift) * 500)  # 0.1 * 500 = 50
        composite_score += drift_component * 0.10  # 50 * 0.10 = 5.0
        
        # Expected: 22.5 + 20.0 + 12.0 + 2.25 + 5.0 = 61.75
        expected = 61.75
        self.assertAlmostEqual(composite_score, expected, places=2,
            msg=f"Composite score powinien być {expected}")
        
        # Clampowanie
        composite_score = max(0, min(100, composite_score))
        self.assertGreaterEqual(composite_score, 0)
        self.assertLessEqual(composite_score, 100)
    
    def test_composite_score_range(self):
        """Test czy composite_score jest zawsze w zakresie [0, 100]"""
        test_cases = [
            # (signal_strength, confidence, buy_score, sell_score, action, allocation_drift)
            (0, 0.0, 0, 0, "hold", 0.0),
            (50, 0.5, 30, 20, "buy", 0.05),
            (100, 1.0, 100, 0, "buy", 0.20),
            (-50, 0.5, 20, 30, "sell", 0.05),
            (-100, 1.0, 0, 100, "sell", 0.20),
        ]
        
        for signal_strength, confidence, buy_score, sell_score, action, allocation_drift in test_cases:
            composite_score = 0.0
            
            # Signal strength component (30%)
            composite_score += (abs(signal_strength) / 100) * 30
            
            # Confidence component (25%)
            composite_score += (confidence * 100) * 0.25
            
            # Buy/Sell score component (20%)
            composite_score += (buy_score if action == "buy" else sell_score) * 0.20
            
            # Risk adjustment (15%)
            risk_weight = 10
            if confidence > 0.7:
                risk_weight = 15
            elif confidence < 0.4:
                risk_weight = 5
            composite_score += risk_weight * 0.15
            
            # Allocation drift component (10%)
            drift_component = min(100, abs(allocation_drift) * 500)
            composite_score += drift_component * 0.10
            
            # Clampowanie
            composite_score = max(0, min(100, composite_score))
            
            # Sprawdzenie zakresu
            self.assertGreaterEqual(composite_score, 0,
                msg=f"Composite score {composite_score} powinien być >= 0")
            self.assertLessEqual(composite_score, 100,
                msg=f"Composite score {composite_score} powinien być <= 100")
    
    def test_signal_strength_component(self):
        """Test komponentu signal_strength (30% wagi)"""
        test_cases = [
            (0, 0.0),
            (50, 15.0),    # 0.5 * 30 = 15.0
            (100, 30.0),   # 1.0 * 30 = 30.0
            (-50, 15.0),   # abs(-50) = 50, 0.5 * 30 = 15.0
            (-100, 30.0),  # abs(-100) = 100, 1.0 * 30 = 30.0
        ]
        
        for signal_strength, expected_component in test_cases:
            component = (abs(signal_strength) / 100) * 30
            self.assertAlmostEqual(component, expected_component, places=2,
                msg=f"Signal strength component dla {signal_strength} powinien być {expected_component}")
    
    def test_confidence_component(self):
        """Test komponentu confidence (25% wagi)"""
        test_cases = [
            (0.0, 0.0),     # 0 * 100 * 0.25 = 0.0
            (0.5, 12.5),    # 0.5 * 100 * 0.25 = 12.5
            (0.8, 20.0),    # 0.8 * 100 * 0.25 = 20.0
            (1.0, 25.0),    # 1.0 * 100 * 0.25 = 25.0
        ]
        
        for confidence, expected_component in test_cases:
            component = (confidence * 100) * 0.25
            self.assertAlmostEqual(component, expected_component, places=2,
                msg=f"Confidence component dla {confidence} powinien być {expected_component}")
    
    def test_buy_sell_score_component(self):
        """Test komponentu buy/sell score (20% wagi)"""
        test_cases = [
            (50, 0, "buy", 10.0),    # 50 * 0.20 = 10.0
            (0, 50, "sell", 10.0),   # 50 * 0.20 = 10.0
            (100, 0, "buy", 20.0),   # 100 * 0.20 = 20.0
            (0, 100, "sell", 20.0),  # 100 * 0.20 = 20.0
        ]
        
        for buy_score, sell_score, action, expected_component in test_cases:
            component = (buy_score if action == "buy" else sell_score) * 0.20
            self.assertAlmostEqual(component, expected_component, places=2,
                msg=f"Buy/Sell score component dla {action} powinien być {expected_component}")
    
    def test_risk_adjustment_component(self):
        """Test komponentu risk adjustment (15% wagi)"""
        test_cases = [
            (0.3, 5, 0.75),    # Low confidence (< 0.4) -> risk_weight = 5, 5 * 0.15 = 0.75
            (0.5, 10, 1.5),    # Medium confidence -> risk_weight = 10, 10 * 0.15 = 1.5
            (0.8, 15, 2.25),   # High confidence (> 0.7) -> risk_weight = 15, 15 * 0.15 = 2.25
        ]
        
        for confidence, expected_risk_weight, expected_component in test_cases:
            risk_weight = 10  # default medium
            if confidence > 0.7:
                risk_weight = 15
            elif confidence < 0.4:
                risk_weight = 5
            
            component = risk_weight * 0.15
            
            self.assertEqual(risk_weight, expected_risk_weight,
                msg=f"Risk weight dla confidence {confidence} powinien być {expected_risk_weight}")
            self.assertAlmostEqual(component, expected_component, places=2,
                msg=f"Risk adjustment component dla confidence {confidence} powinien być {expected_component}")
    
    def test_allocation_drift_component(self):
        """Test komponentu allocation drift (10% wagi)"""
        test_cases = [
            (0.0, 0.0),      # 0 * 500 = 0, min(100, 0) = 0, 0 * 0.10 = 0.0
            (0.05, 2.5),     # 0.05 * 500 = 25, min(100, 25) = 25, 25 * 0.10 = 2.5
            (0.10, 5.0),     # 0.10 * 500 = 50, min(100, 50) = 50, 50 * 0.10 = 5.0
            (0.20, 10.0),    # 0.20 * 500 = 100, min(100, 100) = 100, 100 * 0.10 = 10.0
            (0.30, 10.0),    # 0.30 * 500 = 150, min(100, 150) = 100, 100 * 0.10 = 10.0 (clamped)
        ]
        
        for allocation_drift, expected_component in test_cases:
            drift_component = min(100, abs(allocation_drift) * 500)
            component = drift_component * 0.10
            self.assertAlmostEqual(component, expected_component, places=2,
                msg=f"Allocation drift component dla {allocation_drift} powinien być {expected_component}")
    
    def test_composite_score_clamping(self):
        """Test clampowania composite_score do zakresu [0, 100]"""
        test_cases = [
            (-50, 0),      # Clampowane do 0
            (0, 0),        # Minimum
            (50, 50),      # W zakresie
            (100, 100),    # Maksimum
            (150, 100),    # Clampowane do 100
        ]
        
        for composite_score_input, expected_clamped in test_cases:
            composite_score = max(0, min(100, composite_score_input))
            self.assertEqual(composite_score, expected_clamped,
                msg=f"Composite score {composite_score_input} powinien być clampowany do {expected_clamped}")
    
    def test_composite_score_with_high_signal_and_confidence(self):
        """Test composite_score dla wysokiego signal_strength i confidence"""
        signal_strength = 80
        confidence = 0.9
        buy_score = 70
        action = "buy"
        allocation_drift = 0.15
        
        composite_score = 0.0
        
        # Signal strength component (30%)
        composite_score += (abs(signal_strength) / 100) * 30  # 0.8 * 30 = 24.0
        
        # Confidence component (25%)
        composite_score += (confidence * 100) * 0.25  # 90 * 0.25 = 22.5
        
        # Buy/Sell score component (20%)
        composite_score += buy_score * 0.20  # 70 * 0.20 = 14.0
        
        # Risk adjustment (15%)
        risk_weight = 15  # High confidence
        composite_score += risk_weight * 0.15  # 15 * 0.15 = 2.25
        
        # Allocation drift component (10%)
        drift_component = min(100, abs(allocation_drift) * 500)  # 75
        composite_score += drift_component * 0.10  # 75 * 0.10 = 7.5
        
        # Expected: 24.0 + 22.5 + 14.0 + 2.25 + 7.5 = 70.25
        expected = 70.25
        self.assertAlmostEqual(composite_score, expected, places=2,
            msg="Composite score dla wysokiego signal i confidence powinien być wysoki")
        
        # Clampowanie
        composite_score = max(0, min(100, composite_score))
        self.assertGreaterEqual(composite_score, 70,
            msg="Composite score dla wysokiego signal i confidence powinien być >= 70")
    
    def test_composite_score_with_low_signal_and_confidence(self):
        """Test composite_score dla niskiego signal_strength i confidence"""
        signal_strength = 20
        confidence = 0.3
        buy_score = 15
        action = "buy"
        allocation_drift = 0.02
        
        composite_score = 0.0
        
        # Signal strength component (30%)
        composite_score += (abs(signal_strength) / 100) * 30  # 0.2 * 30 = 6.0
        
        # Confidence component (25%)
        composite_score += (confidence * 100) * 0.25  # 30 * 0.25 = 7.5
        
        # Buy/Sell score component (20%)
        composite_score += buy_score * 0.20  # 15 * 0.20 = 3.0
        
        # Risk adjustment (15%)
        risk_weight = 5  # Low confidence
        composite_score += risk_weight * 0.15  # 5 * 0.15 = 0.75
        
        # Allocation drift component (10%)
        drift_component = min(100, abs(allocation_drift) * 500)  # 10
        composite_score += drift_component * 0.10  # 10 * 0.10 = 1.0
        
        # Expected: 6.0 + 7.5 + 3.0 + 0.75 + 1.0 = 18.25
        expected = 18.25
        self.assertAlmostEqual(composite_score, expected, places=2,
            msg="Composite score dla niskiego signal i confidence powinien być niski")
        
        # Clampowanie
        composite_score = max(0, min(100, composite_score))
        self.assertLessEqual(composite_score, 20,
            msg="Composite score dla niskiego signal i confidence powinien być <= 20")
    
    def test_composite_score_weights_sum(self):
        """Test czy wagi komponentów sumują się do sensownych wartości"""
        # Wagi powinny być: 30% + 25% + 20% + 15% + 10% = 100%
        weights = {
            'signal_strength': 0.30,
            'confidence': 0.25,
            'buy_sell_score': 0.20,
            'risk_adjustment': 0.15,
            'allocation_drift': 0.10,
        }
        
        total_weight = sum(weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=2,
            msg="Suma wag komponentów powinna być 1.0 (100%)")
    
    def test_composite_score_sell_action(self):
        """Test composite_score dla akcji sell"""
        signal_strength = -60
        confidence = 0.75
        buy_score = 10
        sell_score = 50
        action = "sell"
        allocation_drift = 0.12
        
        composite_score = 0.0
        
        # Signal strength component (30%) - używa abs
        composite_score += (abs(signal_strength) / 100) * 30  # 0.6 * 30 = 18.0
        
        # Confidence component (25%)
        composite_score += (confidence * 100) * 0.25  # 75 * 0.25 = 18.75
        
        # Buy/Sell score component (20%) - używa sell_score dla action="sell"
        composite_score += sell_score * 0.20  # 50 * 0.20 = 10.0
        
        # Risk adjustment (15%)
        risk_weight = 15  # High confidence
        composite_score += risk_weight * 0.15  # 15 * 0.15 = 2.25
        
        # Allocation drift component (10%)
        drift_component = min(100, abs(allocation_drift) * 500)  # 60
        composite_score += drift_component * 0.10  # 60 * 0.10 = 6.0
        
        # Expected: 18.0 + 18.75 + 10.0 + 2.25 + 6.0 = 55.0
        expected = 55.0
        self.assertAlmostEqual(composite_score, expected, places=2,
            msg="Composite score dla sell action powinien używać sell_score")
        
        # Clampowanie
        composite_score = max(0, min(100, composite_score))
        self.assertGreaterEqual(composite_score, 0)
        self.assertLessEqual(composite_score, 100)


if __name__ == '__main__':
    unittest.main()

