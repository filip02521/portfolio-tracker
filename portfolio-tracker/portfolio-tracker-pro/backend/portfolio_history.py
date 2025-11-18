"""
Portfolio value history tracking
Now uses SQLite database instead of JSON file
"""
from datetime import datetime
from typing import Optional
from database import get_db


class PortfolioHistory:
    """Track portfolio value over time"""
    
    def __init__(self, data_file='portfolio_history.json'):
        # Keep data_file for backward compatibility, but use database
        self.data_file = data_file
    
    def add_snapshot(self, total_value_usd: float, total_value_pln: float, timestamp: str = None, user_id: Optional[str] = None):
        """Add a portfolio value snapshot"""
        timestamp = timestamp or datetime.now().isoformat()
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO portfolio_history (user_id, timestamp, value_usd, value_pln)
                VALUES (?, ?, ?, ?)
            ''', (user_id, timestamp, total_value_usd, total_value_pln))
            conn.commit()
        
        # Keep only last 1000 snapshots per user (or globally if user_id is None)
        self._cleanup_old_snapshots(user_id)
        
        return {
            'timestamp': timestamp,
            'value_usd': total_value_usd,
            'value_pln': total_value_pln
        }
    
    def _cleanup_old_snapshots(self, user_id: Optional[str] = None):
        """Keep only last 1000 snapshots"""
        with get_db() as conn:
            cursor = conn.cursor()
            if user_id:
                # Get count for user
                cursor.execute('SELECT COUNT(*) FROM portfolio_history WHERE user_id = ?', (user_id,))
                count = cursor.fetchone()[0]
                if count > 1000:
                    # Delete oldest entries, keeping last 1000
                    cursor.execute('''
                        DELETE FROM portfolio_history 
                        WHERE user_id = ? AND id NOT IN (
                            SELECT id FROM portfolio_history 
                            WHERE user_id = ? 
                            ORDER BY timestamp DESC 
                            LIMIT 1000
                        )
                    ''', (user_id, user_id))
            else:
                # Get count globally
                cursor.execute('SELECT COUNT(*) FROM portfolio_history WHERE user_id IS NULL')
                count = cursor.fetchone()[0]
                if count > 1000:
                    # Delete oldest entries, keeping last 1000
                    cursor.execute('''
                        DELETE FROM portfolio_history 
                        WHERE user_id IS NULL AND id NOT IN (
                            SELECT id FROM portfolio_history 
                            WHERE user_id IS NULL 
                            ORDER BY timestamp DESC 
                            LIMIT 1000
                        )
                    ''')
            conn.commit()
    
    def should_add_snapshot(self, min_interval_hours: int = 1, user_id: Optional[str] = None) -> bool:
        """Check if we should add a new snapshot based on time interval
        Returns True if last snapshot is older than min_interval_hours
        """
        with get_db() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute('''
                    SELECT timestamp FROM portfolio_history 
                    WHERE user_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                ''', (user_id,))
            else:
                cursor.execute('''
                    SELECT timestamp FROM portfolio_history 
                    WHERE user_id IS NULL 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                ''')
            row = cursor.fetchone()
            
            if not row:
                return True
            
            last_timestamp = datetime.fromisoformat(row['timestamp'])
            time_diff = (datetime.now() - last_timestamp).total_seconds() / 3600  # hours
            return time_diff >= min_interval_hours
    
    def get_chart_data(self, days: int = 30, user_id: Optional[str] = None):
        """Get data for chart visualization"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            if days > 0:
                cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
                cutoff_iso = datetime.fromtimestamp(cutoff_date).isoformat()
                
                if user_id:
                    cursor.execute('''
                        SELECT timestamp, value_usd, value_pln 
                        FROM portfolio_history 
                        WHERE user_id = ? AND timestamp > ?
                        ORDER BY timestamp ASC
                    ''', (user_id, cutoff_iso))
                else:
                    cursor.execute('''
                        SELECT timestamp, value_usd, value_pln 
                        FROM portfolio_history 
                        WHERE user_id IS NULL AND timestamp > ?
                        ORDER BY timestamp ASC
                    ''', (cutoff_iso,))
            else:
                if user_id:
                    cursor.execute('''
                        SELECT timestamp, value_usd, value_pln 
                        FROM portfolio_history 
                        WHERE user_id = ?
                        ORDER BY timestamp ASC
                    ''', (user_id,))
                else:
                    cursor.execute('''
                        SELECT timestamp, value_usd, value_pln 
                        FROM portfolio_history 
                        WHERE user_id IS NULL
                        ORDER BY timestamp ASC
                    ''')
            
            rows = cursor.fetchall()
            return [
                {
                    'timestamp': row['timestamp'],
                    'value_usd': row['value_usd'],
                    'value_pln': row['value_pln']
                }
                for row in rows
            ]
    
    def get_latest_value(self, user_id: Optional[str] = None):
        """Get latest portfolio value"""
        with get_db() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute('''
                    SELECT timestamp, value_usd, value_pln 
                    FROM portfolio_history 
                    WHERE user_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                ''', (user_id,))
            else:
                cursor.execute('''
                    SELECT timestamp, value_usd, value_pln 
                    FROM portfolio_history 
                    WHERE user_id IS NULL 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                ''')
            row = cursor.fetchone()
            
            if row:
                return {
                    'timestamp': row['timestamp'],
                    'value_usd': row['value_usd'],
                    'value_pln': row['value_pln']
                }
            return None
