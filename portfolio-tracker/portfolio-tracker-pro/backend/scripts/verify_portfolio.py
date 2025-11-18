"""
Portfolio verification utility to compare exchange holdings with local transaction history.

Examples:
    python -m scripts.verify_portfolio --username <user>
    python -m scripts.verify_portfolio --all --json-output /tmp/verify.json --csv-output /tmp/verify.csv --quiet
"""

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List

from settings_manager import SettingsManager
from portfolio_tracker import PortfolioTracker
from transaction_history import TransactionHistory

TOLERANCE = 1e-6


def compute_net_position(transactions: List[Dict]) -> float:
    """Compute net position (buys - sells) for a given asset."""
    net = 0.0
    for tx in transactions:
        amount = tx.get("amount", 0.0) or 0.0
        if tx.get("type") == "buy":
            net += amount
        elif tx.get("type") == "sell":
            net -= amount
    return net


def verify_user(username: str, *, quiet: bool = False) -> Dict[str, Any]:
    """Verify a single user's holdings against exchange data and return structured results."""
    settings_manager = SettingsManager()
    tracker = PortfolioTracker(settings_manager)
    history = TransactionHistory()

    credentials = settings_manager.get_user_api_credentials(username)
    if not credentials:
        if not quiet:
            print(f"[{username}] No exchange credentials configured – skipping.")
        return {
            "username": username,
            "checked_assets": 0,
            "discrepancy_count": 0,
            "discrepancies": [],
            "skipped": True,
            "reason": "missing_credentials",
        }

    if not quiet:
        print(f"\n=== Verifying portfolio for user: {username} ===")
    portfolios = tracker.get_all_portfolios(username)

    discrepancy_rows: List[Dict[str, Any]] = []
    checked_assets = 0

    for portfolio in portfolios:
        exchange = portfolio.get("exchange", "Unknown")
        balances = portfolio.get("balances", [])

        if not balances:
            if not quiet:
                print(f" - {exchange}: no balances reported.")
            continue

        if not quiet:
            print(f" - {exchange}: {len(balances)} assets")
        for balance in balances:
            asset_symbol = balance.get("asset", "")
            amount_exchange = balance.get("total", 0.0) or 0.0
            value_exchange = balance.get("value_usdt", 0.0) or 0.0

            transactions = history.get_transactions_for_asset(exchange, asset_symbol)
            net_position = compute_net_position(transactions)

            checked_assets += 1
            if math.isclose(amount_exchange, net_position, abs_tol=TOLERANCE):
                continue

            delta = amount_exchange - net_position
            discrepancy_rows.append(
                {
                    "username": username,
                    "exchange": exchange,
                    "asset": asset_symbol,
                    "exchange_amount": amount_exchange,
                    "history_amount": net_position,
                    "delta": delta,
                    "value_usdt": value_exchange,
                }
            )
            if not quiet:
                print(
                    f"   • {asset_symbol}: exchange={amount_exchange:.8f}, "
                    f"history={net_position:.8f}, delta={delta:.8f} (value≈{value_exchange:.2f} USDT)"
                )

    if not quiet:
        if discrepancy_rows:
            print(
                f"[{username}] ⚠ Detected {len(discrepancy_rows)} discrepancy(ies) across {checked_assets} assets."
            )
        else:
            print(f"[{username}] ✅ No discrepancies detected across {checked_assets} assets.")

    return {
        "username": username,
        "checked_assets": checked_assets,
        "discrepancy_count": len(discrepancy_rows),
        "discrepancies": discrepancy_rows,
        "skipped": False,
    }


def write_json_summary(path: str, payload: Dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


def write_csv_rows(path: str, rows: List[Dict[str, Any]]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "username",
        "exchange",
        "asset",
        "exchange_amount",
        "history_amount",
        "delta",
        "value_usdt",
    ]
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify exchange holdings against transaction history."
    )
    parser.add_argument("--username", help="Username to verify")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Verify every user that has stored credentials",
    )
    parser.add_argument("--json-output", help="Write machine-readable summary JSON to the given path")
    parser.add_argument("--csv-output", help="Write detailed discrepancies as CSV to the given path")
    parser.add_argument("--quiet", action="store_true", help="Suppress human-readable output")

    args = parser.parse_args()
    settings_manager = SettingsManager()

    if args.all:
        users = settings_manager.list_users()
        if not users:
            if not args.quiet:
                print("No users with stored credentials found.")
            sys.exit(0)
    elif args.username:
        users = [args.username]
    else:
        parser.error("Specify --username <user> or use --all")

    summary_records: List[Dict[str, Any]] = []
    discrepancy_rows: List[Dict[str, Any]] = []
    total_assets = 0
    total_discrepancies = 0

    for user in users:
        result = verify_user(user, quiet=args.quiet)
        summary_records.append(result)
        total_assets += result.get("checked_assets", 0)
        discrepancy_count = result.get("discrepancy_count", 0)
        total_discrepancies += discrepancy_count
        discrepancy_rows.extend(result.get("discrepancies", []))

    summary_payload = {
        "checked_assets": total_assets,
        "discrepancies": total_discrepancies,
        "users": summary_records,
    }

    if args.json_output:
        write_json_summary(args.json_output, summary_payload)
    if args.csv_output and discrepancy_rows:
        write_csv_rows(args.csv_output, discrepancy_rows)
    elif args.csv_output and not args.quiet:
        print("No discrepancies detected; CSV output skipped.")

    if not args.quiet:
        print(
            f"\nVerification completed. Assets checked: {total_assets}, "
            f"discrepancies found: {total_discrepancies}."
        )

    sys.exit(1 if total_discrepancies > 0 else 0)


if __name__ == "__main__":
    main()

