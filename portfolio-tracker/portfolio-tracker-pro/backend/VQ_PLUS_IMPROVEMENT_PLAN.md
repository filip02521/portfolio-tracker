# Plan Usprawnień i Napraw VQ+ Backtest Strategy

## 📋 Cel
Zoptymalizować i naprawić VQ+ Backtest Strategy, aby zapewnić dokładne, wiarygodne wyniki backtestów zgodne z raportem eksperckim.

---

## 🔍 Analiza Obecnego Stanu

### ✅ Co działa dobrze:
1. **Podstawowa struktura backtestu** - logika rebalansowania działa
2. **Pobieranie danych historycznych** - wsparcie dla okresów do 5 lat
3. **Zamykanie pozycji** - prawidłowe obliczanie zysków/strat
4. **Metryki wydajności** - CAGR, Sharpe Ratio, Max Drawdown
5. **Equity Curve** - wizualizacja wartości portfela w czasie

### ⚠️ Zidentyfikowane Problemy:

#### 1. **Dokładność danych fundamentalnych w czasie**
   - Problem: `screen_vq_plus_strategy` używa obecnych danych fundamentalnych, nie historycznych
   - Wpływ: Backtest może używać przyszłych danych do decyzji z przeszłości
   - Rozwiązanie: Implementacja `get_fundamental_data_historical` z prawdziwymi danymi z danego okresu

#### 2. **Brak cache'owania danych fundamentalnych**
   - Problem: Każde wywołanie `screen_vq_plus_strategy` pobiera dane na nowo
   - Wpływ: Wolne backtesty, potencjalne rate limits
   - Rozwiązanie: Cache dla danych fundamentalnych na każdą datę rebalance

#### 3. **Obsługa brakujących danych cenowych**
   - Problem: `_get_historical_price` może zwrócić `None`, co przerywa backtest
   - Wpływ: Błędy w backtestach dla symboli z lukami w danych
   - Rozwiązanie: Lepsze fallbacki i interpolacja cen

#### 4. **Brak walidacji danych wejściowych**
   - Problem: Brak sprawdzania poprawności dat, symboli, parametrów
   - Wpływ: Błędy runtime zamiast jasnych komunikatów
   - Rozwiązanie: Walidacja na początku `backtest_vq_plus_strategy`

#### 5. **Niespójne rebalansowanie**
   - Problem: Jeśli screening nie zwraca akcji, wszystkie pozycje są zamykane
   - Wpływ: Niepotrzebne transakcje, zwiększone koszty (jeśli dodamy)
   - Rozwiązanie: Opcja "hold if no new candidates" zamiast zamykania wszystkich

#### 6. **Brak kosztów transakcyjnych**
   - Problem: Backtest nie uwzględnia kosztów transakcji
   - Wpływ: Nierrealistyczne wyniki (zawyżone)
   - Rozwiązanie: Parametr `transaction_cost` (np. 0.1% per trade)

#### 7. **Brak sprawdzania płynności**
   - Problem: Backtest może kupować akcje z niską płynnością
   - Wpływ: Nierrealistyczne ceny wykonania
   - Rozwiązanie: Filtr minimalnego dziennego wolumenu

#### 8. **Niedokładne daty rebalance**
   - Problem: Rebalance może przypaść na weekend/święto
   - Wpływ: Brak danych cenowych w dniu rebalance
   - Rozwiązanie: Automatyczne przesunięcie na najbliższy dzień handlowy

#### 9. **Brak walidacji danych fundamentalnych**
   - Problem: Jeśli dane fundamentalne są nieprawidłowe (np. ujemne aktywa), metryki są błędne
   - Wpływ: Nieprawidłowe screeningi
   - Rozwiązanie: Walidacja danych przed użyciem w metrykach

#### 10. **Brak równoległego przetwarzania**
   - Problem: Screening dla każdego symbolu jest sekwencyjny
   - Wpływ: Wolne backtesty dla dużych uniwersów
   - Rozwiązanie: Użycie `concurrent.futures` dla równoległego pobierania danych

---

## 🎯 Priorytety Usprawnień

