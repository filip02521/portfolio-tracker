# AI/ML Features - Portfolio Tracker Pro

## Przegląd

Portfolio Tracker Pro zawiera zaawansowane funkcje AI/ML do analizy portfolio i przewidywań cenowych. Wszystkie biblioteki AI są **opcjonalne** - aplikacja działa z fallbackami jeśli biblioteki nie są zainstalowane.

## Biblioteki AI

### Wymagane dla pełnej funkcjonalności:

1. **Prophet** (`prophet==1.2.1`)
   - **Funkcja:** Przewidywania cen aktywów (crypto i stocks)
   - **Endpoint:** `/api/ai/predictions`
   - **Fallback:** Mock predictions (bez Prophet)
   - **Instalacja:** `pip install prophet`

2. **TA** (`ta==0.11.0`)
   - **Funkcja:** Kompleksowe wskaźniki techniczne dla zaawansowanej analizy rynku i rekomendacji rebalansowania
   - **Endpoint:** `/api/ai/recommendations`
   - **Fallback:** Proste rekomendacje oparte na alokacji (bez wskaźników technicznych)
   - **Instalacja:** `pip install ta`

3. **Transformers** (`transformers==4.35.0`)
   - **Funkcja:** Analiza sentymentu z wiadomości finansowych (FinBERT)
   - **Model:** `ProsusAI/finbert`
   - **Fallback:** Mock sentiment analysis
   - **Wymaga:** PyTorch (`torch==2.2.0`)
   - **Instalacja:** `pip install transformers torch`

4. **NewsAPI** (`newsapi-python==0.2.7`)
   - **Funkcja:** Pobieranie wiadomości finansowych do analizy sentymentu
   - **Fallback:** Mock news data
   - **Wymaga:** Klucz API w zmiennej środowiskowej `NEWSAPI_KEY`
   - **Instalacja:** `pip install newsapi-python`

## Instalacja

### Wszystkie biblioteki (pełna funkcjonalność):
```bash
pip install -r requirements.txt
```

### Tylko podstawowe (bez AI):
Aplikacja działa bez bibliotek AI - używa fallbacków.

### Sprawdzenie instalacji:
```bash
pip list | grep -E "prophet|ta|transformers|newsapi|torch"
```

## Konfiguracja

### Zmienne środowiskowe:

- `NEWSAPI_KEY` - Klucz API do NewsAPI (opcjonalne, tylko dla analizy sentymentu)
  - Bez klucza: używane są mock news data

### Sprawdzanie statusu:

Status bibliotek jest sprawdzany przy starcie aplikacji w logach:
- `PROPHET_AVAILABLE = True/False`
- `TA_AVAILABLE = True/False`
- `TRANSFORMERS_AVAILABLE = True/False`
- `NEWSAPI_AVAILABLE = True/False`

## Funkcje AI

### 1. Przewidywania Cen (`predict_price`)

**Używa:** Prophet (jeśli dostępne)

**Parametry:**
- `symbol` - Symbol aktywa (np. 'BTC', 'AAPL')
- `asset_type` - 'crypto' lub 'stock'
- `days_ahead` - Liczba dni do przewidzenia (7-90)

**Zwraca:**
- `predicted_price` - Przewidywana cena
- `upper_bound` - Górna granica przedziału ufności
- `lower_bound` - Dolna granica przedziału ufności
- `confidence` - Poziom ufności (0.5-0.95)

**Walidacja:**
- Ceny są ograniczone do wartości >= 1% obecnej ceny
- Maksimum: 10x obecna cena
- Automatyczne clampowanie wartości ujemnych

### 2. Rekomendacje Rebalansowania (`recommend_rebalance`)

**Używa:** TA (jeśli dostępne) - kompleksowa analiza techniczna z 20+ wskaźnikami

**Parametry:**
- `portfolio_holdings` - Obecne pozycje {symbol: percentage}
- `target_allocation` - Docelowa alokacja {symbol: target_percentage}
- `rebalance_threshold` - Próg rebalansowania (domyślnie 0.05)

**Zwraca:**
- Lista rekomendacji z szczegółowymi wskaźnikami technicznymi
- `signal_strength` - Agregowany sygnał -100 (sprzedaj) do +100 (kupuj)
- `buy_score` / `sell_score` - Osobne punkty za kupno/sprzedaż (0-100)
- `confidence` - Pewność rekomendacji (0.0-1.0)
- Szczegółowe metryki dla każdego wskaźnika

## Wskaźniki Techniczne

System używa **20+ wskaźników technicznych** zintegrowanych w system scoringu:

### Momentum/Oscillatory Indicators

