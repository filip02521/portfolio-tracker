"""
AI Recommendations History Tracking
Tracks historical AI recommendations and their performance for verification and backtesting
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class AIRecommendationsHistory:
    """Manage AI recommendations history and track their performance"""
    
    def __init__(self, data_file='ai_recommendations_history.json'):
        self.data_file = data_file
        self.recommendations = self.load_history()
    
    def load_history(self) -> List[Dict]:
        """Load recommendations history from file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                return []
        return []
    
    def _sanitize_for_json(self, obj):
        """Recursively convert numpy/pandas types to native Python types for JSON serialization"""
        import numpy as np
        try:
            import pandas as pd
        except ImportError:
            pd = None
        
        if obj is None:
            return None
        
        # Handle numpy scalars
        if isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        if isinstance(obj, (np.integer, int)):
            return int(obj)
        if isinstance(obj, (np.floating, float)):
            if np.isnan(obj):
                return None
            return float(obj)
        
        # Handle numpy arrays
        if isinstance(obj, np.ndarray):
            return [self._sanitize_for_json(item) for item in obj]
        
        # Handle pandas types
        if pd is not None:
            if isinstance(obj, pd.Series):
                return [self._sanitize_for_json(item) for item in obj]
            if isinstance(obj, pd.DataFrame):
                return obj.to_dict('records')
            if pd.isna(obj):
                return None
        
        # Handle dictionaries
        if isinstance(obj, dict):
            return {key: self._sanitize_for_json(value) for key, value in obj.items()}
        
        # Handle lists/tuples
        if isinstance(obj, (list, tuple)):
            return [self._sanitize_for_json(item) for item in obj]
        
        # Try to convert numpy types with .item()
        if hasattr(obj, 'item'):
            try:
                return self._sanitize_for_json(obj.item())
            except (AttributeError, ValueError):
                pass
        
        return obj
    
    def save_history(self):
        """Save recommendations history to file"""
        try:
            # Sanitize all recommendations before saving
            sanitized_recommendations = self._sanitize_for_json(self.recommendations)
            with open(self.data_file, 'w') as f:
                json.dump(sanitized_recommendations, f, indent=2)
        except Exception as e:
            print(f"Error saving recommendations history: {e}")
    
    def save_recommendation(
        self,
        symbol: str,
        action: str,  # 'buy' or 'sell'
        signal_strength: float,
        confidence: float,
        metrics: Dict,
        actual_price_at_time: float,
        timeframe_used: str = 'weekly',
        timestamp: Optional[str] = None
    ) -> Dict:
        """
        Save a new AI recommendation
        
        Args:
            symbol: Asset symbol (e.g., 'BTC')
            action: Recommendation action ('buy' or 'sell')
            signal_strength: Signal strength (-100 to +100)
            confidence: Confidence level (0.0 to 1.0)
            metrics: All technical indicators and metrics as dict
            actual_price_at_time: Current price when recommendation was made
            timeframe_used: Timeframe used for analysis ('weekly', 'monthly', etc.)
            timestamp: Optional timestamp (defaults to now)
            
        Returns:
            Dict with saved recommendation data
        """
        # Sanitize metrics before saving
        sanitized_metrics = self._sanitize_for_json(metrics)
        
        recommendation = {
            'id': len(self.recommendations) + 1,
            'symbol': symbol,
            'action': action,
            'signal_strength': signal_strength,
            'confidence': confidence,
            'metrics': sanitized_metrics,
            'actual_price_at_time': actual_price_at_time,
            'target_price': None,  # Will be set later if prediction is available
            'timeframe_used': timeframe_used,
            'timestamp': timestamp or datetime.now().isoformat(),
            'verified': False,
            'verification_date': None,
            'price_after_7d': None,
            'price_after_30d': None,
            'price_after_90d': None,
            'return_7d': None,
            'return_30d': None,
            'return_90d': None,
            'was_correct_7d': None,
            'was_correct_30d': None,
            'was_correct_90d': None
        }
        
        self.recommendations.append(recommendation)
        self.save_history()
        return recommendation
    
    def update_result(
        self,
        recommendation_id: int,
        price_after_7d: Optional[float] = None,
        price_after_30d: Optional[float] = None,
        price_after_90d: Optional[float] = None
    ) -> bool:
        """
        Update recommendation with results after specified periods
        
        Args:
            recommendation_id: ID of recommendation to update
            price_after_7d: Price 7 days after recommendation
            price_after_30d: Price 30 days after recommendation
            price_after_90d: Price 90 days after recommendation
            
        Returns:
            True if updated, False if not found
        """
        for rec in self.recommendations:
            if rec['id'] == recommendation_id:
                if price_after_7d is not None:
                    rec['price_after_7d'] = price_after_7d
                    rec['return_7d'] = self._calculate_return(
                        rec['actual_price_at_time'],
                        price_after_7d,
                        rec['action']
                    )
                    rec['was_correct_7d'] = self._was_correct(
                        rec['action'],
                        rec['return_7d']
                    )
                
                if price_after_30d is not None:
                    rec['price_after_30d'] = price_after_30d
                    rec['return_30d'] = self._calculate_return(
                        rec['actual_price_at_time'],
                        price_after_30d,
                        rec['action']
                    )
                    rec['was_correct_30d'] = self._was_correct(
                        rec['action'],
                        rec['return_30d']
                    )
                
                if price_after_90d is not None:
                    rec['price_after_90d'] = price_after_90d
                    rec['return_90d'] = self._calculate_return(
                        rec['actual_price_at_time'],
                        price_after_90d,
                        rec['action']
                    )
                    rec['was_correct_90d'] = self._was_correct(
                        rec['action'],
                        rec['return_90d']
                    )
                
                rec['verified'] = True
                rec['verification_date'] = datetime.now().isoformat()
                self.save_history()
                return True
        
        return False
    
    def _calculate_return(self, price_at_time: float, price_after: float, action: str) -> float:
        """
        Calculate return based on recommendation action
        
        Args:
            price_at_time: Price when recommendation was made
            price_after: Price after X days
            action: 'buy' or 'sell'
            
        Returns:
            Return percentage
        """
        if price_at_time <= 0:
            return 0.0
        
        if action == 'buy':
            # Buy: return = (price_after - price_at_time) / price_at_time
            return ((price_after - price_at_time) / price_at_time) * 100
        else:  # sell
            # Sell: return = (price_at_time - price_after) / price_at_time
            return ((price_at_time - price_after) / price_at_time) * 100
    
    def _was_correct(self, action: str, return_pct: float) -> bool:
        """
        Check if recommendation was correct
        
        Args:
            action: 'buy' or 'sell'
            return_pct: Return percentage
            
        Returns:
            True if recommendation was correct (profitable)
        """
        if action == 'buy':
            return return_pct > 0  # Buy is correct if price went up
        else:  # sell
            return return_pct > 0  # Sell is correct if price went down
    
    def get_performance_stats(self) -> Dict:
        """
        Calculate performance statistics for all verified recommendations
        
        Returns:
            Dict with win rate, average returns, per-indicator accuracy, etc.
        """
        verified = [r for r in self.recommendations if r.get('verified', False)]
        
        if not verified:
            return {
                'total_recommendations': len(self.recommendations),
                'verified': 0,
                'win_rate_7d': None,
                'win_rate_30d': None,
                'win_rate_90d': None,
                'avg_return_7d': None,
                'avg_return_30d': None,
                'avg_return_90d': None,
                'signal_strength_vs_accuracy': None,
                'per_indicator_accuracy': None,
                'timeframe_analysis': None
            }
        
        # Win rates
        correct_7d = [r for r in verified if r.get('was_correct_7d')]
        correct_30d = [r for r in verified if r.get('was_correct_30d')]
        correct_90d = [r for r in verified if r.get('was_correct_90d')]
        
        verified_7d = [r for r in verified if r.get('was_correct_7d') is not None]
        verified_30d = [r for r in verified if r.get('was_correct_30d') is not None]
        verified_90d = [r for r in verified if r.get('was_correct_90d') is not None]
        
        win_rate_7d = len(correct_7d) / len(verified_7d) * 100 if verified_7d else None
        win_rate_30d = len(correct_30d) / len(verified_30d) * 100 if verified_30d else None
        win_rate_90d = len(correct_90d) / len(verified_90d) * 100 if verified_90d else None
        
        # Average returns
        returns_7d = [r['return_7d'] for r in verified if r.get('return_7d') is not None]
        returns_30d = [r['return_30d'] for r in verified if r.get('return_30d') is not None]
        returns_90d = [r['return_90d'] for r in verified if r.get('return_90d') is not None]
        
        avg_return_7d = sum(returns_7d) / len(returns_7d) if returns_7d else None
        avg_return_30d = sum(returns_30d) / len(returns_30d) if returns_30d else None
        avg_return_90d = sum(returns_90d) / len(returns_90d) if returns_90d else None
        
        # Signal strength vs accuracy
        signal_accuracy_7d = []
        signal_accuracy_30d = []
        signal_accuracy_90d = []
        
        for r in verified:
            if r.get('was_correct_7d') is not None:
                signal_accuracy_7d.append({
                    'signal_strength': abs(r['signal_strength']),
                    'was_correct': r['was_correct_7d']
                })
            if r.get('was_correct_30d') is not None:
                signal_accuracy_30d.append({
                    'signal_strength': abs(r['signal_strength']),
                    'was_correct': r['was_correct_30d']
                })
            if r.get('was_correct_90d') is not None:
                signal_accuracy_90d.append({
                    'signal_strength': abs(r['signal_strength']),
                    'was_correct': r['was_correct_90d']
                })
        
        # Timeframe analysis
        timeframe_stats = {}
        for tf in ['weekly', 'monthly', 'daily']:
            tf_recommendations = [r for r in verified if r.get('timeframe_used') == tf]
            if tf_recommendations:
                tf_correct_30d = [r for r in tf_recommendations if r.get('was_correct_30d')]
                timeframe_stats[tf] = {
                    'total': len(tf_recommendations),
                    'win_rate_30d': len(tf_correct_30d) / len(tf_recommendations) * 100 if tf_recommendations else 0
                }
        
        return {
            'total_recommendations': len(self.recommendations),
            'verified': len(verified),
            'win_rate_7d': win_rate_7d,
            'win_rate_30d': win_rate_30d,
            'win_rate_90d': win_rate_90d,
            'avg_return_7d': avg_return_7d,
            'avg_return_30d': avg_return_30d,
            'avg_return_90d': avg_return_90d,
            'signal_strength_vs_accuracy': {
                '7d': signal_accuracy_7d,
                '30d': signal_accuracy_30d,
                '90d': signal_accuracy_90d
            },
            'timeframe_analysis': timeframe_stats
        }
    
    def get_all_recommendations(self) -> List[Dict]:
        """Get all recommendations"""
        return self.recommendations
    
    def get_recommendations_for_symbol(self, symbol: str) -> List[Dict]:
        """Get all recommendations for a specific symbol"""
        return [r for r in self.recommendations if r['symbol'] == symbol]

