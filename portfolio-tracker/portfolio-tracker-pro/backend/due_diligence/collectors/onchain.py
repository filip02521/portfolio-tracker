from __future__ import annotations

from typing import Any, Dict, Optional

from ..config import Pillar
from ..models import MetricSnapshot
from .base import CollectorContext, CollectorOutput, MetricCollector


class OnChainCollector(MetricCollector):
    name = "on_chain"

    def collect(self, symbol: str, context: CollectorContext) -> CollectorOutput:
        output = CollectorOutput()
        payload = context.coingecko.get_asset_details(symbol)

        if not payload:
            output.warnings.append("CoinGecko on-chain metrics unavailable; on-chain pillar downgraded.")
            return output

        market_data: Dict[str, Any] = payload.get("market_data") or {}
        glassnode = context.glassnode
        coinmetrics = context.coinmetrics

        mvrv_value = glassnode.get_mvrv_z_score(symbol) if glassnode else None
        mvrv_approx = False
        if mvrv_value is None:
            mvrv_value = self._approximate_mvrv_z_score(market_data)
            mvrv_approx = mvrv_value is not None

        if mvrv_value is not None:
            output.metrics.append(
                MetricSnapshot(
                    name="mvrv_z_score",
                    pillar=Pillar.ON_CHAIN,
                    value=mvrv_value,
                    metadata={
                        "market_cap": (market_data.get("market_cap") or {}).get("usd"),
                        "realized_cap": market_data.get("realized_market_cap"),
                        "approximation": mvrv_approx,
                    },
                )
            )
        else:
            output.warnings.append("MVRV Z-Score unavailable (Glassnode metrics required).")

        nvt_source = None
        nvt_value = coinmetrics.get_nvt_signal(symbol) if coinmetrics else None
        nvt_approx = False
        if nvt_value is not None:
            nvt_source = "coinmetrics"
        else:
            nvt_value = self._compute_nvt_ratio(market_data)
            nvt_approx = nvt_value is not None
            if nvt_approx:
                nvt_source = "coingecko"

        if nvt_value is not None:
            metadata = {
                "market_cap": (market_data.get("market_cap") or {}).get("usd"),
                "total_volume": (market_data.get("total_volume") or {}).get("usd"),
            }
            if nvt_source:
                metadata["source"] = nvt_source
            if nvt_approx:
                metadata["approximation"] = True
            output.metrics.append(
                MetricSnapshot(
                    name="nvt_ratio",
                    pillar=Pillar.ON_CHAIN,
                    value=nvt_value,
                    metadata=metadata,
                )
            )
        else:
            output.warnings.append("NVT ratio unavailable (CoinMetrics metrics required).")

        hot_money = glassnode.get_hot_money_ratio(symbol) if glassnode else None
        if hot_money is not None:
            output.metrics.append(
                MetricSnapshot(
                    name="hodl_waves_hot_money",
                    pillar=Pillar.ON_CHAIN,
                    value=hot_money,
                    metadata={
                        "notes": "Glassnode HODL Waves",
                    },
                )
            )
        else:
            output.warnings.append("HODL Waves (hot money share) unavailable – Glassnode advanced API required.")

        whale_stress = glassnode.get_whale_realized_stress(symbol) if glassnode else None
        whale_approx = False
        if whale_stress is None:
            whale_stress = self._estimate_whale_realized_cap_stress(market_data)
            whale_approx = whale_stress is not None

        if whale_stress is not None:
            output.metrics.append(
                MetricSnapshot(
                    name="whale_realized_cap_stress",
                    pillar=Pillar.ON_CHAIN,
                    value=whale_stress,
                    metadata={
                        "volume_24h": (market_data.get("total_volume") or {}).get("usd"),
                        "circulating_supply": market_data.get("circulating_supply"),
                        "approximation": whale_approx,
                    },
                )
            )
        else:
            output.warnings.append("Whale realized-cap stress unavailable – Glassnode data missing.")

        if not output.metrics:
            output.warnings.append(
                "Unable to derive on-chain heuristics from CoinGecko payload; consider configuring advanced providers."
            )

        return output

    @staticmethod
    def _approximate_mvrv_z_score(market_data: Dict[str, Any]) -> Optional[float]:
        """
        Approximation fallback using market_cap / realized_cap.

        This is not a true Z-Score but offers a heuristic when Glassnode data is unavailable.
        """
        market_cap = OnChainCollector._safe_float((market_data.get("market_cap") or {}).get("usd"))
        realized_cap = OnChainCollector._safe_float(market_data.get("realized_market_cap"))
        if market_cap is None or realized_cap is None or realized_cap <= 0:
            return None
        return market_cap / realized_cap

    @staticmethod
    def _compute_nvt_ratio(market_data: Dict[str, Any]) -> Optional[float]:
        market_cap = OnChainCollector._safe_float((market_data.get("market_cap") or {}).get("usd"))
        tx_volume = OnChainCollector._safe_float((market_data.get("total_volume") or {}).get("usd"))
        if market_cap is None or tx_volume is None or tx_volume <= 0:
            return None
        return market_cap / tx_volume

    @staticmethod
    def _estimate_whale_realized_cap_stress(market_data: Dict[str, Any]) -> Optional[float]:
        volume = OnChainCollector._safe_float((market_data.get("total_volume") or {}).get("usd"))
        supply = OnChainCollector._safe_float(market_data.get("circulating_supply"))
        price = OnChainCollector._safe_float((market_data.get("current_price") or {}).get("usd"))
        if volume is None or supply is None or price is None or supply <= 0:
            return None
        realized_value = supply * price
        if realized_value <= 0:
            return None
        return volume / realized_value

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        if value in (None, "", "null"):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

