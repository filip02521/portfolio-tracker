# Metodologia Weryfikacji Wskaźników AI Recommendations

## 1. Dokumentacja Transparentności Modelu

### 1.1 Lista Wszystkich Wskaźników Technicznych (20+)

System używa następujących wskaźników technicznych do obliczania `signal_strength`:

#### Momentum/Oscillatory Indicators

1. **RSI (Relative Strength Index)**
   - Zakres wartości: 0-100
   - Progi sygnałów:
     - RSI < 30: oversold → BUY
     - RSI > 70: overbought → SELL
   - Waga: ±15 punktów
   - Uzasadnienie: Standardowy wskaźnik momentum, jeden z najważniejszych w analizie technicznej

2. **Stochastic Oscillator (%K, %D)**
   - Zakres wartości: 0-100
   - Progi sygnałów:
     - %K < 20: oversold → BUY
     - %K > 80: overbought → SELL
     - Bullish crossover (%K > %D): BUY
     - Bearish crossover (%K < %D): SELL
   - Waga: ±8 punktów (overbought/oversold), ±6 punktów (crossover)
   - Uzasadnienie: Wskaźnik momentum podobny do RSI, ale z dodatkowym sygnałem crossover

3. **Williams %R**
   - Zakres wartości: -100 do 0
   - Progi sygnałów:
     - %R < -80: oversold → BUY
     - %R > -20: overbought → SELL
   - Waga: ±4 punktów (zredukowane z ±6)
   - Uzasadnienie: Redundantne ze Stochastic, używane jako potwierdzenie

4. **Money Flow Index (MFI)**
   - Zakres wartości: 0-100 (RSI z volume)
   - Progi sygnałów:
     - MFI < 20: oversold → BUY
     - MFI > 80: overbought → SELL
   - Waga: ±7 punktów
   - Uzasadnienie: Uwzględnia volume, bardziej wartościowy niż RSI

5. **CCI (Commodity Channel Index)**
   - Zakres wartości: -300 do +300
   - Progi sygnałów:
     - CCI > 150: strong bullish → BUY (+8)
     - CCI < -150: strong bearish → SELL (-8)
     - CCI > 100: bullish → BUY (+4)
     - CCI < -100: bearish → SELL (-4)
   - Waga: ±8 punktów (próg ±150), ±4 punktów (próg ±100)
   - Uzasadnienie: Zwiększone progi (±150) zmniejszają false signals

#### Trend Indicators

6. **MACD (Moving Average Convergence Divergence)**
   - Komponenty: MACD line, Signal line, Histogram
   - Sygnały:
     - Bullish crossover (MACD > Signal): BUY
     - Bearish crossover (MACD < Signal): SELL
     - MACD trend bullish (tylko gdy brak crossover): BUY
     - MACD trend bearish (tylko gdy brak crossover): SELL
   - Waga: ±20 punktów (crossover - najwyższa waga), ±5 punktów (trend - tylko gdy brak crossover)
   - Uzasadnienie: Crossover jest najbardziej wiarygodny. Trend dodawany tylko gdy brak crossover (eliminacja podwójnego liczenia)

7. **Moving Averages (MA50, MA200)**
   - Sygnały:
     - Price > MA50: BUY
     - Price < MA50: SELL
     - Price > MA200: BUY
     - Price < MA200: SELL
   - Waga: ±5 punktów (MA50), ±8 punktów (MA200)
   - Uzasadnienie: MA200 jest ważniejsza (dłuższy okres). Wagi dodawane tylko gdy brak Golden/Death Cross (eliminacja podwójnego liczenia)

8. **Golden/Death Cross (MA50 vs MA200)**
   - Sygnały:
     - Golden Cross (MA50 > MA200): BUY
     - Death Cross (MA50 < MA200): SELL
   - Waga: ±10 punktów
   - Uzasadnienie: Ważny sygnał długoterminowy. Gdy aktywny, wyklucza indywidualne wagi MA50/MA200

