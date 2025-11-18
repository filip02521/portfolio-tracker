# 📊 Przewodnik po PNL (Profit & Loss)

## 🔍 Jak działa PNL

PNL (Profit & Loss) pokazuje czy Twoje pozycje są na plusie czy minusie.

### ✅ Co musisz mieć:

1. **Transakcje zakupu** - historia kiedy i za ile kupiłeś dane aktywo
2. **Aktualne portfolio** - ile masz teraz danego aktywa

### 📊 Jak działa obliczanie:

```
PNL = Aktualna wartość - Zainwestowana kwota

Gdzie:
- Aktualna wartość = Ilość aktywów × Aktualna cena
- Zainwestowana kwota = Za ile kupiłeś aktywa
```

## 🎯 Przykład:

### ETH:

**Zakupy:**
- Kupiłeś 0.5 ETH za $3,500 (marzec 2024)
- Kupiłeś 0.3 ETH za $3,800 (kwiecień 2024)
- **Łącznie:** 0.8 ETH za $2,950

**Sprzedaże:**
- Sprzedałeś 0.2 ETH za $3,600
- **Zostało:** 0.6 ETH

**Obecnie:**
- Masz 0.6 ETH
- Cena ETH: $4,000
- Aktualna wartość: 0.6 × $4,000 = $2,400

**PNL:**
- Zainwestowałeś: $2,950 × (0.6/0.8) = $2,212.50
- Aktualna wartość: $2,400
- PNL: $2,400 - $2,212.50 = **+$187.50** ✅

## ⚠️ Uwaga:

**Nie możesz obliczyć PNL dla aktywów bez historii zakupów!**

Jeśli masz tylko transakcje sprzedaży (jak w Twoim przypadku z ETH), aplikacja nie wie:
- Za ile kupiłeś
- Kiedy kupiłeś
- Ile zainwestowałeś

## 💡 Co zrobić:

### Opcja 1: Dodaj zakupy ręcznie
1. Przejdź do sekcji PNL
2. Kliknij "Dodaj transakcję ręcznie"
3. Wypełnij:
   - Giełda: Binance/Bybit
   - Aktywo: ETH
   - Ilość: np. 0.5
   - Cena: np. 3500
   - Typ: **buy**
   - Data: data zakupu

### Opcja 2: Synchronizuj z API
1. Kliknij "🔄 Synchronizuj z API"
2. Aplikacja pobierze historię transakcji z giełd
3. PNL wyliczy się automatycznie

## 🚨 Błędne dane?

Jeśli widzisz błędne wartości PNL:
1. Sprawdź czy masz transakcje zakupu w historii
2. Sprawdź czy daty i ceny są poprawne
3. Spróbuj zsynchronizować ponownie z API

## 📝 Przykład poprawnej historii:

```json
{
  "id": 1,
  "exchange": "Binance",
  "asset": "ETH",
  "amount": 0.5,
  "price_usd": 3500,
  "type": "buy",  ← MUSI BYĆ "buy"!
  "date": "2024-03-01"
}
```

