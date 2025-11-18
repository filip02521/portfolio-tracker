# Morning Exchange Sync Setup

We now support per-user exchange credentials and automatic discovery of new trades.
Use the following options to run the morning check at 06:00 without having the main
FastAPI server running.

## 1. CLI Utility

Two helper scripts live under `portfolio-tracker-pro/backend/scripts`:

| Script | Purpose |
| --- | --- |
| `python -m scripts.check_new_trades --username <user>` | Checks exchanges for trades that are not in local history. |
| `python -m scripts.verify_portfolio --username <user>` | Compares exchange balances with recorded holdings. |

Run with `--all` to process every user that has stored credentials:

```bash
cd portfolio-tracker-pro/backend
python -m scripts.check_new_trades --all
```

## 2. Cron Example (macOS / Linux)

Schedule the sync at 06:00 local time by editing the crontab:

```bash
crontab -e
```

Add:

```
0 6 * * * cd /Users/Filip/portfolio-tracker/portfolio-tracker-pro/backend && /usr/bin/env python -m scripts.check_new_trades --all >> /Users/Filip/portfolio-tracker/logs/morning-sync.log 2>&1
```

Adjust paths if the project is elsewhere. The command runs the CLI tool without needing
the FastAPI app online.

## 3. Windows Task Scheduler

Create a new basic task that runs daily at 06:00, executing:

```
python -m scripts.check_new_trades --all
```

Set the working directory to `portfolio-tracker-pro\backend`.

## 4. Scheduled Verification Report

If you also want a daily reconciliation report, schedule `verify_portfolio` with the
new output flags. Example cron entry that writes both JSON and CSV artifacts and
only logs on discrepancy:

```
5 6 * * * cd /Users/Filip/portfolio-tracker/portfolio-tracker-pro/backend && /usr/bin/env python -m scripts.verify_portfolio --all --json-output /Users/Filip/portfolio-tracker/logs/verification-summary.json --csv-output /Users/Filip/portfolio-tracker/logs/verification-details.csv --quiet >> /Users/Filip/portfolio-tracker/logs/verification.log 2>&1
```

The command exits with status `1` if any discrepancies are detected, which allows
cron, systemd, or monitoring tools to alert on failures.

## 5. Serverless/Webhook Option

We also expose an API endpoint if you prefer invoking from a hosted scheduler:

```