9. **ADX (Average Directional Index)**
   - Zakres wartości: 0-100 (trend strength)
   - Sygnały:
     - ADX > 25 (silny trend) + direction bullish: BUY
     - ADX > 25 (silny trend) + direction bearish: SELL
   - Waga: ±8 punktów (tylko gdy ADX > 25)
   - Uzasadnienie: Mierzy siłę trendu, nie tylko kierunek

10. **Parabolic SAR**
    - Sygnały:
      - SAR poniżej ceny: uptrend → BUY
      - SAR powyżej ceny: downtrend → SELL
    - Waga: ±5 punktów
    - Uzasadnienie: Wskaźnik trendu i potencjalnych punktów odwrócenia

#### Volatility Indicators

11. **ATR (Average True Range)**
    - Pomiar: Volatility jako % ceny
    - Użycie: Tylko do confidence adjustment (NIE do signal_strength)
    - Wpływ na confidence:
      - Volatility > 5%: volatility_factor = 0.6 (zmniejsza confidence)
      - Volatility > 3%: volatility_factor = 0.8
      - Volatility ≤ 3%: volatility_factor = 1.0
    - Uzasadnienie: Wysoka volatility = niepewność, nie kierunek

12. **Bollinger Bands**
    - Pozycja: % między górną a dolną bandą (0-100%)
    - Sygnały:
      - Position < 20%: oversold → BUY
      - Position > 80%: overbought → SELL
    - Waga: ±12 punktów
    - Uzasadnienie: Kombinuje volatility i momentum, wysoka waga

13. **Donchian Channels**
    - Sygnały:
      - Breakout powyżej górnego kanału: BUY
      - Breakout poniżej dolnego kanału: SELL
    - Waga: ±10 punktów
    - Uzasadnienie: Wykrywa breakouty, ważne dla trend-following

#### Volume Indicators

14. **OBV (On Balance Volume)**
    - Trend: Zwiększający/malejący
    - Sygnały:
      - OBV trend wzrastający: BUY
      - OBV trend malejący: SELL
    - Waga: ±5 punktów
    - Uzasadnienie: Potwierdza trendy cenowe przez volume

15. **A/D Line (Accumulation/Distribution)**
    - Trend: Accumulating/distributing
    - Sygnały:
      - A/D trend wzrastający: BUY
      - A/D trend malejący: SELL
    - Waga: ±5 punktów
    - Uzasadnienie: Podobny do OBV, różna metodologia

16. **VWAP (Volume Weighted Average Price)**
    - Pozycja: Cena względem VWAP
    - Sygnały:
      - Price > VWAP: bullish → BUY
      - Price < VWAP: bearish → SELL
    - Waga: ±6 punktów
    - Uzasadnienie: Ważny poziom wsparcia/oporu uwzględniający volume

17. **Chaikin Money Flow (CMF)**
    - Zakres wartości: -1 do +1
    - Sygnały:
      - CMF > 0.1: accumulation → BUY
      - CMF < -0.1: distribution → SELL
    - Waga: ±7 punktów
    - Uzasadnienie: Kombinuje price i volume, wyższa waga niż OBV

18. **Volume Rate of Change**
    - Zmiana volume: % zmiany w 14 okresach
    - Sygnały:
      - Volume ROC > 20%: wzrost volume → BUY
      - Volume ROC < -20%: spadek volume → SELL
    - Waga: ±4 punktów
    - Uzasadnienie: Wykrywa nietypowe zmiany volume

#### Price Momentum

19. **7-day Momentum**
    - Zmiana ceny w 7 dniach
    - Sygnały:
      - Momentum > 5%: BUY
      - Momentum < -5%: SELL
    - Waga: ±5 punktów
    - Uzasadnienie: Krótkoterminowy momentum

20. **30-day Momentum**
    - Zmiana ceny w 30 dniach
    - Sygnały:
      - Momentum > 10%: BUY
      - Momentum < -10%: SELL
    - Waga: ±3 punktów
    - Uzasadnienie: Długoterminowy momentum, niższa waga (mniej częste sygnały)

#### Chart Patterns

21. **Head & Shoulders** (Bearish Reversal)
    - Wzór: 3 szczyty (left shoulder < head > right shoulder)
    - Waga: ±15 punktów (weekly), ±20 punktów (monthly)
    - Sygnał: Bearish reversal

