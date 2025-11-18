# Portfolio Tracker

Aplikacja do śledzenia portfolio na wielu giełdach: XTB, Binance i Bybit.

## 📋 Wymagania

- Python 3.7+
- API klucze dla wybranych giełd

## 🚀 Instalacja

1. Sklonuj lub pobierz projekt:
```bash
cd portfolio-tracker
```

2. Zainstaluj zależności:
```bash
pip install -r requirements.txt
```

3. Skonfiguruj API klucze:
```bash
cp env.example .env
```

Edytuj plik `.env` i dodaj swoje klucze API. **Aplikacja działa nawet jeśli podasz tylko niektóre giełdy** - np. możesz mieć tylko Binance i Bybit.

## 📖 Użycie

### Wersja GUI (zalecana) 🌐

Aplikacja webowa z interfejsem graficznym - dostępna na komputerze i telefonie:

```bash
source .venv/bin/activate
streamlit run streamlit_app.py
```

Otwórz przeglądarkę i wejdź na: `http://localhost:8501`

**Dostęp z telefonu**: Użyj Network URL z terminala, gdy aplikacja się uruchomi

### Wersja konsolowa 💻

```bash
python main.py
```

## 🔑 Jak uzyskać API klucze

### Binance
1. Zaloguj się na https://www.binance.com
2. Przejdź do Account > API Management
3. Utwórz nowy klucz API
4. Skopiuj API Key i Secret Key

### Bybit
1. Zaloguj się na https://www.bybit.com
2. Przejdź do Account & Security > API Management
3. Utwórz nowy klucz API
4. Skopiuj API Key i Secret Key

### XTB
1. Skontaktuj się z XTB w sprawie dostępu do API
2. Otrzymasz User ID i Password

## ⚠️ Uwagi bezpieczeństwa

- **NIGDY** nie udostępniaj swoich kluczy API innym osobom
- Plik `.env` jest dodany do `.gitignore` - nie commituj go
- Użyj tylko uprawnień read-only dla API kluczy gdy to możliwe
- Regularnie zmieniaj swoje klucze API

## 📝 Funkcje

- ✅ **Graficzny interfejs webowy** - działający na telefonie i komputerze
- ✅ Śledzenie portfolio na Binance (spot + futures)
- ✅ Śledzenie portfolio na Bybit (unified account)
- ✅ Śledzenie portfolio na XTB (xStation API)
- ✅ Agregacja wszystkich portfoli w jednym miejscu
- ✅ Wyświetlanie szczegółowych danych o aktywach
- ✅ **Wykresy i wizualizacje** - pie chart i bar chart
- ✅ Podział wartości na giełdy (procentowo)
- ✅ Automatyczna konwersja wszystkich walut do USDT
- ✅ **Auto-odświeżanie** - aktualizacja co X sekund
- ✅ Łatwa konfiguracja - działa nawet z jedną giełdą

## 🛠️ Rozwój

Struktura projektu:
```
portfolio-tracker/
├── streamlit_app.py       # Główny plik aplikacji webowej
├── main.py                 # Wersja konsolowa aplikacji
├── config.py               # Konfiguracja i zarządzanie kluczami API
├── portfolio_tracker.py    # Unified portfolio tracker
├── pages/                  # Podstrony aplikacji
│   ├── 1_kryptowaluty.py
│   └── 2_akcje.py
├── exchanges/              # Klienci API dla każdej giełdy
│   ├── binance_client.py
│   ├── bybit_client.py
│   └── xtb_client.py
├── requirements.txt        # Zależności Python
├── .env                    # Klucze API (nie commitować!)
└── README.md              # Ten plik
```

## 📄 Licencja

Ten projekt jest przeznaczony do użytku osobistego.

