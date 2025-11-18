# 📋 Plan Działania - Portfolio Tracker

## ✅ **CO ZOSTAŁO NAPRAWIONE:**
- ✅ Duplikaty IDs w transaction_history.json (ID 7 i 8)
- ✅ Backup został utworzony: `transaction_history.json.backup`
- ✅ Wszystkie 76 transakcji mają teraz unikalne IDs

---

## 🎯 **DO ZROBIENIA - PRIORYTET WYSOKI:**

### 1. **Naprawianie danych transakcji** 🔴 KRYTYCZNE
**Status:** W toku

**Problem:** 
- Brak prowizji w transakcjach
- Brak kursów USD->PLN
- Brak linked_buys (które kupno -> sprzedaż)

**Rozwiązanie:**
```bash
# Stwórz plik do dodania brakujących danych
touch scripts/add_missing_data.py
```

### 2. **Prawdziwy FIFO** 🔴 WYMAGANE DLA PODATKÓW
**Status:** NIEZROBIONE

**Problem:** Obecna implementacja to prosta średnia kosztowa, nie FIFO

**Co zrobić:**
- Przepisać `calculate_pnl()` w `transaction_history.py`
- Dodać matching: kupno -> sprzedaż
- Śledzić dokładnie które akcje zostały sprzedane

### 3. **Kursy walutowe** 🟡 WAŻNE
**Status:** NIEZROBIONE

**Problem:** Brak kursów USD->PLN dla transakcji

**Rozwiązanie:**
```python
# Dodać integrację z NBP API
pip install nbp

# Dla każdej transakcji pobrać kurs z dnia transakcji
```

---

## 📊 **PRIORYTET ŚREDNI:**

### 4. **Export do CSV**
- Raport transakcji
- Raport podatkowy
- Export dla US

### 5. **Walidacja danych**
- Sprawdzanie poprawności przy dodawaniu transakcji
- Alerty o błędach
- Możliwość edycji już dodanych transakcji

### 6. **Monitoring i logging**
- Health checks
- Logowanie działań
- Alerty o problemach

---

## 🚀 **FAZY IMPLEMENTACJI:**

### **FAZA 1: Naprawa danych (1-2 dni)**
```
□ Stwórz skrypt dodawania prowizji
□ Stwórz skrypt pobierania kursów USD->PLN
□ Uruchom migrację dla istniejących transakcji
□ Test czy wszystko działa
```

### **FAZA 2: FIFO (2-3 dni)**
```
□ Przepisz calculate_pnl() na prawdziwy FIFO
□ Dodaj linked_buys do transakcji
□ Testy jednostkowe
□ Test na prawdziwych danych
```

### **FAZA 3: Raporty (2-3 dni)**
```
□ Export do CSV
□ Raport podatkowy na rok
□ Filtr po datach
□ PDF report
```

### **FAZA 4: Monitoring (1-2 dni)**
```
□ Health checks
□ Logging
□ Alerty
□ Backup system
```

---

## 🎯 **CO ROBIMY TERAZ?**

**Krok 1:** Naprawianie duplikatów ✅  
**Krok 2:** Dodanie kursów USD->PLN 🔄  
**Krok 3:** Przepisanie FIFO ⏳  
**Krok 4:** Raporty podatkowe ⏳  

---

## 📝 **SZCZEGÓŁOWY PLAN:**

### Dzisiaj:
1. ✅ Napraw duplikaty IDs - GOTOWE
2. 🔄 Stwórz skrypt pobierania kursów NBP
3. ⏳ Dodaj pole `commission` do transakcji

### Ten tydzień:
1. ⏳ Zaimplementuj prawdziwy FIFO
2. ⏳ Export CSV
3. ⏳ Testy jednostkowe

### Ten miesiąc:
1. ⏳ Raporty podatkowe PDF
2. ⏳ Monitoring i alerty
3. ⏳ System backupów

---

## 🎯 **STATUS:**
- ✅ Dashboard: DZIAŁA
- ✅ Wykresy: DZIAŁAJĄ  
- ✅ Dodawanie transakcji: DZIAŁA
- ✅ PNL calculation: DZIAŁA (ale nieprawdziwy FIFO)
- ❌ Kursy walutowe: BRAK
- ❌ Prowizje: BRAK
- ❌ Export CSV: BRAK
- ❌ Raporty podatkowe: BRAK

---

**CZY KONTYNUUJEMY OD DODANIA KURSÓW USD->PLN?**

