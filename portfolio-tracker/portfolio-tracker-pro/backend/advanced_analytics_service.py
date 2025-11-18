"""
Advanced Analytics Service
Provides correlation matrix, risk-return analysis, efficient frontier, and beta calculations
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import math
import statistics
import numpy as np
from logging_config import get_logger

logger = get_logger(__name__)

class AdvancedAnalyticsService:
    """Service for advanced portfolio analytics"""
    
    def __init__(self, market_data_service=None, portfolio_tracker=None, portfolio_history=None):
        self.market_data_service = market_data_service
        self.portfolio_tracker = portfolio_tracker
        self.portfolio_history = portfolio_history
    
    def calculate_correlation_matrix(
        self, 
        assets: List[str], 
        days: int = 90
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate correlation matrix between assets
        
        Args:
            assets: List of asset symbols
            days: Number of days of history to use
            
        Returns:
            Correlation matrix as nested dict {symbol1: {symbol2: correlation}}
        """
        if not assets or len(assets) < 2:
            return {}
        
        correlation_matrix: Dict[str, Dict[str, float]] = {}
        asset_returns: Dict[str, List[float]] = {}
        
        # Get price history for each asset
        for symbol in assets:
            try:
                if self.market_data_service:
                    history = self.market_data_service.get_symbol_history(symbol, days)
                    if history and len(history) >= 10:
                        prices = [point.get('close', 0) for point in history if point.get('close')]
                        if len(prices) >= 10:
                            # Calculate returns
                            returns = []
                            for i in range(1, len(prices)):
                                if prices[i-1] > 0:
                                    ret = (prices[i] - prices[i-1]) / prices[i-1]
                                    returns.append(ret)
                            if len(returns) >= 2:
                                asset_returns[symbol] = returns
            except Exception as e:
                logger.warning(f"Failed to get history for {symbol}: {e}")
                continue
        
        if len(asset_returns) < 2:
            return {}
        
        # Calculate correlations
        symbols = sorted(asset_returns.keys())
        for symbol1 in symbols:
            correlation_matrix[symbol1] = {}
            returns1 = asset_returns[symbol1]
            
            for symbol2 in symbols:
                if symbol1 == symbol2:
                    correlation_matrix[symbol1][symbol2] = 1.0
                else:
                    returns2 = asset_returns.get(symbol2, [])
                    if len(returns2) < 2:
                        correlation_matrix[symbol1][symbol2] = 0.0
                        continue
                    
                    # Align returns by length
                    min_len = min(len(returns1), len(returns2))
                    if min_len < 2:
                        correlation_matrix[symbol1][symbol2] = 0.0
                        continue
                    
                    r1 = returns1[:min_len]
                    r2 = returns2[:min_len]
                    
                    # Calculate Pearson correlation
                    mean1 = statistics.mean(r1)
                    mean2 = statistics.mean(r2)
                    
                    numerator = sum((r1[i] - mean1) * (r2[i] - mean2) for i in range(min_len))
                    variance1 = sum((r1[i] - mean1) ** 2 for i in range(min_len))
                    variance2 = sum((r2[i] - mean2) ** 2 for i in range(min_len))
                    
                    denominator = math.sqrt(variance1 * variance2)
                    
                    if denominator == 0:
                        correlation = 0.0
                    else:
                        correlation = numerator / denominator
                        correlation = max(-1.0, min(1.0, correlation))
                    
                    correlation_matrix[symbol1][symbol2] = round(correlation, 4)
        
        return correlation_matrix
    
    def calculate_risk_return_scatter(
        self,
        assets: List[Dict],
        days: int = 90
    ) -> List[Dict[str, any]]:
        """
        Calculate risk-return scatter plot data for assets
        
        Args:
            assets: List of asset dicts with symbol, value_usd, etc.
            days: Number of days of history
            
        Returns:
            List of {symbol, return, risk, value, color} dicts
        """
        scatter_data = []
        
        for asset in assets:
            symbol = asset.get('symbol', '')
            if not symbol:
                continue
            
            try:
                if self.market_data_service:
                    history = self.market_data_service.get_symbol_history(symbol, days)
                    if history and len(history) >= 10:
                        prices = [point.get('close', 0) for point in history if point.get('close')]
                        if len(prices) >= 10:
                            # Calculate returns
                            returns = []
                            for i in range(1, len(prices)):
                                if prices[i-1] > 0:
                                    ret = (prices[i] - prices[i-1]) / prices[i-1]
                                    returns.append(ret)
                            
                            if len(returns) >= 2:
                                # Total return (annualized)
                                total_return = ((prices[-1] - prices[0]) / prices[0]) * 100 if prices[0] > 0 else 0
                                annualized_return = total_return * (365.25 / days)
                                
                                # Risk (volatility, annualized)
                                if len(returns) > 1:
                                    std_dev = statistics.stdev(returns)
                                    volatility = std_dev * math.sqrt(252) * 100  # Annualized in percentage
                                else:
                                    volatility = 0.0
                                
                                scatter_data.append({
                                    'symbol': symbol,
                                    'return': round(annualized_return, 2),
                                    'risk': round(volatility, 2),
                                    'value': asset.get('value_usd', 0),
                                    'type': asset.get('asset_type', 'unknown')
                                })
            except Exception as e:
                logger.warning(f"Failed to calculate risk-return for {symbol}: {e}")
                continue
        
        return scatter_data
    
    def calculate_beta_analysis(
        self,
        assets: List[Dict],
        benchmark: str = 'SPY',
        days: int = 90
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate beta for each asset relative to benchmark
        
        Args:
            assets: List of asset dicts
            benchmark: Benchmark symbol (default: SPY for S&P 500)
            days: Number of days of history
            
        Returns:
            Dict of {symbol: {beta, correlation, alpha}} for each asset
        """
        beta_analysis = {}
        
        # Get benchmark returns
        benchmark_returns = []
        benchmark_prices = []
        try:
            if self.market_data_service:
                benchmark_history = self.market_data_service.get_symbol_history(benchmark, days=days)
                if benchmark_history and len(benchmark_history) >= 10:
                    # Handle both tuple (data, interval) and list formats
                    if isinstance(benchmark_history, tuple):
                        benchmark_history = benchmark_history[0]
                    benchmark_prices = [point.get('close', 0) for point in benchmark_history if point.get('close')]
                    if len(benchmark_prices) >= 10:
                        for i in range(1, len(benchmark_prices)):
                            if benchmark_prices[i-1] > 0:
                                ret = (benchmark_prices[i] - benchmark_prices[i-1]) / benchmark_prices[i-1]
                                benchmark_returns.append(ret)
        except Exception as e:
            logger.warning(f"Failed to get benchmark history: {e}")
            return {}
        
        if len(benchmark_returns) < 10:
            return {}
        
        # Calculate beta for each asset
        for asset in assets:
            symbol = asset.get('symbol', '')
            if not symbol:
                continue
            
            try:
                if self.market_data_service:
                    history = self.market_data_service.get_symbol_history(symbol, days=days)
                    if history and len(history) >= 10:
                        # Handle both tuple (data, interval) and list formats
                        if isinstance(history, tuple):
                            history = history[0]
                        prices = [point.get('close', 0) for point in history if point.get('close')]
                        if len(prices) >= 10:
                            asset_returns = []
                            for i in range(1, len(prices)):
                                if prices[i-1] > 0:
                                    ret = (prices[i] - prices[i-1]) / prices[i-1]
                                    asset_returns.append(ret)
                            
                            if len(asset_returns) >= 10:
                                # Align returns
                                min_len = min(len(asset_returns), len(benchmark_returns))
                                asset_ret_aligned = asset_returns[:min_len]
                                bench_ret_aligned = benchmark_returns[:min_len]
                                
                                # Calculate correlation
                                mean_asset = statistics.mean(asset_ret_aligned)
                                mean_bench = statistics.mean(bench_ret_aligned)
                                
                                numerator = sum((asset_ret_aligned[i] - mean_asset) * (bench_ret_aligned[i] - mean_bench) 
                                              for i in range(min_len))
                                var_asset = sum((asset_ret_aligned[i] - mean_asset) ** 2 for i in range(min_len))
                                var_bench = sum((bench_ret_aligned[i] - mean_bench) ** 2 for i in range(min_len))
                                
                                denominator = math.sqrt(var_asset * var_bench)
                                correlation = (numerator / denominator) if denominator > 0 else 0.0
                                correlation = max(-1.0, min(1.0, correlation))
                                
                                # Calculate beta: beta = Cov(asset, benchmark) / Var(benchmark)
                                if var_bench > 0:
                                    covariance = numerator / min_len
                                    beta = covariance / (var_bench / min_len)
                                else:
                                    beta = 1.0
                                
                                # Calculate alpha (simplified: excess return)
                                asset_total_return = ((prices[-1] - prices[0]) / prices[0]) if prices[0] > 0 else 0
                                bench_total_return = ((benchmark_prices[-1] - benchmark_prices[0]) / benchmark_prices[0]) if benchmark_prices and benchmark_prices[0] > 0 else 0
                                alpha = (asset_total_return - bench_total_return) * 100
                                
                                beta_analysis[symbol] = {
                                    'beta': round(beta, 3),
                                    'correlation': round(correlation, 3),
                                    'alpha': round(alpha, 2)
                                }
            except Exception as e:
                logger.warning(f"Failed to calculate beta for {symbol}: {e}")
                continue
        
        return beta_analysis
    
    def calculate_efficient_frontier(
        self,
        assets: List[Dict],
        num_portfolios: int = 30,  # Reduced default from 50 to 30 for better performance
        days: int = 90
    ) -> List[Dict[str, any]]:
        """
        Calculate efficient frontier points (simplified version)
        
        Args:
            assets: List of asset dicts
            num_portfolios: Number of portfolio combinations to generate
            days: Number of days of history
            
        Returns:
            List of {return, risk, sharpe} dicts representing efficient frontier
        """
        # This is a simplified efficient frontier calculation
        # For full MPT, would need covariance matrix and optimization
        
        if len(assets) < 2:
            return []
        
        # Get returns for all assets
        asset_returns_data: Dict[str, List[float]] = {}
        for asset in assets:
            symbol = asset.get('symbol', '')
            if not symbol:
                continue
            
            try:
                if self.market_data_service:
                    history = self.market_data_service.get_symbol_history(symbol, days=days)
                    if history and len(history) >= 10:
                        # Handle both tuple (data, interval) and list formats
                        if isinstance(history, tuple):
                            history = history[0]
                        prices = [point.get('close', 0) for point in history if point.get('close')]
                        if len(prices) >= 10:
                            returns = []
                            for i in range(1, len(prices)):
                                if prices[i-1] > 0:
                                    ret = (prices[i] - prices[i-1]) / prices[i-1]
                                    returns.append(ret)
                            if len(returns) >= 10:
                                asset_returns_data[symbol] = returns
            except Exception:
                continue
        
        if len(asset_returns_data) < 2:
            return []
        
        # Generate random portfolio weights and calculate risk/return
        frontier_points = []
        symbols = list(asset_returns_data.keys())
        
        for _ in range(num_portfolios):
            # Generate random weights (simplified - doesn't ensure they sum to 1)
            weights = np.random.dirichlet(np.ones(len(symbols)))
            
            # Calculate portfolio return and risk
            portfolio_returns = []
            min_len = min(len(asset_returns_data[s]) for s in symbols)
            
            for i in range(min_len):
                portfolio_return = sum(weights[j] * asset_returns_data[symbols[j]][i] for j in range(len(symbols)))
                portfolio_returns.append(portfolio_return)
            
            if len(portfolio_returns) >= 2:
                # Annualized return
                mean_return = statistics.mean(portfolio_returns)
                annualized_return = mean_return * 252 * 100  # Convert to percentage
                
                # Annualized volatility (risk)
                std_dev = statistics.stdev(portfolio_returns)
                annualized_vol = std_dev * math.sqrt(252) * 100
                
                # Sharpe ratio (assuming 0% risk-free rate)
                sharpe = (annualized_return / annualized_vol) if annualized_vol > 0 else 0.0
                
                frontier_points.append({
                    'return': round(annualized_return, 2),
                    'risk': round(annualized_vol, 2),
                    'sharpe': round(sharpe, 3)
                })
        
        # Sort by risk
        frontier_points.sort(key=lambda x: x['risk'])
        
        return frontier_points

