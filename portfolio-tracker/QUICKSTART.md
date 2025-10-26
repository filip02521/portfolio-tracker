# 🚀 Quick Start Guide

## Krok 1: Zainstaluj zależności

```bash
pip install -r requirements.txt
```

## Krok 2: Skonfiguruj API klucze

```bash
cp env.example .env
```

Następnie edytuj plik `.env` i dodaj swoje klucze API.

### Przykład - tylko Binance:

```env
BINANCE_API_KEY=twoj_klucz_api
BINANCE_SECRET_KEY=twoj_secret_key
```

### Przykład - wszystkie giełdy:

```env
BINANCE_API_KEY=twoj_klucz_api
BINANCE_SECRET_KEY=twoj_secret_key

BYBIT_API_KEY=twoj_klucz_api
BYBIT_SECRET_KEY=twoj_secret_key

XTB_USER_ID=twoj_user_id
XTB_PASSWORD=twoje_haslo
```

## Krok 3: Uruchom aplikację

```bash
python main.py
```

## Przykładowy output:

```
============================================================
🚀 Portfolio Tracker - XTB, Binance, Bybit
============================================================

✓ Binance initialized successfully
✓ Bybit initialized successfully
⚠ XTB: XTB credentials not configured

================================================================================
PORTFOLIO SUMMARY
================================================================================

📊 Binance:
Total Value: $1,234.56 USDT
┌────────┬──────────────┬──────────────┬─────────────┐
│ Asset  │ Total        │ Available    │ Locked      │
├────────┼──────────────┼──────────────┼─────────────┤
│ BTC    │ 0.50000000   │ 0.50000000   │ 0.00000000  │
│ USDT   │ 500.00000000 │ 500.00000000 │ 0.00000000  │
└────────┴──────────────┴──────────────┴─────────────┘

📊 Bybit:
Total Value: $567.89 USDT
...

💼 TOTAL PORTFOLIO VALUE: $1,802.45 USDT
================================================================================

📊 ALLOCATION BY EXCHANGE:
------------------------------------------------------------
Binance         $1,234.56 ( 68.45%)
Bybit           $567.89 ( 31.55%)

✅ Portfolio tracking completed successfully!
```

## 🔑 Jak uzyskać API klucze?

### Binance
1. Zaloguj się na https://www.binance.com
2. Przejdź do Account > API Management
3. Utwórz nowy klucz API (tylko do odczytu!)
4. Skopiuj API Key i Secret Key

### Bybit
1. Zaloguj się na https://www.bybit.com
2. Przejdź do Account & Security > API Management
3. Utwórz nowy klucz API (tylko do odczytu!)
4. Skopiuj API Key i Secret Key

### XTB
1. Zaloguj się na https://www.xtb.com
2. Skontaktuj się z supportem w sprawie dostępu do API
3. Otrzymasz User ID i Password

## ⚠️ Ważne uwagi bezpieczeństwa

- **NIGDY** nie udostępniaj swoich kluczy API innym osobom
- Używaj **tylko uprawnień do odczytu** dla kluczy API
- Plik `.env` jest już w `.gitignore` - nie commituj go do repozytorium
- Regularnie zmieniaj swoje klucze API

## ❓ Troubleshooting

### Błąd: "No exchanges configured"
Sprawdź czy plik `.env` istnieje i zawiera poprawne klucze API.

### Błąd: "Failed to initialize Binance"
- Sprawdź czy klucze API są poprawne
- Upewnij się że klucze mają uprawnienia do odczytu
- Sprawdź połączenie z internetem

### XTB nie działa
XTB wymaga osobnego dostępu do API - skontaktuj się z supportem XTB.


