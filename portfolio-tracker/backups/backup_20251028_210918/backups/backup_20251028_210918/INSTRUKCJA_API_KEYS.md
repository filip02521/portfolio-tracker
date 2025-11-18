# 🔐 Jak dodać API Keys na Streamlit Cloud

## ✅ Ważne - Twój projekt jest już skonfigurowany!

Plik `config.py` został zaktualizowany, aby działał zarówno lokalnie (z plikiem `.env`) jak i na Streamlit Cloud (z Secrets).

---

## 📍 Gdzie dodać API Keys?

### Na Streamlit Cloud:

1. **Wejdź na stronę swojej aplikacji:**
   ```
   https://fportfolio-tracker.streamlit.app/
   ```

2. **Kliknij na ikonę ⚙️ (koło zębate) w prawym górnym rogu**

3. **Wybierz "⚙️ Settings"** z menu

4. **Przejdź do zakładki "Secrets"**

5. **Kliknij "Edit secrets"**

6. **Wklej poniższy kod** i zamień wartości na swoje prawdziwe klucze API:

```toml
BINANCE_API_KEY = "twoj_binance_api_key_tutaj"
BINANCE_SECRET_KEY = "twoj_binance_secret_key_tutaj"
BYBIT_API_KEY = "twoj_bybit_api_key_tutaj"
BYBIT_SECRET_KEY = "twoj_bybit_secret_key_tutaj"
```

7. **Kliknij "Save"**

Streamlit automatycznie przeładuje aplikację!

---

## 📝 Przykład wypełnionego pliku:

```toml
BINANCE_API_KEY = "abc123def456ghi789"
BINANCE_SECRET_KEY = "xyz789uvw456rst123"
BYBIT_API_KEY = "bybit_key_12345"
BYBIT_SECRET_KEY = "bybit_secret_67890"
XTB_USER_ID = "12345678"
XTB_PASSWORD = "moje_haslo_xTB"
```

---

## 🔍 Jak sprawdzić czy działa?

Po zapisaniu Secrets:

1. Streamlit automatycznie przeładuje aplikację
2. W sidebarze (lewa strona) zobaczysz status giełd:
   - ✅ **Zielone** = API Key skonfigurowany i działa
   - ⚠️ **Żółte** = Brak API Key lub błąd połączenia

---

## 🐛 Rozwiązywanie problemów

### Problem: "command not found: 'eval"
To błąd w pliku `.zprofile` - nie wpływa na aplikację Streamlit.

### Problem: Aplikacja nie działa
1. Sprawdź czy wszystkie API Keys są poprawnie wklejone w Secrets
2. Sprawdź czy nie ma dodatkowych spacji lub cudzysłowów
3. Sprawdź logi: W Settings → "Show logs"

### Problem: Błędy połączenia z giełdami
1. Sprawdź czy API Keys są aktywne
2. Upewnij się że klucze mają uprawnienia do odczytu (Read-only)
3. Sprawdź czy IP na giełdzie nie jest zablokowane

---

## 💡 Przydatne linki

- **Streamlit Cloud Dashboard:** https://share.streamlit.io
- **Twój projekt:** https://fportfolio-tracker.streamlit.app/

---

## 🔄 Jak aktualizować kod

Po każdej zmianie w kodzie:

```bash
cd /Users/Filip/portfolio-tracker
git add .
git commit -m "Opis zmian"
git push
```

Streamlit Cloud automatycznie wykryje zmiany i przeładuje aplikację!

---

**Gotowe! 🎉**

