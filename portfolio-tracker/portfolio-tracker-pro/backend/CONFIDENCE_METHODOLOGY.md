# Metodologia Obliczania Confidence

## Przegląd

Confidence (pewność) w systemie AI recommendations jest obliczana jako wieloczynnikowa formuła, która uwzględnia:
1. Siłę sygnału (signal_strength)
2. Zgodność wskaźników (consensus)
3. Wyrównanie timeframe'ów (daily vs weekly)
4. Warunki rynkowe (volatility)
5. Kluczowe wzorce (Golden Cross, Inverse Head & Shoulders)
6. Minimum guarantees dla silnych sygnałów

## Formuła Confidence

### Podstawowa Formuła

```
confidence = (base_conf * 0.3 + consensus_conf * 0.4 + alignment_conf * 0.2) * volatility_factor
```

### Komponenty

#### 1. Base Confidence (30% wagi)

**Formuła:**
```
base_conf = abs(signal_strength) / 100.0
```

**Zakres:** [0.0, 1.0]

**Uzasadnienie:**
- Siła sygnału jest podstawowym wskaźnikiem pewności
- Im wyższy `signal_strength` (w wartości bezwzględnej), tym wyższa podstawowa pewność
- 30% wagi oznacza, że siła sygnału jest ważna, ale nie decydująca

**Przykłady:**
- `signal_strength = 0` → `base_conf = 0.0`
- `signal_strength = 50` → `base_conf = 0.5`
- `signal_strength = 100` → `base_conf = 1.0`
- `signal_strength = -75` → `base_conf = 0.75` (abs(-75) = 75)

#### 2. Consensus Confidence (40% wagi) - NAJWAŻNIEJSZY

**Formuła:**
```
consensus_ratio = max(bullish_count, bearish_count) / total_indicators
consensus_conf = consensus_ratio
```

**Zakres:** [0.0, 1.0]

**Uzasadnienie:**
- **Najważniejszy komponent** (40% wagi) - zgodność wskaźników jest kluczowa
- Im więcej wskaźników wskazuje ten sam kierunek, tym wyższa pewność
- Wysoki consensus oznacza, że sygnał jest potwierdzony przez wiele niezależnych wskaźników

**Przykłady:**
- 15 bullish, 3 bearish, 2 neutral → `consensus_ratio = 15/20 = 0.75` (75% consensus)
- 10 bullish, 10 bearish, 0 neutral → `consensus_ratio = 10/20 = 0.5` (50% consensus - brak consensus)
- 18 bullish, 1 bearish, 1 neutral → `consensus_ratio = 18/20 = 0.9` (90% consensus - bardzo wysoki)

**Interpretacja:**
- `consensus_ratio > 0.8`: Wysoki consensus - większość wskaźników zgodna
- `consensus_ratio 0.5-0.8`: Umiarkowany consensus - niektóre wskaźniki zgodne
- `consensus_ratio < 0.5`: Niski consensus - rozbieżne sygnały

#### 3. Alignment Confidence (20% wagi)

**Formuła:**
```
if same_direction:  # Daily i weekly w tym samym kierunku
    alignment_conf = 1.0
else:
    alignment_conf = 0.5
```

**Zakres:** [0.5, 1.0]

**Uzasadnienie:**
- Wyrównanie sygnałów z różnych timeframe'ów zwiększa pewność
- Jeśli daily i weekly wskazują ten sam kierunek, sygnał jest silniejszy
- 20% wagi oznacza, że alignment jest wspierający, ale nie decydujący

**Przykłady:**
- Daily signal = +50, Weekly signal = +40 → `same_direction = True` → `alignment_conf = 1.0`
- Daily signal = +50, Weekly signal = -30 → `same_direction = False` → `alignment_conf = 0.5`
- Daily signal = -60, Weekly signal = -45 → `same_direction = True` → `alignment_conf = 1.0`

#### 4. Volatility Factor (10% wagi) - Multiplier

**Formuła:**
```
if volatility_pct > 5:
    volatility_factor = 0.6  # High volatility - zmniejsza confidence
elif volatility_pct > 3:
    volatility_factor = 0.8  # Medium volatility
else:
    volatility_factor = 1.0  # Low volatility - bez wpływu
```

**Zakres:** [0.6, 1.0]

