"""
Auto-sync transaction history from exchange APIs
"""
from transaction_history import TransactionHistory
from exchanges.binance_client import BinanceClient
from exchanges.bybit_client import BybitClient
from datetime import datetime, timedelta

def sync_binance_transactions():
    """Sync transactions from Binance API"""
    try:
        print("🔄 Próba połączenia z Binance...")
        client = BinanceClient()
        print("✅ Połączenie z Binance nawiązane")
        
        history = TransactionHistory()
        
        # Get balances
        balances = client.get_balances()
        print(f"📊 Znaleziono {len(balances)} aktywów na Binance")
        
        if not balances:
            print("⚠️ Brak aktywów na Binance")
            return True
        
        added_count = 0
        
        # Try multiple quote currencies
        quote_currencies = ['USDT', 'USDC', 'BUSD', 'FDUSD']
        
        for balance in balances:
            asset = balance['asset']
            
            # Skip stablecoins
            if asset in ['USDT', 'BUSD', 'FDUSD', 'USDC']:
                continue
            
            # Skip locked deposits and similar products
            if asset.startswith('LD'):
                continue
            
            # Try each quote currency and collect ALL trades
            all_grouped_trades = {}
            
            for quote in quote_currencies:
                symbol = asset + quote
                try:
                    print(f"📈 Pobieranie historii dla {symbol}...")
                    trades = client.get_trade_history(symbol=symbol, limit=500)
                    
                    if not trades:
                        continue
                    
                    print(f"  ✅ Znaleziono {len(trades)} części transakcji")
                    
                    # Group trades by orderId (same order can have multiple parts)
                    from collections import defaultdict
                    grouped_trades = defaultdict(list)
                    
                    for trade in trades:
                        order_id = trade.get('orderId', 0)
                        if order_id:
                            grouped_trades[order_id].append(trade)
                    
                    # Merge with all_grouped_trades
                    for order_id, order_trades in grouped_trades.items():
                        if order_id not in all_grouped_trades:
                            all_grouped_trades[order_id] = []
                        all_grouped_trades[order_id].extend(order_trades)
                    
                except Exception as e:
                    # Symbol doesn't exist, try next quote currency
                    continue
            
            if all_grouped_trades:
                print(f"  📋 Pogrupowano w {len(all_grouped_trades)} transakcji")
                
                for order_id, order_trades in all_grouped_trades.items():
                    try:
                        # Get details from first trade
                        first_trade = order_trades[0]
                        trade_time = datetime.fromtimestamp(first_trade['time'] / 1000).isoformat()
                        
                        # Aggregate all parts
                        total_qty = sum(float(t['qty']) for t in order_trades)
                        total_quote_qty = sum(float(t['quoteQty']) for t in order_trades)
                        
                        # Calculate average price
                        avg_price = total_quote_qty / total_qty if total_qty > 0 else 0
                        
                        is_buyer = first_trade['isBuyer']
                        
                        # Check if transaction already exists
                        existing = [t for t in history.transactions 
                                   if t['exchange'] == 'Binance' 
                                   and t['asset'] == asset
                                   and abs(float(t['amount']) - total_qty) < 0.0001]
                        
                        if not existing:
                            history.add_transaction(
                                exchange='Binance',
                                asset=asset,
                                amount=total_qty,
                                price_usd=avg_price,
                                transaction_type='buy' if is_buyer else 'sell',
                                date=trade_time
                            )
                            added_count += 1
                            print(f"  ✅ Dodano transakcję: {asset} ({'buy' if is_buyer else 'sell'}) {total_qty:.5f} @ ${avg_price:.2f}")
                    except Exception as e:
                        print(f"  ❌ Błąd przetwarzania transakcji Binance: {e}")
            else:
                print(f"  ⚠️ Brak historii dla {asset}")
        
        print(f"\n🎉 Łącznie dodano {added_count} nowych transakcji z Binance")
        return True
    except Exception as e:
        print(f"❌ Błąd synchronizacji Binance: {e}")
        return False

