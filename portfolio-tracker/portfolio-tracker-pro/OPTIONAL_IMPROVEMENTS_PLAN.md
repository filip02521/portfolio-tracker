# 📋 Plan Opcjonalnych Ulepszeń - Portfolio Tracker Pro

## 🎯 **CEL:**
Zwiększenie inteligencji aplikacji i poprawa jakości danych w czasie rzeczywistym.

---

## 🔍 **ULEPSZENIE 1: Smart Insights Service - Enhancements**

### **Obecny Stan:**
- ✅ Podstawowy `SmartInsightsService` istnieje
- ✅ Enhanced Recommendations już zaimplementowane (rebalancing calculator, tax-loss harvesting)
- ⚠️ Brak zaawansowanych alertów o ryzyku
- ⚠️ Brak automatycznych sugestii rebalansowania w czasie rzeczywistym

### **Co Zaimplementować:**

#### **1.1. Real-time Risk Alerts** (2-3h)
**Backend:**
- Rozszerzyć `SmartInsightsService` o metodę `detect_risk_alerts()`
- Wykrywanie:
  - Koncentracja ryzyka (>40% w jednym aktywie)
  - Nadmierna korelacja (>0.8 między aktywami)
  - Wysoka volatility (>50% rocznie)
  - Duży drawdown (>20% od szczytu)
- Endpoint: `GET /api/insights/risk-alerts`
- Cache: 5 minut (ryzyko może się szybko zmieniać)

**Frontend:**
- Komponent `RiskAlertsPanel` w Dashboard
- Wizualne wskaźniki ryzyka (kolorowe chipsy)
- Auto-refresh co 30 sekund
- Linki do szczegółów (drill-down)

#### **1.2. Automatic Rebalancing Suggestions** (3-4h)
**Backend:**
- Metoda `generate_rebalancing_suggestions()` w `SmartInsightsService`
- Analiza:
  - Obecna alokacja vs optymalna (z Portfolio Optimizer)
  - Drift detection (odchylenie >5%)
  - Koszt rebalansowania (spread, fees)
  - Tax implications
- Endpoint: `GET /api/insights/rebalancing-suggestions`
- Parametry:
  - `threshold`: próg driftu (default: 5%)
  - `include_tax`: uwzględniać podatki (default: true)
  - `max_suggestions`: max liczba sugestii (default: 5)

**Frontend:**
- Sekcja "Rebalancing Suggestions" w Dashboard
- Karty z sugestiami:
  - Symbol, obecna alokacja, docelowa alokacja
  - Kwota do kupna/sprzedaży
  - Oszacowany koszt (fees, spread)
  - Potencjalne korzyści (risk reduction, expected return)
- Przycisk "Apply Suggestions" (opcjonalnie - przyszłość)

#### **1.3. Portfolio Health Score** (2-3h)
**Backend:**
- Metoda `calculate_portfolio_health()` w `SmartInsightsService`
- Czynniki:
  - Dywersyfikacja (liczba aktywów, sektory, regiony)
  - Koncentracja ryzyka
  - Płynność portfela
  - Koszt efektywności (fees, spread)
- Score: 0-100 (0 = bardzo zły, 100 = doskonały)
- Endpoint: `GET /api/insights/health-score`

**Frontend:**
- Health Score widget w Dashboard
- Wizualizacja: progress bar + kolor (red/yellow/green)
- Breakdown: szczegóły każdego czynnika
- Trend: zmiana w czasie (jeśli dostępne dane historyczne)

#### **1.4. Market Sentiment Integration** (4-5h) - OPCJONALNE
**Backend:**
- Integracja z news API (jeśli dostępne)
- Analiza sentymentu dla aktywów w portfolio
- Endpoint: `GET /api/insights/sentiment/{symbol}`
- Cache: 1 godzina

**Frontend:**
- Sentiment indicators w AssetTabs
- Kolorowe wskaźniki (bullish/bearish/neutral)

### **Szacowany Czas: 11-15 godzin**

---

## ⚡ **ULEPSZENIE 2: Real-time Data Accuracy - Improvements**

