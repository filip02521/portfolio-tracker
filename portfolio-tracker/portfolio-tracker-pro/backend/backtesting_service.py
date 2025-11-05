"""
Backtesting Service for Portfolio Tracker Pro
Allows users to test investment strategies on historical data
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)

class StrategyType(str, Enum):
    """Supported backtesting strategies"""
    BUY_AND_HOLD = "buy_and_hold"
    DOLLAR_COST_AVERAGING = "dca"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"


class BacktestEngine:
    """Engine for running backtests on historical data"""
    
    def __init__(self, market_data_service=None):
        """Initialize backtest engine"""
        self.logger = logging.getLogger(__name__)
        self.market_data_service = market_data_service
    
    def run_backtest(
        self,
        strategy: str,
        start_date: str,
        end_date: str,
        initial_capital: float,
        asset_symbol: str,
        asset_type: str = 'crypto',
        strategy_params: Optional[Dict] = None
    ) -> Dict:
        """
        Run a backtest with the specified strategy
        
        Args:
            strategy: Strategy type (buy_and_hold, dca, momentum, mean_reversion)
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            initial_capital: Starting capital in USD
            asset_symbol: Asset to trade
            asset_type: 'crypto' or 'stock'
            strategy_params: Additional strategy parameters
            
        Returns:
            Backtest results with performance metrics
        """
        self.logger.info(f"Running backtest: {strategy} from {start_date} to {end_date}")
        
        # TODO: Implement actual backtesting logic with real historical data
        # Current implementation returns mock results
        
        strategy_enum = StrategyType(strategy)
        
        if strategy_enum == StrategyType.BUY_AND_HOLD:
            return self._backtest_buy_and_hold(
                start_date, end_date, initial_capital, asset_symbol, asset_type
            )
        elif strategy_enum == StrategyType.DOLLAR_COST_AVERAGING:
            dca_frequency = (strategy_params or {}).get('frequency', 'monthly')
            return self._backtest_dca(
                start_date, end_date, initial_capital, asset_symbol, asset_type, dca_frequency
            )
        elif strategy_enum == StrategyType.MOMENTUM:
            lookback_days = (strategy_params or {}).get('lookback_days', 20)
            return self._backtest_momentum(
                start_date, end_date, initial_capital, asset_symbol, asset_type, lookback_days
            )
        elif strategy_enum == StrategyType.MEAN_REVERSION:
            mean_reversion_period = (strategy_params or {}).get('period', 20)
            return self._backtest_mean_reversion(
                start_date, end_date, initial_capital, asset_symbol, asset_type, mean_reversion_period
            )
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    def _backtest_buy_and_hold(
        self, start_date: str, end_date: str, initial_capital: float,
        asset_symbol: str, asset_type: str
    ) -> Dict:
        """Backtest buy and hold strategy with real historical data"""
        
        # Try to get real historical data
        if self.market_data_service:
            try:
                # Calculate days between dates
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                days_diff = (end_dt - start_dt).days
                
                # Get enough historical data to cover the period
                history = self.market_data_service.get_symbol_history(asset_symbol, days=max(days_diff + 10, 30))
                
                if history and len(history) >= 2:
                    # Filter history to date range
                    filtered_history = [
                        h for h in history
                        if start_date <= h.get('date', '') <= end_date
                    ]
                    
                    if len(filtered_history) >= 2:
                        return self._calculate_buy_hold_metrics(
                            filtered_history, initial_capital, asset_symbol
                        )
            except Exception as e:
                self.logger.warning(f"Error fetching real data for backtest: {e}")
        
        # Fallback to mock
        return {
            "strategy": "buy_and_hold",
            "start_date": start_date,
            "end_date": end_date,
            "initial_capital": initial_capital,
            "final_value": initial_capital * 1.25,
            "total_return": 0.25,
            "total_return_usd": initial_capital * 0.25,
            "cagr": 0.12,
            "sharpe_ratio": 1.5,
            "max_drawdown": 0.15,
            "volatility": 0.20,
            "win_rate": 0.60,
            "trades": [],
            "equity_curve": [],
            "status": "fallback"
        }
    
    def _calculate_buy_hold_metrics(
        self, history: List[Dict], initial_capital: float, symbol: str
    ) -> Dict:
        """Calculate actual buy and hold metrics from historical data"""
        try:
            # Sort by date
            sorted_history = sorted(history, key=lambda x: x.get('date', ''))
            
            # Initial investment
            initial_price = sorted_history[0]['close']
            shares = initial_capital / initial_price if initial_price > 0 else 0
            final_price = sorted_history[-1]['close']
            final_value = shares * final_price
            
            # Calculate daily returns
            returns = []
            for i in range(1, len(sorted_history)):
                prev_price = sorted_history[i-1]['close']
                curr_price = sorted_history[i]['close']
                if prev_price > 0:
                    daily_return = (curr_price - prev_price) / prev_price
                    returns.append(daily_return)
            
            # Metrics
            total_return = (final_value - initial_capital) / initial_capital
            num_days = len(sorted_history)
            num_years = num_days / 365.25
            cagr = ((final_value / initial_capital) ** (1 / num_years) - 1) if num_years > 0 and initial_capital > 0 else 0
            
            # Volatility (annualized)
            volatility = np.std(returns) * np.sqrt(252) if returns else 0
            
            # Sharpe ratio (assuming risk-free rate of 0 for simplicity)
            sharpe_ratio = (np.mean(returns) * 252) / volatility if volatility > 0 else 0
            
            # Max drawdown
            peak = initial_price
            max_dd = 0
            for point in sorted_history:
                price = point['close']
                if price > peak:
                    peak = price
                if peak > 0:
                    drawdown = (peak - price) / peak
                    max_dd = max(max_dd, drawdown)
            
            # Equity curve
            equity_curve = [
                {
                    "date": h['date'],
                    "value": (h['close'] / initial_price) * initial_capital
                }
                for h in sorted_history
            ]
            
            return {
                "strategy": "buy_and_hold",
                "start_date": sorted_history[0]['date'],
                "end_date": sorted_history[-1]['date'],
                "initial_capital": initial_capital,
                "final_value": float(final_value),
                "total_return": float(total_return),
                "total_return_usd": float(final_value - initial_capital),
                "cagr": float(cagr),
                "sharpe_ratio": float(sharpe_ratio),
                "max_drawdown": float(max_dd),
                "volatility": float(volatility),
                "win_rate": 0.60,  # Buy and hold always "wins" if total return > 0
                "trades": [{"type": "buy", "date": sorted_history[0]['date'], "price": initial_price, "amount": shares}],
                "equity_curve": equity_curve,
                "status": "success"
            }
        except Exception as e:
            self.logger.error(f"Error calculating buy and hold metrics: {e}")
            raise
    
    def _backtest_dca(
        self, start_date: str, end_date: str, initial_capital: float,
        asset_symbol: str, asset_type: str, frequency: str = 'monthly'
    ) -> Dict:
        """Backtest Dollar Cost Averaging strategy"""
        # Mock implementation
        return {
            "strategy": "dca",
            "frequency": frequency,
            "start_date": start_date,
            "end_date": end_date,
            "initial_capital": initial_capital,
            "final_value": initial_capital * 1.30,  # Mock 30% return
            "total_return": 0.30,
            "total_return_usd": initial_capital * 0.30,
            "cagr": 0.15,
            "sharpe_ratio": 1.8,
            "max_drawdown": 0.12,
            "volatility": 0.18,
            "win_rate": 0.65,
            "trades": [],
            "equity_curve": [],
            "status": "coming_soon"
        }
    
    def _backtest_momentum(
        self, start_date: str, end_date: str, initial_capital: float,
        asset_symbol: str, asset_type: str, lookback_days: int
    ) -> Dict:
        """Backtest momentum strategy"""
        # Mock implementation
        return {
            "strategy": "momentum",
            "lookback_days": lookback_days,
            "start_date": start_date,
            "end_date": end_date,
            "initial_capital": initial_capital,
            "final_value": initial_capital * 1.40,  # Mock 40% return
            "total_return": 0.40,
            "total_return_usd": initial_capital * 0.40,
            "cagr": 0.20,
            "sharpe_ratio": 2.0,
            "max_drawdown": 0.25,
            "volatility": 0.30,
            "win_rate": 0.70,
            "trades": [],
            "equity_curve": [],
            "status": "coming_soon"
        }
    
    def _backtest_mean_reversion(
        self, start_date: str, end_date: str, initial_capital: float,
        asset_symbol: str, asset_type: str, period: int
    ) -> Dict:
        """Backtest mean reversion strategy"""
        # Mock implementation
        return {
            "strategy": "mean_reversion",
            "period": period,
            "start_date": start_date,
            "end_date": end_date,
            "initial_capital": initial_capital,
            "final_value": initial_capital * 1.20,  # Mock 20% return
            "total_return": 0.20,
            "total_return_usd": initial_capital * 0.20,
            "cagr": 0.10,
            "sharpe_ratio": 1.2,
            "max_drawdown": 0.10,
            "volatility": 0.15,
            "win_rate": 0.55,
            "trades": [],
            "equity_curve": [],
            "status": "coming_soon"
        }
    
    def calculate_metrics(self, equity_curve: List[float]) -> Dict:
        """
        Calculate performance metrics from equity curve
        
        Args:
            equity_curve: List of portfolio values over time
            
        Returns:
            Performance metrics dictionary
        """
        if not equity_curve or len(equity_curve) < 2:
            return {
                "total_return": 0.0,
                "volatility": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0
            }
        
        # Calculate actual metric calculations
        returns = [(equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1] 
                   for i in range(1, len(equity_curve))]
        
        total_return = (equity_curve[-1] - equity_curve[0]) / equity_curve[0] if equity_curve[0] > 0 else 0
        
        # Volatility and Sharpe calculation
        # NOTE: This function doesn't specify timeframe, assumes returns are daily
        # If using weekly/monthly data, adjust annualization factor accordingly
        volatility = np.std(returns) * np.sqrt(252) if returns else 0  # Annualized for daily returns
        # Sharpe ratio (assuming risk-free rate of 0)
        # Sharpe = (Annualized Return) / (Annualized Volatility)
        annualized_return = np.mean(returns) * 252  # Annualized for daily returns
        sharpe_ratio = (annualized_return / volatility) if volatility > 0 else 0
        
        # Calculate max drawdown
        peak = equity_curve[0]
        max_drawdown = 0.0
        for value in equity_curve:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            max_drawdown = max(max_drawdown, drawdown)
        
        # Calculate CAGR
        num_days = len(equity_curve)
        num_years = num_days / 365.25
        cagr = (1 + total_return) ** (1 / num_years) - 1 if num_years > 0 and total_return > -1 else 0
        
        return {
            "total_return": total_return,
            "cagr": cagr,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "win_rate": 0.60  # Placeholder
        }
    
    def compare_strategies(
        self,
        strategies: List[Dict],
        start_date: str,
        end_date: str,
        initial_capital: float
    ) -> Dict:
        """
        Compare multiple strategies on the same historical period
        
        Args:
            strategies: List of strategy configurations
            start_date: Start date for backtest
            end_date: End date for backtest
            initial_capital: Starting capital
            
        Returns:
            Comparison results
        """
        self.logger.info(f"Comparing {len(strategies)} strategies")
        
        results = []
        for strategy in strategies:
            result = self.run_backtest(
                strategy=strategy.get('type'),
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                asset_symbol=strategy.get('asset', 'BTC'),
                asset_type=strategy.get('asset_type', 'crypto'),
                strategy_params=strategy.get('params')
            )
            results.append({
                "strategy_name": strategy.get('name', strategy.get('type')),
                "results": result
            })
        
        # Sort by total return
        results.sort(key=lambda x: x["results"]["total_return"], reverse=True)
        
        return {
            "comparison": results,
            "best_strategy": results[0] if results else None,
            "worst_strategy": results[-1] if results else None,
            "status": "coming_soon"
        }

