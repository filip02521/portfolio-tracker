"""
Watchlist Service - per-user watchlist persistence and validation
"""
import os
import json
import re
from typing import List, Dict
from threading import RLock


class WatchlistService:
    def __init__(self, storage_file: str = "watchlist.json"):
        self.storage_file = storage_file
        self._lock = RLock()
        # Create file if missing
        if not os.path.exists(self.storage_file):
            with open(self.storage_file, 'w') as f:
                json.dump({}, f)

    def _load(self) -> Dict[str, List[str]]:
        with self._lock:
            try:
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    return {}
                return data
            except Exception:
                return {}

    def _save(self, data: Dict[str, List[str]]) -> None:
        with self._lock:
            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=2)

    def normalize_symbol(self, symbol: str) -> str:
        return (symbol or '').strip().upper()

    def validate_symbol(self, symbol: str) -> bool:
        # Accept common ticker characters: letters, digits, dot, dash
        return bool(re.match(r'^[A-Z0-9.-]{1,15}$', symbol))

    def get_watchlist(self, username: str) -> List[str]:
        username = username or 'default'
        data = self._load()
        return list(dict.fromkeys([self.normalize_symbol(s) for s in data.get(username, [])]))

    def add_symbol(self, username: str, symbol: str, max_symbols: int = 50) -> List[str]:
        username = username or 'default'
        norm = self.normalize_symbol(symbol)
        if not self.validate_symbol(norm):
            raise ValueError("Invalid symbol format")
        data = self._load()
        current = data.get(username, [])
        # dedup
        if norm not in current:
            if len(current) >= max_symbols:
                raise ValueError("Watchlist limit reached")
            current.append(norm)
        data[username] = current
        self._save(data)
        return current

    def remove_symbol(self, username: str, symbol: str) -> List[str]:
        username = username or 'default'
        norm = self.normalize_symbol(symbol)
        data = self._load()
        current = data.get(username, [])
        current = [s for s in current if s != norm]
        data[username] = current
        self._save(data)
        return current



