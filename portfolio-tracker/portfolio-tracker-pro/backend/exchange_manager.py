"""
ExchangeManager for unified multi-exchange portfolio aggregation
"""
import logging
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from exchanges import BinanceClient, BybitClient, CoinbaseClient, KrakenClient, XTBClient

logger = logging.getLogger(__name__)

ENABLE_XTB_SYNC = os.getenv("ENABLE_XTB_SYNC", "false").lower() in ("1", "true", "yes")
ENABLED_LIVE_EXCHANGES = {
    exch.strip()
    for exch in os.getenv("ENABLED_LIVE_EXCHANGES", "binance").lower().split(",")
    if exch.strip()
}

class ExchangeManager:
    """Manages aggregation of portfolio data from multiple exchanges"""
    
    SUPPORTED_EXCHANGES = ["Binance", "Bybit", "Coinbase", "Kraken", "XTB"]

    def __init__(self, credentials: Optional[Dict[str, Dict[str, str]]] = None):
        """Initialize ExchangeManager with user-specific exchange clients"""
        self.credentials = credentials or {}
        self.exchanges: Dict[str, object] = {}
        self._cache = None
        self._cache_timestamp = None
        self.cache_ttl = 300  # 5 minutes

        # Initialize exchange clients using provided credentials (if available)
        self._initialize_exchanges()
    
    def _initialize_exchanges(self):
        """Initialize all exchange clients"""
        # Binance
        try:
            if "binance" in ENABLED_LIVE_EXCHANGES:
                binance_creds = self.credentials.get("binance", {})
                self.exchanges["Binance"] = BinanceClient(
                    api_key=binance_creds.get("api_key"),
                    secret_key=binance_creds.get("secret_key"),
                )
                logger.info("✓ Binance initialized")
        except (ValueError, Exception) as exc:
            logger.info("Binance client unavailable: %s", exc)

        # Bybit
        try:
            if "bybit" in ENABLED_LIVE_EXCHANGES:
                bybit_creds = self.credentials.get("bybit", {})
                self.exchanges["Bybit"] = BybitClient(
                    api_key=bybit_creds.get("api_key"),
                    secret_key=bybit_creds.get("secret_key"),
                )
                logger.info("✓ Bybit initialized")
        except (ValueError, Exception) as exc:
            logger.info("Bybit client unavailable: %s", exc)

        # Coinbase
        try:
            if "coinbase" in ENABLED_LIVE_EXCHANGES:
                coinbase_creds = self.credentials.get("coinbase", {})
                self.exchanges["Coinbase"] = CoinbaseClient(
                    api_key=coinbase_creds.get("api_key"),
                    api_secret=coinbase_creds.get("secret_key"),
                )
                logger.info("✓ Coinbase initialized")
        except (ValueError, Exception) as exc:
            logger.info("Coinbase client unavailable: %s", exc)

        # Kraken
        try:
            if "kraken" in ENABLED_LIVE_EXCHANGES:
                kraken_creds = self.credentials.get("kraken", {})
                self.exchanges["Kraken"] = KrakenClient(
                    api_key=kraken_creds.get("api_key"),
                    api_secret=kraken_creds.get("secret_key"),
                )
                logger.info("✓ Kraken initialized")
        except (ValueError, Exception) as exc:
            logger.info("Kraken client unavailable: %s", exc)

        # XTB
        if ENABLE_XTB_SYNC and "xtb" in ENABLED_LIVE_EXCHANGES:
            try:
                xtb_creds = self.credentials.get("xtb", {})
                self.exchanges["XTB"] = XTBClient(
                    user_id=xtb_creds.get("username"),
                    password=xtb_creds.get("password"),
                )
                logger.info("✓ XTB initialized")
            except (ValueError, Exception) as exc:
                logger.info("XTB client unavailable: %s", exc)
        elif "xtb" in ENABLED_LIVE_EXCHANGES:
            logger.info("XTB sync disabled via ENABLE_XTB_SYNC flag")
        else:
            logger.info("XTB synchronization disabled; using transaction history fallback")
    
    def normalize_symbol(self, symbol: str, exchange: str) -> str:
        """
        Normalize exchange-specific symbols to a common format
        
        Args:
            symbol: Exchange-specific symbol
            exchange: Exchange name
            
        Returns:
            Normalized symbol
        """
        # Symbol normalization maps
        normalizations = {
            'Kraken': {
                'XXBT': 'BTC',
                'XETH': 'ETH',
                'XZEC': 'ZEC',
                'XLTC': 'LTC',
                'ZUSD': 'USD',
                'ZEUR': 'EUR',
                'XBTUSD': 'BTCUSD'
            },
            'Coinbase': {
                'XBT': 'BTC',
                'BTCEUR': 'BTC-EUR'
            },
            'Binance': {
                'XBT': 'BTC'
            },
            'Bybit': {
                'XBTUSD': 'BTCUSD'
            }
        }
        
        symbol_map = normalizations.get(exchange, {})
        return symbol_map.get(symbol, symbol)
    
    def get_unified_portfolio(self, refresh: bool = False) -> Dict:
        """
        Get unified portfolio aggregated from all exchanges
        
        Args:
            refresh: Force refresh cache
            
        Returns:
            Dictionary with aggregated portfolio data
        """
        # Check cache
        if not refresh and self._cache and self._cache_timestamp:
            age = (datetime.now() - self._cache_timestamp).total_seconds()
            if age < self.cache_ttl:
                logger.debug("Returning cached portfolio data")
                return self._cache
        
        # Fetch portfolios from all exchanges
        portfolios = self._fetch_all_portfolios()
        
        # Aggregate balances
        aggregated = self._aggregate_balances(portfolios)
        
        # Cache result
        self._cache = aggregated
        self._cache_timestamp = datetime.now()
        
        return aggregated
    
    def _fetch_all_portfolios(self) -> List[Dict]:
        """Fetch portfolio data from all exchanges"""
        portfolios = []
        
        for name, client in self.exchanges.items():
            try:
                # Try get_portfolio_value first (Binance, Bybit, XTB)
                if hasattr(client, 'get_portfolio_value'):
                    portfolio = client.get_portfolio_value()
                # Fallback to get_portfolio (Coinbase, Kraken)
                elif hasattr(client, 'get_portfolio'):
                    portfolio_list = client.get_portfolio()
                    # Convert list format to dict format
                    total_value = sum(item.get('value_usdt', 0) for item in portfolio_list)
                    portfolio = {
                        'balances': portfolio_list,
                        'total_value_usdt': total_value,
                        'exchange': name
                    }
                else:
                    portfolio = None
                
                if portfolio:
                    portfolios.append(portfolio)
                    logger.debug(f"✓ Fetched portfolio from {name}")
                else:
                    # Add empty portfolio
                    portfolios.append({
                        'balances': [],
                        'total_value_usdt': 0,
                        'exchange': name
                    })
                    logger.warning(f"⚠ Empty portfolio from {name}")
            except Exception as e:
                logger.error(f"Error fetching {name} portfolio: {e}")
                portfolios.append({
                    'balances': [],
                    'total_value_usdt': 0,
                    'exchange': name
                })
        
        return portfolios
    
    def _aggregate_balances(self, portfolios: List[Dict]) -> Dict:
        """
        Aggregate balances from multiple exchanges by asset symbol
        
        Args:
            portfolios: List of portfolio dictionaries from exchanges
            
        Returns:
            Aggregated portfolio dictionary
        """
        # Aggregate balances by asset
        asset_balances = defaultdict(lambda: {
            'amount': 0.0,
            'value_usdt': 0.0,
            'exchanges': []
        })
        
        total_value = 0.0
        active_exchanges = 0
        
        for portfolio in portfolios:
            exchange_name = portfolio.get('exchange', 'Unknown')
            exchange_value = portfolio.get('total_value_usdt', 0)
            
            if exchange_value > 0:
                active_exchanges += 1
                total_value += exchange_value
            
            # Aggregate balances
            for balance in portfolio.get('balances', []):
                asset = balance.get('asset', '')
                normalized_asset = self.normalize_symbol(asset, exchange_name)
                
                # Use appropriate keys based on exchange format
                amount = balance.get('total', balance.get('amount', 0))
                value = balance.get('value_usdt', 0)
                
                asset_balances[normalized_asset]['amount'] += amount
                asset_balances[normalized_asset]['value_usdt'] += value
                asset_balances[normalized_asset]['exchanges'].append(exchange_name)
        
        # Convert to list format
        balances = []
        for asset, data in asset_balances.items():
            balances.append({
                'asset': asset,
                'total': data['amount'],
                'value_usdt': data['value_usdt'],
                'exchanges': data['exchanges']
            })
        
        # Sort by value descending
        balances.sort(key=lambda x: x.get('value_usdt', 0), reverse=True)
        
        return {
            'balances': balances,
            'total_value_usdt': total_value,
            'active_exchanges': active_exchanges,
            'total_exchanges': len(self.exchanges),
            'last_updated': datetime.now().isoformat()
        }
    
    def refresh_cache(self):
        """Force refresh of cached portfolio data"""
        logger.info("Refreshing exchange portfolio cache")
        return self.get_unified_portfolio(refresh=True)
    
    def get_exchange_status(self) -> List[Dict]:
        """
        Get status of all exchange connections
        
        Returns:
            List of exchange status dictionaries
        """
        status_list = []

        for name in self.SUPPORTED_EXCHANGES:
            if name in self.exchanges:
                # Try to get portfolio to check connectivity
                try:
                    client = self.exchanges[name]
                    if hasattr(client, 'get_portfolio_value'):
                        portfolio = client.get_portfolio_value()
                    elif hasattr(client, 'get_portfolio'):
                        portfolio_list = client.get_portfolio()
                        total_value = sum(item.get('value_usdt', 0) for item in portfolio_list)
                        portfolio = {
                            'total_value_usdt': total_value,
                            'exchange': name
                        }
                    else:
                        portfolio = None
                    
                    status_list.append({
                        'exchange': name,
                        'connected': True,
                        'total_value': portfolio.get('total_value_usdt', 0) if portfolio else 0,
                        'error': None
                    })
                except Exception as e:
                    status_list.append({
                        'exchange': name,
                        'connected': False,
                        'total_value': 0,
                        'error': str(e)
                    })
            else:
                status_list.append({
                    'exchange': name,
                    'connected': False,
                    'total_value': 0,
                    'error': 'Not configured'
                })
        
        return status_list










