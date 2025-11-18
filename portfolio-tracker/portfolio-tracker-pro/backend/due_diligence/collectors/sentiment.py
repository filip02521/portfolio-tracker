from __future__ import annotations

from typing import Any, Dict, Optional

import datetime as dt
from math import isfinite

try:
    import pandas as pd
    import yfinance as yf

    YFINANCE_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    YFINANCE_AVAILABLE = False
    pd = None
    yf = None

from ..config import Pillar
from ..models import MetricSnapshot
from .base import CollectorContext, CollectorOutput, MetricCollector


class SentimentCollector(MetricCollector):
    name = "sentiment"

    def collect(self, symbol: str, context: CollectorContext) -> CollectorOutput:
        output = CollectorOutput()
        payload = context.coingecko.get_asset_details(symbol)

        if not payload:
            output.warnings.append("CoinGecko sentiment data unavailable; sentiment pillar downgraded.")
            return output

        market_data: Dict[str, Any] = payload.get("market_data") or {}

        derivatives = context.binance_derivatives
        funding_value = None
        funding_metadata: Dict[str, Any] = {}

        derivatives_payload = None
        if derivatives:
            derivatives_payload = derivatives.get_funding_and_oi(symbol)
            if derivatives_payload:
                funding_value = self._combine_funding_signal(derivatives_payload, market_data)
                funding_metadata = {
                    "source": "binance_futures",
                    "funding_rate": derivatives_payload.get("funding_rate"),
                    "open_interest_value": derivatives_payload.get("open_interest_value"),
                }

        if funding_value is None:
            funding_value = self._estimate_funding_stress(market_data)
            if funding_value is not None:
                funding_metadata = {
                    "source": "coingecko_heuristic",
                    "price_change_24h": market_data.get("price_change_percentage_24h"),
                    "volume": (market_data.get("total_volume") or {}).get("usd"),
                }

        if funding_value is not None:
            output.metrics.append(
                MetricSnapshot(
                    name="funding_rate_oi_balance",
                    pillar=Pillar.SENTIMENT,
                    value=funding_value,
                    metadata=funding_metadata,
                )
            )
        else:
            output.warnings.append("Funding rate / OI metrics unavailable – integrate derivatives data provider.")

        macro_correlation = self._compute_macro_correlation(symbol)
        macro_metadata: Dict[str, Any] = {}
        if macro_correlation is not None:
            macro_metadata = {
                "source": "yfinance",
                "window_days": 90,
            }
        else:
            macro_correlation = self._estimate_macro_contagion_proxy(market_data)
            if macro_correlation is not None:
                macro_metadata = {
                    "source": "coingecko_heuristic",
                    "market_cap_change_24h": market_data.get("market_cap_change_percentage_24h"),
                    "volume_change_24h": market_data.get("total_volume"),
                }

        if macro_correlation is not None:
            output.metrics.append(
                MetricSnapshot(
                    name="macro_correlation_risk",
                    pillar=Pillar.SENTIMENT,
                    value=macro_correlation,
                    metadata=macro_metadata,
                )
            )
        else:
            output.warnings.append("Macro correlation risk unavailable – consider integrating TradFi correlation feed.")

        if not output.metrics:
            output.warnings.append("Sentiment metrics missing from CoinGecko payload.")

        return output

    @staticmethod
    def _combine_funding_signal(derivatives_data: Dict[str, Any], market_data: Dict[str, Any]) -> Optional[float]:
        try:
            funding_rate = float(derivatives_data.get("funding_rate", 0.0))
        except (TypeError, ValueError):
            funding_rate = 0.0

        market_cap = SentimentCollector._safe_float((market_data.get("market_cap") or {}).get("usd"))
        open_interest_value = derivatives_data.get("open_interest_value")
        if isinstance(open_interest_value, str):
            try:
                open_interest_value = float(open_interest_value)
            except (TypeError, ValueError):
                open_interest_value = None

        leverage_factor = 1.0
        if market_cap and open_interest_value:
            ratio = open_interest_value / market_cap
            leverage_factor = min(max(ratio, 0.0), 5.0)

        if not isfinite(funding_rate):
            return None

        return funding_rate * leverage_factor

    @staticmethod
    def _estimate_funding_stress(market_data: Dict[str, Any]) -> Optional[float]:
        price_change = SentimentCollector._safe_float(market_data.get("price_change_percentage_24h"))
        volume = SentimentCollector._safe_float((market_data.get("total_volume") or {}).get("usd"))
        market_cap = SentimentCollector._safe_float((market_data.get("market_cap") or {}).get("usd"))
        if price_change is None or volume is None or market_cap is None or market_cap <= 0:
            return None
        volume_to_cap = volume / market_cap
        return price_change * volume_to_cap

    @staticmethod
    def _estimate_macro_contagion_proxy(market_data: Dict[str, Any]) -> Optional[float]:
        market_cap_change = SentimentCollector._safe_float(market_data.get("market_cap_change_percentage_24h"))
        volume_change = SentimentCollector._safe_float(market_data.get("total_volume"))
        if market_cap_change is None or volume_change is None:
            return None
        if volume_change == 0:
            return None
        return market_cap_change / 100.0

    @staticmethod
    def _compute_macro_correlation(symbol: str) -> Optional[float]:
        if not YFINANCE_AVAILABLE:
            return None

        end_date = dt.datetime.utcnow().date()
        start_date = end_date - dt.timedelta(days=150)

        crypto_ticker = f"{symbol.upper()}-USD"
        try:
            crypto_df = yf.download(crypto_ticker, start=start_date, end=end_date, progress=False)
            spx_df = yf.download("^GSPC", start=start_date, end=end_date, progress=False)
        except Exception:  # pragma: no cover - network failure
            return None

        if crypto_df.empty or spx_df.empty:
            return None

        crypto_returns = crypto_df["Adj Close"].pct_change().dropna()
        spx_returns = spx_df["Adj Close"].pct_change().dropna()
        joined = crypto_returns.to_frame("asset").join(spx_returns.to_frame("spx"), how="inner")

        if joined.empty or len(joined) < 30:
            return None

        corr = joined["asset"].corr(joined["spx"])
        if corr is None or not isfinite(corr):
            return None
        return float(corr)

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        if value in (None, "", "null"):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
