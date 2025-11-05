"""
Smart Portfolio Insights Service
Provides intelligent analysis and recommendations for portfolio optimization
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

class SmartInsightsService:
    """Service for generating smart portfolio insights"""
    
    def __init__(self):
        # Risk thresholds
        self.CONCENTRATION_RISK_THRESHOLD = 0.4  # 40% - warning
        self.HIGH_CONCENTRATION_THRESHOLD = 0.5  # 50% - critical
        self.MIN_DIVERSIFICATION_ASSETS = 5  # Minimum recommended assets
        self.HIGH_VOLATILITY_THRESHOLD = 30.0  # Annualized volatility > 30%
        
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

