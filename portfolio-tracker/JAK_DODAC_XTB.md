# 📝 Jak wprowadzić XTB - Instrukcja krok po kroku

## 🎯 Problem: XTB nie działa bo masz przykładowe dane

W pliku `.env` masz teraz:
```env
XTB_USER_ID=your_xtb_user_id_here
XTB_PASSWORD=your_xtb_password_here
```

To są **przykładowe wartości** - trzeba je zamienić na prawdziwe!

## 🔧 Rozwiązanie - 3 opcje:

### Opcja 1: Jeśli MASZ konto XTB z dostępem do API

**Krok 1:** Otwórz plik `.env` w edytorze tekstu

**Krok 2:** Znajdź linie z XTB i zamień na swoje dane:

```env
# XTB Credentials
XTB_USER_ID=12345678
XTB_PASSWORD=TwojePrawdzoweHaslo123
```

**Krok 3:** Zapisz plik

**Krok 4:** Odśwież aplikację w przeglądarce

---

### Opcja 2: Jeśli MASZ konto XTB BEZ dostępu do API

**Krok 1:** Skontaktuj się z supportem XTB:
- Email: support@xtb.com
- Telefon: +48 22 250 08 00
- Chat: https://www.xtb.com/pl/kontakt

**Krok 2:** Poproś o:
- Dostęp do **xStation API**
- User ID dla API
- Password dla API

**Krok 3:** Po otrzymaniu danych, zmień w pliku `.env` (jak w Opcji 1)

---

### Opcja 3: Jeśli NIE MASZ konta XTB lub API nie działa

**Po prostu zignoruj XTB!**

Aplikacja działa świetnie z tylko Binance i Bybit:
- ✅ Binance: ~$524 USDT
- ✅ Bybit: ~$3,032 USDT
- ✅ Razem: ~$3,556 USDT

XTB może zostać nieaktywny - aplikacja będzie działać bez niego.

---

## 🎯 Co zrobić TERAZ:

### 1. Edytuj plik .env:

```bash
nano .env
```

Albo użyj dowolnego edytora tekstu.

### 2. Zmień linie XTB:

```env
# BYŁO:
XTB_USER_ID=your_xtb_user_id_here
XTB_PASSWORD=your_xtb_password_here

# ZMIEŃ NA (jeśli masz prawdziwe dane):
XTB_USER_ID=12345678
XTB_PASSWORD=TwojeHaslo123
```

### 3. Jeśli używasz konta DEMO:

Zmień endpoint w pliku `exchanges/xtb_client.py`:

```python
# Linia 19 - zmień na:
self.base_url = "https://xapi-demo.xtb.com"
```

### 4. Odśwież aplikację

Aplikacja automatycznie załaduje nowe dane!

---

## ⚠️ Ważne uwagi:

1. **XTB wymaga specjalnego dostępu** - nie działa jak Binance/Bybit
2. **Konto demo vs real** - różne endpointy API
3. **Password trzeba hashować** - aplikacja robi to automatycznie
4. **Bezpieczeństwo** - plik `.env` NIE jest commited do git!

---

## 💡 Najlepsze rozwiązanie:

**Jeśli XTB nie działa** - po prostu korzystaj z Binance i Bybit!

Aplikacja działa świetnie z 2 giełdami i możesz śledzić:
- ✅ Wartość portfolio
- ✅ Alokację na giełdy
- ✅ Top aktywa
- ✅ PNL dla każdego aktywa

XTB możesz dodać później gdy uzyskasz dostęp do API.

