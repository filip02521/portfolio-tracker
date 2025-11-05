# Instalacja yfinance - Rozwiązanie Signal 0 dla Stocks

## Problem

AAPL, TSLA, GOOGL mają signal 0, ponieważ:
1. **yfinance nie było zainstalowane** - Yahoo Finance fallback nie działał
2. **Polygon.io rate limits** - Blokowały zapytania dla stocks
3. **Brak danych historycznych** - System nie mógł obliczyć wskaźników technicznych

## Rozwiązanie

### 1. Zainstalować yfinance

```bash
cd portfolio-tracker-pro/backend
source venv/bin/activate
pip install yfinance==0.2.33
```

### 2. Zrestartować Backend Server

**Ważne**: Backend musi używać venv Python, nie system Python!

#### Opcja A: macOS LaunchAgent (ZALECANE - automatyczny start)

```bash
cd portfolio-tracker-pro/backend
./backend_service.sh start
```

Zobacz: [LAUNCH_AGENT_SETUP.md](LAUNCH_AGENT_SETUP.md) dla szczegółów.

#### Opcja B: Skrypt startowy (jednorazowy start)

```bash
cd portfolio-tracker-pro/backend
./start_backend.sh
```

#### Opcja C: Ręcznie z venv

```bash
# Sprawdź czy backend używa venv
ps aux | grep uvicorn

# Zrestartuj backend używając venv
cd portfolio-tracker-pro/backend
source venv/bin/activate
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Weryfikacja

Po restarcie backend powinien:
- ✅ Używać yfinance jako fallback dla stocks
- ✅ Zwracać signal > 0 dla AAPL, TSLA, GOOGL
- ✅ Obliczać wskaźniki techniczne (17+ wskaźników)

## Status

- ✅ yfinance zainstalowane w venv
- ✅ Yahoo Finance fallback zaimplementowany
- ✅ macOS LaunchAgent dostępny (automatyczny start z venv)
- ⏳ **Wymaga restartu backend servera** (używa venv Python)

**Zalecane**: Użyj LaunchAgent (Opcja A) dla automatycznego startu przy zalogowaniu.

## Test

Po restarcie backend, sprawdź w UI czy:
- AAPL ma signal > 0 (nie 0)
- TSLA ma signal > 0 (nie 0)
- GOOGL ma signal > 0 (nie 0)

Jeśli nadal signal 0, sprawdź logi:
```bash
grep "Yahoo Finance" backend.log
grep "Signal 0" backend.log
grep "insufficient historical data" backend.log
```

---

**Data utworzenia**: 2025-11-05

