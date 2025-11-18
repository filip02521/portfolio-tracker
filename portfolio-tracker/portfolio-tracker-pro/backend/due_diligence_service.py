from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional

from logging_config import get_logger

from due_diligence.collectors import (
    CollectorContext,
    FundamentalCollector,
    MetricCollector,
    OnChainCollector,
    SentimentCollector,
    TechnicalCollector,
)
from due_diligence.config import DueDiligenceConfig, Pillar
from due_diligence.data_providers import (
    BinanceDerivativesClient,
    CoinGeckoClient,
    CoinMetricsClient,
    DefiLlamaClient,
    GitHubClient,
    GlassnodeClient,
    SantimentClient,
    TokenTerminalClient,
)
from due_diligence.metric_config import METRIC_DEFINITIONS, score_metric
from due_diligence.models import DueDiligenceResult, MetricSnapshot, PillarScore

logger = get_logger(__name__)


class DueDiligenceService:
    """
    Long-horizon Due Diligence 360° scoring engine.

    Orchestrates metric collectors, applies scoring heuristics derived from the
    DUE DILIGENCE 360° methodology, and returns an explainable pillar breakdown.
    """

    def __init__(
        self,
        market_data_service=None,
        config: Optional[DueDiligenceConfig] = None,
        collectors: Optional[Iterable[MetricCollector]] = None,
        cache_ttl_seconds: int = 900,
    ) -> None:
        self.market_data_service = market_data_service
        self.config = config or DueDiligenceConfig.load_from_env()
        self.cache_ttl_seconds = max(cache_ttl_seconds, 120)
        self._cache: Dict[str, Dict[str, object]] = {}
        self._coingecko = CoinGeckoClient()
        self._glassnode = GlassnodeClient()
        self._coinmetrics = CoinMetricsClient()
        self._token_terminal = TokenTerminalClient()
        self._santiment = SantimentClient()
        self._binance_derivatives = BinanceDerivativesClient()
        self._defillama = DefiLlamaClient()
        self._github = GitHubClient()

        if collectors:
            self.collectors = list(collectors)
        else:
            self.collectors = [
                FundamentalCollector(),
                OnChainCollector(),
                TechnicalCollector(),
                SentimentCollector(),
            ]

    def evaluate(self, symbol: str, force_refresh: bool = False) -> DueDiligenceResult:
        cache_key = symbol.lower()
        now_ts = time.time()

        if not force_refresh and cache_key in self._cache:
            entry = self._cache[cache_key]
            if now_ts - entry["timestamp"] < self.cache_ttl_seconds:
                cached_result = entry["result"]
                if isinstance(cached_result, DueDiligenceResult):
                    return cached_result

        context = CollectorContext(
            config=self.config,
            coingecko=self._coingecko,
            market_data_service=self.market_data_service,
            glassnode=self._glassnode,
            coinmetrics=self._coinmetrics,
            token_terminal=self._token_terminal,
            santiment=self._santiment,
            binance_derivatives=self._binance_derivatives,
            defillama=self._defillama,
            github=self._github,
        )

        pillar_weight_map: Dict[Pillar, float] = {
            pillar: sum(defn.weight for defn in METRIC_DEFINITIONS.values() if defn.pillar == pillar)
            for pillar in Pillar
        }
        pillar_map: Dict[Pillar, PillarScore] = {
            pillar: PillarScore(name=pillar, weight=weight)
            for pillar, weight in pillar_weight_map.items()
        }
        global_warnings: List[str] = []
        collected_metrics: Dict[str, MetricSnapshot] = {}

        for collector in self.collectors:
            try:
                output = collector.collect(symbol, context)
            except Exception as exc:
                logger.error("Collector %s failed for %s: %s", collector.name, symbol, exc, exc_info=True)
                global_warnings.append(f"{collector.name} collector failed: {exc}")
                continue

            global_warnings.extend(output.warnings)
            for metric in output.metrics:
                definition = METRIC_DEFINITIONS.get(metric.name)
                if definition is None:
                    global_warnings.append(f"Unhandled metric '{metric.name}' returned by collector.")
                    continue
                metric.weight = definition.weight
                metric.points = score_metric(metric.name, metric.value, metric.metadata)
                if metric.points is not None:
                    metric.score = metric.points / metric.max_points
                else:
                    metric.score = None
                    metric.confidence = 0.0
                pillar_entry = pillar_map[definition.pillar]
                pillar_entry.metrics.append(metric)
                if metric.points is None:
                    if metric.name not in pillar_entry.missing_metrics:
                        pillar_entry.missing_metrics.append(metric.name)
                collected_metrics[metric.name] = metric

        # Mark metrics that were not collected at all
        for name, definition in METRIC_DEFINITIONS.items():
            if name not in collected_metrics:
                pillar_entry = pillar_map[definition.pillar]
                if name not in pillar_entry.missing_metrics:
                    pillar_entry.missing_metrics.append(name)

        pillar_scores: List[PillarScore] = []
        weighted_total = 0.0
        available_weight = 0.0
        missing_pillars: List[Pillar] = []

        for pillar, pillar_entry in pillar_map.items():
            if not pillar_entry.metrics:
                missing_pillars.append(pillar)
                pillar_scores.append(pillar_entry)
                continue

            weighted_sum = 0.0
            weight_total = 0.0
            confidence_total = 0.0
            scored_count = 0

            for metric in pillar_entry.metrics:
                if metric.points is None or metric.weight is None:
                    continue
                metric_confidence = max(min(metric.confidence, 1.0), 0.0)
                contribution_weight = metric.weight * metric_confidence
                weight_total += contribution_weight
                weighted_sum += (metric.points / metric.max_points) * contribution_weight
                confidence_total += metric_confidence
                scored_count += 1

            if weight_total > 0:
                pillar_entry.score = weighted_sum / weight_total
                pillar_entry.confidence = confidence_total / scored_count if scored_count else 0.0
                weighted_total += weighted_sum
                available_weight += weight_total
            else:
                pillar_entry.score = None
                pillar_entry.confidence = 0.0

            pillar_scores.append(pillar_entry)

        normalized_score = (weighted_total / available_weight) if available_weight > 0 else None
        normalized_percent = normalized_score * 100 if normalized_score is not None else None

        verdict = self._verdict_from_score(normalized_percent)

        cached_at = datetime.now(timezone.utc)
        result = DueDiligenceResult(
            symbol=symbol.upper(),
            total_score=normalized_score,
            normalized_score=normalized_percent,
            verdict=verdict,
            confidence=self._aggregate_confidence(pillar_scores),
            cached_at=cached_at,
            valid_until=cached_at + timedelta(seconds=self.cache_ttl_seconds),
            data_provenance={
                "providers": self._provenance_providers(),
                "cache_ttl_seconds": self.cache_ttl_seconds,
            },
            pillar_scores=pillar_scores,
            missing_pillars=missing_pillars,
            global_warnings=global_warnings,
        )

        self._cache[cache_key] = {"result": result, "timestamp": now_ts}
        return result

    def invalidate(self, symbol: Optional[str] = None) -> None:
        if symbol is None:
            self._cache.clear()
            return
        self._cache.pop(symbol.lower(), None)

    @staticmethod
    def _aggregate_confidence(pillar_scores: Iterable[PillarScore]) -> float:
        confidences = [
            score.confidence
            for score in pillar_scores
            if score.confidence is not None and score.metrics
        ]
        if not confidences:
            return 0.0
        return sum(confidences) / len(confidences)

    @staticmethod
    def _verdict_from_score(score: Optional[float]) -> Optional[str]:
        if score is None:
            return None
        if score >= 75:
            return "strong_bullish"
        if score >= 50:
            return "cautious_bullish"
        if score >= 35:
            return "neutral"
        return "bearish"

    def _provenance_providers(self) -> List[str]:
        providers = ["coingecko"]
        if getattr(self._glassnode, "api_key", None):
            providers.append("glassnode")
        if getattr(self._coinmetrics, "api_key", None):
            providers.append("coinmetrics")
        if getattr(self._token_terminal, "api_key", None):
            providers.append("tokenterminal")
        if getattr(self._santiment, "api_key", None):
            providers.append("santiment")
        providers.append("binance_futures")
        providers.append("defillama")
        providers.append("github")
        return providers

