from __future__ import annotations

import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class DefiLlamaClient:
    """
    Minimal client for the open DeFiLlama API.

    Primarily used to fetch protocol-level TVL denominated in USD.
    """

    BASE_URL = "https://api.llama.fi"

    def __init__(self, session: Optional[requests.Session] = None):
        self._session = session or requests.Session()

    def get_protocol_tvl(self, slug: str) -> Optional[float]:
        """
        Fetch the latest total TVL for a given protocol slug (e.g. 'makerdao', 'aave').
        Returns None if the protocol is not listed or the API call fails.
        """
        if not slug:
            return None

        url = f"{self.BASE_URL}/protocol/{slug}"
        try:
            response = self._session.get(url, timeout=8)
            if response.status_code != 200:
                return None
            payload = response.json()
        except Exception as exc:  # pragma: no cover - network failure
            logger.debug("DeFiLlama protocol fetch failed for %s: %s", slug, exc)
            return None

        # Many responses contain 'tvl' (history) and 'currentChainTvls' dict.
        # Prefer 'currentChainTvls' sum if available, otherwise last entry of 'tvl'.
        if isinstance(payload, dict):
            chain_data = payload.get("currentChainTvls")
            if isinstance(chain_data, dict) and chain_data:
                try:
                    return float(sum(chain_data.values()))
                except (TypeError, ValueError):
                    pass

            history = payload.get("tvl")
            if isinstance(history, list) and history:
                for entry in reversed(history):
                    value = entry.get("totalLiquidityUSD")
                    if value is not None:
                        try:
                            return float(value)
                        except (TypeError, ValueError):
                            continue

        return None

