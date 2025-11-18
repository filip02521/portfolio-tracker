# Portfolio Tracker Pro - Instrukcja Uruchomienia

## 🚀 Szybki Start

### Wymagania
- Python 3.12+
- Node.js 24.10+
- Terminal z możliwością uruchamiania procesów w tle

---

## 📋 Kroki Uruchomienia

### 1. Uruchom Backend (Terminal 1)
```bash
cd portfolio-tracker-pro/backend
source venv/bin/activate
python main.py
```

Backend będzie dostępny na: `http://localhost:8000`
- API Docs: http://localhost:8000/api/docs
- Health Check: http://localhost:8000/api/health

### 2. Uruchom Frontend (Terminal 2)
```bash
cd portfolio-tracker-pro/frontend
npm start
```

Frontend będzie dostępny na: `http://localhost:3000`

**React DevServer automatycznie proxy'uje** zapytania do backendu!

---

## ✅ Weryfikacja

### Test Backend
```bash
curl http://localhost:8000/api/health
# Powinno zwrócić: {"status":"healthy",...}
```

### Test Frontend
```bash
curl http://localhost:3000
# Powinno zwrócić: HTML strony
```

### Test Proxy
```bash
curl http://localhost:3000/api/health
# Powinno zwrócić: {"status":"healthy",...}
```

---

## 🔧 Rozwiązywanie Problemów

### Problem: "Cannot connect to server"
**Rozwiązanie:**
1. Sprawdź czy backend działa: `ps aux | grep python.*main.py`
2. Jeśli nie działa, uruchom: `cd backend && source venv/bin/activate && python main.py`
3. Poczekaj ~10 sekund na inicjalizację
4. Przetestuj: `curl http://localhost:8000/api/health`

### Problem: "Port 3000/8000 already in use"
**Rozwiązanie:**
```bash
# Znajdź procesy
lsof -ti:3000
lsof -ti:8000

# Zatrzymaj je
kill -9 <PID1> <PID2>
```

### Problem: "ModuleNotFoundError"
**Rozwiązanie:**
```bash
cd portfolio-tracker-pro/backend
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🔗 Ważne Adresy

| Serwis | URL | Status |
|--------|-----|--------|
| Frontend | http://localhost:3000 | ✅ React DevServer |
| Backend API | http://localhost:8000/api | ✅ FastAPI |
| API Docs | http://localhost:8000/api/docs | ✅ Swagger |
| Health Check | http://localhost:8000/api/health | ✅ Uvicorn |

---

## 📝 Uwagi

1. **Backend MUSI być uruchomiony pierwszy** - frontend próbuje się z nim połączyć
2. **Używaj venv dla backendu** - `source venv/bin/activate` jest wymagane
3. **Proxy React** - frontend na porcie 3000 proxy'uje `/api/*` do `localhost:8000`
4. **Hot Reload** - oba serwery automatycznie przeładowują zmiany

---

## 🎯 Test Konta

Możesz zarejestrować nowe konto lub użyć:
- Username: `testuser`
- Email: `test@example.com`
- Password: `testpass123`

---

## ⚠️ Zmienne Środowiskowe

Backend wymaga `.env` w `backend/` (patrz `env.example`)
Frontend używa proxy - nie wymaga dodatkowej konfiguracji

---

**Gotowe! 🎉** Portfolio Tracker Pro powinien działać teraz poprawnie!

