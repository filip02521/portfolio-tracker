"""
XTB API client for portfolio tracking  
Note: XTB uses xStation API (JSON-RPC)
"""
import requests
import hashlib
from typing import Optional
from config import Config

class XTBClient:
    """Client for interacting with XTB API"""
    
    def __init__(self, user_id: Optional[str] = None, password: Optional[str] = None):
        """Initialize XTB client with credentials"""
        Config.init()  # Initialize config to load credentials
        self.user_id = user_id or Config.XTB_USER_ID
        self.password = password or Config.XTB_PASSWORD
        if not self.user_id or not self.password:
            raise ValueError("XTB credentials not configured")
        
        self.base_url = "https://xapi.xtb.com"
        self.session_id = None
        
    def get_password_hash(self):
        """Generate password hash for XTB authentication"""
        return hashlib.md5(self.password.encode()).hexdigest()
    
    def _send_command(self, command, arguments=None):
        """Send JSON-RPC command to XTB API"""
        try:
            url = f"{self.base_url}/json-rpc"
            payload = {
                "method": command,
                "params": arguments or {}
            }
            
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status'):
                    return data.get('returnData')
                else:
                    error_msg = data.get('errorDescr') or data.get('errorCode') or 'Unknown error'
                    print(f"XTB API error ({command}): {error_msg}")
                    return None
            else:
                print(f"XTB HTTP error ({command}): {response.status_code}")
                return None
        except requests.exceptions.Timeout:
            print(f"XTB API timeout ({command})")
            return None
        except Exception as e:
            print(f"Error sending XTB command {command}: {e}")
            return None
    
    def login(self):
        """Login to XTB and get session ID"""
        try:
            result = self._send_command("login", {
                "userId": self.user_id,
                "password": self.get_password_hash()
            })
            
            if result:
                self.session_id = result.get('sessionId')
                return True
            return False
        except Exception as e:
            print(f"Error logging into XTB: {e}")
            return False
    
    def get_margin_level(self):
        """Get margin level information"""
        try:
            if not self.session_id:
                if not self.login():
                    return None
            
            # Use streaming API approach with session ID
            result = self._send_command("getMarginLevel", {
                "sessionId": self.session_id
            })
            
            return result
        except Exception as e:
            print(f"Error fetching XTB margin level: {e}")
            return None
    
    def get_trades(self):
        """Get open trades"""
        try:
            if not self.session_id:
                if not self.login():
                    return []
            
            result = self._send_command("getTrades", {
                "sessionId": self.session_id,
                "openedOnly": True
            })
            
            return result or []
        except Exception as e:
            print(f"Error fetching XTB trades: {e}")
            return []
    
    def get_symbols(self):
        """Get available symbols"""
        try:
            result = self._send_command("getSymbol", {"symbol": "BTCUSD"})
            return result if result else []
        except Exception as e:
            print(f"Error fetching XTB symbols: {e}")
            return []
    
    def get_portfolio_value(self):
        """Get total portfolio value"""
        try:
            margin_data = self.get_margin_level()
            if not margin_data:
                return {'balances': [], 'total_value_usdt': 0, 'exchange': 'XTB'}
            
            balances = []
            
            # Parse XTB margin data - balance in account currency
            balance = margin_data.get('balance', 0)
            equity = margin_data.get('equity', 0)
            margin = margin_data.get('margin', 0)
            free_margin = margin_data.get('marginFree', 0)
            
            # XTB uses account currency (typically USD or EUR)
            balances.append({
                'asset': 'USD',  # XTB typically uses USD
                'free': free_margin,
                'locked': margin,
                'total': balance
            })
            
            # Use equity as total value (balance + unrealized P/L)
            total_value = equity
            
            return {
                'balances': balances,
                'total_value_usdt': total_value,
                'exchange': 'XTB'
            }
        except Exception as e:
            print(f"Error calculating XTB portfolio value: {e}")
            return {'balances': [], 'total_value_usdt': 0, 'exchange': 'XTB'}

