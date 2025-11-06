#!/usr/bin/env python3
"""
Demo script for VQ+ Strategy Backtesting
Runs a comprehensive backtest and displays results
"""
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from fundamental_screening_service import FundamentalScreeningService
from market_data_service import MarketDataService


def run_demo_backtest():
    """Run a demo VQ+ backtest with sample stocks"""
    print("="*80)
    print("VQ+ Strategy Backtest - Demo")
    print("="*80)
    
    # Initialize services
    print("\n🔧 Inicjalizowanie serwisów...")
    market_data_service = MarketDataService()
    fundamental_service = FundamentalScreeningService(market_data_service=market_data_service)
    
    # Demo parameters - using a smaller set of well-known stocks
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'JPM', 'JNJ', 'V']
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)  # 1 year backtest
    
    print(f"\n📊 Parametry backtestu:")
    print(f"  Symbole: {', '.join(symbols)}")
    print(f"  Okres: {start_date.strftime('%Y-%m-%d')} do {end_date.strftime('%Y-%m-%d')}")
    print(f"  Kapitał początkowy: $100,000")
    print(f"  Rebalans: Kwartalny")
    print(f"  Maksymalna liczba pozycji: 8")
    print(f"  Filtry VQ+:")
    print(f"    - Min F-Score: 6 (obniżony dla demo)")
    print(f"    - Min Z-Score: 2.0 (obniżony dla demo)")
    print(f"    - Max Accrual Ratio: 10.0")
    print()
    
    try:
        print("⏳ Uruchamianie backtestu... (to może zająć kilka minut)")
        print("-"*80)
        
        result = fundamental_service.backtest_vq_plus_strategy(
            symbols=symbols,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            initial_capital=100000.0,
            rebalance_frequency='quarterly',
            max_positions=8,
            min_f_score=6,  # Lowered for demo
            max_z_score=2.0,  # Lowered threshold
            max_accrual_ratio=10.0,  # More lenient
            auto_universe=False,
            universe_index='SP500',
            value_percentile=0.2
        )
        
        if result.get('status') == 'error':
            print(f"\n❌ Błąd backtestu: {result.get('error', 'Unknown error')}")
            return
        
        print("\n" + "="*80)
        print("WYNIKI BACKTESTU")
        print("="*80)
        
        # Performance Summary
        print(f"\n📈 Podsumowanie Wydajności:")
        print(f"  Total Return: {result.get('total_return', 0):.2f}%")
        print(f"  CAGR: {result.get('cagr', 0):.2f}%")
        print(f"  Sharpe Ratio: {result.get('sharpe_ratio', 0):.3f}")
        print(f"  Max Drawdown: {result.get('max_drawdown', 0):.2f}%")
        print(f"  Win Rate: {result.get('win_rate', 0):.2f}%")
        print(f"  Profit Factor: {result.get('profit_factor', 0):.2f}")
        
        # Capital
        print(f"\n💰 Kapitał:")
        print(f"  Początkowy: ${result.get('initial_capital', 0):,.2f}")
        print(f"  Końcowy: ${result.get('final_value', 0):,.2f}")
        profit_loss = result.get('final_value', 0) - result.get('initial_capital', 0)
        print(f"  Zysk/Strata: ${profit_loss:,.2f} ({'+' if profit_loss >= 0 else ''}{result.get('total_return', 0):.2f}%)")
        
        # Trade Statistics
        print(f"\n📊 Statystyki Transakcji:")
        print(f"  Wszystkie transakcje: {result.get('total_trades', 0)}")
        print(f"  Zyskowne: {result.get('winning_trades', 0)}")
        print(f"  Stratne: {result.get('losing_trades', 0)}")
        
        # Rebalance Dates
        rebalance_dates = result.get('rebalance_dates', [])
        if rebalance_dates:
            print(f"\n🔄 Daty Rebalansu ({len(rebalance_dates)}):")
            for date in rebalance_dates:
                print(f"  - {date}")
        
        # Portfolio Compositions
        portfolio_compositions = result.get('portfolio_compositions', [])
        if portfolio_compositions:
            print(f"\n📦 Skład Portfela:")
            for i, comp in enumerate(portfolio_compositions, 1):
                print(f"\n  Rebalance {i} ({comp.get('date', 'N/A')}):")
                print(f"    Wartość portfela: ${comp.get('total_value', 0):,.2f}")
                print(f"    Gotówka: ${comp.get('cash', 0):,.2f}")
                positions = comp.get('positions', [])
                if positions:
                    print(f"    Pozycje ({len(positions)}):")
                    for pos in positions:
                        symbol = pos.get('symbol', 'N/A')
                        shares = pos.get('shares', 0)
                        value = pos.get('value', 0)
                        return_pct = pos.get('return_pct', 0)
                        current_price = pos.get('current_price', 0)
                        entry_price = pos.get('entry_price', 0)
                        print(f"      {symbol}: {shares:.4f} shares @ ${current_price:.2f} = ${value:,.2f} ({return_pct:+.2f}%) [entry: ${entry_price:.2f}]")
                else:
                    print(f"    Brak pozycji")
        
        # Trade History (summary)
        trade_history = result.get('trade_history', [])
        if trade_history:
            print(f"\n📝 Historia Transakcji (wszystkie {len(trade_history)} transakcji):")
            print(f"\n  BUY ({len([t for t in trade_history if t.get('action') == 'buy'])}):")
            buy_trades = [t for t in trade_history if t.get('action') == 'buy']
            for trade in buy_trades[:10]:  # Show first 10
                date = trade.get('date', 'N/A')
                symbol = trade.get('symbol', 'N/A')
                price = trade.get('price', 0)
                shares = trade.get('shares', 0)
                value = trade.get('value', 0)
                print(f"    {date} | {symbol:6s} | ${price:8.2f} | {shares:.4f} shares | ${value:10,.2f}")
            
            print(f"\n  SELL ({len([t for t in trade_history if t.get('action') == 'sell'])}):")
            sell_trades = [t for t in trade_history if t.get('action') == 'sell']
            for trade in sell_trades[:10]:  # Show first 10
                date = trade.get('date', 'N/A')
                symbol = trade.get('symbol', 'N/A')
                price = trade.get('price', 0)
                shares = trade.get('shares', 0)
                value = trade.get('value', 0)
                return_pct = trade.get('return_pct', None)
                profit = trade.get('profit', 0)
                profit_str = f" | Profit: ${profit:,.2f} ({return_pct:+.2f}%)" if return_pct is not None else ""
                print(f"    {date} | {symbol:6s} | ${price:8.2f} | {shares:.4f} shares | ${value:10,.2f}{profit_str}")
            
            if len(trade_history) > 20:
                print(f"    ... i {len(trade_history) - 20} więcej transakcji")
        
        # Equity Curve Summary
        equity_curve = result.get('equity_curve', [])
        if equity_curve:
            print(f"\n📊 Krzywa Kapitału ({len(equity_curve)} punktów):")
            if len(equity_curve) > 0:
                first_value = equity_curve[0].get('value', 0)
                last_value = equity_curve[-1].get('value', 0)
                max_value = max(p.get('value', 0) for p in equity_curve)
                min_value = min(p.get('value', 0) for p in equity_curve)
                
                print(f"  Start: ${first_value:,.2f} ({equity_curve[0].get('date', 'N/A')})")
                print(f"  Koniec: ${last_value:,.2f} ({equity_curve[-1].get('date', 'N/A')})")
                print(f"  Maksimum: ${max_value:,.2f}")
                print(f"  Minimum: ${min_value:,.2f}")
                print(f"  Zmiana: ${last_value - first_value:,.2f} ({((last_value - first_value) / first_value * 100) if first_value > 0 else 0:.2f}%)")
        
        # Parameters used
        params = result.get('parameters', {})
        if params:
            print(f"\n⚙️  Użyte Parametry:")
            for key, value in params.items():
                print(f"  {key}: {value}")
        
        print("\n" + "="*80)
        print("✅ Backtest zakończony pomyślnie!")
        print("="*80)
        
        # Recommendations
        print(f"\n💡 Rekomendacje:")
        if result.get('total_return', 0) > 0:
            print(f"  ✅ Strategia wygenerowała dodatni zwrot: {result.get('total_return', 0):.2f}%")
        else:
            print(f"  ⚠️  Strategia wygenerowała ujemny zwrot: {result.get('total_return', 0):.2f}%")
        
        if result.get('sharpe_ratio', 0) > 1.0:
            print(f"  ✅ Sharpe Ratio > 1.0 - dobra relacja zysk/ryzyko")
        elif result.get('sharpe_ratio', 0) > 0:
            print(f"  ⚠️  Sharpe Ratio > 0 ale < 1.0 - strategia jest dodatnia ale z niższym zwrotem")
        else:
            print(f"  ❌ Sharpe Ratio <= 0 - strategia nie generuje pozytywnego zwrotu skorygowanego o ryzyko")
        
        if result.get('win_rate', 0) > 50:
            print(f"  ✅ Win Rate > 50% - większość transakcji jest zyskowna")
        else:
            print(f"  ⚠️  Win Rate < 50% - większość transakcji jest stratna")
        
        if result.get('max_drawdown', 0) < 20:
            print(f"  ✅ Max Drawdown < 20% - akceptowalny poziom ryzyka")
        else:
            print(f"  ⚠️  Max Drawdown > 20% - wysoki poziom ryzyka")
        
    except Exception as e:
        print(f"\n❌ Błąd podczas backtestu: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    run_demo_backtest()

