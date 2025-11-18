"""
Utilities for synchronizing and verifying exchange transactions.
"""
from datetime import datetime, timezone
from typing import Dict, Optional, Any, List

from portfolio_tracker import PortfolioTracker
from transaction_history import TransactionHistory


def _normalize_trade(exchange: str, trade: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Normalize exchange-specific trade payloads for comparison."""
    exchange_lower = exchange.lower()

    if exchange_lower == "binance":
        symbol = trade.get("symbol", "")
        amount = float(trade.get("qty", 0) or 0)
        price = float(trade.get("price", 0) or 0)
        timestamp_ms = trade.get("time")
        side = "buy" if trade.get("isBuyer") else "sell"
        quote = ""
        base = symbol
        for candidate in ["USDT", "BUSD", "USDC", "BTC", "ETH"]:
            if symbol.endswith(candidate):
                base = symbol[:-len(candidate)]
                quote = candidate
                break
        if not timestamp_ms:
            timestamp = datetime.utcnow().isoformat() + "Z"
        else:
            timestamp = datetime.fromtimestamp(int(timestamp_ms) / 1000, tz=timezone.utc).isoformat()
        return {
            "exchange": exchange,
            "symbol": symbol,
            "asset": base,
            "quote": quote,
            "amount": amount,
            "price": price,
            "side": side,
            "timestamp": timestamp,
            "raw": trade,
        }

    if exchange_lower == "bybit":
        symbol = trade.get("symbol", "")
        amount = float(trade.get("execQty", 0) or 0)
        price = float(trade.get("execPrice", 0) or 0)
        side = trade.get("side", "").lower()
        timestamp_ms = trade.get("execTime")
        if not timestamp_ms:
            timestamp = datetime.utcnow().isoformat() + "Z"
        else:
            timestamp = datetime.fromtimestamp(int(timestamp_ms) / 1000, tz=timezone.utc).isoformat()
        base = symbol
        quote = ""
        for candidate in ["USDT", "USDC", "BTC", "ETH"]:
            if symbol.endswith(candidate):
                base = symbol[:-len(candidate)]
                quote = candidate
                break
        return {
            "exchange": exchange,
            "symbol": symbol,
            "asset": base,
            "quote": quote,
            "amount": amount,
            "price": price,
            "side": side,
            "timestamp": timestamp,
            "raw": trade,
        }

    return None


def detect_new_trades(
    tracker: PortfolioTracker,
    history: TransactionHistory,
    username: str,
    limit: int = 50,
) -> Dict[str, Any]:
    """Fetch recent trades and detect those not present in transaction history."""
    clients = tracker.get_exchange_clients(username)
    transactions = history.get_all_transactions(user_id=username)

    existing_keys = set()
    for t in transactions:
        try:
            key = history.build_transaction_key(
                t.get("exchange", ""),
                t.get("asset", ""),
                t.get("type", ""),
                t.get("amount", 0.0),
                t.get("price_usd", 0.0),
                t.get("date", ""),
            )
            existing_keys.add(key)
        except Exception:
            continue

    summary = {"checked_exchanges": [], "new_trades": 0}
    details: Dict[str, Dict[str, Any]] = {}

    for exchange_name, client in clients.items():
        summary["checked_exchanges"].append(exchange_name)
        if not hasattr(client, "get_trade_history"):
            details[exchange_name] = {"fetched": 0, "new": []}
            continue

        try:
            raw_trades = client.get_trade_history(limit=limit)
        except Exception as exc:
            details[exchange_name] = {
                "fetched": 0,
                "new": [],
                "error": str(exc),
            }
            continue

        normalized_new = []
        normalized_count = 0

        for trade in raw_trades or []:
            normalized = _normalize_trade(exchange_name, trade)
            if not normalized:
                continue
            normalized_count += 1
            try:
                key = history.build_transaction_key(
                    exchange_name,
                    normalized["asset"],
                    normalized["side"],
                    normalized["amount"],
                    normalized["price"],
                    normalized["timestamp"],
                )
            except ValueError:
                continue

            if key not in existing_keys:
                normalized_new.append(normalized)

        summary["new_trades"] += len(normalized_new)
        details[exchange_name] = {
            "fetched": normalized_count,
            "new": normalized_new,
        }

    return {"summary": summary, "details": details}


def import_new_trades(
    tracker: PortfolioTracker,
    history: TransactionHistory,
    username: str,
    limit: int = 50,
) -> Dict[str, Any]:
    """Detect new trades and automatically import them into transaction history."""
    result = detect_new_trades(tracker, history, username, limit=limit)
    
    imported_count = 0
    imported_by_exchange: Dict[str, int] = {}
    errors: List[Dict[str, str]] = []
    
    for exchange_name, exchange_details in result.get("details", {}).items():
        new_trades = exchange_details.get("new", [])
        exchange_imported = 0
        
        for trade in new_trades:
            try:
                # Convert normalized trade to transaction format
                asset = trade.get("asset", "")
                side = trade.get("side", "").lower()
                amount = trade.get("amount", 0.0)
                price = trade.get("price", 0.0)
                timestamp = trade.get("timestamp", "")
                
                # Map side to transaction type
                transaction_type = "buy" if side == "buy" else "sell"
                
                # Add transaction to history
                history.add_transaction(
                    exchange=exchange_name,
                    asset=asset,
                    amount=amount,
                    price_usd=price,
                    transaction_type=transaction_type,
                    date=timestamp,
                    commission=0.0,  # Commission not available from normalized trade
                    commission_currency="USD",
                    user_id=username
                )
                
                exchange_imported += 1
                imported_count += 1
            except Exception as e:
                errors.append({
                    "exchange": exchange_name,
                    "trade": str(trade.get("symbol", "")),
                    "error": str(e)
                })
        
        if exchange_imported > 0:
            imported_by_exchange[exchange_name] = exchange_imported
    
    return {
        "summary": {
            "checked_exchanges": result.get("summary", {}).get("checked_exchanges", []),
            "new_trades_detected": result.get("summary", {}).get("new_trades", 0),
            "imported_count": imported_count,
            "imported_by_exchange": imported_by_exchange,
            "errors": errors
        },
        "details": result.get("details", {})
    }

