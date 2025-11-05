"""
Price Alert Service - Manages price alerts for users
"""
from typing import List, Dict, Optional
from datetime import datetime
from logging_config import get_logger

logger = get_logger(__name__)

class PriceAlertService:
    def __init__(self):
        # In-memory storage (in production, use database)
        # Format: {user_id: [alerts]}
        self._alerts: Dict[str, List[Dict]] = {}
        
    def create_alert(
        self, 
        user_id: str, 
        symbol: str, 
        condition: str, 
        price: float,
        name: str = None
    ) -> Dict:
        """Create a new price alert"""
        try:
            alert = {
                'id': len(self._alerts.get(user_id, [])) + 1,
                'symbol': symbol.upper(),
                'name': name or symbol.upper(),
                'condition': condition,  # 'above' or 'below'
                'price': price,
                'active': True,
                'triggered': False,
                'created_at': datetime.now().isoformat(),
                'triggered_at': None
            }
            
            if user_id not in self._alerts:
                self._alerts[user_id] = []
            
            self._alerts[user_id].append(alert)
            
            logger.info(f"Created price alert for user {user_id}: {symbol} {condition} ${price}")
            return alert
        except Exception as e:
            logger.error(f"Error creating price alert: {e}")
            raise
    
    def get_alerts(self, user_id: str) -> List[Dict]:
        """Get all alerts for a user"""
        return self._alerts.get(user_id, [])
    
    def update_alert(
        self,
        user_id: str,
        alert_id: int,
        condition: Optional[str] = None,
        price: Optional[float] = None,
        active: Optional[bool] = None
    ) -> Dict:
        """Update an existing alert"""
        try:
            alerts = self._alerts.get(user_id, [])
            alert = next((a for a in alerts if a['id'] == alert_id), None)
            
            if not alert:
                raise ValueError(f"Alert {alert_id} not found")
            
            if condition is not None:
                alert['condition'] = condition
            if price is not None:
                alert['price'] = price
            if active is not None:
                alert['active'] = active
            
            alert['updated_at'] = datetime.now().isoformat()
            
            logger.info(f"Updated alert {alert_id} for user {user_id}")
            return alert
        except Exception as e:
            logger.error(f"Error updating alert: {e}")
            raise
    
    def delete_alert(self, user_id: str, alert_id: int) -> bool:
        """Delete an alert"""
        try:
            alerts = self._alerts.get(user_id, [])
            initial_count = len(alerts)
            self._alerts[user_id] = [a for a in alerts if a['id'] != alert_id]
            
            deleted = len(self._alerts[user_id]) < initial_count
            if deleted:
                logger.info(f"Deleted alert {alert_id} for user {user_id}")
            
            return deleted
        except Exception as e:
            logger.error(f"Error deleting alert: {e}")
            raise
    
    def check_alerts(self, user_id: str, current_prices: Dict[str, float]) -> List[Dict]:
        """Check if any alerts should be triggered"""
        triggered_alerts = []
        alerts = self._alerts.get(user_id, [])
        
        for alert in alerts:
            if not alert['active'] or alert['triggered']:
                continue
            
            symbol = alert['symbol']
            if symbol not in current_prices:
                continue
            
            current_price = current_prices[symbol]
            should_trigger = False
            
            if alert['condition'] == 'above' and current_price >= alert['price']:
                should_trigger = True
            elif alert['condition'] == 'below' and current_price <= alert['price']:
                should_trigger = True
            
            if should_trigger:
                alert['triggered'] = True
                alert['triggered_at'] = datetime.now().isoformat()
                triggered_alerts.append({
                    'alert_id': alert['id'],
                    'symbol': symbol,
                    'condition': alert['condition'],
                    'target_price': alert['price'],
                    'current_price': current_price,
                    'message': f"{symbol} price is now ${current_price:.2f}, {'above' if alert['condition'] == 'above' else 'below'} your alert price of ${alert['price']:.2f}"
                })
                logger.info(f"Alert triggered: {symbol} {alert['condition']} ${alert['price']}")
        
        return triggered_alerts


