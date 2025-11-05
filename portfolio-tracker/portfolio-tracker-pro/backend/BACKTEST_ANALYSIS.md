# Analiza Przebiegu Backtestu Optymalizacji Wag

## Data Testu
2025-11-05

## Parametry Testu
- **Okres**: 180 dni (2025-05-09 do 2025-11-05)
- **Symbole**: BTC, ETH, SOL, AAPL, MSFT, TSLA
- **Progi signal_threshold**: 10.0, 20.0, 30.0
- **Kapitał początkowy**: $10,000
- **Strategia**: follow_ai
- **Konfiguracje**: 7 różnych zestawów wag

## Wyniki Testu

### ⚠️ KRYTYCZNY PROBLEM: 0 transakcji we wszystkich testach

**Wszystkie 7 konfiguracji wag:**
- Threshold 10.0: **0 transakcji** ❌
- Threshold 20.0: **0 transakcji** ❌
- Threshold 30.0: **0 transakcji** ❌

**Wszystkie metryki = 0:**
- Total Return: 0%
- Sharpe Ratio: 0.00
- Win Rate: 0%
- Num Trades: 0

## Analiza Problemów

### 1. Problem z Danymi API ❌

**Logi pokazują:**
```
✅ Fetched 52 1w candles for BTC
✅ Fetched 52 1w candles for ETH
✅ Fetched 52 1w candles for SOL
✅ Fetched 55 1w candles for AAPL
✅ Fetched 55 1w candles for MSFT
❌ Polygon aggregates 429 rate limit for TSLA
❌ Alpha Vantage fetch failed for TSLA: AV rate limit cooldown
❌ Error fetching stock price for TSLA: Polygon circuit open
```

**Wniosek:**
- ✅ BTC, ETH, SOL, AAPL, MSFT - dane pobrane
- ❌ TSLA - **BRAK DANYCH** z powodu rate limits

### 2. Problem z Generowaniem Recommendations ❓

**Test manualny recommendations:**
```python
# Test dla BTC/ETH
result = ai.recommend_rebalance(portfolio, target, 0.05)
# Wynik: ETH: signal=20.0, action=sell
#        BTC: signal=-2.0, action=buy
```

**Wniosek:**
- Recommendations są generowane ✅
- Signal_strength może być 20.0 (ETH) - przekracza threshold 10.0 ✅
- Signal_strength może być -2.0 (BTC) - nie przekracza threshold 10.0 ❌

### 3. Problem z Filtrowaniem w Backtestcie ❌

**Kod filtrowania (ai_service.py:2434-2436):**
```python
if strategy == 'follow_ai':
    if signal_strength > signal_threshold or signal_strength < -signal_threshold:
        filtered_recommendations.append(rec)
```

**Warunki wykonania transakcji:**
- `signal_strength > 10.0` LUB `signal_strength < -10.0` (dla threshold=10.0)
- `signal_strength > 20.0` LUB `signal_strength < -20.0` (dla threshold=20.0)
- `signal_strength > 30.0` LUB `signal_strength < -30.0` (dla threshold=30.0)

**Problem:**
- Jeśli signal_strength w backtestcie jest zawsze < 10.0 (np. -2.0, 5.0, 8.0), to **żadne transakcje nie są wykonywane**
- Backtest używa **tygodniowych danych** (weekly candles) - może być mniej okazji do sygnałów

### 4. Problem z Formatem Danych w Backtestcie ❓

**Kod pobierania danych (ai_service.py:2314-2316):**
```python
data, interval = self.market_data_service.get_symbol_history_with_interval(
    symbol, 90  # Weekly data (prediction_horizon > 60 returns weekly)
)
```

**Filtrowanie po datach (ai_service.py:2320-2326):**
```python
for candle in data:
    candle_date = datetime.fromisoformat(
        candle.get('timestamp', candle.get('date', '')).replace('Z', '+00:00')
    )
    if start_dt <= candle_date <= end_dt:
        filtered_data.append(candle)
```

**Możliwe problemy:**
- Format daty w candle może być nieprawidłowy
- Filtrowanie może nie działać poprawnie
- Weekly candles mogą mieć mniej dat niż oczekiwano

