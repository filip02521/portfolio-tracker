from __future__ import annotations

import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class BinanceDerivativesClient:
    """
    Lightweight client for Binance USDT perpetual futures endpoints (public, no auth required).
    Provides funding rate and open interest used for the Sentiment pillar.
    """

    BASE_URL = "https://fapi.binance.com"

    def __init__(self, session: Optional[requests.Session] = None):
        self._session = session or requests.Session()

    def get_funding_and_oi(self, asset_symbol: str) -> Optional[dict]:
        """
        Fetch the latest funding rate, mark price and open interest for a given asset (e.g. BTC).
        Returns None if Binance does not list the symbol or the request fails.
        """
        symbol = f"{asset_symbol.upper()}USDT"

        premium_url = f"{self.BASE_URL}/fapi/v1/premiumIndex"
        oi_url = f"{self.BASE_URL}/fapi/v1/openInterest"

        try:
            premium_resp = self._session.get(premium_url, params={"symbol": symbol}, timeout=5)
            if premium_resp.status_code != 200:
                return None
            premium_data = premium_resp.json()
        except Exception as exc:  # pragma: no cover - network failure
            logger.debug("Binance premiumIndex fetch failed for %s: %s", symbol, exc)
            return None

        try:
            oi_resp = self._session.get(oi_url, params={"symbol": symbol}, timeout=5)
            if oi_resp.status_code == 200:
                oi_data = oi_resp.json()
            else:
                oi_data = {}
        except Exception as exc:  # pragma: no cover
            logger.debug("Binance openInterest fetch failed for %s: %s", symbol, exc)
            oi_data = {}

        try:
            funding_rate = float(premium_data.get("lastFundingRate", 0.0))
        except (TypeError, ValueError):
            funding_rate = 0.0

        try:
            mark_price = float(premium_data.get("markPrice", 0.0))
        except (TypeError, ValueError):
            mark_price = 0.0

        try:
            open_interest = float(oi_data.get("openInterest", 0.0))
        except (TypeError, ValueError):
            open_interest = 0.0

        open_interest_value = open_interest * mark_price if mark_price > 0 else None

        return {
            "symbol": symbol,
            "funding_rate": funding_rate,
            "mark_price": mark_price,
            "open_interest": open_interest,
            "open_interest_value": open_interest_value,
        }

