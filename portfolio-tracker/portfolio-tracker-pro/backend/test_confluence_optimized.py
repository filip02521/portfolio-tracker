#!/usr/bin/env python3
"""
Optimized backtest with lower thresholds to generate trades
"""
import sys
import os
from datetime import datetime, timedelta
import logging

sys.path.insert(0, os.path.dirname(__file__))

# Enable debug logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

from confluence_strategy_service import ConfluenceStrategyService
from market_data_service import MarketDataService


def run_optimized_backtest():
    """Run backtest with optimized parameters"""
    print("🚀 Optimized Confluence Strategy Backtest")
    print("="*60)
    
    market_data_service = MarketDataService()
    service = ConfluenceStrategyService(market_data_service)
    
    # Test with lower thresholds to generate more trades
    test_configs = [
        {
            'symbol': 'BTC',
            'interval': '1d',
            'days': 365,
            'min_confluence_score': 3,  # Lower threshold
            'min_confidence': 0.6,  # Lower threshold
            'description': 'BTC 1D - Lower thresholds (3/0.6)'
        },
        {
            'symbol': 'ETH',
            'interval': '1d',
            'days': 365,
            'min_confluence_score': 3,
            'min_confidence': 0.6,
            'description': 'ETH 1D - Lower thresholds (3/0.6)'
        },
        {
            'symbol': 'BTC',
            'interval': '1d',
            'days': 365,
            'min_confluence_score': 2,  # Even lower
            'min_confidence': 0.5,
            'description': 'BTC 1D - Very low thresholds (2/0.5)'
        },
    ]
    
    for i, config in enumerate(test_configs, 1):
        print(f"\n\n{'='*60}")
        print(f"Test {i}/{len(test_configs)}: {config['description']}")
        print(f"{'='*60}")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=config['days'])
        
        try:
            result = service.backtest_confluence_strategy(
                symbol=config['symbol'],
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                initial_capital=10000.0,
                interval=config['interval'],
                risk_per_trade=0.02,
                min_confluence_score=config['min_confluence_score'],
                min_confidence=config['min_confidence']
            )
            
            if result.get('status') == 'error':
                print(f"❌ Error: {result.get('error')}")
                if 'total_historical' in result:
                    print(f"   Total historical data: {result.get('total_historical')}")
                    print(f"   Filtered data: {result.get('filtered_count')}")
                continue
            
            # Print results
            print(f"\n📊 Results:")
            print(f"   Total Return: {result.get('total_return', 0):.2f}%")
            print(f"   CAGR: {result.get('cagr', 0):.2f}%")
            print(f"   Sharpe Ratio: {result.get('sharpe_ratio', 0):.3f}")
            print(f"   Max Drawdown: {result.get('max_drawdown', 0):.2f}%")
            print(f"   Win Rate: {result.get('win_rate', 0):.2f}%")
            print(f"   Profit Factor: {result.get('profit_factor', 0):.2f}")
            print(f"   Total Trades: {result.get('total_trades', 0)}")
            print(f"   Winning: {result.get('winning_trades', 0)} / Losing: {result.get('losing_trades', 0)}")
            print(f"   Final Value: ${result.get('final_value', 10000):,.2f}")
            
            # Show first few trades
            trade_history = result.get('trade_history', [])
            if trade_history:
                print(f"\n   First 5 trades:")
                for trade in trade_history[:5]:
                    print(f"     {trade.get('date', 'N/A')[:10]} - {trade.get('action')} @ ${trade.get('price', 0):.2f}")
            
            # Profitability assessment
            total_return = result.get('total_return', 0)
            profit_factor = result.get('profit_factor', 0)
            win_rate = result.get('win_rate', 0)
            
            if total_return > 0 and profit_factor > 1.0 and win_rate > 50:
                print(f"\n   ✅ PROFITABLE")
            elif total_return > 0:
                print(f"\n   ⚠️  Shows profit but needs optimization")
            else:
                print(f"\n   ❌ NOT profitable")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            import traceback
            traceback.print_exc()
        
        import time
        time.sleep(1)


if __name__ == '__main__':
    run_optimized_backtest()


