"""
Smart Portfolio Insights Service
Provides intelligent analysis and recommendations for portfolio optimization
"""
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import math
import statistics

class SmartInsightsService:
    """Service for generating smart portfolio insights"""
    
    def __init__(self, market_data_service=None, portfolio_history=None):
        # Risk thresholds
        self.CONCENTRATION_RISK_THRESHOLD = 0.4  # 40% - warning
        self.HIGH_CONCENTRATION_THRESHOLD = 0.5  # 50% - critical
        self.MIN_DIVERSIFICATION_ASSETS = 5  # Minimum recommended assets
        self.HIGH_VOLATILITY_THRESHOLD = 50.0  # Annualized volatility > 50%
        self.HIGH_CORRELATION_THRESHOLD = 0.8  # Correlation > 0.8
        self.HIGH_DRAWDOWN_THRESHOLD = 20.0  # Drawdown > 20%
        # Safety limits for expensive risk calculations
        from os import getenv
        self.MAX_RISK_SYMBOLS = int(getenv("INSIGHTS_MAX_RISK_SYMBOLS", "25"))
        self.MAX_RISK_SECONDS = float(getenv("INSIGHTS_MAX_SECONDS", "8.0"))
        self.market_data_service = market_data_service
        self.portfolio_history = portfolio_history
        
    def analyze_portfolio(self, portfolios: List[Dict], transaction_history: List[Dict]) -> Dict:
        """
        Analyze portfolio and generate insights
        
        Args:
            portfolios: List of portfolio data from exchanges
            transaction_history: List of historical transactions
            
        Returns:
            Dictionary with insights, alerts, and recommendations
        """
        if not portfolios:
            return {
                "insights": [],
                "alerts": [],
                "recommendations": [],
                "health_score": 0,
                "risk_level": "Unknown"
            }
        
        insights = []
        alerts = []
        recommendations = []
        
        # Calculate total portfolio value
        total_value = sum(p.get('total_value_usdt', 0) for p in portfolios)
        
        if total_value == 0:
            return {
                "insights": [{"type": "info", "message": "Portfolio is empty. Start by adding your first investment."}],
                "alerts": [],
                "recommendations": [],
                "health_score": 0,
                "risk_level": "Empty"
            }
        
        # 1. Asset Concentration Analysis
        concentration_insights = self._analyze_concentration(portfolios, total_value)
        insights.extend(concentration_insights['insights'])
        alerts.extend(concentration_insights['alerts'])
        recommendations.extend(concentration_insights['recommendations'])
        
        # 2. Best/Worst Performers
        performers = self._analyze_performers(portfolios, transaction_history)
        insights.extend(performers['insights'])
        
        # 3. Diversification Analysis
        diversification = self._analyze_diversification(portfolios, total_value)
        insights.extend(diversification['insights'])
        alerts.extend(diversification.get('alerts', []))
        recommendations.extend(diversification['recommendations'])
        
        # 4. Exchange Distribution
        exchange_dist = self._analyze_exchange_distribution(portfolios, total_value)
        insights.extend(exchange_dist['insights'])
        
        # 5. Rebalancing Suggestions
        rebalancing = self._suggest_rebalancing(portfolios, total_value)
        recommendations.extend(rebalancing)
        
        # Calculate overall health score
        health_score = self._calculate_health_score(
            concentration_insights,
            diversification,
            exchange_dist
        )
        
        # Determine risk level
        risk_level = self._determine_risk_level(health_score, concentration_insights)
        
        return {
            "insights": insights,
            "alerts": alerts,
            "recommendations": recommendations,
            "health_score": health_score,
            "risk_level": risk_level,
            "total_value": total_value,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _analyze_concentration(self, portfolios: List[Dict], total_value: float) -> Dict:
        """Analyze asset concentration risk"""
        insights = []
        alerts = []
        recommendations = []
        
        # Get all assets with their values
        assets = {}
        for portfolio in portfolios:
            for balance in portfolio.get('balances', []):
                asset = balance.get('asset', '')
                value = balance.get('value_usdt', 0)
                if value > 0:
                    if asset not in assets:
                        assets[asset] = 0
                    assets[asset] += value
        
        if not assets:
            return {"insights": [], "alerts": [], "recommendations": []}
        
        # Find top asset
        sorted_assets = sorted(assets.items(), key=lambda x: x[1], reverse=True)
        top_asset, top_value = sorted_assets[0]
        top_percentage = (top_value / total_value) * 100
        
        # Concentration insights
        if top_percentage >= self.HIGH_CONCENTRATION_THRESHOLD * 100:
            alerts.append({
                "type": "critical",
                "title": "High Concentration Risk",
                "message": f"{top_asset} accounts for {top_percentage:.1f}% of your portfolio. This creates significant risk.",
                "severity": "high"
            })
            recommendations.append({
                "type": "rebalance",
                "priority": "high",
                "action": f"Consider reducing {top_asset} exposure to below 40%",
                "details": f"Sell approximately ${(top_value - total_value * 0.4):,.2f} worth of {top_asset}"
            })
        elif top_percentage >= self.CONCENTRATION_RISK_THRESHOLD * 100:
            alerts.append({
                "type": "warning",
                "title": "Moderate Concentration Risk",
                "message": f"{top_asset} represents {top_percentage:.1f}% of your portfolio. Consider diversification.",
                "severity": "medium"
            })
            recommendations.append({
                "type": "rebalance",
                "priority": "medium",
                "action": f"Consider diversifying away from {top_asset}",
                "details": f"Current: {top_percentage:.1f}%. Recommended: < 40%"
            })
        
        insights.append({
            "type": "concentration",
            "title": "Top Asset",
            "message": f"{top_asset} represents {top_percentage:.1f}% of your portfolio",
            "value": top_percentage,
            "asset": top_asset
        })
        
        return {"insights": insights, "alerts": alerts, "recommendations": recommendations}
    
    def _analyze_performers(self, portfolios: List[Dict], transaction_history: List[Dict]) -> Dict:
        """Analyze best and worst performing assets"""
        insights = []
        
        # Calculate P&L per asset from transactions
        asset_pnl = {}
        asset_costs = {}
        
        for tx in transaction_history:
            asset = tx.get('asset', '')
            tx_type = tx.get('type', '').lower()
            amount = tx.get('amount', 0)
            price = tx.get('price_usd', 0)
            
            if tx_type == 'buy':
                if asset not in asset_costs:
                    asset_costs[asset] = {'amount': 0, 'cost': 0}
                asset_costs[asset]['amount'] += amount
                asset_costs[asset]['cost'] += amount * price
            elif tx_type == 'sell':
                # For simplicity, calculate realized P&L
                if asset in asset_costs and asset_costs[asset]['amount'] > 0:
                    avg_cost = asset_costs[asset]['cost'] / asset_costs[asset]['amount']
                    pnl = (price - avg_cost) * amount
                    if asset not in asset_pnl:
                        asset_pnl[asset] = 0
                    asset_pnl[asset] += pnl
        
        # Get current values
        current_values = {}
        for portfolio in portfolios:
            for balance in portfolio.get('balances', []):
                asset = balance.get('asset', '')
                value = balance.get('value_usdt', 0)
                if value > 0:
                    if asset not in current_values:
                        current_values[asset] = 0
                    current_values[asset] += value
        
        # Calculate unrealized P&L (if we have cost basis)
        # For now, focus on realized P&L from transactions
        
        if asset_pnl:
            sorted_pnl = sorted(asset_pnl.items(), key=lambda x: x[1], reverse=True)
            
            best_asset, best_pnl = sorted_pnl[0]
            worst_asset, worst_pnl = sorted_pnl[-1]
            
            if best_pnl > 0:
                insights.append({
                    "type": "performance",
                    "title": "Best Performer",
                    "message": f"{best_asset} generated ${best_pnl:,.2f} in realized profits",
                    "value": best_pnl,
                    "asset": best_asset
                })
            
            if worst_pnl < 0:
                insights.append({
                    "type": "performance",
                    "title": "Worst Performer",
                    "message": f"{worst_asset} realized losses of ${abs(worst_pnl):,.2f}",
                    "value": worst_pnl,
                    "asset": worst_asset
                })
        
        # Add top holdings by value
        if current_values:
            sorted_values = sorted(current_values.items(), key=lambda x: x[1], reverse=True)
            if len(sorted_values) >= 3:
                insights.append({
                    "type": "holdings",
                    "title": "Top 3 Holdings",
                    "message": f"Your largest positions: {', '.join([f'{a} (${v:,.0f})' for a, v in sorted_values[:3]])}",
                    "data": sorted_values[:3]
                })
        
        return {"insights": insights}
    
    def _analyze_diversification(self, portfolios: List[Dict], total_value: float) -> Dict:
        """Analyze portfolio diversification"""
        insights = []
        recommendations = []
        
        # Count unique assets
        unique_assets = set()
        for portfolio in portfolios:
            for balance in portfolio.get('balances', []):
                if balance.get('value_usdt', 0) > 0:
                    unique_assets.add(balance.get('asset', ''))
        
        asset_count = len(unique_assets)
        
        alerts_data = []
        if asset_count < self.MIN_DIVERSIFICATION_ASSETS:
            alerts_data = [{
                "type": "warning",
                "title": "Low Diversification",
                "message": f"You hold only {asset_count} asset(s). Consider adding more assets to reduce risk.",
                "severity": "medium"
            }]
            recommendations.append({
                "type": "diversification",
                "priority": "medium",
                "action": f"Add {self.MIN_DIVERSIFICATION_ASSETS - asset_count} more assets to improve diversification",
                "details": "A well-diversified portfolio typically has 5-10 different assets"
            })
        else:
            insights.append({
                "type": "diversification",
                "title": "Diversification Status",
                "message": f"Good diversification: {asset_count} different assets",
                "value": asset_count
            })
        
        # Calculate Herfindahl-Hirschman Index (HHI) for concentration
        assets_values = {}
        for portfolio in portfolios:
            for balance in portfolio.get('balances', []):
                asset = balance.get('asset', '')
                value = balance.get('value_usdt', 0)
                if value > 0:
                    if asset not in assets_values:
                        assets_values[asset] = 0
                    assets_values[asset] += value
        
        if assets_values and total_value > 0:
            # HHI = sum of squared market shares
            hhi = sum((v / total_value) ** 2 for v in assets_values.values())
            hhi_percent = hhi * 100
            
            insights.append({
                "type": "concentration_index",
                "title": "Concentration Index (HHI)",
                "message": f"HHI: {hhi_percent:.1f} (lower is better, < 25 is ideal)",
                "value": hhi_percent,
                "status": "good" if hhi < 0.25 else "warning" if hhi < 0.35 else "critical"
            })
        
        return {
            "insights": insights,
            "alerts": alerts_data,
            "recommendations": recommendations
        }
    
    def _analyze_exchange_distribution(self, portfolios: List[Dict], total_value: float) -> Dict:
        """Analyze distribution across exchanges"""
        insights = []
        
        exchange_values = {}
        for portfolio in portfolios:
            exchange = portfolio.get('exchange', '')
            value = portfolio.get('total_value_usdt', 0)
            if value > 0:
                if exchange not in exchange_values:
                    exchange_values[exchange] = 0
                exchange_values[exchange] += value
        
        if len(exchange_values) > 1:
            insights.append({
                "type": "exchange_diversity",
                "title": "Exchange Distribution",
                "message": f"Assets spread across {len(exchange_values)} exchanges: {', '.join(exchange_values.keys())}",
                "value": len(exchange_values)
            })
        else:
            insights.append({
                "type": "exchange_diversity",
                "title": "Exchange Distribution",
                "message": f"Assets held on {len(exchange_values)} exchange(s)",
                "value": len(exchange_values)
            })
        
        return {"insights": insights}
    
    def _suggest_rebalancing(self, portfolios: List[Dict], total_value: float) -> List[Dict]:
        """Generate rebalancing suggestions"""
        recommendations = []
        
        if total_value == 0:
            return recommendations
        
        # Get asset distribution
        assets_values = {}
        for portfolio in portfolios:
            for balance in portfolio.get('balances', []):
                asset = balance.get('asset', '')
                value = balance.get('value_usdt', 0)
                if value > 0:
                    if asset not in assets_values:
                        assets_values[asset] = 0
                    assets_values[asset] += value
        
        if not assets_values:
            return recommendations
        
        # Find assets that are over-concentrated
        for asset, value in assets_values.items():
            percentage = (value / total_value) * 100
            
            if percentage > self.HIGH_CONCENTRATION_THRESHOLD * 100:
                target_value = total_value * 0.35  # Target 35% max
                reduction_amount = value - target_value
                
                recommendations.append({
                    "type": "rebalance",
                    "priority": "high",
                    "action": f"Reduce {asset} allocation",
                    "details": f"Sell ${reduction_amount:,.2f} of {asset} (from {percentage:.1f}% to ~35%)",
                    "asset": asset,
                    "current_percentage": percentage,
                    "target_percentage": 35
                })
        
        # Suggest adding more assets if portfolio is too concentrated
        if len(assets_values) < 3:
            recommendations.append({
                "type": "rebalance",
                "priority": "medium",
                "action": "Diversify portfolio",
                "details": f"Consider adding {3 - len(assets_values)} more asset(s) to improve diversification",
                "current_assets": len(assets_values),
                "recommended_assets": 5
            })
        
        return recommendations
    
    def _calculate_health_score(self, concentration: Dict, diversification: Dict, exchange_dist: Dict) -> int:
        """Calculate portfolio health score (0-100)"""
        score = 100
        
        # Penalize for high concentration
        concentration_alerts = [a for a in concentration.get('alerts', []) if a.get('severity') == 'high']
        if concentration_alerts:
            score -= 20
        
        # Penalize for low diversification
        diversification_recs = diversification.get('recommendations', [])
        if diversification_recs:
            score -= 15
        
        # Bonus for exchange diversity
        exchange_insights = exchange_dist.get('insights', [])
        if len(exchange_insights) > 0:
            exchange_count = exchange_insights[0].get('value', 1)
            if exchange_count >= 2:
                score += 5
        
        return max(0, min(100, score))
    
    def _determine_risk_level(self, health_score: int, concentration: Dict) -> str:
        """Determine overall risk level"""
        critical_alerts = [a for a in concentration.get('alerts', []) if a.get('severity') == 'high']
        
        if health_score >= 80 and not critical_alerts:
            return "Low"
        elif health_score >= 60:
            return "Medium"
        elif health_score >= 40:
            return "High"
        else:
            return "Very High"
    
    def detect_risk_alerts(
        self, 
        portfolios: List[Dict], 
        days: int = 90
    ) -> Dict:
        """
        Detect real-time risk alerts for portfolio
        
        Args:
            portfolios: List of portfolio data from exchanges
            days: Number of days to analyze for volatility/drawdown
            
        Returns:
            Dictionary with risk alerts categorized by type
        """
        alerts = {
            "concentration": [],
            "correlation": [],
            "volatility": [],
            "drawdown": [],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if not portfolios:
            return alerts
        
        # Calculate total portfolio value
        total_value = sum(p.get('total_value_usdt', 0) for p in portfolios)
        if total_value == 0:
            return alerts
        
        # Get all assets with their values
        assets = {}
        for portfolio in portfolios:
            for balance in portfolio.get('balances', []):
                asset = balance.get('asset', '')
                value = balance.get('value_usdt', 0) or balance.get('value_usd', 0)
                if asset and value > 0:
                    if asset not in assets:
                        assets[asset] = 0
                    assets[asset] += value
        
        if not assets:
            return alerts
        
        # 1. Concentration Risk Alerts
        alerts["concentration"] = self._detect_concentration_risks(assets, total_value)
        
        # 2. Correlation Risk Alerts (if market_data_service available)
        if self.market_data_service and len(assets) >= 2:
            alerts["correlation"] = self._detect_correlation_risks(list(assets.keys()), days)
        
        # 3. Volatility Risk Alerts
        if self.market_data_service:
            alerts["volatility"] = self._detect_volatility_risks(assets, days)
        
        # 4. Drawdown Risk Alerts
        if self.portfolio_history:
            alerts["drawdown"] = self._detect_drawdown_risks(days)
        
        return alerts

    def generate_rebalancing_suggestions(
        self,
        portfolios: List[Dict],
        threshold: float = 5.0,
        max_suggestions: int = 5,
        target_allocation: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Generate automatic rebalancing suggestions based on allocation drift.

        Args:
            portfolios: List of portfolio data from exchanges
            threshold: Minimum drift in percentage points to trigger suggestion (e.g. 5.0)
            max_suggestions: Maximum number of suggestions to return
            target_allocation: Optional target allocation per symbol (in %, sum ~100). If not provided,
                               a simple equal-weight target is used.

        Returns:
            Dict with current allocation, target allocation and list of suggestions
        """
        # Defensive defaults
        try:
            threshold = float(threshold)
        except (TypeError, ValueError):
            threshold = 5.0

        try:
            max_suggestions = int(max_suggestions)
        except (TypeError, ValueError):
            max_suggestions = 5

        if not portfolios:
            return {
                "current_allocation": {},
                "target_allocation": {},
                "suggestions": [],
                "total_value": 0.0,
            }

        # Calculate total portfolio value
        total_value = sum(p.get("total_value_usdt", 0) for p in portfolios)
        if total_value <= 0:
            return {
                "current_allocation": {},
                "target_allocation": {},
                "suggestions": [],
                "total_value": 0.0,
            }

        # Aggregate asset values
        asset_values: Dict[str, float] = {}
        for portfolio in portfolios:
            for balance in portfolio.get("balances", []):
                symbol = balance.get("asset", "")
                value = balance.get("value_usdt", 0) or balance.get("value_usd", 0)
                if not symbol or value <= 0:
                    continue
                symbol_key = symbol.upper()
                asset_values[symbol_key] = asset_values.get(symbol_key, 0.0) + float(value)

        if not asset_values:
            return {
                "current_allocation": {},
                "target_allocation": {},
                "suggestions": [],
                "total_value": float(total_value),
            }

        # Current allocation in percentages
        current_allocation: Dict[str, float] = {}
        for symbol, value in asset_values.items():
            current_allocation[symbol] = (value / total_value) * 100.0

        # Target allocation - either provided or simple equal weight
        if target_allocation:
            # Normalize provided target so that sum is ~100
            cleaned_target: Dict[str, float] = {}
            total_target = 0.0
            for symbol, pct in target_allocation.items():
                try:
                    pct_val = float(pct)
                except (TypeError, ValueError):
                    continue
                if pct_val <= 0:
                    continue
                symbol_key = symbol.upper()
                cleaned_target[symbol_key] = pct_val
                total_target += pct_val

            if total_target > 0:
                target_allocation_norm: Dict[str, float] = {
                    symbol: (pct / total_target) * 100.0 for symbol, pct in cleaned_target.items()
                }
            else:
                target_allocation_norm = {}
        else:
            # Equal weight target for all assets currently in portfolio
            asset_count = len(asset_values)
            equal_weight = 100.0 / asset_count if asset_count > 0 else 0.0
            target_allocation_norm = {symbol: equal_weight for symbol in asset_values.keys()}

        target_allocation_pct: Dict[str, float] = target_allocation_norm

        suggestions: List[Dict[str, Any]] = []
        fee_rate = 0.001  # 0.1% assumed trading fee for cost estimate

        for symbol, current_pct in current_allocation.items():
            target_pct = target_allocation_pct.get(symbol)
            if target_pct is None:
                # If symbol not present in target, skip for now
                continue

            drift_pct = current_pct - target_pct
            if abs(drift_pct) < threshold:
                continue

            # Positive drift -> overweight -> sell, Negative -> underweight -> buy
            action = "decrease" if drift_pct > 0 else "increase"
            # Value to adjust so that allocation moves towards target
            adjustment_pct = drift_pct
            adjustment_value = (adjustment_pct / 100.0) * total_value

            if adjustment_value == 0:
                continue

            est_cost = abs(adjustment_value) * fee_rate

            suggestions.append(
                {
                    "symbol": symbol,
                    "action": action,
                    "drift_percent": drift_pct,
                    "current_percent": current_pct,
                    "target_percent": target_pct,
                    "adjustment_value": adjustment_value,
                    "estimated_cost": est_cost,
                }
            )

        # Sort by absolute adjustment size, largest first
        suggestions.sort(key=lambda s: abs(s.get("adjustment_value", 0.0)), reverse=True)
        if max_suggestions > 0:
            suggestions = suggestions[:max_suggestions]

        return {
            "current_allocation": current_allocation,
            "target_allocation": target_allocation_pct,
            "suggestions": suggestions,
            "total_value": float(total_value),
            "threshold": float(threshold),
        }
    
    def _detect_concentration_risks(self, assets: Dict[str, float], total_value: float) -> List[Dict]:
        """Detect concentration risk alerts"""
        alerts = []
        
        sorted_assets = sorted(assets.items(), key=lambda x: x[1], reverse=True)
        
        for asset, value in sorted_assets:
            percentage = (value / total_value) * 100
            
            if percentage >= self.HIGH_CONCENTRATION_THRESHOLD * 100:
                alerts.append({
                    "type": "critical",
                    "symbol": asset,
                    "message": f"{asset} accounts for {percentage:.1f}% of portfolio (critical: >50%)",
                    "severity": "high",
                    "percentage": round(percentage, 2),
                    "value_usd": round(value, 2),
                    "recommendation": f"Reduce {asset} allocation to below 40%"
                })
            elif percentage >= self.CONCENTRATION_RISK_THRESHOLD * 100:
                alerts.append({
                    "type": "warning",
                    "symbol": asset,
                    "message": f"{asset} represents {percentage:.1f}% of portfolio (warning: >40%)",
                    "severity": "medium",
                    "percentage": round(percentage, 2),
                    "value_usd": round(value, 2),
                    "recommendation": f"Consider diversifying away from {asset}"
                })
        
        return alerts
    
    def _detect_correlation_risks(self, asset_symbols: List[str], days: int) -> List[Dict]:
        """Detect high correlation between assets"""
        alerts = []
        import time
        start_ts = time.time()
        
        if not self.market_data_service or len(asset_symbols) < 2:
            return alerts
        
        # Process only the most important symbols (sorted for determinism)
        symbols_to_process = sorted(asset_symbols)[: self.MAX_RISK_SYMBOLS]

        # Get returns for each asset
        asset_returns: Dict[str, List[float]] = {}
        for symbol in symbols_to_process:
            if time.time() - start_ts > self.MAX_RISK_SECONDS:
                # Time budget exceeded – stop enriching further symbols
                break
            try:
                history = self.market_data_service.get_symbol_history(symbol, days)
                if history and len(history) >= 10:
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
                            asset_returns[symbol] = returns
            except Exception:
                continue
        
        if len(asset_returns) < 2:
            return alerts
        
        # Calculate correlations between all pairs
        symbols = list(asset_returns.keys())
        for i in range(len(symbols)):
            for j in range(i + 1, len(symbols)):
                if time.time() - start_ts > self.MAX_RISK_SECONDS:
                    return alerts
                symbol1, symbol2 = symbols[i], symbols[j]
                returns1 = asset_returns[symbol1]
                returns2 = asset_returns[symbol2]
                
                # Align returns
                min_len = min(len(returns1), len(returns2))
                if min_len < 10:
                    continue
                
                r1 = returns1[:min_len]
                r2 = returns2[:min_len]
                
                # Calculate Pearson correlation
                mean1 = statistics.mean(r1)
                mean2 = statistics.mean(r2)
                
                numerator = sum((r1[k] - mean1) * (r2[k] - mean2) for k in range(min_len))
                variance1 = sum((r1[k] - mean1) ** 2 for k in range(min_len))
                variance2 = sum((r2[k] - mean2) ** 2 for k in range(min_len))
                
                denominator = math.sqrt(variance1 * variance2)
                if denominator == 0:
                    continue
                
                correlation = numerator / denominator
                correlation = max(-1.0, min(1.0, correlation))
                
                if correlation >= self.HIGH_CORRELATION_THRESHOLD:
                    alerts.append({
                        "type": "warning",
                        "symbols": [symbol1, symbol2],
                        "message": f"High correlation ({correlation:.2f}) between {symbol1} and {symbol2}",
                        "severity": "medium",
                        "correlation": round(correlation, 3),
                        "recommendation": "Consider diversifying into less correlated assets"
                    })
        
        return alerts
    
    def _detect_volatility_risks(self, assets: Dict[str, float], days: int) -> List[Dict]:
        """Detect high volatility assets"""
        alerts = []
        import time
        start_ts = time.time()
        
        if not self.market_data_service:
            return alerts
        
        # Sort assets by value (descending) and cap count for expensive volatility calculations
        sorted_assets = sorted(assets.items(), key=lambda x: x[1], reverse=True)
        for idx, (symbol, value_usd) in enumerate(sorted_assets):
            if idx >= self.MAX_RISK_SYMBOLS:
                break
            if time.time() - start_ts > self.MAX_RISK_SECONDS:
                break
            try:
                history = self.market_data_service.get_symbol_history(symbol, days)
                if history and len(history) >= 30:
                    if isinstance(history, tuple):
                        history = history[0]
                    prices = [point.get('close', 0) for point in history if point.get('close')]
                    if len(prices) >= 30:
                        # Calculate returns
                        returns = []
                        for i in range(1, len(prices)):
                            if prices[i-1] > 0:
                                ret = (prices[i] - prices[i-1]) / prices[i-1]
                                returns.append(ret)
                        
                        if len(returns) >= 20:
                            # Annualized volatility
                            std_dev = statistics.stdev(returns)
                            annualized_vol = std_dev * math.sqrt(252) * 100  # Convert to percentage
                            
                            if annualized_vol >= self.HIGH_VOLATILITY_THRESHOLD:
                                alerts.append({
                                    "type": "warning",
                                    "symbol": symbol,
                                    "message": f"{symbol} has high volatility: {annualized_vol:.1f}% annually",
                                    "severity": "medium",
                                    "volatility": round(annualized_vol, 2),
                                    "value_usd": round(value_usd, 2),
                                    "recommendation": "Consider reducing position size or adding hedging"
                                })
            except Exception:
                continue
        
        return alerts
    
    def _detect_drawdown_risks(self, days: int) -> List[Dict]:
        """Detect portfolio drawdown risks"""
        alerts = []
        
        if not self.portfolio_history:
            return alerts
        
        try:
            # Get portfolio history
            history_points = self.portfolio_history.get_chart_data(days)
            if len(history_points) < 10:
                return alerts
            
            # Extract values
            values = []
            for point in history_points:
                value = point.get('value_usd', 0)
                if value > 0:
                    values.append(value)
            
            if len(values) < 10:
                return alerts
            
            # Calculate drawdown from peak
            peak = values[0]
            max_drawdown = 0.0
            current_drawdown = 0.0
            
            for value in values:
                if value > peak:
                    peak = value
                    current_drawdown = 0.0
                else:
                    current_drawdown = ((peak - value) / peak) * 100 if peak > 0 else 0.0
                    if current_drawdown > max_drawdown:
                        max_drawdown = current_drawdown
            
            # Check current drawdown
            if len(values) > 0:
                current_value = values[-1]
                current_drawdown = ((peak - current_value) / peak) * 100 if peak > 0 else 0.0
                
                if current_drawdown >= self.HIGH_DRAWDOWN_THRESHOLD:
                    alerts.append({
                        "type": "critical",
                        "message": f"Portfolio is down {current_drawdown:.1f}% from peak",
                        "severity": "high",
                        "drawdown_percent": round(current_drawdown, 2),
                        "max_drawdown_percent": round(max_drawdown, 2),
                        "recommendation": "Review portfolio allocation and consider risk management"
                    })
                elif max_drawdown >= self.HIGH_DRAWDOWN_THRESHOLD:
                    alerts.append({
                        "type": "warning",
                        "message": f"Portfolio experienced {max_drawdown:.1f}% drawdown in the last {days} days",
                        "severity": "medium",
                        "drawdown_percent": round(current_drawdown, 2),
                        "max_drawdown_percent": round(max_drawdown, 2),
                        "recommendation": "Monitor portfolio closely and consider rebalancing"
                    })
        except Exception:
            pass
        
        return alerts

