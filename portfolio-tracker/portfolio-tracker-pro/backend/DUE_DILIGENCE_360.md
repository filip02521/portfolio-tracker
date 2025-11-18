# Due Diligence 360° Methodology

The legacy short-term Confluence Strategy has been replaced by a long-horizon **Due Diligence 360°** framework that evaluates digital assets across four strategic pillars:

| Pillar        | Weight | Focus                                                             | Example Metrics                                                                           |
| ------------- | ------ | ----------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| On-Chain      | 45%    | Network health, capital rotation, and whale behaviour            | MVRV ratio, NVT ratio, hot money share, realized-cap stress                              |
| Fundamental   | 35%    | Supply mechanics, protocol traction, and development resilience  | Deflationary pressure, staking ratio, TVL/MC, protocol revenue, commits & contributors   |
| Technical     | 10%    | Long-horizon price structure and regime                         | Daily MA200 trend, weekly MA trend alignment, macro RSI                                  |
| Sentiment     | 10%    | Derivatives stress & community momentum                         | Crowd sentiment ratio, funding rate proxy, macro contagion proxy, community growth       |

## Data Architecture

- **Collectors** live in `due_diligence/collectors/` and encapsulate pillar-specific acquisition and heuristics. CoinGecko is the default free provider; adapters can be swapped via the `CollectorContext`.
- **Scoring Engine** (`due_diligence_service.DueDiligenceService`) orchestrates collection → normalisation → weighted aggregation and exposes a cached `evaluate(symbol)` API.
- **Shared Contracts** (`due_diligence/models.py`) define reusable Pydantic models (`DueDiligenceResult`, `PillarScore`, `MetricSnapshot`) for backend and frontend consumers.
- **Configuration** is centralised in `due_diligence/config.py` with optional environment overrides:
  - `DD360_PILLAR_WEIGHTS` e.g. `on_chain=0.5,fundamental=0.3`
  - `DD360_METRIC_WEIGHTS` e.g. `deflationary_pressure=1.2`

## API Surface

- `GET /api/analysis/due-diligence/{symbol}?refresh=false`
  - Returns `{ symbol, result }` where `result` is a serialized `DueDiligenceResult`.
  - `refresh=true` bypasses caching for on-demand recalculation.
- Legacy `/api/strategy/confluence/*` endpoints now return deprecation messages with embedded Due Diligence payloads.

## Implementation Notes

- Metric definitions and checklist weights from the expert report live in `due_diligence/metric_config.py`. Every metric
  is scored on a 0/1/2 scale and re-normalised so the overall score remains bounded in `[0, 100]`.
- Pillar scores now expose `missing_metrics` to highlight which premium feeds (Glassnode, TokenTerminal, Coinglass,
  Santiment, etc.) are required for a complete evaluation. Without API keys the placeholders fall back to simplified
  heuristics or mark the metric as unavailable.
- CoinMetrics Community API is queried for NVT ratios (90-day average of `CapMrktCurUSD / volume_reported_spot_usd_1d`).
  Supplying `COINMETRICS_API_KEY` unlocks higher rate limits; if the API request fails we fall back to CoinGecko heuristics.
- `DueDiligenceService` rebalances weights dynamically based on the metrics that were actually scored, so temporary data
  gaps do not distort the final result.

## Frontend Integration

- `portfolioService.getDueDiligence(symbol)` memoizes API results for one hour.
- Asset details drawer renders the pillar breakdown and confidence, including refresh controls and alerts for low scores.
- AI recommendations include the Due Diligence snapshot which influences composite scoring and surfacing (strengths/concerns badges).

## Extending the Framework

1. **Add new metrics:** Implement a collector in `due_diligence/collectors/` and return enriched `MetricSnapshot`s.
2. **Adjust thresholds:** Update `score_metric` logic in `due_diligence/metric_config.py` or extend the metric metadata.
3. **Swap data providers:** Create adapters in `due_diligence/data_providers/` and wire them into `CollectorContext`.
4. **Consumer features:** The shared models allow other services (alerts, dashboards, AI) to subscribe without reimplementing logic.

## Migration Notes

- `ConfluenceStrategyService` is now a thin compatibility layer that forwards callers to Due Diligence 360° and emits deprecation warnings.
- Short-term technical triggers (EMA pullbacks, pin bars) remain available in AI backtests but are no longer the primary evaluation engine.
- Backtested composite scoring now blends technical signals with Due Diligence scores to reflect long-term conviction.