1. **RSI (Relative Strength Index)**
   - Wartości: 0-100
   - Sygnały: <30 (oversold/buy), >70 (overbought/sell)
   - Waga: ±15 punktów

2. **Stochastic Oscillator (%K, %D)**
   - Wartości: 0-100
   - Sygnały: <20 (oversold), >80 (overbought), crossover signals
   - Waga: ±8 punktów (overbought/oversold), ±6 (crossover)

3. **Williams %R**
   - Wartości: -100 do 0
   - Sygnały: <-80 (oversold), >-20 (overbought)
   - Waga: ±6 punktów

4. **Money Flow Index (MFI)**
   - Wartości: 0-100 (RSI z volume)
   - Sygnały: <20 (oversold), >80 (overbought)
   - Waga: ±7 punktów

5. **CCI (Commodity Channel Index)**
   - Wartości: -300 do +300
   - Sygnały: >100 (strong bullish), <-100 (strong bearish)
   - Waga: ±8 punktów

### Trend Indicators

6. **MACD (Moving Average Convergence Divergence)**
   - Komponenty: MACD line, Signal line, Histogram
   - Sygnały: Bullish/bearish crossover, histogram momentum
   - Waga: ±20 (crossover), ±5 (trend), ±3 (histogram)

7. **Moving Averages (MA50, MA200)**
   - Sygnały: Cena powyżej/poniżej MA
   - Waga: ±5 (MA50), ±8 (MA200)

8. **Golden/Death Cross (MA50 vs MA200)**
   - Sygnały: Golden Cross (MA50 > MA200 = buy), Death Cross (sell)
   - Waga: ±10 punktów

9. **ADX (Average Directional Index)**
   - Wartości: 0-100 (trend strength)
   - Sygnały: ADX >25 (silny trend), kierunek DI+/DI-
   - Waga: ±8 punktów (silny trend)

10. **Parabolic SAR**
    - Sygnały: SAR poniżej ceny (uptrend), powyżej (downtrend)
    - Waga: ±5 punktów

### Volatility Indicators

11. **ATR (Average True Range)**
    - Pomiar: Volatility jako % ceny
    - Wykrywanie: Wysoka volatility (>3%) = potencjalne breakout
    - Waga: +3 punktów (wysoka volatility)

12. **Bollinger Bands**
    - Pozycja: % między górną a dolną bandą
    - Sygnały: <20% (oversold), >80% (overbought)
    - Waga: ±12 punktów

13. **Donchian Channels**
    - Sygnały: Breakout powyżej górnego kanału (buy), poniżej dolnego (sell)
    - Waga: ±10 punktów

### Volume Indicators

14. **OBV (On Balance Volume)**
    - Trend: Zwiększający/malejący
    - Waga: ±5 punktów

15. **A/D Line (Accumulation/Distribution)**
    - Trend: Accumulating/distributing
    - Waga: ±5 punktów

16. **VWAP (Volume Weighted Average Price)**
    - Pozycja: Cena względem VWAP
    - Sygnały: Powyżej VWAP (bullish), poniżej (bearish)
    - Waga: ±6 punktów

17. **Chaikin Money Flow (CMF)**
    - Wartości: -1 do +1
    - Sygnały: >0.1 (accumulation), <-0.1 (distribution)
    - Waga: ±7 punktów

18. **Volume Rate of Change**
    - Zmiana volume: % zmiany w 14 okresach
    - Sygnały: >20% (wzrost volume), <-20% (spadek)
    - Waga: ±4 punktów

### Price Momentum

19. **7-day Momentum**
    - Zmiana ceny w 7 dniach
    - Waga: ±5 punktów (>5% lub <-5%)

20. **30-day Momentum**
    - Zmiana ceny w 30 dniach
    - Waga: ±3 punktów (>10% lub <-10%)

### Chart Patterns (Phase 2) ✅

21. **Head & Shoulders** (Bearish Reversal)
    - Wzór: 3 szczyty (left shoulder < head > right shoulder)
    - Waga: ±15 punktów (weekly), ±20 (monthly)
    - Sygnał: Bearish reversal

22. **Inverse Head & Shoulders** (Bullish Reversal)
    - Wzór: 3 doliny (left shoulder > head < right shoulder)
    - Waga: ±15 punktów (weekly), ±20 (monthly)
    - Sygnał: Bullish reversal

23. **Ascending Triangle** (Bullish Continuation)
    - Wzór: Pozioma resistance, rising support
    - Waga: ±10 punktów (weekly), ±15 (monthly)
    - Sygnał: Bullish continuation

24. **Descending Triangle** (Bearish Continuation)
    - Wzór: Pozioma support, falling resistance
    - Waga: ±10 punktów (weekly), ±15 (monthly)
    - Sygnał: Bearish continuation

