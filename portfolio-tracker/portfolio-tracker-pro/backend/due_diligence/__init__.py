"""
Due Diligence 360° package.

Provides shared configuration and data models for the long-horizon
fundamental/on-chain scoring engine so multiple services (strategy,
AI insight, analytics) can reuse the same contracts without duplication.
"""

from .config import DueDiligenceConfig, DEFAULT_PILLAR_WEIGHTS, Pillar  # noqa: F401
from .models import (  # noqa: F401
    DueDiligenceResult,
    MetricSnapshot,
    PillarScore,
)

__all__ = [
    "DueDiligenceConfig",
    "DEFAULT_PILLAR_WEIGHTS",
    "Pillar",
    "DueDiligenceResult",
    "PillarScore",
    "MetricSnapshot",
]

