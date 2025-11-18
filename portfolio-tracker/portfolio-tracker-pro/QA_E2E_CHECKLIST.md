# E2E regression (backend stabilized)

1. Dashboard manual smoke test
   - Start backend + frontend
   - Log in as standard user
   - Hit manual refresh in global status bar
   - Trigger trade sync (expect toast + warning banner)
   - Toggle filters and ensure persisted state

2. Transactions workflow
   - Add manual stock trade (use ISIN lookup)
   - Verify new trade badge + data warning
   - Confirm table sorting, detail dialog alerts

3. API sanity via CLI
   - Run `python -m scripts.check_new_trades --username <test>`
   - Run `python -m scripts.verify_portfolio --username <test>`
   - Check `logs/morning-sync.log` for errors

4. Cross-browser spot check
   - Chrome (primary)
   - Safari or Firefox (tooltip + sticky column)

5. Post-test validation
   - `npm run build` (frontend)
   - `python3 -m pytest` (backend)
   - Capture summary for release notes
