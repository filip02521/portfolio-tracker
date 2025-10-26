"""
Transaction history tracking and PNL calculation
"""
import json
import os
from datetime import datetime
from typing import List, Dict

class TransactionHistory:
    """Manage transaction history and calculate PNL"""
    
    def __init__(self, data_file='transaction_history.json'):
        self.data_file = data_file
        self.transactions = self.load_history()
    
    def load_history(self):
        """Load transaction history from file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_history(self):
        """Save transaction history to file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.transactions, f, indent=2)
    
    def add_transaction(self, exchange: str, asset: str, amount: float, 
                       price_usd: float, transaction_type: str, date: str = None):
        """Add a new transaction"""
        transaction = {
            'id': len(self.transactions) + 1,
            'exchange': exchange,
            'asset': asset,
            'amount': amount,
            'price_usd': price_usd,
            'type': transaction_type,  # 'buy' or 'sell'
            'date': date or datetime.now().isoformat(),
            'value_usd': amount * price_usd
        }
        self.transactions.append(transaction)
        self.save_history()
        return transaction
    
    def get_transactions_for_asset(self, exchange: str, asset: str):
        """Get all transactions for a specific asset"""
        return [t for t in self.transactions 
                if t['exchange'] == exchange and t['asset'] == asset]
    
    def calculate_pnl(self, exchange: str, asset: str, current_price: float, current_amount: float):
        """Calculate PNL for an asset
        
        Args:
            exchange: Exchange name
            asset: Asset symbol
            current_price: Current price per unit
            current_amount: Current amount held in portfolio
            
        Returns:
            dict with PNL data or None if no transactions
        """
        transactions = self.get_transactions_for_asset(exchange, asset)
        
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
    
    def get_all_pnl(self, portfolios: List[Dict]):
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
                    pnl = self.calculate_pnl(exchange, asset, current_price, amount)
                    if pnl:
                        pnl_results.append(pnl)
        
        return pnl_results
    
    def import_from_csv(self, file_path: str, exchange: str):
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
                    date=row.get('date', None)
                )
            
            return True
        except Exception as e:
            print(f"Error importing CSV: {e}")
            return False

