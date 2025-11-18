from __future__ import annotations

import threading
import time
from typing import Any, Dict, Optional

import requests

from logging_config import get_logger

logger = get_logger(__name__)

_DEFAULT_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "portfolio-tracker-due-diligence/1.0",
}


class CoinGeckoClient:
    """
    Minimal CoinGecko client focused on metrics required by the Due Diligence engine.

    The public API is rate-limited (up to 50 calls/minute). We therefore cache responses
    aggressively and guard concurrent refreshes with a simple lock.
    """

    def __init__(self, session: Optional[requests.Session] = None, ttl_seconds: int = 900):
        self._session = session or requests.Session()
        self._session.headers.update(_DEFAULT_HEADERS)
        self._ttl_seconds = max(ttl_seconds, 60)
        self._coin_cache: Dict[str, Dict[str, Any]] = {}
        self._id_cache: Dict[str, str] = {}
        self._lock = threading.Lock()

    def get_asset_details(self, asset_symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch the CoinGecko `coins/{id}` payload for a given asset symbol (e.g. BTC, ETH).

        Returns cached results when available; otherwise performs a lookup via `/search`
        and then fetches the full asset payload with `localization=false` to minimise size.
        """
        symbol = (asset_symbol or "").lower().strip()
        if not symbol:
            return None

        # Serve from cache when fresh
        cached = self._coin_cache.get(symbol)
        if cached and time.time() - cached["timestamp"] < self._ttl_seconds:
            return cached["data"]

        with self._lock:
            cached = self._coin_cache.get(symbol)
            if cached and time.time() - cached["timestamp"] < self._ttl_seconds:
                return cached["data"]

            coin_id = self._resolve_coin_id(symbol)
            if not coin_id:
                logger.debug("CoinGecko lookup failed for symbol %s", symbol)
                return None

            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
            params = {
                "localization": "false",
                "tickers": "false",
                "market_data": "true",
                "community_data": "false",
                "developer_data": "true",
                "sparkline": "false",
            }

            try:
                response = self._session.get(url, params=params, timeout=10)
                response.raise_for_status()
                payload = response.json()
                self._coin_cache[symbol] = {"data": payload, "timestamp": time.time()}
                return payload
            except requests.HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else None
                if status == 429:
                    logger.warning("CoinGecko rate limit reached while fetching %s; returning stale data if available", symbol)
                    if cached:
                        return cached["data"]
                logger.warning("CoinGecko HTTP error for %s: %s", symbol, exc)
            except requests.RequestException as exc:
                logger.warning("CoinGecko network error for %s: %s", symbol, exc)

            return cached["data"] if cached else None

    def _resolve_coin_id(self, symbol: str) -> Optional[str]:
        """
        Resolve a CoinGecko coin ID from a symbol (case insensitive).
        Results are cached to avoid repeated `/search` calls.
        """
        if symbol in self._id_cache:
            return self._id_cache[symbol]

        search_url = "https://api.coingecko.com/api/v3/search"
        try:
            response = self._session.get(search_url, params={"query": symbol}, timeout=8)
            response.raise_for_status()
            items = (response.json() or {}).get("coins") or []
            for item in items:
                if item.get("symbol", "").lower() == symbol:
                    coin_id = item.get("id")
                    if coin_id:
                        self._id_cache[symbol] = coin_id
                        return coin_id
        except requests.RequestException as exc:
            logger.warning("CoinGecko search error for %s: %s", symbol, exc)
            return None

        return None

