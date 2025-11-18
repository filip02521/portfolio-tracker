"""
Unified portfolio tracker for multiple exchanges with per-user credentials
"""
import os
from typing import Any, Dict, List, Optional

from exchanges import (
    BinanceClient,
    BybitClient,
    CoinbaseClient,
    KrakenClient,
    XTBClient,
)
from exchange_manager import ExchangeManager
from settings_manager import SettingsManager
from transaction_history import TransactionHistory

ENABLE_XTB_SYNC = os.getenv("ENABLE_XTB_SYNC", "false").lower() in ("1", "true", "yes")
ENABLED_LIVE_EXCHANGES = {
    exch.strip()
    for exch in os.getenv("ENABLED_LIVE_EXCHANGES", "binance").lower().split(",")
    if exch.strip()
}


class PortfolioTracker:
    """Main portfolio tracker class handling per-user exchange credentials"""

    def __init__(self, settings_manager: SettingsManager, market_data_service=None):
        self.settings_manager = settings_manager
        self._transaction_history = TransactionHistory()
        self._market_data_service = market_data_service

    def _instantiate_exchange_clients(self, credentials: Dict[str, Dict[str, str]]):
        """Create exchange clients based on provided credentials"""
        clients = {}

        try:
            if "binance" in ENABLED_LIVE_EXCHANGES:
                binance_creds = credentials.get("binance", {})
                clients["Binance"] = BinanceClient(
                    api_key=binance_creds.get("api_key"),
                    secret_key=binance_creds.get("secret_key"),
                )
        except Exception:
            pass

        try:
            if "bybit" in ENABLED_LIVE_EXCHANGES:
                bybit_creds = credentials.get("bybit", {})
                clients["Bybit"] = BybitClient(
                    api_key=bybit_creds.get("api_key"),
                    secret_key=bybit_creds.get("secret_key"),
                )
        except Exception:
            pass

        try:
            if "coinbase" in ENABLED_LIVE_EXCHANGES:
                coinbase_creds = credentials.get("coinbase", {})
                clients["Coinbase"] = CoinbaseClient(
                    api_key=coinbase_creds.get("api_key"),
                    api_secret=coinbase_creds.get("secret_key"),
                )
        except Exception:
            pass

        try:
            if "kraken" in ENABLED_LIVE_EXCHANGES:
                kraken_creds = credentials.get("kraken", {})
                clients["Kraken"] = KrakenClient(
                    api_key=kraken_creds.get("api_key"),
                    api_secret=kraken_creds.get("secret_key"),
                )
        except Exception:
            pass

        try:
            if ENABLE_XTB_SYNC and "xtb" in ENABLED_LIVE_EXCHANGES:
                xtb_creds = credentials.get("xtb", {})
                clients["XTB"] = XTBClient(
                    user_id=xtb_creds.get("username"),
                    password=xtb_creds.get("password"),
                )
        except Exception:
            pass

        return clients

    def get_exchange_clients(self, username: Optional[str] = None):
        """Return instantiated exchange clients for a user"""
        credentials = self.settings_manager.get_user_api_credentials(username) if username else {}
        clients = self._instantiate_exchange_clients(credentials)

        if not clients:
            manager = ExchangeManager(credentials)
            clients = manager.exchanges

        return clients

    def _build_transaction_portfolios(self, exclude_exchanges: Optional[set] = None, username: Optional[str] = None) -> List[Dict[str, Any]]:
        """Construct portfolio snapshots based on transaction history for exchanges without live sync.
        Uses current market prices from market_data_service instead of transaction prices."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            if not self._market_data_service:
                # Fallback: try to import from main module (for backwards compatibility)
                try:
                    import main
                    market_data_service = main.market_data_service
                except (ImportError, AttributeError):
                    # Last resort: create a new instance
                    from market_data_service import MarketDataService
                    market_data_service = MarketDataService()
            else:
                market_data_service = self._market_data_service
            
            exclude_exchanges = exclude_exchanges or set()
            
            # Get transactions from SQL database with error handling
            try:
                logger.debug(f"Fetching transactions for user: {username}")
                transactions = self._transaction_history.get_all_transactions(user_id=username)
                logger.debug(f"Got {len(transactions)} transactions for user: {username}")
            except Exception as e:
                logger.error(f"Error fetching transactions for user {username}: {e}", exc_info=True)
                return []  # Return empty list instead of crashing

            holdings: Dict[str, Dict[str, Dict[str, Any]]] = {}
            
            # Process transactions with error handling
            for tx_idx, tx in enumerate(transactions):
                try:
                    exchange = tx.get("exchange") or "Unknown"
                    if exchange in exclude_exchanges:
                        continue
                    
                    asset = (tx.get("asset") or "").upper()
                    if not asset:
                        continue
                    
                    tx_type = (tx.get("type") or "").lower()
                    if tx_type not in ["buy", "sell"]:
                        logger.warning(f"Unknown transaction type '{tx_type}' for transaction {tx.get('id', tx_idx)}")
                        continue
                    
                    # Safely parse amount and price
                    try:
                        amount = float(tx.get("amount", 0) or 0)
                        price = float(tx.get("price_usd", tx.get("price", 0)) or 0)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid amount or price in transaction {tx.get('id', tx_idx)}: {e}")
                        continue
                    
                    if amount <= 0:
                        logger.warning(f"Non-positive amount in transaction {tx.get('id', tx_idx)}: {amount}")
                        continue
                    
                    record = holdings.setdefault(exchange, {}).setdefault(asset, {
                        "amount": 0.0,
                        "lots": []  # FIFO lots for remaining position
                    })

                    if tx_type == "buy" and amount > 0:
                        record["amount"] += amount
                        record["lots"].append({"amount": amount, "price": price})
                    elif tx_type == "sell" and amount > 0:
                        record["amount"] -= amount
                        remaining = amount
                        while remaining > 0 and record["lots"]:
                            lot = record["lots"][0]
                            if lot["amount"] > remaining:
                                lot["amount"] -= remaining
                                remaining = 0
                            else:
                                remaining -= lot["amount"]
                                record["lots"].pop(0)
                        if record["amount"] < 0:
                            record["amount"] = 0.0
                            record["lots"].clear()
                except Exception as e:
                    logger.warning(f"Error processing transaction {tx.get('id', tx_idx)}: {e}")
                    continue  # Skip this transaction but continue processing others

            portfolios: List[Dict[str, Any]] = []
            
            # Pre-fetch prices for all unique assets to leverage cache
            # This allows market_data_service to batch requests and use cache more efficiently
            unique_assets = set()
            for exchange, assets in holdings.items():
                for asset, record in assets.items():
                    if record.get("amount", 0) > 0:
                        unique_assets.add((asset, exchange))
            
            logger.debug(f"Processing {len(unique_assets)} unique assets across {len(holdings)} exchanges")
            
            # Pre-warm cache by requesting prices (with timeout to avoid blocking)
            # Limit pre-fetch time to avoid exceeding budget
            import time
            pre_fetch_start = time.time()
            pre_fetch_timeout = 8.0  # Max 8 seconds for pre-fetch (leave time for portfolio building)
            price_cache_prefetch = {}
            
            for asset, exchange in unique_assets:
                # Check timeout - stop pre-fetching if taking too long
                if time.time() - pre_fetch_start > pre_fetch_timeout:
                    logger.debug(f"Pre-fetch timeout reached ({pre_fetch_timeout}s), stopping early. {len(price_cache_prefetch)}/{len(unique_assets)} prices cached.")
                    break
                
                try:
                    exchange_lower = exchange.lower()
                    is_crypto = any(x in exchange_lower for x in ['binance', 'bybit', 'coinbase', 'kraken', 'crypto'])
                    asset_type = 'crypto' if is_crypto else 'auto'
                    try:
                        # Use 'low' priority to avoid rate limits and timeout quickly if API is slow
                        # Cache will handle deduplication and provide stale prices if fresh ones fail
                        price_data = market_data_service.get_price(asset, asset_type=asset_type, priority='low')
                        if price_data and price_data.get('price'):
                            price_cache_prefetch[(asset, exchange)] = price_data.get('price')
                    except Exception as e:
                        logger.debug(f"Failed to pre-fetch price for {asset} on {exchange}: {e}")
                        # If price fetch fails, we'll use fallback below
                        pass
                except Exception as e:
                    logger.debug(f"Error pre-fetching price for {asset} on {exchange}: {e}")
                    continue
            
            # Build portfolios from holdings
            for exchange, assets in holdings.items():
                try:
                    balances = []
                    total_value = 0.0
                    for asset, record in assets.items():
                        try:
                            net_amount = record.get("amount", 0)
                            if net_amount <= 0:
                                continue
                            
                            # Get current market price from pre-fetched cache or fetch now
                            exchange_lower = exchange.lower()
                            is_crypto = any(x in exchange_lower for x in ['binance', 'bybit', 'coinbase', 'kraken', 'crypto'])
                            asset_type = 'crypto' if is_crypto else 'auto'
                            
                            # Try pre-fetched price first
                            current_price = price_cache_prefetch.get((asset, exchange))
                            
                            # If not in pre-fetch, try market data service (should hit cache now)
                            # Use 'low' priority and quick timeout to avoid blocking
                            if not current_price:
                                try:
                                    # Use 'low' priority - it will use cache if available, or fail fast
                                    price_data = market_data_service.get_price(asset, asset_type=asset_type, priority='low')
                                    current_price = price_data.get('price') if price_data else None
                                except Exception as e:
                                    logger.debug(f"Failed to fetch price for {asset} on {exchange}: {e}")
                                    current_price = None
                            
                            # Fallback to average cost if current price unavailable
                            if not current_price or current_price <= 0:
                                lots = record.get("lots", [])
                                total_cost = sum(lot.get("amount", 0) * lot.get("price", 0) for lot in lots)
                                if net_amount > 0 and total_cost > 0:
                                    current_price = total_cost / net_amount
                                else:
                                    current_price = 0.0
                            
                            value_usdt = net_amount * current_price
                            balances.append({
                                "asset": asset,
                                "free": net_amount,
                                "locked": 0.0,
                                "total": net_amount,
                                "value_usdt": value_usdt,
                            })
                            total_value += value_usdt
                        except Exception as e:
                            logger.warning(f"Error processing asset {asset} on {exchange}: {e}")
                            continue  # Skip this asset but continue with others

                    if balances:
                        portfolios.append({
                            "balances": balances,
                            "total_value_usdt": total_value,
                            "exchange": exchange,
                        })
                except Exception as e:
                    logger.warning(f"Error processing exchange {exchange}: {e}")
                    continue  # Skip this exchange but continue with others

            logger.debug(f"Built {len(portfolios)} portfolios from transactions")
            return portfolios
        except Exception as e:
            logger.error(f"Error in _build_transaction_portfolios for user {username}: {e}", exc_info=True)
            return []  # Return empty list instead of crashing

    def get_all_portfolios(self, username: Optional[str] = None, use_transactions_only: bool = True) -> List[Dict]:
        """Get portfolio data from all configured exchanges for a user
        
        Args:
            username: Optional username for user-specific credentials
            use_transactions_only: If True, skip exchange API calls and build portfolio only from transaction history
        """
        # If transaction-only mode, skip all exchange API calls
        if use_transactions_only:
            return self._build_transaction_portfolios(exclude_exchanges=None, username=username)
        
        # Original behavior: fetch from exchanges and supplement with transaction history
        credentials = self.settings_manager.get_user_api_credentials(username) if username else {}

        # Instantiate clients (fallback to global env variables if user not provided)
        clients = self._instantiate_exchange_clients(credentials)

        # If no user-specific clients could be created, fall back to ExchangeManager using env config
        if not clients:
            manager = ExchangeManager(credentials)
            clients = manager.exchanges

        portfolios: List[Dict] = []

        for name, client in clients.items():
            try:
                portfolio = None
                if hasattr(client, "get_portfolio_value"):
                    portfolio = client.get_portfolio_value()
                elif hasattr(client, "get_portfolio"):
                    portfolio_list = client.get_portfolio()
                    total_value = sum(item.get("value_usdt", 0) for item in portfolio_list)
                    portfolio = {
                        "balances": portfolio_list,
                        "total_value_usdt": total_value,
                        "exchange": name,
                    }

                if portfolio:
                    portfolios.append(portfolio)
                else:
                    portfolios.append(
                        {
                            "balances": [],
                            "total_value_usdt": 0,
                            "exchange": name,
                        }
                    )
            except Exception as exc:
                print(f"Error fetching {name} portfolio: {exc}")
                portfolios.append(
                    {
                        "balances": [],
                        "total_value_usdt": 0,
                        "exchange": name,
                    }
                )

        existing_exchanges = {p.get("exchange") for p in portfolios}
        manual_portfolios = self._build_transaction_portfolios(existing_exchanges, username=username)
        portfolios.extend(manual_portfolios)

        return portfolios

    def get_detailed_stats(self, username: Optional[str] = None):
        """Get detailed statistics for a user's portfolio"""
        portfolios = self.get_all_portfolios(username)

        stats = {
            "total_value": sum(p.get("total_value_usdt", 0) for p in portfolios),
            "exchange_count": len(portfolios),
            "exchanges": {},
        }

        for portfolio in portfolios:
            stats["exchanges"][portfolio["exchange"]] = {
                "value": portfolio.get("total_value_usdt", 0),
                "percentage": 0,
            }

        # Calculate percentages
        total = stats["total_value"]
        if total > 0:
            for exchange in stats["exchanges"]:
                stats["exchanges"][exchange]["percentage"] = (
                    stats["exchanges"][exchange]["value"] / total * 100
                )

        return stats

    def calculate_total_portfolio(self, username: Optional[str] = None) -> Dict[str, Any]:
        """Calculate aggregated portfolio summary for a user"""
        portfolios = self.get_all_portfolios(username)
        total_value = sum(p.get("total_value_usdt", 0) for p in portfolios)

        exchange_values = {
            p.get("exchange", "Unknown"): p.get("total_value_usdt", 0) for p in portfolios
        }

        return {
            "total_value_usd": total_value,
            "exchange_values": exchange_values,
            "portfolios": portfolios,
        }
