from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .config import Pillar


class MetricSnapshot(BaseModel):
    """
    Container for individual metric values and metadata.

    Each metric may expose both the raw numeric value and supporting context
    so downstream layers (AI insights, dashboards) can render rich explanations.
    """

    name: str
    pillar: Pillar
    value: Optional[float] = None
    score: Optional[float] = Field(
        default=None,
        description="Normalised metric score in range [0, 1] used during aggregation.",
    )
    weight: Optional[float] = None
    points: Optional[int] = Field(
        default=None,
        description="Discrete score in {0,1,2} reflecting checklist alignment.",
    )
    max_points: int = Field(default=2, description="Maximum attainable points for the metric.")
    confidence: float = Field(
        default=1.0,
        description="Confidence multiplier (0-1). Low confidence metrics contribute proportionally less.",
    )
    source: Optional[str] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None


class PillarScore(BaseModel):
    """
    Aggregated score for a single analytical pillar.
    """

    name: Pillar
    weight: float
    score: Optional[float] = None
    confidence: float = 1.0
    metrics: List[MetricSnapshot] = Field(default_factory=list)
    missing_metrics: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class DueDiligenceResult(BaseModel):
    """
    Top-level response returned by the Due Diligence 360° engine.
    """

    symbol: str
    base_currency: str = "USD"
    horizon: str = Field(
        default="long_term",
        description="Describes the typical evaluation horizon (e.g. long_term, mid_term).",
    )
    total_score: Optional[float] = None
    normalized_score: Optional[float] = Field(
        default=None,
        description="Score scaled to 0-100 for UI display.",
    )
    verdict: Optional[str] = None
    confidence: float = 1.0
    cached_at: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    data_provenance: Dict[str, Any] = Field(default_factory=dict)
    pillar_scores: List[PillarScore] = Field(default_factory=list)
    missing_pillars: List[Pillar] = Field(default_factory=list)
    global_warnings: List[str] = Field(default_factory=list)

    def get_pillar(self, pillar: Pillar) -> Optional[PillarScore]:
        for pillar_score in self.pillar_scores:
            if pillar_score.name == pillar:
                return pillar_score
        return None

