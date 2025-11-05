"""
Market Data Service - Fetches real-time market prices
"""
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from logging_config import get_logger
from config import Config
import time
import os
import datetime as dt
from prometheus_client import Counter
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

logger = get_logger(__name__)

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
        # Cache for prices (TTL: 5 minutes for prices, 1 hour for history)
        self._price_cache: Dict[str, Dict] = {}
        self._cache_ttl = 300  # 5 minutes for current prices
        self._history_cache_ttl = 7200  # 2 hours for historical data (increased for weekly/monthly candles)
        # Alpha Vantage rate limiting (5 req/min => min 12s interval)
        self._av_last_request_time: float = 0.0
        self._av_min_interval: float = 12.0
        # Polygon rate limiting (min 1s interval to avoid 429 errors)
        self._pg_last_request_time: float = 0.0
        self._pg_min_interval: float = 1.0  # At least 1 second between requests
        # Circuit breakers
        self._av_failures = 0
        self._av_open_until = 0.0
        self._pg_failures = 0
        self._pg_open_until = 0.0
        # Request collapsing (simple in-flight guard)
        self._inflight: Dict[str, float] = {}
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
        
    def get_crypto_price(self, symbol: str) -> Optional[float]:
        """Get current crypto price from Binance API"""
        try:
            # Check cache first
            cache_key = f"CRYPTO_{symbol}"
            # Redis cache
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
                if time.time() - cached['timestamp'] < self._cache_ttl:
                    market_cache_hits.inc()
                    return cached['price']
            
            # Fetch from Binance
            url = f"https://api.binance.com/api/v3/ticker/price"
            params = {"symbol": f"{symbol}USDT"}
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            price = float(data.get('price', 0))
            
            # Cache the result
            self._price_cache[cache_key] = {
                'price': price,
                'timestamp': time.time()
            }
            if self._redis:
                try:
                    self._redis.setex(cache_key, self._cache_ttl, str(price))
                except Exception:
                    pass
            
            return price
        except Exception as e:
            logger.error(f"Error fetching crypto price for {symbol}: {e}")
            return None
    
    def get_stock_price(self, symbol: str) -> Optional[float]:
        """Get current stock price using Alpha Vantage; fallback to Polygon.io; then mock"""
        try:
            # Check cache first
            cache_key = f"STOCK_{symbol}"
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
                if time.time() - cached['timestamp'] < self._cache_ttl:
                    market_cache_hits.inc()
                    return cached['price']

            # Try Alpha Vantage if configured
            Config.init()
            api_key = Config.ALPHA_VANTAGE_API_KEY
            if api_key:
                try:
                    # Circuit breaker check
                    now_ts = time.time()
                    if now_ts < self._av_open_until:
                        raise RuntimeError("AV circuit open")
                    # Respect Alpha Vantage rate limit
                    now = time.time()
                    elapsed = now - self._av_last_request_time
                    if elapsed < self._av_min_interval:
                        # Too soon: if we have any stale cache, return it; else skip AV call
                        if cache_key in self._price_cache:
                            return self._price_cache[cache_key]['price']
                        # No cache: do not call to avoid 429; fall through to mock
                        raise RuntimeError("AV rate limit cooldown")

                    market_provider_requests.labels('alpha_vantage', 'attempt').inc()
                    url = "https://www.alphavantage.co/query"
                    params = {
                        "function": "GLOBAL_QUOTE",
                        "symbol": symbol.upper(),
                        "apikey": api_key
                    }
                    response = requests.get(url, params=params, timeout=8)
                    response.raise_for_status()
                    data = response.json()
                    # Handle AV rate limit note
                    if isinstance(data, dict) and data.get("Note"):
                        # Set cooldown and fall back
                        self._av_last_request_time = time.time()
                        self._av_failures += 1
                        if self._av_failures >= 3:
                            self._av_open_until = time.time() + 60
                        market_provider_requests.labels('alpha_vantage', 'rate_limited').inc()
                        raise RuntimeError("AV rate limit reached: Note present")
                    self._av_last_request_time = time.time()
                    quote = data.get("Global Quote", {})
                    price_str = quote.get("05. price") or quote.get("05. Price")
                    if price_str:
                        price = float(price_str)
                        self._price_cache[cache_key] = {
                            'price': price,
                            'timestamp': time.time()
                        }
                        if self._redis:
                            try:
                                self._redis.setex(cache_key, self._cache_ttl, str(price))
                            except Exception:
                                pass
                        self._av_failures = 0
                        market_provider_requests.labels('alpha_vantage', 'success').inc()
                        return price
                except Exception as e:
                    logger.warning(f"Alpha Vantage fetch failed for {symbol}: {e}")
                    market_provider_requests.labels('alpha_vantage', 'error').inc()

            # Try Polygon.io as secondary provider
            try:
                polygon_key = Config.POLYGON_API_KEY
                if polygon_key:
                    # Circuit breaker check
                    now_ts = time.time()
                    if now_ts < self._pg_open_until:
                        raise RuntimeError("Polygon circuit open")
                    
                    # Rate limiting: respect minimum interval
                    elapsed = now_ts - self._pg_last_request_time
                    if elapsed < self._pg_min_interval:
                        # Too soon: if we have cache, return it; else skip to avoid 429
                        if cache_key in self._price_cache:
                            return self._price_cache[cache_key]['price']
                        raise RuntimeError("Polygon rate limit cooldown")
                    
                    market_provider_requests.labels('polygon', 'attempt').inc()
                    
                    # Retry logic with exponential backoff for 429 errors
                    max_retries = 3
                    base_delay = 2.0
                    for attempt in range(max_retries):
                        try:
                            # Use previous aggregate close as a robust, cacheable proxy for last price
                            pg_url = f"https://api.polygon.io/v2/aggs/ticker/{symbol.upper()}/prev"
                            pg_params = {"adjusted": "true", "apiKey": polygon_key}
                            pg_resp = requests.get(pg_url, params=pg_params, timeout=8)
                            
                            # Handle 429 rate limit errors
                            if pg_resp.status_code == 429:
                                if attempt < max_retries - 1:
                                    delay = base_delay * (2 ** attempt)  # 2s, 4s, 8s
                                    logger.warning(f"Polygon 429 rate limit for {symbol}, retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})")
                                    time.sleep(delay)
                                    continue
                                else:
                                    # Max retries reached, open circuit breaker
                                    self._pg_open_until = time.time() + 60
                                    self._pg_failures += 1
                                    market_provider_requests.labels('polygon', 'rate_limited').inc()
                                    raise RuntimeError("Polygon rate limit exceeded after retries")
                            
                            pg_resp.raise_for_status()
                            pg_data = pg_resp.json()
                            results = (pg_data or {}).get("results") or []
                            if results:
                                close_val = results[0].get("c") or results[0].get("close")
                                if close_val:
                                    price = float(close_val)
                                    self._price_cache[cache_key] = {
                                        'price': price,
                                        'timestamp': time.time()
                                    }
                                    if self._redis:
                                        try:
                                            self._redis.setex(cache_key, self._cache_ttl, str(price))
                                        except Exception:
                                            pass
                                    self._pg_failures = 0
                                    self._pg_last_request_time = time.time()
                                    market_provider_requests.labels('polygon', 'success').inc()
                                    return price
                            self._pg_failures += 1
                            if self._pg_failures >= 3:
                                self._pg_open_until = time.time() + 60
                            market_provider_requests.labels('polygon', 'empty').inc()
                            break  # Successfully processed, exit retry loop
                        except requests.exceptions.RequestException as req_err:
                            # Network errors: retry with exponential backoff
                            if attempt < max_retries - 1:
                                delay = base_delay * (2 ** attempt) / 2  # 1s, 2s, 4s (shorter for network errors)
                                logger.warning(f"Polygon network error for {symbol}, retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries}): {req_err}")
                                time.sleep(delay)
                                continue
                            else:
                                raise
            except RuntimeError:
                # Circuit breaker or rate limit - don't retry, just log
                raise
            except Exception as e:
                logger.warning(f"Polygon fetch failed for {symbol}: {e}")
                self._pg_failures += 1
                if self._pg_failures >= 3:
                    self._pg_open_until = time.time() + 60
                market_provider_requests.labels('polygon', 'error').inc()

            # Try Yahoo Finance as fallback (no rate limits, free)
            if YFINANCE_AVAILABLE:
                try:
                    market_provider_requests.labels('yahoo_finance', 'attempt').inc()
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    # Try 'currentPrice' or 'regularMarketPrice' or last close
                    price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
                    if price:
                        price = float(price)
                        self._price_cache[cache_key] = {
                            'price': price,
                            'timestamp': time.time()
                        }
                        if self._redis:
                            try:
                                self._redis.setex(cache_key, self._cache_ttl, str(price))
                            except Exception:
                                pass
                        market_provider_requests.labels('yahoo_finance', 'success').inc()
                        logger.info(f"Yahoo Finance: fetched price for {symbol}: {price}")
                        return price
                except Exception as e:
                    logger.warning(f"Yahoo Finance fetch failed for {symbol}: {e}")
                    market_provider_requests.labels('yahoo_finance', 'error').inc()

            # Fallback to mock data
            mock_prices = {
                'AAPL': 175.43,
                'TSLA': 248.90,
                'MSFT': 378.85,
                'GOOGL': 142.50,
            }
            if symbol.upper() in mock_prices:
                price = mock_prices[symbol.upper()]
                self._price_cache[cache_key] = {
                    'price': price,
                    'timestamp': time.time()
                }
                return price
            
            logger.warning(f"Stock price for {symbol} not available")
            return None
        except Exception as e:
            logger.error(f"Error fetching stock price for {symbol}: {e}")
            return None
    
    def get_price(self, symbol: str, asset_type: str = 'auto') -> Optional[Dict]:
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
                price = self.get_crypto_price(symbol)
            else:
                price = self.get_stock_price(symbol)
            
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
    
    def get_watchlist_prices(self, symbols: List[str]) -> List[Dict]:
        """Get prices for multiple symbols"""
        results = []
        for symbol in symbols:
            data = self.get_price(symbol)
            if data:
                results.append(data)
        return results
    
    def get_market_data(self, symbol: str, asset_type: str = 'auto') -> Optional[Dict]:
        """Get comprehensive market data for an asset"""
        price_data = self.get_price(symbol, asset_type)
        if not price_data:
            return None
        
        # Add additional market data
        # TODO: Add volume, market cap, etc.
        return price_data

    def get_symbol_history(self, symbol: str, days: int = 7) -> Optional[List[Dict]]:
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
                    if time.time() - cached['timestamp'] < self._history_cache_ttl:
                        market_cache_hits.inc()
                        return cached['data']
            
            series = None
            # If crypto (simple detection by known list), use Binance
            crypto_symbols = ['BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'DOT', 'MATIC', 'AVAX']
            if symbol in crypto_symbols:
                try:
                    url = "https://api.binance.com/api/v3/klines"
                    params = {"symbol": f"{symbol}USDT", "interval": "1d", "limit": max(7, days)}
                    resp = requests.get(url, params=params, timeout=8)
                    resp.raise_for_status()
                    klines = resp.json() or []
                    series = []
                    for k in klines[-days:]:
                        # kline format: [ openTime, open, high, low, close, volume, closeTime, ... ]
                        close_price = float(k[4])
                        close_time_ms = int(k[6])
                        d = datetime.fromtimestamp(close_time_ms/1000).date().isoformat()
                        series.append({"date": d, "close": close_price})
                except Exception:
                    pass
            # Try Polygon aggregates range 1 day for past N days
            if series is None:
                try:
                    Config.init()
                    polygon_key = Config.POLYGON_API_KEY
                    if polygon_key:
                        import datetime as dt
                        end = dt.date.today()
                        start = end - dt.timedelta(days=days + 3)
                        url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{start}/{end}"
                        params = {"adjusted": "true", "sort": "asc", "limit": 250, "apiKey": polygon_key}
                        resp = requests.get(url, params=params, timeout=8)
                        resp.raise_for_status()
                        data = resp.json()
                        results = (data or {}).get("results") or []
                        series = [
                            {"date": datetime.fromtimestamp(r.get("t", 0)/1000).date().isoformat(), "close": float(r.get("c"))}
                            for r in results if r.get("c") is not None
                        ]
                        if series:
                            series = series[-days:]
                except Exception:
                    pass

            # Try Alpha Vantage TIME_SERIES_DAILY
            if series is None:
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
                            # Sorted asc by date
                            items = sorted(ts.items())
                            series = [{"date": d, "close": float(v.get("4. close"))} for d, v in items][-days:]
                except Exception:
                    pass

            # Fallback: synthesize from current price
            if series is None:
                base = self.get_price(symbol)
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
                        self._redis.setex(history_cache_key, self._history_cache_ttl, json.dumps(series))
                    except Exception:
                        pass
            
            return series if series else None
        except Exception as e:
            logger.error(f"Error fetching history for {symbol}: {e}")
            return None

    def get_symbol_history_with_interval(
        self, 
        symbol: str, 
        prediction_horizon: int
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
            
            # Determine interval and data requirements based on horizon
            if prediction_horizon <= 14:
                # Short-term: use hourly data
                interval = '1h'
                history_days = min(60, max(30, prediction_horizon * 3))
                limit_points = 1000  # Binance 1h limit
            elif prediction_horizon <= 60:
                # Medium-term: use daily data
                interval = '1d'
                history_days = min(180, max(120, prediction_horizon * 2))
                limit_points = 500  # Daily limit
            else:
                # Long-term: use weekly data
                interval = '1w'
                history_days = min(730, max(365, prediction_horizon * 4))
                limit_points = 500  # Weekly limit
            
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
                        # Circuit breaker check
                        now_ts = time.time()
                        if now_ts < self._pg_open_until:
                            raise RuntimeError("Polygon circuit open")
                        
                        # Rate limiting: respect minimum interval
                        elapsed = now_ts - self._pg_last_request_time
                        if elapsed < self._pg_min_interval:
                            # Too soon: wait or skip
                            wait_time = self._pg_min_interval - elapsed
                            logger.debug(f"Polygon rate limit: waiting {wait_time:.1f}s before request for {symbol}")
                            time.sleep(wait_time)
                        
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
                                        # Max retries reached, open circuit breaker
                                        self._pg_open_until = time.time() + 60
                                        self._pg_failures += 1
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
                                self._pg_last_request_time = time.time()
                                self._pg_failures = 0
                                break  # Successfully processed, exit retry loop
                            except requests.exceptions.RequestException as req_err:
                                # Network errors: retry with exponential backoff
                                if attempt < max_retries - 1:
                                    delay = base_delay * (2 ** attempt) / 2  # 1s, 2s, 4s (shorter for network errors)
                                    logger.warning(f"Polygon aggregates network error for {symbol}, retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries}): {req_err}")
                                    time.sleep(delay)
                                    continue
                                else:
                                    raise
                except RuntimeError:
                    # Circuit breaker or rate limit - don't retry, just log
                    logger.warning(f"Polygon aggregates fetch failed for {symbol}: circuit open or rate limit")
                except Exception as e:
                    logger.warning(f"Polygon aggregates fetch failed for {symbol}: {e}")
                    self._pg_failures += 1
                    if self._pg_failures >= 3:
                        self._pg_open_until = time.time() + 60
                    market_provider_requests.labels('polygon', 'error').inc()
            
            # Try Yahoo Finance as fallback (no rate limits, supports multiple intervals)
            if series is None and YFINANCE_AVAILABLE:
                try:
                    market_provider_requests.labels('yahoo_finance', 'attempt').inc()
                    ticker = yf.Ticker(symbol)
                    
                    # Calculate date range
                    end_date = dt.date.today()
                    start_date = end_date - dt.timedelta(days=history_days + 10)
                    
                    # Map interval to yfinance period
                    period_map = {
                        '1h': '1mo',  # 1 month of hourly data
                        '1d': '1y',   # 1 year of daily data
                        '1w': '2y'    # 2 years of weekly data
                    }
                    
                    # Use history() method for historical data
                    if interval == '1h':
                        hist = ticker.history(start=start_date, end=end_date, interval='1h')
                    elif interval == '1d':
                        hist = ticker.history(start=start_date, end=end_date, interval='1d')
                    elif interval == '1w':
                        hist = ticker.history(start=start_date, end=end_date, interval='1wk')
                    else:
                        hist = ticker.history(start=start_date, end=end_date, interval='1d')
                    
                    if not hist.empty:
                        series = []
                        for date, row in hist.iterrows():
                            series.append({
                                "date": date.date().isoformat(),
                                "close": float(row['Close']),
                                "open": float(row['Open']),
                                "high": float(row['High']),
                                "low": float(row['Low']),
                                "volume": float(row['Volume']) if 'Volume' in row else 0.0
                            })
                        
                        # Limit to requested history_days
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
                        logger.info(f"Yahoo Finance: fetched {len(series)} historical data points for {symbol} ({interval})")
                except Exception as e:
                    logger.warning(f"Yahoo Finance history fetch failed for {symbol}: {e}")
                    market_provider_requests.labels('yahoo_finance', 'error').inc()
            
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
                base = self.get_price(symbol)
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

    def search_symbols(self, query: str, limit: int = 10) -> List[Dict]:
        """Search tradable symbols using Polygon (preferred) or Alpha Vantage search.
        Returns a list of { symbol, name, type }.
        """
        results: List[Dict] = []
        q = (query or '').strip()
        if not q:
            return results
        try:
            # Try Polygon v3 reference tickers search
            try:
                Config.init()
                polygon_key = Config.POLYGON_API_KEY
                if polygon_key:
                    url = "https://api.polygon.io/v3/reference/tickers"
                    params = {"search": q, "active": "true", "limit": str(min(limit, 50)), "apiKey": polygon_key}
                    r = requests.get(url, params=params, timeout=8)
                    r.raise_for_status()
                    js = r.json() or {}
                    for it in (js.get('results') or [])[:limit]:
                        results.append({
                            'symbol': it.get('ticker'),
                            'name': it.get('name'),
                            'type': 'stock'
                        })
            except Exception:
                pass
            if results:
                return results

            # Fallback Alpha Vantage SYMBOL_SEARCH
            try:
                api_key = Config.ALPHA_VANTAGE_API_KEY
                if api_key:
                    url = "https://www.alphavantage.co/query"
                    params = {"function": "SYMBOL_SEARCH", "keywords": q, "apikey": api_key}
                    r = requests.get(url, params=params, timeout=8)
                    r.raise_for_status()
                    js = r.json() or {}
                    for it in (js.get('bestMatches') or [])[:limit]:
                        symbol = it.get('1. symbol')
                        name = it.get('2. name')
                        if symbol:
                            results.append({ 'symbol': symbol, 'name': name, 'type': 'stock' })
            except Exception:
                pass
        except Exception as e:
            logger.warning(f"search_symbols error: {e}")
        return results

