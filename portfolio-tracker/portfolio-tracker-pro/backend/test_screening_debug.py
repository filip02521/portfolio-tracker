#!/usr/bin/env python3
"""
Debug script to check why stocks don't pass VQ+ screening
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from fundamental_screening_service import FundamentalScreeningService
from market_data_service import MarketDataService


def debug_screening():
    """Debug VQ+ screening to see why stocks fail"""
    print("="*80)
    print("VQ+ Screening Debug")
    print("="*80)
    
    market_data_service = MarketDataService()
    fundamental_service = FundamentalScreeningService(market_data_service=market_data_service)
    
    test_symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    for symbol in test_symbols:
        print(f"\n{'='*80}")
        print(f"Analiza {symbol}")
        print(f"{'='*80}")
        
        # Get fundamental data
        data = fundamental_service.get_fundamental_data(symbol)
        if not data:
            print(f"❌ Brak danych fundamentalnych dla {symbol}")
            continue
        
        print(f"\n📊 Dane Fundamentalne:")
        print(f"  Company: {data.get('company_name', 'N/A')}")
        print(f"  Market Cap: ${data.get('market_cap', 0):,.0f}")
        print(f"  Revenue: ${data.get('revenue', 0):,.0f}")
        print(f"  Net Income: ${data.get('net_income', 0):,.0f}")
        print(f"  Total Assets: ${data.get('total_assets', 0):,.0f}")
        print(f"  Total Liabilities: ${data.get('total_liabilities', 0):,.0f}")
        print(f"  EBIT: ${data.get('ebit', 0):,.0f}")
        print(f"  Operating Cash Flow: ${data.get('operating_cash_flow', 0):,.0f}")
        print(f"  Current Assets: ${data.get('current_assets', 0):,.0f}")
        print(f"  Current Liabilities: ${data.get('current_liabilities', 0):,.0f}")
        print(f"  Long Term Debt: ${data.get('long_term_debt', 0):,.0f}")
        print(f"  Cash: ${data.get('cash_and_cash_equivalents', 0):,.0f}")
        print(f"  Retained Earnings: ${data.get('retained_earnings', 0):,.0f}")
        print(f"  Source: {data.get('source', 'unknown')}")
        
        # Calculate metrics
        print(f"\n🧮 Obliczanie Metryk:")
        
        # F-Score
        f_score_result = fundamental_service.calculate_piotroski_f_score(symbol, data)
        f_score = f_score_result.get('score', 0)
        print(f"  F-Score: {f_score}/9")
        print(f"    Filtry: Min 6 (obecnie: {'✅ PASS' if f_score >= 6 else '❌ FAIL'})")
        
        # Z-Score
        z_score_result = fundamental_service.calculate_altman_z_score(symbol, data)
        z_score = z_score_result.get('z_score', 0)
        print(f"  Z-Score: {z_score:.2f} ({z_score_result.get('risk_level', 'unknown')})")
        print(f"    Filtry: Min 2.0 (obecnie: {'✅ PASS' if z_score >= 2.0 else '❌ FAIL'})")
        
        # Magic Formula
        magic = fundamental_service.calculate_magic_formula_metrics(symbol, financial_data=data)
        roic = magic.get('roic', 0)
        ebit_ev = magic.get('ebit_ev', 0)
        print(f"  ROIC: {roic:.2f}%")
        print(f"  EBIT/EV: {ebit_ev:.2f}%")
        
        # Accrual Ratio
        accrual = fundamental_service.calculate_accrual_ratio(symbol, data)
        accrual_ratio = accrual.get('accrual_ratio', 0)
        print(f"  Accrual Ratio: {accrual_ratio:.2f}% ({accrual.get('quality_flag', 'unknown')})")
        print(f"    Filtry: Max 10.0% (obecnie: {'✅ PASS' if accrual_ratio <= 10.0 else '❌ FAIL'})")
        
        # Check if passes all filters
        passes = True
        failures = []
        
        if f_score < 6:
            passes = False
            failures.append(f"F-Score {f_score} < 6")
        
        if z_score < 2.0:
            passes = False
            failures.append(f"Z-Score {z_score:.2f} < 2.0")
        
        if accrual_ratio > 10.0:
            passes = False
            failures.append(f"Accrual Ratio {accrual_ratio:.2f}% > 10.0%")
        
        print(f"\n{'='*80}")
        if passes:
            print(f"✅ {symbol} PRZECHODZI wszystkie filtry VQ+")
        else:
            print(f"❌ {symbol} NIE PRZECHODZI filtrów VQ+")
            print(f"   Powody: {', '.join(failures)}")
        print(f"{'='*80}")


if __name__ == '__main__':
    debug_screening()

