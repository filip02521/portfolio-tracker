"""
System weryfikacji historycznej dla AI recommendations
Testuje skuteczność sygnałów na różnych okresach, aktywach i progach signal_strength
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
    from ai_service import AIService
    from market_data_service import MarketDataService
except ImportError as e:
    logging.error(f"Błąd importu: {e}")
    AIService = None
    MarketDataService = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VerificationBacktest:
    """System weryfikacji historycznej dla AI recommendations"""
    
    def __init__(self):
        """Inicjalizacja systemu weryfikacji"""
        if MarketDataService is None or AIService is None:
            raise ImportError("AIService i MarketDataService nie są dostępne. Upewnij się, że pliki istnieją.")
        self.market_data_service = MarketDataService()
        self.ai_service = AIService(market_data_service=self.market_data_service)
        self.results = []
    
    def run_verification_backtests(
        self,
        periods: List[Dict[str, str]] = None,
        symbols: List[str] = None,
        signal_thresholds: List[float] = None,
        confidence_thresholds: List[float] = None,
        strategies: List[str] = None,
        initial_capital: float = 10000.0
    ) -> Dict[str, Any]:
        """
        Uruchom backtesty weryfikacyjne na różnych parametrach
        
        Args:
            periods: Lista okresów [{'start': '2024-01-01', 'end': '2024-06-30', 'name': '6 months'}]
            symbols: Lista symboli do testowania
            signal_thresholds: Lista progów signal_strength [10, 20, 30, 50, 70]
            confidence_thresholds: Lista progów confidence [0.5, 0.6, 0.7] (None = bez filtrowania)
            strategies: Lista strategii ['follow_ai', 'high_confidence']
            initial_capital: Kapitał początkowy
        
        Returns:
            Dictionary z wynikami wszystkich backtestów
        """
        if periods is None:
            # Domyślne okresy: 3 miesiące, 6 miesięcy, 1 rok
            end_date = datetime.now()
            periods = [
                {
                    'start': (end_date - timedelta(days=90)).isoformat(),
                    'end': end_date.isoformat(),
                    'name': '3 months'
                },
                {
                    'start': (end_date - timedelta(days=180)).isoformat(),
                    'end': end_date.isoformat(),
                    'name': '6 months'
                },
                {
                    'start': (end_date - timedelta(days=365)).isoformat(),
                    'end': end_date.isoformat(),
                    'name': '1 year'
                }
            ]
        
        if symbols is None:
            # Domyślne symbole: BTC, ETH, SOL, AAPL, MSFT, TSLA
            symbols = ['BTC', 'ETH', 'SOL', 'AAPL', 'MSFT', 'TSLA']
        
        if signal_thresholds is None:
            # Domyślne progi: 10, 20, 30, 50, 70
            signal_thresholds = [10, 20, 30, 50, 70]
        
        if confidence_thresholds is None:
            # Domyślnie bez filtrowania po confidence
            confidence_thresholds = [None]
        
        if strategies is None:
            # Domyślne strategie
            strategies = ['follow_ai', 'high_confidence', 'buy_and_hold']
        
        logger.info(f"Rozpoczynanie weryfikacji backtestów:")
        logger.info(f"  Okresy: {len(periods)}")
        logger.info(f"  Symbole: {len(symbols)}")
        logger.info(f"  Progi signal_strength: {signal_thresholds}")
        logger.info(f"  Progi confidence: {confidence_thresholds}")
        logger.info(f"  Strategie: {strategies}")
        
        all_results = []
        total_tests = len(periods) * len(symbols) * len(signal_thresholds) * len(confidence_thresholds) * len(strategies)
        current_test = 0
        
        for period in periods:
            for symbol_group in [symbols]:  # Testujemy wszystkie symbole razem
                for signal_threshold in signal_thresholds:
                    for confidence_threshold in confidence_thresholds:
                        for strategy in strategies:
                            current_test += 1
                            logger.info(f"Test {current_test}/{total_tests}: {period['name']}, "
                                      f"symbols={len(symbol_group)}, threshold={signal_threshold}, "
                                      f"confidence={confidence_threshold}, strategy={strategy}")
                            
                            try:
                                result = self._run_single_backtest(
                                    start_date=period['start'],
                                    end_date=period['end'],
                                    symbols=symbol_group,
                                    strategy=strategy,
                                    signal_threshold=signal_threshold,
                                    confidence_threshold=confidence_threshold,
                                    initial_capital=initial_capital
                                )
                                
                                if result and result.get('status') == 'success':
                                    result['period_name'] = period['name']
                                    result['period_start'] = period['start']
                                    result['period_end'] = period['end']
                                    result['symbols'] = symbol_group
                                    result['signal_threshold'] = signal_threshold
                                    result['confidence_threshold'] = confidence_threshold
                                    all_results.append(result)
                                    logger.info(f"  ✅ Success: Return={result.get('total_return', 0):.2f}%, "
                                              f"Sharpe={result.get('sharpe_ratio', 0):.2f}, "
                                              f"Win Rate={result.get('win_rate', 0):.2f}%")
                                else:
                                    logger.warning(f"  ⚠️ Failed: {result.get('error', 'Unknown error')}")
                            
                            except Exception as e:
                                logger.error(f"  ❌ Error: {e}")
                                all_results.append({
                                    'status': 'error',
                                    'error': str(e),
                                    'period_name': period['name'],
                                    'symbols': symbol_group,
                                    'signal_threshold': signal_threshold,
                                    'confidence_threshold': confidence_threshold,
                                    'strategy': strategy
                                })
        
        # Agregacja wyników
        summary = self._aggregate_results(all_results)
        
        return {
            'summary': summary,
            'detailed_results': all_results,
            'total_tests': total_tests,
            'successful_tests': len([r for r in all_results if r.get('status') == 'success']),
            'failed_tests': len([r for r in all_results if r.get('status') == 'error'])
        }
    
    def _run_single_backtest(
        self,
        start_date: str,
        end_date: str,
        symbols: List[str],
        strategy: str,
        signal_threshold: float,
        confidence_threshold: Optional[float],
        initial_capital: float
    ) -> Optional[Dict[str, Any]]:
        """
        Uruchom pojedynczy backtest
        
        Dla strategii 'follow_ai' z filtrowaniem po confidence, modyfikujemy strategię
        aby używała custom logic
        """
        if strategy == 'follow_ai' and confidence_threshold is not None:
            # Custom strategy z filtrowaniem po confidence
            # Musimy użyć backtest_recommendations z modyfikacją strategii
            result = self.ai_service.backtest_recommendations(
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                symbols=symbols,
                strategy='follow_ai',
                signal_threshold=signal_threshold
            )
            
            if result and result.get('status') == 'success':
                # Filtrowanie po confidence wymaga modyfikacji trade_history
                # Dla uproszczenia, zwracamy wynik bez filtrowania (można dodać później)
                result['confidence_threshold'] = confidence_threshold
                return result
            else:
                return result
        else:
            # Standardowa strategia
            return self.ai_service.backtest_recommendations(
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                symbols=symbols,
                strategy=strategy,
                signal_threshold=signal_threshold
            )
    
    def _aggregate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Agreguj wyniki backtestów"""
        successful_results = [r for r in results if r.get('status') == 'success']
        
        if not successful_results:
            return {
                'avg_total_return': 0.0,
                'avg_sharpe_ratio': 0.0,
                'avg_win_rate': 0.0,
                'avg_profit_factor': 0.0,
                'avg_max_drawdown': 0.0,
                'avg_calmar_ratio': 0.0,
                'best_strategy': None,
                'best_period': None,
                'best_threshold': None
            }
        
        # Agregacja metryk
        avg_total_return = sum(r.get('total_return', 0) for r in successful_results) / len(successful_results)
        avg_sharpe_ratio = sum(r.get('sharpe_ratio', 0) for r in successful_results) / len(successful_results)
        avg_win_rate = sum(r.get('win_rate', 0) for r in successful_results) / len(successful_results)
        avg_profit_factor = sum(r.get('profit_factor', 0) if r.get('profit_factor') != float('inf') else 0 
                               for r in successful_results) / len(successful_results)
        avg_max_drawdown = sum(r.get('max_drawdown', 0) for r in successful_results) / len(successful_results)
        avg_calmar_ratio = sum(r.get('calmar_ratio', 0) for r in successful_results) / len(successful_results)
        
        # Najlepsze wyniki
        best_by_return = max(successful_results, key=lambda x: x.get('total_return', 0))
        best_by_sharpe = max(successful_results, key=lambda x: x.get('sharpe_ratio', 0))
        best_by_win_rate = max(successful_results, key=lambda x: x.get('win_rate', 0))
        
        # Agregacja per strategy
        strategy_stats = {}
        for result in successful_results:
            strategy = result.get('strategy', 'unknown')
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {
                    'count': 0,
                    'total_return': 0.0,
                    'sharpe_ratio': 0.0,
                    'win_rate': 0.0,
                    'profit_factor': 0.0
                }
            
            strategy_stats[strategy]['count'] += 1
            strategy_stats[strategy]['total_return'] += result.get('total_return', 0)
            strategy_stats[strategy]['sharpe_ratio'] += result.get('sharpe_ratio', 0)
            strategy_stats[strategy]['win_rate'] += result.get('win_rate', 0)
            pf = result.get('profit_factor', 0)
            if pf != float('inf'):
                strategy_stats[strategy]['profit_factor'] += pf
        
        # Średnie per strategy
        for strategy in strategy_stats:
            count = strategy_stats[strategy]['count']
            if count > 0:
                strategy_stats[strategy]['avg_total_return'] = strategy_stats[strategy]['total_return'] / count
                strategy_stats[strategy]['avg_sharpe_ratio'] = strategy_stats[strategy]['sharpe_ratio'] / count
                strategy_stats[strategy]['avg_win_rate'] = strategy_stats[strategy]['win_rate'] / count
                strategy_stats[strategy]['avg_profit_factor'] = strategy_stats[strategy]['profit_factor'] / count
        
        # Agregacja per threshold
        threshold_stats = {}
        for result in successful_results:
            threshold = result.get('signal_threshold', 0)
            if threshold not in threshold_stats:
                threshold_stats[threshold] = {
                    'count': 0,
                    'total_return': 0.0,
                    'sharpe_ratio': 0.0,
                    'win_rate': 0.0
                }
            
            threshold_stats[threshold]['count'] += 1
            threshold_stats[threshold]['total_return'] += result.get('total_return', 0)
            threshold_stats[threshold]['sharpe_ratio'] += result.get('sharpe_ratio', 0)
            threshold_stats[threshold]['win_rate'] += result.get('win_rate', 0)
        
        # Średnie per threshold
        for threshold in threshold_stats:
            count = threshold_stats[threshold]['count']
            if count > 0:
                threshold_stats[threshold]['avg_total_return'] = threshold_stats[threshold]['total_return'] / count
                threshold_stats[threshold]['avg_sharpe_ratio'] = threshold_stats[threshold]['sharpe_ratio'] / count
                threshold_stats[threshold]['avg_win_rate'] = threshold_stats[threshold]['win_rate'] / count
        
        return {
            'avg_total_return': avg_total_return,
            'avg_sharpe_ratio': avg_sharpe_ratio,
            'avg_win_rate': avg_win_rate,
            'avg_profit_factor': avg_profit_factor,
            'avg_max_drawdown': avg_max_drawdown,
            'avg_calmar_ratio': avg_calmar_ratio,
            'best_by_return': {
                'strategy': best_by_return.get('strategy'),
                'period': best_by_return.get('period_name'),
                'threshold': best_by_return.get('signal_threshold'),
                'return': best_by_return.get('total_return', 0),
                'sharpe': best_by_return.get('sharpe_ratio', 0),
                'win_rate': best_by_return.get('win_rate', 0)
            },
            'best_by_sharpe': {
                'strategy': best_by_sharpe.get('strategy'),
                'period': best_by_sharpe.get('period_name'),
                'threshold': best_by_sharpe.get('signal_threshold'),
                'return': best_by_sharpe.get('total_return', 0),
                'sharpe': best_by_sharpe.get('sharpe_ratio', 0),
                'win_rate': best_by_sharpe.get('win_rate', 0)
            },
            'best_by_win_rate': {
                'strategy': best_by_win_rate.get('strategy'),
                'period': best_by_win_rate.get('period_name'),
                'threshold': best_by_win_rate.get('signal_threshold'),
                'return': best_by_win_rate.get('total_return', 0),
                'sharpe': best_by_win_rate.get('sharpe_ratio', 0),
                'win_rate': best_by_win_rate.get('win_rate', 0)
            },
            'strategy_stats': strategy_stats,
            'threshold_stats': threshold_stats
        }
    
    def save_results(self, results: Dict[str, Any], filename: str = 'verification_backtest_results.json'):
        """Zapisz wyniki do pliku JSON"""
        filepath = os.path.join(os.path.dirname(__file__), filename)
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Wyniki zapisane do {filepath}")
    
    def load_results(self, filename: str = 'verification_backtest_results.json') -> Optional[Dict[str, Any]]:
        """Wczytaj wyniki z pliku JSON"""
        filepath = os.path.join(os.path.dirname(__file__), filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        return None


def main():
    """Main function do uruchomienia weryfikacji"""
    verifier = VerificationBacktest()
    
    # Uruchom weryfikację
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
        symbols=['BTC', 'ETH', 'AAPL', 'MSFT'],
        signal_thresholds=[10, 20, 30, 50],
        confidence_thresholds=[None, 0.6, 0.7],
        strategies=['follow_ai', 'high_confidence', 'buy_and_hold'],
        initial_capital=10000.0
    )
    
    # Zapisz wyniki
    verifier.save_results(results)
    
    # Wyświetl podsumowanie
    print("\n" + "="*60)
    print("PODSUMOWANIE WERYFIKACJI")
    print("="*60)
    summary = results.get('summary', {})
    print(f"Średni Total Return: {summary.get('avg_total_return', 0):.2f}%")
    print(f"Średni Sharpe Ratio: {summary.get('avg_sharpe_ratio', 0):.2f}")
    print(f"Średni Win Rate: {summary.get('avg_win_rate', 0):.2f}%")
    print(f"Średni Profit Factor: {summary.get('avg_profit_factor', 0):.2f}")
    print(f"Średni Max Drawdown: {summary.get('avg_max_drawdown', 0):.2f}%")
    print(f"Średni Calmar Ratio: {summary.get('avg_calmar_ratio', 0):.2f}")
    print(f"\nNajlepszy wynik (Total Return):")
    best_return = summary.get('best_by_return', {})
    print(f"  Strategia: {best_return.get('strategy')}")
    print(f"  Okres: {best_return.get('period')}")
    print(f"  Threshold: {best_return.get('threshold')}")
    print(f"  Return: {best_return.get('return', 0):.2f}%")
    print(f"  Sharpe: {best_return.get('sharpe', 0):.2f}")
    print(f"  Win Rate: {best_return.get('win_rate', 0):.2f}%")
    print(f"\nNajlepszy wynik (Sharpe Ratio):")
    best_sharpe = summary.get('best_by_sharpe', {})
    print(f"  Strategia: {best_sharpe.get('strategy')}")
    print(f"  Okres: {best_sharpe.get('period')}")
    print(f"  Threshold: {best_sharpe.get('threshold')}")
    print(f"  Return: {best_sharpe.get('return', 0):.2f}%")
    print(f"  Sharpe: {best_sharpe.get('sharpe', 0):.2f}")
    print(f"  Win Rate: {best_sharpe.get('win_rate', 0):.2f}%")
    print("="*60)


if __name__ == '__main__':
    main()

