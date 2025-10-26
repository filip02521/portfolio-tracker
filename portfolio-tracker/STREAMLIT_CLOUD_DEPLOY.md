# 🚀 Deployment na Streamlit Cloud - Instrukcja krok po kroku

## ✅ Krok 1: Projekt jest gotowy!
- Git zainicjalizowany ✓
- .gitignore skonfigurowany ✓  
- Pierwszy commit zrobiony ✓
- API keys bezpieczne (.env nie będzie w Git) ✓

---

## 📝 Krok 2: Utwórz repozytorium na GitHub

1. **Zaloguj się na GitHub:** https://github.com
2. **Kliknij "+" → "New repository"**
3. **Ustawienia:**
   - Repository name: `portfolio-tracker` (lub dowolna nazwa)
   - Description: "Professional Portfolio Tracker for Binance, Bybit, XTB"
   - **Visibility: PRIVATE** (ważne!)
   - **NIE zaznaczaj** "Add README" ani "Add .gitignore"
4. **Kliknij "Create repository"**

---

## 📤 Krok 3: Push projektu na GitHub

W terminalu wykonaj:

```bash
cd /Users/Filip/portfolio-tracker

# Dodaj remote GitHub
git remote add origin https://github.com/TWOJA_NAZWA/portfolio-tracker.git

# Push na GitHub
git branch -M main
git push -u origin main
```

**Zastąp `TWOJA_NAZWA` swoją nazwą użytkownika GitHub!**

Przykład:
```bash
git remote add origin https://github.com/filipmasny/portfolio-tracker.git
```

---

## 🌐 Krok 4: Deploy na Streamlit Cloud

1. **Wejdź na:** https://share.streamlit.io
2. **Zaloguj się GitHubem** (Sign in with GitHub)
3. **Kliknij "New app"**
4. **Ustawienia:**
   - **Repository:** Wybierz `portfolio-tracker`
   - **Branch:** `main`
   - **Main file path:** `streamlit_app.py`
   - **Python version:** Auto (latest)
5. **Kliknij "Deploy"**

Streamlit Cloud zacznie budować aplikację (2-3 minuty).

---

## 🔐 Krok 5: Dodaj Secrets (klucze API)

1. **W Streamlit Cloud** kliknij "⚙️ Manage app"
2. **Przejdź do zakładki "Secrets"**
3. **Kliknij "Edit secrets"**
4. **Dodaj swoje klucze API:**

```toml
BINANCE_API_KEY = "twoj_binance_api_key"
BINANCE_SECRET_KEY = "twoj_binance_secret_key"
BYBIT_API_KEY = "twoj_bybit_api_key"
BYBIT_SECRET_KEY = "twoj_bybit_secret_key"
XTB_USER_ID = "twoj_xtb_user_id"
XTB_PASSWORD = "twoj_xtb_password"
```

5. **Kliknij "Save"**

⚠️ **Ważne:** Streamlit automatycznie przeładuje aplikację po zapisaniu Secrets.

---

## 🎉 Gotowe!

Twoja aplikacja będzie dostępna pod adresem:
```
https://nazwa-uzytkownika-portfolio-tracker.streamlit.app
```

Możesz otworzyć ją na telefonie, tablecie, komputerze - gdziekolwiek!

---

## 🔄 Jak aktualizować aplikację?

Wystarczy push na GitHub:

```bash
git add .
git commit -m "Opis zmian"
git push
```

Streamlit Cloud automatycznie wykryje zmiany i przeładuje aplikację!

---

## ❓ FAQ

**Q: Czy moje klucze API są bezpieczne?**
A: Tak! Secrets są szyfrowane i widoczne tylko dla Ciebie.

**Q: Czy mogę użyć prywatnego repozytorium?**
A: Tak! Streamlit Cloud działa z prywatnymi repozytoriami.

**Q: Co jeśli mam błąd deployment?**
A: Sprawdź logi w Streamlit Cloud → Settings → Logs

**Q: Jak zatrzymać/deletować aplikację?**
A: W Settings → Delete app

---

## 📱 Używanie na telefonie

Po deployment po prostu otwórz URL w przeglądarce na telefonie. 
Streamlit automatycznie dostosowuje się do ekranu mobilnego!

---

**Szczęśliwego tradingu! 📊**
