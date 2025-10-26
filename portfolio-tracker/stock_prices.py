"""
Get stock prices from Yahoo Finance API
"""
import requests
import json

def get_stock_price(symbol):
    """
    Get current stock price from Yahoo Finance
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL', 'TSLA')
    
    Returns:
        Current price or None if not found
    """
    try:
        # Yahoo Finance API (free, no key needed)
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'chart' in data and 'result' in data['chart']:
                result = data['chart']['result'][0]
                
                if 'meta' in result and 'regularMarketPrice' in result['meta']:
                    return result['meta']['regularMarketPrice']
        
        return None
    except Exception as e:
        print(f"Error fetching stock price for {symbol}: {e}")
        return None

def get_multiple_stock_prices(symbols):
    """
    Get current prices for multiple stocks
    
    Args:
        symbols: List of stock symbols
    
    Returns:
        Dictionary with symbol -> price mapping
    """
    prices = {}
    
    for symbol in symbols:
        price = get_stock_price(symbol)
        if price:
            prices[symbol] = price
        # Small delay to avoid rate limiting
        import time
        time.sleep(0.1)
    
    return prices

