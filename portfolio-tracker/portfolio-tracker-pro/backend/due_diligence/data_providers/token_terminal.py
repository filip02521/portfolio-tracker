from __future__ import annotations

import logging
import os
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class TokenTerminalClient:
    """
    Skeleton client for the TokenTerminal API (https://tokenterminal.com/).
    Requires API access – returns None when credentials are missing.
    """

    BASE_URL = "https://api.tokenterminal.com/v2"

    def __init__(self, api_key: Optional[str] = None, session: Optional[requests.Session] = None):
        self.api_key = api_key or os.getenv("TOKENTERMINAL_API_KEY")
        self._session = session or requests.Session()
        if not self.api_key:
            logger.debug("TOKENTERMINAL_API_KEY not configured; protocol revenue metrics unavailable.")

    def _headers(self) -> dict:
        if not self.api_key:
            return {}
        return {"Authorization": f"Bearer {self.api_key}"}

    def get_revenue(self, symbol: str) -> Optional[float]:
        # Endpoint placeholder: /protocols/{symbol}/financials
        return None

    def get_tvl(self, symbol: str) -> Optional[float]:
        # Endpoint placeholder: /protocols/{symbol}/metrics
        return None