### **Obecny Stan:**
- ✅ `MarketDataService` działa
- ✅ Podstawowe cache'owanie
- ✅ Fallbacki do różnych źródeł
- ⚠️ Brak inteligentnego zarządzania rate limitami
- ⚠️ Brak priorytetyzacji requestów
- ⚠️ Brak automatycznego retry z backoff

### **Co Zaimplementować:**

#### **2.1. Intelligent Rate Limit Management** (3-4h)
**Backend:**
- Klasa `RateLimitManager` w `market_data_service.py`
- Funkcje:
  - Tracking requestów per API provider
  - Automatyczne throttling przy zbliżaniu się do limitu
  - Priority queue dla requestów (krytyczne > normalne > background)
  - Distributed rate limiting (jeśli wiele instancji backendu)
- Implementacja:
  ```python
  class RateLimitManager:
      def __init__(self):
          self.providers = {
              'binance': {'limit': 1200, 'window': 60, 'current': 0},
              'yfinance': {'limit': 2000, 'window': 60, 'current': 0},
              # ...
          }
      
      def can_make_request(self, provider: str, priority: str = 'normal') -> bool
      def record_request(self, provider: str)
      def get_wait_time(self, provider: str) -> float
  ```

**Integracja:**
- Używać w `get_price()`, `get_symbol_history()`, `get_watchlist_prices()`
- Automatyczne opóźnianie requestów przy rate limit
- Logowanie warningów przy zbliżaniu się do limitu

#### **2.2. Request Prioritization System** (2-3h)
**Backend:**
- Priority levels:
  - `critical`: Dashboard summary, active alerts (0 delay)
  - `high`: User portfolio assets, watchlist prices (100ms delay)
  - `normal`: Historical data, analytics (500ms delay)
  - `low`: Background prefetch, non-critical data (2000ms delay)
- Implementacja w `MarketDataService`:
  ```python
  async def get_price(self, symbol: str, priority: str = 'normal') -> Dict:
      if not rate_limit_manager.can_make_request('provider', priority):
          wait_time = rate_limit_manager.get_wait_time('provider')
          await asyncio.sleep(wait_time)
      # ... make request
  ```

**Frontend:**
- Parametr `priority` w `portfolioService` methods:
  - `getSummary()` → `critical`
  - `getAssets()` → `high`
  - `getAdvancedAnalytics()` → `normal`
  - `prefetchContextualData()` → `low`

#### **2.3. Enhanced Fallback Strategy** (2-3h)
**Backend:**
- Hierarchia źródeł danych:
  1. Primary source (np. Binance API dla crypto)
  2. Secondary source (np. CoinGecko dla crypto)
  3. Tertiary source (np. yfinance jako fallback)
  4. Cached data (jeśli wszystkie źródła fail)
- Automatyczne przełączanie przy błędach
- Health checks dla każdego źródła
- Circuit breaker pattern (temporary disable przy wielokrotnych błędach)

**Implementacja:**
```python
class DataSourceManager:
    def __init__(self):
        self.sources = {
            'crypto': [
                {'name': 'binance', 'priority': 1, 'healthy': True},
                {'name': 'coingecko', 'priority': 2, 'healthy': True},
                {'name': 'yfinance', 'priority': 3, 'healthy': True}
            ]
        }
    
    async def get_data(self, symbol: str, data_type: str) -> Dict:
        for source in sorted_sources:
            try:
                return await self._fetch_from_source(source, symbol)
            except Exception as e:
                self._mark_unhealthy(source)
                continue
        # All sources failed, return cached data
        return self._get_cached_data(symbol)
```

#### **2.4. Smart Caching with TTL per Data Type** (2-3h)
**Backend:**
- Różne TTL dla różnych typów danych:
  - Real-time prices: 5-10 sekund
  - Historical data: 1 godzina
  - Analytics: 15 minut
  - Static data (symbol info): 24 godziny
- Cache invalidation strategy:
  - Time-based (TTL)
  - Event-based (gdy dane się zmieniają)
  - Manual (przez endpoint)
- Cache warming dla krytycznych danych

**Implementacja w `MarketDataService`:**
```python
CACHE_TTL = {
    'price': 10,  # seconds
    'history': 3600,  # 1 hour
    'analytics': 900,  # 15 minutes
    'symbol_info': 86400  # 24 hours
}

def get_cached_or_fetch(self, key: str, fetch_fn, ttl: int):
    cached = self.cache.get(key)
    if cached and not self._is_expired(cached, ttl):
        return cached['data']
    data = fetch_fn()
    self.cache.set(key, {'data': data, 'timestamp': time.time()}, ttl)
    return data
```

