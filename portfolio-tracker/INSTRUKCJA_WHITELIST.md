# 📋 Instrukcja: Dodanie IP Railway do Whitelist

## 🎯 Cel
Dodanie IP adresu Railway do whitelist w Binance i Bybit, aby API mogły działać.

## 🌐 IP Adres Railway: `78.142.224.51`

---

## 🔵 Binance - Dodanie IP do Whitelist

### Krok 1: Zaloguj się do Binance
1. Wejdź na https://www.binance.com/
2. Zaloguj się na swoje konto

### Krok 2: Przejdź do API Management
1. Kliknij prawy górny róg (ikonka profilu)
2. Wybierz **"API Management"**
3. Wybierz **"Edit"** dla swojego klucza API

### Krok 3: Dodaj IP do Whitelist
1. W sekcji **"Restrict access to trusted IPs only"**
2. Wklej IP: `78.142.224.51`
3. Kliknij **"Save"**

### Krok 4: Potwierdzenie
- Otrzymasz email z potwierdzeniem zmian

---

## 🟢 Bybit - Dodanie IP do Whitelist

### Krok 1: Zaloguj się do Bybit
1. Wejdź na https://www.bybit.com/
2. Zaloguj się na swoje konto

### Krok 2: Przejdź do API Management
1. Przejdź do **Settings** (⚙️)
2. Wybierz **"API"** lub **"API Keys"**

### Krok 3: Dodaj IP do Whitelist
1. Wybierz **"Edit"** dla swojego klucza API
2. W sekcji **"IP Whitelist"**
3. Wklej IP: `78.142.224.51`
4. Kliknij **"Confirm"**

### Krok 4: Potwierdzenie
- IP zostanie dodane do whitelist

---

## ✅ Po dodaniu IP

1. Poczekaj **2-3 minuty** na propagację zmian
2. Przejdź do aplikacji: https://portfolio-tracker-production-b6ae.up.railway.app
3. Sprawdź czy API działa:
   - Kliknij "Synchronizuj z API"
   - Powinieneś zobaczyć transakcje z Binance i Bybit

---

## 🔧 Jeśli API nadal nie działa

### Problem: "Restricted location" (Binance)
- Sprawdź czy IP jest na whitelist
- Poczekaj 5 minut na propagację

### Problem: "IP is from the USA" (Bybit)
- Sprawdź czy IP jest na whitelist
- Railway używa europejskich serwerów

### Problem: Rate Limit
- To normalne - poczekaj 1 minutę i spróbuj ponownie

---

## 📊 Status IP Whitelist

**Binance:** ⏳ Do skonfigurowania  
**Bybit:** ⏳ Do skonfigurowania

---

## 🎯 Po zakończeniu

Aplikacja będzie działać **dokładnie jak lokalnie**, z prawdziwymi danymi z Binance i Bybit!

**Gotowe?** Przejdź do pliku `KROK_PO_KROKU.md` żeby zobaczyć co dalej.
