# Backup System - Dokumentacja

## Przegląd

System automatycznych backupów dla Portfolio Tracker Pro zapewnia bezpieczeństwo danych użytkownika poprzez regularne kopie zapasowe wszystkich ważnych plików.

## Funkcjonalności

### 1. Automatyczne Backupy
- **Codziennie o 2:00** - automatyczny backup wszystkich danych
- **Automatyczne czyszczenie** - stare backupy (powyżej 30 dni) są usuwane automatycznie (co niedzielę o 3:00)
- **Zachowanie minimum** - zawsze zachowywanych jest minimum 5 backupów

### 2. Ręczne Backupy
- Użytkownik może utworzyć backup w dowolnym momencie
- Możliwość dodania opcjonalnego opisu
- Wybór czy backupować pliki wrażliwe (users.json)

### 3. Przywracanie z Backupu
- Lista wszystkich dostępnych backupów
- Szczegółowe informacje o każdym backupie
- Przywracanie z wybranego backupu
- Opcja nadpisania istniejących plików

### 4. Zarządzanie Backupami
- Usuwanie pojedynczych backupów
- Automatyczne czyszczenie starych backupów
- Wyświetlanie rozmiaru i liczby plików w backupie

## Pliki Backupowane

### Zawsze Backupowane
- `transaction_history.json` - historia transakcji
- `portfolio_history.json` - historia wartości portfolio
- `goals.json` - cele inwestycyjne
- `app_settings.json` - ustawienia aplikacji
- `watchlist.json` - lista obserwowanych aktywów
- `ai_recommendations_history.json` - historia rekomendacji AI

### Opcjonalnie (include_sensitive=true)
- `users.json` - konta użytkowników (dla bezpieczeństwa domyślnie wyłączone)

## Format Backupu

- **Format**: JSON skompresowany gzip
- **Lokalizacja**: `backups/backup_YYYYMMDD_HHMMSS.json.gz`
- **Struktura**:
  ```json
  {
    "backup_id": "20251105_212453",
    "timestamp": "2025-11-05T21:24:53.123456",
    "description": "Manual backup",
    "version": "1.0",
    "files": {
      "transaction_history.json": {
        "size": 12345,
        "data": { ... }
      },
      ...
    },
    "metadata": {
      "files_count": 6,
      "total_size_bytes": 123456,
      "total_size_mb": 0.12
    },
    "backup_size_bytes": 12345,
    "backup_size_mb": 0.01,
    "compression_ratio": 0.10
  }
  ```

## API Endpoints

### POST `/api/backup/create`
Utworzenie nowego backupu.

**Request Body**:
```json
{
  "description": "Optional description",
  "include_sensitive": false
}
```

**Response**:
```json
{
  "success": true,
  "backup_id": "20251105_212453",
  "backup_filename": "backup_20251105_212453.json.gz",
  "timestamp": "2025-11-05T21:24:53.123456",
  "files_count": 6,
  "total_size_mb": 0.12,
  "backup_size_mb": 0.01,
  "compression_ratio": 0.10
}
```

### GET `/api/backup/list?limit=50`
Lista wszystkich backupów.

**Response**:
```json
[
  {
    "backup_id": "20251105_212453",
    "backup_filename": "backup_20251105_212453.json.gz",
    "timestamp": "2025-11-05T21:24:53.123456",
    "description": "Manual backup",
    "files_count": 6,
    "backup_size_mb": 0.01
  },
  ...
]
```

### GET `/api/backup/info/{backup_id}`
Szczegółowe informacje o backupie.

### POST `/api/backup/restore`
Przywrócenie z backupu.

**Request Body**:
```json
{
  "backup_id": "20251105_212453",
  "overwrite": true
}
```

**Response**:
```json
{
  "success": true,
  "backup_id": "20251105_212453",
  "restored_files": ["transaction_history.json", ...],
  "skipped_files": [],
  "error_files": [],
  "restored_count": 6
}
```

