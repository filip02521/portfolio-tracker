"""
Transaction history tracking and PNL calculation
Now uses SQLite database instead of JSON file for better performance and persistence
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from database import get_db, migrate_json_to_db

class TransactionHistory:
    """Manage transaction history and calculate PNL"""
    
    def __init__(self, data_file='transaction_history.json'):
        self.data_file = data_file
        # Migrate from JSON to database on first init
        migrate_json_to_db(data_file)
        # Load transactions from database
        self.transactions = self.load_history()
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert database row to transaction dictionary"""
        # sqlite3.Row supports dict-like access but not .get()
        return {
            'id': row['id'],
            'user_id': row['user_id'] if 'user_id' in row.keys() else None,
            'exchange': row['exchange'],
            'asset': row['asset'],
            'amount': row['amount'],
            'price_usd': row['price_usd'],
            'type': row['type'],
            'date': row['date'],
            'value_usd': row['value_usd'],
            'commission': row['commission'] if 'commission' in row.keys() else 0.0,
            'commission_currency': row['commission_currency'] if 'commission_currency' in row.keys() else 'USD',
            'isin': row['isin'] if 'isin' in row.keys() and row['isin'] else None,
            'asset_name': row['asset_name'] if 'asset_name' in row.keys() and row['asset_name'] else None,
            'exchange_rate_usd_pln': None,
            'value_pln': None,
            'linked_buys': [],
        }
    
    def load_history(self, user_id: Optional[str] = None) -> List[Dict]:
        """Load transaction history from database"""
        with get_db() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute('SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC, id DESC', (user_id,))
            else:
                cursor.execute('SELECT * FROM transactions ORDER BY date DESC, id DESC')
            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]
    
    def save_history(self):
        """No-op: transactions are saved directly to database"""
        pass
    
    # --- Transaction normalization helpers -----------------------------------------------------

    def _next_transaction_id(self) -> int:
        """Return the next transaction identifier from database."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT MAX(id) FROM transactions')
            result = cursor.fetchone()
            max_id = result[0] if result[0] is not None else 0
            return max_id + 1

    @staticmethod
    def _normalize_type(tx_type: str) -> str:
        normalized = (tx_type or '').strip().lower()
        if normalized not in ('buy', 'sell'):
            raise ValueError(f"Unsupported transaction type '{tx_type}'")
        return normalized

    @staticmethod
    def _normalize_asset(asset: str) -> str:
        asset_clean = (asset or '').strip().upper()
        if not asset_clean:
            raise ValueError("Asset symbol cannot be empty")
        return asset_clean

    @staticmethod
    def _normalize_exchange(exchange: str) -> str:
        exch_clean = (exchange or '').strip()
        if not exch_clean:
            raise ValueError("Exchange name cannot be empty")
        return exch_clean

    @staticmethod
    def _normalize_amount(value: Any, field: str) -> float:
        try:
            amount = float(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field} must be a numeric value")
        return amount

    @staticmethod
    def _normalize_date(date_str: Optional[str]) -> str:
        if not date_str:
            return datetime.utcnow().isoformat() + "Z"
        try:
            # Accept ISO strings or YYYY-MM-DD
            if 'T' in date_str:
                datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                datetime.strptime(date_str, '%Y-%m-%d')
            return date_str
        except ValueError:
            raise ValueError(f"Unsupported date format '{date_str}'")

    def _build_transaction_payload(
        self,
        *,
        exchange: str,
        asset: str,
        amount: float,
        price_usd: float,
        transaction_type: str,
        date: Optional[str] = None,
        commission: Optional[float] = 0.0,
        commission_currency: Optional[str] = 'USD',
        isin: Optional[str] = None,
        asset_name: Optional[str] = None,
        transaction_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Normalize and return a transaction dictionary without mutating state."""
        normalized_exchange = self._normalize_exchange(exchange)
        normalized_asset = self._normalize_asset(asset)
        normalized_type = self._normalize_type(transaction_type)
        normalized_amount = self._normalize_amount(amount, "Amount")
        normalized_price = self._normalize_amount(price_usd, "Price (USD)")
        normalized_commission = self._normalize_amount(commission or 0.0, "Commission")
        normalized_date = self._normalize_date(date)

        if normalized_amount <= 0:
            raise ValueError("Amount must be greater than zero")
        if normalized_price <= 0:
            raise ValueError("Price (USD) must be greater than zero")
        if normalized_commission < 0:
            raise ValueError("Commission cannot be negative")

        value_usd = normalized_amount * normalized_price

        transaction = {
            'id': transaction_id if transaction_id is not None else self._next_transaction_id(),
            'exchange': normalized_exchange,
            'asset': normalized_asset,
            'amount': normalized_amount,
            'price_usd': normalized_price,
            'type': normalized_type,
            'date': normalized_date,
            'value_usd': value_usd,
            'commission': normalized_commission,
            'commission_currency': (commission_currency or 'USD'),
            'isin': (isin or '').upper() or None,
            'asset_name': (asset_name or '').strip() or None,
            'exchange_rate_usd_pln': None,
            'value_pln': None,
            'linked_buys': [],
        }
        return transaction

    # -------------------------------------------------------------------------------------------

    def build_transaction_key(
        self,
        exchange: str,
        asset: str,
        transaction_type: str,
        amount: float,
        price_usd: float,
        date: str,
        precision: Tuple[int, int] = (8, 8)
    ) -> Tuple:
        """Return a normalized key used for deduplicating transactions across ingestion paths."""
        norm_exchange = self._normalize_exchange(exchange).lower()
        norm_asset = self._normalize_asset(asset)
        norm_type = self._normalize_type(transaction_type)
        norm_amount = self._normalize_amount(amount, "Amount")
        norm_price = self._normalize_amount(price_usd, "Price (USD)")
        norm_date = self._normalize_date(date)

        amount_precision, price_precision = precision
        return (
            norm_exchange,
            norm_asset,
            norm_type,
            round(norm_amount, amount_precision),
            round(norm_price, price_precision),
            norm_date[:10],
        )

    # -------------------------------------------------------------------------------------------

    def add_transaction(self, exchange: str, asset: str, amount: float,
                        price_usd: float, transaction_type: str, date: str = None,
                        commission: float = 0.0, commission_currency: str = 'USD',
                        isin: str = None, asset_name: str = None, user_id: Optional[str] = None):
        """Add a new transaction with normalized payload and persisted id."""
        transaction = self._build_transaction_payload(
            exchange=exchange,
            asset=asset,
            amount=amount,
            price_usd=price_usd,
            transaction_type=transaction_type,
            date=date,
            commission=commission,
            commission_currency=commission_currency,
            isin=isin,
            asset_name=asset_name,
        )
        
        # Save to database
        with get_db() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO transactions (
                        id, exchange, asset, amount, price_usd, type, date,
                        value_usd, commission, commission_currency, isin, asset_name, user_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    transaction['id'],
                    transaction['exchange'],
                    transaction['asset'],
                    transaction['amount'],
                    transaction['price_usd'],
                    transaction['type'],
                    transaction['date'],
                    transaction['value_usd'],
                    transaction['commission'],
                    transaction['commission_currency'],
                    transaction['isin'],
                    transaction['asset_name'],
                    user_id,
                ))
                conn.commit()
            except Exception as e:
                # If insert fails (e.g., duplicate), try to get existing transaction
                conn.rollback()
                cursor.execute('''
                    SELECT * FROM transactions 
                    WHERE exchange = ? AND asset = ? AND date = ? AND type = ? 
                    AND amount = ? AND price_usd = ?
                ''', (
                    transaction['exchange'],
                    transaction['asset'],
                    transaction['date'],
                    transaction['type'],
                    transaction['amount'],
                    transaction['price_usd'],
                ))
                existing = cursor.fetchone()
                if existing:
                    return self._row_to_dict(existing)
                raise
        
        # Reload transactions from database
        self.transactions = self.load_history(user_id)
        return transaction
    
    def get_transactions_for_asset(self, exchange: str, asset: str, user_id: Optional[str] = None):
        """Get all transactions for a specific asset"""
        with get_db() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute('''
                    SELECT * FROM transactions 
                    WHERE exchange = ? AND asset = ? AND (user_id = ? OR user_id IS NULL)
                    ORDER BY date DESC, id DESC
                ''', (exchange, asset, user_id))
            else:
                cursor.execute('''
                    SELECT * FROM transactions 
                    WHERE exchange = ? AND asset = ?
                    ORDER BY date DESC, id DESC
                ''', (exchange, asset))
            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]
    
    def get_all_transactions(self, user_id: Optional[str] = None, limit: Optional[int] = None, offset: int = 0):
        """Get all transactions from database"""
        with get_db() as conn:
            cursor = conn.cursor()
            if user_id:
                query = 'SELECT * FROM transactions WHERE user_id = ? OR user_id IS NULL ORDER BY date DESC, id DESC'
                params = (user_id,)
            else:
                query = 'SELECT * FROM transactions ORDER BY date DESC, id DESC'
                params = ()
            
            if limit:
                query += f' LIMIT {limit} OFFSET {offset}'
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]
    
    def delete_transaction(self, transaction_id: int, user_id: Optional[str] = None):
        """Delete a transaction by ID, optionally filtered by user_id"""
        with get_db() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute('DELETE FROM transactions WHERE id = ? AND user_id = ?', (transaction_id, user_id))
            else:
                cursor.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
            conn.commit()
        
        # Reload transactions from database
        self.transactions = self.load_history(user_id=user_id)
    
    def update_transaction(self, transaction_id: int, user_id: Optional[str] = None, **kwargs):
        """Update a transaction by ID, optionally filtered by user_id"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get existing transaction
            if user_id:
                cursor.execute('SELECT * FROM transactions WHERE id = ? AND user_id = ?', (transaction_id, user_id))
            else:
                cursor.execute('SELECT * FROM transactions WHERE id = ?', (transaction_id,))
            existing_row = cursor.fetchone()
            if not existing_row:
                return False
            
            existing = self._row_to_dict(existing_row)
            
            # Update with new values
            updated_payload = existing.copy()
            updated_payload.update(kwargs or {})

            transaction = self._build_transaction_payload(
                exchange=updated_payload.get('exchange', existing['exchange']),
                asset=updated_payload.get('asset', existing['asset']),
                amount=updated_payload.get('amount', existing['amount']),
                price_usd=updated_payload.get('price_usd', existing['price_usd']),
                transaction_type=updated_payload.get('type', existing['type']),
                date=updated_payload.get('date', existing['date']),
                commission=updated_payload.get('commission', existing.get('commission', 0.0)),
                commission_currency=updated_payload.get('commission_currency', existing.get('commission_currency', 'USD')),
                isin=updated_payload.get('isin', existing.get('isin')),
                asset_name=updated_payload.get('asset_name', existing.get('asset_name')),
                transaction_id=transaction_id,
            )

            # Update in database
            if user_id:
                cursor.execute('''
                    UPDATE transactions SET
                        exchange = ?, asset = ?, amount = ?, price_usd = ?, type = ?,
                        date = ?, value_usd = ?, commission = ?, commission_currency = ?,
                        isin = ?, asset_name = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND user_id = ?
                ''', (
                    transaction['exchange'],
                    transaction['asset'],
                    transaction['amount'],
                    transaction['price_usd'],
                    transaction['type'],
                    transaction['date'],
                    transaction['value_usd'],
                    transaction['commission'],
                    transaction['commission_currency'],
                    transaction['isin'],
                    transaction['asset_name'],
                    transaction_id,
                    user_id,
                ))
            else:
                cursor.execute('''
                    UPDATE transactions SET
                        exchange = ?, asset = ?, amount = ?, price_usd = ?, type = ?,
                        date = ?, value_usd = ?, commission = ?, commission_currency = ?,
                        isin = ?, asset_name = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (
                    transaction['exchange'],
                    transaction['asset'],
                    transaction['amount'],
                    transaction['price_usd'],
                    transaction['type'],
                    transaction['date'],
                    transaction['value_usd'],
                    transaction['commission'],
                    transaction['commission_currency'],
                    transaction['isin'],
                    transaction['asset_name'],
                    transaction_id,
                ))
            conn.commit()
        
        # Reload transactions from database
        self.transactions = self.load_history(user_id=user_id)
        return True
    
    def get_total_realized_pnl(self, user_id: Optional[str] = None):
        """Calculate total realized PNL using true FIFO method"""
        transactions = self.get_all_transactions(user_id=user_id)
        total_pnl = 0.0
        
        # Group by asset to calculate PNL per asset
        assets = {}
        for t in transactions:
            key = (t['exchange'], t['asset'])
            if key not in assets:
                assets[key] = {'buys': [], 'sells': []}
            
            if t['type'] == 'buy':
                assets[key]['buys'].append(t)
            else:
                assets[key]['sells'].append(t)
        
        # Calculate realized PNL using true FIFO
        for (exchange, asset), data in assets.items():
            buys = sorted(data['buys'], key=lambda x: x['date'])  # Sort by date (FIFO)
            sells = sorted(data['sells'], key=lambda x: x['date'])
            
            if not sells or not buys:
                continue
            
            # Create FIFO queue
            fifo_queue = []
            for buy in buys:
                fifo_queue.append({
                    'amount': buy['amount'],
                    'price_usd': buy['price_usd'],
                    'value_usd': buy['value_usd'],
                    'commission': buy.get('commission', 0.0),
                    'date': buy['date'],
                    'id': buy['id']
                })
            
            # Process sells using FIFO
            for sell in sells:
                remaining_sell = sell['amount']
                sell_proceeds = sell['value_usd']
                sell_commission = sell.get('commission', 0.0)
                
                while remaining_sell > 0 and fifo_queue:
                    buy_lot = fifo_queue[0]
                    
                    if buy_lot['amount'] <= remaining_sell:
                        # Use entire buy lot
                        used_amount = buy_lot['amount']
                        cost_basis = buy_lot['value_usd']
                        cost_commission = buy_lot['commission']
                        
                        # Calculate PNL for this portion
                        proceeds_portion = (used_amount / sell['amount']) * sell_proceeds
                        commission_portion = (used_amount / sell['amount']) * sell_commission
                        
                        realized_pnl = proceeds_portion - cost_basis - cost_commission - commission_portion
                        total_pnl += realized_pnl
                        
                        remaining_sell -= used_amount
                        fifo_queue.pop(0)  # Remove used buy lot
                        
                    else:
                        # Use partial buy lot
                        used_amount = remaining_sell
                        cost_basis = (used_amount / buy_lot['amount']) * buy_lot['value_usd']
                        cost_commission = (used_amount / buy_lot['amount']) * buy_lot['commission']
                        
                        # Calculate PNL for this portion
                        proceeds_portion = (used_amount / sell['amount']) * sell_proceeds
                        commission_portion = (used_amount / sell['amount']) * sell_commission
                        
                        realized_pnl = proceeds_portion - cost_basis - cost_commission - commission_portion
                        total_pnl += realized_pnl
                        
                        # Update remaining buy lot
                        buy_lot['amount'] -= used_amount
                        buy_lot['value_usd'] -= cost_basis
                        buy_lot['commission'] -= cost_commission
                        
                        remaining_sell = 0
        
        return total_pnl
    
    def calculate_pnl(self, exchange: str, asset: str, current_price: float, current_amount: float, user_id: Optional[str] = None):
        """Calculate PNL for an asset
        
        Args:
            exchange: Exchange name
            asset: Asset symbol
            current_price: Current price per unit
            current_amount: Current amount held in portfolio
            user_id: Optional user ID to filter transactions
            
        Returns:
            dict with PNL data or None if no transactions
        """
        transactions = self.get_transactions_for_asset(exchange, asset, user_id=user_id)
        
        if not transactions:
            return None
        
        # Separate buy and sell transactions
        buy_transactions = [t for t in transactions if t['type'] == 'buy']
        sell_transactions = [t for t in transactions if t['type'] == 'sell']
        
        # Calculate total invested (money spent on buys)
        total_invested = sum(t['value_usd'] for t in buy_transactions)
        
        # Calculate total proceeds from sells
        total_proceeds = sum(t['value_usd'] for t in sell_transactions)
        
        # Calculate net amount held (buys - sells)
        buy_amount = sum(t['amount'] for t in buy_transactions)
        sell_amount = sum(t['amount'] for t in sell_transactions)
        net_amount = buy_amount - sell_amount
        
        # Only calculate PNL if we still hold some of this asset
        if net_amount <= 0:
            return None
        
        # Use net_amount from transactions, not current_amount from portfolio
        # This ensures we calculate PNL based on what we should have, not what we have
        # Calculate cost basis proportionally
        cost_basis = total_invested * (net_amount / buy_amount) if buy_amount > 0 else 0
        
        # Current value based on net amount from transactions
        current_value = net_amount * current_price
        
        # Realized PNL from sells
        realized_pnl = total_proceeds - (total_invested * (sell_amount / buy_amount) if buy_amount > 0 else 0)
        
        # Unrealized PNL from current holdings
        unrealized_pnl = current_value - cost_basis
        
        # Total PNL
        total_pnl = realized_pnl + unrealized_pnl
        
        # PNL percentage based on current holdings
        pnl_percent = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0
        
        return {
            'asset': asset,
            'exchange': exchange,
            'current_amount': net_amount,  # Use net amount from transactions
            'current_price': current_price,
            'current_value': current_value,
            'invested': cost_basis,
            'realized_pnl': realized_pnl,
            'unrealized_pnl': unrealized_pnl,
            'pnl': total_pnl,
            'pnl_percent': pnl_percent,
            'status': 'profit' if total_pnl > 0 else 'loss' if total_pnl < 0 else 'break_even'
        }
    
    def get_all_pnl(self, portfolios: List[Dict], user_id: Optional[str] = None):
        """Calculate PNL for all assets"""
        pnl_results = []
        
        for portfolio in portfolios:
            exchange = portfolio['exchange']
            for balance in portfolio['balances']:
                asset = balance['asset']
                amount = balance['total']
                value_usdt = balance.get('value_usdt', 0)
                
                if amount > 0 and value_usdt > 0:
                    current_price = value_usdt / amount
                    pnl = self.calculate_pnl(exchange, asset, current_price, amount, user_id=user_id)
                    if pnl:
                        pnl_results.append(pnl)
        
        return pnl_results
    
    def import_from_csv(self, file_path: str, exchange: str, user_id: Optional[str] = None):
        """Import transactions from CSV file"""
        import pandas as pd
        
        try:
            df = pd.read_csv(file_path)
            
            # Expected columns: date, asset, amount, price, type
            for _, row in df.iterrows():
                self.add_transaction(
                    exchange=exchange,
                    asset=row['asset'],
                    amount=float(row['amount']),
                    price_usd=float(row['price']),
                    transaction_type=row['type'],
                    date=row.get('date', None),
                    user_id=user_id
                )
            
            return True
        except Exception as e:
            print(f"Error importing CSV: {e}")
            return False
