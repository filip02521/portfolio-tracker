# 🔧 Jak skonfigurować XTB

## ⚠️ Ważne informacje o XTB API

XTB wymaga **specjalnego dostępu do API** - nie działa automatycznie jak Binance czy Bybit.

## 📋 Kroki konfiguracji:

### Krok 1: Sprawdź plik .env

Otwórz plik `.env` w katalogu projektu i sprawdź czy masz:

```env
XTB_USER_ID=twoj_user_id
XTB_PASSWORD=twoje_haslo
```

### Krok 2: Skontaktuj się z supportem XTB

**XTB wymaga aktywacji API przez support!**

1. Zaloguj się na https://www.xtb.com
2. Przejdź do sekcji **"Wsparcie"** lub **"Kontakt"**
3. Napisz email/zadzwoń i poproś o:
   - Dostęp do **xStation API**
   - Aktywację API dla Twojego konta
   - Instrukcje jak uzyskać User ID i Password dla API

### Krok 3: Różnica między kontem demo a real

⚠️ **Ważne:** XTB ma osobne API dla:
- **Konto demo** - endpoint: `https://xapi-demo.xtb.com`
- **Konto real** - endpoint: `https://xapi.xtb.com`

Upewnij się że używasz właściwego User ID i Password dla swojego typu konta!

### Krok 4: Sprawdź czy masz dostęp

Po otrzymaniu dostępu do API od XTB:

1. Sprawdź czy User ID i Password są poprawne
2. Jeśli masz konto **demo**, musisz zmienić endpoint w kodzie

## 🔧 Naprawa dla konta demo XTB

Jeśli masz konto demo, edytuj plik `exchanges/xtb_client.py`:

```python
# Zmień linię 19 z:
self.base_url = "https://xapi.xtb.com"

# Na:
self.base_url = "https://xapi-demo.xtb.com"
```

## 🚫 Alternatywa: Dodać XTB ręcznie

Jeśli XTB API nie działa, możesz:

1. **Ustawić cenę zakupu ręcznie** dla pozycji XTB w aplikacji
2. **Dodać transakcje** w sekcji PNL
3. Portfolio XTB będzie pokazywane jako $0, ale możesz śledzić transakcje ręcznie

## 📞 Kontakt z XTB

- Email: support@xtb.com
- Telefon: +48 22 250 08 00
- Chat online na stronie XTB

## ✅ Po poprawnym skonfigurowaniu

XTB będzie działać tak samo jak Binance i Bybit:
- Automatyczne pobieranie portfolio
- Wyświetlanie pozycji
- Obliczanie wartości

