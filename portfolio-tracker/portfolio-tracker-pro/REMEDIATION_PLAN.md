# Remediation Priorities & Follow-Up Actions

## 1. Data Integrity & Valuation
- **Normalize exchange valuations** *(done)*: fallback to reference pricing when exchange quotes deviate >15 % or are missing.
- **Next:** unify FIFO adjustments for manual/API trades; build validation to flag negative balances and stale timestamps.

## 2. API Resilience
- Layer retry/backoff per provider with provider-specific cooldown surfacing.
- Standardize error payloads so the UI can display precise failure states.
- Externalize rate-limit budgets for Polygon/Finnhub/Alpha Vantage.

## 3. Frontend Data Flow
- Introduce shared loading/error boundaries across dashboard/portfolio/watchlist.
- Remove legacy direct fetch calls; route everything through `portfolioService`.
- Debounce filter/controls interactions to avoid excessive network calls.

3. Implement Backend Integrity Checks

- Add validation layer in `backend/main.py` (portfolio and summary endpoints) that flags negative holdings, zero-priced assets, or prices deviating >15% vs reference (reuse new normalization metadata)
- Propagate warnings in API responses for frontend display/logging
- Implemented `_build_assets_with_validation` helper which annotates each asset with `issues`, reports aggregated warnings through `PortfolioSummary.warnings`, and logs anomalies server-side.

4. Automate Verification Script Reporting

- Extend `backend/scripts/verify_portfolio.py` to produce machine-readable diff output (JSON/CSV) and exit codes
- Add scheduler-friendly wrapper (e.g., new script or CLI option) plus documentation update (`MORNING_SYNC_SETUP.md`) for daily runs
- Added `--json-output`, `--csv-output`, and `--quiet` flags to the verification CLI so scheduled jobs can persist results and alert on discrepancies.

## 4. Manual Entry Enhancements
- Reuse the new autocomplete in edit dialogs and quick-add flows.
- Validate CSV import pipeline using the same name/ISIN resolver before persisting updates.

## 5. Verification & Monitoring
- Convert manual verification script to a scheduled run (reuses morning sync infra) with diff reports.
- Surface sync metadata (last success, misaligned assets) in the Global Status Bar.

## 6. UX & Feedback
- Add skeleton loaders / empty states for watchlist & ROI modules.
- Replace remaining `window.alert/confirm` usages with coordinated dialogs/snackbars.

## 7. Testing Debt
- Extend API tests for `/api/transactions` (name/ISIN flows, validation failures).
- Add smoke E2E coverage (dashboard load, manual transaction add, filter toggles) with mocked APIs.

> These items are ordered by impact; proceed top-down unless a user request dictates otherwise. Update this plan as items move to “done” or as new gaps are identified. 

