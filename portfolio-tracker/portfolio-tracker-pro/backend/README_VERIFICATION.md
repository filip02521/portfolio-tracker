# System Weryfikacji AI Recommendations

## Przegląd

System weryfikacji służy do sprawdzenia sensowności i skuteczności wskaźników (signal_strength, confidence, composite_score) w systemie AI recommendations poprzez backtesting i analizę historyczną.

## Struktura Systemu

### Pliki Dokumentacji

1. **VERIFICATION_METHODOLOGY.md** - Pełna dokumentacja metodologii
   - Lista wszystkich wskaźników technicznych (31 wskaźników)
   - Formuły obliczania signal_strength, confidence, composite_score
   - Definicja "dobrego momentu" z progami
   - Weryfikacja skalowania i normalizacji

2. **CONFIDENCE_METHODOLOGY.md** - Dokumentacja confidence
   - Szczegółowa dokumentacja obliczania confidence
   - Uzasadnienie wag (30/40/20/10)
   - Przykłady obliczeń
   - Rekomendacje ulepszeń

3. **VERIFICATION_REPORT.md** - Raport podsumowujący
   - Podsumowanie weryfikacji
   - Analiza skuteczności
   - Rekomendacje ulepszeń

4. **weights_matrix.json** - Macierz wag wszystkich wskaźników
   - Wagi wszystkich 31 wskaźników
   - Uzasadnienie wag
   - Metadane systemu

### Pliki Systemowe

1. **verification_backtest.py** - System weryfikacji historycznej
   - Testy na różnych okresach (3, 6, 12 miesięcy)
   - Testy na różnych aktywach (crypto, stocks)
   - Testy z różnymi progami signal_strength
   - Agregacja wyników

2. **asset_class_analysis.py** - Analiza klas aktywów
   - Testy na kryptowalutach
   - Testy na akcjach
   - Testy na mieszanych portfelach
   - Porównanie wyników

3. **verification_report_generator.py** - Generator raportów
   - Generowanie raportów HTML
   - Generowanie raportów tekstowych
   - Wizualizacja wyników

4. **run_verification.py** - Skrypt pomocniczy
   - Uruchamia pełną weryfikację
   - Automatyczne generowanie raportów

### Testy Jednostkowe

1. **tests/test_signal_scaling.py** - Testy skalowania
2. **tests/test_confidence_calculation.py** - Testy confidence
3. **tests/test_signal_strength_calculation.py** - Testy signal_strength
4. **tests/test_composite_score.py** - Testy composite_score

## Użycie

### Uruchomienie Pełnej Weryfikacji

```bash
cd portfolio-tracker-pro/backend
python run_verification.py
```

### Uruchomienie Poszczególnych Komponentów

#### 1. Weryfikacja Backtestów

```bash
python verification_backtest.py
```

#### 2. Analiza Klas Aktywów

```bash
python asset_class_analysis.py
```

#### 3. Generowanie Raportów

```bash
python verification_report_generator.py
```

### Uruchomienie Testów Jednostkowych

```bash
# Wszystkie testy
python -m pytest tests/ -v

# Konkretne testy
python -m pytest tests/test_signal_scaling.py -v
python -m pytest tests/test_confidence_calculation.py -v
python -m pytest tests/test_signal_strength_calculation.py -v
python -m pytest tests/test_composite_score.py -v
```

## Wyniki

### Pliki Wynikowe

Po uruchomieniu weryfikacji zostaną utworzone następujące pliki:

1. **verification_backtest_results.json** - Wyniki backtestów (JSON)
2. **asset_class_analysis_results.json** - Wyniki analizy klas aktywów (JSON)
3. **verification_report.html** - Raport HTML z wynikami
4. **verification_report.txt** - Raport tekstowy z wynikami
5. **asset_class_analysis_report.txt** - Raport analizy klas aktywów

### Interpretacja Wyników

#### Metryki Efektywności

- **Total Return** - Całkowity zwrot w %
- **Sharpe Ratio** - Ryzyko-skorygowany zwrot (wyższy = lepszy)
- **Win Rate** - % trafnych sygnałów (wyższy = lepszy)
- **Profit Factor** - total_profit / total_loss (wyższy = lepszy, >1.0 = zyskowny)
- **Max Drawdown** - Maksymalne obsunięcie kapitału (niższy = lepszy)
- **Calmar Ratio** - CAGR / Max Drawdown (wyższy = lepszy)
- **Average Return per Trade** - Średni zwrot na transakcję (wyższy = lepszy)

#### Ocena Skuteczności

- **Sharpe Ratio > 1.0** - Dobra strategia
- **Win Rate > 50%** - Więcej trafnych niż nietrafnych sygnałów
- **Profit Factor > 1.5** - Zyski znacznie przewyższają straty
- **Max Drawdown < 20%** - Akceptowalne ryzyko
- **Calmar Ratio > 1.0** - Dobry stosunek zwrotu do ryzyka

## Rekomendacje

### Priorytet Wysoki

1. **Uruchomienie Backtestów** - Uruchomić `run_verification.py` na reprezentatywnych danych
2. **Analiza Wyników** - Przeanalizować korelację confidence-skuteczność
3. **Dodanie Historycznej Skuteczności** - Dodać komponent do confidence po backtestach

### Priorytet Średni

4. **Dynamiczne Dostosowywanie Wag** - Różne wagi dla różnych klas aktywów
5. **Rozszerzenie Bonusów** - Dodatkowe bonusy za silne wzorce

### Priorytet Niski

6. **Wizualizacja Equity Curve** - Dodać wykresy do raportów HTML
7. **Optymalizacja Wag** - Automatyczna optymalizacja na podstawie backtestów

## Wymagania

- Python 3.8+
- Wszystkie zależności z `requirements.txt`
- Dostęp do danych historycznych (przez `market_data_service`)
- Wystarczająca ilość danych (minimum 6 miesięcy historii)

## Status

✅ **WSZYSTKIE KOMPONENTY ZAIMPLEMENTOWANE**

- ✅ Dokumentacja metodologii
- ✅ Testy jednostkowe
- ✅ System weryfikacji historycznej
- ✅ Analiza klas aktywów
- ✅ Generator raportów
- ⏳ Wymaga uruchomienia backtestów na danych

## Kontakt

W razie pytań lub problemów, zobacz dokumentację w:
- `VERIFICATION_METHODOLOGY.md`
- `CONFIDENCE_METHODOLOGY.md`
- `VERIFICATION_REPORT.md`



