"""
Stock symbol validation and search
"""
import requests
import json

def get_popular_stocks():
    """Get list of popular stock symbols"""
    return {
        # US Stocks
        'AAPL': 'Apple Inc.',
        'TSLA': 'Tesla Inc.',
        'MSFT': 'Microsoft Corporation',
        'GOOGL': 'Alphabet Inc.',
        'AMZN': 'Amazon.com Inc.',
        'META': 'Meta Platforms Inc.',
        'NVDA': 'NVIDIA Corporation',
        'NFLX': 'Netflix Inc.',
        'AMD': 'Advanced Micro Devices',
        'DIS': 'The Walt Disney Company',
        'JPM': 'JPMorgan Chase & Co.',
        'BAC': 'Bank of America Corp',
        'WMT': 'Walmart Inc.',
        'V': 'Visa Inc.',
        'MA': 'Mastercard Inc.',
        'JNJ': 'Johnson & Johnson',
        'PG': 'Procter & Gamble Co',
        'XOM': 'Exxon Mobil Corporation',
        'CVX': 'Chevron Corporation',
        'KO': 'The Coca-Cola Company',
        
        # European Stocks
        'ASML': 'ASML Holding',
        'SAP': 'SAP SE',
        'SAN': 'Banco Santander',
        'SHEL': 'Shell plc',
        'BP': 'BP plc',
        'GSK': 'GSK plc',
        'BASF': 'BASF SE',
        'BMW': 'Bayerische Motoren Werke',
        'VOW3': 'Volkswagen AG',
        
        # Crypto ETFs
        'BITQ': 'Bitwise Crypto Industry Innovators ETF',
        'ARKB': 'ARK 21Shares Bitcoin ETF',
        'HODL': 'VanEck Bitcoin Strategy ETF',
        
        # Commodities
        'GOLD': 'Gold',
        'SILVER': 'Silver',
        'OIL': 'Crude Oil',
        
        # Currencies
        'EURUSD': 'Euro vs US Dollar',
        'GBPUSD': 'British Pound vs US Dollar',
        'USDJPY': 'US Dollar vs Japanese Yen',
        'AUDUSD': 'Australian Dollar vs US Dollar',
        'NZDUSD': 'New Zealand Dollar vs US Dollar',
        'USDCAD': 'US Dollar vs Canadian Dollar',
        'USDCHF': 'US Dollar vs Swiss Franc',
    }

def validate_stock_symbol(symbol):
    """
    Validate if stock symbol exists in Yahoo Finance
    
    Args:
        symbol: Stock symbol to validate
    
    Returns:
        Tuple: (is_valid, stock_name or None)
    """
    try:
        # Yahoo Finance API
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'chart' in data and 'result' in data['chart']:
                result = data['chart']['result'][0]
                
                if 'meta' in result:
                    stock_name = result['meta'].get('longName') or result['meta'].get('shortName', symbol)
                    return True, stock_name
        
        return False, None
    except Exception as e:
        print(f"Error validating stock symbol {symbol}: {e}")
        return False, None

def search_stocks(query):
    """
    Search for stocks matching query
    
    Args:
        query: Search query
    
    Returns:
        List of matching stocks (symbol, name)
    """
    popular = get_popular_stocks()
    query_lower = query.upper()
    
    matches = []
    
    # Search in popular stocks
    for symbol, name in popular.items():
        if query_lower in symbol.upper() or query_lower in name.upper():
            matches.append((symbol, name))
    
    return matches[:10]  # Return top 10 matches

def search_by_isin(isin):
    """
    Search for stock symbol by ISIN
    
    Args:
        isin: ISIN code (e.g., 'US0378331005' for AAPL)
    
    Returns:
        Tuple: (symbol, stock_name) or (None, None) if not found
    """
    try:
        # Use Yahoo Finance API with ISIN search
        url = f"https://query1.finance.yahoo.com/v1/finance/search?q={isin}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'quotes' in data and len(data['quotes']) > 0:
                # Try to find exact ISIN match
                for quote in data['quotes']:
                    if quote.get('symbol'):
                        symbol = quote['symbol']
                        stock_name = quote.get('longname') or quote.get('shortname', symbol)
                        return symbol, stock_name
        
        return None, None
    except Exception as e:
        print(f"Error searching by ISIN {isin}: {e}")
        return None, None

def get_stock_info(symbol_or_isin, search_by_isin_flag=False):
    """
    Get stock information by symbol or ISIN
    
    Args:
        symbol_or_isin: Stock symbol or ISIN code
        search_by_isin_flag: If True, treat input as ISIN
    
    Returns:
        Dictionary with stock info: {symbol, name, price, currency, exchange}
    """
    try:
        if search_by_isin_flag:
            symbol, name = search_by_isin(symbol_or_isin)
            if not symbol:
                return None
        else:
            symbol = symbol_or_isin.upper()
            name = None
        
        # Get detailed info from Yahoo Finance
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'chart' in data and 'result' in data['chart']:
                result = data['chart']['result'][0]
                
                if 'meta' in result:
                    meta = result['meta']
                    stock_name = name or meta.get('longName') or meta.get('shortName', symbol)
                    price = meta.get('regularMarketPrice')
                    currency = meta.get('currency', 'USD')
                    exchange = meta.get('exchange', '')
                    
                    return {
                        'symbol': symbol,
                        'name': stock_name,
                        'price': price,
                        'currency': currency,
                        'exchange': exchange
                    }
        
        return None
    except Exception as e:
        print(f"Error getting stock info for {symbol_or_isin}: {e}")
        return None

