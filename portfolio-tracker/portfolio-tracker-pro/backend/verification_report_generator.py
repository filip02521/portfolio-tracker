"""
Generator raportów HTML/PDF z wynikami backtestów
"""
import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VerificationReportGenerator:
    """Generator raportów HTML/PDF z wynikami backtestów"""
    
    def __init__(self):
        """Inicjalizacja generatora"""
        pass
    
    def generate_html_report(
        self,
        verification_results: Dict[str, Any],
        asset_class_results: Optional[Dict[str, Any]] = None,
        output_file: str = 'verification_report.html'
    ) -> str:
        """
        Generuj raport HTML z wynikami backtestów
        
        Args:
            verification_results: Wyniki z verification_backtest.py
            asset_class_results: Wyniki z asset_class_analysis.py (opcjonalnie)
            output_file: Nazwa pliku wyjściowego
        
        Returns:
            Ścieżka do wygenerowanego pliku
        """
        html_content = self._generate_html_content(verification_results, asset_class_results)
        
        filepath = os.path.join(os.path.dirname(__file__), output_file)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Raport HTML zapisany do {filepath}")
        return filepath
    
    def _generate_html_content(
        self,
        verification_results: Dict[str, Any],
        asset_class_results: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generuj zawartość HTML"""
        summary = verification_results.get('summary', {})
        detailed_results = verification_results.get('detailed_results', [])
        
        html = f"""<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Raport Weryfikacji AI Recommendations</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
            border-bottom: 2px solid #ddd;
            padding-bottom: 5px;
        }}
        h3 {{
            color: #666;
            margin-top: 20px;
        }}
        .summary {{
            background-color: #f9f9f9;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .metric {{
            display: inline-block;
            margin: 10px 20px 10px 0;
            padding: 10px 15px;
            background-color: #e8f5e9;
            border-radius: 5px;
            min-width: 150px;
        }}
        .metric-label {{
            font-weight: bold;
            color: #666;
            font-size: 0.9em;
        }}
        .metric-value {{
            font-size: 1.5em;
            color: #2e7d32;
            font-weight: bold;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .positive {{
            color: #2e7d32;
            font-weight: bold;
        }}
        .negative {{
            color: #c62828;
            font-weight: bold;
        }}
        .best {{
            background-color: #fff9c4;
            font-weight: bold;
        }}
        .chart-placeholder {{
            background-color: #f5f5f5;
            padding: 40px;
            text-align: center;
            border: 2px dashed #ddd;
            margin: 20px 0;
            color: #999;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #999;
            font-size: 0.9em;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Raport Weryfikacji AI Recommendations</h1>
        <p>Data wygenerowania: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h2>Podsumowanie</h2>
        <div class="summary">
            <div class="metric">
                <div class="metric-label">Średni Total Return</div>
                <div class="metric-value">{summary.get('avg_total_return', 0):.2f}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Średni Sharpe Ratio</div>
                <div class="metric-value">{summary.get('avg_sharpe_ratio', 0):.2f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Średni Win Rate</div>
                <div class="metric-value">{summary.get('avg_win_rate', 0):.2f}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Średni Profit Factor</div>
                <div class="metric-value">{summary.get('avg_profit_factor', 0):.2f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Średni Max Drawdown</div>
                <div class="metric-value">{summary.get('avg_max_drawdown', 0):.2f}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Średni Calmar Ratio</div>
                <div class="metric-value">{summary.get('avg_calmar_ratio', 0):.2f}</div>
            </div>
        </div>
        
        <h2>Najlepsze Wyniki</h2>
        
        <h3>Najlepszy Total Return</h3>
        <table>
            <tr>
                <th>Strategia</th>
                <th>Okres</th>
                <th>Threshold</th>
                <th>Total Return</th>
                <th>Sharpe Ratio</th>
                <th>Win Rate</th>
            </tr>
            <tr class="best">
                <td>{summary.get('best_by_return', {}).get('strategy', 'N/A')}</td>
                <td>{summary.get('best_by_return', {}).get('period', 'N/A')}</td>
                <td>{summary.get('best_by_return', {}).get('threshold', 'N/A')}</td>
                <td class="positive">{summary.get('best_by_return', {}).get('return', 0):.2f}%</td>
                <td>{summary.get('best_by_return', {}).get('sharpe', 0):.2f}</td>
                <td>{summary.get('best_by_return', {}).get('win_rate', 0):.2f}%</td>
            </tr>
        </table>
        
        <h3>Najlepszy Sharpe Ratio</h3>
        <table>
            <tr>
                <th>Strategia</th>
                <th>Okres</th>
                <th>Threshold</th>
                <th>Total Return</th>
                <th>Sharpe Ratio</th>
                <th>Win Rate</th>
            </tr>
            <tr class="best">
                <td>{summary.get('best_by_sharpe', {}).get('strategy', 'N/A')}</td>
                <td>{summary.get('best_by_sharpe', {}).get('period', 'N/A')}</td>
                <td>{summary.get('best_by_sharpe', {}).get('threshold', 'N/A')}</td>
                <td>{summary.get('best_by_sharpe', {}).get('return', 0):.2f}%</td>
                <td class="positive">{summary.get('best_by_sharpe', {}).get('sharpe', 0):.2f}</td>
                <td>{summary.get('best_by_sharpe', {}).get('win_rate', 0):.2f}%</td>
            </tr>
        </table>
        
        <h3>Najlepszy Win Rate</h3>
        <table>
            <tr>
                <th>Strategia</th>
                <th>Okres</th>
                <th>Threshold</th>
                <th>Total Return</th>
                <th>Sharpe Ratio</th>
                <th>Win Rate</th>
            </tr>
            <tr class="best">
                <td>{summary.get('best_by_win_rate', {}).get('strategy', 'N/A')}</td>
                <td>{summary.get('best_by_win_rate', {}).get('period', 'N/A')}</td>
                <td>{summary.get('best_by_win_rate', {}).get('threshold', 'N/A')}</td>
                <td>{summary.get('best_by_win_rate', {}).get('return', 0):.2f}%</td>
                <td>{summary.get('best_by_win_rate', {}).get('sharpe', 0):.2f}</td>
                <td class="positive">{summary.get('best_by_win_rate', {}).get('win_rate', 0):.2f}%</td>
            </tr>
        </table>
        
        <h2>Statystyki per Strategia</h2>
        <table>
            <tr>
                <th>Strategia</th>
                <th>Średni Total Return</th>
                <th>Średni Sharpe Ratio</th>
                <th>Średni Win Rate</th>
                <th>Średni Profit Factor</th>
                <th>Liczba Testów</th>
            </tr>
"""
        
        strategy_stats = summary.get('strategy_stats', {})
        for strategy, stats in strategy_stats.items():
            html += f"""
            <tr>
                <td><strong>{strategy}</strong></td>
                <td class="{'positive' if stats.get('avg_total_return', 0) > 0 else 'negative'}">{stats.get('avg_total_return', 0):.2f}%</td>
                <td>{stats.get('avg_sharpe_ratio', 0):.2f}</td>
                <td>{stats.get('avg_win_rate', 0):.2f}%</td>
                <td>{stats.get('avg_profit_factor', 0):.2f}</td>
                <td>{stats.get('count', 0)}</td>
            </tr>
"""
        
        html += """
        </table>
        
        <h2>Statystyki per Threshold</h2>
        <table>
            <tr>
                <th>Signal Threshold</th>
                <th>Średni Total Return</th>
                <th>Średni Sharpe Ratio</th>
                <th>Średni Win Rate</th>
                <th>Liczba Testów</th>
            </tr>
"""
        
        threshold_stats = summary.get('threshold_stats', {})
        for threshold, stats in sorted(threshold_stats.items()):
            html += f"""
            <tr>
                <td><strong>{threshold}</strong></td>
                <td class="{'positive' if stats.get('avg_total_return', 0) > 0 else 'negative'}">{stats.get('avg_total_return', 0):.2f}%</td>
                <td>{stats.get('avg_sharpe_ratio', 0):.2f}</td>
                <td>{stats.get('avg_win_rate', 0):.2f}%</td>
                <td>{stats.get('count', 0)}</td>
            </tr>
"""
        
        html += """
        </table>
"""
        
        # Asset class analysis
        if asset_class_results:
            html += """
        <h2>Analiza Klas Aktywów</h2>
        <table>
            <tr>
                <th>Klasa Aktywów</th>
                <th>Średni Total Return</th>
                <th>Średni Sharpe Ratio</th>
                <th>Średni Win Rate</th>
                <th>Średni Profit Factor</th>
                <th>Średni Max Drawdown</th>
            </tr>
"""
            for asset_class, stats in asset_class_results.items():
                if asset_class == 'market_conditions':
                    continue
                if isinstance(stats, dict) and stats:
                    html += f"""
            <tr>
                <td><strong>{asset_class.upper()}</strong></td>
                <td class="{'positive' if stats.get('avg_total_return', 0) > 0 else 'negative'}">{stats.get('avg_total_return', 0):.2f}%</td>
                <td>{stats.get('avg_sharpe_ratio', 0):.2f}</td>
                <td>{stats.get('avg_win_rate', 0):.2f}%</td>
                <td>{stats.get('avg_profit_factor', 0):.2f}</td>
                <td class="negative">{stats.get('avg_max_drawdown', 0):.2f}%</td>
            </tr>
"""
            
            html += """
        </table>
"""
        
        # Detailed results table (first 50)
        html += f"""
        <h2>Szczegółowe Wyniki (pierwsze 50)</h2>
        <table>
            <tr>
                <th>Strategia</th>
                <th>Okres</th>
                <th>Threshold</th>
                <th>Total Return</th>
                <th>Sharpe</th>
                <th>Win Rate</th>
                <th>Profit Factor</th>
                <th>Max Drawdown</th>
            </tr>
"""
        
        successful_results = [r for r in detailed_results if r.get('status') == 'success']
        for result in successful_results[:50]:
            return_val = result.get('total_return', 0)
            return_class = 'positive' if return_val > 0 else 'negative'
            html += f"""
            <tr>
                <td>{result.get('strategy', 'N/A')}</td>
                <td>{result.get('period_name', 'N/A')}</td>
                <td>{result.get('signal_threshold', 'N/A')}</td>
                <td class="{return_class}">{return_val:.2f}%</td>
                <td>{result.get('sharpe_ratio', 0):.2f}</td>
                <td>{result.get('win_rate', 0):.2f}%</td>
                <td>{result.get('profit_factor', 0) if result.get('profit_factor') != float('inf') else '∞'}</td>
                <td class="negative">{result.get('max_drawdown', 0):.2f}%</td>
            </tr>
"""
        
        html += """
        </table>
        
        <h2>Equity Curve</h2>
        <div class="chart-placeholder">
            <p>Wykres equity curve można wygenerować używając danych z detailed_results[].equity_curve</p>
            <p>Zalecane: użycie biblioteki matplotlib lub plotly do wygenerowania wykresu</p>
        </div>
        
        <div class="footer">
            <p>Raport wygenerowany automatycznie przez system weryfikacji AI Recommendations</p>
            <p>Wszystkie dane są oparte na historycznych backtestach i mogą nie odzwierciedlać przyszłych wyników</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html
    
    def generate_text_report(
        self,
        verification_results: Dict[str, Any],
        asset_class_results: Optional[Dict[str, Any]] = None,
        output_file: str = 'verification_report.txt'
    ) -> str:
        """Generuj raport tekstowy"""
        summary = verification_results.get('summary', {})
        
        report = []
        report.append("="*60)
        report.append("RAPORT WERYFIKACJI AI RECOMMENDATIONS")
        report.append("="*60)
        report.append(f"Data wygenerowania: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        report.append("PODSUMOWANIE")
        report.append("-"*60)
        report.append(f"Średni Total Return: {summary.get('avg_total_return', 0):.2f}%")
        report.append(f"Średni Sharpe Ratio: {summary.get('avg_sharpe_ratio', 0):.2f}")
        report.append(f"Średni Win Rate: {summary.get('avg_win_rate', 0):.2f}%")
        report.append(f"Średni Profit Factor: {summary.get('avg_profit_factor', 0):.2f}")
        report.append(f"Średni Max Drawdown: {summary.get('avg_max_drawdown', 0):.2f}%")
        report.append(f"Średni Calmar Ratio: {summary.get('avg_calmar_ratio', 0):.2f}")
        report.append("")
        
        report.append("NAJLEPSZE WYNIKI")
        report.append("-"*60)
        report.append("Najlepszy Total Return:")
        best_return = summary.get('best_by_return', {})
        report.append(f"  Strategia: {best_return.get('strategy')}")
        report.append(f"  Okres: {best_return.get('period')}")
        report.append(f"  Threshold: {best_return.get('threshold')}")
        report.append(f"  Return: {best_return.get('return', 0):.2f}%")
        report.append(f"  Sharpe: {best_return.get('sharpe', 0):.2f}")
        report.append(f"  Win Rate: {best_return.get('win_rate', 0):.2f}%")
        report.append("")
        
        report.append("Najlepszy Sharpe Ratio:")
        best_sharpe = summary.get('best_by_sharpe', {})
        report.append(f"  Strategia: {best_sharpe.get('strategy')}")
        report.append(f"  Okres: {best_sharpe.get('period')}")
        report.append(f"  Threshold: {best_sharpe.get('threshold')}")
        report.append(f"  Return: {best_sharpe.get('return', 0):.2f}%")
        report.append(f"  Sharpe: {best_sharpe.get('sharpe', 0):.2f}")
        report.append(f"  Win Rate: {best_sharpe.get('win_rate', 0):.2f}%")
        report.append("")
        
        if asset_class_results:
            report.append("ANALIZA KLAS AKTYWÓW")
            report.append("-"*60)
            for asset_class, stats in asset_class_results.items():
                if asset_class == 'market_conditions':
                    continue
                if isinstance(stats, dict) and stats:
                    report.append(f"{asset_class.upper()}:")
                    report.append(f"  Total Return: {stats.get('avg_total_return', 0):.2f}%")
                    report.append(f"  Sharpe Ratio: {stats.get('avg_sharpe_ratio', 0):.2f}")
                    report.append(f"  Win Rate: {stats.get('avg_win_rate', 0):.2f}%")
                    report.append("")
        
        report.append("="*60)
        
        content = "\n".join(report)
        
        filepath = os.path.join(os.path.dirname(__file__), output_file)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Raport tekstowy zapisany do {filepath}")
        return filepath


def main():
    """Main function do generowania raportów"""
    generator = VerificationReportGenerator()
    
    # Wczytaj wyniki
    verification_results_file = os.path.join(os.path.dirname(__file__), 'verification_backtest_results.json')
    asset_class_results_file = os.path.join(os.path.dirname(__file__), 'asset_class_analysis_results.json')
    
    verification_results = None
    asset_class_results = None
    
    if os.path.exists(verification_results_file):
        with open(verification_results_file, 'r') as f:
            verification_results = json.load(f)
    
    if os.path.exists(asset_class_results_file):
        with open(asset_class_results_file, 'r') as f:
            asset_class_results = json.load(f)
    
    if verification_results:
        # Generuj raport HTML
        generator.generate_html_report(verification_results, asset_class_results)
        
        # Generuj raport tekstowy
        generator.generate_text_report(verification_results, asset_class_results)
    else:
        logger.warning("Brak wyników backtestów. Uruchom najpierw verification_backtest.py")


if __name__ == '__main__':
    main()



