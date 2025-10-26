# 📱 Jak używać aplikacji na telefonie

## 🚀 Uruchomienie aplikacji

### Na komputerze (Mac/Linux):

```bash
# Aktywuj virtual environment
source .venv/bin/activate

# Uruchom aplikację Streamlit
streamlit run streamlit_app.py
```

Po uruchomieniu zobaczysz w terminalu:
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

### 📱 Dostęp z telefonu

#### Metoda 1: Sieć lokalna (najprostsza)

1. **Upewnij się, że telefon i komputer są w tej samej sieci WiFi**
2. W terminalu znajdź adres **Network URL** (np. `http://192.168.1.100:8501`)
3. **Otwórz przeglądarkę na telefonie** i wpisz ten adres
4. ✅ Aplikacja będzie działać na telefonie!

#### Metoda 2: Ngrok (dostęp z internetu)

Jeśli chcesz mieć dostęp z dowolnego miejsca (również poza domem):

1. **Zainstaluj ngrok:**
   ```bash
   brew install ngrok
   ```

2. **Zarejestruj się na** https://ngrok.com (darmowe konto)

3. **Uruchom ngrok:**
   ```bash
   ngrok http 8501
   ```

4. **Skopiuj URL** z ngrok (np. `https://xxxxx.ngrok.io`)

5. **Otwórz ten URL na telefonie** - będzie działać wszędzie!

⚠️ **UWAGA**: Nigdy nie udostępniaj ngrok URL publicznie - zawiera Twoje klucze API!

## 🔄 Auto-odświeżanie

Aplikacja ma wbudowaną funkcję auto-odświeżania:

1. Otwórz sidebar (hamburger menu)
2. Włącz **"Automatyczne odświeżanie"**
3. Ustaw interwał (np. 60 sekund)
4. Portfolio będzie automatycznie się aktualizować!

## 📊 Funkcje aplikacji

### Główny widok:
- 💼 **Całkowita wartość portfolio** w USDT
- 📈 **Aktywne giełdy** - ile giełd jest skonfigurowanych
- 🪙 **Liczba aktywów** - ile różnych kryptowalut

### Wykresy:
- 📊 **Pie chart** - podział portfolio na giełdy
- 📊 **Bar chart** - wartość każdej giełdy

### Szczegóły:
- 📋 **Lista wszystkich aktywów** na każdej giełdzie
- 📊 **Szczegóły**: Total, Available, Locked

## 🛡️ Bezpieczeństwo

- ✅ Klucze API są przechowywane tylko na Twoim komputerze
- ✅ Aplikacja działa lokalnie
- ✅ Nie wysyła danych do żadnych zewnętrznych serwerów
- ⚠️ Używaj tylko read-only kluczy API!

## 🐛 Troubleshooting

### Nie widzę aplikacji na telefonie?

1. Sprawdź czy telefon i komputer są w tej samej sieci WiFi
2. Sprawdź firewall - port 8501 musi być otwarty
3. Użyj Network URL z terminala (nie Local URL)

### Aplikacja jest wolna?

- Bybit i XTB mogą być wolne jeśli nie są skonfigurowane
- Binance działa szybko z prawdziwymi kluczami API

### Port zajęty?

```bash
# Uruchom na innym porcie
streamlit run streamlit_app.py --server.port 8502
```

## 🎨 Responsywny design

Aplikacja automatycznie dostosowuje się do rozmiaru ekranu:
- ✅ **Telefon** - kolumny się układają pionowo
- ✅ **Tablet** - optymalny układ
- ✅ **Desktop** - pełny widok

## 💡 Tips

- Dodaj aplikację do ekranu głównego telefonu jako "Add to Home Screen"
- Uruchom aplikację w tle - będzie działać nawet gdy zamkniesz przeglądarkę
- Użyj auto-odświeżania dla stałego monitorowania

