# Finnhub API Setup Guide

## Jak skonfigurować Finnhub API Key

### 1. Zdobądź API Key
1. Zaloguj się na https://finnhub.io/
2. Przejdź do sekcji "Settings" (prawy górny róg)
3. Skopiuj swój **API Key** (maskowany tekst z ikoną oka/kopiowania)

### 2. Ustaw API Key w aplikacji

#### Opcja A: Plik `.env` (lokalnie)
Utwórz lub edytuj plik `.env` w folderze `portfolio-tracker-pro/backend/`:

```bash
FINNHUB_API_KEY=d46f5d1r01qgc9esi820d46f5d1r01qgc9esi82g
```

**UWAGA:** Plik `.env` jest ignorowany przez git (nie powinien być commitowany ze względów bezpieczeństwa).

#### Opcja B: Zmienna środowiskowa systemowa (produkcja)
Ustaw zmienną środowiskową w systemie operacyjnym:

**Linux/macOS:**
```bash
export FINNHUB_API_KEY="d46f5d1r01qgc9esi820d46f5d1r01qgc9esi82g"
```

**Windows (PowerShell):**
```powershell
$env:FINNHUB_API_KEY="d46f5d1r01qgc9esi820d46f5d1r01qgc9esi82g"
```

**Windows (CMD):**
```cmd
set FINNHUB_API_KEY=twoj_api_key_tutaj
```

#### Opcja C: Railway / Heroku / Inne platformy
Ustaw zmienną środowiskową w panelu administracyjnym platformy:
- **Railway**: Settings → Variables → Add Variable
- **Heroku**: Settings → Config Vars → Reveal Config Vars

### 3. Weryfikacja
Po ustawieniu API Key, zrestartuj serwer backend:

```bash
cd portfolio-tracker-pro/backend
source venv/bin/activate  # jeśli używasz venv
python main.py
```

Aplikacja automatycznie użyje API Key z konfiguracji.

### 4. Limity API (Free Tier)
- **60 wywołań/minutę** (1 wywołanie/sekundę)
- **Dla backtestingu:** Jeśli testujesz wiele symboli, może być konieczne dodanie opóźnień między wywołaniami

### 5. Webhook (opcjonalne)
Webhook nie jest wymagany dla backtestu VQ+ Strategy. Jest używany tylko jeśli potrzebujesz real-time aktualizacji danych finansowych.

### Troubleshooting

**Problem:** "Rate limit exceeded"
- **Rozwiązanie:** Dodaj opóźnienia między wywołaniami API lub użyj cache

**Problem:** "Invalid API key"
- **Rozwiązanie:** Sprawdź czy API key jest poprawnie ustawiony w `.env` lub zmiennych środowiskowych

**Problem:** "No data returned"
- **Rozwiązanie:** Niektóre symbole mogą nie mieć danych w Finnhub. Aplikacja automatycznie użyje Alpha Vantage jako fallback.

### Przykładowy plik `.env`

```bash
# Finnhub API
FINNHUB_API_KEY=d46f5d1r01qgc9esi820d46f5d1r01qgc9esi82g

# Alpha Vantage (backup)
ALPHA_VANTAGE_API_KEY=twoj_alpha_vantage_key

# Polygon (dla danych rynkowych)
POLYGON_API_KEY=twoj_polygon_key
```