25. **Symmetrical Triangle** (Neutral/Bilateral)
    - Wzór: Zbieżne support i resistance
    - Waga: ±5 punktów (kierunek breakout)
    - Sygnał: Zależny od kierunku breakout

26. **Bull Flag** (Bullish Continuation)
    - Wzór: Strong uptrend pole + consolidation flag
    - Waga: ±12 punktów (weekly), ±18 (monthly)
    - Sygnał: Bullish continuation

27. **Bear Flag** (Bearish Continuation)
    - Wzór: Strong downtrend pole + consolidation flag
    - Waga: ±12 punktów (weekly), ±18 (monthly)
    - Sygnał: Bearish continuation

### Volume Profile (Phase 2) ✅

28. **Point of Control (POC)**
    - Poziom cenowy z najwyższym volume
    - Waga: ±5 punktów (cena przy POC)
    - Sygnał: Ważny poziom akumulacji/dystrybucji

29. **Value Area (VAH/VAL)**
    - Value Area High (VAH): Górna granica 70% volume
    - Value Area Low (VAL): Dolna granica 70% volume
    - Waga: ±8 punktów (cena poniżej VAL = oversold, powyżej VAH = overbought)
    - Sygnał: Oversold/overbought w kontekście volume

### System Scoringu

Wszystkie wskaźniki są agregowane w **signal_strength** (-100 do +100):
- **>20**: Rekomendacja KUP (medium priority)
- **>50**: Rekomendacja KUP (high priority)
- **<-20**: Rekomendacja SPRZEDAŻ (medium priority)
- **<-50**: Rekomendacja SPRZEDAŻ (high priority)

**Confidence** = abs(signal_strength) / 100.0

### Poprawki Zaimplementowane (2024)

#### 1. Usunięcie Podwójnego Liczenia Sygnałów ✅
- **MACD**: Gdy crossover jest aktywny, nie dodaje się wagi za trend (eliminuje +20 +5 = +25, teraz tylko +20)
- **Moving Averages + Golden Cross**: Gdy Golden/Death Cross jest aktywny, nie dodaje się wag MA50/MA200 osobno (eliminuje podwójne liczenie)
- **Williams %R**: Zredukowana waga z ±6 do ±4 (redundantne ze Stochastic)

#### 2. ATR Przeniesiony do Confidence Adjustment ✅
- ATR nie jest już sygnałem kierunkowym (nie dodaje do signal_strength)
- Wysoka volatility (ATR > 3%) zmniejsza confidence zamiast zwiększać signal_strength

#### 3. CCI Zwiększone Progi ✅
- Próg zwiększony z ±100 na ±150 dla silniejszych sygnałów
- Zmniejsza liczbę false signals

## Optymalizacja Wag - Backtesting Framework

System zawiera framework do testowania różnych konfiguracji wag wskaźników technicznych poprzez backtesting.

### Użycie

```bash
cd portfolio-tracker-pro/backend
python run_weight_optimization.py
```

### Konfiguracje Wag

System zawiera 7 predefiniowanych konfiguracji wag w `weight_configs.json`:

1. **base** - Obecne wagi jako baseline
2. **no_double_counting** - Wagi z poprawkami podwójnego liczenia
3. **momentum_focused** - Wyższe wagi dla wskaźników momentum (RSI, Stochastic, MFI)
4. **trend_focused** - Wyższe wagi dla wskaźników trendu (MACD, MA, ADX)
5. **volume_focused** - Wyższe wagi dla wskaźników volume (OBV, CMF, VWAP)
6. **conservative** - Wyższe progi, niższe wagi (mniej sygnałów, silniejsze)
7. **aggressive** - Niższe progi, wyższe wagi (więcej sygnałów)

### Parametry Backtestu

- **Okres**: 180 dni (ostatnie 6 miesięcy)
- **Symbole**: BTC, ETH, SOL, AAPL, MSFT, TSLA
- **Strategia**: `follow_ai` (podążanie za sygnałami AI)
- **Progi sygnałów**: 10, 20, 30
- **Kapitał początkowy**: $10,000

### Metryki Oceny

Konfiguracje są oceniane według:
1. **Sharpe Ratio** (priorytet 50%) - ryzyko-skorygowany zwrot
2. **Win Rate** (priorytet 30%) - skuteczność sygnałów
3. **Total Return** (priorytet 20%) - całkowity zwrot

### Wyniki

Wyniki są zapisywane do `weight_optimization_results.json` i zawierają:
- Metryki dla każdej konfiguracji i progu
- Ranking konfiguracji według composite score
- Najlepsza konfiguracja ogólnie oraz według każdej metryki

