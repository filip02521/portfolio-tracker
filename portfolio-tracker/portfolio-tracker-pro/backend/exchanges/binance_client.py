"""
Binance API client for portfolio tracking
"""
import time
from typing import Optional
from binance.client import Client
from binance.exceptions import BinanceAPIException
from config import Config
from requests.exceptions import Timeout, ConnectionError, RequestException

class BinanceClient:
    """Client for interacting with Binance API"""
    
    def __init__(self, api_key: Optional[str] = None, secret_key: Optional[str] = None):
        """Initialize Binance client with API credentials"""
        Config.init()  # Initialize config to load credentials if not provided
        self.api_key = api_key or Config.BINANCE_API_KEY
        self.secret_key = secret_key or Config.BINANCE_SECRET_KEY
        if not self.api_key or not self.secret_key:
            raise ValueError("Binance API credentials not configured")
        
        self.client = Client(
            api_key=self.api_key,
            api_secret=self.secret_key,
            requests_params={'timeout': 15}  # Set timeout to 15 seconds
        )
    
    def _make_request_with_retry(self, func, max_retries=5, base_delay=2):
        """Make API request with exponential backoff retry logic and better error handling"""
        for attempt in range(max_retries):
            try:
                return func()
            except BinanceAPIException as e:
                error_msg = str(e)
                error_code = getattr(e, 'code', 0)
                
                # Handle different types of errors
                if "rate limit" in error_msg.lower() or "429" in error_msg or error_code == 429:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt) + (attempt * 0.5)  # Exponential backoff with jitter
                        print(f"Rate limit hit, waiting {delay:.1f} seconds before retry {attempt + 1}/{max_retries}")
                        time.sleep(delay)
                        continue
                    else:
                        print(f"Max retries reached for rate limit. Error: {e}")
                        raise e
                elif "restricted location" in error_msg.lower() or "403" in error_msg or error_code == 403:
                    print(f"Binance API restricted for this location: {e}")
                    # Don't retry for location restrictions - they won't change
                    print("Location restriction detected - not retrying")
                    raise e
                elif "invalid api-key" in error_msg.lower() or error_code == 2014:
                    print(f"Invalid API key: {e}")
                    raise e
                elif "api key does not exist" in error_msg.lower() or error_code == 2015:
                    print(f"API key does not exist: {e}")
                    raise e
                else:
                    # Other API error, retry with longer delay
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        print(f"API error, retrying in {delay:.1f} seconds: {e}")
                        time.sleep(delay)
                        continue
                    else:
                        print(f"Max retries reached for API error: {e}")
                        raise e
            except Timeout as e:
                error_msg = str(e)
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    print(f"Binance API timeout (read timeout), retrying in {delay:.1f} seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    continue
                else:
                    print(f"Max retries reached for timeout error: {e}")
                    raise ConnectionError(f"Binance API timeout after {max_retries} retries: {error_msg}")
            except ConnectionError as e:
                error_msg = str(e)
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    print(f"Binance API connection error, retrying in {delay:.1f} seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    continue
                else:
                    print(f"Max retries reached for connection error: {e}")
                    raise ConnectionError(f"Binance API connection failed after {max_retries} retries: {error_msg}")
            except RequestException as e:
                error_msg = str(e)
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    print(f"Binance API request error, retrying in {delay:.1f} seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    continue
                else:
                    print(f"Max retries reached for request error: {e}")
                    raise RequestException(f"Binance API request failed after {max_retries} retries: {error_msg}")
            except Exception as e:
                error_msg = str(e)
                error_type = type(e).__name__
                print(f"Unexpected error in Binance API request ({error_type}): {error_msg}")
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    print(f"Retrying in {delay:.1f} seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    continue
                else:
                    print(f"Max retries reached for unexpected error: {e}")
                    raise Exception(f"Binance API error after {max_retries} retries ({error_type}): {error_msg}")
        
    def get_account_info(self):
        """Get account information"""
        try:
            def _request():
                return self.client.get_account()
            
            return self._make_request_with_retry(_request)
        except Exception as e:
            print(f"Error fetching Binance account info: {e}")
            return None
    
    def get_balances(self):
        """Get non-zero balances from Binance (spot wallet + Earn products as LD*)"""
        try:
            account = self.get_account_info()
            if not account:
                return []
            
            balances = []
            earn_mapping = {}  # To combine LD* assets with their base assets
            
            for balance in account['balances']:
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                
                if total > 0:
                    asset = balance['asset']
                    
                    # Check if this is an Earn product (LD* prefix)
                    if asset.startswith('LD') and len(asset) > 2:
                        # LDETH -> ETH, LDBTC -> BTC, etc.
                        base_asset = asset[2:]  # Remove 'LD' prefix
                        
                        # Combine with existing Earn balance if exists
                        if base_asset not in earn_mapping:
                            earn_mapping[base_asset] = {
                                'asset': base_asset,
                                'free': 0,
                                'locked': 0,
                                'total': 0,
                                'is_earn': True
                            }
                        
                        earn_mapping[base_asset]['locked'] += total
                        earn_mapping[base_asset]['total'] += total
                    else:
                        # Regular spot balance
                        balances.append({
                            'asset': asset,
                            'free': free,
                            'locked': locked,
                            'total': total
                        })
            
            # Add combined Earn balances
            balances.extend(earn_mapping.values())
            
            return balances
        except Exception as e:
            print(f"Error fetching Binance balances: {e}")
            return []
    
    def get_earn_balances(self):
        """Get balances from Binance Earn products (Flexible Savings, Locked Staking, DeFi Staking)"""
        try:
            earn_balances = {}
            
            # 1. Flexible Savings and other lending products using API request
            try:
                lending_account = self.client._request_api('get', 'sapi/v1/lending/union/account', signed=True)
                if lending_account and 'positionAmountVos' in lending_account:
                    for position in lending_account['positionAmountVos']:
                        asset = position['asset']
                        amount = float(position['amount'])
                        if amount > 0:
                            if asset not in earn_balances:
                                earn_balances[asset] = 0
                            earn_balances[asset] += amount
            except Exception as e:
                print(f"Note: Could not fetch Binance Lending balances: {e}")
            
            # 2. DeFi Staking positions
            try:
                staking_positions = self.client._request_api('get', 'sapi/v1/staking/stakingRecord', signed=True, params={'product': 'STAKING'})
                if staking_positions:
                    for position in staking_positions:
                        if 'asset' in position and 'amount' in position:
                            asset = position['asset']
                            amount = float(position['amount'])
                            if amount > 0:
                                if asset not in earn_balances:
                                    earn_balances[asset] = 0
                                earn_balances[asset] += amount
            except Exception as e:
                print(f"Note: Could not fetch Binance Staking positions: {e}")
            
            # 3. Locked Staking
            try:
                locked_staking = self.client._request_api('get', 'sapi/v1/staking/stakingRecord', signed=True, params={'product': 'F_DEFI'})
                if locked_staking:
                    for position in locked_staking:
                        if 'asset' in position and 'amount' in position:
                            asset = position['asset']
                            amount = float(position['amount'])
                            if amount > 0:
                                if asset not in earn_balances:
                                    earn_balances[asset] = 0
                                earn_balances[asset] += amount
            except Exception as e:
                print(f"Note: Could not fetch Binance Locked Staking: {e}")
            
            # Convert to list format matching get_balances()
            balances = []
            for asset, total in earn_balances.items():
                balances.append({
                    'asset': asset,
                    'free': 0,
                    'locked': total,
                    'total': total,
                    'is_earn': True  # Flag to identify Earn products
                })
            
            return balances
        except Exception as e:
            print(f"Error fetching Binance Earn balances: {e}")
            return []
    
    def get_ticker_prices(self, symbols):
        """Get current prices for symbols"""
        try:
            prices = self.client.get_all_tickers()
            price_dict = {ticker['symbol']: float(ticker['price']) for ticker in prices}
            return price_dict
        except Exception as e:
            print(f"Error fetching Binance prices: {e}")
            return {}
    
    def get_symbol_price(self, symbol):
        """Get price for a specific symbol"""
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except Exception:
            return None
    
    def get_trade_history(self, symbol: Optional[str] = None, limit: int = 100):
        """Get trade history from Binance"""
        try:
            if symbol:
                trades = self.client.get_my_trades(symbol=symbol, limit=limit)
            else:
                trades = []
                balances = self.get_balances()
                symbols_to_check = []
                for balance in balances:
                    asset = balance.get('asset')
                    if not asset or asset == 'USDT':
                        continue
                    symbols_to_check.append(f"{asset}USDT")
                # Limit number of symbols to avoid rate limits and timeouts
                # Reduced from 10 to 5 to speed up sync
                for sym in symbols_to_check[:5]:
                    try:
                        # Use smaller limit per symbol to reduce total time
                        symbol_trades = self.client.get_my_trades(symbol=sym, limit=min(limit, 20))
                        trades.extend(symbol_trades)
                        # Stop if we have enough trades
                        if len(trades) >= limit:
                            break
                    except Exception as e:
                        # Skip on error to continue with other symbols
                        print(f"Error fetching trades for {sym}: {e}")
                        continue
            return trades[:limit]  # Ensure we don't return more than requested
        except Exception as e:
            print(f"Error fetching Binance trade history: {e}")
            return []
    
    def get_portfolio_value(self):
        """Get total portfolio value in USDT (including Earn products)"""
        try:
            # Get all balances (spot + Earn products as LD*)
            balances = self.get_balances()
            
            if not balances:
                return {'balances': [], 'total_value_usdt': 0, 'exchange': 'Binance'}
            
            # Handle USDT separately
            usdt_balance = next((b for b in balances if b['asset'] == 'USDT'), None)
            usdt_value = usdt_balance['total'] if usdt_balance else 0
            
            # Get all ticker prices
            prices = self.get_ticker_prices([])
            
            total_value = usdt_value
            
            # Calculate USDT value for each asset
            for balance in balances:
                asset_value = 0
                
                if balance['asset'] == 'USDT':
                    asset_value = balance['total']
                else:
                    # Try direct USDT pair first
                    symbol = balance['asset'] + 'USDT'
                    if symbol in prices:
                        asset_value = balance['total'] * prices[symbol]
                    else:
                        # Try BUSD pair if USDT not available
                        busd_symbol = balance['asset'] + 'BUSD'
                        if busd_symbol in prices:
                            asset_value = balance['total'] * prices[busd_symbol]
                        else:
                            # Try BNB if available (as intermediary)
                            bnb_symbol = balance['asset'] + 'BNB'
                            bnb_usdt_symbol = 'BNBUSDT'
                            if bnb_symbol in prices and bnb_usdt_symbol in prices:
                                asset_value = balance['total'] * prices[bnb_symbol] * prices[bnb_usdt_symbol]
                
                # Add value to balance dict
                balance['value_usdt'] = asset_value
                total_value += asset_value
            
            return {
                'balances': balances,
                'total_value_usdt': total_value,
                'exchange': 'Binance'
            }
        except Exception as e:
            print(f"Error calculating Binance portfolio value: {e}")
            return {'balances': [], 'total_value_usdt': 0, 'exchange': 'Binance'}

