# 🚀 Szybki start - GUI

## Uruchomienie w 3 krokach:

### 1️⃣ Aktywuj środowisko
```bash
source .venv/bin/activate
```

### 2️⃣ Uruchom aplikację
```bash
streamlit run streamlit_app.py
```

### 3️⃣ Otwórz przeglądarkę
- Na komputerze: http://localhost:8501
- Na telefonie: http://[IP_TWOJEGO_KOMPUTERA]:8501

## 📱 Dostęp z telefonu

1. **Znajdź adres IP komputera** w terminalu po uruchomieniu Streamlit:
   ```
   Network URL: http://192.168.x.x:8501
   ```

2. **Upewnij się, że telefon i komputer są w tej samej sieci WiFi**

3. **Otwórz przeglądarkę na telefonie** i wpisz adres IP

4. ✅ **Gotowe!** Twoje portfolio na telefonie!

## 🎯 Co możesz zrobić?

- ✅ **Zobacz całkowitą wartość** portfolio w USDT
- ✅ **Przeglądaj aktywa** na każdej giełdzie
- ✅ **Oglądaj wykresy** - pie chart i bar chart
- ✅ **Włącz auto-odświeżanie** - portfolio aktualizuje się automatycznie
- ✅ **Szczegóły aktywów** - total, available, locked

## 💡 Przydatne komendy

### Uruchomienie
```bash
streamlit run streamlit_app.py
```

### Inny port (jeśli 8501 zajęty)
```bash
streamlit run streamlit_app.py --server.port 8502
```

### Zatrzymanie
Naciśnij `Ctrl+C` w terminalu

## 🎨 Funkcje aplikacji

### Sidebar (panel boczny):
- 🔄 Przycisk odświeżania
- ⚙️ Auto-odświeżanie (10-300 sekund)
- 📊 Status skonfigurowanych giełd

### Główny widok:
- 💼 Całkowita wartość portfolio
- 📈 Aktywne giełdy
- 🪙 Liczba aktywów
- 📊 Wykresy alokacji
- 📋 Szczegóły każdej giełdy

## 🛑 Zatrzymanie aplikacji

W terminalu naciśnij: `Ctrl+C`

## ❓ Pomoc

Szczegółowa instrukcja: [MOBILE_GUIDE.md](MOBILE_GUIDE.md)

