"""
Goal Tracking Service for Portfolio Tracker Pro
Manages investment goals, progress tracking, and milestones
Now uses SQLite database instead of JSON file
"""
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging
from database import get_db

logger = logging.getLogger(__name__)

class GoalTrackingService:
    """Service for managing investment goals"""
    
    def __init__(self):
        # No longer need to load goals on init - they're in database
        pass
    
    def _row_to_dict(self, row) -> Dict:
        """Convert database row to goal dictionary"""
        milestones = []
        try:
            milestones = json.loads(row['milestones'] or '[]')
        except (json.JSONDecodeError, TypeError):
            milestones = []
        
        return {
            "id": row['id'],
            "user_id": row['user_id'],
            "title": row['title'],
            "type": row['type'],
            "target_value": row['target_value'],
            "target_percentage": row['target_percentage'],
            "target_date": row['target_date'],
            "start_date": row['start_date'],
            "start_value": row['start_value'],
            "current_value": row['current_value'],
            "progress": row['progress'],
            "status": row['status'],
            "milestones": milestones,
            "created_at": row['created_at'],
            "updated_at": row['updated_at']
        }
    
    def create_goal(self, user_id: str, goal_data: Dict) -> Dict:
        """
        Create a new goal
        
        Args:
            user_id: User ID
            goal_data: Goal data (title, target_amount, target_date, type, etc.)
            
        Returns:
            Created goal with ID and progress
        """
        now = datetime.now().isoformat()
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO goals (
                    user_id, title, type, target_value, target_percentage,
                    target_date, start_date, start_value, current_value,
                    progress, status, milestones, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                goal_data.get("title", ""),
                goal_data.get("type", "value"),
                goal_data.get("target_value", 0),
                goal_data.get("target_percentage"),
                goal_data.get("target_date"),
                now,
                goal_data.get("start_value", 0),
                goal_data.get("start_value", 0),
                0.0,
                "active",
                json.dumps([]),
                now,
                now
            ))
            goal_id = cursor.lastrowid
            conn.commit()
        
        logger.info(f"Created goal {goal_id} for user {user_id}")
        return self.get_goal(goal_id, user_id)
    
    def get_user_goals(self, user_id: str) -> List[Dict]:
        """Get all goals for a user (excluding cancelled)"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM goals 
                WHERE user_id = ? AND status != 'cancelled'
                ORDER BY created_at DESC
            ''', (user_id,))
            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]
    
    def get_goal(self, goal_id: int, user_id: str) -> Optional[Dict]:
        """Get a specific goal by ID"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM goals WHERE id = ? AND user_id = ?', (goal_id, user_id))
            row = cursor.fetchone()
            if row:
                return self._row_to_dict(row)
            return None
    
    def update_goal_progress(self, goal_id: int, user_id: str, current_portfolio_value: float) -> Optional[Dict]:
        """
        Update goal progress based on current portfolio value
        
        Args:
            goal_id: Goal ID
            user_id: User ID
            current_portfolio_value: Current total portfolio value
            
        Returns:
            Updated goal with new progress
        """
        goal = self.get_goal(goal_id, user_id)
        if not goal:
            return None
        
        goal["current_value"] = current_portfolio_value
        goal["updated_at"] = datetime.now().isoformat()
        
        # Calculate progress based on goal type
        if goal["type"] == "value":
            # Target value goal
            start_value = goal.get("start_value", 0)
            target_value = goal.get("target_value", 0)
            
            if target_value > start_value:
                progress = ((current_portfolio_value - start_value) / (target_value - start_value)) * 100
            else:
                progress = 0.0
            
            # Check if completed
            if current_portfolio_value >= target_value and goal["status"] == "active":
                goal["status"] = "completed"
        
        elif goal["type"] == "return":
            # Target return percentage
            start_value = goal.get("start_value", 0)
            target_percentage = goal.get("target_percentage", 0)
            
            if start_value > 0:
                current_return = ((current_portfolio_value - start_value) / start_value) * 100
                progress = (current_return / target_percentage) * 100 if target_percentage > 0 else 0.0
                
                # Check if completed
                if current_return >= target_percentage and goal["status"] == "active":
                    goal["status"] = "completed"
            else:
                progress = 0.0
        
        elif goal["type"] == "diversification":
            # Diversification goal (number of assets)
            progress = 0.0
        
        goal["progress"] = max(0.0, min(100.0, progress))  # Clamp between 0 and 100
        
        # Update milestones
        self._check_milestones(goal)
        
        # Save to database
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE goals SET
                    current_value = ?, progress = ?, status = ?,
                    milestones = ?, updated_at = ?
                WHERE id = ? AND user_id = ?
            ''', (
                goal["current_value"],
                goal["progress"],
                goal["status"],
                json.dumps(goal["milestones"]),
                goal["updated_at"],
                goal_id,
                user_id
            ))
            conn.commit()
        
        return goal
    
    def _check_milestones(self, goal: Dict):
        """Check and create milestones"""
        progress = goal.get("progress", 0)
        milestones = goal.get("milestones", [])
        
        # Create milestones at 25%, 50%, 75%, 100%
        milestone_percentages = [25, 50, 75, 100]
        
        for percentage in milestone_percentages:
            milestone_name = f"{percentage}% milestone"
            
            # Check if milestone already exists
            existing = any(m.get("percentage") == percentage for m in milestones)
            
            if not existing and progress >= percentage:
                milestone = {
                    "percentage": percentage,
                    "name": milestone_name,
                    "achieved_at": datetime.now().isoformat(),
                    "value_at_achievement": goal.get("current_value", 0)
                }
                milestones.append(milestone)
        
        goal["milestones"] = milestones
    
    def update_goal(self, goal_id: int, user_id: str, updates: Dict) -> Optional[Dict]:
        """Update goal properties"""
        goal = self.get_goal(goal_id, user_id)
        if not goal:
            return None
        
        # Update allowed fields
        if "title" in updates:
            goal["title"] = updates["title"]
        if "target_value" in updates:
            goal["target_value"] = updates["target_value"]
        if "target_percentage" in updates:
            goal["target_percentage"] = updates["target_percentage"]
        if "target_date" in updates:
            goal["target_date"] = updates["target_date"]
        
        goal["updated_at"] = datetime.now().isoformat()
        
        # Recalculate progress if value changed
        if "current_value" in updates:
            goal["current_value"] = updates["current_value"]
        
        # Save to database
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE goals SET
                    title = ?, target_value = ?, target_percentage = ?,
                    target_date = ?, current_value = ?, updated_at = ?
                WHERE id = ? AND user_id = ?
            ''', (
                goal["title"],
                goal["target_value"],
                goal["target_percentage"],
                goal["target_date"],
                goal["current_value"],
                goal["updated_at"],
                goal_id,
                user_id
            ))
            conn.commit()
        
        return goal
    
    def delete_goal(self, goal_id: int, user_id: str) -> bool:
        """Delete (cancel) a goal"""
        goal = self.get_goal(goal_id, user_id)
        if not goal:
            return False
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE goals SET status = 'cancelled', updated_at = ?
                WHERE id = ? AND user_id = ?
            ''', (datetime.now().isoformat(), goal_id, user_id))
            conn.commit()
        
        logger.info(f"Cancelled goal {goal_id} for user {user_id}")
        return True
    
    def get_projections(self, goal: Dict, current_portfolio_value: float) -> Dict:
        """
        Calculate projections for goal completion
        
        Args:
            goal: Goal dictionary
            current_portfolio_value: Current portfolio value
            
        Returns:
            Projections (ETA, required rate, etc.)
        """
        if goal["status"] != "active":
            return {"eta": None, "required_monthly_growth": None, "feasible": False}
        
        if goal["type"] == "value":
            start_value = goal.get("start_value", 0)
            target_value = goal.get("target_value", 0)
            current_value = goal.get("current_value", 0)
            
            if target_value <= current_value:
                return {"eta": "Achieved!", "required_monthly_growth": 0, "feasible": True}
            
            # Calculate required growth
            remaining = target_value - current_value
            
            # Simple projection based on current rate of change
            if goal.get("start_date"):
                start_date = datetime.fromisoformat(goal["start_date"])
                days_elapsed = (datetime.now() - start_date).days
                
                if days_elapsed > 0 and current_value > start_value:
                    # Calculate average daily growth rate
                    growth_per_day = (current_value - start_value) / days_elapsed
                    
                    if growth_per_day > 0:
                        days_remaining = remaining / growth_per_day
                        eta_days = int(days_remaining)
                        
                        # Monthly growth required
                        monthly_growth = (growth_per_day * 30) / current_value * 100 if current_value > 0 else 0
                        
                        return {
                            "eta_days": eta_days,
                            "eta_months": round(eta_days / 30, 1),
                            "required_monthly_growth": round(monthly_growth, 2),
                            "feasible": True
                        }
        
        return {"eta_days": None, "required_monthly_growth": None, "feasible": False}
