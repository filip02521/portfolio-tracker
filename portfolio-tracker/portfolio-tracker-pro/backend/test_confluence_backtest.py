#!/usr/bin/env python3
"""
Test script for Confluence Strategy Backtesting
Tests the strategy on multiple symbols and intervals to verify profitability
"""
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from confluence_strategy_service import ConfluenceStrategyService
from market_data_service import MarketDataService


def run_backtest(
    service: ConfluenceStrategyService,
    symbol: str,
    interval: str,
    days: int = 90,
    initial_capital: float = 10000.0,
    risk_per_trade: float = 0.02,
    min_confluence_score: int = 4,
    min_confidence: float = 0.7
):
    """Run a single backtest and return results"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        print(f"\n{'='*60}")
        print(f"Backtesting {symbol} on {interval} interval")
        print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"Parameters: min_confluence={min_confluence_score}, min_confidence={min_confidence}")
        print(f"{'='*60}")
        
        result = service.backtest_confluence_strategy(
            symbol=symbol,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            initial_capital=initial_capital,
            interval=interval,
            risk_per_trade=risk_per_trade,
            min_confluence_score=min_confluence_score,
            min_confidence=min_confidence
        )
        
        if result.get('status') == 'error':
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
            return None
        
        return result
    except Exception as e:
        print(f"❌ Exception during backtest: {e}")
        import traceback
        traceback.print_exc()
        return None


def print_results(result, symbol: str, interval: str):
    """Print formatted backtest results"""
    if not result:
        return
    
    print(f"\n📊 Results for {symbol} ({interval}):")
    print(f"{'-'*60}")
    
    # Key metrics
    total_return = result.get('total_return', 0)
    cagr = result.get('cagr', 0)
    sharpe = result.get('sharpe_ratio', 0)
    max_dd = result.get('max_drawdown', 0)
    win_rate = result.get('win_rate', 0)
    profit_factor = result.get('profit_factor', 0)
    total_trades = result.get('total_trades', 0)
    winning_trades = result.get('winning_trades', 0)
    losing_trades = result.get('losing_trades', 0)
    
    initial = result.get('initial_capital', 10000)
    final = result.get('final_value', initial)
    
    # Format output
    print(f"💰 Total Return:      {total_return:>7.2f}%")
    print(f"📈 CAGR:              {cagr:>7.2f}%")
    print(f"📊 Sharpe Ratio:      {sharpe:>7.3f}")
    print(f"📉 Max Drawdown:      {max_dd:>7.2f}%")
    print(f"🎯 Win Rate:          {win_rate:>7.2f}%")
    print(f"💵 Profit Factor:     {profit_factor:>7.2f}")
    print(f"🔢 Total Trades:      {total_trades:>7d}")
    print(f"✅ Winning Trades:    {winning_trades:>7d}")
    print(f"❌ Losing Trades:     {losing_trades:>7d}")
    print(f"💼 Initial Capital:   ${initial:>10,.2f}")
    print(f"💼 Final Value:       ${final:>10,.2f}")
    print(f"💵 Net Profit/Loss:   ${final - initial:>10,.2f}")
    
    # Profitability assessment
    print(f"\n{'='*60}")
    if total_return > 0 and profit_factor > 1.0 and win_rate > 50:
        print("✅ Strategy is PROFITABLE")
    elif total_return > 0:
        print("⚠️  Strategy shows profit but may need optimization")
    else:
        print("❌ Strategy is NOT profitable - needs optimization")
    print(f"{'='*60}")


def main():
    """Main function to run comprehensive backtests"""
    print("🚀 Starting Confluence Strategy Backtest Suite")
    print("="*60)
    
    # Initialize services
    try:
        market_data_service = MarketDataService()
        confluence_service = ConfluenceStrategyService(market_data_service)
        print("✅ Services initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize services: {e}")
        return
    
    # Test configurations
    test_configs = [
        {
            'symbol': 'BTC',
            'interval': '4h',
            'days': 180,
            'min_confluence_score': 4,
            'min_confidence': 0.7
        },
        {
            'symbol': 'ETH',
            'interval': '4h',
            'days': 180,
            'min_confluence_score': 4,
            'min_confidence': 0.7
        },
        {
            'symbol': 'SOL',
            'interval': '4h',
            'days': 180,
            'min_confluence_score': 4,
            'min_confidence': 0.7
        },
        {
            'symbol': 'BTC',
            'interval': '1d',
            'days': 365,
            'min_confluence_score': 4,
            'min_confidence': 0.7
        },
        {
            'symbol': 'ETH',
            'interval': '1d',
            'days': 365,
            'min_confluence_score': 4,
            'min_confidence': 0.7
        },
        # Test with lower thresholds to get more trades
        {
            'symbol': 'BTC',
            'interval': '4h',
            'days': 180,
            'min_confluence_score': 3,
            'min_confidence': 0.6
        },
    ]
    
    results = []
    
    for i, config in enumerate(test_configs, 1):
        print(f"\n\n🔍 Test {i}/{len(test_configs)}")
        
        result = run_backtest(
            service=confluence_service,
            symbol=config['symbol'],
            interval=config['interval'],
            days=config['days'],
            min_confluence_score=config['min_confluence_score'],
            min_confidence=config['min_confidence']
        )
        
        if result:
            print_results(result, config['symbol'], config['interval'])
            results.append({
                'config': config,
                'result': result
            })
        
        # Small delay to avoid rate limiting
        import time
        time.sleep(1)
    
    # Summary
    print("\n\n" + "="*60)
    print("📋 SUMMARY")
    print("="*60)
    
    if not results:
        print("❌ No successful backtests completed")
        return
    
    profitable = 0
    total_return_sum = 0
    total_trades_sum = 0
    
    for item in results:
        config = item['config']
        result = item['result']
        
        total_return = result.get('total_return', 0)
        total_trades = result.get('total_trades', 0)
        
        if total_return > 0:
            profitable += 1
        
        total_return_sum += total_return
        total_trades_sum += total_trades
        
        status = "✅" if total_return > 0 else "❌"
        print(f"{status} {config['symbol']} ({config['interval']}, {config['days']}d): "
              f"{total_return:>7.2f}% return, {total_trades} trades")
    
    print(f"\n{'='*60}")
    print(f"Profitable tests: {profitable}/{len(results)}")
    print(f"Average return: {total_return_sum / len(results):.2f}%")
    print(f"Total trades across all tests: {total_trades_sum}")
    print(f"{'='*60}")
    
    if profitable >= len(results) * 0.6:  # 60% profitable
        print("\n✅ Strategy shows overall profitability")
    elif profitable >= len(results) * 0.4:  # 40% profitable
        print("\n⚠️  Strategy shows mixed results - optimization recommended")
    else:
        print("\n❌ Strategy needs significant optimization")


if __name__ == '__main__':
    main()