def sync_bybit_transactions():
    """Sync transactions from Bybit API"""
    try:
        print("🔄 Próba połączenia z Bybit...")
        client = BybitClient()
        print("✅ Połączenie z Bybit nawiązane")
        
        history = TransactionHistory()
        
        # Get recent execution list
        print(f"📈 Pobieranie historii transakcji z Bybit...")
        executions = client.get_trade_history(limit=200)
        print(f"📊 Znaleziono {len(executions)} egzekucji z Bybit")
        
        if not executions:
            print("⚠️ Brak transakcji na Bybit")
            return True
        
        # Group executions by orderId (same order can have multiple executions)
        from collections import defaultdict
        grouped_executions = defaultdict(list)
        
        for execution in executions:
            order_id = execution.get('orderId', '')
            if order_id:
                grouped_executions[order_id].append(execution)
        
        print(f"📋 Pogrupowano w {len(grouped_executions)} transakcji")
        
        added_count = 0
        
        for order_id, order_executions in grouped_executions.items():
            try:
                # Get symbol from first execution
                symbol = order_executions[0].get('symbol', '')
                if not symbol:
                    continue
                
                # Extract asset from symbol (remove USDT suffix)
                asset = symbol.replace('USDT', '').replace('USD', '')
                if not asset or asset == 'USDT':
                    continue
                
                # Aggregate all executions for this order
                total_qty = sum(float(e.get('execQty', 0)) for e in order_executions)
                total_value = sum(float(e.get('execValue', 0)) for e in order_executions)
                
                # Calculate average price
                avg_price = total_value / total_qty if total_qty > 0 else 0
                
                # Get details from first execution
                exec_time = int(order_executions[0].get('execTime', 0))
                side = order_executions[0].get('side', '')
                
                if total_qty <= 0 or avg_price <= 0:
                    continue
                
                # Convert timestamp to ISO format
                trade_time = datetime.fromtimestamp(exec_time / 1000).isoformat()
                
                # Check if transaction already exists (by orderId stored in description or unique timestamp)
                existing = [t for t in history.transactions 
                           if t['exchange'] == 'Bybit' 
                           and t['asset'] == asset
                           and abs(float(t['amount']) - total_qty) < 0.0001]  # Allow small rounding differences
                
                if not existing:
                    history.add_transaction(
                        exchange='Bybit',
                        asset=asset,
                        amount=total_qty,
                        price_usd=avg_price,
                        transaction_type='buy' if side == 'Buy' else 'sell',
                        date=trade_time
                    )
                    added_count += 1
                    print(f"  ✅ Dodano transakcję: {asset} ({side}) {total_qty:.5f} @ ${avg_price:.2f}")
                    
            except Exception as e:
                print(f"  ❌ Błąd przetwarzania transakcji Bybit: {e}")
        
        print(f"\n🎉 Łącznie dodano {added_count} nowych transakcji z Bybit")
        return True
    except Exception as e:
        print(f"❌ Błąd synchronizacji Bybit: {e}")
        return False

def sync_all_transactions():
    """Sync transactions from all exchanges with better error handling"""
    print("🚀 Rozpoczynam synchronizację historii transakcji...")
    print("=" * 60)
    
    binance_ok = False
    bybit_ok = False
    
    # Try Binance with error handling
    try:
        print("\n📊 === BINANCE ===")
        binance_ok = sync_binance_transactions()
    except Exception as e:
        print(f"❌ Binance sync failed completely: {e}")
        binance_ok = False
    
    # Try Bybit with error handling
    try:
        print("\n📊 === BYBIT ===")
        bybit_ok = sync_bybit_transactions()
    except Exception as e:
        print(f"❌ Bybit sync failed completely: {e}")
        bybit_ok = False
    
    print("\n" + "=" * 60)
    print("📋 PODSUMOWANIE SYNCHRONIZACJI:")
    print(f"Binance: {'✅ OK' if binance_ok else '❌ Błąd'}")
    print(f"Bybit: {'✅ OK' if bybit_ok else '❌ Błąd'}")
    
    if not (binance_ok or bybit_ok):
        print("\n⚠️ Wszystkie synchronizacje zakończyły się niepowodzeniem.")
        print("Możliwe przyczyny:")
        print("- Problemy z połączeniem internetowym")
        print("- Ograniczenia geograficzne API")
        print("- Nieprawidłowe klucze API")
        print("- Przekroczenie limitów API")
        print("\n💡 Spróbuj ponownie później lub skontaktuj się z pomocą techniczną.")
    else:
        print(f"\n🎉 Synchronizacja zakończona! {'Binance' if binance_ok else ''} {'Bybit' if bybit_ok else ''}")
    
    return binance_ok or bybit_ok

if __name__ == "__main__":
    sync_all_transactions()