22. **Inverse Head & Shoulders** (Bullish Reversal)
    - Wzór: 3 doliny (left shoulder > head < right shoulder)
    - Waga: ±15 punktów (weekly), ±20 punktów (monthly)
    - Sygnał: Bullish reversal

23. **Ascending Triangle** (Bullish Continuation)
    - Wzór: Pozioma resistance, rising support
    - Waga: ±10 punktów (weekly), ±15 punktów (monthly)
    - Sygnał: Bullish continuation

24. **Descending Triangle** (Bearish Continuation)
    - Wzór: Pozioma support, falling resistance
    - Waga: ±10 punktów (weekly), ±15 punktów (monthly)
    - Sygnał: Bearish continuation

25. **Bull Flag** (Bullish Continuation)
    - Wzór: Strong uptrend pole + consolidation flag
    - Waga: ±12 punktów (weekly), ±18 punktów (monthly)
    - Sygnał: Bullish continuation

26. **Bear Flag** (Bearish Continuation)
    - Wzór: Strong downtrend pole + consolidation flag
    - Waga: ±12 punktów (weekly), ±18 punktów (monthly)
    - Sygnał: Bearish continuation

#### Volume Profile

27. **Point of Control (POC)**
    - Poziom cenowy z najwyższym volume
    - Waga: ±5 punktów (cena przy POC)
    - Sygnał: Ważny poziom akumulacji/dystrybucji

28. **Value Area (VAH/VAL)**
    - Value Area High (VAH): Górna granica 70% volume
    - Value Area Low (VAL): Dolna granica 70% volume
    - Sygnały:
      - Price < VAL: oversold → BUY
      - Price > VAH: overbought → SELL
    - Waga: ±8 punktów
    - Uzasadnienie: Ważny poziom wsparcia/oporu w kontekście volume

#### Support/Resistance

29. **Support/Resistance Levels**
    - Wykrywanie: Swing highs/lows z lookback period
    - Sygnały:
      - Price near support: BUY
      - Price near resistance: SELL
    - Waga: ±8 punktów
    - Uzasadnienie: Kluczowe poziomy psychologiczne

#### Candlestick Patterns

30. **Candlestick Patterns**
    - Wzorce: Doji, Hammer, Shooting Star, Bullish/Bearish Engulfing
    - Waga: ±10 punktów (dla wszystkich wzorców)
    - Uzasadnienie: Krótkoterminowe sygnały odwrócenia

#### Correlation/Beta

31. **Correlation/Beta**
    - Benchmark: BTC (dla crypto), S&P 500 (dla stocks)
    - Sygnały:
      - Outperforming benchmark: BUY
      - Underperforming benchmark: SELL
    - Waga: ±3 punktów
    - Uzasadnienie: Relatywna siła, niska waga (wspierające)

### 1.2 Formuła Obliczania Signal Strength

```
signal_strength = 0.0

# Dla każdego wskaźnika:
if indicator_signal == 'buy':
    signal_strength += indicator_weight
    buy_score += indicator_weight
    bullish_count += 1
elif indicator_signal == 'sell':
    signal_strength -= indicator_weight
    sell_score += indicator_weight
    bearish_count += 1
else:
    neutral_count += 1

# Obliczanie consensus ratio
total_indicators = bullish_count + bearish_count + neutral_count
consensus_ratio = max(bullish_count, bearish_count) / total_indicators

# Quality multiplier
quality_multiplier = 1.0
if consensus_ratio > 0.8:
    quality_multiplier += 0.2  # Bonus za zgodność wskaźników
if same_direction and abs_daily > 30 and abs_weekly > 30:
    quality_multiplier += 0.3  # Bonus za timeframe alignment
if has_golden_cross or has_inverse_h_and_s:
    quality_multiplier += 0.2  # Bonus za kluczowe wzorce

# Zastosowanie quality multiplier
signal_strength = signal_strength * quality_multiplier

# Clampowanie do zakresu [-100, 100]
signal_strength = max(-100, min(100, signal_strength))
```

