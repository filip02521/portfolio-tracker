"""
Pełna weryfikacja - bardziej rozsądny zakres testów
"""
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from verification_backtest import VerificationBacktest
from asset_class_analysis import AssetClassAnalysis
from verification_report_generator import VerificationReportGenerator

def main():
    """Uruchom pełną weryfikację"""
    print("="*60)
    print("PEŁNA WERYFIKACJA AI RECOMMENDATIONS")
    print("="*60)
    
    # 1. Weryfikacja backtestów
    print("\n1. Uruchamianie weryfikacji backtestów...")
    verifier = VerificationBacktest()
    
    results = verifier.run_verification_backtests(
        periods=[
            {
                'start': (datetime.now() - timedelta(days=90)).isoformat(),
                'end': datetime.now().isoformat(),
                'name': '3 months'
            },
            {
                'start': (datetime.now() - timedelta(days=180)).isoformat(),
                'end': datetime.now().isoformat(),
                'name': '6 months'
            }
        ],
        symbols=['BTC', 'ETH', 'AAPL', 'MSFT'],  # 4 symbole
        signal_thresholds=[10, 20, 30, 50],  # 4 progi
        confidence_thresholds=[None],
        strategies=['follow_ai', 'high_confidence', 'buy_and_hold'],  # 3 strategie
        initial_capital=10000.0
    )
    
    verifier.save_results(results)
    print("✅ Weryfikacja backtestów zakończona")
    
    # 2. Analiza klas aktywów
    print("\n2. Uruchamianie analizy klas aktywów...")
    analyzer = AssetClassAnalysis()
    
    asset_class_results = analyzer.analyze_asset_classes(
        periods=[
            {
                'start': (datetime.now() - timedelta(days=180)).isoformat(),
                'end': datetime.now().isoformat(),
                'name': '6 months'
            }
        ],
        signal_thresholds=[10, 20, 30],  # 3 progi
        strategies=['follow_ai', 'buy_and_hold'],  # 2 strategie
        initial_capital=10000.0
    )
    
    analyzer.save_results(asset_class_results)
    print("✅ Analiza klas aktywów zakończona")
    
    # 3. Generowanie raportów
    print("\n3. Generowanie raportów...")
    generator = VerificationReportGenerator()
    
    # Generuj raport HTML
    html_file = generator.generate_html_report(
        results,
        asset_class_results,
        output_file='verification_report.html'
    )
    print(f"✅ Raport HTML wygenerowany: {html_file}")
    
    # Generuj raport tekstowy
    txt_file = generator.generate_text_report(
        results,
        asset_class_results,
        output_file='verification_report.txt'
    )
    print(f"✅ Raport tekstowy wygenerowany: {txt_file}")
    
    # 4. Podsumowanie
    print("\n" + "="*60)
    print("WERYFIKACJA ZAKOŃCZONA")
    print("="*60)
    
    summary = results.get('summary', {})
    print(f"\nPodsumowanie wyników:")
    print(f"  Średni Total Return: {summary.get('avg_total_return', 0):.2f}%")
    print(f"  Średni Sharpe Ratio: {summary.get('avg_sharpe_ratio', 0):.2f}")
    print(f"  Średni Win Rate: {summary.get('avg_win_rate', 0):.2f}%")
    print(f"  Średni Profit Factor: {summary.get('avg_profit_factor', 0):.2f}")
    print(f"  Średni Max Drawdown: {summary.get('avg_max_drawdown', 0):.2f}%")
    print(f"  Średni Calmar Ratio: {summary.get('avg_calmar_ratio', 0):.2f}")
    
    if summary.get('best_by_return'):
        best_return = summary['best_by_return']
        print(f"\nNajlepszy wynik (Total Return):")
        print(f"  Strategia: {best_return.get('strategy')}")
        print(f"  Return: {best_return.get('return', 0):.2f}%")
        print(f"  Sharpe: {best_return.get('sharpe', 0):.2f}")
        print(f"  Win Rate: {best_return.get('win_rate', 0):.2f}%")
    
    if summary.get('best_by_sharpe'):
        best_sharpe = summary['best_by_sharpe']
        print(f"\nNajlepszy wynik (Sharpe Ratio):")
        print(f"  Strategia: {best_sharpe.get('strategy')}")
        print(f"  Return: {best_sharpe.get('return', 0):.2f}%")
        print(f"  Sharpe: {best_sharpe.get('sharpe', 0):.2f}")
        print(f"  Win Rate: {best_sharpe.get('win_rate', 0):.2f}%")
    
    print("\n✅ Wszystkie raporty zostały wygenerowane pomyślnie!")
    print("="*60)

if __name__ == '__main__':
    main()



