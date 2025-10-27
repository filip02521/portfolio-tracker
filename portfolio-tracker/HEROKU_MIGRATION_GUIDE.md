# 🚀 Migracja na Heroku - Instrukcja

## Dlaczego Heroku?

✅ **Statyczne IP adresy** - można dodać do whitelist w Binance/Bybit  
✅ **Lepsze zasoby** - więcej RAM i CPU niż Streamlit Cloud  
✅ **Stabilność** - mniej problemów z timeoutami  
✅ **Kontrola** - pełna kontrola nad środowiskiem  

## 📋 Kroki migracji

### 1. Przygotowanie aplikacji ✅
- [x] Utworzony `Procfile` 
- [x] Utworzony `runtime.txt`
- [x] Sprawdzony `requirements.txt`

### 2. Instalacja Heroku CLI
```bash
# macOS (z Homebrew)
brew tap heroku/brew && brew install heroku

# Lub pobierz z: https://devcenter.heroku.com/articles/heroku-cli
```

### 3. Logowanie do Heroku
```bash
heroku login
```

### 4. Utworzenie aplikacji Heroku
```bash
# W katalogu projektu
heroku create portfolio-tracker-filip

# Lub z określeniem regionu (Europa)
heroku create portfolio-tracker-filip --region eu
```

### 5. Konfiguracja zmiennych środowiskowych
```bash
# Dodaj API keys
heroku config:set BINANCE_API_KEY="your_binance_api_key"
heroku config:set BINANCE_SECRET_KEY="your_binance_secret_key"
heroku config:set BYBIT_API_KEY="your_bybit_api_key" 
heroku config:set BYBIT_SECRET_KEY="your_bybit_secret_key"
```

### 6. Wdrożenie aplikacji
```bash
git add .
git commit -m "Prepare for Heroku deployment"
git push heroku main
```

### 7. Otwarcie aplikacji
```bash
heroku open
```

## 🔧 Konfiguracja API po wdrożeniu

### 1. Pobierz IP adres Heroku
```bash
heroku run curl ifconfig.me
```

### 2. Dodaj IP do whitelist w Binance
1. Zaloguj się do Binance
2. Przejdź do API Management
3. Edytuj swój klucz API
4. Dodaj IP adres Heroku do "Restrict access to trusted IPs only"

### 3. Dodaj IP do whitelist w Bybit
1. Zaloguj się do Bybit
2. Przejdź do API Management
3. Edytuj swój klucz API
4. Dodaj IP adres Heroku do "IP Whitelist"

## 📊 Monitoring

### Logi aplikacji
```bash
heroku logs --tail
```

### Status aplikacji
```bash
heroku ps
```

### Restart aplikacji
```bash
heroku restart
```

## 💰 Koszty

- **Heroku Hobby** ($7/miesiąc): Wystarczy dla aplikacji portfolio
- **Heroku Basic** ($25/miesiąc): Jeśli potrzebujesz więcej zasobów

## 🆘 Rozwiązywanie problemów

### Problem: Aplikacja nie startuje
```bash
heroku logs --tail
# Sprawdź błędy w logach
```

### Problem: API nie działa
1. Sprawdź czy IP jest dodane do whitelist
2. Sprawdź zmienne środowiskowe: `heroku config`
3. Sprawdź logi: `heroku logs --tail`

### Problem: Brak pamięci
```bash
# Zwiększ dyno
heroku ps:scale web=1:standard-1x
```

## 🎯 Następne kroki

1. ✅ Wdrożenie na Heroku
2. ✅ Konfiguracja API keys
3. ✅ Dodanie IP do whitelist
4. ✅ Testowanie funkcjonalności
5. ✅ Migracja domeny (opcjonalnie)

