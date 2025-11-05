#!/usr/bin/env python3
"""
Extended backtest with large dataset and larger intervals
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


def run_extended_backtest():
    """Run extended backtest with large dataset and larger intervals"""
    print("🚀 Extended Confluence Strategy Backtest")
    print("="*60)
    print("Large dataset (730 days) + Larger intervals (4h, 1d)")
    print("="*60)
    
    market_data_service = MarketDataService()
    service = ConfluenceStrategyService(market_data_service)
    
    # Extended test configurations with larger intervals and more data
    test_configs = [
        {
            'symbol': 'BTC',
            'interval': '4h',
            'days': 730,  # 2 years
            'min_confluence_score': 3,
            'min_confidence': 0.6,
            'description': 'BTC 4H - 2 years (730 days)'
        },
        {
            'symbol': 'BTC',
            'interval': '1d',
            'days': 730,  # 2 years
            'min_confluence_score': 3,
            'min_confidence': 0.6,
            'description': 'BTC 1D - 2 years (730 days)'
        },
        {
            'symbol': 'ETH',
            'interval': '4h',
            'days': 730,  # 2 years
            'min_confluence_score': 3,
            'min_confidence': 0.6,
            'description': 'ETH 4H - 2 years (730 days)'
        },
        {
            'symbol': 'ETH',
            'interval': '1d',
            'days': 730,  # 2 years
            'min_confluence_score': 3,
            'min_confidence': 0.6,
            'description': 'ETH 1D - 2 years (730 days)'
        },
        {
            'symbol': 'BTC',
            'interval': '1d',
            'days': 365,  # 1 year with lower thresholds
            'min_confluence_score': 2,
            'min_confidence': 0.5,
            'description': 'BTC 1D - 1 year, lower thresholds (2/0.5)'
        },
    ]
    
    results = []
    
    for i, config in enumerate(test_configs, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}/{len(test_configs)}: {config['description']}")
        print(f"{'='*60}")
        
        try:
            # Calculate start_date from days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=config['days'])
            
            result = service.backtest_confluence_strategy(
                symbol=config['symbol'],
                interval=config['interval'],
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                initial_capital=10000,
                min_confluence_score=config['min_confluence_score'],
                min_confidence=config['min_confidence'],
                risk_per_trade=0.02
            )
            
            if result.get('status') == 'success':
                print(f"\n📊 Results:")
                print(f"   Total Return: {result['total_return']:.2f}%")
                print(f"   CAGR: {result['cagr']:.2f}%")
                print(f"   Sharpe Ratio: {result['sharpe_ratio']:.3f}")
                print(f"   Max Drawdown: {result['max_drawdown']:.2f}%")
                print(f"   Win Rate: {result['win_rate']:.2f}%")
                print(f"   Profit Factor: {result['profit_factor']:.2f}")
                print(f"   Total Trades: {result['total_trades']}")
                print(f"   Winning: {result['winning_trades']} / Losing: {result['losing_trades']}")
                print(f"   Final Value: ${result['final_value']:,.2f}")
                
                if result['total_trades'] > 0:
                    avg_return = result['total_return'] / result['total_trades'] if result['total_trades'] > 0 else 0
                    print(f"   Avg Return per Trade: {avg_return:.2f}%")
                
                # Show first 5 trades
                if result.get('trade_history'):
                    print(f"\n   First 5 trades:")
                    for trade in result['trade_history'][:5]:
                        action = trade.get('action', 'unknown')
                        price = trade.get('price', 0)
                        date = trade.get('date', 'unknown')
                        shares = trade.get('shares', 0)
                        value = trade.get('value', 0)
                        reason = trade.get('reason', '')
                        return_pct = trade.get('return_pct', 0)
                        
                        if action == 'buy':
                            print(f"     {date} - {action} @ ${price:.2f}, shares={shares:.4f}, value=${value:.2f}")
                        else:
                            print(f"     {date} - {action} @ ${price:.2f}, shares={shares:.4f}, value=${value:.2f}, return={return_pct:.2f}% ({reason})")
                
                # Determine if profitable
                if result['total_return'] > 0 and result['win_rate'] > 50:
                    print(f"\n   ✅ PROFITABLE with good win rate")
                elif result['total_return'] > 0:
                    print(f"\n   ⚠️  Shows profit but needs optimization")
                else:
                    print(f"\n   ❌ NOT profitable")
                
                results.append({
                    'config': config,
                    'result': result
                })
            else:
                print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"\n❌ Exception: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print(f"\n{'='*60}")
    print("📈 SUMMARY")
    print(f"{'='*60}")
    
    profitable_count = sum(1 for r in results if r['result'].get('total_return', 0) > 0)
    total_trades = sum(r['result'].get('total_trades', 0) for r in results)
    avg_return = sum(r['result'].get('total_return', 0) for r in results) / len(results) if results else 0
    avg_win_rate = sum(r['result'].get('win_rate', 0) for r in results) / len(results) if results else 0
    
    print(f"Total Tests: {len(results)}")
    print(f"Profitable: {profitable_count}/{len(results)}")
    print(f"Total Trades Across All Tests: {total_trades}")
    print(f"Average Return: {avg_return:.2f}%")
    print(f"Average Win Rate: {avg_win_rate:.2f}%")
    
    # Best performing test
    if results:
        best = max(results, key=lambda x: x['result'].get('total_return', 0))
        print(f"\n🏆 Best Performing Test:")
        print(f"   {best['config']['description']}")
        print(f"   Return: {best['result']['total_return']:.2f}%")
        print(f"   Win Rate: {best['result']['win_rate']:.2f}%")
        print(f"   Trades: {best['result']['total_trades']}")


if __name__ == '__main__':
    run_extended_backtest()

