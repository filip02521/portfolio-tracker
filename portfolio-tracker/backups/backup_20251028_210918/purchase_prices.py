"""
Purchase price tracking for portfolio assets
"""
import json
import os
from typing import Optional

class PurchasePriceTracker:
    """Track purchase prices for assets"""
    
    def __init__(self, data_file='purchase_prices.json'):
        self.data_file = data_file
        self.prices = self.load_prices()
    
    def load_prices(self):
        """Load purchase prices from file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def save_prices(self):
        """Save purchase prices to file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.prices, f, indent=2)
    
    def set_purchase_price(self, exchange: str, asset: str, price_usd: float):
        """Set purchase price for an asset"""
        key = f"{exchange}_{asset}"
        self.prices[key] = {
            'exchange': exchange,
            'asset': asset,
            'purchase_price': price_usd
        }
        self.save_prices()
    
    def get_purchase_price(self, exchange: str, asset: str) -> Optional[float]:
        """Get purchase price for an asset"""
        key = f"{exchange}_{asset}"
        if key in self.prices:
            return self.prices[key]['purchase_price']
        return None
    
    def calculate_simple_pnl(self, exchange: str, asset: str, current_price: float, amount: float):
        """Calculate simple PNL based on purchase price"""
        purchase_price = self.get_purchase_price(exchange, asset)
        
        if purchase_price is None:
            return None
        
        current_value = amount * current_price
        invested = amount * purchase_price
        pnl = current_value - invested
        pnl_percent = ((current_price - purchase_price) / purchase_price * 100) if purchase_price > 0 else 0
        
        return {
            'asset': asset,
            'exchange': exchange,
            'amount': amount,
            'purchase_price': purchase_price,
            'current_price': current_price,
            'current_value': current_value,
            'invested': invested,
            'pnl': pnl,
            'pnl_percent': pnl_percent,
            'status': 'profit' if pnl > 0 else 'loss' if pnl < 0 else 'break_even'
        }

