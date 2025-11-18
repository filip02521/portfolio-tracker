from __future__ import annotations

import logging
import os
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class GlassnodeClient:
    """
    Lightweight wrapper for Glassnode API.

    Only minimal scaffolding is provided – real requests require a valid API key.
    Methods return None when the API key is missing so callers can fall back gracefully.
    """

    BASE_URL = "https://api.glassnode.com/v1"

    def __init__(self, api_key: Optional[str] = None, session: Optional[requests.Session] = None):
        self.api_key = api_key or os.getenv("GLASSNODE_API_KEY")
        self._session = session or requests.Session()
        if not self.api_key:
            logger.debug("GLASSNODE_API_KEY not configured; premium on-chain metrics will be unavailable.")

    def _get(self, endpoint: str, params: Optional[dict] = None) -> Optional[dict]:
        if not self.api_key:
            return None
        try:
            payload = {"api_key": self.api_key}
            if params:
                payload.update(params)
            response = self._session.get(f"{self.BASE_URL}/{endpoint.lstrip('/')}", params=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as exc:  # pragma: no cover - network failures
            logger.warning("Glassnode request failed for %s: %s", endpoint, exc)
            return None

    def get_mvrv_z_score(self, symbol: str) -> Optional[float]:
        # Endpoint: metrics/market/mvrv_z_score (requires paid plan)
        # TODO: implement actual parsing when premium API access is available.
        return None

    def get_hot_money_ratio(self, symbol: str) -> Optional[float]:
        # Endpoint: metrics/supply/hodl_waves
        return None

    def get_whale_realized_stress(self, symbol: str) -> Optional[float]:
        # Endpoint placeholder – requires entity-adjusted realized cap metrics.
        return None

