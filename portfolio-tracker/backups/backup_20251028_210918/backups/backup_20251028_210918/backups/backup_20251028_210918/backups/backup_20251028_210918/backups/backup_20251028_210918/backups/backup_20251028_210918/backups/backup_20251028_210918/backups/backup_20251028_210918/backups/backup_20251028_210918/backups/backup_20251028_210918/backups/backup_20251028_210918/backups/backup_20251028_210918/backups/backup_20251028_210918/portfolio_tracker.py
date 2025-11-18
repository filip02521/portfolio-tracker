"""
Unified portfolio tracker for multiple exchanges
"""
from exchanges import BinanceClient, BybitClient
from tabulate import tabulate

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
            print(f"❌ Failed to initialize Binance: {e}")
        
        # Initialize Bybit
        try:
            self.exchanges['Bybit'] = BybitClient()
            print("✓ Bybit initialized successfully")
        except ValueError as e:
            print(f"⚠ Bybit: {e}")
        except Exception as e:
            print(f"❌ Failed to initialize Bybit: {e}")
    
    def get_all_portfolios(self):
        """Get portfolio data from all exchanges"""
        portfolios = []
        
        for name, client in self.exchanges.items():
            try:
                portfolio = client.get_portfolio_value()
                if portfolio:
                    portfolios.append(portfolio)
                else:
                    # Add empty portfolio if None returned
                    portfolios.append({
                        'balances': [],
                        'total_value_usdt': 0,
                        'exchange': name
                    })
            except Exception as e:
                print(f"Error fetching {name} portfolio: {e}")
                # Add empty portfolio for this exchange
                portfolios.append({
                    'balances': [],
                    'total_value_usdt': 0,
                    'exchange': name
                })
        
        return portfolios
    
    def display_portfolio(self):
        """Display portfolio information in a formatted table"""
        portfolios = self.get_all_portfolios()
        
        if not portfolios:
            print("\n⚠ No portfolio data available.")
            return
        
        print("\n" + "="*80)
        print("PORTFOLIO SUMMARY")
        print("="*80 + "\n")
        
        # Display individual exchange portfolios
        for portfolio in portfolios:
            exchange = portfolio['exchange']
            total_value = portfolio['total_value_usdt']
            
            print(f"\n📊 {exchange}:")
            print(f"Total Value: ${total_value:,.2f} USDT")
            
            if portfolio['balances']:
                table_data = []
                for balance in portfolio['balances']:
                    table_data.append([
                        balance['asset'],
                        f"{balance['total']:.8f}",
                        f"{balance['free']:.8f}",
                        f"{balance['locked']:.8f}"
                    ])
                
                print(tabulate(
                    table_data,
                    headers=['Asset', 'Total', 'Available', 'Locked'],
                    tablefmt='grid'
                ))
            else:
                print("No balances found")
        
        # Calculate total across all exchanges
        total_portfolio_value = sum(p['total_value_usdt'] for p in portfolios)
        
        print("\n" + "="*80)
        print(f"💼 TOTAL PORTFOLIO VALUE: ${total_portfolio_value:,.2f} USDT")
        print("="*80 + "\n")
    
    def get_detailed_stats(self):
        """Get detailed statistics"""
        portfolios = self.get_all_portfolios()
        
        stats = {
            'total_value': sum(p['total_value_usdt'] for p in portfolios),
            'exchange_count': len(portfolios),
            'exchanges': {}
        }
        
        for portfolio in portfolios:
            stats['exchanges'][portfolio['exchange']] = {
                'value': portfolio['total_value_usdt'],
                'percentage': 0
            }
        
        # Calculate percentages
        if stats['total_value'] > 0:
            for exchange in stats['exchanges']:
                stats['exchanges'][exchange]['percentage'] = (
                    stats['exchanges'][exchange]['value'] / stats['total_value'] * 100
                )
        
        return stats

