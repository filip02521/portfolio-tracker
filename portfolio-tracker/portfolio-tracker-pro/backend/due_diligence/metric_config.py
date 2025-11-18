from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from .config import Pillar


@dataclass(frozen=True)
class MetricDefinition:
    name: str
    pillar: Pillar
    weight: float
    description: str


# Raw weights as described in the expert report (Table VI.1)
_RAW_WEIGHTS = {
    # On-Chain (base sum 0.35 -> scaled to 0.45)
    "mvrv_z_score": 0.15,
    "nvt_ratio": 0.05,
    "hodl_waves_hot_money": 0.075,
    "whale_realized_cap_stress": 0.075,
    # Fundamental (sum 0.35)
    "deflationary_pressure_net": 0.10,
    "staking_ratio": 0.05,
    "tvl_market_cap_ratio": 0.05,
    "protocol_revenue_trend": 0.05,
    "development_activity_score": 0.05,
    "developer_contributor_count": 0.05,
    # Technical (sum 0.10)
    "ma200_trend_state": 0.05,
    "macro_rsi_position": 0.05,
    # Sentiment (sum 0.10)
    "funding_rate_oi_balance": 0.05,
    "macro_correlation_risk": 0.05,
}

_ONCHAIN_SCALE = 0.45 / 0.35

_METRIC_BASE: Dict[str, MetricDefinition] = {
    "mvrv_z_score": MetricDefinition(
        name="mvrv_z_score",
        pillar=Pillar.ON_CHAIN,
        weight=_RAW_WEIGHTS["mvrv_z_score"] * _ONCHAIN_SCALE,
        description="MVRV Z-Score (Market Value vs Realized Value).",
    ),
    "nvt_ratio": MetricDefinition(
        name="nvt_ratio",
        pillar=Pillar.ON_CHAIN,
        weight=_RAW_WEIGHTS["nvt_ratio"] * _ONCHAIN_SCALE,
        description="NVT Ratio (Network Value to Transaction).",
    ),
    "hodl_waves_hot_money": MetricDefinition(
        name="hodl_waves_hot_money",
        pillar=Pillar.ON_CHAIN,
        weight=_RAW_WEIGHTS["hodl_waves_hot_money"] * _ONCHAIN_SCALE,
        description="Share of supply held by short-term holders (Hot Money).",
    ),
    "whale_realized_cap_stress": MetricDefinition(
        name="whale_realized_cap_stress",
        pillar=Pillar.ON_CHAIN,
        weight=_RAW_WEIGHTS["whale_realized_cap_stress"] * _ONCHAIN_SCALE,
        description="Realized-cap stress within whale cohorts.",
    ),
    "deflationary_pressure_net": MetricDefinition(
        name="deflationary_pressure_net",
        pillar=Pillar.FUNDAMENTAL,
        weight=_RAW_WEIGHTS["deflationary_pressure_net"],
        description="Net deflationary pressure (burn minus issuance).",
    ),
    "staking_ratio": MetricDefinition(
        name="staking_ratio",
        pillar=Pillar.FUNDAMENTAL,
        weight=_RAW_WEIGHTS["staking_ratio"],
        description="Percentage of supply locked in staking (PoS security).",
    ),
    "tvl_market_cap_ratio": MetricDefinition(
        name="tvl_market_cap_ratio",
        pillar=Pillar.FUNDAMENTAL,
        weight=_RAW_WEIGHTS["tvl_market_cap_ratio"],
        description="Total Value Locked to Market Cap ratio.",
    ),
    "protocol_revenue_trend": MetricDefinition(
        name="protocol_revenue_trend",
        pillar=Pillar.FUNDAMENTAL,
        weight=_RAW_WEIGHTS["protocol_revenue_trend"],
        description="Revenue / fee generation trend.",
    ),
    "development_activity_score": MetricDefinition(
        name="development_activity_score",
        pillar=Pillar.FUNDAMENTAL,
        weight=_RAW_WEIGHTS["development_activity_score"],
        description="Santiment-style development activity score.",
    ),
    "developer_contributor_count": MetricDefinition(
        name="developer_contributor_count",
        pillar=Pillar.FUNDAMENTAL,
        weight=_RAW_WEIGHTS["developer_contributor_count"],
        description="Unique active contributors.",
    ),
    "ma200_trend_state": MetricDefinition(
        name="ma200_trend_state",
        pillar=Pillar.TECHNICAL,
        weight=_RAW_WEIGHTS["ma200_trend_state"],
        description="Weekly/Macro MA200 trend confirmation.",
    ),
    "macro_rsi_position": MetricDefinition(
        name="macro_rsi_position",
        pillar=Pillar.TECHNICAL,
        weight=_RAW_WEIGHTS["macro_rsi_position"],
        description="Macro RSI positioning for pullback timing.",
    ),
    "funding_rate_oi_balance": MetricDefinition(
        name="funding_rate_oi_balance",
        pillar=Pillar.SENTIMENT,
        weight=_RAW_WEIGHTS["funding_rate_oi_balance"],
        description="Funding rate and open-interest stress.",
    ),
    "macro_correlation_risk": MetricDefinition(
        name="macro_correlation_risk",
        pillar=Pillar.SENTIMENT,
        weight=_RAW_WEIGHTS["macro_correlation_risk"],
        description="TradFi contagion / macro correlation risk.",
    ),
}