**Uwagi:**
- Signal strength jest sumą wag wszystkich wskaźników
- Quality multiplier zwiększa siłę sygnału gdy wskaźniki są zgodne
- Finalne clampowanie zapewnia zakres [-100, 100]

### 1.3 Formuła Obliczania Confidence (Multi-Factor)

```
# 1. Base confidence (30% wagi)
base_conf = abs(signal_strength) / 100.0

# 2. Indicator consensus (40% wagi)
consensus_conf = max(bullish_count, bearish_count) / total_indicators

# 3. Timeframe alignment (20% wagi)
if same_direction:  # Daily i weekly w tym samym kierunku
    alignment_conf = 1.0
else:
    alignment_conf = 0.5

# 4. Volatility adjustment (10% wagi)
if volatility_pct > 5:
    volatility_factor = 0.6  # High volatility
elif volatility_pct > 3:
    volatility_factor = 0.8  # Medium volatility
else:
    volatility_factor = 1.0  # Low volatility

# Combined confidence (przed bonusami)
confidence = (base_conf * 0.3 + consensus_conf * 0.4 + alignment_conf * 0.2) * volatility_factor

# Bonusy (dodatkowe)
if same_direction and abs_daily > 30 and abs_weekly > 30:
    confidence += 0.1  # Bonus za silne timeframe alignment
if has_golden_cross or has_inverse_h_and_s:
    confidence += 0.1  # Bonus za kluczowe wzorce

# Minimum confidence guarantee
abs_signal = abs(signal_strength)
if abs_signal > 70:
    confidence = max(0.70, confidence)  # Min 70% dla signal > 70
elif abs_signal > 50:
    confidence = max(0.50, confidence)  # Min 50% dla signal > 50
elif abs_signal > 30:
    confidence = max(0.30, confidence)  # Min 30% dla signal > 30

# Clampowanie do zakresu [0.05, 0.95]
confidence = min(0.95, max(0.05, confidence))
```

**Uzasadnienie wag:**
- **Consensus (40%)**: Najważniejszy - im więcej wskaźników zgodnych, tym wyższa pewność
- **Base (30%)**: Siła sygnału jest ważna, ale nie decydująca
- **Alignment (20%)**: Wsparcie z różnych timeframe'ów zwiększa pewność
- **Volatility (10%)**: Wysoka volatility zmniejsza pewność (mnożnik)

### 1.4 Formuła Obliczania Composite Score

```
composite_score = 0.0

# 1. Signal strength component (30% wagi)
composite_score += (abs(signal_strength) / 100) * 30

# 2. Confidence component (25% wagi)
composite_score += (confidence * 100) * 0.25

# 3. Buy/Sell score component (20% wagi)
composite_score += (buy_score if action == "buy" else sell_score) * 0.20

# 4. Risk adjustment (15% wagi)
if confidence > 0.7:
    risk_weight = 15  # High confidence = low risk
elif confidence < 0.4:
    risk_weight = 5   # Low confidence = high risk
else:
    risk_weight = 10  # Medium risk
composite_score += risk_weight * 0.15

# 5. Allocation drift component (10% wagi)
drift_component = min(100, abs(allocation_drift) * 500)  # 20% drift = 100 points
composite_score += drift_component * 0.10

# Clampowanie do zakresu [0, 100]
composite_score = max(0, min(100, composite_score))
```

**Uzasadnienie wag:**
- **Signal strength (30%)**: Najważniejszy - siła sygnału technicznego
- **Confidence (25%)**: Pewność rekomendacji
- **Buy/Sell score (20%)**: Agregacja sygnałów buy/sell
- **Risk (15%)**: Dostosowanie do poziomu pewności
- **Allocation drift (10%)**: Wsparcie dla rebalansowania

### 1.5 Definicja "Dobrego Momentu"

System definiuje "dobry moment" na podstawie `signal_strength`:

#### Progi Signal Strength

1. **Signal Strength > 20**: Medium Priority BUY
   - Opis: Umiarkowany sygnał kupna
   - Minimum confidence: 30%
   - Uzasadnienie: Większość wskaźników wskazuje na kupno, ale sygnał nie jest bardzo silny

