"""
Alert System for Portfolio Tracker
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import schedule
import time
import threading

class AlertSystem:
    """System alertów i powiadomień"""
    
    def __init__(self, config_file='alert_config.json'):
        self.config_file = config_file
        self.config = self.load_config()
        self.alerts_history = []
    
    def load_config(self):
        """Load alert configuration"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Default configuration
        default_config = {
            'email_alerts': False,
            'email_settings': {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'email': '',
                'password': ''
            },
            'alert_thresholds': {
                'portfolio_change_percent': 5.0,  # Alert if portfolio changes by 5%
                'daily_change_percent': 10.0,     # Alert if daily change > 10%
                'low_balance_threshold': 100.0     # Alert if balance < $100
            },
            'notification_frequency': 'daily',  # daily, weekly, monthly
            'enabled_alerts': [
                'portfolio_change',
                'daily_change',
                'low_balance',
                'new_transaction'
            ]
        }
        
        self.save_config(default_config)
        return default_config
    
    def save_config(self, config=None):
        """Save alert configuration"""
        if config is None:
            config = self.config
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def check_portfolio_change_alert(self, current_value: float, previous_value: float):
        """Check if portfolio change exceeds threshold"""
        if previous_value == 0:
            return None
        
        change_percent = abs((current_value - previous_value) / previous_value * 100)
        threshold = self.config['alert_thresholds']['portfolio_change_percent']
        
        if change_percent >= threshold:
            direction = "wzrost" if current_value > previous_value else "spadek"
            return {
                'type': 'portfolio_change',
                'message': f"Portfolio {direction} o {change_percent:.2f}% (próg: {threshold}%)",
                'current_value': current_value,
                'previous_value': previous_value,
                'change_percent': change_percent,
                'timestamp': datetime.now().isoformat()
            }
        
        return None
    
    def check_daily_change_alert(self, daily_change_percent: float):
        """Check if daily change exceeds threshold"""
        threshold = self.config['alert_thresholds']['daily_change_percent']
        
        if abs(daily_change_percent) >= threshold:
            direction = "wzrost" if daily_change_percent > 0 else "spadek"
            return {
                'type': 'daily_change',
                'message': f"Dzienny {direction} portfolio o {abs(daily_change_percent):.2f}% (próg: {threshold}%)",
                'change_percent': daily_change_percent,
                'timestamp': datetime.now().isoformat()
            }
        
        return None
    
    def check_low_balance_alert(self, balances: List[Dict]):
        """Check for low balances"""
        threshold = self.config['alert_thresholds']['low_balance_threshold']
        low_balances = []
        
        for balance in balances:
            if balance.get('value_usdt', 0) < threshold:
                low_balances.append({
                    'exchange': balance.get('exchange', 'Unknown'),
                    'asset': balance.get('asset', 'Unknown'),
                    'value': balance.get('value_usdt', 0)
                })
        
        if low_balances:
            return {
                'type': 'low_balance',
                'message': f"Znaleziono {len(low_balances)} niskich sald (< ${threshold})",
                'low_balances': low_balances,
                'timestamp': datetime.now().isoformat()
            }
        
        return None
    
    def check_new_transaction_alert(self, new_transactions: List[Dict]):
        """Check for new transactions"""
        if new_transactions:
            return {
                'type': 'new_transaction',
                'message': f"Dodano {len(new_transactions)} nowych transakcji",
                'transactions': new_transactions,
                'timestamp': datetime.now().isoformat()
            }
        
        return None
    
    def send_email_alert(self, alert: Dict):
        """Send email alert"""
        if not self.config['email_alerts']:
            return False
        
        try:
            email_config = self.config['email_settings']
            
            msg = MIMEMultipart()
            msg['From'] = email_config['email']
            msg['To'] = email_config['email']  # Send to self for now
            msg['Subject'] = f"Portfolio Alert: {alert['type']}"
            
            body = f"""
Portfolio Tracker Alert

Typ: {alert['type']}
Wiadomość: {alert['message']}
Czas: {alert['timestamp']}

---
Portfolio Tracker
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['email'], email_config['password'])
            text = msg.as_string()
            server.sendmail(email_config['email'], email_config['email'], text)
            server.quit()
            
            print(f"✅ Email alert sent: {alert['type']}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email alert: {e}")
            return False
    
    def process_alert(self, alert: Dict):
        """Process and store alert"""
        if alert is None:
            return
        
        # Store alert in history
        self.alerts_history.append(alert)
        
        # Send email if enabled
        if self.config['email_alerts']:
            self.send_email_alert(alert)
        
        print(f"🔔 Alert: {alert['message']}")
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict]:
        """Get alerts from last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_alerts = []
        for alert in self.alerts_history:
            alert_time = datetime.fromisoformat(alert['timestamp'])
            if alert_time >= cutoff_time:
                recent_alerts.append(alert)
        
        return recent_alerts
    
    def run_portfolio_checks(self, portfolio_data: Dict):
        """Run all portfolio checks"""
        alerts = []
        
        # Check portfolio change
        if 'portfolio_change' in self.config['enabled_alerts']:
            current_value = portfolio_data.get('current_value', 0)
            previous_value = portfolio_data.get('previous_value', 0)
            alert = self.check_portfolio_change_alert(current_value, previous_value)
            if alert:
                alerts.append(alert)
        
        # Check daily change
        if 'daily_change' in self.config['enabled_alerts']:
            daily_change = portfolio_data.get('daily_change_percent', 0)
            alert = self.check_daily_change_alert(daily_change)
            if alert:
                alerts.append(alert)
        
        # Check low balances
        if 'low_balance' in self.config['enabled_alerts']:
            balances = portfolio_data.get('balances', [])
            alert = self.check_low_balance_alert(balances)
            if alert:
                alerts.append(alert)
        
        # Process all alerts
        for alert in alerts:
            self.process_alert(alert)
        
        return alerts
    
    def configure_email(self, email: str, password: str, smtp_server: str = 'smtp.gmail.com', smtp_port: int = 587):
        """Configure email settings"""
        self.config['email_alerts'] = True
        self.config['email_settings'] = {
            'smtp_server': smtp_server,
            'smtp_port': smtp_port,
            'email': email,
            'password': password
        }
        self.save_config()
        print("✅ Email configuration saved")
    
    def set_thresholds(self, portfolio_change: float = None, daily_change: float = None, low_balance: float = None):
        """Set alert thresholds"""
        if portfolio_change is not None:
            self.config['alert_thresholds']['portfolio_change_percent'] = portfolio_change
        if daily_change is not None:
            self.config['alert_thresholds']['daily_change_percent'] = daily_change
        if low_balance is not None:
            self.config['alert_thresholds']['low_balance_threshold'] = low_balance
        
        self.save_config()
        print("✅ Alert thresholds updated")

# Example usage
if __name__ == "__main__":
    alert_system = AlertSystem()
    
    # Test configuration
    alert_system.set_thresholds(portfolio_change=3.0, daily_change=5.0, low_balance=50.0)
    
    # Test portfolio data
    test_portfolio = {
        'current_value': 10000,
        'previous_value': 9500,
        'daily_change_percent': 5.26,
        'balances': [
            {'exchange': 'Binance', 'asset': 'BTC', 'value_usdt': 5000},
            {'exchange': 'Binance', 'asset': 'ETH', 'value_usdt': 30},  # Low balance
            {'exchange': 'Bybit', 'asset': 'SOL', 'value_usdt': 2000}
        ]
    }
    
    # Run checks
    alerts = alert_system.run_portfolio_checks(test_portfolio)
    print(f"Generated {len(alerts)} alerts")
    
    # Show recent alerts
    recent = alert_system.get_recent_alerts(1)
    print(f"Recent alerts: {len(recent)}")
