"""
Mock data provider for when APIs are unavailable
This provides sample data to demonstrate the application functionality
"""
import random
from datetime import datetime, timedelta

class MockDataProvider:
    """Provides mock portfolio data when APIs are unavailable"""
    
    @staticmethod
    def get_mock_portfolio_data():
        """Generate mock portfolio data for demonstration"""
        
        # Sample crypto assets with realistic values
        mock_assets = [
            {'asset': 'BTC', 'base_price': 45000, 'volatility': 0.05},
            {'asset': 'ETH', 'base_price': 2800, 'volatility': 0.08},
            {'asset': 'BNB', 'base_price': 320, 'volatility': 0.06},
            {'asset': 'ADA', 'base_price': 0.45, 'volatility': 0.12},
            {'asset': 'SOL', 'base_price': 95, 'volatility': 0.15},
            {'asset': 'DOT', 'base_price': 6.5, 'volatility': 0.10},
            {'asset': 'MATIC', 'base_price': 0.85, 'volatility': 0.18},
            {'asset': 'AVAX', 'base_price': 25, 'volatility': 0.14},
        ]
        
        portfolios = []
        
        # Mock Binance portfolio
        binance_balances = []
        binance_total = 0
        
        for asset_data in mock_assets[:4]:  # First 4 assets for Binance
            # Generate random amounts
            amount = round(random.uniform(0.1, 2.0), 6)
            # Add some price variation
            price_variation = random.uniform(0.9, 1.1)
            current_price = asset_data['base_price'] * price_variation
            
            value_usdt = amount * current_price
            binance_total += value_usdt
            
            binance_balances.append({
                'asset': asset_data['asset'],
                'free': amount * 0.7,  # 70% free
                'locked': amount * 0.3,  # 30% locked
                'total': amount,
                'value_usdt': value_usdt
            })
        
        portfolios.append({
            'balances': binance_balances,
            'total_value_usdt': binance_total,
            'exchange': 'Binance'
        })
        
        # Mock Bybit portfolio
        bybit_balances = []
        bybit_total = 0
        
        for asset_data in mock_assets[4:]:  # Last 4 assets for Bybit
            # Generate random amounts
            amount = round(random.uniform(0.1, 1.5), 6)
            # Add some price variation
            price_variation = random.uniform(0.9, 1.1)
            current_price = asset_data['base_price'] * price_variation
            
            value_usdt = amount * current_price
            bybit_total += value_usdt
            
            bybit_balances.append({
                'asset': asset_data['asset'],
                'free': amount * 0.8,  # 80% free
                'locked': amount * 0.2,  # 20% locked
                'total': amount,
                'value_usdt': value_usdt
            })
        
        portfolios.append({
            'balances': bybit_balances,
            'total_value_usdt': bybit_total,
            'exchange': 'Bybit'
        })
        
        return portfolios
    
    @staticmethod
    def get_mock_transaction_history():
        """Generate mock transaction history"""
        transactions = []
        
        # Generate some sample transactions
        assets = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'DOT', 'MATIC', 'AVAX']
        exchanges = ['Binance', 'Bybit']
        
        for i in range(20):  # Generate 20 mock transactions
            asset = random.choice(assets)
            exchange = random.choice(exchanges)
            
            # Generate transaction date (last 6 months)
            days_ago = random.randint(1, 180)
            transaction_date = datetime.now() - timedelta(days=days_ago)
            
            # Generate transaction details
            amount = round(random.uniform(0.01, 1.0), 6)
            price = round(random.uniform(100, 50000), 2)
            transaction_type = random.choice(['buy', 'sell'])
            
            transactions.append({
                'exchange': exchange,
                'asset': asset,
                'amount': amount,
                'price_usd': price,
                'transaction_type': transaction_type,
                'date': transaction_date.isoformat(),
                'total_value_usd': amount * price
            })
        
        # Sort by date (newest first)
        transactions.sort(key=lambda x: x['date'], reverse=True)
        
        return transactions
    
    @staticmethod
    def is_api_available():
        """Check if APIs are available (mock implementation)"""
        # In a real implementation, this would check API connectivity
        # For now, we'll return False to indicate APIs are not available
        return False
