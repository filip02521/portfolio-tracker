"""
Portfolio value history tracking
"""
import json
import os
from datetime import datetime

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
            except Exception:
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
    
    def should_add_snapshot(self, min_interval_hours: int = 1) -> bool:
        """Check if we should add a new snapshot based on time interval
        Returns True if last snapshot is older than min_interval_hours
        """
        if not self.history:
            return True
        
        # Get most recent snapshot timestamp
        sorted_history = sorted(self.history, key=lambda x: x.get('timestamp', ''))
        last_snapshot = sorted_history[-1]
        last_timestamp = datetime.fromisoformat(last_snapshot.get('timestamp', datetime.now().isoformat()))
        
        # Check if enough time has passed
        time_diff = (datetime.now() - last_timestamp).total_seconds() / 3600  # hours
        return time_diff >= min_interval_hours
    
    def get_chart_data(self, days: int = 30):
        """Get data for chart visualization"""
        if not self.history:
            return []
        
        # Sort by timestamp (oldest first for proper chart display)
        sorted_history = sorted(self.history, key=lambda x: x.get('timestamp', ''))
        
        # Filter by days if specified
        if days > 0:
            cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
            filtered = [h for h in sorted_history 
                       if datetime.fromisoformat(h['timestamp']).timestamp() > cutoff_date]
            return filtered
        
        return sorted_history
    
    def get_latest_value(self):
        """Get latest portfolio value"""
        if not self.history:
            return None
        return self.history[-1]

