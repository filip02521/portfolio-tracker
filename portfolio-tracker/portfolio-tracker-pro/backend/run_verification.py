"""
Skrypt pomocniczy do uruchomienia pełnej weryfikacji AI recommendations
"""
import sys
import os
import logging
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_full_verification():
    """Uruchom pełną weryfikację AI recommendations"""
    logger.info("="*60)
    logger.info("ROZPOCZĘCIE PEŁNEJ WERYFIKACJI AI RECOMMENDATIONS")
    logger.info("="*60)
    
    try:
        # 1. Weryfikacja backtestów
        logger.info("\n1. Uruchamianie weryfikacji backtestów...")
        from verification_backtest import VerificationBacktest
        
        verifier = VerificationBacktest()
        verification_results = verifier.run_verification_backtests(
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
            symbols=['BTC', 'ETH', 'AAPL', 'MSFT'],
            signal_thresholds=[10, 20, 30, 50],
            confidence_thresholds=[None],
            strategies=['follow_ai', 'high_confidence', 'buy_and_hold'],
            initial_capital=10000.0
        )
        
        verifier.save_results(verification_results)
        logger.info("✅ Weryfikacja backtestów zakończona")
        
        # 2. Analiza klas aktywów
        logger.info("\n2. Uruchamianie analizy klas aktywów...")
        from asset_class_analysis import AssetClassAnalysis
        
        analyzer = AssetClassAnalysis()
        asset_class_results = analyzer.analyze_asset_classes(
            periods=[
                {
                    'start': (datetime.now() - timedelta(days=180)).isoformat(),
                    'end': datetime.now().isoformat(),
                    'name': '6 months'
                }
            ],
            signal_thresholds=[10, 20, 30],
            strategies=['follow_ai', 'buy_and_hold'],
            initial_capital=10000.0
        )
        
        analyzer.save_results(asset_class_results)
        logger.info("✅ Analiza klas aktywów zakończona")
        
        # 3. Generowanie raportów
        logger.info("\n3. Generowanie raportów...")
        from verification_report_generator import VerificationReportGenerator
        
        generator = VerificationReportGenerator()
        
        # Generuj raport HTML
        html_file = generator.generate_html_report(
            verification_results,
            asset_class_results,
            output_file='verification_report.html'
        )
        logger.info(f"✅ Raport HTML wygenerowany: {html_file}")
        
        # Generuj raport tekstowy
        txt_file = generator.generate_text_report(
            verification_results,
            asset_class_results,
            output_file='verification_report.txt'
        )
        logger.info(f"✅ Raport tekstowy wygenerowany: {txt_file}")
        
        # 4. Podsumowanie
        logger.info("\n" + "="*60)
        logger.info("WERYFIKACJA ZAKOŃCZONA POMYŚLNIE")
        logger.info("="*60)
        
        summary = verification_results.get('summary', {})
        logger.info(f"\nPodsumowanie wyników:")
        logger.info(f"  Średni Total Return: {summary.get('avg_total_return', 0):.2f}%")
        logger.info(f"  Średni Sharpe Ratio: {summary.get('avg_sharpe_ratio', 0):.2f}")
        logger.info(f"  Średni Win Rate: {summary.get('avg_win_rate', 0):.2f}%")
        logger.info(f"  Średni Profit Factor: {summary.get('avg_profit_factor', 0):.2f}")
        logger.info(f"\nNajlepszy wynik (Total Return):")
        best_return = summary.get('best_by_return', {})
        logger.info(f"  Strategia: {best_return.get('strategy')}")
        logger.info(f"  Return: {best_return.get('return', 0):.2f}%")
        logger.info(f"  Sharpe: {best_return.get('sharpe', 0):.2f}")
        
        logger.info("\n✅ Wszystkie raporty zostały wygenerowane pomyślnie!")
        
    except Exception as e:
        logger.error(f"❌ Błąd podczas weryfikacji: {e}", exc_info=True)
        return False
    
    return True


if __name__ == '__main__':
    from datetime import timedelta
    success = run_full_verification()
    sys.exit(0 if success else 1)