### 5. Problem z Generowaniem Recommendations dla Każdej Daty ❓

**Kod backtestu (ai_service.py:2400-2418):**
```python
if strategy in ['follow_ai', 'high_confidence', 'weighted_allocation']:
    # Get AI recommendations for this date
    for date_str in sorted_dates:
        recommendations_result = self.recommend_rebalance(
            current_holdings,
            target_allocation,
            rebalance_threshold=0.05
        )
```

**Problem:**
- `recommend_rebalance` używa **obecnych danych rynkowych** (dzisiejsza data)
- W backtestcie potrzebujemy **historycznych danych** dla każdej daty
- `recommend_rebalance` może nie działać poprawnie dla historycznych dat

## Weryfikacja

### Test 1: Czy recommendations są generowane dla historycznych dat?
**Odpowiedź**: ❓ Nie wiemy - potrzebujemy testu

### Test 2: Czy signal_strength w backtestcie przekracza threshold?
**Odpowiedź**: ❌ Najprawdopodobniej NIE - dlatego 0 transakcji

### Test 3: Czy dane historyczne są dostępne dla wszystkich symboli?
**Odpowiedź**: ❌ TSLA nie ma danych (rate limits)

### Test 4: Czy filtrowanie po datach działa poprawnie?
**Odpowiedź**: ❓ Nie wiemy - potrzebujemy testu

## Rekomendacje Naprawy

### Priorytet 1: Naprawić Problem z 0 Transakcji

1. **Dodać logowanie w backtestcie:**
   - Logować każdą datę w backtestcie
   - Logować liczbę recommendations dla każdej daty
   - Logować signal_strength dla każdego recommendation
   - Logować liczbę filtered_recommendations po filtrowaniu

2. **Sprawdzić czy recommendations są generowane:**
   - Dodać test dla pojedynczej daty historycznej
   - Sprawdzić czy `recommend_rebalance` działa dla historycznych dat

3. **Zmniejszyć threshold dla testów:**
   - Przetestować z threshold=5.0 zamiast 10.0
   - Sprawdzić czy wtedy są transakcje

### Priorytet 2: Naprawić Problem z Danymi API

1. **Dodać Yahoo Finance fallback dla TSLA:**
   - Sprawdzić czy TSLA ma dane w Yahoo Finance
   - Użyć yfinance dla TSLA jeśli Polygon/Alpha Vantage nie działa

2. **Dodać opóźnienia między zapytaniami:**
   - Unikać rate limits przez dodanie opóźnień
   - Użyć cache dla powtarzających się zapytań

### Priorytet 3: Ulepszyć Backtest

1. **Dodać tryb debug:**
   - Szczegółowe logowanie każdego kroku
   - Export intermediate results do JSON

2. **Sprawdzić format dat:**
   - Weryfikować format timestamp w candle data
   - Upewnić się że filtrowanie po datach działa

## Wnioski

### ❌ Test NIE był kompletny

**Problemy:**
1. **0 transakcji** - główny problem, test nie miał sensu
2. **Brak danych dla TSLA** - rate limits API
3. **Nie wiemy czy recommendations były generowane** - brak logowania
4. **Nie wiemy jakie były signal_strength** - brak logowania

### ✅ Co działało:
- Framework backtestu działał (bez błędów)
- Dane dla 5/6 symboli były pobrane
- Recommendations są generowane (test manualny)

### ❌ Co nie działało:
- **0 transakcji** - test nie miał sensu
- TSLA brak danych
- Brak szczegółowego logowania

## Następne Kroki

1. **Dodać szczegółowe logowanie** do backtestu
2. **Przetestować z niższym threshold** (5.0)
3. **Naprawić problem z TSLA** (Yahoo Finance fallback)
4. **Uruchomić ponownie backtest** z logowaniem
5. **Przeanalizować logi** aby zrozumieć dlaczego 0 transakcji

---

**Status**: ⚠️ **TEST NIEKOMPLETNY - WYMAGA NAPRAWY**

**Data analizy**: 2025-11-05

