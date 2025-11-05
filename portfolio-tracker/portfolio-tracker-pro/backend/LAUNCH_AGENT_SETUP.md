# macOS LaunchAgent Setup dla Backend

## Przegląd

macOS LaunchAgent automatycznie uruchamia backend z venv Python po zalogowaniu użytkownika, zapewniając:
- ✅ Automatyczny start backend przy zalogowaniu
- ✅ Automatyczny restart przy crashu
- ✅ Użycie venv Python (dostęp do yfinance)
- ✅ Logi w dedykowanych plikach
- ✅ Łatwe zarządzanie przez helper script

## Instalacja

### Krok 1: Utworzenie LaunchAgent plist

Plik `com.portfolio-tracker.backend.plist` został już utworzony w:
```
~/Library/LaunchAgents/com.portfolio-tracker.backend.plist
```

### Krok 2: Uruchomienie Service

Użyj helper script (ZALECANE):
```bash
cd portfolio-tracker-pro/backend
./backend_service.sh start
```

Lub ręcznie (macOS 10.13+):
```bash
launchctl bootstrap "gui/$(id -u)" ~/Library/LaunchAgents/com.portfolio-tracker.backend.plist
```

Dla starszych wersji macOS (< 10.13):
```bash
launchctl load ~/Library/LaunchAgents/com.portfolio-tracker.backend.plist
```

### Krok 3: Weryfikacja

Sprawdź status service:
```bash
./backend_service.sh status
```

Backend powinien być dostępny na `http://localhost:8000`

## Zarządzanie Service

### Helper Script

Użyj `backend_service.sh` do zarządzania service:

```bash
cd portfolio-tracker-pro/backend

# Start service
./backend_service.sh start

# Stop service
./backend_service.sh stop

# Restart service
./backend_service.sh restart

# Sprawdź status
./backend_service.sh status

# Pokaż logi (ostatnie 50 linii)
./backend_service.sh logs

# Pokaż więcej logów (np. 100 linii)
./backend_service.sh logs 100

# Pomoc
./backend_service.sh help
```

### Ręczne Zarządzanie (launchctl)

**macOS 10.13+ (Zalecane):**
```bash
# Start service
launchctl bootstrap "gui/$(id -u)" ~/Library/LaunchAgents/com.portfolio-tracker.backend.plist

# Stop service
launchctl bootout "gui/$(id -u)/com.portfolio-tracker.backend"

# Sprawdź status
launchctl print "gui/$(id -u)/com.portfolio-tracker.backend"

# Lista wszystkich service
launchctl list | grep com.portfolio-tracker.backend
```

**Starsze macOS (< 10.13):**
```bash
# Start service
launchctl load ~/Library/LaunchAgents/com.portfolio-tracker.backend.plist

# Stop service
launchctl unload ~/Library/LaunchAgents/com.portfolio-tracker.backend.plist

# Sprawdź status
launchctl list | grep com.portfolio-tracker.backend

# Szczegóły service
launchctl list com.portfolio-tracker.backend
```

## Logi

Logi są zapisywane w:
- **Standard output**: `portfolio-tracker-pro/backend/backend.log`
- **Standard error**: `portfolio-tracker-pro/backend/backend.error.log`

Zobacz logi:
```bash
# Użyj helper script
./backend_service.sh logs

# Lub ręcznie
tail -f portfolio-tracker-pro/backend/backend.log
tail -f portfolio-tracker-pro/backend/backend.error.log
```

## Konfiguracja

### Zmiana Portu

Edytuj `~/Library/LaunchAgents/com.portfolio-tracker.backend.plist` i zmień:
```xml
<string>--port</string>
<string>8000</string>  <!-- Zmień na inny port -->
```

Następnie zrestartuj service:
```bash
./backend_service.sh restart
```

### Wyłączenie Auto-Start

Edytuj plist i zmień:
```xml
<key>RunAtLoad</key>
<false/>  <!-- Zmień z true na false -->
```

Lub po prostu unload service:
```bash
./backend_service.sh stop
```

### Wyłączenie Auto-Restart

Edytuj plist i zmień:
```xml
<key>KeepAlive</key>
<false/>  <!-- Zmień z true na false -->
```

## Troubleshooting

### Service nie startuje

1. **Sprawdź czy plist istnieje:**
   ```bash
   ls -la ~/Library/LaunchAgents/com.portfolio-tracker.backend.plist
   ```

2. **Sprawdź logi błędów:**
   ```bash
   ./backend_service.sh logs
   cat backend.error.log
   ```

3. **Sprawdź czy venv Python istnieje:**
   ```bash
   ls -la portfolio-tracker-pro/backend/venv/bin/python
   ```

4. **Sprawdź czy uvicorn jest zainstalowane:**
   ```bash
   cd portfolio-tracker-pro/backend
   source venv/bin/activate
   python -m uvicorn --version
   ```

5. **Sprawdź czy port 8000 jest wolny:**
   ```bash
   lsof -i :8000
   ```

### Service crashuje natychmiast

1. **Sprawdź logi błędów:**
   ```bash
   ./backend_service.sh logs
   ```

2. **Sprawdź czy wszystkie zależności są zainstalowane:**
   ```bash
   cd portfolio-tracker-pro/backend
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Sprawdź czy plik main.py istnieje:**
   ```bash
   ls -la portfolio-tracker-pro/backend/main.py
   ```

### Service nie używa venv Python

Sprawdź czy plist zawiera prawidłową ścieżkę do venv Python:
```xml
<string>/Users/Filip/portfolio-tracker/portfolio-tracker-pro/backend/venv/bin/python</string>
```

Jeśli ścieżka się zmieniła, zaktualizuj plist i zrestartuj service.

### Port już zajęty

1. **Znajdź proces używający portu 8000:**
   ```bash
   lsof -i :8000
   ```

2. **Zatrzymaj proces:**
   ```bash
   kill <PID>
   ```

3. **Lub zmień port w plist** (patrz sekcja "Zmiana Portu")

## Odinstalowanie

Aby całkowicie usunąć LaunchAgent:

1. **Zatrzymaj service:**
   ```bash
   ./backend_service.sh stop
   ```

2. **Usuń plist:**
   ```bash
   rm ~/Library/LaunchAgents/com.portfolio-tracker.backend.plist
   ```

3. **Usuń logi (opcjonalnie):**
   ```bash
   rm portfolio-tracker-pro/backend/backend.log
   rm portfolio-tracker-pro/backend/backend.error.log
   ```

## Korzyści LaunchAgent

### vs. Ręczny Start

- ✅ Automatyczny start po zalogowaniu
- ✅ Automatyczny restart przy crashu
- ✅ Nie trzeba pamiętać o uruchomieniu backend

### vs. Terminal (w tle)

- ✅ Nie zamyka się przy zamknięciu terminala
- ✅ Logi w dedykowanych plikach
- ✅ Łatwiejsze zarządzanie

### vs. PM2/Docker

- ✅ Nie wymaga instalacji dodatkowych narzędzi (Node.js, Docker)
- ✅ Natywne rozwiązanie macOS
- ✅ Lżejsze (mniej zasobów)

## Uwagi

- LaunchAgent działa tylko dla zalogowanego użytkownika (nie system-wide)
- Service nie startuje automatycznie przy boot (tylko przy zalogowaniu)
- Dla system-wide service użyj LaunchDaemon (wymaga sudo)

---

**Data utworzenia**: 2025-11-05

