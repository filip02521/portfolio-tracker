from __future__ import annotations

import logging
import os
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class SantimentClient:
    """
    Santiment API client scaffold for development activity metrics.

    Full implementation depends on paid API access; this placeholder simply provides
    the interface needed by collectors and returns None when data is unavailable.
    """

    BASE_URL = "https://api.santiment.net/graphql"

    def __init__(self, api_key: Optional[str] = None, session: Optional[requests.Session] = None):
        self.api_key = api_key or os.getenv("SANTIMENT_API_KEY")
        self._session = session or requests.Session()
        if not self.api_key:
            logger.debug("SANTIMENT_API_KEY not configured; development activity metrics unavailable.")

    def get_development_activity(self, symbol: str) -> Optional[float]:
        return None

    def get_contributor_count(self, symbol: str) -> Optional[float]:
        return None

