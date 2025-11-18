from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Mapping, Optional


class Pillar(str, Enum):
    ON_CHAIN = "on_chain"
    FUNDAMENTAL = "fundamental"
    TECHNICAL = "technical"
    SENTIMENT = "sentiment"


DEFAULT_PILLAR_WEIGHTS: Mapping[Pillar, float] = {
    Pillar.ON_CHAIN: 0.45,
    Pillar.FUNDAMENTAL: 0.35,
    Pillar.TECHNICAL: 0.10,
    Pillar.SENTIMENT: 0.10,
}


def _parse_env_mapping(env_value: Optional[str]) -> Dict[str, float]:
    """
    Parse environment override strings of the form "pillar=weight,pillar=weight".

    Invalid entries are ignored, allowing safe partial overrides.
    """
    result: Dict[str, float] = {}
    if not env_value:
        return result

    for entry in env_value.split(","):
        key_value = entry.strip().split("=")
        if len(key_value) != 2:
            continue
        key, value = key_value
        try:
            result[key.strip()] = float(value)
        except (TypeError, ValueError):
            continue
    return result


@dataclass(frozen=True)
class DueDiligenceConfig:
    """
    Runtime configuration for the Due Diligence 360° scoring engine.

    Loads weight overrides from environment variables so experimentation/backtesting
    can happen without code changes.
    """

    pillar_weights: Mapping[Pillar, float]
    metric_weight_overrides: Mapping[str, float]

    @classmethod
    def load_from_env(
        cls,
        pillar_env: str = "DD360_PILLAR_WEIGHTS",
        metric_env: str = "DD360_METRIC_WEIGHTS",
    ) -> "DueDiligenceConfig":
        pillar_weights = dict(DEFAULT_PILLAR_WEIGHTS)

        env_pillar_overrides = _parse_env_mapping(os.getenv(pillar_env))
        for key, value in env_pillar_overrides.items():
            try:
                pillar = Pillar(key)
            except ValueError:
                continue
            pillar_weights[pillar] = value

        metric_weight_overrides = _parse_env_mapping(os.getenv(metric_env))

        cls._normalise_weights(pillar_weights)

        return cls(
            pillar_weights=pillar_weights,
            metric_weight_overrides=metric_weight_overrides,
        )

    @staticmethod
    def _normalise_weights(weights: Dict[Pillar, float]) -> None:
        total = sum(weights.values())
        if total <= 0:
            raise ValueError("Pillar weights must sum to a positive number")

        if abs(total - 1.0) < 1e-9:
            return

        scale = 1.0 / total
        for pillar, value in list(weights.items()):
            weights[pillar] = value * scale

