# 📱 Jak uruchomić aplikację w pracy

## 🎯 Rozwiązanie problemu z API

Railway nie ma statycznego IP, więc Bybit/Binance IP whitelist nie działa.

**ROZWIĄZANIE**: Uruchom aplikację lokalnie + Ngrok = dostęp z dowolnego miejsca! ✅

---

## 🚀 URUCHOMIENIE (3 KROKI)

### KROK 1: Otwórz Terminal i wpisz:

```bash
cd /Users/Filip/portfolio-tracker
./START_PRACY.sh
```

To uruchomi Streamlit lokalnie.

---

### KROK 2: Otwórz NOWY terminal i wpisz:

```bash
ngrok http 8501
```

Zobaczysz coś takiego:
```
Forwarding  https://abc123.ngrok-free.app -> http://localhost:8501
```

**Skopiuj URL** (ten z https://...)

---

### KROK 3: Otwórz na telefonie w pracy:

1. Otwórz przeglądarkę na telefonie
2. Wklej URL z Ngrok (np. `https://abc123.ngrok-free.app`)
3. ✅ **DZIAŁA!** API będzie działać bo używa Twojego lokalnego IP!

---

## ✅ Zalety tego rozwiązania

- ✅ API **DZIAŁA** (używasz swojego lokalnego IP)
- ✅ Dostęp **z dowolnego miejsca** (Ngrok tworzy tunel)
- ✅ **Bezpieczne** (szyfrowany tunel)
- ✅ **Darmowe** (Ngrok free tier)

---

## 🔄 Codzienne użytkowanie

### Rano przed pracą:
1. Otwórz Terminal
2. Wpisz `./START_PRACY.sh`
3. Otwórz nowy terminal i wpisz `ngrok http 8501`
4. Skopiuj URL do telefonu

### Wieczorem po pracy:
1. Zamknij terminale (Ctrl+C)

---

## ⚠️ Ważne

- Ngrok URL zmienia się przy każdym uruchomieniu
- Skopiuj URL ponownie jeśli zrestartujesz ngrok
- Aplikacja działa dopóki terminal jest otwarty

---

## 🐛 Jeśli Ngrok nie działa:

```bash
brew install ngrok
```

Następnie zarejestruj się na https://ngrok.com (darmowe)

---

**Gotowe!** Teraz masz dostęp do aplikacji z pracy! 🎉

