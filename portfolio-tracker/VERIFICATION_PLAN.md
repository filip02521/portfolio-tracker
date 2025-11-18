# Plan Weryfikacji i Naprawy Portfolio Tracker

## 📋 **FAZA 1: WERYFIKACJA OBECNYCH DANYCH**

### 1.1 Sprawdź poprawność transakcji
```bash
# Przejrzyj transaction_history.json i sprawdź:
- Czy każda transakcja ma wymagane pola?
- Czy daty są poprawne?
- Czy ceny i wartości są spójne?
- Czy nie ma duplikatów?
```

**Jak sprawdzić:**
1. Otwórz `transaction_history.json`
2. Sprawdź czy `amount * price_usd = value_usd` dla każdej transakcji
3. Sprawdź daty: czy są w formacie ISO, czy są logiczne?
4. Sprawdź duplikaty: ID powinny być unikalne

### 1.2 Sprawdź kalkulacje PNL
```python
# Uruchom test
python -c "from transaction_history import TransactionHistory; th = TransactionHistory(); print(th.get_total_realized_pnl())"
```

**Sprawdź:**
- Czy realized PNL jest logiczny?
- Czy suma buy = suma sell dla zamkniętych pozycji?

### 1.3 Sprawdź portfolio history
```bash
# Przejrzyj portfolio_history.json
```

**Sprawdź:**
- Czy są dane z ostatniego miesiąca?
- Czy wartości rosną logicznie?
- Czy nie ma brakujących dni?

### 1.4 Sprawdź API connections
```bash
# Sprawdź czy giełdy działają
python -c "from portfolio_tracker import PortfolioTracker; pt = PortfolioTracker(); print(pt.get_all_portfolios())"
```

---

## 🔧 **FAZA 2: NAPRAWA KRYTYCZNYCH BŁĘDÓW**

### 2.1 Napraw duplikaty transakcji
**Problem:** W `transaction_history.json` są powtórzone IDs (widzę ID=7 dwa razy, ID=8 dwa razy)

**Rozwiązanie:**
1. Stwórz backup: `cp transaction_history.json transaction_history_backup.json`
2. Napraw IDs:
```python
# scripts/fix_transaction_ids.py
import json

with open('transaction_history.json', 'r') as f:
    transactions = json.load(f)

# Fix IDs
for i, tx in enumerate(transactions, start=1):
    tx['id'] = i

with open('transaction_history.json', 'w') as f:
    json.dump(transactions, f, indent=2)

print(f"Fixed {len(transactions)} transactions")
```

### 2.2 Dodaj brakujące kursy USD->PLN
**Problem:** Żadna transakcja nie ma `exchange_rate_usd_pln`

**Rozwiązanie:**
1. Instaluj bibliotekę do NBP:
```bash
pip install nbp
```

2. Stwórz skrypt migracji:
```python
# scripts/add_usd_rates.py
from nbp import NBP
from transaction_history import TransactionHistory
from datetime import datetime

th = TransactionHistory()
nbp = NBP()

for tx in th.transactions:
    date = datetime.fromisoformat(tx['date'][:10])
    rate = nbp.get_rate(date)
    tx['exchange_rate_usd_pln'] = rate
    tx['value_pln'] = tx['value_usd'] * rate

th.save_history()
print("Added USD->PLN rates")
```

### 2.3 Dodaj brakujące prowizje
**Problem:** Brak danych o prowizjach

**Rozwiązanie:**
1. Dodać pole `commission` do nowych transakcji
2. Dla starych: ustaw domyślnie 0.1% lub pozwól użytkownikowi edytować

---

## 🎯 **FAZA 3: POPRAWKI SYSTEMU**

### 3.1 Prawdziwy FIFO (zamiast średniej kosztowej)
**Obecna implementacja:** Średnia cena zakupu  
**Wymagane dla podatków:** FIFO (First In First Out)

**Zaimplementuj:**
```python
def calculate_fifo_pnl(buys, sells):
    """
    Prawdziwy FIFO:
    1. Weź najstarszy zakup
    2. Dopasuj do najstarszej sprzedaży
    3. Oblicz zysk/stratę
    4. Powtarzaj aż zabraknie transakcji
    """
    realized_pnl = 0
    buy_queue = sorted(buys, key=lambda x: x['date'])
    sell_queue = sorted(sells, key=lambda x: x['date'])
    
    # FIFO matching
    for sell in sell_queue:
        remaining_sell = sell['amount']
        
        for buy in buy_queue:
            if remaining_sell <= 0:
                break
                
            used = min(remaining_sell, buy['amount'])
            cost = (used / buy['amount']) * buy['value_usd']
            proceeds = (used / sell['amount']) * sell['value_usd']
            
            realized_pnl += proceeds - cost
            remaining_sell -= used
            buy['amount'] -= used
    
    return realized_pnl
```

