# 🚀 Jak uruchomić aplikację - Instrukcja krok po kroku

## Metoda 1: Proste uruchomienie (zalecane)

### Krok 1: Otwórz terminal
- Na Mac: `Cmd + Space` → wpisz "Terminal" → Enter

### Krok 2: Przejdź do folderu aplikacji
```bash
cd /Users/Filip/portfolio-tracker
```

### Krok 3: Aktywuj środowisko wirtualne
```bash
source .venv/bin/activate
```

### Krok 4: Uruchom aplikację
```bash
streamlit run streamlit_app.py
```

### Krok 5: Pomiń prompt emaila
- Gdy pojawi się pytanie: `Email:`
- **Po prostu naciśnij Enter** (zostaw puste)
- Aplikacja się uruchomi!

### Krok 6: Otwórz przeglądarkę
- Aplikacja otworzy się automatycznie w przeglądarce
- Lub otwórz ręcznie: http://localhost:8501

---

## Metoda 2: Użyj skryptu (najprostsze)

### Krok 1: Otwórz terminal

### Krok 2: Uruchom skrypt
```bash
cd /Users/Filip/portfolio-tracker
./start_app.sh
```

---

## Metoda 3: Bezpośrednio z katalogu

W terminalu wpisz wszystko w jednej linii:

```bash
cd /Users/Filip/portfolio-tracker && source .venv/bin/activate && streamlit run streamlit_app.py
```

---

## 💡 Co zobaczysz?

Po uruchomieniu zobaczysz:

```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

---

## 📱 Dostęp z telefonu

1. Znajdź adres **Network URL** w terminalu
2. Otwórz ten adres w przeglądarce na telefonie
3. Upewnij się że telefon i komputer są w tej samej sieci WiFi

---

## ⛔ Zatrzymanie aplikacji

W terminalu naciśnij: `Ctrl + C`

---

## ❓ Problemy?

### Aplikacja nie otwiera się automatycznie?
- Kopiuj URL z terminala: `http://localhost:8501`
- Wklej do przeglądarki

### Port zajęty?
```bash
streamlit run streamlit_app.py --server.port 8502
```

### Błąd "command not found: streamlit"?
```bash
source .venv/bin/activate
pip install streamlit
```

