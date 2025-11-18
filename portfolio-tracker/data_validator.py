"""
Data Validation System for Portfolio Tracker
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd

class DataValidator:
    """System walidacji danych portfolio"""
    
    def __init__(self, validation_config='validation_config.json'):
        self.validation_config = validation_config
        self.config = self.load_config()
        self.validation_results = []
    
    def load_config(self):
        """Load validation configuration"""
        if os.path.exists(self.validation_config):
            try:
                with open(self.validation_config, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Default validation rules
        default_config = {
            'transaction_validation': {
                'required_fields': ['id', 'exchange', 'asset', 'amount', 'price_usd', 'type', 'date'],
                'amount_min': 0.000001,  # Minimum transaction amount
                'amount_max': 1000000,   # Maximum transaction amount
                'price_min': 0.000001,   # Minimum price
                'price_max': 1000000,    # Maximum price
                'date_format': '%Y-%m-%d',
                'valid_types': ['buy', 'sell'],
                'valid_exchanges': ['Binance', 'Bybit', 'XTB', 'Manual']
            },
            'portfolio_validation': {
                'balance_min': 0.0,
                'balance_max': 10000000,
                'price_min': 0.000001,
                'price_max': 1000000
            },
            'data_consistency': {
                'check_duplicates': True,
                'check_missing_data': True,
                'check_date_ranges': True,
                'check_price_anomalies': True,
                'check_balance_consistency': True
            },
            'alert_thresholds': {
                'price_change_percent': 50.0,  # Alert if price changes > 50%
                'balance_change_percent': 100.0,  # Alert if balance changes > 100%
                'duplicate_threshold': 1,  # Alert if duplicates found
                'missing_data_threshold': 5  # Alert if > 5% data missing
            }
        }
        
        self.save_config(default_config)
        return default_config
    
    def save_config(self, config=None):
        """Save validation configuration"""
        if config is None:
            config = self.config
        
        with open(self.validation_config, 'w') as f:
            json.dump(config, f, indent=2)
    
    def validate_transactions(self, transactions: List[Dict]) -> Dict:
        """Validate transaction data"""
        validation_results = {
            'total_transactions': len(transactions),
            'valid_transactions': 0,
            'invalid_transactions': 0,
            'errors': [],
            'warnings': [],
            'duplicates': [],
            'missing_data': []
        }
        
        if not transactions:
            validation_results['errors'].append("Brak transakcji do walidacji")
            return validation_results
        
        # Check for duplicates
        if self.config['data_consistency']['check_duplicates']:
            duplicates = self._find_duplicate_transactions(transactions)
            validation_results['duplicates'] = duplicates
        
        # Validate each transaction
        for i, transaction in enumerate(transactions):
            transaction_errors = self._validate_single_transaction(transaction, i)
            
            if transaction_errors['errors']:
                validation_results['invalid_transactions'] += 1
                validation_results['errors'].extend(transaction_errors['errors'])
            else:
                validation_results['valid_transactions'] += 1
            
            if transaction_errors['warnings']:
                validation_results['warnings'].extend(transaction_errors['warnings'])
        
        # Check for missing data
        if self.config['data_consistency']['check_missing_data']:
            missing_data = self._check_missing_data(transactions)
            validation_results['missing_data'] = missing_data
        
        return validation_results
    
    def _validate_single_transaction(self, transaction: Dict, index: int) -> Dict:
        """Validate a single transaction"""
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = self.config['transaction_validation']['required_fields']
        for field in required_fields:
            if field not in transaction:
                errors.append(f"Transakcja {index}: Brak wymaganego pola '{field}'")
            elif transaction[field] is None or transaction[field] == '':
                errors.append(f"Transakcja {index}: Pole '{field}' jest puste")
        
        # Validate amount
        if 'amount' in transaction:
            amount = transaction['amount']
            if not isinstance(amount, (int, float)):
                errors.append(f"Transakcja {index}: Ilość musi być liczbą")
            elif amount < self.config['transaction_validation']['amount_min']:
                errors.append(f"Transakcja {index}: Ilość za mała ({amount})")
            elif amount > self.config['transaction_validation']['amount_max']:
                errors.append(f"Transakcja {index}: Ilość za duża ({amount})")
        
        # Validate price
        if 'price_usd' in transaction:
            price = transaction['price_usd']
            if not isinstance(price, (int, float)):
                errors.append(f"Transakcja {index}: Cena musi być liczbą")
            elif price < self.config['transaction_validation']['price_min']:
                errors.append(f"Transakcja {index}: Cena za mała ({price})")
            elif price > self.config['transaction_validation']['price_max']:
                errors.append(f"Transakcja {index}: Cena za duża ({price})")
        
        # Validate transaction type
        if 'type' in transaction:
            valid_types = self.config['transaction_validation']['valid_types']
            if transaction['type'] not in valid_types:
                errors.append(f"Transakcja {index}: Nieprawidłowy typ transakcji ({transaction['type']})")
        
        # Validate exchange
        if 'exchange' in transaction:
            valid_exchanges = self.config['transaction_validation']['valid_exchanges']
            if transaction['exchange'] not in valid_exchanges:
                warnings.append(f"Transakcja {index}: Nieznana giełda ({transaction['exchange']})")
        
        # Validate date format
        if 'date' in transaction:
            try:
                datetime.strptime(transaction['date'][:10], self.config['transaction_validation']['date_format'])
            except ValueError:
                errors.append(f"Transakcja {index}: Nieprawidłowy format daty ({transaction['date']})")
        
        return {'errors': errors, 'warnings': warnings}
    
    def _find_duplicate_transactions(self, transactions: List[Dict]) -> List[Dict]:
        """Find duplicate transactions"""
        duplicates = []
        seen = set()
        
        for i, transaction in enumerate(transactions):
            # Create a key for duplicate detection
            key = (
                transaction.get('exchange', ''),
                transaction.get('asset', ''),
                transaction.get('amount', 0),
                transaction.get('price_usd', 0),
                transaction.get('type', ''),
                transaction.get('date', '')[:10]  # Date only
            )
            
            if key in seen:
                duplicates.append({
                    'index': i,
                    'transaction': transaction,
                    'duplicate_key': key
                })
            else:
                seen.add(key)
        
        return duplicates
    
    def _check_missing_data(self, transactions: List[Dict]) -> List[Dict]:
        """Check for missing data patterns"""
        missing_data = []
        
        # Check for missing exchange rates
        missing_rates = []
        for i, transaction in enumerate(transactions):
            if 'exchange_rate_usd_pln' not in transaction or transaction['exchange_rate_usd_pln'] is None:
                missing_rates.append(i)
        
        if missing_rates:
            missing_data.append({
                'type': 'missing_exchange_rates',
                'count': len(missing_rates),
                'indices': missing_rates[:10],  # Show first 10
                'description': f"Brak kursów USD->PLN w {len(missing_rates)} transakcjach"
            })
        
        # Check for missing commissions
        missing_commissions = []
        for i, transaction in enumerate(transactions):
            if 'commission' not in transaction or transaction['commission'] is None:
                missing_commissions.append(i)
        
        if missing_commissions:
            missing_data.append({
                'type': 'missing_commissions',
                'count': len(missing_commissions),
                'indices': missing_commissions[:10],
                'description': f"Brak prowizji w {len(missing_commissions)} transakcjach"
            })
        
        return missing_data
    
    def validate_portfolio_data(self, portfolios: List[Dict]) -> Dict:
        """Validate portfolio data"""
        validation_results = {
            'total_portfolios': len(portfolios),
            'valid_portfolios': 0,
            'invalid_portfolios': 0,
            'errors': [],
            'warnings': [],
            'anomalies': []
        }
        
        if not portfolios:
            validation_results['errors'].append("Brak danych portfolio do walidacji")
            return validation_results
        
        for i, portfolio in enumerate(portfolios):
            portfolio_errors = self._validate_single_portfolio(portfolio, i)
            
            if portfolio_errors['errors']:
                validation_results['invalid_portfolios'] += 1
                validation_results['errors'].extend(portfolio_errors['errors'])
            else:
                validation_results['valid_portfolios'] += 1
            
            if portfolio_errors['warnings']:
                validation_results['warnings'].extend(portfolio_errors['warnings'])
            
            if portfolio_errors['anomalies']:
                validation_results['anomalies'].extend(portfolio_errors['anomalies'])
        
        return validation_results
    
    def _validate_single_portfolio(self, portfolio: Dict, index: int) -> Dict:
        """Validate a single portfolio"""
        errors = []
        warnings = []
        anomalies = []
        
        # Check required fields
        if 'exchange' not in portfolio:
            errors.append(f"Portfolio {index}: Brak nazwy giełdy")
        
        if 'balances' not in portfolio:
            errors.append(f"Portfolio {index}: Brak danych sald")
        else:
            balances = portfolio['balances']
            if not isinstance(balances, list):
                errors.append(f"Portfolio {index}: Salda muszą być listą")
            else:
                for j, balance in enumerate(balances):
                    balance_errors = self._validate_single_balance(balance, f"{index}.{j}")
                    errors.extend(balance_errors['errors'])
                    warnings.extend(balance_errors['warnings'])
                    anomalies.extend(balance_errors['anomalies'])
        
        return {'errors': errors, 'warnings': warnings, 'anomalies': anomalies}
    
    def _validate_single_balance(self, balance: Dict, index: str) -> Dict:
        """Validate a single balance"""
        errors = []
        warnings = []
        anomalies = []
        
        # Check required fields
        required_fields = ['asset', 'amount', 'price_usd']
        for field in required_fields:
            if field not in balance:
                errors.append(f"Saldo {index}: Brak pola '{field}'")
            elif balance[field] is None:
                errors.append(f"Saldo {index}: Pole '{field}' jest puste")
        
        # Validate amount
        if 'amount' in balance:
            amount = balance['amount']
            if not isinstance(amount, (int, float)):
                errors.append(f"Saldo {index}: Ilość musi być liczbą")
            elif amount < self.config['portfolio_validation']['balance_min']:
                warnings.append(f"Saldo {index}: Bardzo mała ilość ({amount})")
            elif amount > self.config['portfolio_validation']['balance_max']:
                warnings.append(f"Saldo {index}: Bardzo duża ilość ({amount})")
        
        # Validate price
        if 'price_usd' in balance:
            price = balance['price_usd']
            if not isinstance(price, (int, float)):
                errors.append(f"Saldo {index}: Cena musi być liczbą")
            elif price < self.config['portfolio_validation']['price_min']:
                anomalies.append(f"Saldo {index}: Bardzo niska cena ({price})")
            elif price > self.config['portfolio_validation']['price_max']:
                anomalies.append(f"Saldo {index}: Bardzo wysoka cena ({price})")
        
        return {'errors': errors, 'warnings': warnings, 'anomalies': anomalies}
    
    def get_data_health_score(self, validation_results: Dict) -> float:
        """Calculate data health score (0-100)"""
        if not validation_results:
            return 0.0
        
        total_items = validation_results.get('total_transactions', 0) + validation_results.get('total_portfolios', 0)
        if total_items == 0:
            return 100.0
        
        # Calculate penalty points
        penalty_points = 0
        
        # Errors are severe
        penalty_points += len(validation_results.get('errors', [])) * 10
        
        # Warnings are moderate
        penalty_points += len(validation_results.get('warnings', [])) * 3
        
        # Anomalies are minor
        penalty_points += len(validation_results.get('anomalies', [])) * 1
        
        # Duplicates are moderate
        penalty_points += len(validation_results.get('duplicates', [])) * 5
        
        # Missing data is moderate
        penalty_points += len(validation_results.get('missing_data', [])) * 2
        
        # Calculate score
        max_penalty = total_items * 10  # Maximum possible penalty
        health_score = max(0, 100 - (penalty_points / max_penalty * 100))
        
        return round(health_score, 1)
    
    def get_validation_recommendations(self, validation_results: Dict) -> List[str]:
        """Get recommendations based on validation results"""
        recommendations = []
        
        if not validation_results:
            return recommendations
        
        # Error-based recommendations
        errors = validation_results.get('errors', [])
        if errors:
            recommendations.append(f"🚨 URGENTNE: Napraw {len(errors)} błędów w danych")
            recommendations.append("Sprawdź wymagane pola i formaty danych")
        
        # Warning-based recommendations
        warnings = validation_results.get('warnings', [])
        if warnings:
            recommendations.append(f"⚠️ Sprawdź {len(warnings)} ostrzeżeń")
            recommendations.append("Zweryfikuj nieprawidłowe wartości")
        
        # Duplicate-based recommendations
        duplicates = validation_results.get('duplicates', [])
        if duplicates:
            recommendations.append(f"🔄 Znaleziono {len(duplicates)} duplikatów")
            recommendations.append("Usuń duplikaty transakcji")
        
        # Missing data recommendations
        missing_data = validation_results.get('missing_data', [])
        if missing_data:
            recommendations.append(f"📊 Brakuje danych w {len(missing_data)} kategoriach")
            recommendations.append("Uzupełnij brakujące kursy i prowizje")
        
        # Anomaly-based recommendations
        anomalies = validation_results.get('anomalies', [])
        if anomalies:
            recommendations.append(f"🔍 Sprawdź {len(anomalies)} anomalii cenowych")
            recommendations.append("Zweryfikuj nieprawidłowe ceny")
        
        # Health score recommendations
        health_score = self.get_data_health_score(validation_results)
        if health_score >= 90:
            recommendations.append("✅ Doskonała jakość danych")
        elif health_score >= 70:
            recommendations.append("🟡 Dobra jakość danych")
        elif health_score >= 50:
            recommendations.append("🟠 Średnia jakość danych")
        else:
            recommendations.append("🔴 Słaba jakość danych - wymaga naprawy")
        
        return recommendations

# Example usage
if __name__ == "__main__":
    # Test data validation
    validator = DataValidator()
    
    # Sample transaction data
    sample_transactions = [
        {
            'id': 1,
            'exchange': 'Binance',
            'asset': 'BTC',
            'amount': 0.1,
            'price_usd': 50000,
            'type': 'buy',
            'date': '2024-01-01T10:00:00',
            'exchange_rate_usd_pln': 4.0,
            'commission': 10
        },
        {
            'id': 2,
            'exchange': 'Binance',
            'asset': 'BTC',
            'amount': 0.1,  # Duplicate
            'price_usd': 50000,
            'type': 'buy',
            'date': '2024-01-01T10:00:00',
            'exchange_rate_usd_pln': None,  # Missing data
            'commission': None  # Missing data
        },
        {
            'id': 3,
            'exchange': 'Unknown',  # Invalid exchange
            'asset': 'ETH',
            'amount': -0.1,  # Invalid amount
            'price_usd': 0,  # Invalid price
            'type': 'invalid',  # Invalid type
            'date': 'invalid-date',  # Invalid date
            'exchange_rate_usd_pln': 4.0,
            'commission': 5
        }
    ]
    
    # Validate transactions
    transaction_results = validator.validate_transactions(sample_transactions)
    
    print("Transaction Validation Results:")
    print(f"Total: {transaction_results['total_transactions']}")
    print(f"Valid: {transaction_results['valid_transactions']}")
    print(f"Invalid: {transaction_results['invalid_transactions']}")
    print(f"Errors: {len(transaction_results['errors'])}")
    print(f"Warnings: {len(transaction_results['warnings'])}")
    print(f"Duplicates: {len(transaction_results['duplicates'])}")
    print(f"Missing data: {len(transaction_results['missing_data'])}")
    
    # Calculate health score
    health_score = validator.get_data_health_score(transaction_results)
    print(f"\nData Health Score: {health_score}/100")
    
    # Get recommendations
    recommendations = validator.get_validation_recommendations(transaction_results)
    print(f"\nRecommendations:")
    for rec in recommendations:
        print(f"• {rec}")
    
    # Show specific errors
    if transaction_results['errors']:
        print(f"\nSpecific Errors:")
        for error in transaction_results['errors'][:5]:  # Show first 5
            print(f"• {error}")


