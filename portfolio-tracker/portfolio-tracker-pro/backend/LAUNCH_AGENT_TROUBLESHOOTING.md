# LaunchAgent Troubleshooting

## Problem: Proces używa system Python zamiast venv Python

### Symptomy
- `ps aux` pokazuje system Python: `/usr/local/Cellar/python@3.12/...`
- Ale backend działa i odpowiada na API

### Wyjaśnienie

**To jest normalne!** W macOS venv często używa symlinków do systemowego Python. Ważne jest to, że:

1. ✅ **Backend działa** - odpowiada na `/api/health`
2. ✅ **yfinance jest dostępne** - sprawdź: `source venv/bin/activate && python -c "import yfinance"`
3. ✅ **LaunchAgent używa venv Python** - ścieżka w plist wskazuje na venv

### Weryfikacja

Sprawdź czy backend rzeczywiście używa yfinance:

```bash
# Sprawdź logi backend
./backend_service.sh logs | grep -i "yfinance"

# Sprawdź czy API recommendations działa
curl http://localhost:8000/api/ai/recommendations
```

Jeśli backend zwraca recommendations z signal > 0 dla stocks (AAPL, TSLA, GOOGL), to znaczy że yfinance działa!

### Dlaczego ps aux pokazuje system Python?

Venv/bin/python jest symlinkiem do systemowego Python, ale:
- Environment variables (PATH, PYTHONPATH) są ustawione przez LaunchAgent
- Biblioteki Python są z venv/lib/python3.12/site-packages
- yfinance jest zainstalowane w venv, nie system

### Rozwiązanie

**Nie trzeba nic robić!** Jeśli backend działa i recommendations mają signal > 0, wszystko jest OK.

---

**Data utworzenia**: 2025-11-05