2. **Signal Strength > 50**: High Priority BUY
   - Opis: Silny sygnał kupna
   - Minimum confidence: 50%
   - Uzasadnienie: Wiele wskaźników zgodnie wskazuje na kupno, sygnał jest silny

3. **Signal Strength > 70**: Very High Priority BUY
   - Opis: Bardzo silny sygnał kupna
   - Minimum confidence: 70%
   - Uzasadnienie: Zdecydowana większość wskaźników wskazuje na kupno, sygnał jest bardzo silny

4. **Signal Strength < -20**: Medium Priority SELL
   - Opis: Umiarkowany sygnał sprzedaży
   - Minimum confidence: 30%
   - Uzasadnienie: Większość wskaźników wskazuje na sprzedaż

5. **Signal Strength < -50**: High Priority SELL
   - Opis: Silny sygnał sprzedaży
   - Minimum confidence: 50%
   - Uzasadnienie: Wiele wskaźników zgodnie wskazuje na sprzedaż

6. **Signal Strength < -70**: Very High Priority SELL
   - Opis: Bardzo silny sygnał sprzedaży
   - Minimum confidence: 70%
   - Uzasadnienie: Zdecydowana większość wskaźników wskazuje na sprzedaż

#### Interpretacja Confidence

- **Confidence > 0.7**: Wysoka pewność - większość wskaźników zgodna, niska volatility, timeframe alignment
- **Confidence 0.5-0.7**: Średnia pewność - umiarkowana zgodność wskaźników
- **Confidence < 0.5**: Niska pewność - rozbieżne sygnały, wysoka volatility, brak alignment

#### Warunki Rynkowe

System uwzględnia warunki rynkowe poprzez:
- **Volatility adjustment**: Wysoka volatility (ATR > 5%) zmniejsza confidence
- **Timeframe alignment**: Zgodność daily i weekly sygnałów zwiększa confidence
- **Consensus ratio**: Zgodność wskaźników zwiększa confidence

## 2. Weryfikacja Ważenia

### 2.1 Macierz Wag

Wszystkie wagi są zdefiniowane w `ai_service.py` (linie 929-1274) i są stałe (nie dynamiczne).

### 2.2 Eliminacja Podwójnego Liczenia

System implementuje następujące mechanizmy eliminacji podwójnego liczenia:

1. **MACD**: Gdy crossover jest aktywny, trend nie jest dodawany (eliminuje +20 +5 = +25)
2. **Moving Averages + Golden Cross**: Gdy Golden/Death Cross jest aktywny, indywidualne wagi MA50/MA200 nie są dodawane
3. **Williams %R**: Zredukowana waga z ±6 do ±4 (redundantne ze Stochastic)

### 2.3 Uzasadnienie Wag

- **MACD Crossover (±20)**: Najwyższa waga - najbardziej wiarygodny sygnał
- **RSI (±15)**: Wysoka waga - standardowy wskaźnik momentum
- **Bollinger Bands (±12)**: Wysoka waga - kombinuje volatility i momentum
- **Golden/Death Cross (±10)**: Wysoka waga - ważny sygnał długoterminowy
- **Chart Patterns (±15-20)**: Wysoka waga - silne sygnały odwrócenia/kontynuacji
- **Candlestick Patterns (±10)**: Średnia waga - krótkoterminowe sygnały
- **Volume Indicators (±5-7)**: Średnia waga - potwierdzenie przez volume
- **Correlation/Beta (±3)**: Niska waga - wspierające, nie decydujące

## 3. Weryfikacja Skalowania i Normalizacji

### 3.1 Signal Strength

- **Zakres**: [-100, 100]
- **Clampowanie**: `signal_strength = max(-100, min(100, signal_strength))`
- **Normalizacja**: Wszystkie wagi są już znormalizowane (punkty od -100 do +100)

### 3.2 Confidence

- **Zakres**: [0.05, 0.95]
- **Clampowanie**: `confidence = min(0.95, max(0.05, confidence))`
- **Normalizacja**: Wszystkie komponenty są w zakresie [0, 1], finalna wartość jest clampowana

### 3.3 Composite Score

