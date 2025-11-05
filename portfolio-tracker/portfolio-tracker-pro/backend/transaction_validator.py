"""
Transaction Validator for Portfolio Tracker Pro
Simple validation without external dependencies
"""
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class TransactionValidator:
    """Validator for transaction data"""
    
    # Validation rules
    AMOUNT_MIN = 0.000001
    AMOUNT_MAX = 1000000
    PRICE_MIN = 0.000001
    PRICE_MAX = 1000000
    VALID_TYPES = ['buy', 'sell']
    VALID_EXCHANGES = ['Binance', 'Bybit', 'XTB', 'Manual']
    
    @staticmethod
    def validate_create(data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate transaction data for creation
        
        Args:
            data: Transaction data dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Required fields
        required_fields = ['symbol', 'type', 'amount', 'price', 'date', 'exchange']
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == '':
                errors.append(f"{field} is required")
        
        if errors:
            return (False, errors)
        
        # Validate symbol
        symbol = data.get('symbol', '').strip()
        if not symbol:
            errors.append("Symbol cannot be empty")
        elif len(symbol) > 50:
            errors.append("Symbol cannot exceed 50 characters")
        
        # Validate type
        tx_type = data.get('type', '').lower()
        if tx_type not in TransactionValidator.VALID_TYPES:
            errors.append(f"Type must be one of: {', '.join(TransactionValidator.VALID_TYPES)}")
        
        # Validate exchange
        exchange = data.get('exchange', '')
        if exchange not in TransactionValidator.VALID_EXCHANGES:
            errors.append(f"Exchange must be one of: {', '.join(TransactionValidator.VALID_EXCHANGES)}")
        
        # Validate amount
        try:
            amount = float(data.get('amount', 0))
            if amount <= 0:
                errors.append(f"Amount must be greater than 0")
            elif amount < TransactionValidator.AMOUNT_MIN:
                errors.append(f"Amount too small (minimum: {TransactionValidator.AMOUNT_MIN})")
            elif amount > TransactionValidator.AMOUNT_MAX:
                errors.append(f"Amount too large (maximum: {TransactionValidator.AMOUNT_MAX})")
        except (ValueError, TypeError):
            errors.append("Amount must be a valid number")
        
        # Validate price
        try:
            price = float(data.get('price', 0))
            if price <= 0:
                errors.append(f"Price must be greater than 0")
            elif price < TransactionValidator.PRICE_MIN:
                errors.append(f"Price too small (minimum: {TransactionValidator.PRICE_MIN})")
            elif price > TransactionValidator.PRICE_MAX:
                errors.append(f"Price too large (maximum: {TransactionValidator.PRICE_MAX})")
        except (ValueError, TypeError):
            errors.append("Price must be a valid number")
        
        # Validate date
        date_str = data.get('date', '')
        if date_str:
            try:
                # Try parsing ISO format
                if 'T' in date_str:
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                
                # Check if date is in future
                now = datetime.now()
                if date_obj.date() > now.date():
                    errors.append("Transaction date cannot be in the future")
            except ValueError:
                errors.append("Invalid date format. Use YYYY-MM-DD or ISO format")
        
        # Validate commission (optional, but must be non-negative if provided)
        if 'commission' in data and data['commission'] is not None:
            try:
                commission = float(data.get('commission', 0))
                if commission < 0:
                    errors.append("Commission cannot be negative")
            except (ValueError, TypeError):
                errors.append("Commission must be a valid number")
        
        return (len(errors) == 0, errors)
    
    @staticmethod
    def validate_update(data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate transaction data for update
        
        Args:
            data: Transaction data dictionary (only fields being updated)
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate symbol if provided
        if 'symbol' in data and data['symbol'] is not None:
            symbol = str(data['symbol']).strip()
            if not symbol:
                errors.append("Symbol cannot be empty")
            elif len(symbol) > 50:
                errors.append("Symbol cannot exceed 50 characters")
        
        # Validate type if provided
        if 'type' in data and data['type'] is not None:
            tx_type = str(data['type']).lower()
            if tx_type not in TransactionValidator.VALID_TYPES:
                errors.append(f"Type must be one of: {', '.join(TransactionValidator.VALID_TYPES)}")
        
        # Validate exchange if provided
        if 'exchange' in data and data['exchange'] is not None:
            exchange = data['exchange']
            if exchange not in TransactionValidator.VALID_EXCHANGES:
                errors.append(f"Exchange must be one of: {', '.join(TransactionValidator.VALID_EXCHANGES)}")
        
        # Validate amount if provided
        if 'amount' in data and data['amount'] is not None:
            try:
                amount = float(data['amount'])
                if amount <= 0:
                    errors.append("Amount must be greater than 0")
                elif amount < TransactionValidator.AMOUNT_MIN:
                    errors.append(f"Amount too small (minimum: {TransactionValidator.AMOUNT_MIN})")
                elif amount > TransactionValidator.AMOUNT_MAX:
                    errors.append(f"Amount too large (maximum: {TransactionValidator.AMOUNT_MAX})")
            except (ValueError, TypeError):
                errors.append("Amount must be a valid number")
        
        # Validate price if provided
        if 'price' in data and data['price'] is not None:
            try:
                price = float(data['price'])
                if price <= 0:
                    errors.append("Price must be greater than 0")
                elif price < TransactionValidator.PRICE_MIN:
                    errors.append(f"Price too small (minimum: {TransactionValidator.PRICE_MIN})")
                elif price > TransactionValidator.PRICE_MAX:
                    errors.append(f"Price too large (maximum: {TransactionValidator.PRICE_MAX})")
            except (ValueError, TypeError):
                errors.append("Price must be a valid number")
        
        # Validate date if provided
        if 'date' in data and data['date'] is not None:
            date_str = str(data['date'])
            try:
                if 'T' in date_str:
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                
                now = datetime.now()
                if date_obj.date() > now.date():
                    errors.append("Transaction date cannot be in the future")
            except ValueError:
                errors.append("Invalid date format. Use YYYY-MM-DD or ISO format")
        
        # Validate commission if provided
        if 'commission' in data and data['commission'] is not None:
            try:
                commission = float(data['commission'])
                if commission < 0:
                    errors.append("Commission cannot be negative")
            except (ValueError, TypeError):
                errors.append("Commission must be a valid number")
        
        return (len(errors) == 0, errors)


