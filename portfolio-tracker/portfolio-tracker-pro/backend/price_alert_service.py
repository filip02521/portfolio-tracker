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
        price: Optional[float] = None,
        name: str = None,
        rsi_threshold: Optional[float] = None,
        volume_spike_percent: Optional[float] = None,
        dd_score_threshold: Optional[float] = None
    ) -> Dict:
        """Create a new price alert with optional advanced conditions"""
        try:
            alert = {
                'id': len(self._alerts.get(user_id, [])) + 1,
                'symbol': symbol.upper(),
                'name': name or symbol.upper(),
                'condition': condition,  # 'above', 'below', 'rsi_above', 'rsi_below', 'volume_spike', 'dd_score_below'
                'price': price,
                'active': True,
                'triggered': False,
                'created_at': datetime.now().isoformat(),
                'triggered_at': None,
                'rsi_threshold': rsi_threshold,
                'volume_spike_percent': volume_spike_percent,
                'dd_score_threshold': dd_score_threshold
            }
            
            if user_id not in self._alerts:
                self._alerts[user_id] = []
            
            self._alerts[user_id].append(alert)
            
            logger.info(f"Created alert for user {user_id}: {symbol} {condition}")
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
    
    def check_alerts(
        self, 
        user_id: str, 
        current_prices: Dict[str, float],
        market_data: Optional[Dict[str, Dict]] = None,
        dd_scores: Optional[Dict[str, float]] = None
    ) -> List[Dict]:
        """
        Check if any alerts should be triggered.
        
        Args:
            user_id: User identifier
            current_prices: Dict of symbol -> current price
            market_data: Optional dict of symbol -> market data (with RSI, volume_24h, etc.)
            dd_scores: Optional dict of symbol -> DD score
        """
        triggered_alerts = []
        alerts = self._alerts.get(user_id, [])
        
        for alert in alerts:
            if not alert['active'] or alert['triggered']:
                continue
            
            symbol = alert['symbol']
            condition = alert['condition']
            should_trigger = False
            message = ""
            
            # Price-based conditions
            if condition in ['above', 'below']:
                if symbol not in current_prices:
                    continue
                current_price = current_prices[symbol]
                if condition == 'above' and current_price >= alert['price']:
                    should_trigger = True
                    message = f"{symbol} price is now ${current_price:.2f}, above your alert price of ${alert['price']:.2f}"
                elif condition == 'below' and current_price <= alert['price']:
                    should_trigger = True
                    message = f"{symbol} price is now ${current_price:.2f}, below your alert price of ${alert['price']:.2f}"
            
            # RSI conditions
            elif condition in ['rsi_above', 'rsi_below']:
                if not market_data or symbol not in market_data:
                    continue
                rsi = market_data[symbol].get('rsi')
                threshold = alert.get('rsi_threshold')
                if rsi is not None and threshold is not None:
                    if condition == 'rsi_above' and rsi >= threshold:
                        should_trigger = True
                        message = f"{symbol} RSI is now {rsi:.1f}, above your threshold of {threshold:.1f}"
                    elif condition == 'rsi_below' and rsi <= threshold:
                        should_trigger = True
                        message = f"{symbol} RSI is now {rsi:.1f}, below your threshold of {threshold:.1f}"
            
            # Volume spike condition
            elif condition == 'volume_spike':
                if not market_data or symbol not in market_data:
                    continue
                volume_24h = market_data[symbol].get('volume_24h')
                spike_percent = alert.get('volume_spike_percent', 200)
                # Calculate 7-day average volume (simplified - would need historical data)
                # For now, we'll use a simple heuristic: compare to typical volume
                # In production, you'd fetch historical volume data
                if volume_24h and volume_24h > 0:
                    # Simplified: assume average is half of current if no history
                    # In production, calculate from actual 7d history
                    avg_volume = volume_24h * 0.5  # Placeholder
                    if avg_volume > 0:
                        volume_ratio = (volume_24h / avg_volume) * 100
                        if volume_ratio >= spike_percent:
                            should_trigger = True
                            message = f"{symbol} volume spike detected: {volume_ratio:.1f}% of average (threshold: {spike_percent}%)"
            
            # DD score condition
            elif condition == 'dd_score_below':
                if not dd_scores or symbol not in dd_scores:
                    continue
                current_dd = dd_scores[symbol]
                threshold = alert.get('dd_score_threshold')
                if current_dd is not None and threshold is not None:
                    if current_dd <= threshold:
                        should_trigger = True
                        message = f"{symbol} DD score is now {current_dd:.1f}, below your threshold of {threshold:.1f}"
            
            if should_trigger:
                alert['triggered'] = True
                alert['triggered_at'] = datetime.now().isoformat()
                triggered_alerts.append({
                    'alert_id': alert['id'],
                    'symbol': symbol,
                    'condition': condition,
                    'message': message,
                    'triggered_at': alert['triggered_at']
                })
                logger.info(f"Alert triggered: {symbol} {condition} - {message}")
        
        return triggered_alerts


