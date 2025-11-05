#!/usr/bin/env python3
"""
Detailed test of confluence strategy entry signals
Tests if signals are being generated at all
"""
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from confluence_strategy_service import ConfluenceStrategyService
from market_data_service import MarketDataService
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

def test_entry_signals():
    """Test entry signal generation"""
    print("🔍 Testing Entry Signal Generation")
    print("="*60)
    
    market_data_service = MarketDataService()
    service = ConfluenceStrategyService(market_data_service)
    
    symbols = ['BTC', 'ETH', 'SOL']
    intervals = ['4h', '1d']
    
    for symbol in symbols:
        for interval in intervals:
            print(f"\n📊 Testing {symbol} on {interval} interval")
            print("-"*60)
            
            try:
                result = service.analyze_entry_signals(
                    symbol=symbol,
                    interval=interval,
                    timeframe=interval
                )
                
                print(f"Entry Signal: {result.get('entry_signal')}")
                print(f"Confluence Score: {result.get('confluence_score')}/6")
                print(f"Confidence: {result.get('confidence', 0):.2%}")
                print(f"Entry Price: ${result.get('entry_price', 0):.2f}")
                print(f"Risk Level: {result.get('risk_level')}")
                
                if result.get('error'):
                    print(f"❌ Error: {result.get('error')}")
                
                conditions = result.get('confluence_conditions', [])
                print(f"\nConfluence Conditions:")
                for cond in conditions[:3]:  # Show first 3
                    print(f"  {cond}")
                
            except Exception as e:
                print(f"❌ Exception: {e}")
                import traceback
                traceback.print_exc()

if __name__ == '__main__':
    test_entry_signals()