**Uzasadnienie:**
- Wysoka volatility = niepewność rynkowa = niższa pewność sygnałów
- Volatility factor jest **mnożnikiem** (nie komponentem), więc wpływa na wszystkie komponenty
- 10% wagi oznacza, że volatility jest ważnym, ale nie dominującym czynnikiem

**Przykłady:**
- Volatility = 2% → `volatility_factor = 1.0` (bez wpływu)
- Volatility = 4% → `volatility_factor = 0.8` (zmniejsza confidence o 20%)
- Volatility = 7% → `volatility_factor = 0.6` (zmniejsza confidence o 40%)

**Źródło volatility:**
- ATR (Average True Range) jako % ceny
- Obliczane z danych historycznych

### Bonusy (Dodatkowe)

#### Bonus za Timeframe Alignment

**Formuła:**
```
if same_direction and abs_daily > 30 and abs_weekly > 30:
    confidence += 0.1
```

**Uzasadnienie:**
- Silne wyrównanie sygnałów z różnych timeframe'ów (+0.1)
- Tylko gdy oba sygnały są silne (abs > 30) i w tym samym kierunku

#### Bonus za Kluczowe Wzorce

**Formuła:**
```
if has_golden_cross or has_inverse_h_and_shoulders:
    confidence += 0.1
```

**Uzasadnienie:**
- Kluczowe wzorce (Golden Cross, Inverse Head & Shoulders) są bardzo wiarygodne (+0.1)
- Wzorce te są rzadkie, ale gdy występują, są silnymi sygnałami

### Minimum Confidence Guarantees

**Formuła:**
```
abs_signal = abs(signal_strength)
if abs_signal > 70:
    confidence = max(0.70, confidence)  # Min 70% dla signal > 70
elif abs_signal > 50:
    confidence = max(0.50, confidence)  # Min 50% dla signal > 50
elif abs_signal > 30:
    confidence = max(0.30, confidence)  # Min 30% dla signal > 30
```

**Uzasadnienie:**
- Silne sygnały powinny mieć minimum pewności
- Gwarantuje, że silne sygnały (signal > 70) zawsze mają confidence >= 0.70
- Zapobiega sytuacji, gdy silny sygnał ma niską pewność z powodu innych czynników

**Przykłady:**
- `signal_strength = 80`, calculated confidence = 0.60 → final confidence = 0.70 (minimum guarantee)
- `signal_strength = 55`, calculated confidence = 0.45 → final confidence = 0.50 (minimum guarantee)
- `signal_strength = 35`, calculated confidence = 0.25 → final confidence = 0.30 (minimum guarantee)

### Final Clamping

**Formuła:**
```
confidence = min(0.95, max(0.05, confidence))
```

**Zakres:** [0.05, 0.95]

**Uzasadnienie:**
- Zawsze pozostawiamy margines (5% minimum, 95% maksimum)
- Zapobiega ekstremalnym wartościom (0% lub 100%)
- 5% minimum oznacza, że nawet słabe sygnały mają minimalną pewność
- 95% maksimum oznacza, że nigdy nie jesteśmy 100% pewni (ryzyko zawsze istnieje)

## Przykłady Obliczeń

### Przykład 1: Wysoki Consensus, Same Direction, Niska Volatility

**Parametry:**
- `signal_strength = 75`
- `bullish_count = 15`, `bearish_count = 3`, `neutral_count = 2`
- `same_direction = True`
- `volatility_pct = 2.0`
- `abs_daily = 75`, `abs_weekly = 70`
- `has_golden_cross = True`

**Obliczenia:**
1. `base_conf = abs(75) / 100.0 = 0.75`
2. `total_indicators = 15 + 3 + 2 = 20`
3. `consensus_ratio = max(15, 3) / 20 = 0.75`
4. `consensus_conf = 0.75`
5. `alignment_conf = 1.0` (same_direction)
6. `volatility_factor = 1.0` (volatility < 3%)

7. **Combined confidence:**
   ```
   confidence = (0.75 * 0.3 + 0.75 * 0.4 + 1.0 * 0.2) * 1.0
              = (0.225 + 0.300 + 0.200) * 1.0
              = 0.725
   ```

8. **Bonusy:**
   - Timeframe alignment: `same_direction and abs_daily > 30 and abs_weekly > 30` → `+0.1`
   - Kluczowe wzorce: `has_golden_cross` → `+0.1`
   ```
   confidence = 0.725 + 0.1 + 0.1 = 0.925
   ```

