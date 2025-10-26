"""
Bybit API client for portfolio tracking
"""
from pybit.unified_trading import HTTP
from config import Config

class BybitClient:
    """Client for interacting with Bybit API"""
    
    def __init__(self):
        """Initialize Bybit client with API credentials"""
        if not Config.BYBIT_API_KEY or not Config.BYBIT_SECRET_KEY:
            raise ValueError("Bybit API credentials not configured")
        
        self.session = HTTP(
            testnet=False,
            api_key=Config.BYBIT_API_KEY,
            api_secret=Config.BYBIT_SECRET_KEY
        )
    
    def get_wallet_balance(self):
        """Get wallet balance from Bybit"""
        try:
            response = self.session.get_wallet_balance(accountType="UNIFIED")
            if response['retCode'] == 0:
                return response['result']
            else:
                print(f"Bybit API error: {response['retMsg']}")
                return None
        except Exception as e:
            print(f"Error fetching Bybit wallet balance: {e}")
            return None
    
    def get_ticker_prices(self):
        """Get current ticker prices"""
        try:
            response = self.session.get_tickers(category="spot")
            if response['retCode'] == 0:
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
            
            response = self.session.get_executions(**params)
            
            if response['retCode'] == 0:
                executions = response['result'].get('list', [])
                print(f"Pobrano {len(executions)} egzekucji z Bybit")
                return executions
            else:
                print(f"Bybit API error: {response.get('retMsg', 'Unknown error')}")
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