### Priorytet 1: Krytyczne (Wpływ na dokładność)
1. ✅ **Dane fundamentalne w czasie** - Użycie historycznych danych fundamentalnych
2. ✅ **Walidacja danych wejściowych** - Sprawdzanie poprawności dat, symboli
3. ✅ **Obsługa brakujących danych** - Lepsze fallbacki dla cen i danych fundamentalnych
4. ✅ **Daty rebalance** - Przesunięcie na dni handlowe

### Priorytet 2: Ważne (Wpływ na realizm)
5. ✅ **Koszty transakcyjne** - Uwzględnienie kosztów transakcji
6. ✅ **Filtr płynności** - Sprawdzanie minimalnego wolumenu
7. ✅ **Walidacja danych fundamentalnych** - Sprawdzanie poprawności wartości

### Priorytet 3: Optymalizacja (Wpływ na wydajność)
8. ✅ **Cache danych fundamentalnych** - Cache'owanie danych dla dat rebalance
9. ✅ **Równoległe przetwarzanie** - Równoległe pobieranie danych dla wielu symboli
10. ✅ **Optymalizacja zapytań API** - Batch requests gdzie możliwe

---

## 📝 Szczegółowy Plan Implementacji

### 1. Dane fundamentalne w czasie (Priorytet 1)

**Problem**: Obecnie `screen_vq_plus_strategy` używa `get_fundamental_data`, które zwraca najnowsze dane, nie historyczne.

**Rozwiązanie**:
- Użyć `get_fundamental_data_historical` w backtestach
- Jeśli nie dostępne, użyć najbliższych dostępnych danych (nie przyszłych)
- Dodać parametr `as_of_date` do `get_fundamental_data`

**Implementacja**:
```python
def screen_vq_plus_strategy(self, ..., as_of_date: datetime = None):
    # Use historical data if as_of_date is provided
    if as_of_date:
        fundamental_data = self.get_fundamental_data_historical(symbol, as_of_date)
    else:
        fundamental_data = self.get_fundamental_data(symbol)
```

### 2. Walidacja danych wejściowych (Priorytet 1)

**Implementacja**:
```python
# Validate dates
if start_date >= end_date:
    raise ValueError("start_date must be before end_date")
if (end_date - start_date).days > 3650:  # 10 years max
    raise ValueError("Backtest period cannot exceed 10 years")

# Validate symbols
if symbols and not isinstance(symbols, list):
    raise ValueError("symbols must be a list")
if symbols and len(symbols) == 0:
    raise ValueError("symbols list cannot be empty")

# Validate parameters
if initial_capital <= 0:
    raise ValueError("initial_capital must be positive")
if max_positions <= 0:
    raise ValueError("max_positions must be positive")
```

### 3. Obsługa brakujących danych (Priorytet 1)

**Implementacja**:
- W `_get_historical_price`: Jeśli brak ceny, użyj interpolacji liniowej między najbliższymi datami
- W `screen_vq_plus_strategy`: Jeśli brak danych fundamentalnych, pomiń symbol z ostrzeżeniem
- Dodać parametr `max_missing_data_pct` (domyślnie 10%) - maksymalny % brakujących danych

### 4. Daty rebalance - dni handlowe (Priorytet 1)

**Implementacja**:
```python
def _adjust_to_trading_day(self, date: datetime) -> datetime:
    """Adjust date to nearest trading day (skip weekends/holidays)"""
    # Simple implementation: skip weekends
    while date.weekday() >= 5:  # Saturday = 5, Sunday = 6
        date -= timedelta(days=1)
    return date
```

### 5. Koszty transakcyjne (Priorytet 2)

**Implementacja**:
```python
def backtest_vq_plus_strategy(
    ...,
    transaction_cost: float = 0.001  # 0.1% per trade
):
    # When opening position:
    transaction_fee = position_value * transaction_cost
    cash -= transaction_fee
    
    # When closing position:
    transaction_fee = exit_value * transaction_cost
    cash += exit_value - transaction_fee
```

### 6. Filtr płynności (Priorytet 2)

