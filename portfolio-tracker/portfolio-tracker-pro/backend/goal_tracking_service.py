"""
Goal Tracking Service for Portfolio Tracker Pro
Manages investment goals, progress tracking, and milestones
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class GoalTrackingService:
    """Service for managing investment goals"""
    
    GOALS_FILE = "goals.json"
    
    def __init__(self):
        self.goals = self._load_goals()
    
    def _load_goals(self) -> List[Dict]:
        """Load goals from JSON file"""
        if os.path.exists(self.GOALS_FILE):
            try:
                with open(self.GOALS_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading goals: {e}")
                return []
        return []
    
    def _save_goals(self):
        """Save goals to JSON file"""
        try:
            with open(self.GOALS_FILE, 'w') as f:
                json.dump(self.goals, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving goals: {e}")
            return False
    
    def create_goal(self, user_id: str, goal_data: Dict) -> Dict:
        """
        Create a new goal
        
        Args:
            user_id: User ID
            goal_data: Goal data (title, target_amount, target_date, type, etc.)
            
        Returns:
            Created goal with ID and progress
        """
        goal_id = len(self.goals) + 1
        
        goal = {
            "id": goal_id,
            "user_id": user_id,
            "title": goal_data.get("title", ""),
            "type": goal_data.get("type", "value"),  # value, return, diversification
            "target_value": goal_data.get("target_value", 0),
            "target_percentage": goal_data.get("target_percentage"),  # For return goals
            "target_date": goal_data.get("target_date"),
            "start_date": datetime.now().isoformat(),
            "start_value": goal_data.get("start_value", 0),  # Starting portfolio value
            "current_value": goal_data.get("start_value", 0),
            "progress": 0.0,
            "status": "active",  # active, completed, cancelled
            "milestones": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.goals.append(goal)
        self._save_goals()
        
        logger.info(f"Created goal {goal_id} for user {user_id}")
        return goal
    
    def get_user_goals(self, user_id: str) -> List[Dict]:
        """Get all goals for a user"""
        return [g for g in self.goals if g.get("user_id") == user_id and g.get("status") != "cancelled"]
    
    def get_goal(self, goal_id: int, user_id: str) -> Optional[Dict]:
        """Get a specific goal by ID"""
        for goal in self.goals:
            if goal.get("id") == goal_id and goal.get("user_id") == user_id:
                return goal
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
                goal["completed_at"] = datetime.now().isoformat()
        
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
                    goal["completed_at"] = datetime.now().isoformat()
            else:
                progress = 0.0
        
        elif goal["type"] == "diversification":
            # Diversification goal (number of assets)
            # This would need additional data from portfolio
            progress = 0.0
        
        goal["progress"] = max(0.0, min(100.0, progress))  # Clamp between 0 and 100
        
        # Update milestones
        self._check_milestones(goal)
        
        self._save_goals()
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
            # Progress will be recalculated on next update_goal_progress call
        
        self._save_goals()
        return goal
    
    def delete_goal(self, goal_id: int, user_id: str) -> bool:
        """Delete (cancel) a goal"""
        goal = self.get_goal(goal_id, user_id)
        if not goal:
            return False
        
        goal["status"] = "cancelled"
        goal["updated_at"] = datetime.now().isoformat()
        
        self._save_goals()
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


