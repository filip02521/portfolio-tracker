#!/usr/bin/env python3
"""Test return calculation in VQ+ backtest"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fundamental_screening_service import FundamentalScreeningService
from market_data_service import MarketDataService
from datetime import datetime, timedelta

def test_return_calculation():
    """Test that return percentages are calculated correctly"""
    market_data_service = MarketDataService()
    service = FundamentalScreeningService(market_data_service=market_data_service)
    
    # Test with a simple scenario
    symbols = ['GOOGL']  # Single symbol for easier debugging
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"Testing VQ+ backtest return calculation...")
    print(f"Symbols: {symbols}")
    print(f"Start: {start_date}, End: {end_date}")
    print("=" * 80)
    
    try:
        result = service.backtest_vq_plus_strategy(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            initial_capital=100000.0,
            rebalance_frequency='quarterly',
            max_positions=1,
            min_f_score=6,  # Lower threshold for testing
            max_z_score=2.0,
            max_accrual_ratio=10.0
        )
        
        if result.get('status') == 'error':
            print(f"❌ Backtest failed: {result.get('error')}")
            return
        
        print(f"\n✅ Backtest completed successfully!")
        print(f"\n📊 Performance Metrics:")
        print(f"  Total Return: {result.get('total_return', 0):.2f}%")
        print(f"  CAGR: {result.get('cagr', 0):.2f}%")
        print(f"  Sharpe Ratio: {result.get('sharpe_ratio', 0):.3f}")
        print(f"  Max Drawdown: {result.get('max_drawdown', 0):.2f}%")
        print(f"  Win Rate: {result.get('win_rate', 0):.2f}%")
        print(f"  Profit Factor: {result.get('profit_factor', 0):.2f}")
        print(f"  Total Trades: {result.get('total_trades', 0)}")
        
        # Check trade history
        trade_history = result.get('trade_history', [])
        print(f"\n📈 Trade History ({len(trade_history)} trades):")
        for i, trade in enumerate(trade_history[:10], 1):
            action = trade.get('action', '').upper()
            symbol = trade.get('symbol', '')
            price = trade.get('price', 0)
            shares = trade.get('shares', 0)
            value = trade.get('value', 0)
            return_pct = trade.get('return_pct')
            profit = trade.get('profit')
            entry_price = trade.get('entry_price')
            
            print(f"  {i}. {action} {symbol} @ ${price:.2f}, {shares:.4f} shares, ${value:,.2f}")
            if return_pct is not None:
                print(f"      Return: {return_pct:+.2f}%, Profit: ${profit:,.2f}" if profit else f"      Return: {return_pct:+.2f}%")
            if entry_price:
                print(f"      Entry: ${entry_price:.2f}")
        
        # Verify return calculations
        print(f"\n🔍 Verification:")
        sell_trades = [t for t in trade_history if t.get('action') == 'sell']
        print(f"  Sell trades: {len(sell_trades)}")
        
        for trade in sell_trades:
            entry_price = trade.get('entry_price')
            exit_price = trade.get('price')
            return_pct = trade.get('return_pct')
            profit = trade.get('profit')
            
            if entry_price and exit_price:
                expected_return = ((exit_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
                expected_profit = (exit_price - entry_price) * trade.get('shares', 0)
                
                print(f"  {trade.get('symbol')}: Entry=${entry_price:.2f}, Exit=${exit_price:.2f}")
                print(f"    Expected Return: {expected_return:.2f}%, Actual: {return_pct:.2f}%")
                print(f"    Expected Profit: ${expected_profit:,.2f}, Actual: ${profit:,.2f}")
                
                if abs(expected_return - (return_pct or 0)) > 0.01:
                    print(f"    ⚠️  RETURN MISMATCH!")
                if abs(expected_profit - (profit or 0)) > 0.01:
                    print(f"    ⚠️  PROFIT MISMATCH!")
        
        # Check equity curve
        equity_curve = result.get('equity_curve', [])
        if equity_curve:
            print(f"\n📉 Equity Curve:")
            print(f"  Start: ${equity_curve[0].get('value', 0):,.2f}")
            print(f"  End: ${equity_curve[-1].get('value', 0):,.2f}")
            calculated_return = ((equity_curve[-1].get('value', 0) - equity_curve[0].get('value', 0)) / equity_curve[0].get('value', 0) * 100) if equity_curve[0].get('value', 0) > 0 else 0
            print(f"  Calculated Return: {calculated_return:.2f}%")
            print(f"  Reported Return: {result.get('total_return', 0):.2f}%")
            
            if abs(calculated_return - result.get('total_return', 0)) > 0.01:
                print(f"  ⚠️  EQUITY CURVE RETURN MISMATCH!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_return_calculation()