**Implementacja**:
```python
def _check_liquidity(self, symbol: str, date: datetime, min_volume: float = 1000000) -> bool:
    """Check if symbol has sufficient liquidity (daily volume)"""
    historical_data = self.market_data_service.get_symbol_history(symbol, days=30)
    # Find volume for date
    # Return True if volume >= min_volume
```

### 7. Walidacja danych fundamentalnych (Priorytet 2)

**Implementacja**:
```python
def _validate_fundamental_data(self, data: Dict) -> bool:
    """Validate fundamental data for sanity"""
    # Check for negative assets (shouldn't happen)
    if data.get('total_assets', 0) < 0:
        return False
    # Check for unrealistic values
    if data.get('revenue', 0) < 0:
        return False
    # ... more checks
    return True
```

### 8. Cache danych fundamentalnych (Priorytet 3)

**Implementacja**:
```python
# Use a cache key: f"FUNDAMENTAL_{symbol}_{as_of_date}"
# Cache TTL: 24 hours
# Store in Redis or in-memory cache
```

### 9. Równoległe przetwarzanie (Priorytet 3)

**Implementacja**:
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def _screen_symbols_parallel(self, symbols: List[str], as_of_date: datetime, ...):
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(self.screen_vq_plus_strategy, symbol, ..., as_of_date): symbol
            for symbol in symbols
        }
        results = []
        for future in as_completed(futures):
            symbol = futures[future]
            try:
                result = future.result()
                if result:
                    results.append(result)
            except Exception as e:
                self.logger.warning(f"Error screening {symbol}: {e}")
    return results
```

### 10. Optymalizacja zapytań API (Priorytet 3)

**Implementacja**:
- Batch requests dla Alpha Vantage (jeśli API wspiera)
- Prefetch danych dla wszystkich symboli na początku backtestu
- Użycie cache'u Redis dla współdzielonych danych

---

## 🧪 Testy

### Testy jednostkowe:
1. `test_backtest_with_historical_data` - Sprawdzenie użycia historycznych danych
2. `test_backtest_with_transaction_costs` - Sprawdzenie kosztów transakcji
3. `test_backtest_with_missing_data` - Sprawdzenie obsługi brakujących danych
4. `test_rebalance_trading_days` - Sprawdzenie przesunięcia na dni handlowe
5. `test_validate_fundamental_data` - Sprawdzenie walidacji danych

### Testy integracyjne:
1. `test_full_backtest_3_years` - Pełny backtest na 3 lata
2. `test_backtest_vs_buy_hold` - Porównanie z buy-and-hold
3. `test_backtest_performance_metrics` - Sprawdzenie metryk wydajności

---

## 📊 Metryki Sukcesu

### Dokładność:
- ✅ Wszystkie dane fundamentalne są historyczne (nie przyszłe)
- ✅ Wszystkie ceny są z odpowiednich dat
- ✅ Brak błędów z powodu brakujących danych (< 1% brakujących danych)

### Realizm:
- ✅ Koszty transakcyjne są uwzględnione
- ✅ Tylko płynne akcje są w portfelu
- ✅ Rebalance tylko w dni handlowe

### Wydajność:
- ✅ Backtest 3 lat na 500 symboli < 5 minut
- ✅ Cache hit rate > 80%
- ✅ Wykorzystanie API < 80% limitów

---

## 🚀 Harmonogram

### Faza 1: Krytyczne naprawy (1-2 dni)
- [ ] Dane fundamentalne w czasie
- [ ] Walidacja danych wejściowych
- [ ] Obsługa brakujących danych
- [ ] Daty rebalance - dni handlowe

### Faza 2: Realizm (1 dzień)
- [ ] Koszty transakcyjne
- [ ] Filtr płynności
- [ ] Walidacja danych fundamentalnych

### Faza 3: Optymalizacja (1 dzień)
- [ ] Cache danych fundamentalnych
- [ ] Równoległe przetwarzanie
- [ ] Optymalizacja zapytań API

---

## 📝 Notatki

- Wszystkie zmiany muszą być zgodne z istniejącym API
- Zachować backward compatibility
- Dodać obszerne logowanie dla debugowania
- Dokumentować wszystkie parametry i ich domyślne wartości

