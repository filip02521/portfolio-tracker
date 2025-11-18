"""
Analiza korelacji między confidence a skutecznością sygnałów
"""
import sys
import os
import json
import numpy as np
from typing import Dict, List, Any
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_results(filename: str = 'verification_backtest_results.json') -> Dict:
    """Załaduj wyniki backtestów"""
    filepath = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return {}


def analyze_confidence_effectiveness(results: Dict) -> Dict:
    """Analizuj korelację między confidence a skutecznością"""
    if not results or 'results' not in results:
        return {}
    
    # Grupuj wyniki według confidence ranges
    confidence_ranges = {
        'low': (0.0, 0.4),      # 0-40%
        'medium': (0.4, 0.7),   # 40-70%
        'high': (0.7, 1.0)      # 70-100%
    }
    
    analysis = {
        'by_confidence_range': {},
        'correlation': {},
        'recommendations': []
    }
    
    for range_name, (min_conf, max_conf) in confidence_ranges.items():
        range_results = []
        for result in results['results']:
            # Sprawdź czy result ma confidence w tym zakresie
            # (może być w metadata lub można wyciągnąć z recommendations)
            conf = result.get('metadata', {}).get('avg_confidence', 0.5)
            if min_conf <= conf < max_conf:
                range_results.append(result)
        
        if range_results:
            returns = [r.get('total_return', 0) for r in range_results]
            win_rates = [r.get('win_rate', 0) for r in range_results]
            sharpe_ratios = [r.get('sharpe_ratio', 0) for r in range_results]
            profit_factors = [r.get('profit_factor', 0) for r in range_results if r.get('profit_factor', 0) > 0]
            
            analysis['by_confidence_range'][range_name] = {
                'count': len(range_results),
                'avg_return': np.mean(returns) if returns else 0,
                'avg_win_rate': np.mean(win_rates) if win_rates else 0,
                'avg_sharpe': np.mean(sharpe_ratios) if sharpe_ratios else 0,
                'avg_profit_factor': np.mean(profit_factors) if profit_factors else 0,
                'median_return': np.median(returns) if returns else 0,
                'std_return': np.std(returns) if returns else 0
            }
    
    # Oblicz korelację confidence vs return (jeśli dostępne)
    all_confidences = []
    all_returns = []
    all_win_rates = []
    
    for result in results['results']:
        conf = result.get('metadata', {}).get('avg_confidence', None)
        if conf is not None:
            all_confidences.append(conf)
            all_returns.append(result.get('total_return', 0))
            all_win_rates.append(result.get('win_rate', 0))
    
    if len(all_confidences) > 1:
        analysis['correlation'] = {
            'confidence_vs_return': float(np.corrcoef(all_confidences, all_returns)[0, 1]) if len(all_confidences) > 1 else 0,
            'confidence_vs_win_rate': float(np.corrcoef(all_confidences, all_win_rates)[0, 1]) if len(all_win_rates) > 1 else 0
        }
    
    # Rekomendacje
    if analysis['by_confidence_range']:
        high_conf = analysis['by_confidence_range'].get('high', {})
        medium_conf = analysis['by_confidence_range'].get('medium', {})
        low_conf = analysis['by_confidence_range'].get('low', {})
        
        if high_conf.get('avg_return', 0) > medium_conf.get('avg_return', 0) > low_conf.get('avg_return', 0):
            analysis['recommendations'].append(
                "✅ Wysoka korelacja: Wyższy confidence = wyższy return"
            )
        elif high_conf.get('avg_win_rate', 0) > medium_conf.get('avg_win_rate', 0):
            analysis['recommendations'].append(
                "✅ Wysoki confidence poprawia Win Rate"
            )
        else:
            analysis['recommendations'].append(
                "⚠️ Brak wyraźnej korelacji confidence-skuteczność - wymaga dalszej analizy"
            )
    
    return analysis


def generate_report(analysis: Dict, output_file: str = 'confidence_effectiveness_analysis.txt'):
    """Generuj raport z analizy"""
    filepath = os.path.join(os.path.dirname(__file__), output_file)
    
    with open(filepath, 'w') as f:
        f.write("="*60 + "\n")
        f.write("ANALIZA KORELACJI CONFIDENCE - SKUTECZNOŚĆ\n")
        f.write("="*60 + "\n\n")
        
        if analysis.get('by_confidence_range'):
            f.write("WYNIKI WEDŁUG ZAKRESÓW CONFIDENCE:\n")
            f.write("-"*60 + "\n")
            
            for range_name, stats in analysis['by_confidence_range'].items():
                f.write(f"\n{range_name.upper()} CONFIDENCE ({stats.get('count', 0)} testów):\n")
                f.write(f"  Średni Return: {stats.get('avg_return', 0):.2f}%\n")
                f.write(f"  Mediana Return: {stats.get('median_return', 0):.2f}%\n")
                f.write(f"  Odchylenie std: {stats.get('std_return', 0):.2f}%\n")
                f.write(f"  Średni Win Rate: {stats.get('avg_win_rate', 0):.2f}%\n")
                f.write(f"  Średni Sharpe: {stats.get('avg_sharpe', 0):.2f}\n")
                f.write(f"  Średni Profit Factor: {stats.get('avg_profit_factor', 0):.2f}\n")
        
        if analysis.get('correlation'):
            f.write("\n" + "="*60 + "\n")
            f.write("KORELACJE:\n")
            f.write("-"*60 + "\n")
            f.write(f"Confidence vs Return: {analysis['correlation'].get('confidence_vs_return', 0):.3f}\n")
            f.write(f"Confidence vs Win Rate: {analysis['correlation'].get('confidence_vs_win_rate', 0):.3f}\n")
        
        if analysis.get('recommendations'):
            f.write("\n" + "="*60 + "\n")
            f.write("REKOMENDACJE:\n")
            f.write("-"*60 + "\n")
            for rec in analysis['recommendations']:
                f.write(f"{rec}\n")
        
        f.write("\n" + "="*60 + "\n")
    
    logger.info(f"Raport zapisany do {filepath}")
    return filepath


def main():
    """Uruchom analizę"""
    print("="*60)
    print("ANALIZA KORELACJI CONFIDENCE - SKUTECZNOŚĆ")
    print("="*60)
    
    # Załaduj wyniki
    results = load_results()
    if not results:
        print("⚠️ Brak wyników backtestów. Uruchom najpierw run_full_verification.py")
        return
    
    # Analizuj
    analysis = analyze_confidence_effectiveness(results)
    
    # Generuj raport
    report_file = generate_report(analysis)
    
    # Wyświetl podsumowanie
    print("\nPodsumowanie:")
    if analysis.get('by_confidence_range'):
        for range_name, stats in analysis['by_confidence_range'].items():
            print(f"\n{range_name.upper()} CONFIDENCE:")
            print(f"  Średni Return: {stats.get('avg_return', 0):.2f}%")
            print(f"  Win Rate: {stats.get('avg_win_rate', 0):.2f}%")
            print(f"  Sharpe: {stats.get('avg_sharpe', 0):.2f}")
    
    if analysis.get('correlation'):
        print(f"\nKorelacja Confidence vs Return: {analysis['correlation'].get('confidence_vs_return', 0):.3f}")
        print(f"Korelacja Confidence vs Win Rate: {analysis['correlation'].get('confidence_vs_win_rate', 0):.3f}")
    
    print(f"\n✅ Raport zapisany do {report_file}")
    print("="*60)


if __name__ == '__main__':
    main()