### 3.2 Walidacja danych przy dodawaniu transakcji
**Problem:** Użytkownik może dodać nieprawidłowe dane

**Rozwiązanie:**
```python
def validate_transaction(asset, amount, price_usd, date):
    """Validate transaction data"""
    errors = []
    
    if amount <= 0:
        errors.append("Ilość musi być > 0")
    
    if price_usd <= 0:
        errors.append("Cena musi być > 0")
    
    if len(asset) == 0:
        errors.append("Symbol nie może być pusty")
    
    # Check if date is not in future
    if date > datetime.now():
        errors.append("Data nie może być w przyszłości")
    
    return errors
```

### 3.3 Backup i restore
**Dodaj automatyczne backupy:**
```python
# w transaction_history.py

def backup(self):
    """Create backup"""
    backup_file = f"{self.data_file}.backup.{int(time.time())}"
    shutil.copy(self.data_file, backup_file)
    return backup_file

def restore(self, backup_file):
    """Restore from backup"""
    shutil.copy(backup_file, self.data_file)
    self.load_history()
```

---

## ✅ **FAZA 4: TESTY**

### 4.1 Unit tests
```python
# tests/test_transaction_history.py

def test_add_transaction():
    th = TransactionHistory()
    tx = th.add_transaction("Binance", "BTC", 1.0, 50000.0, "buy")
    assert tx['id'] > 0
    assert tx['value_usd'] == 50000.0

def test_realized_pnl():
    th = TransactionHistory()
    # Add buy
    th.add_transaction("Binance", "BTC", 1.0, 50000.0, "buy")
    # Add sell
    th.add_transaction("Binance", "BTC", 1.0, 60000.0, "sell")
    assert th.get_total_realized_pnl() == 10000.0
```

### 4.2 Integration tests
```python
def test_end_to_end():
    # Add transaction via UI (mock Streamlit)
    # Check if it appears in history
    # Check if PNL is calculated correctly
    pass
```

---

## 📊 **FAZA 5: MONITORING**

### 5.1 Health checks
Dodaj sprawdzanie integralności danych:
```python
def check_data_integrity():
    """Check if data is consistent"""
    issues = []
    
    # Check for duplicate IDs
    ids = [tx['id'] for tx in transactions]
    if len(ids) != len(set(ids)):
        issues.append("Duplicate transaction IDs")
    
    # Check for missing required fields
    for tx in transactions:
        if not tx.get('date'):
            issues.append(f"Missing date in transaction {tx['id']}")
        if not tx.get('price_usd'):
            issues.append(f"Missing price in transaction {tx['id']}")
    
    return issues
```

### 5.2 Logging
```python
import logging

logging.basicConfig(
    filename='portfolio_tracker.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# W transaction_history.py:
def add_transaction(...):
    logging.info(f"Added transaction: {asset} {amount} @ {price_usd}")
```

---

## 🎯 **PLAN DZIAŁANIA - KROK PO KROKU**

### Tydzień 1: Naprawy krytyczne
- [ ] Napraw duplicate IDs
- [ ] Dodaj kursy USD->PLN do istniejących transakcji
- [ ] Dodaj pole `commission` do transakcji

### Tydzień 2: FIFO i walidacja
- [ ] Zaimplementuj prawdziwy FIFO
- [ ] Dodaj walidację danych
- [ ] Testy jednostkowe

### Tydzień 3: Monitoring i backup
- [ ] System backupów
- [ ] Logging
- [ ] Health checks

### Tydzień 4: Raporty podatkowe
- [ ] Export do CSV
- [ ] Raport podatkowy na rok
- [ ] PDF report

---

## 🚀 **AKTUALNE STATUS**

- ✅ Dashboard działa
- ✅ Wykresy się wyświetlają
- ✅ Transakcje można dodawać/usuwać
- ⚠️ **PROBLEM:** Duplikaty IDs w transakcjach
- ⚠️ **PROBLEM:** Brak kursów USD->PLN
- ⚠️ **PROBLEM:** FIFO to faktycznie średnia kosztowa
- ⚠️ **PROBLEM:** Brak prowizji w transakcjach

---

## 🎯 **CO ROBIĆ TERAZ?**

1. **Natychmiast:** Napraw duplicate IDs w transaction_history.json
2. **Dzisiaj:** Dodaj kursy USD->PLN dla istniejących transakcji
3. **Ten tydzień:** Zaimplementuj prawdziwy FIFO
4. **Ten miesiąc:** Export CSV i raporty podatkowe

---

**Stwórzmy harmonogram z konkretnymi datami i przypisań?**

