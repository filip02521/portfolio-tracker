#!/usr/bin/env python3
"""
Unit tests for fundamental screening compliance with expert report
"""
import unittest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fundamental_screening_service import FundamentalScreeningService


class TestFundamentalScreeningCompliance(unittest.TestCase):
    """Test compliance with expert report requirements"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.service = FundamentalScreeningService(market_data_service=None)
        
        # Sample financial data with all required fields
        self.sample_data = {
            'symbol': 'TEST',
            'company_name': 'Test Corp',
            'market_cap': 1000000000,  # $1B
            'total_assets': 2000000000,  # $2B
            'total_liabilities': 800000000,  # $800M
            'net_income': 100000000,  # $100M
            'operating_cash_flow': 150000000,  # $150M
            'revenue': 1000000000,  # $1B
            'ebit': 120000000,  # $120M
            'current_assets': 500000000,  # $500M
            'current_liabilities': 300000000,  # $300M
            'long_term_debt': 500000000,  # $500M
            'book_value': 1200000000,  # $1.2B
            'shares_outstanding': 100000000,
            'cogs': 600000000,  # $600M (60% of revenue)
            'gross_profit': 400000000,  # $400M (Revenue - COGS)
            'retained_earnings': 800000000,  # $800M
            'cash_and_cash_equivalents': 200000000,  # $200M
            'total_stockholders_equity': 1200000000,  # $1.2B
            'source': 'test'
        }
        
        # Previous year data (worse performance for comparison)
        self.previous_year_data = {
            'total_assets': 1900000000,  # $1.9B (slightly lower)
            'total_liabilities': 850000000,  # $850M (higher)
            'net_income': 80000000,  # $80M (lower)
            'operating_cash_flow': 120000000,  # $120M (lower)
            'revenue': 900000000,  # $900M (lower)
            'ebit': 100000000,  # $100M (lower)
            'current_assets': 450000000,  # $450M (lower)
            'current_liabilities': 320000000,  # $320M (higher)
            'long_term_debt': 530000000,  # $530M (higher)
            'shares_outstanding': 105000000,  # Higher (new equity issued)
            'cogs': 540000000,  # $540M (60% of $900M revenue)
            'gross_profit': 360000000,  # $360M
        }
    
    def test_f_score_gross_margin_true_calculation(self):
        """Test that F-Score uses true Gross Margin (Revenue - COGS) instead of EBIT/Revenue"""
        result = self.service.calculate_piotroski_f_score(
            'TEST',
            current_data=self.sample_data,
            previous_data=self.previous_year_data
        )
        
        # Check that gross margin calculation is correct
        # Current: $400M gross profit / $1B revenue = 40%
        # Previous: $360M gross profit / $900M revenue = 40%
        # Since they're equal, we should not get a point for increasing gross margin
        # But if current > previous, we should get the point
        
        # Modify to ensure increase
        self.sample_data['gross_profit'] = 420000000  # 42% margin
        result = self.service.calculate_piotroski_f_score(
            'TEST',
            current_data=self.sample_data,
            previous_data=self.previous_year_data
        )
        
        # Should have point for increasing gross margin
        self.assertIn('increasing_gross_margin', result['breakdown'])
        # Verify it's using true gross margin, not EBIT/Revenue
        details_str = ' '.join(result['details'])
        self.assertIn('Gross Margin', details_str)
    
    def test_z_score_retained_earnings_true(self):
        """Test that Z-Score uses true Retained Earnings from balance sheet"""
        result = self.service.calculate_altman_z_score('TEST', financial_data=self.sample_data)
        
        # Z-Score component B should use retained_earnings, not net_income
        # B = Retained Earnings / Total Assets
        # B = $800M / $2B = 0.4
        expected_B = 800000000 / 2000000000
        actual_B = result['components']['B']
        
        # Should be close to 0.4 (allowing for rounding)
        self.assertAlmostEqual(actual_B, expected_B, places=2)
    
    def test_roic_with_cash(self):
        """Test that ROIC calculation includes Cash in Invested Capital"""
        result = self.service.calculate_magic_formula_metrics('TEST', financial_data=self.sample_data)
        
        # ROIC = EBIT / (Total Assets - Current Liabilities - Cash)
        # ROIC = $120M / ($2B - $300M - $200M) = $120M / $1.5B = 8%
        expected_roic = (120000000 / (2000000000 - 300000000 - 200000000)) * 100
        
        self.assertAlmostEqual(result['roic'], expected_roic, places=1)
    
    def test_ev_with_cash(self):
        """Test that Enterprise Value calculation includes Cash"""
        result = self.service.calculate_magic_formula_metrics('TEST', financial_data=self.sample_data)
        
        # EV = Market Cap + Total Debt - Cash
        # EV = $1B + ($500M + $300M) - $200M = $1.6B
        expected_ev = 1000000000 + (500000000 + 300000000) - 200000000
        
        self.assertAlmostEqual(result['enterprise_value'], expected_ev, places=0)
    
    def test_accrual_ratio_formula(self):
        """Test that Accrual Ratio uses correct formula: (Net Income - CFO) / Total Assets"""
        result = self.service.calculate_accrual_ratio('TEST', financial_data=self.sample_data)
        
        # Accrual Ratio = (Net Income - Operating Cash Flow) / Total Assets
        # = ($100M - $150M) / $2B = -$50M / $2B = -2.5%
        expected_ratio = ((100000000 - 150000000) / 2000000000) * 100
        
        self.assertAlmostEqual(result['accrual_ratio'], expected_ratio, places=2)
    
    def test_historical_data_fetching(self):
        """Test that historical data can be fetched for previous year"""
        # Mock the API calls
        with patch.object(self.service, '_fetch_from_alpha_vantage_historical') as mock_fetch:
            mock_fetch.return_value = self.previous_year_data
            
            historical = self.service.get_fundamental_data_historical('TEST', year_offset=1)
            
            self.assertIsNotNone(historical)
            self.assertEqual(historical['total_assets'], 1900000000)
            mock_fetch.assert_called_once_with('TEST', 1)
    
    def test_universe_ranking(self):
        """Test ranking universe by EBIT/EV"""
        symbols = ['AAPL', 'MSFT', 'GOOGL']
        
        with patch.object(self.service, 'get_fundamental_data') as mock_get_data:
            # Mock data with different EBIT/EV values
            mock_get_data.side_effect = [
                {**self.sample_data, 'symbol': 'AAPL', 'market_cap': 3000000000, 'ebit': 1000000000},  # High EBIT/EV
                {**self.sample_data, 'symbol': 'MSFT', 'market_cap': 2000000000, 'ebit': 800000000},   # Medium EBIT/EV
                {**self.sample_data, 'symbol': 'GOOGL', 'market_cap': 2500000000, 'ebit': 600000000},  # Lower EBIT/EV
            ]
            
            with patch.object(self.service, 'calculate_magic_formula_metrics') as mock_magic:
                mock_magic.side_effect = [
                    {'ebit_ev': 25.0, 'roic': 15.0, 'current_price': 150.0, 'enterprise_value': 4000000000},
                    {'ebit_ev': 20.0, 'roic': 12.0, 'current_price': 200.0, 'enterprise_value': 4000000000},
                    {'ebit_ev': 15.0, 'roic': 10.0, 'current_price': 100.0, 'enterprise_value': 4000000000},
                ]
                
                ranked = self.service.rank_universe_by_ebit_ev(symbols, percentile=0.33)
                
                # Should return top 33% (1 stock) with highest EBIT/EV
                self.assertEqual(len(ranked), 1)
                self.assertEqual(ranked[0]['symbol'], 'AAPL')  # Highest EBIT/EV
                self.assertEqual(ranked[0]['ebit_ev'], 25.0)
    
    def test_equal_weight_allocation(self):
        """Test equal weight capital allocation"""
        screened_stocks = [
            {'symbol': 'AAPL', 'current_price': 150.0, 'f_score': 8},
            {'symbol': 'MSFT', 'current_price': 200.0, 'f_score': 9},
            {'symbol': 'GOOGL', 'current_price': 100.0, 'f_score': 7},
        ]
        
        total_capital = 30000.0  # $30k
        
        allocated = self.service.allocate_capital_equal_weights(screened_stocks, total_capital)
        
        self.assertEqual(len(allocated), 3)
        # Each stock should get $10k
        for stock in allocated:
            self.assertEqual(stock['allocation_amount'], 10000.0)
            self.assertEqual(stock['allocation_percent'], 33.33)  # Approximately
            # Verify shares calculation
            expected_shares = 10000.0 / stock['current_price']
            self.assertAlmostEqual(stock['shares_to_buy'], expected_shares, places=2)
    
    def test_rebalancing_logic(self):
        """Test portfolio rebalancing logic"""
        current_holdings = {
            'AAPL': 8000.0,   # $8k current
            'MSFT': 12000.0,  # $12k current
            'GOOGL': 5000.0,  # $5k current
        }
        
        target_allocations = [
            {'symbol': 'AAPL', 'allocation_amount': 10000.0, 'current_price': 150.0},
            {'symbol': 'MSFT', 'allocation_amount': 10000.0, 'current_price': 200.0},
            {'symbol': 'GOOGL', 'allocation_amount': 10000.0, 'current_price': 100.0},
        ]
        
        rebalance_result = self.service.rebalance_portfolio(
            current_holdings=current_holdings,
            target_allocations=target_allocations,
            rebalance_date='2024-01-01'
        )
        
        # Should generate buy actions for AAPL and GOOGL, sell for MSFT
        actions = rebalance_result['rebalance_actions']
        self.assertGreater(len(actions), 0)
        
        # Find AAPL action (should be buy)
        aapl_action = next((a for a in actions if a['symbol'] == 'AAPL'), None)
        self.assertIsNotNone(aapl_action)
        self.assertEqual(aapl_action['action'], 'buy')
        self.assertAlmostEqual(aapl_action['amount'], 2000.0, places=0)  # $10k target - $8k current


if __name__ == '__main__':
    unittest.main()