9. **Minimum guarantee:**
   - `abs_signal = 75 > 70` → `confidence = max(0.70, 0.925) = 0.925`

10. **Final clamping:**
    ```
    confidence = min(0.95, max(0.05, 0.925)) = 0.925
    ```

**Wynik:** `confidence = 0.925` (92.5%)

### Przykład 2: Niski Consensus, Different Direction, Wysoka Volatility

**Parametry:**
- `signal_strength = 40`
- `bullish_count = 8`, `bearish_count = 7`, `neutral_count = 5`
- `same_direction = False`
- `volatility_pct = 6.0`
- `abs_daily = 40`, `abs_weekly = -25`
- `has_golden_cross = False`

**Obliczenia:**
1. `base_conf = abs(40) / 100.0 = 0.40`
2. `total_indicators = 8 + 7 + 5 = 20`
3. `consensus_ratio = max(8, 7) / 20 = 0.40`
4. `consensus_conf = 0.40`
5. `alignment_conf = 0.5` (different direction)
6. `volatility_factor = 0.6` (volatility > 5%)

7. **Combined confidence:**
   ```
   confidence = (0.40 * 0.3 + 0.40 * 0.4 + 0.5 * 0.2) * 0.6
              = (0.120 + 0.160 + 0.100) * 0.6
              = 0.380 * 0.6
              = 0.228
   ```

8. **Bonusy:**
   - Timeframe alignment: `same_direction = False` → brak bonusu
   - Kluczowe wzorce: `has_golden_cross = False` → brak bonusu

9. **Minimum guarantee:**
   - `abs_signal = 40 > 30` → `confidence = max(0.30, 0.228) = 0.30`

10. **Final clamping:**
    ```
    confidence = min(0.95, max(0.05, 0.30)) = 0.30
    ```

**Wynik:** `confidence = 0.30` (30%)

### Przykład 3: Średni Consensus, Same Direction, Średnia Volatility

**Parametry:**
- `signal_strength = 60`
- `bullish_count = 12`, `bearish_count = 5`, `neutral_count = 3`
- `same_direction = True`
- `volatility_pct = 4.0`
- `abs_daily = 60`, `abs_weekly = 55`
- `has_golden_cross = False`

**Obliczenia:**
1. `base_conf = abs(60) / 100.0 = 0.60`
2. `total_indicators = 12 + 5 + 3 = 20`
3. `consensus_ratio = max(12, 5) / 20 = 0.60`
4. `consensus_conf = 0.60`
5. `alignment_conf = 1.0` (same_direction)
6. `volatility_factor = 0.8` (volatility > 3%, <= 5%)

7. **Combined confidence:**
   ```
   confidence = (0.60 * 0.3 + 0.60 * 0.4 + 1.0 * 0.2) * 0.8
              = (0.180 + 0.240 + 0.200) * 0.8
              = 0.620 * 0.8
              = 0.496
   ```

8. **Bonusy:**
   - Timeframe alignment: `same_direction and abs_daily > 30 and abs_weekly > 30` → `+0.1`
   - Kluczowe wzorce: `has_golden_cross = False` → brak bonusu
   ```
   confidence = 0.496 + 0.1 = 0.596
   ```

9. **Minimum guarantee:**
   - `abs_signal = 60 > 50` → `confidence = max(0.50, 0.596) = 0.596`

10. **Final clamping:**
    ```
    confidence = min(0.95, max(0.05, 0.596)) = 0.596
    ```

**Wynik:** `confidence = 0.596` (59.6%)

## Uzasadnienie Wag

### Dlaczego Consensus ma 40% wagi?

1. **Zgodność wskaźników jest najważniejsza**: Jeśli większość wskaźników wskazuje ten sam kierunek, sygnał jest bardzo wiarygodny
2. **Redukcja false signals**: Wysoki consensus oznacza, że sygnał jest potwierdzony przez wiele niezależnych metod
3. **Empiryczna weryfikacja**: W analizie technicznej, sygnały potwierdzone przez wiele wskaźników są bardziej wiarygodne

### Dlaczego Base Confidence ma 30% wagi?

1. **Siła sygnału jest ważna**: Wysoki `signal_strength` oznacza silny sygnał
2. **Ale nie decydująca**: Siła sygnału sama w sobie nie gwarantuje pewności (może być fałszywy sygnał)
3. **Wspierająca**: Base confidence wspiera consensus, ale nie dominuje

