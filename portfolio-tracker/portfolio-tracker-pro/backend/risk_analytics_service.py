"""
Risk Analytics Service - VaR, CVaR, Rolling Sharpe
"""
from typing import List, Dict
from datetime import datetime
import math

class RiskAnalyticsService:
    def __init__(self):
        pass

    def compute_daily_returns(self, values: List[Dict]) -> List[float]:
        """Compute daily percentage returns from portfolio value history.
        Expects list of dicts with keys: 'timestamp', 'value_usd'
        Returns returns in percent (e.g., 0.5 for +0.5%).
        """
        if not values or len(values) < 2:
            return []
        # Sort by timestamp
        sorted_vals = sorted(values, key=lambda x: x['timestamp'])
        returns: List[float] = []
        prev = sorted_vals[0]['value_usd'] or 0
        for i in range(1, len(sorted_vals)):
            cur = sorted_vals[i]['value_usd'] or 0
            if prev > 0 and cur is not None:
                r = ((cur - prev) / prev) * 100.0
                returns.append(r)
            prev = cur
        return returns

    def calculate_var_cvar(self, returns_percent: List[float], confidence: float = 0.95) -> Dict:
        """
        Historical VaR/CVaR on returns (%). VaR is positive number meaning loss magnitude.
        confidence ∈ (0,1), e.g., 0.95.
        
        Uses conservative floor method for percentile calculation:
        - For 95% confidence (alpha=0.05), takes floor(alpha * n) percentile
        - This is more conservative than interpolation but valid for historical VaR
        - Example: n=100, alpha=0.05, k=floor(5)=5, takes 6th worst return (index 5)
        """
        if not returns_percent:
            return {"var": 0.0, "cvar": 0.0, "confidence": confidence, "sample": 0}

        # Sort ascending (losses first, i.e., negative returns first)
        sorted_ret = sorted(returns_percent)
        n = len(sorted_ret)
        
        # Percentile index for (1 - confidence) = alpha
        # For 95% confidence: alpha = 0.05, we want the 5th percentile (worst 5%)
        alpha = 1.0 - confidence
        
        # Conservative method: use floor (takes worst case)
        # This ensures we never underestimate risk
        # Alternative: use ceil or interpolation for more precise quantile
        k = max(0, min(n - 1, int(math.floor(alpha * n))))
        var_ret = sorted_ret[k]  # This is the return at the VaR threshold
        
        # CVaR (Conditional VaR): average of all returns worse than VaR threshold
        # Take tail from start (worst) up to and including k
        tail = sorted_ret[: (k + 1)] if k >= 0 else [var_ret]
        cvar_ret = sum(tail) / len(tail) if tail else var_ret
        
        # Report as positive losses (convert negative returns to positive loss values)
        # If var_ret is -3.5%, VaR should be 3.5% (positive loss)
        return {
            "var": max(0.0, -var_ret),      # VaR as positive loss percentage
            "cvar": max(0.0, -cvar_ret),    # CVaR as positive loss percentage
            "confidence": confidence,
            "sample": n,
        }

    def calculate_rolling_sharpe(self, returns_percent: List[float], window: int = 30, risk_free_daily: float = 0.0) -> Dict:
        """Rolling Sharpe ratio over a window (days). Returns series and latest value.
        returns_percent: daily returns in percent.
        risk_free_daily: daily risk-free rate in percent.
        """
        if not returns_percent or window < 2:
            return {"window": window, "latest": 0.0, "series": []}

        series = []
        for i in range(window, len(returns_percent) + 1):
            window_slice = returns_percent[i - window : i]
            # Excess returns
            excess = [(r - risk_free_daily) for r in window_slice]
            avg = sum(excess) / window
            # Std dev
            variance = sum((r - avg) ** 2 for r in excess) / (window - 1)
            std = math.sqrt(variance) if variance > 0 else 0.0
            sharpe = (avg / std) if std > 0 else 0.0
            series.append(sharpe)

        latest = series[-1] if series else 0.0
        return {"window": window, "latest": latest, "series": series}



