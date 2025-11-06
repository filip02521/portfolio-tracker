#!/usr/bin/env python3
"""
Test script for VQ+ Strategy Backtesting
Tests the strategy on sample stocks to verify functionality
"""
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from fundamental_screening_service import FundamentalScreeningService
from market_data_service import MarketDataService


def run_backtest():
    """Run a sample VQ+ backtest"""
    print("="*70)
    print("VQ+ Strategy Backtest - Test Run")
    print("="*70)
    
    # Initialize services
    market_data_service = MarketDataService()
    fundamental_service = FundamentalScreeningService(market_data_service=market_data_service)
    
    # Set test parameters
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']  # Sample large-cap stocks
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)  # 1 year backtest
    
    print(f"\nTest Parameters:")
    print(f"  Symbols: {', '.join(symbols)}")
    print(f"  Start Date: {start_date.strftime('%Y-%m-%d')}")
    print(f"  End Date: {end_date.strftime('%Y-%m-%d')}")
    print(f"  Initial Capital: $100,000")
    print(f"  Rebalance Frequency: Quarterly")
    print(f"  Max Positions: 5")
    print(f"  Min F-Score: 7")
    print(f"  Min Z-Score: 3.0")
    print(f"  Max Accrual Ratio: 5.0")
    print()
    
    try:
        print("Running backtest...")
        result = fundamental_service.backtest_vq_plus_strategy(
            symbols=symbols,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            initial_capital=100000.0,
            rebalance_frequency='quarterly',
            max_positions=5,
            min_f_score=7,
            max_z_score=3.0,
            max_accrual_ratio=5.0,
            auto_universe=False,
            universe_index='SP500',
            value_percentile=0.2
        )
        
        if result.get('status') == 'error':
            print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
            return
        
        print("\n" + "="*70)
        print("BACKTEST RESULTS")
        print("="*70)
        
        # Performance Metrics
        print(f"\n📊 Performance Metrics:")
        print(f"  Total Return: {result.get('total_return', 0):.2f}%")
        print(f"  CAGR: {result.get('cagr', 0):.2f}%")
        print(f"  Sharpe Ratio: {result.get('sharpe_ratio', 0):.3f}")
        print(f"  Max Drawdown: {result.get('max_drawdown', 0):.2f}%")
        print(f"  Win Rate: {result.get('win_rate', 0):.2f}%")
        print(f"  Profit Factor: {result.get('profit_factor', 0):.2f}")
        
        # Trade Statistics
        print(f"\n📈 Trade Statistics:")
        print(f"  Total Trades: {result.get('total_trades', 0)}")
        print(f"  Winning Trades: {result.get('winning_trades', 0)}")
        print(f"  Losing Trades: {result.get('losing_trades', 0)}")
        
        # Capital
        print(f"\n💰 Capital:")
        print(f"  Initial Capital: ${result.get('initial_capital', 0):,.2f}")
        print(f"  Final Value: ${result.get('final_value', 0):,.2f}")
        
        # Rebalance Dates
        rebalance_dates = result.get('rebalance_dates', [])
        if rebalance_dates:
            print(f"\n🔄 Rebalance Dates ({len(rebalance_dates)}):")
            for date in rebalance_dates[:5]:  # Show first 5
                print(f"  - {date}")
            if len(rebalance_dates) > 5:
                print(f"  ... and {len(rebalance_dates) - 5} more")
        
        # Portfolio Compositions
        portfolio_compositions = result.get('portfolio_compositions', [])
        if portfolio_compositions:
            print(f"\n📦 Portfolio Compositions:")
            for i, comp in enumerate(portfolio_compositions[:3], 1):  # Show first 3
                print(f"\n  Rebalance {i} ({comp.get('date', 'N/A')}):")
                print(f"    Total Value: ${comp.get('total_value', 0):,.2f}")
                print(f"    Cash: ${comp.get('cash', 0):,.2f}")
                positions = comp.get('positions', [])
                if positions:
                    print(f"    Positions ({len(positions)}):")
                    for pos in positions[:5]:  # Show first 5 positions
                        symbol = pos.get('symbol', 'N/A')
                        shares = pos.get('shares', 0)
                        value = pos.get('value', 0)
                        return_pct = pos.get('return_pct', 0)
                        print(f"      {symbol}: {shares:.4f} shares, ${value:,.2f} ({return_pct:+.2f}%)")
        
        # Trade History
        trade_history = result.get('trade_history', [])
        if trade_history:
            print(f"\n📝 Trade History (showing first 10 of {len(trade_history)}):")
            for trade in trade_history[:10]:
                date = trade.get('date', 'N/A')
                action = trade.get('action', 'N/A')
                symbol = trade.get('symbol', 'N/A')
                price = trade.get('price', 0)
                shares = trade.get('shares', 0)
                value = trade.get('value', 0)
                reason = trade.get('reason', 'N/A')
                return_pct = trade.get('return_pct', None)
                
                if action == 'buy':
                    print(f"  {date} | BUY  | {symbol:6s} | ${price:8.2f} | {shares:.4f} shares | ${value:10,.2f} | {reason}")
                else:
                    profit_info = f" ({return_pct:+.2f}%)" if return_pct is not None else ""
                    print(f"  {date} | SELL | {symbol:6s} | ${price:8.2f} | {shares:.4f} shares | ${value:10,.2f}{profit_info} | {reason}")
        
        # Equity Curve
        equity_curve = result.get('equity_curve', [])
        if equity_curve:
            print(f"\n📊 Equity Curve ({len(equity_curve)} data points):")
            print(f"  First: {equity_curve[0].get('date', 'N/A')} - ${equity_curve[0].get('value', 0):,.2f}")
            print(f"  Last:  {equity_curve[-1].get('date', 'N/A')} - ${equity_curve[-1].get('value', 0):,.2f}")
            if len(equity_curve) > 2:
                print(f"  Peak:  ${max(p.get('value', 0) for p in equity_curve):,.2f}")
                print(f"  Low:   ${min(p.get('value', 0) for p in equity_curve):,.2f}")
        
        print("\n" + "="*70)
        print("Backtest completed successfully!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Exception during backtest: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    run_backtest()

