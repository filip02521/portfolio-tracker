"""
Analiza skuteczności AI recommendations na różnych klasach aktywów
(crypto, stocks, różne warunki rynkowe)
"""
import sys
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from verification_backtest import VerificationBacktest
except ImportError:
    # Fallback if import fails
    VerificationBacktest = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AssetClassAnalysis:
    """Analiza skuteczności na różnych klasach aktywów"""
    
    def __init__(self):
        """Inicjalizacja analizy"""
        if VerificationBacktest is None:
            raise ImportError("VerificationBacktest nie jest dostępny. Upewnij się, że verification_backtest.py istnieje.")
        self.verifier = VerificationBacktest()
        self.results = {}
    
    # Define asset classes
    CRYPTO_SYMBOLS = ['BTC', 'ETH', 'SOL', 'BNB', 'ADA', 'XRP']
    STOCK_SYMBOLS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA']
    
    def analyze_asset_classes(
        self,
        periods: List[Dict[str, str]] = None,
        signal_thresholds: List[float] = None,
        strategies: List[str] = None,
        initial_capital: float = 10000.0
    ) -> Dict[str, Any]:
        """
        Analizuj skuteczność na różnych klasach aktywów
        
        Args:
            periods: Lista okresów do testowania
            signal_thresholds: Lista progów signal_strength
            strategies: Lista strategii
            initial_capital: Kapitał początkowy
        
        Returns:
            Dictionary z wynikami analizy per asset class
        """
        if periods is None:
            end_date = datetime.now()
            periods = [
                {
                    'start': (end_date - timedelta(days=180)).isoformat(),
                    'end': end_date.isoformat(),
                    'name': '6 months'
                }
            ]
        
        if signal_thresholds is None:
            signal_thresholds = [10, 20, 30, 50]
        
        if strategies is None:
            strategies = ['follow_ai', 'high_confidence', 'buy_and_hold']
        
        logger.info("Analiza skuteczności na różnych klasach aktywów")
        
        results = {
            'crypto': {},
            'stocks': {},
            'mixed': {}
        }
        
        # Analiza crypto
        logger.info("Analiza kryptowalut...")
        crypto_results = self.verifier.run_verification_backtests(
            periods=periods,
            symbols=self.CRYPTO_SYMBOLS[:3],  # BTC, ETH, SOL
            signal_thresholds=signal_thresholds,
            confidence_thresholds=[None],
            strategies=strategies,
            initial_capital=initial_capital
        )
        results['crypto'] = crypto_results.get('summary', {})
        
        # Analiza stocks
        logger.info("Analiza akcji...")
        stock_results = self.verifier.run_verification_backtests(
            periods=periods,
            symbols=self.STOCK_SYMBOLS[:3],  # AAPL, MSFT, GOOGL
            signal_thresholds=signal_thresholds,
            confidence_thresholds=[None],
            strategies=strategies,
            initial_capital=initial_capital
        )
        results['stocks'] = stock_results.get('summary', {})
        
        # Analiza mixed (crypto + stocks)
        logger.info("Analiza mieszana (crypto + stocks)...")
        mixed_symbols = [self.CRYPTO_SYMBOLS[0], self.CRYPTO_SYMBOLS[1], 
                        self.STOCK_SYMBOLS[0], self.STOCK_SYMBOLS[1]]
        mixed_results = self.verifier.run_verification_backtests(
            periods=periods,
            symbols=mixed_symbols,
            signal_thresholds=signal_thresholds,
            confidence_thresholds=[None],
            strategies=strategies,
            initial_capital=initial_capital
        )
        results['mixed'] = mixed_results.get('summary', {})
        
        # Analiza warunków rynkowych (bull vs bear market)
        market_conditions = self._analyze_market_conditions(periods, signal_thresholds, strategies, initial_capital)
        results['market_conditions'] = market_conditions
        
        return results
    
    def _analyze_market_conditions(
        self,
        periods: List[Dict[str, str]],
        signal_thresholds: List[float],
        strategies: List[str],
        initial_capital: float
    ) -> Dict[str, Any]:
        """Analizuj skuteczność w różnych warunkach rynkowych"""
        # Dla uproszczenia, analizujemy ostatnie 6 miesięcy jako jeden okres
        # W rzeczywistości można by określić bull/bear market na podstawie trendu
        
        logger.info("Analiza warunków rynkowych...")
        
        # Wszystkie symbole (crypto + stocks)
        all_symbols = self.CRYPTO_SYMBOLS[:2] + self.STOCK_SYMBOLS[:2]
        
        results = self.verifier.run_verification_backtests(
            periods=periods,
            symbols=all_symbols,
            signal_thresholds=signal_thresholds,
            confidence_thresholds=[None],
            strategies=strategies,
            initial_capital=initial_capital
        )
        
        return results.get('summary', {})
    
    def compare_asset_classes(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Porównaj wyniki między klasami aktywów"""
        comparison = {
            'best_return': {
                'class': None,
                'value': 0.0
            },
            'best_sharpe': {
                'class': None,
                'value': 0.0
            },
            'best_win_rate': {
                'class': None,
                'value': 0.0
            },
            'class_comparison': {}
        }
        
        for asset_class, summary in results.items():
            if asset_class == 'market_conditions':
                continue
            
            if summary:
                avg_return = summary.get('avg_total_return', 0)
                avg_sharpe = summary.get('avg_sharpe_ratio', 0)
                avg_win_rate = summary.get('avg_win_rate', 0)
                
                comparison['class_comparison'][asset_class] = {
                    'avg_return': avg_return,
                    'avg_sharpe': avg_sharpe,
                    'avg_win_rate': avg_win_rate
                }
                
                # Najlepsze wyniki
                if avg_return > comparison['best_return']['value']:
                    comparison['best_return'] = {
                        'class': asset_class,
                        'value': avg_return
                    }
                
                if avg_sharpe > comparison['best_sharpe']['value']:
                    comparison['best_sharpe'] = {
                        'class': asset_class,
                        'value': avg_sharpe
                    }
                
                if avg_win_rate > comparison['best_win_rate']['value']:
                    comparison['best_win_rate'] = {
                        'class': asset_class,
                        'value': avg_win_rate
                    }
        
        return comparison
    
    def save_results(self, results: Dict[str, Any], filename: str = 'asset_class_analysis_results.json'):
        """Zapisz wyniki do pliku JSON"""
        filepath = os.path.join(os.path.dirname(__file__), filename)
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Wyniki zapisane do {filepath}")
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generuj raport tekstowy z wynikami"""
        report = []
        report.append("="*60)
        report.append("ANALIZA SKUTECZNOŚCI NA RÓŻNYCH KLASACH AKTYWÓW")
        report.append("="*60)
        report.append("")
        
        for asset_class, summary in results.items():
            if asset_class == 'market_conditions':
                continue
            
            report.append(f"Klasa aktywów: {asset_class.upper()}")
            report.append("-"*60)
            if summary:
                report.append(f"  Średni Total Return: {summary.get('avg_total_return', 0):.2f}%")
                report.append(f"  Średni Sharpe Ratio: {summary.get('avg_sharpe_ratio', 0):.2f}")
                report.append(f"  Średni Win Rate: {summary.get('avg_win_rate', 0):.2f}%")
                report.append(f"  Średni Profit Factor: {summary.get('avg_profit_factor', 0):.2f}")
                report.append(f"  Średni Max Drawdown: {summary.get('avg_max_drawdown', 0):.2f}%")
                report.append(f"  Średni Calmar Ratio: {summary.get('avg_calmar_ratio', 0):.2f}")
            report.append("")
        
        # Porównanie
        comparison = self.compare_asset_classes(results)
        report.append("PORÓWNANIE KLAS AKTYWÓW")
        report.append("-"*60)
        report.append(f"Najlepszy Return: {comparison['best_return']['class']} ({comparison['best_return']['value']:.2f}%)")
        report.append(f"Najlepszy Sharpe: {comparison['best_sharpe']['class']} ({comparison['best_sharpe']['value']:.2f})")
        report.append(f"Najlepszy Win Rate: {comparison['best_win_rate']['class']} ({comparison['best_win_rate']['value']:.2f}%)")
        report.append("")
        report.append("="*60)
        
        return "\n".join(report)


def main():
    """Main function do uruchomienia analizy"""
    analyzer = AssetClassAnalysis()
    
    # Uruchom analizę
    results = analyzer.analyze_asset_classes(
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
    
    # Zapisz wyniki
    analyzer.save_results(results)
    
    # Generuj raport
    report = analyzer.generate_report(results)
    print(report)
    
    # Zapisz raport
    report_filepath = os.path.join(os.path.dirname(__file__), 'asset_class_analysis_report.txt')
    with open(report_filepath, 'w') as f:
        f.write(report)
    logger.info(f"Raport zapisany do {report_filepath}")


if __name__ == '__main__':
    main()

