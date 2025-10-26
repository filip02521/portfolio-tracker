# 🌐 Przewodnik: Jak uruchomić aplikację na telefonie

## Opcja 1: Ngrok (Najszybsze - tunel do Twojego komputera)

### Instalacja Ngrok:
```bash
# macOS
brew install ngrok

# Lub pobierz z: https://ngrok.com/download
```

### Konfiguracja:
1. Zarejestruj się na https://ngrok.com (darmowe)
2. Pobierz token autoryzacyjny
3. Autoryzuj ngrok:
```bash
ngrok config add-authtoken YOUR_TOKEN_HERE
```

### Uruchomienie:
```bash
# Terminal 1: Uruchom aplikację Streamlit
cd /Users/Filip/portfolio-tracker
source .venv/bin/activate
streamlit run streamlit_app.py

# Terminal 2: Uruchom ngrok tunel
ngrok http 8501
```

### Wynik:
Ngrok wyświetli publiczny URL, np.:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:8501
```

**Ten URL działa z telefonu z dowolnego miejsca!**

⚠️ **Ważne:** URL zmienia się przy każdym uruchomieniu (w darmowej wersji). Zapisz go.

---

## Opcja 2: Streamlit Cloud (Trwałe rozwiązanie - zalecane)

### Zalety:
- ✅ Działanie 24/7
- ✅ Stały URL
- ✅ Darmowe
- ✅ Automatyczne aktualizacje z GitHub

### Kroki:

#### 1. Zainicjalizuj Git w projekcie:
```bash
cd /Users/Filip/portfolio-tracker
git init
git add .
git commit -m "Initial commit"
```

#### 2. Utwórz repozytorium na GitHub:
- Wejdź na https://github.com/new
- Utwórz nowe repozytorium (np. `portfolio-tracker`)
- **WAŻNE:** Nie dodawaj `.env` do repozytorium!

#### 3. Dodaj .gitignore:
```bash
# Sprawdź czy .gitignore istnieje i zawiera:
echo ".env" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
echo ".venv/" >> .gitignore
echo "*.log" >> .gitignore
```

#### 4. Push do GitHub:
```bash
git remote add origin https://github.com/TWOJA_NAZWA/portfolio-tracker.git
git branch -M main
git push -u origin main
```

#### 5. Deploy na Streamlit Cloud:
1. Wejdź na https://share.streamlit.io
2. Zaloguj się GitHubem
3. Kliknij "New app"
4. Wybierz swoje repozytorium
5. Ustaw Main file path: `streamlit_app.py`
6. Kliknij "Deploy"

#### 6. Konfiguracja zmiennych środowiskowych:
1. W Streamlit Cloud, przejdź do Settings
2. Dodaj "Secrets" z Twoimi kluczami API:
```
BINANCE_API_KEY=twoj_klucz
BINANCE_SECRET_KEY=twoj_secret
BYBIT_API_KEY=twoj_klucz
BYBIT_SECRET_KEY=twoj_secret
XTB_USER_ID=twoj_user_id
XTB_PASSWORD=twoje_haslo
```

### Wynik:
Otrzymasz stały URL: `https://twoja-nazwa.streamlit.app`

---

## Opcja 3: Render.com (Alternatywa dla Streamlit Cloud)

### Kroki:
1. Utwórz konto na https://render.com
2. Połącz z GitHub
3. Utwórz "Web Service"
4. Wybierz swoje repozytorium
5. Build Command: `pip install -r requirements.txt`
6. Start Command: `streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0`
7. Dodaj zmienne środowiskowe

---

## Opcja 4: Lokalny serwer z WireGuard VPN

### Wymagania:
- Komputer z macOS/Linux
- Stały adres IP (router)

### Konfiguracja:
1. Zainstaluj WireGuard na komputerze
2. Skonfiguruj VPN
3. Uruchom Streamlit na IP lokalnym
4. Połącz telefon przez VPN

---

## 🎯 Rekomendacja

**Dla szybkiego testu:** Ngrok (Opcja 1)
**Dla produkcji:** Streamlit Cloud (Opcja 2)

---

## 📱 Środki bezpieczeństwa

⚠️ **WAŻNE - Nigdy nie commituj `.env` do Git!**

Twój `.gitignore` powinien zawierać:
```
.env
.env.local
*.log
__pycache__/
*.pyc
.venv/
```

### Bezpieczeństwo kluczy API:
- Używaj tylko uprawnień READ-ONLY
- Regularnie zmieniaj klucze
- Nigdy nie udostępniaj kluczy innym

---

## 🚀 Quick Start Script (Ngrok)

Utwórz plik `start_mobile.sh`:
```bash
#!/bin/bash
cd /Users/Filip/portfolio-tracker
source .venv/bin/activate

# Terminal 1: Start Streamlit
streamlit run streamlit_app.py &

# Terminal 2: Start Ngrok (wymaga osobnego terminala)
ngrok http 8501
```

Chmod:
```bash
chmod +x start_mobile.sh
```

---

## 📞 Jak używać na telefonie

1. Uruchom aplikację lokalnie lub na Streamlit Cloud
2. Otwórz przeglądarkę na telefonie
3. Wpisz URL z ngrok lub Streamlit Cloud
4. Ciesz się dostępem do swojego portfolio! 📊
