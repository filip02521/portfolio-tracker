"""
Migration script to add missing data to existing transactions
"""
import json
from datetime import datetime
from nbp_api import NBPAPI

def migrate_transactions():
    """Add exchange rates and commission data to existing transactions"""
    
    # Load transactions
    with open('transaction_history.json', 'r') as f:
        transactions = json.load(f)
    
    print(f"Found {len(transactions)} transactions to migrate")
    
    # Initialize NBP API
    nbp = NBPAPI()
    
    # Get unique dates
    dates = set()
    for tx in transactions:
        date_str = tx['date'][:10]  # Extract YYYY-MM-DD
        dates.add(date_str)
    
    print(f"Fetching rates for {len(dates)} unique dates...")
    
    # Get all rates at once
    rates = nbp.get_multiple_rates(list(dates))
    print(f"Successfully fetched {len(rates)} exchange rates")
    
    # Update transactions
    updated = 0
    for tx in transactions:
        date_str = tx['date'][:10]
        
        # Add exchange rate if available
        if date_str in rates:
            tx['exchange_rate_usd_pln'] = rates[date_str]
            tx['value_pln'] = tx['value_usd'] * rates[date_str]
        else:
            tx['exchange_rate_usd_pln'] = None
            tx['value_pln'] = None
        
        # Add commission fields if missing
        if 'commission' not in tx:
            tx['commission'] = 0.0
        if 'commission_currency' not in tx:
            tx['commission_currency'] = 'USD'
        if 'linked_buys' not in tx:
            tx['linked_buys'] = []
        
        updated += 1
    
    # Save updated transactions
    with open('transaction_history.json', 'w') as f:
        json.dump(transactions, f, indent=2)
    
    print(f"✅ Updated {updated} transactions")
    print(f"✅ Added exchange rates for {len(rates)} dates")
    
    # Show sample
    sample_tx = transactions[0]
    print(f"\nSample transaction:")
    print(f"  Asset: {sample_tx['asset']}")
    print(f"  Date: {sample_tx['date'][:10]}")
    print(f"  Value USD: ${sample_tx['value_usd']:.2f}")
    if sample_tx['exchange_rate_usd_pln']:
        print(f"  Exchange rate: {sample_tx['exchange_rate_usd_pln']} PLN/USD")
        print(f"  Value PLN: {sample_tx['value_pln']:.2f} PLN")
    else:
        print(f"  Exchange rate: Not available")

if __name__ == "__main__":
    migrate_transactions()
