#!/usr/bin/env python3
"""
Benchmark analytics helper for comparing portfolio performance against major indices.
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple
import math
import numpy as np


class BenchmarkService:
    """
    Provides benchmark metrics (S&P 500, Dow Jones, Nasdaq 100) and
    comparative analytics against an optional portfolio equity curve.
    """

    BENCHMARKS = [
        {"symbol": "^GSPC", "name": "S&P 500"},
        {"symbol": "^DJI", "name": "Dow Jones Industrial Average"},
        {"symbol": "^NDX", "name": "Nasdaq 100"},
    ]

    def __init__(self, market_data_service):
        self.market_data_service = market_data_service

    def get_benchmark_summary(
        self,
        days: int = 365,
        equity_curve: Optional[List[Dict]] = None,
    ) -> List[Dict]:
        """
        Returns benchmark metrics and optional relative performance statistics.

        Args:
            days: Number of days to fetch history for benchmarks.
            equity_curve: Optional portfolio equity curve list of dicts:
                [{"date": "YYYY-MM-DD", "value": float}, ...]
        """
        portfolio_returns = None
        portfolio_total_return = None
        portfolio_dates = None

        if equity_curve:
            portfolio_dates, portfolio_prices = self._extract_curve(equity_curve)
            if len(portfolio_prices) >= 2:
                portfolio_returns = self._compute_returns(portfolio_prices)
                portfolio_total_return = (portfolio_prices[-1] / portfolio_prices[0]) - 1

        results = []
        for benchmark in self.BENCHMARKS:
            history = self._fetch_history(benchmark["symbol"], days)
            if not history or len(history[1]) < 2:
                continue

            bench_dates, bench_prices = history
            bench_returns = self._compute_returns(bench_prices)
            total_return = (bench_prices[-1] / bench_prices[0]) - 1
            annual_volatility = self._annualized_volatility(bench_returns)

            entry = {
                "symbol": benchmark["symbol"],
                "name": benchmark["name"],
                "total_return": round(total_return * 100, 2),
                "annual_volatility": round(annual_volatility * 100, 2) if annual_volatility is not None else None,
            }

            if portfolio_returns is not None and portfolio_total_return is not None:
                rel_metrics = self._compute_relative_metrics(
                    portfolio_dates,
                    portfolio_returns,
                    portfolio_total_return,
                    bench_dates,
                    bench_returns,
                    total_return,
                )
                entry.update(rel_metrics)

            results.append(entry)

        return results

    def _fetch_history(self, symbol: str, days: int) -> Optional[Tuple[List[str], List[float]]]:
        """
        Fetches symbol history using market_data_service.
        Returns tuple of (dates, prices).
        """
        try:
            history = self.market_data_service.get_symbol_history(symbol, days=days)
            if history is None:
                return None
            if isinstance(history, tuple):
                # Some services return (data, interval)
                history = history[0]
            dates = []
            prices = []
            for candle in history:
                if not isinstance(candle, dict):
                    continue
                date_str = candle.get("timestamp") or candle.get("date")
                price = candle.get("close") or candle.get("price")
                if not date_str or price is None:
                    continue
                try:
                    date = datetime.fromisoformat(str(date_str).replace("Z", "+00:00")).date()
                except ValueError:
                    try:
                        date = datetime.strptime(str(date_str), "%Y-%m-%d").date()
                    except ValueError:
                        continue
                try:
                    price = float(price)
                except (TypeError, ValueError):
                    continue
                if price <= 0:
                    continue
                dates.append(date.isoformat())
                prices.append(price)
            if len(prices) < 2:
                return None
            return dates, prices
        except Exception:
            return None

    def _extract_curve(self, curve: List[Dict]) -> Tuple[List[str], List[float]]:
        dates = []
        values = []
        for point in curve:
            date_str = point.get("date")
            value = point.get("value")
            if not date_str or value is None:
                continue
            try:
                date = datetime.fromisoformat(str(date_str)).date()
            except ValueError:
                try:
                    date = datetime.strptime(str(date_str), "%Y-%m-%d").date()
                except ValueError:
                    continue
            try:
                value = float(value)
            except (TypeError, ValueError):
                continue
            if value <= 0:
                continue
            dates.append(date.isoformat())
            values.append(value)
        return dates, values

    def _compute_returns(self, prices: List[float]) -> List[float]:
        returns = []
        for i in range(1, len(prices)):
            prev = prices[i - 1]
            curr = prices[i]
            if prev > 0:
                returns.append((curr / prev) - 1)
        return returns

    def _annualized_volatility(self, returns: List[float]) -> Optional[float]:
        if not returns:
            return None
        if len(returns) < 2:
            return abs(returns[0]) * math.sqrt(252)
        return float(np.std(returns, ddof=1)) * math.sqrt(252)

    def _compute_relative_metrics(
        self,
        portfolio_dates: List[str],
        portfolio_returns: List[float],
        portfolio_total_return: float,
        bench_dates: List[str],
        bench_returns: List[float],
        bench_total_return: float,
    ) -> Dict:
        # Align dates
        portfolio_ret_by_date = self._returns_by_date(portfolio_dates, portfolio_returns)
        bench_ret_by_date = self._returns_by_date(bench_dates, bench_returns)

        common_dates = sorted(set(portfolio_ret_by_date.keys()) & set(bench_ret_by_date.keys()))
        if len(common_dates) < 2:
            return {
                "relative_return": round((portfolio_total_return - bench_total_return) * 100, 2),
                "beta": None,
                "tracking_error": None,
                "alpha": round((portfolio_total_return - bench_total_return) * 100, 2),
                "correlation": None,
            }

        portfolio_aligned = np.array([portfolio_ret_by_date[d] for d in common_dates], dtype=float)
        bench_aligned = np.array([bench_ret_by_date[d] for d in common_dates], dtype=float)

        beta = None
        correlation = None
        tracking_error = None

        if np.var(bench_aligned, ddof=1) > 0:
            covariance = np.cov(portfolio_aligned, bench_aligned, ddof=1)[0][1]
            beta = covariance / np.var(bench_aligned, ddof=1)
        if len(portfolio_aligned) > 1 and np.std(portfolio_aligned, ddof=1) > 0 and np.std(bench_aligned, ddof=1) > 0:
            correlation = float(np.corrcoef(portfolio_aligned, bench_aligned)[0][1])
        diff = portfolio_aligned - bench_aligned
        if len(diff) > 1:
            tracking_error = float(np.std(diff, ddof=1) * math.sqrt(252))

        relative_return = portfolio_total_return - bench_total_return

        alpha = relative_return * 100

        return {
            "relative_return": round(relative_return * 100, 2),
            "alpha": round(alpha, 2),
            "beta": round(float(beta), 3) if beta is not None else None,
            "tracking_error": round(tracking_error * 100, 2) if tracking_error is not None else None,
            "correlation": round(correlation, 3) if correlation is not None else None,
        }

    def _returns_by_date(self, dates: List[str], returns: List[float]) -> Dict[str, float]:
        mapping: Dict[str, float] = {}
        for i in range(1, len(dates)):
            mapping[dates[i]] = returns[i - 1]
        return mapping






