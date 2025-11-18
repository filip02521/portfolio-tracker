# 🚀 Instrukcja Instalacji - Portfolio Tracker Pro

Kompletny przewodnik instalacji projektu na nowym komputerze (Windows, macOS, Linux).

## 📋 Wymagania Systemowe

### Backend (Python)
- **Python 3.10+** (sprawdź: `python3 --version` lub `python --version`)
- **pip** (zwykle dołączony z Python)
- **Git** (do klonowania repozytorium)

### Frontend (Node.js)
- **Node.js 16+** (sprawdź: `node --version`)
- **npm** lub **yarn** (zwykle dołączony z Node.js)

### Opcjonalne
- **Redis** (dla cache'owania - opcjonalne, aplikacja działa bez tego)
- **PostgreSQL** (opcjonalne, domyślnie używa SQLite)

---

## 📥 Krok 1: Klonowanie Projektu

```bash
# Sklonuj repozytorium z GitHub
git clone https://github.com/filip02521/portfolio-tracker.git

# Przejdź do głównego katalogu projektu
cd portfolio-tracker/portfolio-tracker-pro
```

---

## 🔧 Krok 2: Instalacja Backendu

### 2.1. Utwórz wirtualne środowisko Python

```bash
# Przejdź do katalogu backend
cd backend

# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 2.2. Zainstaluj zależności

```bash
pip install -r requirements.txt
```

**Uwaga:** Instalacja może zająć kilka minut, szczególnie `torch` i `transformers` (AI modele).

### 2.3. Skonfiguruj zmienne środowiskowe

```bash
# Skopiuj plik przykładu
cp env.example .env

# Edytuj plik .env (użyj edytora tekstu: nano, vim, notepad, VS Code)
```

**Wymagane zmienne w `.env`:**

```env
# Security - ZMIEŃ TE WARTOŚCI!
SECRET_KEY=twoj-super-secret-klucz-min-32-znaki-zmien-na-losowy
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database (SQLite - domyślnie)
DATABASE_PATH=portfolio_tracker.db

# Exchange API Keys (opcjonalne - dodaj tylko te giełdy, które chcesz używać)
BINANCE_API_KEY=twoj_binance_api_key
BINANCE_SECRET_KEY=twoj_binance_secret_key

BYBIT_API_KEY=twoj_bybit_api_key
BYBIT_SECRET_KEY=twoj_bybit_secret_key

XTB_USERNAME=twoj_xtb_username
XTB_PASSWORD=twoj_xtb_password

# External APIs (opcjonalne)
NEWSAPI_KEY=twoj_newsapi_key
ALPHA_VANTAGE_API_KEY=twoj_alpha_vantage_key

# App Settings
DEBUG=True
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

**⚠️ WAŻNE:**
- **SECRET_KEY** - wygeneruj losowy klucz (min. 32 znaki). Możesz użyć:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- Aplikacja **działa bez API keys** - możesz dodać je później
- Jeśli nie dodasz API keys, niektóre funkcje będą niedostępne

### 2.4. Inicjalizacja bazy danych

Baza danych SQLite zostanie automatycznie utworzona przy pierwszym uruchomieniu backendu. Nie musisz nic robić ręcznie.

---

## 🎨 Krok 3: Instalacja Frontendu

### 3.1. Zainstaluj zależności

```bash
# Wróć do głównego katalogu projektu
cd ..

# Przejdź do katalogu frontend
cd frontend

# Zainstaluj zależności Node.js
npm install
```

**Uwaga:** Instalacja może zająć 2-5 minut.

### 3.2. Skonfiguruj zmienne środowiskowe (opcjonalne)

Frontend domyślnie łączy się z `http://localhost:8000/api`. Jeśli chcesz zmienić URL backendu:

```bash
# Utwórz plik .env w katalogu frontend
echo "REACT_APP_API_URL=http://localhost:8000/api" > .env
```

---

## ▶️ Krok 4: Uruchomienie Aplikacji

Aplikacja składa się z dwóch serwerów, które muszą działać jednocześnie:

### 4.1. Uruchom Backend (Terminal 1)

```bash
# Przejdź do katalogu backend
cd portfolio-tracker-pro/backend

# Aktywuj virtualenv (jeśli jeszcze nie jest aktywny)
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Uruchom serwer
python main.py

# Alternatywnie, jeśli main.py nie działa:
# uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend będzie dostępny na: `http://localhost:8000`

### 4.2. Uruchom Frontend (Terminal 2)

```bash
# Przejdź do katalogu frontend
cd portfolio-tracker-pro/frontend

# Uruchom serwer deweloperski
npm start
```

Frontend automatycznie otworzy się w przeglądarce na: `http://localhost:3000`

---

## ✅ Krok 5: Weryfikacja Instalacji

1. **Backend działa?**
   - Sprawdź: `http://localhost:8000/docs` - powinna się otworzyć dokumentacja API (Swagger)

2. **Frontend działa?**
   - Sprawdź: `http://localhost:3000` - powinna się otworzyć strona logowania

3. **Utwórz konto**
   - Kliknij "Register" na stronie logowania
   - Utwórz nowe konto użytkownika

4. **Zaloguj się**
   - Zaloguj się nowo utworzonym kontem

---

## 🐛 Rozwiązywanie Problemów

### Backend nie startuje

**Problem:** `ModuleNotFoundError` lub brak modułu
```bash
# Upewnij się, że virtualenv jest aktywny i zależności są zainstalowane
cd backend
source venv/bin/activate  # macOS/Linux
# lub venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

**Problem:** Port 8000 już zajęty
```bash
# Windows - znajdź proces na porcie 8000
netstat -ano | findstr :8000

# macOS/Linux - znajdź proces na porcie 8000
lsof -i :8000

# Zabij proces lub zmień port w main.py
```

**Problem:** Błąd z bazą danych
```bash
# Usuń starą bazę danych (utworzy się nowa automatycznie)
cd backend
rm portfolio_tracker.db  # macOS/Linux
# lub del portfolio_tracker.db  # Windows
```

### Frontend nie startuje

**Problem:** Port 3000 już zajęty
```bash
# Zmień port w package.json lub użyj zmiennej środowiskowej
PORT=3001 npm start  # macOS/Linux
# lub set PORT=3001 && npm start  # Windows
```

**Problem:** `npm install` nie działa
```bash
# Usuń node_modules i spróbuj ponownie
rm -rf node_modules package-lock.json  # macOS/Linux
# lub rmdir /s node_modules i del package-lock.json  # Windows
npm install
```

**Problem:** Błędy kompilacji TypeScript
```bash
# Wyczyść cache i spróbuj ponownie
rm -rf node_modules/.cache  # macOS/Linux
npm start
```

### Błędy połączenia Frontend-Backend

**Problem:** Frontend nie może połączyć się z backendem
- Sprawdź, czy backend działa: `http://localhost:8000/docs`
- Sprawdź `CORS_ORIGINS` w `.env` backendu - powinno zawierać `http://localhost:3000`
- Sprawdź, czy firewall nie blokuje portów

**Problem:** 401 Unauthorized przy logowaniu
- Sprawdź `SECRET_KEY` w `.env` backendu - musi być ustawiony
- Sprawdź logi backendu w terminalu

### Inne problemy

**Problem:** Aplikacja działa, ale nie widzę transakcji
- To normalne - musisz najpierw zsynchronizować transakcje
- Przejdź do zakładki "Transactions" i kliknij "Sync Transactions"
- Upewnij się, że masz skonfigurowane API keys dla giełd

**Problem:** Dashboard pokazuje puste dane
- Kliknij przycisk "Load Dashboard" na stronie głównej
- Dashboard ładuje dane ręcznie (nie automatycznie)

---

## 📚 Dodatkowe Informacje

### Struktura Projektu

```
portfolio-tracker-pro/
├── backend/              # Python FastAPI backend
│   ├── main.py          # Główny plik aplikacji
│   ├── database.py      # Zarządzanie bazą danych SQLite
│   ├── requirements.txt # Zależności Python
│   └── .env            # Zmienne środowiskowe (nie commituj!)
│
└── frontend/            # React TypeScript frontend
    ├── src/            # Kod źródłowy
    ├── package.json    # Zależności Node.js
    └── .env           # Zmienne środowiskowe (opcjonalne)
```

### API Keys - Jak uzyskać?

#### Binance
1. Zaloguj się na https://www.binance.com
2. Przejdź do Account > API Management
3. Utwórz nowy klucz API (tylko do odczytu - Read Only)
4. Skopiuj API Key i Secret Key do `.env`

#### Bybit
1. Zaloguj się na https://www.bybit.com
2. Przejdź do Account & Security > API Management
3. Utwórz nowy klucz API (tylko do odczytu)
4. Skopiuj API Key i Secret Key do `.env`

#### XTB
1. Skontaktuj się z XTB w sprawie dostępu do API
2. Otrzymasz User ID i Password
3. Wpisz je do `.env` jako `XTB_USERNAME` i `XTB_PASSWORD`

### Bezpieczeństwo

⚠️ **WAŻNE:**
- **NIGDY** nie commituj pliku `.env` do Git (jest w `.gitignore`)
- Używaj tylko uprawnień **Read Only** dla API keys
- Regularnie zmieniaj swoje klucze API
- `SECRET_KEY` powinien być unikalny dla każdego środowiska

---

## 🎉 Gotowe!

Po wykonaniu wszystkich kroków aplikacja powinna działać. Jeśli masz problemy, sprawdź sekcję "Rozwiązywanie Problemów" powyżej.

**Następne kroki:**
1. Zaloguj się do aplikacji
2. Przejdź do "Transactions" i zsynchronizuj transakcje
3. Przejdź do "Dashboard" i załaduj dane
4. Ciesz się aplikacją! 🚀

---

## 📞 Wsparcie

Jeśli napotkasz problemy, które nie są opisane w tym przewodniku:
1. Sprawdź logi backendu (w terminalu, gdzie uruchomiłeś `python main.py`)
2. Sprawdź konsolę przeglądarki (F12 > Console)
3. Sprawdź, czy wszystkie wymagania są spełnione

