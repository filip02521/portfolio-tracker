"""
Kraken API client for portfolio tracking
"""
import requests
import time
import base64
import hmac
import hashlib
from typing import Dict, List, Optional
from config import Config
from requests.exceptions import Timeout, ConnectionError, RequestException

class KrakenClient:
    """Client for interacting with Kraken API"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """Initialize Kraken client with API credentials"""
        Config.init()
        self.api_key = api_key or Config.KRAKEN_API_KEY
        self.api_secret = api_secret or Config.KRAKEN_SECRET_KEY
        
        if not self.api_key or not self.api_secret:
            raise ValueError("Kraken API credentials not configured")
        
        self.base_url = "https://api.kraken.com"
        self.timeout = 15
    
    def _generate_signature(self, endpoint: str, nonce: str, post_data: str) -> str:
        """Generate Kraken API signature (HMAC-SHA512)"""
        message = nonce + post_data
        signature = hmac.new(
            base64.b64decode(self.api_secret),
            endpoint.encode('utf-8') + hashlib.sha256(nonce.encode('utf-8') + post_data.encode('utf-8')).digest(),
            hashlib.sha512
        ).digest()
        return base64.b64encode(signature).decode()
    
    def _make_request_with_retry(self, method: str, endpoint: str, params: Dict = None, max_retries: int = 3):
        """Make API request with retry logic"""
        url = f"{self.base_url}{endpoint}"
        
        # Prepare POST data for private endpoints
        if method.upper() == 'POST' and params:
            import urllib.parse
            post_data = urllib.parse.urlencode(params)
        else:
            post_data = ""
        
        # Generate signature for private endpoints
        if '/private/' in endpoint:
            nonce = str(int(time.time() * 1000))
            # Add nonce to POST data if not already present
            if method.upper() == 'POST' and params and 'nonce' not in params:
                params['nonce'] = nonce
                post_data = urllib.parse.urlencode(params)
            
            signature = self._generate_signature(endpoint, nonce, post_data)
            headers = {
                "API-Key": self.api_key,
                "API-Sign": signature,
                "Content-Type": "application/x-www-form-urlencoded"
            }
        else:
            headers = {"Content-Type": "application/json"}
        
        for attempt in range(max_retries):
            try:
                if method.upper() == 'GET':
                    response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
                else:
                    response = requests.post(url, headers=headers, data=post_data, timeout=self.timeout)
                
                response.raise_for_status()
                return response.json()
                
            except Timeout:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise ConnectionError(f"Kraken API timeout after {max_retries} retries")
            except ConnectionError:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise
            except Exception as e:
                raise RequestException(f"Kraken API request failed: {str(e)}")
    
    def get_balance(self) -> Dict:
        """
        Get account balance
        
        Returns:
            Dictionary with account balance information
        """
        try:
            # Kraken Private API endpoint: POST /0/private/Balance
            response = self._make_request_with_retry('POST', '/0/private/Balance', {})
            result = response.get('result', {})
            
            total_balance = 0.0
            for currency, balance in result.items():
                balance_float = float(balance)
                # Convert to USD if needed (simplified)
                if currency in ['ZUSD', 'USD']:
                    total_balance += balance_float
            
            return {
                "balance": total_balance,
                "currency": "USD",
                "available": total_balance
            }
        except Exception as e:
            print(f"Error fetching Kraken balance: {e}")
            return {}
    
    def get_portfolio(self) -> List[Dict]:
        """
        Get portfolio holdings
        
        Returns:
            List of asset holdings
        """
        try:
            # Kraken Private API endpoint: POST /0/private/Balance
            response = self._make_request_with_retry('POST', '/0/private/Balance', {})
            result = response.get('result', {})
            
            portfolio = []
            for currency, balance in result.items():
                balance_float = float(balance)
                if balance_float > 0:
                    # Map Kraken currency codes to standard symbols
                    symbol_map = {
                        'XXBT': 'BTC',
                        'XETH': 'ETH',
                        'XZEC': 'ZEC',
                        'XLTC': 'LTC',
                        'ZUSD': 'USD',
                        'ZEUR': 'EUR'
                    }
                    asset = symbol_map.get(currency, currency)
                    
                    portfolio.append({
                        "asset": asset,
                        "amount": balance_float,
                        "value_usdt": balance_float  # Placeholder, needs price conversion
                    })
            
            return portfolio
        except Exception as e:
            print(f"Error fetching Kraken portfolio: {e}")
            return []
    
    def get_transactions(self, limit: int = 50) -> List[Dict]:
        """
        Get recent transactions
        
        Returns:
            List of transactions
        """
        try:
            # Kraken Private API endpoint: POST /0/private/Ledgers
            # This endpoint requires additional parameters like type, asset, etc.
            return []
        except Exception as e:
            print(f"Error fetching Kraken transactions: {e}")
            return []
    
    def place_order(self, symbol: str, side: str, amount: float, order_type: str = "market") -> Dict:
        """
        Place a new order
        
        Args:
            symbol: Trading pair (e.g., 'XBTUSD')
            side: 'buy' or 'sell'
            amount: Amount to trade
            order_type: 'market' or 'limit'
            
        Returns:
            Order details
        """
        try:
            # Kraken Private API endpoint: POST /0/private/AddOrder
            params = {
                "nonce": str(int(time.time() * 1000)),
                "pair": symbol,
                "type": side,
                "ordertype": order_type,
                "volume": str(amount)
            }
            
            response = self._make_request_with_retry('POST', '/0/private/AddOrder', params)
            return response
        except Exception as e:
            print(f"Error placing Kraken order: {e}")
            return {}
    
    def get_products(self) -> List[Dict]:
        """
        Get available trading products
        
        Returns:
            List of trading pairs
        """
        try:
            # Kraken Public API endpoint: GET /0/public/AssetPairs
            response = self._make_request_with_retry('GET', '/0/public/AssetPairs')
            pairs = response.get('result', {})
            
            products = []
            for pair_name, pair_data in pairs.items():
                products.append({
                    "symbol": pair_name,
                    "display_name": pair_data.get('altname', pair_name),
                    "base": pair_data.get('base', ''),
                    "quote": pair_data.get('quote', '')
                })
            
            return products
        except Exception as e:
            print(f"Error fetching Kraken products: {e}")
            return []

