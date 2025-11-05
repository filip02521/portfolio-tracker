# Confluence Strategy Documentation

## Overview

The Confluence Strategy is an advanced trading strategy that combines multiple technical indicators to identify high-probability entry and exit points. The strategy is based on the principle that when multiple independent indicators confirm the same direction, the probability of a successful trade increases significantly.

## Strategy Components

### Entry Signal Analysis

The entry signal is determined by analyzing 6 key confluence conditions:

1. **Trend Confirmation**: EMA 50 > EMA 200 (uptrend) OR Golden Cross
2. **Price Position**: Pullback to EMA 50 support in uptrend OR price above EMA 50/200
3. **RSI Condition**: RSI in range 40-50 (not overbought) OR RSI recovering from oversold (>30)
4. **Reversal Pattern**: Bullish Pin Bar OR Engulfing Pattern at support
5. **Volume Confirmation**: Volume > 1.5x average on breakout
6. **Market Structure**: Higher High pattern confirming uptrend

**Entry Signal Logic:**
- **Buy Signal**: Confluence score >= 4 and confidence >= 0.7
- **Hold Signal**: Confluence score < 4 or confidence < 0.7

**Confidence Calculation:**
- Base confidence: 0.5 + (confluence_score * 0.1)
- Capped at 0.9 maximum
- Higher confluence score = higher confidence

### Exit Signal Analysis

The exit strategy uses a comprehensive position management approach:

#### Stop Loss (SL)
- **ATR-based**: `entry_price - (2 * ATR)` for long positions
- **Fallback**: 5% below entry price if ATR unavailable
- **Risk Limit**: Maximum 1-2% of portfolio value per trade

#### Take Profit Levels
- **TP1 (R:R 1:2)**: 50% of position at `entry_price + 2 * (entry_price - stop_loss)`
- **TP2 (R:R 1:3)**: 25% of position at `entry_price + 3 * (entry_price - stop_loss)`
- **Trailing Stop**: 50% of position protected by trailing stop

#### Trailing Stop
- **Activation**: Only when position is in profit (>1%)
- **Methods**:
  1. 7% below highest price since entry (for crypto)
  2. Below EMA 20 (if available)
  3. Below last swing low
- Uses the most conservative (highest) trailing stop level

#### Exit Conditions
1. Take Profit 1 hit → Sell 50%
2. Take Profit 2 hit → Sell additional 25%
3. Trailing Stop hit → Sell remaining 50% (100% total)
4. Stop Loss hit → Sell 100%
5. RSI > 70 and overbought → Sell 50%
6. Price closes below EMA 10/20 → Sell 50%

### Risk Management

- **Position Sizing**: Based on risk per trade (default 2% of portfolio)
- **Risk Calculation**: `position_size = (portfolio_value * risk_per_trade) / (entry_price - stop_loss)`
- **Maximum Risk**: 1-2% of total portfolio value per trade

## Backtesting

The backtesting system simulates the strategy on historical data:

### Parameters
- **Min Confluence Score**: Minimum score to enter (default: 4)
- **Min Confidence**: Minimum confidence to enter (default: 0.7)
- **Risk Per Trade**: Percentage of portfolio to risk (default: 2%)
- **Intervals**: 1H, 4H, 1D

### Metrics Calculated
- Total Return (%)
- CAGR (Compound Annual Growth Rate)
- Sharpe Ratio
- Max Drawdown (%)
- Win Rate (%)
- Profit Factor
- Total Trades
- Winning/Losing Trades
- Equity Curve (time series)
- Trade History (detailed)

## API Endpoints

### POST `/api/strategy/confluence/analyze-entry`
Analyze entry signals for a symbol.

**Request:**
```json
{
  "symbol": "BTC",
  "interval": "4h",
  "timeframe": "4h"
}
```

**Response:**
```json
{
  "entry_signal": "buy",
  "confidence": 0.85,
  "confluence_score": 5,
  "entry_price": 50000.0,
  "entry_reasons": ["Uptrend confirmed", "RSI in optimal range", ...],
  "confluence_conditions": ["✅ Uptrend confirmed", "❌ No volume confirmation", ...],
  "indicators": {...},
  "patterns": {...},
  "risk_level": "low"
}
```

### POST `/api/strategy/confluence/analyze-exit`
Analyze exit signals for an open position.

**Request:**
```json
{
  "symbol": "BTC",
  "entry_price": 50000.0,
  "entry_date": "2024-01-01T00:00:00Z",
  "current_price": 51000.0,
  "current_date": "2024-01-02T00:00:00Z",
  "interval": "4h",
  "portfolio_value": 10000.0,
  "risk_per_trade": 0.02
}
```

**Response:**
```json
{
  "exit_signal": "hold",
  "exit_reason": null,
  "stop_loss": 47500.0,
  "take_profit_1": 55000.0,
  "take_profit_2": 57500.0,
  "trailing_stop": 49500.0,
  "current_return": 2.0,
  "risk_reward_ratio": 2.0,
  "position_size": 0.8,
  "position_value": 40000.0
}
```

