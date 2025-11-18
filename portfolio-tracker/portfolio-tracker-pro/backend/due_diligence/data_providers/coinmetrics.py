from __future__ import annotations

import logging
import os
import time
from typing import Dict, Optional

import requests
from requests import RequestException

logger = logging.getLogger(__name__)


class CoinMetricsClient:
    """
    Adapter for the CoinMetrics Community API.

    Fetches NVT Signal (90-day smoothed) when possible. Falls back to None so the
    calling collectors can rely on heuristic approximations.
    """

    BASE_URL = "https://community-api.coinmetrics.io/v4"
    DEFAULT_TIMEOUT = 10
    CACHE_TTL_SECONDS = 900
    _ASSET_ALIASES: Dict[str, str] = {
        "btc": "btc",
        "xbt": "btc",
        "eth": "eth",
        "sol": "sol",
        "ada": "ada",
        "avax": "avax",
        "matic": "matic",
        "pol": "matic",
        "dot": "dot",
        "ltc": "ltc",
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        session: Optional[requests.Session] = None,
    ):
        self.api_key = api_key or os.getenv("COINMETRICS_API_KEY")
        self._session = session or requests.Session()
        self._headers = {}
        if self.api_key:
            self._headers["X-CoinMetrics-API-Key"] = self.api_key
        else:
            logger.debug("COINMETRICS_API_KEY not configured; using public community limits.")
        self._cache: Dict[str, Dict[str, float]] = {}

    def get_nvt_signal(self, symbol: str, window: int = 90) -> Optional[float]:
        """
        Retrieves the latest CoinMetrics NVT Signal (90-day average).
        Returns None if the metric is unavailable or the request fails.
        """
        asset = self._normalize_symbol(symbol)
        if asset is None:
            logger.debug("CoinMetrics: unable to normalise symbol '%s'", symbol)
            return None

        cached = self._cache.get(asset)
        now = time.time()
        if cached and now - cached.get("timestamp", 0) < self.CACHE_TTL_SECONDS:
            return cached.get("value")

        params = {
            "assets": asset,
            "metrics": "CapMrktCurUSD,volume_reported_spot_usd_1d",
            "page_size": max(window, 90),
        }

        payload = self._get("timeseries/asset-metrics", params)
        if not payload:
            return None

        data = payload.get("data") or []
        ratios = []
        for entry in data:
            market_cap = self._safe_float(entry.get("CapMrktCurUSD"))
            volume = self._safe_float(entry.get("volume_reported_spot_usd_1d"))
            if market_cap is None or volume is None or volume <= 0:
                continue
            ratios.append(market_cap / volume)

        if not ratios:
            return None

        windowed = ratios[-window:] if len(ratios) > window else ratios
        value = sum(windowed) / len(windowed)
        self._cache[asset] = {"value": value, "timestamp": now}
        return value

    def _get(self, endpoint: str, params: Dict[str, object]) -> Optional[Dict[str, object]]:
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            response = self._session.get(
                url,
                params=params,
                headers=self._headers,
                timeout=self.DEFAULT_TIMEOUT,
            )
        except RequestException as exc:  # pragma: no cover - network failure
            logger.warning("CoinMetrics request failed for %s: %s", url, exc)
            return None

        if response.status_code == 401:
            logger.warning("CoinMetrics API rejected request (401). Configure COINMETRICS_API_KEY for extended access.")
            return None
        if response.status_code == 404:
            logger.debug("CoinMetrics metric not found for params %s", params)
            return None
        if not response.ok:
            logger.warning("CoinMetrics returned status %s for %s: %s", response.status_code, url, response.text)
            return None

        try:
            return response.json()
        except ValueError:
            logger.warning("CoinMetrics payload could not be parsed as JSON.")
            return None

    @classmethod
    def _normalize_symbol(cls, symbol: str) -> Optional[str]:
        if not symbol:
            return None
        canonical = cls._ASSET_ALIASES.get(symbol.lower())
        if canonical:
            return canonical
        if len(symbol) <= 6:
            return symbol.lower()
        return None

    @staticmethod
    def _safe_float(value: Optional[str]) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None


