# Integracja Yahoo Finance

## Przegląd

Dodano wsparcie dla Yahoo Finance jako alternatywne źródło danych dla akcji, które działa jako fallback gdy Polygon.io i Alpha Vantage są niedostępne lub osiągają rate limits.

## Zalety Yahoo Finance

1. **Brak rate limits** - Yahoo Finance nie ma oficjalnych limitów dla podstawowych zapytań
2. **Darmowe** - Nie wymaga API key
3. **Dobre pokrycie** - Wspiera większość akcji na giełdach światowych
4. **Różne interwały** - Wspiera hourly, daily, weekly data

## Implementacja

### get_stock_price()
- **Pozycja**: Fallback po Alpha Vantage i Polygon.io, przed mockiem
- **Metoda**: Używa `yf.Ticker(symbol).info` do pobrania ceny
- **Pola**: `currentPrice`, `regularMarketPrice`, `previousClose`

### get_symbol_history_with_interval()
- **Pozycja**: Fallback po Polygon.io, przed Alpha Vantage
- **Metoda**: Używa `yf.Ticker(symbol).history()` z odpowiednimi parametrami
- **Interwały**: 
  - `1h` - hourly data
  - `1d` - daily data
  - `1wk` - weekly data

## Instalacja

```bash
pip install yfinance==0.2.33
```

## Status

✅ **Zaimplementowane**:
- Import yfinance z graceful fallback
- get_stock_price() fallback
- get_symbol_history_with_interval() fallback
- Caching wyników
- Prometheus metrics tracking

## Użycie

System automatycznie użyje Yahoo Finance gdy:
1. Polygon.io circuit breaker jest otwarty
2. Alpha Vantage rate limit jest osiągnięty
3. Polygon.io zwraca błąd

## Monitoring

Yahoo Finance requests są trackowane przez Prometheus:
- `market_provider_requests_total{provider="yahoo_finance", status="attempt"}`
- `market_provider_requests_total{provider="yahoo_finance", status="success"}`
- `market_provider_requests_total{provider="yahoo_finance", status="error"}`

## Limiti i Ograniczenia

- Yahoo Finance może czasami zwracać niepełne dane dla niektórych symboli
- Niektóre symbole mogą nie być dostępne w Yahoo Finance
- Nie ma oficjalnego API, więc może się zmieniać bez ostrzeżenia

## Testowanie

```python
from market_data_service import MarketDataService

mds = MarketDataService()

# Test get_stock_price
price = mds.get_stock_price('AAPL')
print(f"AAPL price: {price}")

# Test get_symbol_history_with_interval
history, interval = mds.get_symbol_history_with_interval('AAPL', 30)
print(f"History: {len(history)} points, interval: {interval}")
```

## Rekomendacje

1. **Monitoruj użycie** - Sprawdzaj Prometheus metrics, aby zobaczyć jak często używany jest Yahoo Finance
2. **Fallback hierarchy** - Polygon.io → Yahoo Finance → Alpha Vantage → Mock
3. **Cache** - Yahoo Finance results są cachowane tak samo jak inne źródła

---

**Data utworzenia**: 2025-11-05

