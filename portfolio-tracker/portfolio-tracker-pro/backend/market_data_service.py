"""
Market Data Service - Fetches real-time market prices
"""
import requests
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from logging_config import get_logger
from config import Config
import time
import os
import datetime as dt
import re
from threading import Lock
from prometheus_client import Counter

try:
    import pandas as pd
except ImportError:
    pd = None

logger = get_logger(__name__)

try:
    import redis  # Optional
except Exception:
    redis = None

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logger.warning("yfinance not available - Yahoo Finance fallback disabled")

market_provider_requests = Counter(
    'market_provider_requests_total',
    'Total number of market data provider requests',
    ['provider', 'status']
)
market_cache_hits = Counter(
    'market_cache_hits_total',
    'Number of cache hits for market data',
)

class MarketDataService:
    def __init__(self):
        # TTL configuration per data type (seconds)
        # Values can be customized via environment variables to avoid hardcoding.
        self._ttl_config: Dict[str, float] = {
            'price': float(os.getenv('MARKET_TTL_PRICE_SEC', '10')),          # Real-time prices
            'history': float(os.getenv('MARKET_TTL_HISTORY_SEC', '3600')),    # Historical data
            'news': float(os.getenv('MARKET_TTL_NEWS_SEC', '300')),           # News headlines
            'symbol_info': float(os.getenv('MARKET_TTL_SYMBOL_INFO_SEC', '86400')),  # Static symbol metadata
        }

        # Cache for prices and history
        self._price_cache: Dict[str, Dict] = {}
        # Backwards-compatible attributes, backed by TTL map
        self._cache_ttl = self._ttl_config['price']
        self._history_cache_ttl = self._ttl_config['history']
        self._news_cache: Dict[str, Dict[str, Any]] = {}
        self._news_cache_ttl = self._ttl_config['news']
        self._max_news_age = timedelta(days=int(os.getenv('MAX_NEWS_AGE_DAYS', '21')))
        self._max_news_age_fallback = timedelta(days=int(os.getenv('MAX_NEWS_AGE_FALLBACK_DAYS', '180')))
        if self._max_news_age_fallback < self._max_news_age:
            self._max_news_age_fallback = self._max_news_age
        preferred_sources = os.getenv(
            'PREFERRED_NEWS_SOURCES',
            'reuters,bloomberg,the wall street journal,benzinga,motley fool,cnbc,financial times'
        )
        blocked_sources = os.getenv(
            'BLOCKED_NEWS_SOURCES',
            'globenewswire inc.,pr newswire,business wire,accesswire,newsfile'
        )
        self._preferred_sources = {
            source.strip().lower(): idx
            for idx, source in enumerate(preferred_sources.split(','), start=1)
            if source.strip()
        }
        self._blocked_sources = {source.strip().lower() for source in blocked_sources.split(',') if source.strip()}
        # Provider rate limiting state
        self._provider_lock: Lock = Lock()
        self._provider_state: Dict[str, Dict[str, float]] = {
            'alpha_vantage': {
                'last_request': 0.0,
                'min_interval': 12.0,
                'cooldown_until': 0.0,
                'failures': 0.0,
                'cooldown_step': 120.0  # 2 minutes after rate limit
            },
            'polygon': {
                'last_request': 0.0,
                'min_interval': 1.0,
                'cooldown_until': 0.0,
                'failures': 0.0,
                'cooldown_step': 90.0
            },
            'yahoo_finance': {
                'last_request': 0.0,
                'min_interval': 2.0,
                'cooldown_until': 0.0,
                'failures': 0.0,
                'cooldown_step': 30.0
            },
            'binance': {
                'last_request': 0.0,
                'min_interval': 0.7,
                'cooldown_until': 0.0,
                'failures': 0.0,
                'cooldown_step': 15.0
            },
            'coingecko': {
                'last_request': 0.0,
                'min_interval': 1.0,
                'cooldown_until': 0.0,
                'failures': 0.0,
                'cooldown_step': 30.0
            },
            'polygon_news': {
                'last_request': 0.0,
                'min_interval': 1.0,
                'cooldown_until': 0.0,
                'failures': 0.0,
                'cooldown_step': 120.0
            },
            'finnhub_news': {
                'last_request': 0.0,
                'min_interval': 1.0,
                'cooldown_until': 0.0,
                'failures': 0.0,
                'cooldown_step': 120.0
            }
        }
        # Track delisted/inactive assets to avoid spamming logs & HTTP calls
        self._inactive_symbols: Dict[str, float] = {}
        # Request collapsing (simple in-flight guard)
        self._inflight: Dict[str, float] = {}
        # Priority configuration for request handling
        # Values tune how long we are willing to wait for a provider when respecting rate limits
        self._priority_max_wait: Dict[str, float] = {
            'critical': 5.0,
            'high': 3.0,
            'normal': 2.0,
            'low': 0.25,
        }
        # Optional Redis
        self._redis = None
        redis_url = os.getenv('REDIS_URL')
        if redis and redis_url:
            try:
                self._redis = redis.Redis.from_url(redis_url, decode_responses=True)
                self._redis.ping()
                logger.info("Redis cache enabled for market data")
            except Exception as e:
                logger.warning(f"Redis unavailable: {e}")
                self._redis = None
        self._stock_fetch_enabled = os.getenv('ENABLE_STOCK_PRICE_FETCH', 'true').lower() in ('1', 'true', 'yes')
        provider_env = os.getenv('STOCK_PRICE_PROVIDER_ORDER', 'polygon,alpha_vantage,yahoo_finance')
        self._stock_provider_order = [p.strip().lower() for p in provider_env.split(',') if p.strip()]
        if not self._stock_provider_order:
            self._stock_provider_order = ['yfinance', 'polygon', 'alpha_vantage']
        if not self._stock_fetch_enabled:
            logger.info("Stock price fetching disabled via ENABLE_STOCK_PRICE_FETCH")
        
    def _get_provider_state(self, provider: str) -> Dict[str, float]:
        with self._provider_lock:
            state = self._provider_state.setdefault(provider, {
                'last_request': 0.0,
                'min_interval': 0.0,
                'cooldown_until': 0.0,
                'failures': 0.0,
                'cooldown_step': 30.0
            })
            return state.copy()

    def _get_max_wait_for_priority(self, priority: Optional[str], default: float) -> float:
        """
        Map logical priority to max_wait budget for rate limiting.

        priority:
            - critical: tolerate longer waits to avoid missing fresh data
            - high: moderate tolerance
            - normal: baseline
            - low: prefer fast-fail and cache/fallback instead of blocking
        """
        if not priority:
            return default
        return self._priority_max_wait.get(priority, default)

    def _respect_rate_limit(self, provider: str, max_wait: float = 5.0) -> bool:
        state_snapshot = self._get_provider_state(provider)
        now = time.time()
        wait_time = 0.0
        cooldown_until = state_snapshot.get('cooldown_until', 0.0)
        if cooldown_until and cooldown_until > now:
            wait_time = max(wait_time, cooldown_until - now)
        min_interval = state_snapshot.get('min_interval', 0.0)
        last_request = state_snapshot.get('last_request', 0.0)
        elapsed = now - last_request
        if min_interval and elapsed < min_interval:
            wait_time = max(wait_time, min_interval - elapsed)
        if wait_time <= 0:
            return True
        if wait_time > max_wait:
            logger.debug(f"{provider} provider cooldown {wait_time:.1f}s exceeds max wait {max_wait:.1f}s, skipping request.")
            return False
        logger.debug(f"Respecting {provider} rate limit: sleeping {wait_time:.2f}s before request.")
        time.sleep(wait_time)
        return True

    def _get_ttl(self, data_type: str, default: Optional[float] = None) -> float:
        """
        Helper to fetch TTL for a given data type with a sane default.
        """
        if default is None:
            default = self._cache_ttl
        return float(self._ttl_config.get(data_type, default))

    def _record_request(
        self,
        provider: str,
        success: bool,
        rate_limited: bool = False,
        cooldown: Optional[float] = None
    ) -> None:
        with self._provider_lock:
            state = self._provider_state.setdefault(provider, {
                'last_request': 0.0,
                'min_interval': 0.0,
                'cooldown_until': 0.0,
                'failures': 0.0,
                'cooldown_step': 30.0
            })
            state['last_request'] = time.time()
            if success:
                state['failures'] = 0.0
                if not rate_limited:
                    state['cooldown_until'] = 0.0
            else:
                state['failures'] = state.get('failures', 0.0) + 1.0
                step = cooldown or state.get('cooldown_step', 30.0)
                if rate_limited:
                    state['cooldown_until'] = max(state.get('cooldown_until', 0.0), time.time() + step)
                elif state['failures'] >= 3 and step:
                    state['cooldown_until'] = max(state.get('cooldown_until', 0.0), time.time() + min(step, 120.0))

    def _set_cooldown(self, provider: str, seconds: float) -> None:
        if seconds <= 0:
            return
        with self._provider_lock:
            state = self._provider_state.setdefault(provider, {
                'last_request': 0.0,
                'min_interval': 0.0,
                'cooldown_until': 0.0,
                'failures': 0.0,
                'cooldown_step': 30.0
            })
            state['cooldown_until'] = max(state.get('cooldown_until', 0.0), time.time() + seconds)
            state['failures'] = state.get('failures', 0.0) + 1.0

    def _http_get_with_retry(
        self,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 8.0,
        max_retries: int = 3,
        base_delay: float = 1.0,
        provider: Optional[str] = None,
        retry_statuses: Tuple[int, ...] = (429, 500, 502, 503, 504),
        backoff_factor: float = 2.0,
    ) -> requests.Response:
        """
        Unified helper for HTTP GET with exponential backoff.

        Retries network errors and selected HTTP status codes.
        """
        last_exc: Optional[Exception] = None
        for attempt in range(max_retries):
            try:
                resp = requests.get(url, params=params, headers=headers, timeout=timeout)
                if resp.status_code in retry_statuses and attempt < max_retries - 1:
                    delay = base_delay * (backoff_factor ** attempt)
                    logger.debug(
                        f"HTTP {resp.status_code} from {url} (provider={provider}); "
                        f"retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(delay)
                    continue
                return resp
            except requests.RequestException as exc:
                last_exc = exc
                if attempt >= max_retries - 1:
                    break
                delay = base_delay * (backoff_factor ** attempt)
                logger.debug(
                    f"HTTP request error for {url} (provider={provider}): {exc}; "
                    f"retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(delay)

        if last_exc:
            raise last_exc
        raise RuntimeError(f"HTTP retries exhausted for {url} (provider={provider})")

    def get_crypto_price(self, symbol: str, priority: str = 'normal') -> Optional[float]:
        """Get current crypto price using a provider chain: Binance → CoinGecko/Yahoo → cache."""
        symbol_upper = symbol.upper()
        cache_key = f"CRYPTO_{symbol}"

        # If symbol was previously marked inactive, return cached zero-price.
        if symbol_upper in self._inactive_symbols:
            return 0.0

        # 1) Fresh cache check (Redis, then in-memory)
        try:
            price_ttl = self._get_ttl('price')
            if self._redis:
                try:
                    val = self._redis.get(cache_key)
                    if val is not None:
                        market_cache_hits.inc()
                        return float(val)
                except Exception:
                    pass
            if cache_key in self._price_cache:
                cached = self._price_cache[cache_key]
                if time.time() - cached.get('timestamp', 0.0) < price_ttl:
                    market_cache_hits.inc()
                    return cached.get('price')
        except Exception:
            # Cache errors should never break price fetching
            pass

        def cache_price(value: float, inactive: bool = False) -> float:
            self._price_cache[cache_key] = {
                'price': value,
                'timestamp': time.time(),
                'inactive': inactive,
            }
            if self._redis:
                try:
                    self._redis.setex(cache_key, int(self._get_ttl('price')), str(value))
                except Exception:
                    pass
            return value

        # Provider 1: Binance
        try:
            if not self._respect_rate_limit('binance', max_wait=self._get_max_wait_for_priority(priority, 2.0)):
                self._record_request('binance', success=False, rate_limited=True)
                logger.debug(f"Skipping Binance price fetch for {symbol_upper} due to cooldown/priority.")
            else:
                url = "https://api.binance.com/api/v3/ticker/price"
                params = {"symbol": f"{symbol_upper}USDT"}
                response = self._http_get_with_retry(
                    url,
                    params=params,
                    timeout=5,
                    max_retries=3,
                    base_delay=1.0,
                    provider='binance',
                )
                # Treat unsupported symbols (400/404) as delisted – return a zero price instead of propagating errors
                if response.status_code in (400, 404):
                    if symbol_upper not in self._inactive_symbols:
                        logger.info(
                            "Binance reports %s as unavailable (%s); treating as inactive with price 0.",
                            symbol_upper,
                            response.status_code,
                        )
                    self._inactive_symbols[symbol_upper] = time.time()
                    self._record_request('binance', success=True)
                    return cache_price(0.0, inactive=True)

                response.raise_for_status()
                data = response.json() or {}
                price_val = float(data.get('price', 0.0))
                if price_val > 0:
                    self._record_request('binance', success=True)
                    if symbol_upper in self._inactive_symbols:
                        self._inactive_symbols.pop(symbol_upper, None)
                    return cache_price(price_val)
        except Exception as e:
            logger.debug(f"Binance crypto price fetch failed for {symbol_upper}: {e}")
            self._record_request('binance', success=False)

        # Provider 2: CoinGecko (simple/price endpoint)
        try:
            if not self._respect_rate_limit('coingecko', max_wait=self._get_max_wait_for_priority(priority, 2.0)):
                self._record_request('coingecko', success=False, rate_limited=True)
                logger.debug(f"Skipping CoinGecko price fetch for {symbol_upper} due to cooldown/priority.")
            else:
                # CoinGecko requires an "id" (e.g. "bitcoin"), but we try a best-effort mapping
                # by using the symbol as id (works for many majors like btc, eth).
                cg_id = symbol.lower()
                url = "https://api.coingecko.com/api/v3/simple/price"
                params = {
                    "ids": cg_id,
                    "vs_currencies": "usd",
                }
                response = self._http_get_with_retry(
                    url,
                    params=params,
                    timeout=6,
                    max_retries=3,
                    base_delay=1.0,
                    provider='coingecko',
                )
                if response.status_code == 429:
                    # Soft failure with cooldown
                    self._record_request('coingecko', success=False, rate_limited=True, cooldown=60.0)
                response.raise_for_status()
                data = response.json() or {}
                if cg_id in data and isinstance(data[cg_id], dict):
                    price_val_raw = data[cg_id].get('usd')
                    if price_val_raw:
                        price_val = float(price_val_raw)
                        self._record_request('coingecko', success=True)
                        return cache_price(price_val)
        except Exception as e:
            logger.debug(f"CoinGecko crypto price fetch failed for {symbol_upper}: {e}")
            self._record_request('coingecko', success=False)

        # Provider 3: Yahoo Finance (BTC-USD style ticker)
        if YFINANCE_AVAILABLE:
            try:
                yf_symbol = f"{symbol_upper}-USD"
                if not self._respect_rate_limit('yahoo_finance', max_wait=self._get_max_wait_for_priority(priority, 2.0)):
                    self._record_request('yahoo_finance', success=False, rate_limited=True)
                else:
                    ticker = yf.Ticker(yf_symbol)
                    info = ticker.info
                    price_raw = (
                        info.get('currentPrice')
                        or info.get('regularMarketPrice')
                        or info.get('previousClose')
                    )
                    if price_raw:
                        price_val = float(price_raw)
                        self._record_request('yahoo_finance', success=True)
                        return cache_price(price_val)
            except Exception as e:
                logger.debug(f"Yahoo Finance crypto price fetch failed for {symbol_upper}: {e}")
                self._record_request('yahoo_finance', success=False)

        # Final fallback: return stale cached value if available (even if TTL expired)
        cached_entry = self._price_cache.get(cache_key)
        if cached_entry and 'price' in cached_entry:
            logger.warning(
                "All crypto providers failed for %s – returning stale cached price (age=%.1fs).",
                symbol_upper,
                time.time() - cached_entry.get('timestamp', 0.0),
            )
            return cached_entry.get('price')

        logger.warning(f"Crypto price for {symbol_upper} not available from any provider")
        return None
    
    def get_stock_price(self, symbol: str, priority: str = 'normal') -> Optional[float]:
        """Get current stock price using configured provider order."""
        if not self._stock_fetch_enabled:
            return None

        cache_key = f"STOCK_{symbol}"

        # Cache check (Redis first, then in-memory)
        if self._redis:
            try:
                val = self._redis.get(cache_key)
                if val is not None:
                    market_cache_hits.inc()
                    return float(val)
            except Exception:
                pass
        cached_entry = self._price_cache.get(cache_key)
        if cached_entry and time.time() - cached_entry.get('timestamp', 0) < self._get_ttl('price'):
            market_cache_hits.inc()
            return cached_entry.get('price')

        Config.init()

        def cache_price(value: float, inactive: bool = False) -> float:
            self._price_cache[cache_key] = {
                'price': value,
                'timestamp': time.time(),
                'inactive': inactive,
            }
            if self._redis:
                try:
                    self._redis.setex(cache_key, self._cache_ttl, str(value))
                except Exception:
                    pass
            return value

        def fetch_from_yfinance() -> Optional[float]:
            if not YFINANCE_AVAILABLE:
                return None
            try:
                if not self._respect_rate_limit('yahoo_finance', max_wait=self._get_max_wait_for_priority(priority, 2.0)):
                    self._record_request('yahoo_finance', success=False, rate_limited=True)
                    return None
                market_provider_requests.labels('yahoo_finance', 'attempt').inc()
                ticker = yf.Ticker(symbol)
                info = ticker.info
                price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
                if price:
                    price_val = float(price)
                    cache_price(price_val)
                    self._record_request('yahoo_finance', success=True)
                    market_provider_requests.labels('yahoo_finance', 'success').inc()
                    return price_val
            except Exception as exc:
                logger.debug(f"Yahoo Finance fetch failed for {symbol}: {exc}")
                self._record_request('yahoo_finance', success=False)
                market_provider_requests.labels('yahoo_finance', 'error').inc()
            return None

        def fetch_from_polygon() -> Optional[float]:
            polygon_key = Config.POLYGON_API_KEY
            if not polygon_key:
                return None
            if not self._respect_rate_limit('polygon', max_wait=self._get_max_wait_for_priority(priority, 2.0)):
                self._record_request('polygon', success=False, rate_limited=True)
                return None
            market_provider_requests.labels('polygon', 'attempt').inc()
            max_retries = 2
            base_delay = 1.5
            for attempt in range(max_retries):
                try:
                    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol.upper()}/prev"
                    params = {"adjusted": "true", "apiKey": polygon_key}
                    response = requests.get(url, params=params, timeout=5)
                    if response.status_code in (400, 404):
                        self._record_request('polygon', success=True)
                        logger.info(f"Polygon reports {symbol} as unavailable ({response.status_code}); treating as inactive with price 0.")
                        market_provider_requests.labels('polygon', 'success').inc()
                        return cache_price(0.0, inactive=True)
                    if response.status_code == 429:
                        self._record_request('polygon', success=False, rate_limited=True, cooldown=90.0)
                        market_provider_requests.labels('polygon', 'rate_limited').inc()
                        if attempt < max_retries - 1:
                            time.sleep(base_delay * (attempt + 1))
                            continue
                        return None
                    response.raise_for_status()
                    data = response.json() or {}
                    results = data.get('results') or []
                    if results:
                        close_val = results[0].get('c') or results[0].get('close')
                        if close_val is not None:
                            price_val = float(close_val)
                            cache_price(price_val)
                            self._record_request('polygon', success=True)
                            market_provider_requests.labels('polygon', 'success').inc()
                            return price_val
                    market_provider_requests.labels('polygon', 'empty').inc()
                    break
                except requests.RequestException as exc:
                    if attempt < max_retries - 1:
                        delay = base_delay * (attempt + 1)
                        logger.debug(f"Polygon fetch error for {symbol}, retrying in {delay:.1f}s: {exc}")
                        time.sleep(delay)
                        continue
                    logger.warning(f"Polygon fetch failed for {symbol}: {exc}")
                    self._record_request('polygon', success=False)
                    market_provider_requests.labels('polygon', 'error').inc()
            return None

        def fetch_from_alpha() -> Optional[float]:
            api_key = Config.ALPHA_VANTAGE_API_KEY
            if not api_key:
                return None
            if not self._respect_rate_limit('alpha_vantage', max_wait=self._get_max_wait_for_priority(priority, 2.0)):
                self._record_request('alpha_vantage', success=False, rate_limited=True)
                return None
            market_provider_requests.labels('alpha_vantage', 'attempt').inc()
            try:
                url = "https://www.alphavantage.co/query"
                params = {
                    "function": "GLOBAL_QUOTE",
                    "symbol": symbol.upper(),
                    "apikey": api_key,
                }
                response = requests.get(url, params=params, timeout=4)
                if response.status_code == 429:
                    self._record_request('alpha_vantage', success=False, rate_limited=True, cooldown=180.0)
                    market_provider_requests.labels('alpha_vantage', 'rate_limited').inc()
                    return None
                response.raise_for_status()
                data = response.json() or {}
                if isinstance(data, dict) and data.get("Note"):
                    self._record_request('alpha_vantage', success=False, rate_limited=True, cooldown=180.0)
                    market_provider_requests.labels('alpha_vantage', 'rate_limited').inc()
                    return None
                quote = data.get("Global Quote", {})
                price_str = quote.get("05. price") or quote.get("05. Price")
                if price_str:
                    price_val = float(price_str)
                    cache_price(price_val)
                    self._record_request('alpha_vantage', success=True)
                    market_provider_requests.labels('alpha_vantage', 'success').inc()
                    return price_val
            except Exception as exc:
                logger.debug(f"Alpha Vantage fetch failed for {symbol}: {exc}")
                self._record_request('alpha_vantage', success=False)
                market_provider_requests.labels('alpha_vantage', 'error').inc()
            return None

        provider_map = {
            'yfinance': fetch_from_yfinance,
            'polygon': fetch_from_polygon,
            'alpha_vantage': fetch_from_alpha,
        }

        for provider in self._stock_provider_order:
            fetcher = provider_map.get(provider)
            if not fetcher:
                continue
            price = fetcher()
            if price is not None:
                return price

        # Final fallback: return stale cached value if available (even if TTL expired)
        if cached_entry and 'price' in cached_entry:
            logger.warning(
                "All stock providers failed for %s – returning stale cached price (age=%.1fs).",
                symbol.upper(),
                time.time() - cached_entry.get('timestamp', 0.0),
            )
            return cached_entry.get('price')

        # Mock fallback
        mock_prices = {
            'AAPL': 175.43,
            'TSLA': 248.90,
            'MSFT': 378.85,
            'GOOGL': 142.50,
        }
        if symbol.upper() in mock_prices:
            return cache_price(mock_prices[symbol.upper()])

        logger.warning(f"Stock price for {symbol} not available")
        return None
    
    def get_price(self, symbol: str, asset_type: str = 'auto', priority: str = 'normal') -> Optional[Dict]:
        """Get price for any asset (auto-detect type)"""
        try:
            # Request collapsing: avoid duplicate upstream calls within a short window
            key = f"{asset_type}:{symbol.upper()}"
            now = time.time()
            inprog_at = self._inflight.get(key)
            if inprog_at and now - inprog_at < 2.0:
                # Wait briefly for cache to populate
                for _ in range(5):
                    time.sleep(0.1)
                    # Check in-memory cache
                    cache_key = ("CRYPTO_" if asset_type == 'crypto' else "STOCK_") + symbol
                    if cache_key in self._price_cache and now - self._price_cache[cache_key]['timestamp'] < self._cache_ttl:
                        market_cache_hits.inc()
                        break
                # Continue; normal flow will hit cache if available
            else:
                self._inflight[key] = now
            # Auto-detect if not specified
            if asset_type == 'auto':
                # Common crypto symbols
                crypto_symbols = ['BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'DOT', 'MATIC', 'AVAX']
                asset_type = 'crypto' if symbol.upper() in crypto_symbols else 'stock'
            
            price = None
            if asset_type == 'crypto':
                price = self.get_crypto_price(symbol, priority=priority)
            else:
                price = self.get_stock_price(symbol, priority=priority)
            
            if price is None:
                return None
            
            # Get 24h change (for crypto, from Binance)
            change_24h = None
            change_percent_24h = None
            
            if asset_type == 'crypto':
                try:
                    url = f"https://api.binance.com/api/v3/ticker/24hr"
                    params = {"symbol": f"{symbol}USDT"}
                    response = requests.get(url, params=params, timeout=5)
                    response.raise_for_status()
                    data = response.json()
                    change_24h = float(data.get('priceChange', 0))
                    change_percent_24h = float(data.get('priceChangePercent', 0))
                except:
                    pass
            
            return {
                'symbol': symbol.upper(),
                'price': price,
                'change_24h': change_24h,
                'change_percent_24h': change_percent_24h,
                'type': asset_type,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return None
        finally:
            try:
                if 'key' in locals() and self._inflight.get(key):
                    # Clear in-flight marker
                    self._inflight.pop(key, None)
            except Exception:
                pass
    
    def get_watchlist_prices(self, symbols: List[str], priority: str = 'high') -> List[Dict]:
        """Get prices for multiple symbols with extended metrics when available"""
        results = []
        for symbol in symbols:
            # Use get_market_data to get extended metrics
            data = self.get_market_data(symbol, priority=priority)
            if data:
                results.append(data)
        return results
    
    def get_market_data(self, symbol: str, asset_type: str = 'auto', priority: str = 'normal') -> Optional[Dict]:
        """Get comprehensive market data for an asset including extended metrics"""
        price_data = self.get_price(symbol, asset_type, priority=priority)
        if not price_data:
            return None
        
        # Start with basic price data
        market_data = price_data.copy()
        
        # Add extended metrics based on asset type
        if asset_type == 'crypto' or price_data.get('type') == 'crypto':
            # For crypto, get extended data from Binance
            try:
                url = f"https://api.binance.com/api/v3/ticker/24hr"
                params = {"symbol": f"{symbol}USDT"}
                response = requests.get(url, params=params, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    market_data['volume_24h'] = float(data.get('volume', 0)) * float(data.get('lastPrice', 0))
                    market_data['high_24h'] = float(data.get('highPrice', 0))
                    market_data['low_24h'] = float(data.get('lowPrice', 0))
                    # Try to get market cap from CoinGecko if available
                    try:
                        import requests as req
                        cg_url = f"https://api.coingecko.com/api/v3/simple/price"
                        cg_params = {"ids": symbol.lower(), "vs_currencies": "usd", "include_market_cap": "true"}
                        cg_resp = req.get(cg_url, params=cg_params, timeout=5)
                        if cg_resp.status_code == 200:
                            cg_data = cg_resp.json()
                            if symbol.lower() in cg_data:
                                market_data['market_cap'] = cg_data[symbol.lower()].get('usd_market_cap')
                    except Exception:
                        pass
            except Exception:
                pass
        else:
            # For stocks, try to get extended data from Polygon or yfinance
            try:
                Config.init()
                polygon_key = Config.POLYGON_API_KEY
                if polygon_key and self._respect_rate_limit('polygon', max_wait=self._get_max_wait_for_priority(priority, 2.5)):
                    import datetime as dt
                    today = dt.date.today()
                    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{today}/{today}"
                    params = {"adjusted": "true", "apiKey": polygon_key}
                    response = requests.get(url, params=params, timeout=8)
                    if response.status_code == 200:
                        data = response.json()
                        results = (data or {}).get("results") or []
                        if results:
                            latest = results[-1]
                            market_data['volume_24h'] = float(latest.get('v', 0))
                            market_data['high_24h'] = float(latest.get('h', 0))
                            market_data['low_24h'] = float(latest.get('l', 0))
            except Exception:
                pass
            
            # Try yfinance for market cap and other metrics
            if YFINANCE_AVAILABLE:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    if info:
                        market_data['market_cap'] = info.get('marketCap')
                        market_data['volume_24h'] = info.get('volume') or market_data.get('volume_24h')
                        market_data['high_24h'] = info.get('dayHigh') or market_data.get('high_24h')
                        market_data['low_24h'] = info.get('dayLow') or market_data.get('low_24h')
                        # Add name from yfinance if available
                        if info.get('longName'):
                            market_data['name'] = info.get('longName')
                        elif info.get('shortName'):
                            market_data['name'] = info.get('shortName')
                except Exception:
                    pass
        
        return market_data
    
    def validate_symbol(self, symbol: str) -> Dict[str, Any]:
        """Validate if a symbol exists and is tradeable.
        Returns dict with 'valid': bool, 'exists': bool, 'symbol': str, 'type': str, 'name': str (optional)
        """
        try:
            symbol = symbol.upper().strip()
            if not symbol or len(symbol) > 15:
                return {'valid': False, 'exists': False, 'symbol': symbol, 'error': 'Invalid symbol format'}
            
            # Try to get price - if successful, symbol exists
            price_data = self.get_price(symbol)
            if price_data:
                return {
                    'valid': True,
                    'exists': True,
                    'symbol': symbol,
                    'type': price_data.get('type', 'unknown'),
                    'name': symbol  # Default name
                }
            
            # Try search to see if symbol exists in any exchange
            # Search with higher limit to find exact match even if not first result
            search_results = self.search_symbols(symbol, limit=20)
            if search_results:
                # Look for exact match (case-insensitive)
                exact_match = None
                for result in search_results:
                    if result.get('symbol', '').upper() == symbol:
                        exact_match = result
                        break
                
                if exact_match:
                    return {
                        'valid': True,
                        'exists': True,
                        'symbol': symbol,
                        'type': exact_match.get('type', 'unknown'),
                        'name': exact_match.get('name', symbol),
                        'exchange': exact_match.get('exchange')
                    }
            
            return {'valid': False, 'exists': False, 'symbol': symbol, 'error': 'Symbol not found'}
        except Exception as e:
            logger.error(f"Error validating symbol {symbol}: {e}")
            return {'valid': False, 'exists': False, 'symbol': symbol, 'error': str(e)}
    
    def get_symbol_preview(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get preview data for a symbol before adding to watchlist.
        Returns price, 24h change, volume, market cap, mini chart data, and Due Diligence score if available.
        """
        try:
            symbol = symbol.upper().strip()
            if not symbol:
                return None
            
            # Get current price and basic data
            price_data = self.get_price(symbol, priority='high')
            if not price_data:
                return None
            
            preview: Dict[str, Any] = {
                'symbol': symbol,
                'price': price_data.get('price'),
                'change_24h': price_data.get('change_24h'),
                'change_percent_24h': price_data.get('change_percent_24h'),
                'type': price_data.get('type', 'unknown'),
                'timestamp': price_data.get('timestamp')
            }
            
            # Get 7-day history for mini chart
            history = self.get_symbol_history(symbol, days=7)
            if history:
                preview['chart_data'] = [{'date': h.get('date'), 'close': h.get('close')} for h in history]
            
            # Get extended metrics using get_market_data (works for both crypto and stocks)
            extended_data = self.get_market_data(symbol, price_data.get('type', 'auto'))
            if extended_data:
                preview['volume_24h'] = extended_data.get('volume_24h')
                preview['market_cap'] = extended_data.get('market_cap')
                preview['high_24h'] = extended_data.get('high_24h')
                preview['low_24h'] = extended_data.get('low_24h')
                # Add name if available
                if extended_data.get('name'):
                    preview['name'] = extended_data.get('name')
            else:
                # Fallback: set to None if get_market_data fails
                preview['volume_24h'] = None
                preview['market_cap'] = None
                preview['high_24h'] = None
                preview['low_24h'] = None
            
            return preview
        except Exception as e:
            logger.error(f"Error getting preview for {symbol}: {e}")
            return None

    def get_symbol_history(self, symbol: str, days: int = 7, priority: str = 'normal') -> Optional[List[Dict]]:
        """Get daily close history for last N days.
        - Crypto: Binance klines (1d)
        - Stocks: Polygon aggregates, fallback Alpha Vantage daily
        - Last resort: synthesize from current price
        """
        try:
            symbol = symbol.upper()
            
            # Check history cache first
            history_cache_key = f"HISTORY_{symbol}_{days}"
            if self._redis:
                try:
                    import json
                    val = self._redis.get(history_cache_key)
                    if val:
                        market_cache_hits.inc()
                        return json.loads(val)
                except Exception:
                    pass
            if history_cache_key in self._price_cache:
                cached = self._price_cache[history_cache_key]
                if isinstance(cached, dict) and 'timestamp' in cached:
                    if time.time() - cached['timestamp'] < self._get_ttl('history'):
                        market_cache_hits.inc()
                        return cached['data']
            
            series = None
            # If crypto (simple detection by known list), use Binance with CoinGecko/Yahoo fallbacks
            crypto_symbols = ['BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'DOT', 'MATIC', 'AVAX']
            if symbol in crypto_symbols:
                try:
                    if not self._respect_rate_limit('binance', max_wait=self._get_max_wait_for_priority(priority, 2.0)):
                        self._record_request('binance', success=False, rate_limited=True)
                        raise RuntimeError("Binance cooldown active")
                    url = "https://api.binance.com/api/v3/klines"
                    params = {"symbol": f"{symbol}USDT", "interval": "1d", "limit": max(7, days)}
                    resp = self._http_get_with_retry(
                        url,
                        params=params,
                        timeout=8,
                        max_retries=3,
                        base_delay=1.0,
                        provider='binance',
                    )
                    resp.raise_for_status()
                    klines = resp.json() or []
                    series = []
                    for k in klines[-days:]:
                        # kline format: [ openTime, open, high, low, close, volume, closeTime, ... ]
                        close_price = float(k[4])
                        close_time_ms = int(k[6])
                        d = datetime.fromtimestamp(close_time_ms/1000).date().isoformat()
                        series.append({"date": d, "close": close_price})
                    self._record_request('binance', success=True)
                except Exception:
                    self._record_request('binance', success=False)
                    # Try CoinGecko daily prices as a secondary crypto history source
                    try:
                        if self._respect_rate_limit('coingecko', max_wait=self._get_max_wait_for_priority(priority, 2.0)):
                            cg_id = symbol.lower()
                            url = "https://api.coingecko.com/api/v3/coins/" + cg_id + "/market_chart"
                            params = {
                                "vs_currency": "usd",
                                "days": str(max(days, 7)),
                                "interval": "daily",
                            }
                            resp = self._http_get_with_retry(
                                url,
                                params=params,
                                timeout=8,
                                max_retries=3,
                                base_delay=1.0,
                                provider='coingecko',
                            )
                            resp.raise_for_status()
                            data = resp.json() or {}
                            prices = data.get('prices') or []
                            if prices:
                                series = []
                                # prices: [[timestamp_ms, price], ...]
                                for ts_ms, price_val in prices[-days:]:
                                    d = datetime.fromtimestamp(ts_ms / 1000).date().isoformat()
                                    try:
                                        series.append({"date": d, "close": float(price_val)})
                                    except Exception:
                                        continue
                            if series:
                                self._record_request('coingecko', success=True)
                        else:
                            self._record_request('coingecko', success=False, rate_limited=True)
                    except Exception:
                        self._record_request('coingecko', success=False)
                        pass
            # Try Polygon aggregates range 1 day for past N days
            if series is None:
                try:
                    Config.init()
                    polygon_key = Config.POLYGON_API_KEY
                    if polygon_key:
                        if self._respect_rate_limit('polygon', max_wait=self._get_max_wait_for_priority(priority, 2.5)):
                            import datetime as dt
                            end = dt.date.today()
                            start = end - dt.timedelta(days=days + 3)
                            url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{start}/{end}"
                            params = {"adjusted": "true", "sort": "asc", "limit": 250, "apiKey": polygon_key}
                            resp = self._http_get_with_retry(
                                url,
                                params=params,
                                timeout=8,
                                max_retries=3,
                                base_delay=1.5,
                                provider='polygon',
                            )
                            if resp.status_code == 429:
                                self._record_request('polygon', success=False, rate_limited=True, cooldown=120.0)
                                raise RuntimeError("Polygon rate limit 429")
                            resp.raise_for_status()
                            data = resp.json()
                            results = (data or {}).get("results") or []
                            series = [
                                {"date": datetime.fromtimestamp(r.get("t", 0)/1000).date().isoformat(), "close": float(r.get("c"))}
                                for r in results if r.get("c") is not None
                            ]
                            if series:
                                series = series[-days:]
                            self._record_request('polygon', success=True)
                        else:
                            self._record_request('polygon', success=False, rate_limited=True)
                except Exception:
                    self._record_request('polygon', success=False)
                    pass

            # Try Alpha Vantage TIME_SERIES_DAILY
            if series is None:
                try:
                    api_key = Config.ALPHA_VANTAGE_API_KEY
                    if api_key:
                        if not self._respect_rate_limit('alpha_vantage', max_wait=self._get_max_wait_for_priority(priority, 3.0)):
                            self._record_request('alpha_vantage', success=False, rate_limited=True)
                            raise RuntimeError("Alpha Vantage cooldown active")
                        url = "https://www.alphavantage.co/query"
                        params = {"function": "TIME_SERIES_DAILY", "symbol": symbol, "apikey": api_key}
                        resp = requests.get(url, params=params, timeout=8)
                        if resp.status_code == 429:
                            self._record_request('alpha_vantage', success=False, rate_limited=True, cooldown=180.0)
                            raise RuntimeError("Alpha Vantage rate limit 429")
                        resp.raise_for_status()
                        js = resp.json()
                        ts = js.get("Time Series (Daily)", {})
                        if ts:
                            # Sorted asc by date
                            items = sorted(ts.items())
                            series = [{"date": d, "close": float(v.get("4. close"))} for d, v in items][-days:]
                        self._record_request('alpha_vantage', success=True)
                except Exception:
                    self._record_request('alpha_vantage', success=False)
                    pass

            # Fallback: synthesize from current price
            if series is None:
                base = self.get_price(symbol, priority='normal')
                if not base:
                    return None
                price = base.get('price', 0.0) or 0.0
                out: List[Dict] = []
                for i in range(days, 0, -1):
                    d = datetime.now().date()
                    day = d - __import__('datetime').timedelta(days=i)
                    factor = 1 + (0.01 * ((i % 3) - 1))  # small drift
                    out.append({"date": day.isoformat(), "close": round(price * factor, 2)})
                series = out
            
            # Cache the result
            if series:
                self._price_cache[history_cache_key] = {
                    'data': series,
                    'timestamp': time.time()
                }
                if self._redis:
                    try:
                        import json
                        self._redis.setex(history_cache_key, int(self._get_ttl('history')), json.dumps(series))
                    except Exception:
                        pass
            
            return series if series else None
        except Exception as e:
            logger.error(f"Error fetching history for {symbol}: {e}")
            return None

    def get_symbol_history_with_interval(
        self,
        symbol: str,
        prediction_horizon: int,
        preferred_interval: Optional[str] = None,
        lookback_years: Optional[int] = None,
        priority: str = 'normal'
    ) -> Tuple[List[Dict], str]:
        """
        Fetch historical data with adaptive interval based on prediction horizon:
        - <14 days: hourly (1h) data for last 30-60 days
        - 14-60 days: daily (1d) data for last 120-180 days
        - 90+ days: weekly or daily→weekly aggregation for 365+ days
        
        Providers (in order): Binance (crypto), Polygon.io (stocks), Yahoo Finance (fallback), Alpha Vantage (daily only)
        
        Returns:
            (historical_data, interval_used)
        """
        try:
            symbol = symbol.upper()

            # Determine interval and data requirements based on horizon / preferences
            interval = preferred_interval
            limit_points = 500
            if interval:
                interval = interval.lower()
                if interval not in {'1h', '1d', '1w'}:
                    interval = '1w' if prediction_horizon > 60 else '1d'
            if not interval:
                if prediction_horizon <= 14:
                    interval = '1h'
                elif prediction_horizon <= 60:
                    interval = '1d'
                else:
                    interval = '1w'

            if interval == '1h':
                history_days = min(60, max(30, prediction_horizon * 3))
                limit_points = 1000
            elif interval == '1d':
                if lookback_years:
                    history_days = max(lookback_years * 365, prediction_horizon * 2)
                else:
                    history_days = min(365 * 2, max(120, prediction_horizon * 2))
                limit_points = 2000
            else:  # 1w
                years = lookback_years if lookback_years else max(3, min(10, max(1, prediction_horizon // 52 + 1)))
                history_days = years * 365
                limit_points = 1000
                prediction_horizon = max(prediction_horizon, 60)

            # Check cache with interval-specific key
            history_cache_key = f"HISTORY_INT_{symbol}_{interval}_{history_days}"
            if self._redis:
                try:
                    import json
                    val = self._redis.get(history_cache_key)
                    if val:
                        market_cache_hits.inc()
                        return (json.loads(val), interval)
                except Exception:
                    pass
            if history_cache_key in self._price_cache:
                cached = self._price_cache[history_cache_key]
                if isinstance(cached, dict) and 'timestamp' in cached:
                    if time.time() - cached['timestamp'] < self._history_cache_ttl:
                        market_cache_hits.inc()
                        return (cached['data'], interval)
            
            series = None
            
            # Fetch crypto data from Binance with specific interval
            crypto_symbols = ['BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'DOT', 'MATIC', 'AVAX']
            if symbol in crypto_symbols:
                try:
                    url = "https://api.binance.com/api/v3/klines"
                    # Calculate actual limit based on history needed
                    if interval == '1h':
                        actual_limit = min(limit_points, history_days * 24)
                    elif interval == '1w':
                        actual_limit = min(limit_points, history_days // 7)
                    else:  # 1d
                        actual_limit = min(limit_points, history_days)
                    
                    params = {
                        "symbol": f"{symbol}USDT", 
                        "interval": interval, 
                        "limit": actual_limit
                    }
                    resp = requests.get(url, params=params, timeout=10)
                    resp.raise_for_status()
                    klines = resp.json() or []
                    series = []
                    for k in klines:
                        close_price = float(k[4])
                        volume = float(k[5])
                        high_price = float(k[2])
                        low_price = float(k[3])
                        close_time_ms = int(k[6])
                        d = datetime.fromtimestamp(close_time_ms/1000).date().isoformat()
                        series.append({
                            "date": d, 
                            "close": close_price,
                            "open": float(k[1]),
                            "high": high_price,
                            "low": low_price,
                            "volume": volume
                        })
                except Exception as e:
                    logger.warning(f"Binance klines fetch failed for {symbol}: {e}")
            
            # Fetch stock data from Polygon with appropriate timespan
            if series is None:
                try:
                    Config.init()
                    polygon_key = Config.POLYGON_API_KEY
                    if polygon_key:
                        if not self._respect_rate_limit('polygon', max_wait=self._get_max_wait_for_priority(priority, 3.0)):
                            self._record_request('polygon', success=False, rate_limited=True)
                            raise RuntimeError("Polygon cooldown active")
                        
                        end = dt.date.today()
                        start = end - dt.timedelta(days=history_days + 10)  # Add buffer
                        
                        # Map interval to Polygon timespan
                        timespan_map = {'1h': '1/hour', '1d': '1/day', '1w': '1/week'}
                        polygon_timespan = timespan_map.get(interval, '1/day')
                        
                        url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/{polygon_timespan}/{start}/{end}"
                        params = {"adjusted": "true", "sort": "asc", "limit": 50000, "apiKey": polygon_key}
                        
                        # Retry logic with exponential backoff for 429 errors
                        max_retries = 3
                        base_delay = 2.0
                        for attempt in range(max_retries):
                            try:
                                resp = requests.get(url, params=params, timeout=12)
                                
                                # Handle 429 rate limit errors
                                if resp.status_code == 429:
                                    if attempt < max_retries - 1:
                                        delay = base_delay * (2 ** attempt)  # 2s, 4s, 8s
                                        logger.warning(f"Polygon aggregates 429 rate limit for {symbol}, retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})")
                                        time.sleep(delay)
                                        continue
                                    else:
                                        self._record_request('polygon', success=False, rate_limited=True, cooldown=120.0)
                                        market_provider_requests.labels('polygon', 'rate_limited').inc()
                                        raise RuntimeError("Polygon rate limit exceeded after retries")
                                
                                resp.raise_for_status()
                                data = resp.json()
                                results = (data or {}).get("results") or []
                                series = []
                                for r in results:
                                    if r.get("c") is not None:
                                        series.append({
                                            "date": datetime.fromtimestamp(r.get("t", 0)/1000).date().isoformat(),
                                            "close": float(r.get("c")),
                                            "open": float(r.get("o", 0)),
                                            "high": float(r.get("h", 0)),
                                            "low": float(r.get("l", 0)),
                                            "volume": float(r.get("v", 0))
                                        })
                                # Update last request time on success
                                self._record_request('polygon', success=True)
                                break  # Successfully processed, exit retry loop
                            except requests.exceptions.RequestException as req_err:
                                # Network errors: retry with exponential backoff
                                if attempt < max_retries - 1:
                                    delay = base_delay * (2 ** attempt) / 2  # 1s, 2s, 4s (shorter for network errors)
                                    logger.warning(f"Polygon aggregates network error for {symbol}, retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries}): {req_err}")
                                    time.sleep(delay)
                                    continue
                                else:
                                    self._record_request('polygon', success=False)
                                    raise
                except RuntimeError:
                    # Circuit breaker or rate limit - don't retry, just log
                    logger.warning(f"Polygon aggregates fetch skipped for {symbol}: provider cooldown")
                except Exception as e:
                    logger.warning(f"Polygon aggregates fetch failed for {symbol}: {e}")
                    self._record_request('polygon', success=False)
                    market_provider_requests.labels('polygon', 'error').inc()
            
            # Try Yahoo Finance as fallback (no rate limits, supports multiple intervals)
            if series is None and YFINANCE_AVAILABLE:
                # Retry logic for Yahoo Finance
                max_retries = 3
                base_delay = 1.0
                cooldown_triggered = False
                for attempt in range(max_retries):
                    try:
                        if not self._respect_rate_limit('yahoo_finance', max_wait=self._get_max_wait_for_priority(priority, 3.0)):
                            self._record_request('yahoo_finance', success=False, rate_limited=True)
                            cooldown_triggered = True
                            break
                        market_provider_requests.labels('yahoo_finance', 'attempt').inc()
                        ticker = yf.Ticker(symbol)
                        
                        # Calculate date range
                        end_date = dt.date.today()
                        start_date = end_date - dt.timedelta(days=history_days + 10)
                        
                        # Determine appropriate period based on history_days and interval
                        # For weekly data, we need longer periods
                        if interval == '1w':
                            if history_days > 365:
                                period = '5y'  # 5 years for long-term weekly
                            elif history_days > 180:
                                period = '2y'  # 2 years
                            else:
                                period = '1y'  # 1 year
                        elif interval == '1d':
                            if history_days > 365:
                                period = '2y'  # 2 years for daily
                            else:
                                period = '1y'  # 1 year
                        else:  # 1h
                            period = '60d'  # 60 days for hourly
                        
                        # Use history() method for historical data
                        # Try period first (more reliable), then fallback to start/end dates
                        hist = None
                        try:
                            if interval == '1h':
                                hist = ticker.history(period=period, interval='1h', timeout=10)
                            elif interval == '1d':
                                hist = ticker.history(period=period, interval='1d', timeout=10)
                            elif interval == '1w':
                                hist = ticker.history(period=period, interval='1wk', timeout=10)
                            else:
                                hist = ticker.history(period='1y', interval='1d', timeout=10)
                        except Exception as e1:
                            logger.debug(f"Yahoo Finance period fetch failed for {symbol}, trying start/end dates: {e1}")
                            # Fallback to start/end dates if period fails
                            try:
                                if interval == '1h':
                                    hist = ticker.history(start=start_date, end=end_date, interval='1h', timeout=10)
                                elif interval == '1d':
                                    hist = ticker.history(start=start_date, end=end_date, interval='1d', timeout=10)
                                elif interval == '1w':
                                    hist = ticker.history(start=start_date, end=end_date, interval='1wk', timeout=10)
                                else:
                                    hist = ticker.history(start=start_date, end=end_date, interval='1d', timeout=10)
                            except Exception as e2:
                                logger.debug(f"Yahoo Finance start/end fetch failed for {symbol}: {e2}")
                                if attempt < max_retries - 1:
                                    delay = base_delay * (2 ** attempt)  # 1s, 2s, 4s
                                    logger.debug(f"Yahoo Finance retry {attempt + 1}/{max_retries} for {symbol} in {delay:.1f}s")
                                    time.sleep(delay)
                                    continue
                                else:
                                    hist = None
                        
                        if hist is not None and not hist.empty:
                            series = []
                            for date, row in hist.iterrows():
                                # Handle both DatetimeIndex and regular index
                                if isinstance(date, pd.Timestamp):
                                    date_str = date.date().isoformat()
                                    timestamp = date.isoformat()
                                else:
                                    date_str = str(date)
                                    timestamp = date_str
                                
                                series.append({
                                    "date": date_str,
                                    "timestamp": timestamp,
                                    "close": float(row['Close']) if 'Close' in row else 0.0,
                                    "open": float(row['Open']) if 'Open' in row else 0.0,
                                    "high": float(row['High']) if 'High' in row else 0.0,
                                    "low": float(row['Low']) if 'Low' in row else 0.0,
                                    "volume": float(row['Volume']) if 'Volume' in row and pd.notna(row['Volume']) else 0.0
                                })
                            
                            # Limit to requested history_days (approximate)
                            if len(series) > history_days:
                                series = series[-history_days:]
                            
                            # Cache the result
                            if history_cache_key:
                                self._price_cache[history_cache_key] = {
                                    'data': series,
                                    'timestamp': time.time()
                                }
                                if self._redis:
                                    try:
                                        import json
                                        self._redis.setex(history_cache_key, self._history_cache_ttl, json.dumps(series))
                                    except Exception:
                                        pass
                            
                            market_provider_requests.labels('yahoo_finance', 'success').inc()
                            self._record_request('yahoo_finance', success=True)
                            logger.info(f"Yahoo Finance: fetched {len(series)} historical data points for {symbol} ({interval}, period={period})")
                            break  # Success, exit retry loop
                        else:
                            if attempt < max_retries - 1:
                                delay = base_delay * (2 ** attempt)
                                logger.debug(f"Yahoo Finance empty result for {symbol}, retry {attempt + 1}/{max_retries} in {delay:.1f}s")
                                time.sleep(delay)
                                continue
                            else:
                                logger.warning(f"Yahoo Finance: no data returned for {symbol} after {max_retries} attempts")
                                market_provider_requests.labels('yahoo_finance', 'empty').inc()
                                self._record_request('yahoo_finance', success=False)
                    except Exception as e:
                        if cooldown_triggered:
                            break
                        if attempt < max_retries - 1:
                            delay = base_delay * (2 ** attempt)
                            logger.warning(f"Yahoo Finance history fetch failed for {symbol} (attempt {attempt + 1}/{max_retries}), retrying in {delay:.1f}s: {e}")
                            time.sleep(delay)
                            continue
                        else:
                            logger.warning(f"Yahoo Finance history fetch failed for {symbol} after {max_retries} attempts: {e}")
                            market_provider_requests.labels('yahoo_finance', 'error').inc()
                            self._record_request('yahoo_finance', success=False)
            
            # Try Alpha Vantage as fallback (daily only)
            if series is None and interval == '1d':
                try:
                    api_key = Config.ALPHA_VANTAGE_API_KEY
                    if api_key:
                        url = "https://www.alphavantage.co/query"
                        params = {"function": "TIME_SERIES_DAILY", "symbol": symbol, "apikey": api_key}
                        resp = requests.get(url, params=params, timeout=8)
                        resp.raise_for_status()
                        js = resp.json()
                        ts = js.get("Time Series (Daily)", {})
                        if ts:
                            items = sorted(ts.items())
                            series = []
                            for d, v in items[-history_days:]:
                                series.append({
                                    "date": d,
                                    "close": float(v.get("4. close")),
                                    "open": float(v.get("1. open")),
                                    "high": float(v.get("2. high")),
                                    "low": float(v.get("3. low")),
                                    "volume": float(v.get("5. volume", 0))
                                })
                except Exception as e:
                    logger.debug(f"Alpha Vantage fallback failed: {e}")
            
            # For long-term, if we only have daily, aggregate to weekly
            if series and interval == '1w' and len(series) > 7:
                try:
                    # Group by week and aggregate
                    df_dict = {}
                    for entry in series:
                        date_obj = dt.datetime.strptime(entry['date'], '%Y-%m-%d').date()
                        # Get ISO week
                        iso_year, iso_week, _ = date_obj.isocalendar()
                        week_key = f"{iso_year}-W{iso_week:02d}"
                        
                        if week_key not in df_dict:
                            df_dict[week_key] = {
                                'date': date_obj,  # Store first date of week
                                'opens': [],
                                'highs': [],
                                'lows': [],
                                'closes': [],
                                'volumes': []
                            }
                        
                        df_dict[week_key]['opens'].append(entry.get('open', 0))
                        df_dict[week_key]['highs'].append(entry.get('high', 0))
                        df_dict[week_key]['lows'].append(entry.get('low', 0))
                        df_dict[week_key]['closes'].append(entry.get('close', 0))
                        df_dict[week_key]['volumes'].append(entry.get('volume', 0))
                    
                    # Create weekly aggregated series
                    aggregated = []
                    for week_key in sorted(df_dict.keys()):
                        week_data = df_dict[week_key]
                        aggregated.append({
                            'date': week_data['date'].isoformat(),
                            'open': week_data['opens'][0] if week_data['opens'] else 0,
                            'high': max(week_data['highs']) if week_data['highs'] else 0,
                            'low': min(week_data['lows']) if week_data['lows'] else 0,
                            'close': week_data['closes'][-1] if week_data['closes'] else 0,
                            'volume': sum(week_data['volumes'])
                        })
                    
                    series = aggregated[-history_days:] if len(aggregated) > history_days else aggregated
                except Exception as e:
                    logger.warning(f"Weekly aggregation failed, using daily data: {e}")
            
            # Fallback to synthesize if no data available
            if not series:
                base = self.get_price(symbol, priority='normal')
                if base:
                    price = base.get('price', 0.0) or 0.0
                    series = []
                    for i in range(history_days, 0, -1):
                        day = dt.date.today() - dt.timedelta(days=i)
                        factor = 1 + (0.01 * ((i % 3) - 1))
                        series.append({
                            "date": day.isoformat(), 
                            "close": round(price * factor, 2),
                            "open": round(price * factor * 0.99, 2),
                            "high": round(price * factor * 1.01, 2),
                            "low": round(price * factor * 0.98, 2),
                            "volume": 0
                        })
            
            # Cache the result
            if series:
                self._price_cache[history_cache_key] = {
                    'data': series,
                    'timestamp': time.time()
                }
                if self._redis:
                    try:
                        import json
                        self._redis.setex(history_cache_key, self._history_cache_ttl, json.dumps(series))
                    except Exception:
                        pass
                
                logger.info(f"Fetched {len(series)} {interval} candles for {symbol}")
                return (series, interval)
            
            return (None, interval)
            
        except Exception as e:
            logger.error(f"Error fetching history with interval for {symbol}: {e}")
            return (None, '1d')

    def search_symbols(self, query: str, limit: int = 10, priority: str = 'normal') -> List[Dict]:
        """Search tradable symbols using Polygon, Finnhub, and Alpha Vantage.
        Returns a list of dicts containing symbol metadata (symbol, name, type, exchange, currency, isin).
        """
        results: List[Dict] = []
        q = (query or '').strip()
        if not q:
            return results

        normalized_limit = max(1, min(limit, 50))
        Config.init()
        polygon_key = Config.POLYGON_API_KEY
        finnhub_key = Config.FINNHUB_API_KEY
        alpha_vantage_key = Config.ALPHA_VANTAGE_API_KEY

        seen: set[str] = set()

        def add_result(symbol: Optional[str], **metadata):
            if not symbol:
                return
            key = symbol.upper()
            if key in seen:
                return
            entry = {'symbol': symbol}
            for field, value in metadata.items():
                if value:
                    entry[field] = value
            results.append(entry)
            seen.add(key)

        uppercase_query = q.upper()
        isin_pattern = r'^[A-Z]{2}[A-Z0-9]{9}[0-9]$'
        is_isin_query = bool(re.match(isin_pattern, uppercase_query))

        # 1. Direct ISIN lookup via Finnhub (if available)
        if is_isin_query and finnhub_key:
            try:
                resp = requests.get(
                    "https://finnhub.io/api/v1/stock/profile2",
                    params={"isin": uppercase_query, "token": finnhub_key},
                    timeout=6,
                )
                if resp.status_code == 200:
                    data = resp.json() or {}
                    ticker = data.get('ticker')
                    if ticker:
                        add_result(
                            ticker,
                            name=data.get('name') or data.get('ticker'),
                            type='stock',
                            exchange=data.get('exchange'),
                            currency=data.get('currency'),
                            isin=data.get('isin') or uppercase_query,
                            source='finnhub'
                        )
                        if len(results) >= normalized_limit:
                            return results[:normalized_limit]
            except Exception as e:
                logger.warning(f"Finnhub ISIN lookup failed: {e}")

        # 2. Polygon search (supports search and ISIN filter)
        if polygon_key:
            try:
                url = "https://api.polygon.io/v3/reference/tickers"
                params = {
                    "active": "true",
                    "limit": str(normalized_limit),
                    "apiKey": polygon_key,
                }
                if is_isin_query:
                    params["isin"] = uppercase_query
                else:
                    params["search"] = q
                if not self._respect_rate_limit('polygon', max_wait=self._get_max_wait_for_priority(priority, 2.5)):
                    self._record_request('polygon', success=False, rate_limited=True)
                    raise RuntimeError("Polygon search cooldown active")
                r = requests.get(url, params=params, timeout=8)
                r.raise_for_status()
                js = r.json() or {}
                for it in js.get('results') or []:
                    add_result(
                        it.get('ticker'),
                        name=it.get('name'),
                        type=it.get('type') or 'stock',
                        exchange=it.get('primary_exchange'),
                        currency=it.get('currency_name'),
                        isin=it.get('isin') or it.get('composite_figi'),
                        source='polygon'
                    )
                    if len(results) >= normalized_limit:
                        break
            except Exception as e:
                logger.warning(f"Polygon search failed: {e}")

            if len(results) >= normalized_limit:
                return results[:normalized_limit]

        # 3. Alpha Vantage fallback search (no ISIN, but adds extra matches)
        if alpha_vantage_key and len(results) < normalized_limit:
            try:
                url = "https://www.alphavantage.co/query"
                params = {"function": "SYMBOL_SEARCH", "keywords": q, "apikey": alpha_vantage_key}
                r = requests.get(url, params=params, timeout=8)
                r.raise_for_status()
                js = r.json() or {}
                for it in js.get('bestMatches') or []:
                    add_result(
                        it.get('1. symbol'),
                        name=it.get('2. name'),
                        type='stock',
                        exchange=it.get('4. region'),
                        currency=it.get('8. currency'),
                        source='alpha_vantage'
                    )
                    if len(results) >= normalized_limit:
                        break
            except Exception as e:
                logger.warning(f"Alpha Vantage search failed: {e}")

        # 4. Finnhub keyword search for additional metadata (including ISIN when available)
        if finnhub_key and len(results) < normalized_limit:
            try:
                search_resp = requests.get(
                    "https://finnhub.io/api/v1/search",
                    params={"q": q, "token": finnhub_key},
                    timeout=6,
                )
                search_resp.raise_for_status()
                search_data = search_resp.json() or {}
                for item in search_data.get('result', []):
                    if len(results) >= normalized_limit:
                        break
                    symbol = item.get('symbol') or item.get('displaySymbol')
                    if not symbol:
                        continue

                    profile_data = {}
                    try:
                        profile_resp = requests.get(
                            "https://finnhub.io/api/v1/stock/profile2",
                            params={"symbol": symbol, "token": finnhub_key},
                            timeout=6,
                        )
                        if profile_resp.status_code == 200:
                            profile_data = profile_resp.json() or {}
                    except Exception:
                        profile_data = {}

                    add_result(
                        symbol,
                        name=profile_data.get('name') or item.get('description'),
                        type=item.get('type'),
                        exchange=profile_data.get('exchange'),
                        currency=profile_data.get('currency'),
                        isin=profile_data.get('isin'),
                        source='finnhub'
                    )
            except Exception as e:
                logger.warning(f"Finnhub search failed: {e}")

        return results[:normalized_limit]

    def get_news(
        self,
        symbols: Optional[List[str]] = None,
        limit: int = 5,
        priority: str = 'normal',
        _allow_global_fallback: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Fetch market news headlines for the given symbols (or general market news when no symbols supplied).
        Aggregates Polygon and Finnhub feeds with caching and graceful fallbacks.
        """
        normalized_limit = max(1, min(limit, 20))
        symbol_list: List[str] = []
        if symbols:
            # Deduplicate while preserving order
            seen = set()
            for raw in symbols:
                if not raw:
                    continue
                ticker = raw.strip().upper()
                if ticker and ticker not in seen:
                    seen.add(ticker)
                    symbol_list.append(ticker)

        cache_key = "global" if not symbol_list else ",".join(symbol_list)
        cached = self._news_cache.get(cache_key)
        now_ts = time.time()
        if cached and (now_ts - cached.get("timestamp", 0.0)) < self._get_ttl('news'):
            return cached.get("items", [])[:normalized_limit]

        items: List[Dict[str, Any]] = []
        dedup_keys: set[str] = set()

        def add_item(article: Dict[str, Any]) -> None:
            if not article:
                return
            key = article.get("id") or article.get("url")
            if not key:
                return
            if key in dedup_keys:
                return
            dedup_keys.add(str(key))
            items.append(article)

        def parse_iso(ts: Optional[str]) -> Optional[str]:
            if not ts:
                return None
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()
            except Exception:
                return None

        # Primary provider: Polygon
        Config.init()
        polygon_key = Config.POLYGON_API_KEY
        if polygon_key:
            market_provider_requests.labels('polygon_news', 'attempt').inc()
            tickers_to_fetch = symbol_list if symbol_list else [None]
            try:
                if not self._respect_rate_limit('polygon_news', max_wait=self._get_max_wait_for_priority(priority, 2.5)):
                    self._record_request('polygon_news', success=False, rate_limited=True)
                else:
                    for ticker in tickers_to_fetch:
                        if len(items) >= normalized_limit:
                            break
                        params = {
                            "limit": str(normalized_limit),
                            "order": "desc",
                            "sort": "published_utc",
                            "apiKey": polygon_key
                        }
                        if ticker:
                            params["ticker"] = ticker
                        response = requests.get(
                            "https://api.polygon.io/v2/reference/news",
                            params=params,
                            timeout=8
                        )
                        if response.status_code == 429:
                            self._record_request('polygon_news', success=False, rate_limited=True, cooldown=180.0)
                            market_provider_requests.labels('polygon_news', 'rate_limited').inc()
                            break
                        response.raise_for_status()
                        data = response.json() or {}
                        results = data.get("results") or []
                        for entry in results:
                            if len(items) >= normalized_limit:
                                break
                            published = parse_iso(entry.get("published_utc"))
                            tickers = entry.get("tickers") or []
                            primary_symbol = None
                            if isinstance(tickers, list) and tickers:
                                primary_symbol = str(tickers[0]).upper()
                            elif ticker:
                                primary_symbol = ticker
                            if not primary_symbol:
                                primary_symbol = "MARKET"
                            article = {
                                "id": entry.get("id") or entry.get("article_url"),
                                "title": entry.get("title") or "",
                                "source": (entry.get("publisher") or {}).get("name") or entry.get("publisher") or "Polygon",
                                "timestamp": published or datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
                                "url": entry.get("article_url"),
                                "summary": entry.get("description"),
                                "sentiment": entry.get("sentiment") if entry.get("sentiment") in ("positive", "negative", "neutral") else "neutral",
                                "symbol": primary_symbol.upper()
                            }
                            add_item(article)
                        self._record_request('polygon_news', success=True)
                        market_provider_requests.labels('polygon_news', 'success').inc()
            except requests.HTTPError as http_err:
                if getattr(http_err.response, "status_code", None) == 429:
                    self._record_request('polygon_news', success=False, rate_limited=True, cooldown=180.0)
                    market_provider_requests.labels('polygon_news', 'rate_limited').inc()
                else:
                    self._record_request('polygon_news', success=False)
                    market_provider_requests.labels('polygon_news', 'error').inc()
                logger.warning(f"Polygon news fetch failed: {http_err}")
            except Exception as exc:
                self._record_request('polygon_news', success=False)
                market_provider_requests.labels('polygon_news', 'error').inc()
                logger.warning(f"Polygon news fetch error: {exc}")

        # Secondary provider: Finnhub
        if len(items) < normalized_limit:
            finnhub_key = Config.FINNHUB_API_KEY
            if finnhub_key:
                market_provider_requests.labels('finnhub_news', 'attempt').inc()
                date_to = dt.date.today()
                date_from = date_to - dt.timedelta(days=7)
                endpoints: List[Tuple[str, Dict[str, Any], Optional[str]]] = []
                if symbol_list:
                    for ticker in symbol_list[:3]:  # avoid excessive calls
                        endpoints.append((
                            "https://finnhub.io/api/v1/company-news",
                            {
                                "symbol": ticker,
                                "from": date_from.isoformat(),
                                "to": date_to.isoformat(),
                                "token": finnhub_key
                            },
                            ticker
                        ))
                else:
                    endpoints.append((
                        "https://finnhub.io/api/v1/news",
                        {
                            "category": "general",
                            "token": finnhub_key
                        },
                        None
                    ))

                for url, params, ticker in endpoints:
                    if len(items) >= normalized_limit:
                        break
                    try:
                        if not self._respect_rate_limit('finnhub_news', max_wait=self._get_max_wait_for_priority(priority, 2.5)):
                            self._record_request('finnhub_news', success=False, rate_limited=True)
                            break
                        response = requests.get(url, params=params, timeout=8)
                        if response.status_code == 429:
                            self._record_request('finnhub_news', success=False, rate_limited=True, cooldown=120.0)
                            market_provider_requests.labels('finnhub_news', 'rate_limited').inc()
                            break
                        response.raise_for_status()
                        data = response.json() or []
                        for entry in data:
                            if len(items) >= normalized_limit:
                                break
                            ts = entry.get("datetime") or entry.get("time")
                            if isinstance(ts, (int, float)):
                                published = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
                            else:
                                published = parse_iso(entry.get("datetime")) or datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
                            related = entry.get("related") or entry.get("ticker")
                            primary_symbol = ticker or (related.split(',')[0] if isinstance(related, str) and related else None)
                            if not primary_symbol:
                                primary_symbol = entry.get("symbol")
                            if not primary_symbol:
                                primary_symbol = "MARKET"
                            article = {
                                "id": f"finnhub-{entry.get('id') or entry.get('url') or published}",
                                "title": entry.get("headline") or entry.get("title") or "",
                                "source": entry.get("source") or "Finnhub",
                                "timestamp": published,
                                "url": entry.get("url"),
                                "summary": entry.get("summary") or entry.get("description"),
                                "sentiment": "neutral",
                                "symbol": primary_symbol
                            }
                            add_item(article)
                        self._record_request('finnhub_news', success=True)
                        market_provider_requests.labels('finnhub_news', 'success').inc()
                    except requests.HTTPError as http_err:
                        if getattr(http_err.response, "status_code", None) == 429:
                            self._record_request('finnhub_news', success=False, rate_limited=True, cooldown=120.0)
                            market_provider_requests.labels('finnhub_news', 'rate_limited').inc()
                        else:
                            self._record_request('finnhub_news', success=False)
                            market_provider_requests.labels('finnhub_news', 'error').inc()
                        logger.warning(f"Finnhub news fetch failed: {http_err}")
                    except Exception as exc:
                        self._record_request('finnhub_news', success=False)
                        market_provider_requests.labels('finnhub_news', 'error').inc()
                        logger.warning(f"Finnhub news fetch error: {exc}")

        def parse_timestamp(ts_value: Any) -> Optional[datetime]:
            if isinstance(ts_value, datetime):
                return ts_value
            if isinstance(ts_value, (int, float)):
                try:
                    return datetime.fromtimestamp(ts_value, tz=timezone.utc)
                except Exception:
                    return None
            if isinstance(ts_value, str):
                try:
                    return datetime.fromisoformat(ts_value.replace("Z", "+00:00"))
                except Exception:
                    return None
            return None

        now_utc = datetime.now(timezone.utc)

        def filter_articles(articles: List[Dict[str, Any]], max_age: Optional[timedelta]) -> List[Dict[str, Any]]:
            if not articles:
                return []
            cutoff = now_utc - max_age if max_age else None
            filtered_list: List[Dict[str, Any]] = []
            for article in articles:
                source_raw = (article.get("source") or "").strip()
                source_norm = source_raw.lower()
                if source_norm and source_norm in self._blocked_sources:
                    continue

                ts_value = parse_timestamp(article.get("timestamp"))
                if ts_value is None:
                    ts_value = parse_timestamp(article.get("published") or article.get("published_utc"))
                if ts_value is None:
                    ts_value = now_utc

                ts_utc = ts_value.astimezone(timezone.utc)
                if cutoff and ts_utc < cutoff:
                    continue

                article_copy = dict(article)
                article_copy["_ts_dt"] = ts_utc
                article_copy["timestamp"] = ts_utc.isoformat()
                article_copy["_source_weight"] = self._preferred_sources.get(source_norm, 0)
                filtered_list.append(article_copy)
            return filtered_list

        filtered = filter_articles(items, self._max_news_age)
        if not filtered and items:
            fallback_age = getattr(self, "_max_news_age_fallback", self._max_news_age)
            filtered = filter_articles(items, fallback_age)

        if not filtered and symbol_list and _allow_global_fallback:
            global_items = self.get_news(
                symbols=None,
                limit=limit,
                priority=priority,
                _allow_global_fallback=False,
            )
            # Cache global result normally inside recursive call; return here
            self._news_cache[cache_key] = {"items": global_items, "timestamp": now_ts}
            return global_items[:normalized_limit]
        if filtered:
            filtered.sort(
                key=lambda x: (
                    -(x.get("_source_weight") or 0),
                    -((x.get("_ts_dt") or now_utc).timestamp())
                )
            )
            filtered = filtered[:normalized_limit]

            for article in filtered:
                article.pop("_source_weight", None)
                article.pop("_ts_dt", None)

            self._news_cache[cache_key] = {"items": filtered, "timestamp": now_ts}
            return filtered

        self._news_cache[cache_key] = {"items": [], "timestamp": now_ts}
        return []

    def get_quality_report(self) -> Dict[str, Any]:
        """
        Generate a data quality report for market data:
        - Staleness of price and history caches
        - Provider health / cooldown status
        - Detected anomalies in recent price history (large jumps)
        """
        now_ts = time.time()
        price_ttl = self._get_ttl('price')
        history_ttl = self._get_ttl('history')

        price_entries = 0
        stale_price_entries = 0
        inactive_symbols = 0

        for key, entry in self._price_cache.items():
            if not isinstance(entry, dict):
                continue
            ts = entry.get('timestamp')
            if ts is None:
                continue
            price_entries += 1
            age = now_ts - ts
            if age > price_ttl * 3:  # consider stale when 3× TTL
                stale_price_entries += 1
            if entry.get('inactive'):
                inactive_symbols += 1

        history_entries = 0
        stale_history_entries = 0
        for key, entry in self._price_cache.items():
            if not key.startswith("HISTORY_"):
                continue
            if not isinstance(entry, dict):
                continue
            ts = entry.get('timestamp')
            if ts is None:
                continue
            history_entries += 1
            age = now_ts - ts
            if age > history_ttl * 2:
                stale_history_entries += 1

        provider_health: Dict[str, Dict[str, Any]] = {}
        with self._provider_lock:
            for name, state in self._provider_state.items():
                last_req = state.get('last_request', 0.0)
                cooldown_until = state.get('cooldown_until', 0.0)
                provider_health[name] = {
                    'last_request_age_sec': max(0.0, now_ts - last_req) if last_req else None,
                    'in_cooldown': cooldown_until > now_ts,
                    'cooldown_remaining_sec': max(0.0, cooldown_until - now_ts) if cooldown_until > now_ts else 0.0,
                    'failures': state.get('failures', 0.0),
                    'min_interval_sec': state.get('min_interval', 0.0),
                }

        # Simple anomaly detection: look at latest cached history series and flag very large jumps
        anomalies: List[Dict[str, Any]] = []
        try:
            # Limit to a small subset to avoid heavy computations
            for key, entry in list(self._price_cache.items())[:50]:
                if not key.startswith("HISTORY_"):
                    continue
                series = entry.get('data') or []
                if not isinstance(series, list) or len(series) < 3:
                    continue
                last = series[-1]
                prev = series[-2]
                try:
                    last_close = float(last.get('close', 0.0))
                    prev_close = float(prev.get('close', 0.0))
                    if prev_close <= 0:
                        continue
                    change_pct = (last_close - prev_close) / prev_close * 100.0
                    if abs(change_pct) > 30.0:
                        anomalies.append({
                            'series_key': key,
                            'previous_close': prev_close,
                            'last_close': last_close,
                            'change_pct': round(change_pct, 2),
                        })
                except Exception:
                    continue
        except Exception:
            # Diagnostics only; never break the API
            pass

        return {
            'timestamp': datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
            'ttl_seconds': self._ttl_config,
            'price_cache': {
                'entries': price_entries,
                'stale_entries': stale_price_entries,
                'inactive_symbols': inactive_symbols,
            },
            'history_cache': {
                'entries': history_entries,
                'stale_entries': stale_history_entries,
            },
            'provider_health': provider_health,
            'anomalies': anomalies,
        }
