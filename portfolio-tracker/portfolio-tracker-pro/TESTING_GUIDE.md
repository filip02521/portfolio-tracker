# 🧪 Przewodnik testowania Portfolio Tracker Pro

## ✅ Status: Gotowe do testów!

Wszystkie funkcjonalności zostały zaimplementowane i są gotowe do testowania.

---

## 🚀 Jak rozpocząć testowanie

### 1. Uruchom backend (jeśli nie działa)
```bash
cd portfolio-tracker-pro/backend
source venv/bin/activate
python main.py
```

### 2. Uruchom frontend (jeśli nie działa)
```bash
cd portfolio-tracker-pro/frontend
npm start
```

### 3. Otwórz przeglądarkę
```
http://localhost:3000
```

---

## 🧪 Scenariusze testowe

### **Test 1: Rejestracja użytkownika**
1. Otwórz `http://localhost:3000`
2. Kliknij "Register" (lub przejdź do `/register`)
3. Wypełnij formularz:
   - Username: `testuser` (minimum 3 znaki)
   - Email: `test@example.com`
   - Password: `test123` (minimum 6 znaków)
   - Confirm Password: `test123`
4. Kliknij "Create Account"
5. **Oczekiwany rezultat**: Komunikat sukcesu i przekierowanie do `/login`

### **Test 2: Logowanie**
1. Na stronie `/login` wprowadź:
   - Username: `testuser`
   - Password: `test123`
2. Kliknij "Sign In"
3. **Oczekiwany rezultat**: 
   - Zalogowanie się
   - Przekierowanie do Dashboard (`/`)
   - Widoczne przyciski nawigacji + przycisk "Logout"

### **Test 3: Ochrona tras**
1. **Bez logowania**:
   - Spróbuj wejść na `/` lub `/portfolio`
   - **Oczekiwany rezultat**: Automatyczne przekierowanie do `/login`

2. **Po zalogowaniu**:
   - Wszystkie trasy powinny być dostępne
   - Nawigacja powinna działać normalnie

### **Test 4: Settings - API Keys**
1. Zaloguj się
2. Przejdź do **Settings** (`/settings`)
3. Zakładka **API Keys**:
   - Sprawdź status kluczy API (Configured/Not Configured)
   - Wprowadź klucze API dla Binance/Bybit/XTB
   - Kliknij "Save"
   - Kliknij "Test Connection" dla każdej giełdy
   - **Oczekiwany rezultat**: Status kluczy, możliwość zapisu i testowania

### **Test 5: Settings - App Settings**
1. W Settings przejdź do zakładki **App Settings**
2. Zmień ustawienia:
   - Enable/Disable Cache
   - Enable/Disable Auto Refresh
   - Zmień Refresh Interval
   - Zmień Currency
3. Kliknij "Save Settings"
4. **Oczekiwany rezultat**: Ustawienia zapisane, komunikat sukcesu

### **Test 6: Settings - Cache Management**
1. W Settings przejdź do zakładki **Cache & Data**
2. Kliknij "Clear All Cache"
3. **Oczekiwany rezultat**: Cache wyczyszczony, komunikat sukcesu

### **Test 7: Logout**
1. Kliknij przycisk "Logout" w prawym górnym rogu
2. **Oczekiwany rezultat**: 
   - Wylogowanie
   - Przekierowanie do `/login`
   - Token usunięty z localStorage

### **Test 8: Dashboard (chronione)**
1. Zaloguj się
2. Sprawdź Dashboard - wszystkie metryki powinny działać
3. Sprawdź auto-refresh (przełącznik w prawym górnym rogu)
4. **Oczekiwany rezultat**: Dane portfolio, wykresy, auto-refresh działa

### **Test 9: Portfolio (chronione)**
1. Zaloguj się
2. Przejdź do Portfolio
3. Sprawdź wyświetlanie aktywów
4. Sprawdź wykresy alokacji
5. **Oczekiwany rezultat**: Dane portfolio, wykresy, możliwość filtrowania

### **Test 10: Transactions (chronione)**
1. Zaloguj się
2. Przejdź do Transactions
3. Przetestuj:
   - Wyświetlanie transakcji
   - Dodawanie nowej transakcji
   - Edycję transakcji
   - Usuwanie transakcji
   - Filtrowanie
   - Export CSV
4. **Oczekiwany rezultat**: Wszystkie operacje CRUD działają

---

## 🔍 Co sprawdzić

### Backend endpoints:
- ✅ `POST /api/auth/register` - rejestracja
- ✅ `POST /api/auth/login` - logowanie
- ✅ `GET /api/auth/me` - informacje o użytkowniku (wymaga tokena)
- ✅ `POST /api/auth/logout` - wylogowanie
- ✅ `GET /api/settings/api-keys` - status kluczy
- ✅ `PUT /api/settings/api-keys/{exchange}` - aktualizacja kluczy
- ✅ `POST /api/settings/test-connection/{exchange}` - test połączenia
- ✅ `GET /api/settings/app` - ustawienia aplikacji
- ✅ `PUT /api/settings/app` - aktualizacja ustawień
- ✅ `POST /api/settings/clear-cache` - czyszczenie cache

### Frontend:
- ✅ Strony Login i Register działają
- ✅ Ochrona tras - redirect do `/login` jeśli niezalogowany
- ✅ Navigation pokazuje Login/Register dla niezalogowanych
- ✅ Navigation pokazuje Logout dla zalogowanych
- ✅ Token jest automatycznie dodawany do requestów
- ✅ 401 error powoduje automatyczny logout i redirect do login

---

## 📝 Uwagi

1. **Pierwsze użycie**: Musisz się zarejestrować przed zalogowaniem
2. **Token**: JWT token jest przechowywany w `localStorage` jako `authToken`
3. **Wygaśnięcie tokena**: Token wygasa po 24 godzinach (domyślnie)
4. **Użytkownicy**: Są przechowywani w pliku `backend/users.json`

---

## 🐛 Rozwiązywanie problemów

### Problem: "Cannot connect to server"
- Sprawdź czy backend działa na `http://localhost:8000`
- Sprawdź logi backendu

### Problem: "401 Unauthorized"
- Sprawdź czy jesteś zalogowany
- Spróbuj się wylogować i zalogować ponownie
- Sprawdź czy token istnieje w localStorage (F12 → Application → Local Storage)

### Problem: Backend nie startuje
- Sprawdź czy wszystkie zależności są zainstalowane: `pip install -r requirements.txt`
- Sprawdź czy `SECRET_KEY` jest ustawiony w `.env` (opcjonalne, ma domyślną wartość)

### Problem: Frontend nie kompiluje się
- Sprawdź czy wszystkie zależności są zainstalowane: `npm install`
- Sprawdź błędy TypeScript w konsoli

---

## ✅ Gotowe do testów!

Wszystko jest skonfigurowane i gotowe. Możesz rozpocząć testowanie!


