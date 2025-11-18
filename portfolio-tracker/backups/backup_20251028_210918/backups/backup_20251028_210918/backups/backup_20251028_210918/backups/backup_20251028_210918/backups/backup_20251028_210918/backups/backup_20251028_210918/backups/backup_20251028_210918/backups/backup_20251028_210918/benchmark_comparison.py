"""
Benchmark Comparison System
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os

class BenchmarkComparison:
    """System porównania z benchmarkami rynkowymi"""
    
    def __init__(self):
        self.benchmarks = {
            'S&P 500': '^GSPC',
            'NASDAQ': '^IXIC', 
            'DOW': '^DJI',
            'Bitcoin': 'BTC-USD',
            'Ethereum': 'ETH-USD',
            'Gold': 'GC=F',
            'WIG20': 'WIG20.WA'  # Polish index
        }
    
    def get_benchmark_data(self, symbol: str, period: str = '1y') -> Optional[pd.DataFrame]:
        """Get benchmark data from Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            return data
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return None
    
    def calculate_returns(self, data: pd.DataFrame) -> Dict:
        """Calculate various return metrics"""
        if data.empty:
            return {}
        
        # Get first and last prices
        first_price = data['Close'].iloc[0]
        last_price = data['Close'].iloc[-1]
        
        # Calculate total return
        total_return = (last_price - first_price) / first_price * 100
        
        # Calculate daily returns
        daily_returns = data['Close'].pct_change().dropna()
        
        # Calculate volatility (annualized)
        volatility = daily_returns.std() * (252 ** 0.5) * 100
        
        # Calculate max drawdown
        cumulative = (1 + daily_returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min() * 100
        
        # Calculate Sharpe ratio (assuming 0% risk-free rate)
        sharpe_ratio = (daily_returns.mean() * 252) / (daily_returns.std() * (252 ** 0.5))
        
        return {
            'total_return': total_return,
            'volatility': volatility,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'current_price': last_price,
            'first_price': first_price
        }
    
    def compare_portfolio_to_benchmarks(self, portfolio_value_history: List[Dict], 
                                      current_portfolio_value: float) -> Dict:
        """Compare portfolio performance to benchmarks"""
        
        if not portfolio_value_history:
            return {}
        
        # Convert portfolio history to DataFrame
        portfolio_df = pd.DataFrame(portfolio_value_history)
        portfolio_df['date'] = pd.to_datetime(portfolio_df['date'])
        portfolio_df = portfolio_df.set_index('date')
        
        # Calculate portfolio returns
        portfolio_first_value = portfolio_df['value'].iloc[0]
        portfolio_total_return = (current_portfolio_value - portfolio_first_value) / portfolio_first_value * 100
        
        # Calculate portfolio volatility
        portfolio_daily_returns = portfolio_df['value'].pct_change().dropna()
        portfolio_volatility = portfolio_daily_returns.std() * (252 ** 0.5) * 100
        
        # Calculate portfolio Sharpe ratio
        portfolio_sharpe = (portfolio_daily_returns.mean() * 252) / (portfolio_daily_returns.std() * (252 ** 0.5))
        
        # Calculate portfolio max drawdown
        portfolio_cumulative = (1 + portfolio_daily_returns).cumprod()
        portfolio_running_max = portfolio_cumulative.expanding().max()
        portfolio_drawdown = (portfolio_cumulative - portfolio_running_max) / portfolio_running_max
        portfolio_max_drawdown = portfolio_drawdown.min() * 100
        
        portfolio_metrics = {
            'total_return': portfolio_total_return,
            'volatility': portfolio_volatility,
            'max_drawdown': portfolio_max_drawdown,
            'sharpe_ratio': portfolio_sharpe
        }
        
        # Get benchmark data
        benchmark_results = {}
        for name, symbol in self.benchmarks.items():
            data = self.get_benchmark_data(symbol, '1y')
            if data is not None:
                metrics = self.calculate_returns(data)
                benchmark_results[name] = metrics
        
        # Calculate outperformance
        outperformance = {}
        for benchmark_name, metrics in benchmark_results.items():
            if 'total_return' in metrics:
                outperformance[benchmark_name] = portfolio_total_return - metrics['total_return']
        
        return {
            'portfolio_metrics': portfolio_metrics,
            'benchmark_results': benchmark_results,
            'outperformance': outperformance
        }
    
    def get_benchmark_recommendations(self, comparison_results: Dict) -> List[str]:
        """Get recommendations based on benchmark comparison"""
        recommendations = []
        
        if not comparison_results:
            return recommendations
        
        portfolio_metrics = comparison_results.get('portfolio_metrics', {})
        outperformance = comparison_results.get('outperformance', {})
        
        # Analyze outperformance
        positive_outperformance = [name for name, value in outperformance.items() if value > 0]
        negative_outperformance = [name for name, value in outperformance.items() if value < 0]
        
        if len(positive_outperformance) > len(negative_outperformance):
            recommendations.append("🎉 Portfolio przewyższa większość benchmarków!")
            recommendations.append("Rozważ zwiększenie ekspozycji na rynek")
        elif len(negative_outperformance) > len(positive_outperformance):
            recommendations.append("📉 Portfolio za benchmarkami")
            recommendations.append("Przeanalizuj strategię inwestycyjną")
            recommendations.append("Rozważ dywersyfikację")
        
        # Analyze volatility
        portfolio_volatility = portfolio_metrics.get('volatility', 0)
        if portfolio_volatility > 30:
            recommendations.append("⚠️ Wysoka zmienność portfolio")
            recommendations.append("Rozważ dodanie stabilnych aktywów")
        elif portfolio_volatility < 10:
            recommendations.append("✅ Niska zmienność portfolio")
            recommendations.append("Rozważ zwiększenie ryzyka dla wyższych zwrotów")
        
        # Analyze Sharpe ratio
        portfolio_sharpe = portfolio_metrics.get('sharpe_ratio', 0)
        if portfolio_sharpe > 1.0:
            recommendations.append("🚀 Doskonały stosunek zwrotu do ryzyka")
        elif portfolio_sharpe < 0.5:
            recommendations.append("📊 Niski stosunek zwrotu do ryzyka")
            recommendations.append("Optymalizuj alokację aktywów")
        
        return recommendations
    
    def generate_comparison_report(self, comparison_results: Dict) -> str:
        """Generate a text report of the comparison"""
        if not comparison_results:
            return "Brak danych do porównania"
        
        report = "📊 RAPORT PORÓWNANIA Z BENCHMARKAMI\n\n"
        
        portfolio_metrics = comparison_results.get('portfolio_metrics', {})
        outperformance = comparison_results.get('outperformance', {})
        
        # Portfolio summary
        report += "PORTFOLIO:\n"
        report += f"• Całkowity zwrot: {portfolio_metrics.get('total_return', 0):.2f}%\n"
        report += f"• Zmienność: {portfolio_metrics.get('volatility', 0):.2f}%\n"
        report += f"• Max spadek: {portfolio_metrics.get('max_drawdown', 0):.2f}%\n"
        report += f"• Sharpe ratio: {portfolio_metrics.get('sharpe_ratio', 0):.2f}\n\n"
        
        # Outperformance
        report += "PRZEWAGA NAD BENCHMARKAMI:\n"
        for benchmark, value in outperformance.items():
            if value > 0:
                report += f"• {benchmark}: +{value:.2f}%\n"
            else:
                report += f"• {benchmark}: {value:.2f}%\n"
        
        return report

# Example usage
if __name__ == "__main__":
    benchmark = BenchmarkComparison()
    
    # Test with sample portfolio data
    sample_portfolio_history = [
        {'date': '2024-01-01', 'value': 10000},
        {'date': '2024-02-01', 'value': 10500},
        {'date': '2024-03-01', 'value': 11000},
        {'date': '2024-04-01', 'value': 10800},
        {'date': '2024-05-01', 'value': 11500},
        {'date': '2024-06-01', 'value': 12000},
        {'date': '2024-07-01', 'value': 12500},
        {'date': '2024-08-01', 'value': 12200},
        {'date': '2024-09-01', 'value': 12800},
        {'date': '2024-10-01', 'value': 13000}
    ]
    
    current_value = 13000
    
    # Run comparison
    results = benchmark.compare_portfolio_to_benchmarks(sample_portfolio_history, current_value)
    
    print("Benchmark Comparison Results:")
    print(f"Portfolio return: {results.get('portfolio_metrics', {}).get('total_return', 0):.2f}%")
    
    outperformance = results.get('outperformance', {})
    for benchmark_name, value in outperformance.items():
        print(f"vs {benchmark_name}: {value:+.2f}%")
    
    # Get recommendations
    recommendations = benchmark.get_benchmark_recommendations(results)
    print("\nRecommendations:")
    for rec in recommendations:
        print(f"• {rec}")
    
    # Generate report
    report = benchmark.generate_comparison_report(results)
    print(f"\n{report}")