- **Zakres**: [0, 100]
- **Clampowanie**: `composite_score = max(0, min(100, composite_score))`
- **Normalizacja**: Wszystkie komponenty są przeskalowane do zakresu [0, 100]

### 3.4 Wskaźniki Techniczne

- **RSI**: 0-100 (już znormalizowane)
- **Stochastic**: 0-100 (już znormalizowane)
- **Williams %R**: -100 do 0 (już znormalizowane)
- **MFI**: 0-100 (już znormalizowane)
- **CCI**: -300 do +300 (używane progi ±100, ±150)
- **ADX**: 0-100 (już znormalizowane)
- **Bollinger Bands**: Position 0-100% (już znormalizowane)
- **CMF**: -1 do +1 (używane progi ±0.1)

## 4. Historia Zmian

### 4.1 Poprawki Zaimplementowane (2024)

1. **Usunięcie podwójnego liczenia sygnałów**
   - MACD: Trend dodawany tylko gdy brak crossover
   - Moving Averages: Indywidualne wagi tylko gdy brak Golden/Death Cross
   - Williams %R: Zredukowana waga z ±6 do ±4

2. **ATR przeniesiony do confidence adjustment**
   - ATR nie jest już sygnałem kierunkowym
   - Wysoka volatility zmniejsza confidence zamiast zwiększać signal_strength

3. **CCI zwiększone progi**
   - Próg zwiększony z ±100 na ±150 dla silniejszych sygnałów
   - Dodatkowy próg ±100 z mniejszą wagą (±4)

4. **Multi-factor confidence calculation**
   - Dodano consensus ratio (40% wagi)
   - Dodano timeframe alignment (20% wagi)
   - Dodano volatility adjustment (10% wagi)
   - Dodano minimum confidence guarantees

5. **Quality multiplier**
   - Dodano bonus za zgodność wskaźników (>80% consensus)
   - Dodano bonus za timeframe alignment
   - Dodano bonus za kluczowe wzorce

## 5. Metodologia Weryfikacji

### 5.1 Kryteria Weryfikacji

1. **Transparentność**: Czy wiadomo, jakie dane wejściowe są brane pod uwagę? ✅
   - Wszystkie wskaźniki są zdefiniowane w tym dokumencie

2. **Ważenie**: Czy wagi są sensowne i uzasadnione? ✅
   - Wagi są uzasadnione w sekcji 2.3

3. **Skalowanie**: Czy dane są poprawnie przeskalowane? ✅
   - Wszystkie wartości są clampowane do odpowiednich zakresów

4. **Definicja "dobrego momentu"**: Czy system jasno definiuje, co oznacza "dobry moment"? ✅
   - Progi są zdefiniowane w sekcji 1.5

### 5.2 Weryfikacja Realnej Punktacji

Weryfikacja wymaga:
1. **Backtesting**: Testy historyczne na reprezentatywnych danych
2. **Metryki efektywności**: Win Rate, Profit Factor, Sharpe Ratio, Max Drawdown
3. **Weryfikacja na różnych aktywach**: Crypto, stocks, różne warunki rynkowe
4. **Korelacja confidence-skuteczność**: Czy wysokie confidence = wyższa skuteczność?

### 5.3 Brakujące Elementy

1. **Historyczna skuteczność**: Confidence nie uwzględnia historycznej skuteczności podobnych sygnałów
2. **Dynamiczne wagi**: Wagi są stałe, nie dostosowują się do warunków rynkowych
3. **Asset class specificity**: Wagi są takie same dla wszystkich klas aktywów

## 6. Rekomendacje Ulepszeń

1. **Dodanie historycznej skuteczności do confidence**
   - Uczyć się z przeszłych sygnałów o podobnych charakterystykach
   - Dodatkowy komponent do confidence calculation

2. **Dynamiczne dostosowywanie wag**
   - Różne wagi dla różnych klas aktywów (crypto vs stocks)
   - Adaptacja do warunków rynkowych (bull vs bear market)

3. **Rozszerzenie backtestingu**
   - Pełne metryki efektywności
   - Weryfikacja na różnych okresach i aktywach
   - Analiza korelacji confidence-skuteczność