METRIC_DEFINITIONS: Dict[str, MetricDefinition] = _METRIC_BASE
TOTAL_WEIGHT = sum(definition.weight for definition in METRIC_DEFINITIONS.values())


def score_metric(name: str, value: Optional[float], metadata: Optional[dict] = None) -> Optional[int]:
    """
    Map raw metric values to discrete checklist points (0,1,2).
    Returns None when the metric could not be evaluated due to missing data.
    """
    metadata = metadata or {}

    if value is None:
        return None

    if name == "mvrv_z_score":
        if value <= 0.0:
            return 2
        if value < 7.0:
            return 1
        return 0

    if name == "nvt_ratio":
        trend = metadata.get("trend")
        if trend == "falling":
            return 2
        if value <= 50:
            return 2
        if value <= 90:
            return 1
        return 0

    if name == "hodl_waves_hot_money":
        if value <= 0.20:
            return 2
        if value <= 0.35:
            return 1
        return 0

    if name == "whale_realized_cap_stress":
        if value <= 0.10:
            return 2
        if value <= 0.20:
            return 1
        return 0

    if name == "deflationary_pressure_net":
        if value > 0:
            return 2
        if abs(value) <= 0.01:
            return 1
        return 0

    if name == "staking_ratio":
        if value >= 0.60:
            return 2
        if value >= 0.40:
            return 1
        return 0

    if name == "tvl_market_cap_ratio":
        if value >= 1.0:
            return 2
        if value >= 0.6:
            return 1
        return 0

    if name == "protocol_revenue_trend":
        trend = metadata.get("trend")
        if trend == "growing":
            return 2
        if trend == "stable":
            return 1
        if value >= 1_000_000:
            return 2
        if value >= 100_000:
            return 1
        return 0

    if name == "development_activity_score":
        if value >= 80:
            return 2
        if value >= 30:
            return 1
        return 0

    if name == "developer_contributor_count":
        if value >= 20:
            return 2
        if value >= 5:
            return 1
        return 0

    if name == "ma200_trend_state":
        if value >= 1.0:
            return 2
        if value >= 0.95:
            return 1
        return 0

    if name == "macro_rsi_position":
        if 40 <= value <= 60:
            return 2
        if 35 <= value <= 70:
            return 1
        return 0

    if name == "funding_rate_oi_balance":
        if abs(value) <= 0.02:
            return 2
        if abs(value) <= 0.05:
            return 1
        return 0

    if name == "macro_correlation_risk":
        if abs(value) <= 0.3:
            return 2
        if abs(value) <= 0.5:
            return 1
        return 0

    return None

