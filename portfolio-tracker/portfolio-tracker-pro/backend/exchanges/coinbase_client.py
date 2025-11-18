"""
Coinbase API client for portfolio tracking
"""
import requests
import time
import hmac
import hashlib
import base64
from typing import Dict, List, Optional
from config import Config
from requests.exceptions import Timeout, ConnectionError, RequestException

class CoinbaseClient:
    """Client for interacting with Coinbase Pro API (Advanced Trade)"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """Initialize Coinbase client with API credentials"""
        Config.init()
        self.api_key = api_key or Config.COINBASE_API_KEY
        self.api_secret = api_secret or Config.COINBASE_SECRET_KEY
        
        if not self.api_key or not self.api_secret:
            raise ValueError("Coinbase API credentials not configured")
        
        self.base_url = "https://api.coinbase.com/api/v3/brokerage"
        self.timeout = 15
    
    def _generate_signature(self, method: str, path: str, body: str = "") -> str:
        """Generate HMAC signature for Coinbase Advanced Trade API"""
        timestamp = str(int(time.time()))
        message = timestamp + method + path + body
        
        if self.api_secret:
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).digest()
            signature_b64 = base64.b64encode(signature).decode('utf-8')
            return timestamp, signature_b64
        return timestamp, ""
    
    def _make_request_with_retry(self, method: str, endpoint: str, params: Dict = None, max_retries: int = 3):
        """Make API request with retry logic"""
        url = f"{self.base_url}{endpoint}"
        
        # Generate HMAC signature
        body = ""
        if params and method.upper() == 'POST':
            import json
            body = json.dumps(params)
        
        timestamp, signature = self._generate_signature(method.upper(), endpoint, body)
        
        headers = {
            "Content-Type": "application/json",
            "CB-ACCESS-KEY": self.api_key,
            "CB-ACCESS-SIGN": signature,
            "CB-ACCESS-TIMESTAMP": timestamp
        }
        
        for attempt in range(max_retries):
            try:
                if method.upper() == 'GET':
                    response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
                else:
                    response = requests.post(url, headers=headers, data=body, timeout=self.timeout)
                
                response.raise_for_status()
                return response.json()
                
            except Timeout:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise ConnectionError(f"Coinbase API timeout after {max_retries} retries")
            except ConnectionError:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise
            except Exception as e:
                raise RequestException(f"Coinbase API request failed: {str(e)}")
    
    def get_balance(self) -> Dict:
        """
        Get account balance
        
        Returns:
            Dictionary with account balance information
        """
        try:
            # Coinbase Advanced Trade API endpoint: GET /accounts
            response = self._make_request_with_retry('GET', '/accounts')
            accounts = response.get('accounts', [])
            
            if accounts:
                total_balance = 0.0
                for acc in accounts:
                    balance = float(acc.get('available_balance', {}).get('value', 0))
                    if acc.get('available_balance', {}).get('currency') == 'USD':
                        total_balance += balance
                
                return {
                    "balance": total_balance,
                    "currency": "USD",
                    "available": total_balance
                }
            
            return {"balance": 0.0, "currency": "USD", "available": 0.0}
        except Exception as e:
            print(f"Error fetching Coinbase balance: {e}")
            return {}
    
    def get_portfolio(self) -> List[Dict]:
        """
        Get portfolio holdings
        
        Returns:
            List of asset holdings
        """
        try:
            # Coinbase Advanced Trade API endpoint: GET /accounts
            response = self._make_request_with_retry('GET', '/accounts')
            accounts = response.get('accounts', [])
            
            portfolio = []
            for acc in accounts:
                if float(acc.get('available_balance', {}).get('value', 0)) > 0:
                    currency = acc.get('available_balance', {}).get('currency', '')
                    amount = float(acc.get('available_balance', {}).get('value', 0))
                    
                    # TODO: Convert to USD value using current prices
                    # For now, return raw balances
                    portfolio.append({
                        "asset": currency,
                        "amount": amount,
                        "value_usdt": amount  # Placeholder
                    })
            
            return portfolio
        except Exception as e:
            print(f"Error fetching Coinbase portfolio: {e}")
            return []
    
    def get_transactions(self, limit: int = 50) -> List[Dict]:
        """
        Get recent transactions
        
        Returns:
            List of transactions
        """
        try:
            # Coinbase Advanced Trade API endpoint: GET /fills
            # Note: This requires additional parameters like product_id
            return []
        except Exception as e:
            print(f"Error fetching Coinbase transactions: {e}")
            return []
    
    def place_order(self, symbol: str, side: str, amount: float, order_type: str = "market") -> Dict:
        """
        Place a new order
        
        Args:
            symbol: Trading pair (e.g., 'BTC-USD')
            side: 'buy' or 'sell'
            amount: Amount to trade
            order_type: 'market' or 'limit'
            
        Returns:
            Order details
        """
        try:
            # Coinbase Advanced Trade API endpoint: POST /orders
            payload = {
                "product_id": symbol,
                "side": side,
                "order_configuration": {
                    "market_market_ioc": {
                        "quote_size": str(amount) if side == 'buy' else None,
                        "base_size": str(amount) if side == 'sell' else None
                    }
                }
            }
            
            response = self._make_request_with_retry('POST', '/orders', payload)
            return response
        except Exception as e:
            print(f"Error placing Coinbase order: {e}")
            return {}
    
    def get_products(self) -> List[Dict]:
        """
        Get available trading products
        
        Returns:
            List of trading pairs
        """
        try:
            # Coinbase Advanced Trade API endpoint: GET /products
            response = self._make_request_with_retry('GET', '/products')
            products = response.get('products', [])
            
            return [
                {
                    "symbol": p.get('product_id', ''),
                    "display_name": p.get('display_name', '')
                }
                for p in products
            ]
        except Exception as e:
            print(f"Error fetching Coinbase products: {e}")
            return []

