"""
Risk Management Service - Portfolio risk analysis and suggestions
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from logging_config import get_logger
import statistics

logger = get_logger(__name__)

class RiskManagementService:
    def __init__(self):
        pass
    
    def calculate_portfolio_risk_score(
        self,
        assets: List[Dict],
        portfolio_value: float
    ) -> Dict:
        """Calculate overall portfolio risk score (0-100)"""
        try:
            if not assets or portfolio_value == 0:
                return {
                    'risk_score': 50,
                    'risk_level': 'moderate',
                    'factors': []
                }
            
            risk_factors = []
            risk_points = 0
            
            # Factor 1: Concentration risk (max single asset %)
            max_allocation = max([a.get('allocation_percent', 0) for a in assets], default=0)
            if max_allocation > 40:
                risk_points += 30
                risk_factors.append({
                    'type': 'high_concentration',
                    'severity': 'high',
                    'message': f'High concentration: {max_allocation:.1f}% in single asset',
                    'suggestion': 'Consider diversifying to reduce concentration risk'
                })
            elif max_allocation > 25:
                risk_points += 15
                risk_factors.append({
                    'type': 'moderate_concentration',
                    'severity': 'medium',
                    'message': f'Moderate concentration: {max_allocation:.1f}% in single asset',
                    'suggestion': 'Monitor concentration levels'
                })
            
            # Factor 2: Number of assets (diversification)
            num_assets = len(assets)
            if num_assets < 3:
                risk_points += 20
                risk_factors.append({
                    'type': 'low_diversification',
                    'severity': 'high',
                    'message': f'Low diversification: only {num_assets} assets',
                    'suggestion': 'Add more assets to improve diversification'
                })
            elif num_assets < 5:
                risk_points += 10
                risk_factors.append({
                    'type': 'moderate_diversification',
                    'severity': 'medium',
                    'message': f'Moderate diversification: {num_assets} assets',
                    'suggestion': 'Consider adding more assets'
                })
            
            # Factor 3: Asset type concentration
            crypto_pct = sum([a.get('allocation_percent', 0) for a in assets if a.get('type') == 'crypto'], default=0)
            if crypto_pct > 60:
                risk_points += 15
                risk_factors.append({
                    'type': 'crypto_concentration',
                    'severity': 'medium',
                    'message': f'High crypto concentration: {crypto_pct:.1f}%',
                    'suggestion': 'Consider adding stocks or other asset types'
                })
            
            # Factor 4: Volatility (if available)
            high_volatility_assets = [a for a in assets if a.get('volatility', 0) > 50]
            if len(high_volatility_assets) > len(assets) * 0.5:
                risk_points += 10
                risk_factors.append({
                    'type': 'high_volatility',
                    'severity': 'medium',
                    'message': 'Many high-volatility assets in portfolio',
                    'suggestion': 'Consider balancing with more stable assets'
                })
            
            # Calculate risk score (0-100, higher = riskier)
            risk_score = min(100, risk_points)
            
            # Determine risk level
            if risk_score < 30:
                risk_level = 'low'
            elif risk_score < 60:
                risk_level = 'moderate'
            else:
                risk_level = 'high'
            
            return {
                'risk_score': risk_score,
                'risk_level': risk_level,
                'factors': risk_factors,
                'max_allocation': max_allocation,
                'num_assets': num_assets,
                'diversification_score': min(100, num_assets * 20)
            }
        except Exception as e:
            logger.error(f"Error calculating portfolio risk: {e}")
            return {
                'risk_score': 50,
                'risk_level': 'moderate',
                'factors': []
            }
    
    def suggest_stop_loss(
        self,
        entry_price: float,
        current_price: float,
        asset_type: str = 'crypto'
    ) -> Dict:
        """Suggest stop-loss level based on asset volatility and type"""
        try:
            pnl_percent = ((current_price - entry_price) / entry_price) * 100
            
            # Different SL strategies for different asset types
            if asset_type == 'crypto':
                # More volatile, wider SL
                if pnl_percent > 20:
                    sl_percent = 15  # Protect profits
                elif pnl_percent > 0:
                    sl_percent = 10  # Break-even + small profit
                else:
                    sl_percent = 5  # Tight SL for losses
            else:  # stocks
                # Less volatile, tighter SL
                if pnl_percent > 10:
                    sl_percent = 7
                elif pnl_percent > 0:
                    sl_percent = 5
                else:
                    sl_percent = 3
            
            sl_price = current_price * (1 - sl_percent / 100)
            
            return {
                'suggested_sl': sl_price,
                'sl_percent': sl_percent,
                'current_price': current_price,
                'entry_price': entry_price,
                'pnl_percent': pnl_percent,
                'risk_reward_ratio': abs(pnl_percent) / sl_percent if sl_percent > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error suggesting stop-loss: {e}")
            return {}
    
    def suggest_take_profit(
        self,
        entry_price: float,
        current_price: float,
        asset_type: str = 'crypto'
    ) -> Dict:
        """Suggest take-profit levels"""
        try:
            pnl_percent = ((current_price - entry_price) / entry_price) * 100
            
            if asset_type == 'crypto':
                tp_levels = [
                    {'level': 1, 'percent': 25, 'price': entry_price * 1.25},
                    {'level': 2, 'percent': 50, 'price': entry_price * 1.50},
                    {'level': 3, 'percent': 100, 'price': entry_price * 2.00},
                ]
            else:
                tp_levels = [
                    {'level': 1, 'percent': 10, 'price': entry_price * 1.10},
                    {'level': 2, 'percent': 20, 'price': entry_price * 1.20},
                    {'level': 3, 'percent': 30, 'price': entry_price * 1.30},
                ]
            
            return {
                'tp_levels': tp_levels,
                'current_price': current_price,
                'entry_price': entry_price,
                'pnl_percent': pnl_percent
            }
        except Exception as e:
            logger.error(f"Error suggesting take-profit: {e}")
            return {}
    
    def calculate_position_size(
        self,
        portfolio_value: float,
        risk_per_trade: float = 2.0,  # Risk 2% of portfolio per trade
        entry_price: float = 0,
        stop_loss_price: float = 0
    ) -> Dict:
        """Calculate optimal position size based on risk"""
        try:
            if entry_price == 0 or stop_loss_price == 0:
                return {}
            
            risk_amount = portfolio_value * (risk_per_trade / 100)
            price_risk = abs(entry_price - stop_loss_price)
            
            if price_risk == 0:
                return {}
            
            position_size = risk_amount / price_risk
            position_value = position_size * entry_price
            
            return {
                'position_size': position_size,
                'position_value': position_value,
                'risk_amount': risk_amount,
                'risk_percent': risk_per_trade,
                'entry_price': entry_price,
                'stop_loss_price': stop_loss_price,
                'price_risk': price_risk
            }
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return {}
    
    def generate_portfolio_heatmap(
        self,
        assets: List[Dict]
    ) -> Dict:
        """Generate risk heat map for portfolio"""
        try:
            heatmap_data = []
            
            for asset in assets:
                allocation = asset.get('allocation_percent', 0)
                volatility = asset.get('volatility', 30)  # Default volatility
                pnl_percent = asset.get('pnl_percent', 0)
                
                # Risk score per asset (0-100)
                risk_score = volatility * 0.7 + (allocation * 0.3)
                
                heatmap_data.append({
                    'symbol': asset.get('symbol', ''),
                    'name': asset.get('name', ''),
                    'allocation': allocation,
                    'risk_score': min(100, risk_score),
                    'pnl_percent': pnl_percent,
                    'color': self._get_risk_color(risk_score)
                })
            
            return {
                'heatmap': heatmap_data,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error generating heatmap: {e}")
            return {'heatmap': []}
    
    def _get_risk_color(self, risk_score: float) -> str:
        """Get color for risk level"""
        if risk_score < 33:
            return 'green'
        elif risk_score < 66:
            return 'yellow'
        else:
            return 'red'


