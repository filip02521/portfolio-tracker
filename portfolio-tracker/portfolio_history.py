"""
Portfolio value history tracking
"""
import json
import os
from datetime import datetime
from typing import List, Dict

class PortfolioHistory:
    """Track portfolio value over time"""
    
    def __init__(self, data_file='portfolio_history.json'):
        self.data_file = data_file
        self.history = self.load_history()
    
    def load_history(self):
        """Load portfolio history from file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_history(self):
        """Save portfolio history to file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def add_snapshot(self, total_value_usd: float, total_value_pln: float, timestamp: str = None):
        """Add a portfolio value snapshot"""
        snapshot = {
            'timestamp': timestamp or datetime.now().isoformat(),
            'value_usd': total_value_usd,
            'value_pln': total_value_pln
        }
        self.history.append(snapshot)
        
        # Keep only last 1000 snapshots
        if len(self.history) > 1000:
            self.history = self.history[-1000:]
        
        self.save_history()
        return snapshot
    
    def get_chart_data(self, days: int = 30):
        """Get data for chart visualization"""
        if not self.history:
            return []
        
        # Filter by days if specified
        if days > 0:
            cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
            filtered = [h for h in self.history 
                       if datetime.fromisoformat(h['timestamp']).timestamp() > cutoff_date]
            return filtered
        
        return self.history
    
    def get_latest_value(self):
        """Get latest portfolio value"""
        if not self.history:
            return None
        return self.history[-1]

