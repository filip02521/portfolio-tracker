"""
Utility functions for portfolio tracker
"""
import requests
from datetime import datetime

def get_usd_to_pln_rate():
    """Get current USD to PLN exchange rate"""
    try:
        response = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data['rates'].get('PLN', 4.0)
    except:
        pass
    # Fallback rate
    return 4.0

def format_currency(amount, currency='USD'):
    """Format currency amount"""
    if currency == 'PLN':
        return f"{amount:,.2f} zł"
    else:
        return f"${amount:,.2f}"

def get_top_assets(portfolios, top_n=10):
    """Get top N assets by value"""
    all_assets = []
    
    for portfolio in portfolios:
        exchange = portfolio['exchange']
        for balance in portfolio['balances']:
            if balance['total'] > 0:
                all_assets.append({
                    'exchange': exchange,
                    'asset': balance['asset'],
                    'total': balance['total'],
                    'free': balance['free'],
                    'locked': balance['locked'],
                    'value_usdt': balance.get('value_usdt', 0)  # Add value if available
                })
    
    # Sort by value in USDT (if available), otherwise by total amount
    all_assets.sort(key=lambda x: x.get('value_usdt', x['total']), reverse=True)
    return all_assets[:top_n]

def calculate_diversification(portfolios):
    """Calculate portfolio diversification metrics"""
    total_value = sum(p['total_value_usdt'] for p in portfolios)
    
    # Exchange diversification
    exchange_distribution = {}
    for portfolio in portfolios:
        if portfolio['total_value_usdt'] > 0:
            exchange_distribution[portfolio['exchange']] = portfolio['total_value_usdt']
    
    # Asset count
    total_assets = sum(len(p['balances']) for p in portfolios)
    
    return {
        'total_value': total_value,
        'exchange_distribution': exchange_distribution,
        'total_assets': total_assets,
        'total_exchanges': len(exchange_distribution)
    }

