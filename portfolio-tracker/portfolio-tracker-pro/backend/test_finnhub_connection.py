#!/usr/bin/env python3
"""
Test script to verify Finnhub API connection and data retrieval
"""
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from config import Config
from fundamental_screening_service import FundamentalScreeningService
from market_data_service import MarketDataService


def test_finnhub_api():
    """Test Finnhub API connection and data retrieval"""
    print("="*70)
    print("Finnhub API Connection Test")
    print("="*70)
    
    # Initialize Config
    Config.init()
    
    # Check if API key is set
    api_key = Config.FINNHUB_API_KEY or os.getenv('FINNHUB_API_KEY', '')
    
    if not api_key:
        print("\n❌ ERROR: FINNHUB_API_KEY nie jest ustawiony!")
        print("\n📝 Instrukcja:")
        print("1. Skopiuj API Key z panelu Finnhub (https://finnhub.io/)")
        print("2. Utwórz plik .env w folderze portfolio-tracker-pro/backend/")
        print("3. Dodaj linię: FINNHUB_API_KEY=twoj_api_key_tutaj")
        print("4. Zrestartuj serwer backend")
        print("\nLub ustaw jako zmienną środowiskową:")
        print("export FINNHUB_API_KEY='twoj_api_key'")
        return False
    else:
        print(f"\n✅ API Key znaleziony: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else '****'}")
    
    # Initialize services
    print("\n🔧 Inicjalizowanie serwisów...")
    market_data_service = MarketDataService()
    fundamental_service = FundamentalScreeningService(market_data_service=market_data_service)
    
    # Test symbols
    test_symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    print(f"\n📊 Testowanie pobierania danych fundamentalnych dla: {', '.join(test_symbols)}")
    print("-"*70)
    
    success_count = 0
    fail_count = 0
    
    for symbol in test_symbols:
        print(f"\n🔍 Testowanie {symbol}...")
        try:
            # Try to get fundamental data
            data = fundamental_service.get_fundamental_data(symbol)
            
            if data:
                print(f"  ✅ Dane pobrane pomyślnie!")
                print(f"     - Company: {data.get('company_name', 'N/A')}")
                print(f"     - Market Cap: ${data.get('market_cap', 0):,.0f}" if data.get('market_cap') else "     - Market Cap: N/A")
                print(f"     - Revenue: ${data.get('revenue', 0):,.0f}" if data.get('revenue') else "     - Revenue: N/A")
                print(f"     - Net Income: ${data.get('net_income', 0):,.0f}" if data.get('net_income') else "     - Net Income: N/A")
                print(f"     - Source: {data.get('source', 'unknown')}")
                success_count += 1
            else:
                print(f"  ⚠️  Brak danych dla {symbol}")
                fail_count += 1
                
        except Exception as e:
            print(f"  ❌ Błąd: {str(e)}")
            fail_count += 1
    
    print("\n" + "="*70)
    print(f"Wyniki testu: {success_count} sukcesów, {fail_count} błędów")
    
    if success_count > 0:
        print("\n✅ Finnhub API działa poprawnie!")
        print("\n🧪 Testowanie kalkulacji metryk...")
        
        # Test calculation of metrics
        symbol = test_symbols[0]
        print(f"\n📈 Obliczanie metryk dla {symbol}...")
        
        try:
            data = fundamental_service.get_fundamental_data(symbol)
            if data:
                # Test F-Score
                f_score = fundamental_service.calculate_piotroski_f_score(symbol, data)
                print(f"  ✅ F-Score: {f_score.get('score', 0)}/9")
                
                # Test Z-Score
                z_score = fundamental_service.calculate_altman_z_score(symbol, data)
                print(f"  ✅ Z-Score: {z_score.get('z_score', 0):.2f} ({z_score.get('risk_level', 'unknown')})")
                
                # Test Magic Formula
                magic = fundamental_service.calculate_magic_formula_metrics(symbol, data)
                print(f"  ✅ ROIC: {magic.get('roic', 0):.2f}%")
                print(f"  ✅ EBIT/EV: {magic.get('ebit_ev', 0):.2f}%")
                
                # Test Accrual Ratio
                accrual = fundamental_service.calculate_accrual_ratio(symbol, data)
                print(f"  ✅ Accrual Ratio: {accrual.get('accrual_ratio', 0):.2f}%")
                
                print("\n✅ Wszystkie metryki obliczone poprawnie!")
            else:
                print(f"  ⚠️  Brak danych dla {symbol}, nie można obliczyć metryk")
        except Exception as e:
            print(f"  ❌ Błąd podczas obliczania metryk: {str(e)}")
            import traceback
            traceback.print_exc()
    else:
        print("\n❌ Finnhub API nie zwraca danych. Sprawdź:")
        print("  1. Czy API key jest poprawny")
        print("  2. Czy masz dostęp do danych fundamentalnych w swoim planie")
        print("  3. Czy nie przekroczyłeś limitu rate limit")
    
    print("\n" + "="*70)
    return success_count > 0


if __name__ == '__main__':
    success = test_finnhub_api()
    sys.exit(0 if success else 1)

