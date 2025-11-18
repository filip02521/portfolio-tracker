"""
Goals and Progress Tracking System
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd

class GoalsTracker:
    """System śledzenia celów inwestycyjnych"""
    
    def __init__(self, goals_file='goals.json'):
        self.goals_file = goals_file
        self.goals = self.load_goals()
    
    def load_goals(self):
        """Load goals from file"""
        if os.path.exists(self.goals_file):
            try:
                with open(self.goals_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Default goals
        default_goals = {
            'portfolio_value': {
                'target': 10000.0,
                'current': 0.0,
                'start_date': datetime.now().isoformat(),
                'target_date': (datetime.now() + timedelta(days=365)).isoformat(),
                'enabled': True
            },
            'monthly_return': {
                'target': 5.0,  # 5% monthly return
                'current': 0.0,
                'start_date': datetime.now().isoformat(),
                'target_date': (datetime.now() + timedelta(days=30)).isoformat(),
                'enabled': True
            },
            'realized_profit': {
                'target': 1000.0,
                'current': 0.0,
                'start_date': datetime.now().isoformat(),
                'target_date': (datetime.now() + timedelta(days=180)).isoformat(),
                'enabled': True
            }
        }
        
        self.save_goals(default_goals)
        return default_goals
    
    def save_goals(self, goals=None):
        """Save goals to file"""
        if goals is None:
            goals = self.goals
        
        with open(self.goals_file, 'w') as f:
            json.dump(goals, f, indent=2)
    
    def update_portfolio_value_goal(self, current_value: float):
        """Update portfolio value goal progress"""
        if 'portfolio_value' in self.goals and self.goals['portfolio_value']['enabled']:
            self.goals['portfolio_value']['current'] = current_value
            self.save_goals()
    
    def update_realized_profit_goal(self, realized_pnl: float):
        """Update realized profit goal progress"""
        if 'realized_profit' in self.goals and self.goals['realized_profit']['enabled']:
            self.goals['realized_profit']['current'] = realized_pnl
            self.save_goals()
    
    def calculate_monthly_return(self, current_value: float, start_value: float, days_elapsed: int):
        """Calculate monthly return percentage"""
        if start_value == 0 or days_elapsed == 0:
            return 0.0
        
        # Calculate daily return
        daily_return = (current_value - start_value) / start_value
        
        # Annualize and convert to monthly
        annual_return = daily_return * (365 / days_elapsed)
        monthly_return = annual_return / 12
        
        return monthly_return * 100  # Convert to percentage
    
    def update_monthly_return_goal(self, current_value: float, start_value: float, days_elapsed: int):
        """Update monthly return goal progress"""
        if 'monthly_return' in self.goals and self.goals['monthly_return']['enabled']:
            monthly_return = self.calculate_monthly_return(current_value, start_value, days_elapsed)
            self.goals['monthly_return']['current'] = monthly_return
            self.save_goals()
    
    def get_goal_progress(self, goal_name: str) -> Dict:
        """Get progress for a specific goal"""
        if goal_name not in self.goals:
            return None
        
        goal = self.goals[goal_name]
        if not goal['enabled']:
            return None
        
        current = goal['current']
        target = goal['target']
        
        # Calculate progress percentage
        if target == 0:
            progress_percent = 0
        else:
            progress_percent = min((current / target) * 100, 100)
        
        # Calculate days remaining
        target_date = datetime.fromisoformat(goal['target_date'])
        days_remaining = (target_date - datetime.now()).days
        
        # Calculate status
        if progress_percent >= 100:
            status = "achieved"
        elif days_remaining < 0:
            status = "overdue"
        elif progress_percent >= 80:
            status = "on_track"
        elif progress_percent >= 50:
            status = "progressing"
        else:
            status = "behind"
        
        return {
            'name': goal_name,
            'current': current,
            'target': target,
            'progress_percent': progress_percent,
            'days_remaining': days_remaining,
            'status': status,
            'enabled': goal['enabled']
        }
    
    def get_all_goals_progress(self) -> List[Dict]:
        """Get progress for all goals"""
        progress_list = []
        
        for goal_name in self.goals:
            progress = self.get_goal_progress(goal_name)
            if progress:
                progress_list.append(progress)
        
        return progress_list
    
    def set_goal_target(self, goal_name: str, target: float, target_date: str = None):
        """Set target for a goal"""
        if goal_name not in self.goals:
            self.goals[goal_name] = {
                'target': target,
                'current': 0.0,
                'start_date': datetime.now().isoformat(),
                'target_date': target_date or (datetime.now() + timedelta(days=365)).isoformat(),
                'enabled': True
            }
        else:
            self.goals[goal_name]['target'] = target
            if target_date:
                self.goals[goal_name]['target_date'] = target_date
        
        self.save_goals()
        print(f"✅ Goal {goal_name} target set to {target}")
    
    def enable_goal(self, goal_name: str, enabled: bool = True):
        """Enable or disable a goal"""
        if goal_name in self.goals:
            self.goals[goal_name]['enabled'] = enabled
            self.save_goals()
            print(f"✅ Goal {goal_name} {'enabled' if enabled else 'disabled'}")
    
    def get_motivational_message(self, progress: Dict) -> str:
        """Get motivational message based on progress"""
        status = progress['status']
        progress_percent = progress['progress_percent']
        days_remaining = progress['days_remaining']
        
        if status == "achieved":
            return "🎉 Cel osiągnięty! Gratulacje!"
        elif status == "overdue":
            return f"⏰ Cel przekroczony o {abs(days_remaining)} dni. Nie poddawaj się!"
        elif status == "on_track":
            return f"🚀 Świetnie! {progress_percent:.1f}% wykonane. Jesteś na dobrej drodze!"
        elif status == "progressing":
            return f"📈 Dobry postęp! {progress_percent:.1f}% wykonane. Kontynuuj!"
        else:
            return f"💪 Zacznijmy działać! {progress_percent:.1f}% wykonane. Możesz to zrobić!"
    
    def get_goal_recommendations(self, progress: Dict) -> List[str]:
        """Get recommendations based on goal progress"""
        recommendations = []
        status = progress['status']
        days_remaining = progress['days_remaining']
        progress_percent = progress['progress_percent']
        
        if status == "behind" and days_remaining > 0:
            recommendations.append("Rozważ zwiększenie częstotliwości inwestowania")
            recommendations.append("Przeanalizuj strategię inwestycyjną")
            recommendations.append("Sprawdź czy cele są realistyczne")
        
        elif status == "on_track":
            recommendations.append("Kontynuuj obecną strategię")
            recommendations.append("Rozważ zwiększenie celów")
        
        elif status == "achieved":
            recommendations.append("Ustaw nowe, ambitniejsze cele")
            recommendations.append("Przeanalizuj co przyniosło sukces")
        
        return recommendations

# Example usage
if __name__ == "__main__":
    tracker = GoalsTracker()
    
    # Set some goals
    tracker.set_goal_target('portfolio_value', 15000.0)
    tracker.set_goal_target('monthly_return', 8.0)
    tracker.set_goal_target('realized_profit', 2000.0)
    
    # Update progress
    tracker.update_portfolio_value_goal(12000.0)
    tracker.update_realized_profit_goal(800.0)
    tracker.update_monthly_return_goal(12000.0, 10000.0, 30)
    
    # Get progress
    progress_list = tracker.get_all_goals_progress()
    
    print("Goals Progress:")
    for progress in progress_list:
        print(f"- {progress['name']}: {progress['progress_percent']:.1f}% ({progress['status']})")
        print(f"  Message: {tracker.get_motivational_message(progress)}")
        recommendations = tracker.get_goal_recommendations(progress)
        if recommendations:
            print(f"  Recommendations: {', '.join(recommendations)}")
        print()
