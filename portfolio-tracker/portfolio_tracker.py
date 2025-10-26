"""
Unified portfolio tracker for multiple exchanges
"""
try:
    from exchanges import BinanceClient, BybitClient
except ImportError as e:
    print(f"Warning: Could not import exchange clients: {e}")
    # Create dummy classes for fallback
    class BinanceClient:
        def __init__(self): raise ValueError("Binance not available")
    class BybitClient:
        def __init__(self): raise ValueError("Bybit not available")

class PortfolioTracker:
    """Main portfolio tracker class"""
    
    def __init__(self):
        """Initialize tracker with all exchange clients"""
        self.exchanges = {}
        
        # Initialize Binance
        try:
            self.exchanges['Binance'] = BinanceClient()
            print("✓ Binance initialized successfully")
        except ValueError as e:
            print(f"⚠ Binance: {e}")
        except Exception as e:
            print(f"✗ Binance initialization failed: {e}")
        
        # Initialize Bybit
        try:
            self.exchanges['Bybit'] = BybitClient()
            print("✓ Bybit initialized successfully")
        except ValueError as e:
            print(f"⚠ Bybit: {e}")
        except Exception as e:
            print(f"✗ Bybit initialization failed: {e}")
        
        print(f"Initialized {len(self.exchanges)} exchange(s)")
    
    def get_all_portfolio_data(self):
        """Get portfolio data from all exchanges"""
        all_data = []
        
        for exchange_name, client in self.exchanges.items():
            try:
                data = client.get_portfolio_value()
                if data and data.get('balances'):
                    all_data.append(data)
            except Exception as e:
                print(f"Error getting {exchange_name} portfolio: {e}")
        
        return all_data
    
    def get_total_portfolio_value(self):
        """Get total portfolio value across all exchanges"""
        all_data = self.get_all_portfolio_data()
        total_value = sum(data.get('total_value_usdt', 0) for data in all_data)
        return total_value
    
    def get_portfolio_summary(self):
        """Get formatted portfolio summary"""
        all_data = self.get_all_portfolio_data()
        
        if not all_data:
            return "No portfolio data available"
        
        summary = []
        total_value = 0
        
        for data in all_data:
            exchange = data.get('exchange', 'Unknown')
            value = data.get('total_value_usdt', 0)
            total_value += value
            
            summary.append(f"{exchange}: ${value:,.2f}")
        
        summary.append(f"\nTotal: ${total_value:,.2f}")
        return "\n".join(summary)
    
    def print_portfolio_table(self):
        """Print portfolio in table format"""
        try:
            from tabulate import tabulate
        except ImportError:
            print("Warning: tabulate not available, using simple format")
            self._print_portfolio_simple()
            return
        
        all_data = self.get_all_portfolio_data()
        
        if not all_data:
            print("No portfolio data available")
            return
        
        table_data = []
        total_value = 0
        
        for data in all_data:
            exchange = data.get('exchange', 'Unknown')
            balances = data.get('balances', [])
            
            for balance in balances:
                asset = balance.get('asset', '')
                amount = balance.get('total', 0)
                value_usdt = balance.get('value_usdt', 0)
                
                if amount > 0:
                    table_data.append([
                        exchange,
                        asset,
                        f"{amount:.6f}",
                        f"${value_usdt:.2f}"
                    ])
                    total_value += value_usdt
        
        if table_data:
            headers = ["Exchange", "Asset", "Amount", "Value (USDT)"]
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
            print(f"\nTotal Portfolio Value: ${total_value:,.2f}")
        else:
            print("No assets found in portfolio")
    
    def _print_portfolio_simple(self):
        """Print portfolio in simple format without tabulate"""
        all_data = self.get_all_portfolio_data()
        
        if not all_data:
            print("No portfolio data available")
            return
        
        total_value = 0
        
        for data in all_data:
            exchange = data.get('exchange', 'Unknown')
            balances = data.get('balances', [])
            
            print(f"\n{exchange}:")
            for balance in balances:
                asset = balance.get('asset', '')
                amount = balance.get('total', 0)
                value_usdt = balance.get('value_usdt', 0)
                
                if amount > 0:
                    print(f"  {asset}: {amount:.6f} (${value_usdt:.2f})")
                    total_value += value_usdt
        
        print(f"\nTotal Portfolio Value: ${total_value:,.2f}")

if __name__ == "__main__":
    tracker = PortfolioTracker()
    tracker.print_portfolio_table()