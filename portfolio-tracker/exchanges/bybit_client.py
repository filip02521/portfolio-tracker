"""
Bybit API client for portfolio tracking
"""
import time
from pybit.unified_trading import HTTP
from pybit.exceptions import FailedRequestError
from config import Config

class BybitClient:
    """Client for interacting with Bybit API"""
    
    def __init__(self):
        """Initialize Bybit client with API credentials"""
        Config.init()  # Initialize config to load credentials
        if not Config.BYBIT_API_KEY or not Config.BYBIT_SECRET_KEY:
            raise ValueError("Bybit API credentials not configured")
        
        self.session = HTTP(
            testnet=False,
            api_key=Config.BYBIT_API_KEY,
            api_secret=Config.BYBIT_SECRET_KEY
        )
    
    def _make_request_with_retry(self, func, max_retries=3, base_delay=1):
        """Make API request with exponential backoff retry logic and better error handling"""
        for attempt in range(max_retries):
            try:
                return func()
            except FailedRequestError as e:
                error_msg = str(e)
                error_code = getattr(e, 'ret_code', 0)
                
                # Handle different types of errors
                if "rate limit" in error_msg.lower() or "403" in error_msg or error_code == 403:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)  # Shorter delays: 1s, 2s, 4s
                        print(f"Rate limit hit, waiting {delay:.1f} seconds before retry {attempt + 1}/{max_retries}")
                        time.sleep(delay)
                        continue
                    else:
                        print(f"Max retries reached for rate limit. Error: {e}")
                        raise e
                elif "ip is from the usa" in error_msg.lower() or "restricted" in error_msg.lower():
                    print(f"Bybit API restricted for this IP/location: {e}")
                    # Don't retry for IP restrictions - they won't change
                    print("IP restriction detected - not retrying")
                    raise e
                elif "invalid api key" in error_msg.lower() or error_code == 10003:
                    print(f"Invalid API key: {e}")
                    raise e
                elif "api key not found" in error_msg.lower() or error_code == 10004:
                    print(f"API key not found: {e}")
                    raise e
                else:
                    # Other API error, retry with shorter delay
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        print(f"API error, retrying in {delay:.1f} seconds: {e}")
                        time.sleep(delay)
                        continue
                    else:
                        print(f"Max retries reached for API error: {e}")
                        raise e
            except Exception as e:
                print(f"Unexpected error in API request: {e}")
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    print(f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                    continue
                else:
                    raise e
        
    def get_wallet_balance(self):
        """Get wallet balance from Bybit"""
        try:
            def _request():
                return self.session.get_wallet_balance(accountType="UNIFIED")
            
            response = self._make_request_with_retry(_request)
            if response and response['retCode'] == 0:
                return response['result']
            else:
                print(f"Bybit API error: {response.get('retMsg', 'Unknown error') if response else 'No response'}")
                return None
        except Exception as e:
            print(f"Error fetching Bybit wallet balance: {e}")
            return None
    
    def get_ticker_prices(self):
        """Get current ticker prices"""
        try:
            def _request():
                return self.session.get_tickers(category="spot")
            
            response = self._make_request_with_retry(_request)
            if response and response['retCode'] == 0:
                tickers = response['result']['list']
                return {ticker['symbol']: float(ticker['lastPrice']) for ticker in tickers}
            return {}
        except Exception as e:
            print(f"Error fetching Bybit prices: {e}")
            return {}
    
    def get_trade_history(self, symbol=None, limit=100):
        """Get trade history from Bybit"""
        try:
            # Bybit unified trading - get execution list
            params = {
                "category": "spot",
                "limit": limit
            }
            
            # Add symbol if specified
            if symbol:
                params['symbol'] = symbol
            
            def _request():
                return self.session.get_executions(**params)
            
            response = self._make_request_with_retry(_request)
            
            if response and response['retCode'] == 0:
                executions = response['result'].get('list', [])
                print(f"Pobrano {len(executions)} egzekucji z Bybit")
                return executions
            else:
                print(f"Bybit API error: {response.get('retMsg', 'Unknown error') if response else 'No response'}")
                return []
        except Exception as e:
            print(f"Error fetching Bybit trade history: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_portfolio_value(self):
        """Get total portfolio value in USDT"""
        try:
            wallet_data = self.get_wallet_balance()
            if not wallet_data:
                return {'balances': [], 'total_value_usdt': 0, 'exchange': 'Bybit'}
            
            balances = []
            total_value = 0
            
            # Parse Bybit wallet structure
            coin_list = wallet_data.get('list', [])
            for account in coin_list:
                for coin in account.get('coin', []):
                    # Bybit uses 'walletBalance' for total balance
                    wallet_balance = coin.get('walletBalance', 0) or 0
                    locked_value = coin.get('locked', 0) or 0
                    
                    # Convert to string first to handle empty strings
                    balance_str = str(wallet_balance).strip()
                    locked_str = str(locked_value).strip()
                    
                    try:
                        total = float(balance_str) if balance_str else 0.0
                        locked = float(locked_str) if locked_str else 0.0
                        available = total - locked
                    except (ValueError, TypeError):
                        total = 0.0
                        locked = 0.0
                        available = 0.0
                    
                    if total > 0:
                        balances.append({
                            'asset': coin['coin'],
                            'free': available,
                            'locked': locked,
                            'total': total
                        })
                        
                        # Calculate USDT value
                        asset_value = 0
                        if coin['coin'] == 'USDT':
                            asset_value = total
                        else:
                            # Try to get price from ticker
                            prices = self.get_ticker_prices()
                            symbol = coin['coin'] + 'USDT'
                            if symbol in prices:
                                asset_value = total * prices[symbol]
                        
                        # Add value to balance dict
                        balances[-1]['value_usdt'] = asset_value
                        total_value += asset_value
            
            return {
                'balances': balances,
                'total_value_usdt': total_value,
                'exchange': 'Bybit'
            }
        except Exception as e:
            print(f"Error calculating Bybit portfolio value: {e}")
            return {'balances': [], 'total_value_usdt': 0, 'exchange': 'Bybit'}

