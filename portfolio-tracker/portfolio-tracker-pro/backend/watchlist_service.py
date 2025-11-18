"""
Watchlist Service - per-user watchlist persistence and validation
Now uses SQLite database instead of JSON file
"""
import json
import re
from typing import List, Dict, Optional, Any
from database import get_db


class WatchlistService:
    def __init__(self, storage_file: str = "watchlist.json"):
        # Keep storage_file for backward compatibility, but use database
        self.storage_file = storage_file

    def normalize_symbol(self, symbol: str) -> str:
        return (symbol or '').strip().upper()

    def validate_symbol(self, symbol: str) -> bool:
        # Accept common ticker characters: letters, digits, dot, dash
        return bool(re.match(r'^[A-Z0-9.-]{1,15}$', symbol))

    def get_watchlist(self, username: str) -> List[str]:
        """Get list of symbols for a user (backward compatibility)"""
        username = username or 'default'
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT symbol FROM watchlist WHERE user_id = ? ORDER BY created_at', (username,))
            rows = cursor.fetchall()
            return [self.normalize_symbol(row['symbol']) for row in rows]

    def get_watchlist_with_metadata(self, username: str) -> Dict[str, Any]:
        """Get watchlist with metadata (categories, tags)"""
        username = username or 'default'
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT symbol, categories, tags FROM watchlist WHERE user_id = ? ORDER BY created_at', (username,))
            rows = cursor.fetchall()
            
            symbols = []
            metadata = {}
            for row in rows:
                symbol = self.normalize_symbol(row['symbol'])
                symbols.append(symbol)
                try:
                    categories = json.loads(row['categories'] or '[]')
                    tags = json.loads(row['tags'] or '[]')
                except (json.JSONDecodeError, TypeError):
                    categories = []
                    tags = []
                metadata[symbol] = {
                    "categories": categories,
                    "tags": tags
                }
            
            return {
                "symbols": symbols,
                "metadata": metadata
            }

    def add_symbol(self, username: str, symbol: str, max_symbols: int = 200, categories: Optional[List[str]] = None, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        username = username or 'default'
        norm = self.normalize_symbol(symbol)
        if not self.validate_symbol(norm):
            raise ValueError("Invalid symbol format")
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Check current count
            cursor.execute('SELECT COUNT(*) FROM watchlist WHERE user_id = ?', (username,))
            count = cursor.fetchone()[0]
            if count >= max_symbols:
                raise ValueError("Watchlist limit reached")
            
            # Check if symbol already exists
            cursor.execute('SELECT categories, tags FROM watchlist WHERE user_id = ? AND symbol = ?', (username, norm))
            existing = cursor.fetchone()
            
            if existing:
                # Update metadata if provided
                if categories is not None or tags is not None:
                    current_categories = json.loads(existing['categories'] or '[]') if categories is None else categories
                    current_tags = json.loads(existing['tags'] or '[]') if tags is None else tags
                    
                    cursor.execute('''
                        UPDATE watchlist 
                        SET categories = ?, tags = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ? AND symbol = ?
                    ''', (json.dumps(current_categories), json.dumps(current_tags), username, norm))
                    conn.commit()
            else:
                # Insert new symbol
                categories_json = json.dumps(categories or [])
                tags_json = json.dumps(tags or [])
                
                cursor.execute('''
                    INSERT INTO watchlist (user_id, symbol, categories, tags)
                    VALUES (?, ?, ?, ?)
                ''', (username, norm, categories_json, tags_json))
                conn.commit()
        
        # Return updated watchlist
        return self.get_watchlist_with_metadata(username)

    def remove_symbol(self, username: str, symbol: str) -> Dict[str, Any]:
        username = username or 'default'
        norm = self.normalize_symbol(symbol)
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM watchlist WHERE user_id = ? AND symbol = ?', (username, norm))
            conn.commit()
        
        # Return updated watchlist
        return self.get_watchlist_with_metadata(username)

    def update_symbol_metadata(self, username: str, symbol: str, categories: Optional[List[str]] = None, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Update categories and/or tags for a symbol"""
        username = username or 'default'
        norm = self.normalize_symbol(symbol)
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Check if symbol exists
            cursor.execute('SELECT categories, tags FROM watchlist WHERE user_id = ? AND symbol = ?', (username, norm))
            existing = cursor.fetchone()
            
            if not existing:
                raise ValueError(f"Symbol {norm} not in watchlist")
            
            # Get current values if not provided
            current_categories = json.loads(existing['categories'] or '[]') if categories is None else categories
            current_tags = json.loads(existing['tags'] or '[]') if tags is None else tags
            
            # Update
            cursor.execute('''
                UPDATE watchlist 
                SET categories = ?, tags = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND symbol = ?
            ''', (json.dumps(current_categories), json.dumps(current_tags), username, norm))
            conn.commit()
        
        # Return updated watchlist
        return self.get_watchlist_with_metadata(username)
