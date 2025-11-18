# Wymagania dla Szczegółowych Raportów Podatkowych

## 📊 **CO JUŻ MAMY:**

### ✅ Funkcjonalności działające:
- ✅ Historia transakcji (buy/sell)
- ✅ Data transakcji
- ✅ Cena jednostkowa
- ✅ Ilość/amount
- ✅ Wartość USD
- ✅ Realized PNL (zrealizowany zysk/strata)
- ✅ FIFO calculation (podstawowa wersja)
- ✅ Grouping by asset i exchange
- ✅ Export do JSON

---

## ❌ **CZEGO BRAKUJE dla podatków w Polsce:**

### 1. **Opłaty i prowizje**
```json
{
  "commission": 0.0,  // ← BRAKUJE
  "commission_currency": "USDT"
}
```
- Obecne transakcje nie mają zapisanych prowizji
- Dla podatków: prowizja jest kosztem, który MOŻNA odliczyć

### 2. **Kursy walut w dniu transakcji**
```json
{
  "exchange_rate_usd_pln": null,  // ← BRAKUJE
  "value_pln": null
}
```
- Musimy wiedzieć ile PLN było warte w dniu transakcji
- Urząd skarbowy wymaga wyliczeń w PLN

### 3. **Szczegółowa informacja o transakcji**
```json
{
  "transaction_id": null,  // ID z giełdy (dla weryfikacji)
  "order_id": null,
  "transaction_fee_usd": 0.0,
  "notes": ""
}
```

### 4. **Preferowana metoda wyliczeń**
- ⚠️ Obecna: Simple Average (średnia cena zakupu)
- ✅ Wymagane w Polsce: **FIFO (First In First Out)**
- Możliwość wyboru: FIFO/LIFO/Średnia kosztowa

### 5. **Dokumentacja sprzedaży z podziałem**
- Dla każdej sprzedaży: Które dokładnie akcje zostały sprzedane
- Linked to buy transactions (powiązanie z zakupami)
- Cost basis dla każdej partii sprzedanych aktywów

---

## 🔧 **CO MUSIMY DODAĆ:**

### A. Rozszerzyć model transakcji:
```python
transaction = {
    'id': int,
    'exchange': str,
    'asset': str,
    'amount': float,
    'price_usd': float,
    'type': str,  # 'buy' or 'sell'
    'date': str,  # ISO format
    'value_usd': float,
    
    # NOWE POLA:
    'commission': float,  # ← DODAJ
    'commission_currency': str,  # USDT/USD
    'exchange_rate_usd_pln': float,  # ← DODAJ (kurs USD->PLN w dniu transakcji)
    'value_pln': float,  # ← DODAJ
    'order_id': str,  # ID z giełdy
    'linked_buys': [int],  # IDs zakupów z których pochodzą sprzedane aktywa (FIFO)
    'notes': str
}
```

### B. Dodać źródło kursów walut:
```python
# Potrzebujemy API do kursów historycznych NBP (Polski Bank Narodowy)
from nbp_api import get_usd_rate_on_date

# Przykład:
transaction['exchange_rate_usd_pln'] = get_usd_rate_on_date(transaction['date'])
transaction['value_pln'] = transaction['value_usd'] * transaction['exchange_rate_usd_pln']
```

### C. Prawdziwy FIFO z detalami:
```python
def calculate_realized_pnl_fifo(transactions):
    """
    FIFO z dokładnym śledzeniem:
    - Które kupno -> Której sprzedaży
    - Koszt nabycia (cost basis)
    - Przychód ze sprzedaży
    - Zysk/strata (przychód - koszt - prowizja)
    """
    pass
```

### D. Raport podatkowy:
```python
def generate_tax_report(year: int):
    """
    Generuje raport dla urzędu skarbowego:
    
    WYMAGANE (Polska):
    1. Wszystkie transakcje z roku
    2. Dla każdej transakcji:
       - Data
       - Rodzaj (zakup/sprzedaż)
       - Instrument finansowy
       - Liczba jednostek
       - Cena jednostkowa
       - Wartość w PLN
       - Prowizja/opłata
       - Zysk/strata (jeśli sprzedaż)
    3. Suma zysków/strat
    4. Podatek do zapłacenia (19%)
    """
    pass
```

---

## 📝 **PLAN IMPLEMENTACJI:**

### Faza 1: Rozszerzenie danych (Prioritet WYSOKI)
1. ✅ Dodać pole `commission` do każdej nowej transakcji
2. ✅ Pobrać historyczne kursy USD->PLN (NBP API)
3. ✅ Wypełnić brakujące kursy dla istniejących transakcji

### Faza 2: Prawdziwy FIFO (Prioritet WYSOKI)
1. ✅ Przepisać `get_total_realized_pnl()` na prawdziwy FIFO
2. ✅ Dodać `linked_buys` do transakcji
3. ✅ Wyświetlać dokładne szczegóły: które kupno -> sprzedaż

### Faza 3: Raporty (Prioritet ŚREDNI)
1. ✅ Export do CSV (gotowy już mamy `import_from_csv`, teraz odwrotnie)
2. ✅ Raport podatkowy na rok (roczny summary)
3. ✅ PDF report z wykresami

### Faza 4: Walidacja (Prioritet NISKI)
1. ✅ Sprawdzać kompletność danych (czy wszystkie transakcje mają kursy)
2. ✅ Alerty o brakujących danych
3. ✅ Możliwość ręcznej korekty prowizji/komisji

---

## 🎯 **ZACZYNAMY OD:**

**Proponuję zacząć od Fazy 1 - rozszerzenie danych. Potem user będzie mógł poprawić brakujące prowizje ręcznie w istniejących transakcjach.**

Czy zaczynamy od dodania:
1. Pola `commission` do nowych transakcji
2. Automatycznego pobierania kursów USD->PLN z NBP API?
3. Migracji istniejących transakcji (wypełnienie kursów dla starych transakcji)?