### POST `/api/strategy/confluence/backtest`
Run backtest on historical data.

**Request:**
```json
{
  "symbol": "BTC",
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-12-01T00:00:00Z",
  "initial_capital": 10000.0,
  "interval": "4h",
  "risk_per_trade": 0.02,
  "min_confluence_score": 4,
  "min_confidence": 0.7
}
```

**Response:**
```json
{
  "status": "success",
  "total_return": 25.5,
  "cagr": 30.2,
  "sharpe_ratio": 1.85,
  "max_drawdown": 12.3,
  "win_rate": 65.5,
  "profit_factor": 2.1,
  "total_trades": 45,
  "winning_trades": 29,
  "losing_trades": 16,
  "equity_curve": [...],
  "trade_history": [...]
}
```

### GET `/api/strategy/confluence/history/{symbol}`
Get historical confluence signals (placeholder for future implementation).

## Usage Examples

### Python Example

```python
from confluence_strategy_service import ConfluenceStrategyService
from market_data_service import MarketDataService

# Initialize services
market_data_service = MarketDataService()
strategy_service = ConfluenceStrategyService(market_data_service)

# Analyze entry signal
entry_result = strategy_service.analyze_entry_signals(
    symbol='BTC',
    interval='4h',
    timeframe='4h'
)

if entry_result['entry_signal'] == 'buy' and entry_result['confidence'] >= 0.7:
    print(f"Buy signal: {entry_result['entry_price']}")
    print(f"Confidence: {entry_result['confidence']}")
    print(f"Confluence Score: {entry_result['confluence_score']}/6")

# Analyze exit signal
exit_result = strategy_service.analyze_exit_signals(
    symbol='BTC',
    entry_price=50000.0,
    entry_date='2024-01-01T00:00:00Z',
    current_price=51000.0,
    current_date='2024-01-02T00:00:00Z',
    interval='4h',
    portfolio_value=10000.0,
    risk_per_trade=0.02
)

print(f"Exit Signal: {exit_result['exit_signal']}")
print(f"Stop Loss: ${exit_result['stop_loss']}")
print(f"Take Profit 1: ${exit_result['take_profit_1']}")

# Run backtest
backtest_result = strategy_service.backtest_confluence_strategy(
    symbol='BTC',
    start_date='2024-01-01T00:00:00Z',
    end_date='2024-12-01T00:00:00Z',
    initial_capital=10000.0,
    interval='4h',
    risk_per_trade=0.02,
    min_confluence_score=4,
    min_confidence=0.7
)

print(f"Backtest Results:")
print(f"Total Return: {backtest_result['total_return']}%")
print(f"Win Rate: {backtest_result['win_rate']}%")
print(f"Profit Factor: {backtest_result['profit_factor']}")
```

## Best Practices

1. **Wait for High Confluence**: Only enter when confluence score >= 4 and confidence >= 0.7
2. **Respect Stop Loss**: Always use stop loss to protect capital
3. **Position Sizing**: Never risk more than 2% of portfolio per trade
4. **Take Partial Profits**: Use TP1 and TP2 to secure profits
5. **Trailing Stop**: Let trailing stop protect remaining position
6. **Market Conditions**: Strategy works best in trending markets
7. **Timeframe Selection**: 4H interval is recommended for crypto, 1D for stocks

## Limitations

1. **Data Availability**: Requires sufficient historical data (200+ candles for entry, 50+ for exit)
2. **Market Conditions**: May generate fewer signals in sideways markets
3. **API Rate Limits**: Dependent on market data provider availability
4. **Backtesting**: Results are historical and don't guarantee future performance

## Configuration

Key parameters can be adjusted:

- `min_confluence_score`: Minimum score to enter (default: 4)
- `min_confidence`: Minimum confidence to enter (default: 0.7)
- `risk_per_trade`: Risk percentage per trade (default: 0.02 = 2%)
- `interval`: Data interval ('1h', '4h', '1d')

## Troubleshooting

### No Entry Signals Generated
- Check if symbol has sufficient historical data (200+ candles)
- Verify market data service is working
- Check if confluence conditions are being met (may need lower threshold)

### Stop Loss Too Tight/Wide
- ATR-based stop loss adapts to volatility
- Can be adjusted by modifying ATR multiplier (currently 2x)

### Backtest Shows 0 Trades
- Increase backtest period (need more historical data)
- Lower `min_confluence_score` or `min_confidence` thresholds
- Check if symbol has sufficient price data

## Future Enhancements

- [ ] Historical signal storage and retrieval
- [ ] Real-time position tracking
- [ ] Multi-symbol portfolio backtesting
- [ ] Advanced chart visualization with annotations
- [ ] Alert system for confluence signals
- [ ] Performance optimization for large datasets

