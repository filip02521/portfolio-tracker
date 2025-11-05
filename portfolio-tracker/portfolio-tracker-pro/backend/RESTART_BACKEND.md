# Jak Zrestartować Backend z venv (Rozwiązanie Signal 0)

## Problem

Backend server używa **system Python** zamiast **venv Python**, więc:
- ❌ `yfinance` nie jest dostępne (zainstalowane tylko w venv)
- ❌ Yahoo Finance fallback nie działa
- ❌ Polygon rate limits blokują stocks (AAPL, TSLA, GOOGL)
- ❌ Rezultat: Signal 0 dla stocks

## Rozwiązanie

### Krok 1: Zatrzymaj Obecny Backend

```bash
# Sprawdź PID
cat portfolio-tracker-pro/backend/backend.pid

# Zatrzymaj backend
pkill -f "python.*main.py"
# lub
kill $(cat portfolio-tracker-pro/backend/backend.pid)
```

### Krok 2: Uruchom Backend z venv

```bash
cd portfolio-tracker-pro/backend

# Aktywuj venv
source venv/bin/activate

# Uruchom backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Krok 3: Weryfikacja

Po restarcie, sprawdź w UI czy:
- ✅ AAPL ma signal > 0 (nie 0)
- ✅ TSLA ma signal > 0 (nie 0)  
- ✅ GOOGL ma signal > 0 (nie 0)

### Krok 4: Sprawdź Logi

```bash
# W logach powinno być:
grep "Yahoo Finance" portfolio-tracker-pro/backend/backend.log
# Powinno pokazać: "Yahoo Finance: fetched X historical data points for AAPL"

# Sprawdź czy yfinance jest dostępne
grep "yfinance not available" portfolio-tracker-pro/backend/backend.log
# Powinno być puste (brak tego komunikatu)
```

## Alternatywa: Skrypt Startowy

Możesz stworzyć skrypt startowy `start_backend.sh`:

```bash
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Uruchom:
```bash
chmod +x portfolio-tracker-pro/backend/start_backend.sh
./portfolio-tracker-pro/backend/start_backend.sh
```

## Status

- ✅ yfinance zainstalowane w venv
- ✅ Yahoo Finance fallback zaimplementowany
- ⏳ **Wymaga restartu backend z venv**

Po restarcie z venv, stocks powinny mieć signal > 0!

---

**Data utworzenia**: 2025-11-05

