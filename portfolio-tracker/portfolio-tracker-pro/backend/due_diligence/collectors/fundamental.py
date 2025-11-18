from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from ..data_providers.github import GitHubClient

from ..config import Pillar
from ..models import MetricSnapshot
from .base import CollectorContext, CollectorOutput, MetricCollector


class FundamentalCollector(MetricCollector):
    name = "fundamental"

    def collect(self, symbol: str, context: CollectorContext) -> CollectorOutput:
        output = CollectorOutput()
        payload = context.coingecko.get_asset_details(symbol)

        if not payload:
            output.warnings.append(
                "CoinGecko fundamental data unavailable; fundamental pillar will be low confidence."
            )
            return output

        market_data: Dict[str, Any] = payload.get("market_data") or {}
        developer_data: Dict[str, Any] = dict(payload.get("developer_data") or {})
        token_terminal = context.token_terminal
        santiment = context.santiment
        defillama = context.defillama
        github_client = context.github

        deflationary_pressure = self._compute_deflationary_pressure(market_data)
        if deflationary_pressure is not None:
            output.metrics.append(
                MetricSnapshot(
                    name="deflationary_pressure_net",
                    pillar=Pillar.FUNDAMENTAL,
                    value=deflationary_pressure,
                    metadata={
                        "circulating_supply": market_data.get("circulating_supply"),
                        "max_supply": market_data.get("max_supply"),
                        "approximation": True,
                    },
                )
            )

        staking_ratio = self._compute_staking_ratio(market_data)
        if staking_ratio is not None:
            output.metrics.append(
                MetricSnapshot(
                    name="staking_ratio",
                    pillar=Pillar.FUNDAMENTAL,
                    value=staking_ratio,
                    metadata={
                        "total_supply": market_data.get("total_supply"),
                        "circulating_supply": market_data.get("circulating_supply"),
                    },
                )
            )

        tvl_value = None
        tvl_metadata: Dict[str, Any] = {}
        slug = self._resolve_defillama_slug(symbol, payload)
        if defillama and slug:
            tvl_value = defillama.get_protocol_tvl(slug)
            if tvl_value is not None:
                tvl_metadata = {"source": "defillama", "slug": slug}

        if tvl_value is None and token_terminal:
            tvl_value = token_terminal.get_tvl(symbol)
            if tvl_value is not None:
                tvl_metadata = {"source": "tokenterminal"}

        if tvl_value is None:
            tvl_value = self._safe_float(market_data.get("total_value_locked"))
            if tvl_value is not None:
                tvl_metadata = {"source": "coingecko", "approximation": True}

        tvl_ratio = self._compute_tvl_ratio(tvl_value, market_data)
        if tvl_ratio is not None:
            output.metrics.append(
                MetricSnapshot(
                    name="tvl_market_cap_ratio",
                    pillar=Pillar.FUNDAMENTAL,
                    value=tvl_ratio,
                    metadata={
                        "tvl": tvl_value,
                        "market_cap": (market_data.get("market_cap") or {}).get("usd"),
                        **tvl_metadata,
                    },
                )
            )
        else:
            output.warnings.append("TVL / Market Cap ratio unavailable (TokenTerminal recommended).")

        protocol_revenue = token_terminal.get_revenue(symbol) if token_terminal else None
        revenue_metadata = {"source": "tokenterminal"} if protocol_revenue is not None else {}
        if protocol_revenue is None:
            protocol_revenue = self._extract_protocol_revenue(payload)
            if protocol_revenue is not None:
                revenue_metadata = {"source": "coingecko.market_data.protocol_revenue_24h", "approximation": True}

        if protocol_revenue is not None:
            output.metrics.append(
                MetricSnapshot(
                    name="protocol_revenue_trend",
                    pillar=Pillar.FUNDAMENTAL,
                    value=protocol_revenue,
                    metadata=revenue_metadata,
                )
            )
        else:
            output.warnings.append("Protocol revenue data unavailable – configure TokenTerminal API.")

        santiment_commits = santiment.get_development_activity(symbol) if santiment else None
        commits = santiment_commits
        contributors_from_santiment = santiment.get_contributor_count(symbol) if santiment else None

        if commits is None and github_client:
            owner, repo = self._extract_primary_repo(payload)
            if owner and repo:
                commits = github_client.get_recent_commit_count(owner, repo, days=30)
                if commits is not None:
                    developer_data["github_repo"] = f"{owner}/{repo}"
        if commits is None:
            commits = developer_data.get("commit_count_4_weeks")

        if commits is not None:
            output.metrics.append(
                MetricSnapshot(
                    name="development_activity_score",
                    pillar=Pillar.FUNDAMENTAL,
                    value=float(commits),
                    metadata={
                        "period": "4_weeks",
                        "source": (
                            "santiment"
                            if santiment_commits is not None and commits == santiment_commits
                            else "github"
                            if developer_data.get("github_repo")
                            else "coingecko"
                        ),
                        "repo": developer_data.get("github_repo"),
                    },
                )
            )

        contributors_data = dict(developer_data.get("developers") or {})
        total_devs = (
            contributors_from_santiment if contributors_from_santiment is not None else contributors_data.get("count")
        )
        if total_devs is None and github_client:
            owner, repo = self._extract_primary_repo(payload)
            if owner and repo:
                total_devs = github_client.get_contributor_count(owner, repo)
                if total_devs is not None:
                    contributors_data.setdefault("source", "github")

        if total_devs is not None:
            output.metrics.append(
                MetricSnapshot(
                    name="developer_contributor_count",
                    pillar=Pillar.FUNDAMENTAL,
                    value=float(total_devs),
                    metadata={
                        "pull_request_contributors": contributors_data.get("pull_request_contributors"),
                        "stars": developer_data.get("stars"),
                        "source": contributors_data.get("source", "coingecko" if contributors_data else "github"),
                    },
                )
            )

        if not output.metrics:
            output.warnings.append(
                "Fundamental metrics missing from CoinGecko payload; pillar score will rely on fallbacks."
            )

        return output

    @staticmethod
    def _compute_deflationary_pressure(market_data: Dict[str, Any]) -> Optional[float]:
        circulating = FundamentalCollector._safe_float(market_data.get("circulating_supply"))
        max_supply = FundamentalCollector._safe_float(market_data.get("max_supply"))
        if circulating is None or max_supply is None or max_supply <= 0:
            return None
        pressure = 1.0 - (circulating / max_supply)
        return max(min(pressure, 1.0), -1.0)

    @staticmethod
    def _compute_staking_ratio(market_data: Dict[str, Any]) -> Optional[float]:
        total_supply = FundamentalCollector._safe_float(market_data.get("total_supply"))
        circulating = FundamentalCollector._safe_float(market_data.get("circulating_supply"))
        if total_supply is None or total_supply <= 0 or circulating is None:
            return None
        if circulating > total_supply:
            return None
        locked = total_supply - circulating
        return max(min(locked / total_supply, 1.0), 0.0)

    @staticmethod
    def _compute_tvl_ratio(tvl: Optional[float], market_data: Dict[str, Any]) -> Optional[float]:
        market_cap_usd = FundamentalCollector._safe_float((market_data.get("market_cap") or {}).get("usd"))
        if tvl is None or tvl <= 0 or market_cap_usd is None or market_cap_usd <= 0:
            return None
        return tvl / market_cap_usd

    @staticmethod
    def _extract_protocol_revenue(payload: Dict[str, Any]) -> Optional[float]:
        market_data = payload.get("market_data") or {}
        revenue = market_data.get("protocol_revenue_24h")
        if revenue is None:
            return None
        try:
            return float(revenue)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _resolve_defillama_slug(symbol: str, payload: Dict[str, Any]) -> Optional[str]:
        mapping = {
            "ETH": "ethereum",
            "MATIC": "polygon-pos",
            "POL": "polygon-pos",
            "AVAX": "avalanche",
            "SOL": "solana",
            "ADA": "cardano",
            "BNB": "binance-smart-chain",
        }
        symbol_upper = (symbol or "").upper()
        if symbol_upper in mapping:
            return mapping[symbol_upper]

        coin_id = (payload.get("id") or "").lower().replace(" ", "-")
        return coin_id or None

    @staticmethod
    def _extract_primary_repo(payload: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        links = payload.get("links") or {}
        repos = (links.get("repos_url") or {}).get("github") or []
        if not repos and isinstance(links.get("github"), list):
            repos = links.get("github")
        for url in repos:
            owner, repo = GitHubClient.extract_owner_repo(url)
            if owner and repo:
                return owner, repo
        return None, None

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        if value in (None, "", "null"):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

