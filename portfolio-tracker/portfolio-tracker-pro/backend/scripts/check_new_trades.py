"""
CLI helper to check for new trades on configured exchanges.

Usage:
    python -m scripts.check_new_trades --username <user>
    python -m scripts.check_new_trades --all
"""
import argparse
from typing import List

from exchange_sync import detect_new_trades
from portfolio_tracker import PortfolioTracker
from settings_manager import SettingsManager
from transaction_history import TransactionHistory


def check_user(username: str) -> None:
    settings_manager = SettingsManager()
    tracker = PortfolioTracker(settings_manager)
    history = TransactionHistory()

    result = detect_new_trades(tracker, history, username, limit=200)
    summary = result.get("summary", {})
    details = result.get("details", {})

    print(f"\n=== New trade check for user: {username} ===")
    print(f"Checked exchanges: {', '.join(summary.get('checked_exchanges', [])) or 'none'}")
    print(f"New trades detected: {summary.get('new_trades', 0)}")

    for exchange, data in details.items():
        new_trades = data.get("new", [])
        print(f" - {exchange}: fetched={data.get('fetched', 0)}, new={len(new_trades)}")
        for trade in new_trades:
            print(
                f"     • {trade.get('timestamp')} {trade.get('side').upper()} "
                f"{trade.get('amount'):.6f} {trade.get('asset')} @ {trade.get('price'):.4f} "
                f"(pair {trade.get('symbol')})"
            )


def main():
    parser = argparse.ArgumentParser(
        description="Check exchanges for trades not present in local transaction history."
    )
    parser.add_argument("--username", help="Username to check")
    parser.add_argument("--all", action="store_true", help="Check all users with stored credentials")

    args = parser.parse_args()
    settings_manager = SettingsManager()

    users: List[str]
    if args.all:
        users = settings_manager.list_users()
        if not users:
            print("No users with stored credentials found.")
            return
    elif args.username:
        users = [args.username]
    else:
        parser.error("Specify --username <user> or use --all")

    for user in users:
        check_user(user)


if __name__ == "__main__":
    main()