#### **2.5. Automatic Retry with Exponential Backoff** (1-2h)
**Backend:**
- Retry logic z exponential backoff dla:
  - Network errors (timeout, connection error)
  - Rate limit errors (429)
  - Temporary server errors (503, 502)
- Nie retry dla:
  - Client errors (400, 401, 404)
  - Permanent errors (500 bez retry-after header)
- Configurable max retries per request type

**Implementacja:**
```python
async def fetch_with_retry(self, url: str, max_retries: int = 3, 
                          base_delay: float = 1.0) -> Dict:
    for attempt in range(max_retries):
        try:
            return await self._fetch(url)
        except (TimeoutError, ConnectionError, HTTPException) as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            await asyncio.sleep(delay)
    raise Exception("Max retries exceeded")
```

#### **2.6. Data Quality Monitoring** (2-3h)
**Backend:**
- Monitoring jakości danych:
  - Staleness detection (czy dane są aktualne)
  - Anomaly detection (nieoczekiwane zmiany cen)
  - Data completeness (czy wszystkie wymagane pola są wypełnione)
- Endpoint: `GET /api/market-data/quality-report`
- Logging do pliku/metrics dla analizy

**Frontend:**
- Wskaźnik jakości danych w Dashboard
- Ostrzeżenia gdy dane mogą być nieaktualne
- Opcja ręcznego odświeżenia

### **Szacowany Czas: 12-18 godzin**

---

## 📊 **PODSUMOWANIE**

| Ulepszenie | Czas | Priorytet | Wpływ |
|------------|------|-----------|-------|
| **1.1. Real-time Risk Alerts** | 2-3h | Wysoki | ⭐⭐⭐ |
| **1.2. Automatic Rebalancing Suggestions** | 3-4h | Wysoki | ⭐⭐⭐ |
| **1.3. Portfolio Health Score** | 2-3h | Średni | ⭐⭐ |
| **1.4. Market Sentiment Integration** | 4-5h | Niski | ⭐ |
| **2.1. Rate Limit Management** | 3-4h | Wysoki | ⭐⭐⭐ |
| **2.2. Request Prioritization** | 2-3h | Wysoki | ⭐⭐⭐ |
| **2.3. Enhanced Fallback Strategy** | 2-3h | Średni | ⭐⭐ |
| **2.4. Smart Caching** | 2-3h | Średni | ⭐⭐ |
| **2.5. Retry with Backoff** | 1-2h | Średni | ⭐⭐ |
| **2.6. Data Quality Monitoring** | 2-3h | Niski | ⭐ |

**Total: 23-33 godzin pracy**

---

## 🎯 **REKOMENDOWANY PLAN DZIAŁANIA**

### **Faza 1: Critical Improvements (8-10h)**
1. **1.1. Real-time Risk Alerts** (2-3h)
2. **1.2. Automatic Rebalancing Suggestions** (3-4h)
3. **2.1. Rate Limit Management** (3-4h)

### **Faza 2: Important Improvements (6-9h)**
4. **2.2. Request Prioritization** (2-3h)
5. **2.3. Enhanced Fallback Strategy** (2-3h)
6. **1.3. Portfolio Health Score** (2-3h)

### **Faza 3: Nice to Have (9-14h)**
7. **2.4. Smart Caching** (2-3h)
8. **2.5. Retry with Backoff** (1-2h)
9. **2.6. Data Quality Monitoring** (2-3h)
10. **1.4. Market Sentiment Integration** (4-5h) - OPCJONALNE

---

## 🚀 **NASTĘPNE KROKI**

1. **Zatwierdź plan** - czy te ulepszenia są w odpowiedniej kolejności?
2. **Wybierz fazę** - od której fazy zacząć?
3. **Zacznij implementację** - Faza 1 daje największy wpływ

---

## 📝 **NOTATKI**

- Wszystkie ulepszenia są backward compatible
- Można implementować stopniowo
- Każde ulepszenie można testować niezależnie
- Priorytety można zmieniać w zależności od potrzeb