### Aktualne Wagi (no_double_counting)

Po optymalizacji, rekomendowane wagi:
- **RSI**: ±15
- **MACD Crossover**: ±20 (najwyższa waga)
- **MACD Trend**: ±5 (tylko gdy brak crossovu)
- **MA50/MA200**: ±5/±8 (tylko gdy brak Golden/Death Cross)
- **Golden/Death Cross**: ±10 (gdy aktywny, wyklucza MA50/MA200)
- **Bollinger Bands**: ±12
- **CCI**: ±8 (próg ±150)
- **Williams %R**: ±4 (redukowane)
- **ATR**: Brak (tylko confidence adjustment)

## Roadmap - Faza 2 (Przyszłość)

### 2.1 Support/Resistance Detection ✅
- ✅ Automatyczne wykrywanie poziomów S/R
- ✅ Statystyczna analiza swing highs/lows
- ✅ Fibonacci Retracements (23.6%, 38.2%, 50%, 61.8%)

### 2.2 Pattern Recognition ✅
- ✅ Basic Pattern Detection: head & shoulders, triangles, flags
- ✅ Candlestick Patterns: doji, hammer, engulfing
- ⏳ ML-based pattern recognition (TensorFlow/PyTorch) - przyszłość

### 2.3 Market Context & Correlation
- Beta Calculation względem benchmark (BTC vs S&P500, ETH vs BTC)
- Relative Strength vs Market
- Correlation Matrix z innymi assetami w portfolio

### 2.4 Advanced Indicators ✅
- ✅ Ichimoku Cloud (kompleksowy system trend analysis)
- ✅ Volume Profile (volume na poziomach cenowych)
  - Point of Control (POC) - poziom z najwyższym volume
  - Value Area High (VAH) - górna granica 70% volume
  - Value Area Low (VAL) - dolna granica 70% volume
  - Wykrywanie pozycji ceny względem POC/VAH/VAL

### 2.5 Machine Learning Enhancements
- ML-based Pattern Recognition
- Sentiment-Enhanced Predictions (ensemble model)

### 2.6 Risk Metrics ✅
- ✅ Value at Risk (VaR)
- ✅ Maximum Drawdown Analysis

### 2.7 Market Microstructure
- Order Flow Analysis (jeśli dostępne dane)
- Spread Analysis (bid-ask spread)

### 3. Analiza Sentymentu (`analyze_sentiment`)

**Używa:** Transformers (FinBERT) + NewsAPI

**Parametry:**
- `symbol` - Symbol aktywa
- `asset_type` - Typ aktywa
- `news_sources` - Opcjonalna lista źródeł newsów

**Zwraca:**
- `overall_sentiment` - 'bullish', 'neutral', 'bearish'
- `sentiment_score` - Wynik -1.0 do 1.0
- `sentiment_breakdown` - Rozkład sentymentu

## Fallbacki

Jeśli biblioteki AI nie są zainstalowane, aplikacja automatycznie używa fallbacków:

- **Prophet → Mock predictions:** Proste liniowe przewidywania
- **TA → Simple rebalancing:** Rekomendacje oparte tylko na alokacji (bez wskaźników)
- **Transformers → Mock sentiment:** Neutralny sentyment (0.33/0.34/0.33)
- **NewsAPI → Mock news:** Przykładowe nagłówki

## Rozwiązywanie problemów

### Prophet zwraca ujemne wartości cen

**Problem:** Przewidywania spadają poniżej zera

**Rozwiązanie:** 
- Implementacja automatycznie clampuje wartości do >= 1% obecnej ceny
- Dodano `growth='linear'` do Prophet model
- Zmniejszono `changepoint_prior_scale` dla bardziej konserwatywnych przewidywań

### Błędy basedpyright

**Problem:** `reportMissingImports` dla bibliotek AI

**Rozwiązanie:** Utworzono `pyrightconfig.json` z ignorowaniem tych bibliotek (są opcjonalne)

### Model nie trenuje się

**Problem:** Niewystarczająca ilość danych historycznych

**Rozwiązanie:** 
- Wymagane minimum: 14 punktów danych
- Automatyczny fallback do mock predictions jeśli za mało danych
- Sprawdź logi: `Insufficient historical data`

## Wydajność

- **Prophet:** Trening modelu ~2-10 sekund (zależnie od ilości danych)
- **Transformers:** Pierwsze ładowanie FinBERT ~30-60 sekund (cache'owane)
- **TA:** Obliczenia wskaźników ~0.1-0.5 sekundy

## Licencje

- **Prophet:** MIT License
- **TA:** MIT License  
- **Transformers:** Apache 2.0
- **NewsAPI:** Commercial API (wymaga klucza)

