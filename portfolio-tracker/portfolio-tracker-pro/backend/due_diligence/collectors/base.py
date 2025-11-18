from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Protocol, TYPE_CHECKING

from ..config import DueDiligenceConfig
from ..models import MetricSnapshot
from ..data_providers import (
    BinanceDerivativesClient,
    CoinGeckoClient,
    CoinMetricsClient,
    DefiLlamaClient,
    GitHubClient,
    GlassnodeClient,
    SantimentClient,
    TokenTerminalClient,
)

if TYPE_CHECKING:
    from market_data_service import MarketDataService


@dataclass
class CollectorContext:
    """
    Shared dependencies for collectors.

    New providers can be added in the future (e.g., Glassnode, TokenTerminal) without
    changing individual collector signatures.
    """

    config: DueDiligenceConfig
    coingecko: CoinGeckoClient
    market_data_service: Optional["MarketDataService"] = None
    glassnode: Optional[GlassnodeClient] = None
    coinmetrics: Optional[CoinMetricsClient] = None
    token_terminal: Optional[TokenTerminalClient] = None
    santiment: Optional[SantimentClient] = None
    binance_derivatives: Optional[BinanceDerivativesClient] = None
    defillama: Optional[DefiLlamaClient] = None
    github: Optional[GitHubClient] = None


@dataclass
class CollectorOutput:
    metrics: List[MetricSnapshot] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class MetricCollector(Protocol):
    name: str

    def collect(self, symbol: str, context: CollectorContext) -> CollectorOutput:
        ...

