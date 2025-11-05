"""
Szybki test weryfikacji - mniejszy zakres testów
"""
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from verification_backtest import VerificationBacktest

def main():
    """Uruchom szybki test weryfikacji"""
    print("="*60)
    print("SZYBKI TEST WERYFIKACJI")
    print("="*60)
    
    verifier = VerificationBacktest()
    
    # Mniejszy zakres testów - tylko 1 okres, 2 symbole, 2 progi, 2 strategie
    results = verifier.run_verification_backtests(
        periods=[
            {
                'start': (datetime.now() - timedelta(days=90)).isoformat(),
                'end': datetime.now().isoformat(),
                'name': '3 months'
            }
        ],
        symbols=['BTC', 'AAPL'],  # Tylko 2 symbole
        signal_thresholds=[20, 50],  # Tylko 2 progi
        confidence_thresholds=[None],
        strategies=['follow_ai', 'buy_and_hold'],  # Tylko 2 strategie
        initial_capital=10000.0
    )
    
    verifier.save_results(results, 'quick_verification_results.json')
    
    print("\n" + "="*60)
    print("PODSUMOWANIE")
    print("="*60)
    summary = results.get('summary', {})
    print(f"Średni Total Return: {summary.get('avg_total_return', 0):.2f}%")
    print(f"Średni Sharpe Ratio: {summary.get('avg_sharpe_ratio', 0):.2f}")
    print(f"Średni Win Rate: {summary.get('avg_win_rate', 0):.2f}%")
    print(f"Total tests: {results.get('total_tests', 0)}")
    print(f"Successful: {results.get('successful_tests', 0)}")
    print(f"Failed: {results.get('failed_tests', 0)}")
    print("="*60)

if __name__ == '__main__':
    main()

