from __future__ import annotations

from typing import List, Optional

from ..config import Pillar
from ..models import MetricSnapshot
from .base import CollectorContext, CollectorOutput, MetricCollector


class TechnicalCollector(MetricCollector):
    name = "technical"

    def collect(self, symbol: str, context: CollectorContext) -> CollectorOutput:
        output = CollectorOutput()
        market_data_service = context.market_data_service

        if market_data_service is None:
            output.warnings.append("MarketDataService missing; skipping technical metrics.")
            return output

        daily_series = self._fetch_series(market_data_service, symbol, prediction_horizon=365, interval="1d")
        weekly_series = self._fetch_series(market_data_service, symbol, prediction_horizon=365 * 3, interval="1w")

        ma200_ratio = None
        ma200_metadata = {}
        if weekly_series:
            ma200_diff = self._compute_moving_average_trend(weekly_series, window=200)
            if ma200_diff is not None:
                ma200_ratio = 1.0 + ma200_diff
            ma200_metadata = {"window": 200, "interval": "1w"}
        if ma200_ratio is None and daily_series:
            ma200_diff = self._compute_moving_average_trend(daily_series, window=200)
            if ma200_diff is not None:
                ma200_ratio = 1.0 + ma200_diff
            ma200_metadata = {"window": 200, "interval": "1d", "approximation": True}

        if ma200_ratio is not None:
            output.metrics.append(
                MetricSnapshot(
                    name="ma200_trend_state",
                    pillar=Pillar.TECHNICAL,
                    value=ma200_ratio,
                    metadata=ma200_metadata,
                )
            )

        if daily_series:
            rsi_value = self._compute_rsi(daily_series, window=14)
            if rsi_value is not None:
                output.metrics.append(
                    MetricSnapshot(
                        name="macro_rsi_position",
                        pillar=Pillar.TECHNICAL,
                        value=rsi_value,
                        metadata={"window": 14, "interval": "1d"},
                    )
                )

        if not output.metrics:
            output.warnings.append("Insufficient historical data for technical metrics.")

        return output

    @staticmethod
    def _fetch_series(
        market_data_service,
        symbol: str,
        prediction_horizon: int,
        interval: Optional[str] = None,
    ) -> Optional[List[float]]:
        try:
            data, _ = market_data_service.get_symbol_history_with_interval(
                symbol,
                prediction_horizon=prediction_horizon,
                preferred_interval=interval,
                priority='low',
            )
            if not data:
                return None
            closes = [float(item.get("close")) for item in data if item.get("close") is not None]
            return closes if len(closes) >= 10 else None
        except Exception:
            return None

    @staticmethod
    def _compute_moving_average_trend(series: List[float], window: int) -> Optional[float]:
        if len(series) < window + 5:
            return None
        prices = series[-(window + 5) :]
        moving_average = sum(prices[:-5]) / window
        current_price = prices[-1]
        if moving_average == 0:
            return None
        return (current_price - moving_average) / moving_average

    @staticmethod
    def _compute_rsi(series: List[float], window: int) -> Optional[float]:
        if len(series) <= window:
            return None

        gains: List[float] = []
        losses: List[float] = []
        for i in range(1, window + 1):
            delta = series[-i] - series[-i - 1]
            if delta >= 0:
                gains.append(delta)
            else:
                losses.append(abs(delta))

        avg_gain = sum(gains) / window if gains else 0.0
        avg_loss = sum(losses) / window if losses else 0.0

        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1 + rs))