### DELETE `/api/backup/delete/{backup_id}`
Usunięcie backupu.

### POST `/api/backup/cleanup?days=30&keep_minimum=5`
Czyszczenie starych backupów.

## UI Komponent

Komponent `BackupRestore.tsx` jest dostępny w sekcji Settings → "Backup & Restore".

**Funkcje UI**:
- Lista wszystkich backupów
- Przycisk "Create Backup"
- Przyciski Restore i Delete dla każdego backupu
- Wyświetlanie daty, rozmiaru, liczby plików
- Potwierdzenia dla operacji restore i delete

## Automatyzacja

### BackupScheduler
- Klasa `BackupScheduler` w `background_worker.py`
- Uruchamiana automatycznie przy starcie backend
- Używa biblioteki `schedule` do zarządzania zadaniami

### Harmonogram
- **Codziennie o 2:00** - backup
- **Co niedzielę o 3:00** - czyszczenie starych backupów

### Konfiguracja
Harmonogram można zmienić w `main.py`:
```python
backup_scheduler = BackupScheduler(backup_service, backup_time="02:00")
```

## Bezpieczeństwo

### Pliki Wrażliwe
- `users.json` domyślnie **NIE** jest backupowany
- Można włączyć przez `include_sensitive=true` w API
- UI nie oferuje opcji backupowania plików wrażliwych (ze względów bezpieczeństwa)

### Kompresja
- Wszystkie backupy są kompresowane gzip
- Redukcja rozmiaru o ~90% (zależnie od danych)

### Walidacja
- Przed przywróceniem sprawdzana jest poprawność backupu
- Błędne pliki JSON są backupowane jako raw content
- Przywracanie z błędnych plików jest obsługiwane gracefully

## Obsługa Błędów

### Nieprawidłowy JSON
Jeśli plik ma nieprawidłowy JSON (np. `ai_recommendations_history.json`), system:
1. Próbuje odczytać jako JSON
2. Jeśli się nie udaje, zapisuje jako raw content z flagą `_json_error`
3. Przy przywracaniu odtwarza raw content

### Brakujące Pliki
- Pliki, które nie istnieją, są pomijane podczas backupu
- Nie powodują błędów

### Błędy Podczas Backupu
- Błędy dla poszczególnych plików są logowane
- Backup jest kontynuowany dla pozostałych plików
- Informacje o błędach są zapisywane w metadata backupu

## Użycie

### Przez UI
1. Przejdź do Settings → "Backup & Restore"
2. Kliknij "Create Backup" aby utworzyć backup
3. Użyj przycisków Restore/Delete przy każdym backupie

### Przez API
```bash
# Utwórz backup
curl -X POST http://localhost:8000/api/backup/create \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description": "My backup"}'

# Lista backupów
curl http://localhost:8000/api/backup/list \
  -H "Authorization: Bearer YOUR_TOKEN"

# Przywróć backup
curl -X POST http://localhost:8000/api/backup/restore \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"backup_id": "20251105_212453", "overwrite": true}'
```

## Monitoring

### Logi
Backup scheduler loguje:
- Start każdego backupu
- Zakończenie backupu (sukces/błąd)
- Czyszczenie starych backupów

### Weryfikacja
Sprawdź logi backend:
```bash
grep "Backup" backend.log
grep "backup" backend.error.log
```

## Rozszerzenia (Przyszłość)

### Chmura (Google Drive/Dropbox)
- Automatyczny upload backupów do chmury
- Synchronizacja między urządzeniami
- Backup offsite

### Wersjonowanie
- System wersji dla backupów
- Porównywanie różnic między backupami
- Selektywne przywracanie plików

### Backup Incrementalny
- Backupy tylko zmian (delta)
- Oszczędność miejsca
- Szybsze tworzenie backupów

---

**Data utworzenia**: 2025-11-05



