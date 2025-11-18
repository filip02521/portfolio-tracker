# 🚫 Informacje o ograniczeniach API

## ⚠️ Ważne informacje o dostępności API

### Binance API
**Problem:** `Service unavailable from a restricted location`

**Przyczyna:** Binance blokuje dostęp do API z niektórych krajów/regionów ze względu na regulacje prawne.

**Rozwiązania:**
1. **VPN** - użyj VPN z lokalizacji, gdzie Binance jest dostępne
2. **Binance.US** - jeśli jesteś w USA, użyj Binance.US API
3. **Inne giełdy** - rozważ użycie alternatywnych giełd (Bybit, KuCoin, itp.)

### Bybit API
**Problem:** `You have breached the ip rate limit`

**Przyczyna:** Przekroczenie limitu żądań API (600 żądań na 5 sekund)

**Rozwiązania:**
1. **Rate Limiting** - dodano automatyczne opóźnienia między żądaniami
2. **Retry Logic** - eksponencjalne opóźnienia przy błędach rate limit
3. **Mniej żądań** - ograniczenie częstotliwości synchronizacji

## 🔧 Co zostało naprawione

### 1. Rate Limiting Protection
- Dodano `_make_request_with_retry()` do klientów API
- Eksponencjalne opóźnienia przy błędach rate limit
- Maksymalnie 3 próby z opóźnieniami: 1s, 2s, 4s

### 2. Lepsze komunikaty błędów
- Informacje o ograniczeniach geograficznych
- Szczegółowe komunikaty o błędach API
- Graceful handling błędów

### 3. Fallback Strategy
- Aplikacja działa nawet gdy jeden API nie działa
- Możliwość używania tylko jednej giełdy
- Informacje o statusie każdego API

## 📋 Rekomendacje

### Dla użytkowników w Polsce:
1. **Bybit** - powinien działać bez problemów
2. **Binance** - może wymagać VPN
3. **XTB** - działa lokalnie

### Dla użytkowników w USA:
1. **Binance.US** - zamiast Binance.com
2. **Bybit** - może być ograniczony
3. **Lokalne brokerzy** - Interactive Brokers, TD Ameritrade

### Ogólne wskazówki:
1. **Nie używaj VPN** podczas testowania lokalnie
2. **Sprawdź regulacje** w swoim kraju
3. **Używaj oficjalnych API** tylko z dozwolonych lokalizacji
4. **Monitoruj limity** żądań API

## 🛠️ Konfiguracja

### Streamlit Cloud
- API keys są bezpiecznie przechowywane w Secrets
- Automatyczne retry przy błędach
- Graceful degradation przy problemach z API

### Lokalne środowisko
- Użyj pliku `.env` dla kluczy API
- Testuj z VPN jeśli potrzebne
- Monitoruj logi aplikacji

## 📞 Wsparcie

Jeśli masz problemy z API:
1. Sprawdź logi aplikacji
2. Zweryfikuj klucze API
3. Sprawdź status giełdy
4. Rozważ użycie VPN
5. Skontaktuj się z supportem giełdy