### Dlaczego Alignment ma 20% wagi?

1. **Wsparcie z różnych timeframe'ów**: Wyrównanie daily i weekly zwiększa pewność
2. **Wspierająca, nie decydująca**: Alignment sam w sobie nie gwarantuje pewności
3. **Redukcja false signals**: Zgodność timeframe'ów zmniejsza prawdopodobieństwo false signals

### Dlaczego Volatility Factor jest mnożnikiem?

1. **Wpływa na wszystkie komponenty**: Wysoka volatility zmniejsza pewność wszystkich komponentów
2. **Proporcjonalna redukcja**: Volatility nie eliminuje confidence, ale zmniejsza go proporcjonalnie
3. **Realistyczne podejście**: Wysoka volatility = niepewność, ale nie brak pewności

## Brakujące Elementy

### Historyczna Skuteczność (NIE ZAIMPLEMENTOWANE)

**Co powinno być:**
- Uczenie się z przeszłych sygnałów o podobnych charakterystykach
- Jeśli podobne sygnały w przeszłości były skuteczne, confidence powinien być wyższy
- Jeśli podobne sygnały w przeszłości były nieskuteczne, confidence powinien być niższy

**Przykład:**
- Sygnał z `signal_strength = 75`, `consensus = 0.9`, `same_direction = True`
- W przeszłości podobne sygnały miały 80% win rate
- Confidence powinien być zwiększony o komponent historycznej skuteczności

**Rekomendacja:**
- Dodać komponent historycznej skuteczności do confidence calculation
- Użyć backtestów do nauczenia się, które kombinacje sygnałów są skuteczne
- Dodać wagę dla historycznej skuteczności (np. 10-15%)

## Weryfikacja Confidence

### Kryteria Weryfikacji

1. **Zgodność z Zasadami**: ✅
   - Consensus (40%) - zaimplementowane
   - Warunki rynkowe (volatility) - zaimplementowane
   - Historyczna skuteczność - ❌ NIE ZAIMPLEMENTOWANE

2. **Spójność z Signal Strength**: ✅
   - Silne sygnały mają minimum confidence guarantees
   - Confidence rośnie z signal_strength (base_conf)

3. **Empiryczna Weryfikacja**: ⏳ WYMAGA BACKTESTÓW
   - Czy wysokie confidence rzeczywiście oznacza wyższą skuteczność?
   - Czy niskie confidence rzeczywiście oznacza niższą skuteczność?
   - Jaka jest korelacja między confidence a win rate?

## Rekomendacje Ulepszeń

1. **Dodanie Historycznej Skuteczności**
   - Komponent uwzględniający win rate podobnych sygnałów z przeszłości
   - Waga: 10-15%
   - Wymaga: System śledzenia historycznej skuteczności

2. **Dynamiczne Dostosowywanie Wag**
   - Różne wagi dla różnych warunków rynkowych (bull vs bear market)
   - Różne wagi dla różnych klas aktywów (crypto vs stocks)
   - Wymaga: Analiza backtestów i optymalizacja wag

3. **Rozszerzenie Bonusów**
   - Bonus za silne wzorce (np. Inverse Head & Shoulders na weekly timeframe)
   - Bonus za ekstremalne wartości wskaźników (np. RSI < 20)
   - Bonus za volume confirmation (wysoki volume przy sygnale)

4. **Volatility Adjustment**
   - Obecnie: Fixed thresholds (3%, 5%)
   - Ulepszenie: Dynamiczne thresholds oparte na historycznej volatility aktywa
   - Ulepszenie: Uwzględnienie implied volatility (jeśli dostępne)

## Podsumowanie

Obecna formuła confidence jest **wieloczynnikowa i dobrze przemyślana**, ale **wymaga empirycznej weryfikacji** poprzez backtesty. Najważniejszym brakiem jest **historyczna skuteczność**, która powinna być dodana jako dodatkowy komponent.

**Obecne wagi:**
- Consensus: 40% (najważniejszy)
- Base Confidence: 30%
- Alignment: 20%
- Volatility: 10% (mnożnik)

**Rekomendowane ulepszenie:**
- Consensus: 35%
- Base Confidence: 25%
- Alignment: 15%
- Volatility: 10% (mnożnik)
- **Historyczna Skuteczność: 15%** (NOWY)

