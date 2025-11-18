"""
External data provider adapters used by the Due Diligence 360° engine.

These adapters wrap third-party APIs (e.g. CoinGecko, DeFi Llama) behind
thin, cache-aware facades so collectors can remain provider-agnostic.
"""

from .coingecko import CoinGeckoClient  # noqa: F401
from .glassnode import GlassnodeClient  # noqa: F401
from .coinmetrics import CoinMetricsClient  # noqa: F401
from .token_terminal import TokenTerminalClient  # noqa: F401
from .santiment import SantimentClient  # noqa: F401
from .binance_derivatives import BinanceDerivativesClient  # noqa: F401
from .defillama import DefiLlamaClient  # noqa: F401
from .github import GitHubClient  # noqa: F401

__all__ = [
    "CoinGeckoClient",
    "GlassnodeClient",
    "CoinMetricsClient",
    "TokenTerminalClient",
    "SantimentClient",
    "BinanceDerivativesClient",
    "DefiLlamaClient",
    "GitHubClient",
]

