# 🚀 Deployment Guide - Portfolio Tracker Pro

## 📋 Przed rozpoczęciem

### Wymagania:
- Konto GitHub (repo powinno być na GitHub)
- Konto Railway (backend) - [railway.app](https://railway.app)
- Konto Vercel (frontend) - [vercel.com](https://vercel.com)

---

## 🔧 Krok 1: Backend Deployment (Railway)

### 1.1 Przygotowanie
- ✅ Backend jest gotowy (Dockerfile, railway.json)
- ✅ Environment variables są zdefiniowane w `env.example`

### 1.2 Deployment na Railway

1. **Zaloguj się do Railway**
   - Przejdź na [railway.app](https://railway.app)
   - Zaloguj się przez GitHub

2. **Utwórz nowy projekt**
   - Kliknij "New Project"
   - Wybierz "Deploy from GitHub repo"
   - Wybierz swoje repo `portfolio-tracker`
   - Wybierz folder `portfolio-tracker-pro/backend`

3. **Skonfiguruj zmienne środowiskowe**
   - Przejdź do "Variables"
   - Dodaj wszystkie zmienne z `env.example`:
     ```
     SECRET_KEY=twoj-super-secret-key-tutaj
     CORS_ORIGINS=https://twoja-app.vercel.app
     BINANCE_API_KEY=twoj-klucz
     BINANCE_SECRET_KEY=twoj-secret
     # ... itd
     ```
   
   ⚠️ **WAŻNE:**
   - `SECRET_KEY` - zmień na silny, losowy klucz (min. 32 znaki)
   - `CORS_ORIGINS` - dodaj URL swojego frontendu z Vercel (po deploy)
   - Dodaj wszystkie API keys

4. **Deploy**
   - Railway automatycznie wykryje Python i Dockerfile
   - Deploy zacznie się automatycznie
   - Poczekaj na completion (~3-5 minut)

5. **Zapisz Backend URL**
   - Po deploy, Railway da Ci URL (np. `https://backend-production-xxxx.up.railway.app`)
   - Zapisz ten URL - będzie potrzebny dla frontendu

---

## 🎨 Krok 2: Frontend Deployment (Vercel)

### 2.1 Przygotowanie
- ✅ Frontend jest gotowy (`vercel.json`)
- ✅ `.env.example` jest utworzone

### 2.2 Deployment na Vercel

1. **Zaloguj się do Vercel**
   - Przejdź na [vercel.com](https://vercel.com)
   - Zaloguj się przez GitHub

2. **Utwórz nowy projekt**
   - Kliknij "Add New Project"
   - Wybierz swoje repo `portfolio-tracker`
   - W "Root Directory" wybierz: `portfolio-tracker-pro/frontend`

3. **Skonfiguruj build**
   - Framework Preset: **Create React App**
   - Build Command: `npm run build` (auto-detect)
   - Output Directory: `build` (auto-detect)
   
   Vercel automatycznie wykryje ustawienia z `package.json`

4. **Dodaj Environment Variables**
   - Przejdź do "Environment Variables"
   - Dodaj:
     ```
     REACT_APP_API_URL=https://twoj-backend.railway.app/api
     REACT_APP_ENVIRONMENT=production
     ```
   
   ⚠️ Użyj URL z Railway (dodaj `/api` na końcu)

5. **Deploy**
   - Kliknij "Deploy"
   - Poczekaj na build (~2-3 minuty)
   - Vercel da Ci URL (np. `https://portfolio-tracker-pro.vercel.app`)

6. **Update CORS w Railway**
   - Wróć do Railway backend
   - Zaktualizuj `CORS_ORIGINS` z URL frontendu Vercel
   - Redeploy backend (jeśli potrzeba)

---

## 🔄 Krok 3: Weryfikacja

### Sprawdź:

1. **Backend Health Check**
   ```bash
   curl https://twoj-backend.railway.app/api/health
   ```
   Powinien zwrócić: `{"status": "healthy", ...}`

2. **Frontend**
   - Otwórz URL z Vercel
   - Spróbuj się zarejestrować/logować
   - Sprawdź czy API działa

3. **CORS**
   - Otwórz DevTools (F12) → Console
   - Nie powinno być błędów CORS
   - API requests powinny działać

---

## 📝 Zmienne środowiskowe - Checklist

### Backend (Railway):
- [ ] `SECRET_KEY` - silny klucz (min 32 znaki)
- [ ] `CORS_ORIGINS` - URL frontendu z Vercel
- [ ] `BINANCE_API_KEY` (jeśli używasz)
- [ ] `BINANCE_SECRET_KEY` (jeśli używasz)
- [ ] `BYBIT_API_KEY` (jeśli używasz)
- [ ] `BYBIT_SECRET_KEY` (jeśli używasz)
- [ ] `XTB_USERNAME` (jeśli używasz)
- [ ] `XTB_PASSWORD` (jeśli używasz)

### Frontend (Vercel):
- [ ] `REACT_APP_API_URL` - URL backend z Railway + `/api`
- [ ] `REACT_APP_ENVIRONMENT=production`

---

## 🔒 Security Checklist

Przed produkcją upewnij się:

- [ ] `SECRET_KEY` nie jest domyślny
- [ ] `CORS_ORIGINS` nie zawiera `*` (tylko konkretne URL)
- [ ] API keys są prawidłowe
- [ ] HTTPS działa (Railway i Vercel mają automatycznie)
- [ ] Health check endpoint działa

---

## 🐛 Troubleshooting

### Backend nie działa:
- Sprawdź logi w Railway Dashboard
- Upewnij się że port jest `$PORT` (Railway automatycznie ustawia)
- Sprawdź czy wszystkie zmienne środowiskowe są ustawione

### Frontend nie łączy się z backendem:
- Sprawdź `REACT_APP_API_URL` w Vercel
- Sprawdź CORS w Railway (`CORS_ORIGINS`)
- Otwórz DevTools → Network tab i sprawdź requests

### CORS errors:
- Dodaj URL frontendu do `CORS_ORIGINS` w Railway
- Format: `https://twoja-app.vercel.app` (bez końcowego `/`)

---

## 📊 Monitoring

### Railway:
- Dashboard pokazuje CPU, Memory, Network
- Logi są dostępne w czasie rzeczywistym
- Metryki i alerts można skonfigurować

### Vercel:
- Analytics dostępne w dashboardzie
- Function logs dla każdego deploy
- Performance monitoring

---

## 🔄 Automatyczny Deploy

Oba platformy mają automatyczne deploys:
- **Railway**: Automatyczny deploy przy push do `main`
- **Vercel**: Automatyczny deploy przy push do `main`

Możesz wyłączyć auto-deploy w ustawieniach jeśli chcesz manual deploy.

---

## ✅ Gotowe!

Po wykonaniu tych kroków masz:
- ✅ Backend na Railway
- ✅ Frontend na Vercel  
- ✅ Automatyczne HTTPS
- ✅ Automatyczne deploys

**Twoja aplikacja jest live! 🎉**


