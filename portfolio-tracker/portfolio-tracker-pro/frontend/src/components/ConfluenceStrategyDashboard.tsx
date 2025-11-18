import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  CircularProgress,
  Alert,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  LinearProgress,
  Divider,
  Tabs,
  Tab,
  Stack,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  CheckCircle,
  Cancel,
  Warning,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Label,
} from 'recharts';

const srOnlyStyles = {
  position: 'absolute',
  width: 1,
  height: 1,
  padding: 0,
  margin: -1,
  overflow: 'hidden',
  clip: 'rect(0 0 0 0)',
  whiteSpace: 'nowrap' as const,
  border: 0,
};

interface ConfluenceEntrySignal {
  entry_signal: 'buy' | 'sell' | 'hold';
  confidence: number;
  confluence_score: number;
  entry_price: number;
  entry_reasons: string[];
  confluence_conditions: string[];
  indicators?: {
    rsi?: { value: number; signal: string };
    macd?: any;
    bollinger_bands?: any;
    stochastic?: any;
  };
  patterns?: {
    pin_bar?: any;
    candlestick?: any;
    market_structure?: any;
  };
  ema_analysis?: {
    golden_cross: boolean;
    support_test: boolean;
    price_above_ema50: boolean;
    price_above_ema200: boolean;
    trend_strength: number;
  };
  volume_analysis?: {
    volume_ratio: number;
    breakout: boolean;
    signal: string;
  };
  risk_level: 'low' | 'medium' | 'high';
  interval: string;
  timestamp: string;
  error?: string;
}

interface ConfluenceExitSignal {
  exit_signal: 'hold' | 'sell_50%' | 'sell_100%';
  exit_reason?: string;
  stop_loss: number;
  take_profit_1: number;
  take_profit_2: number;
  trailing_stop?: number;
  current_return: number;
  risk_reward_ratio: number;
  position_size: number;
  position_value: number;
  risk_amount: number;
  entry_price: number;
  current_price: number;
  error?: string;
}

interface BacktestResult {
  status: 'success' | 'error';
  total_return?: number;
  cagr?: number;
  sharpe_ratio?: number;
  max_drawdown?: number;
  win_rate?: number;
  profit_factor?: number;
  total_trades?: number;
  winning_trades?: number;
  losing_trades?: number;
  initial_capital?: number;
  final_value?: number;
  equity_curve?: Array<{ date: string; value: number }>;
  trade_history?: Array<any>;
  symbol?: string;
  interval?: string;
  error?: string;
}

const ConfluenceStrategyDashboard: React.FC = () => {
  const [selectedSymbol, setSelectedSymbol] = useState('BTC');
  const [selectedInterval, setSelectedInterval] = useState('4h');
  const [tabValue, setTabValue] = useState(0);
  
  const [entrySignal, setEntrySignal] = useState<ConfluenceEntrySignal | null>(null);
  const [exitSignal, setExitSignal] = useState<ConfluenceExitSignal | null>(null);
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Position tracking (simulated - would come from user's actual positions)
  const [currentPosition, setCurrentPosition] = useState<{
    symbol: string;
    entry_price: number;
    entry_date: string;
    shares: number;
  } | null>(null);
  
  const symbols = ['BTC', 'ETH', 'SOL', 'BNB', 'AAPL', 'MSFT', 'TSLA', 'GOOGL'];
  const intervals = ['1h', '4h', '1d'];
  
  const getAuthToken = () => {
    return localStorage.getItem('authToken');
  };
  
  const getApiUrl = (endpoint: string) => {
    const baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    const apiUrl = baseUrl.endsWith('/api') ? baseUrl : `${baseUrl}/api`;
    return `${apiUrl}${endpoint}`;
  };
  
  const fetchEntrySignal = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const token = getAuthToken();
      if (!token) {
        setError('Authentication required');
        return;
      }
      
      const response = await fetch(
        getApiUrl('/strategy/confluence/analyze-entry'),
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            symbol: selectedSymbol,
            interval: selectedInterval,
            timeframe: selectedInterval,
          }),
        }
      );
      
      if (!response.ok) {
        throw new Error(`Failed to fetch entry signal: ${response.statusText}`);
      }
      
      const data = await response.json();
      setEntrySignal(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch entry signal');
      setEntrySignal(null);
    } finally {
      setLoading(false);
    }
  }, [selectedSymbol, selectedInterval]);
  
  const fetchExitSignal = useCallback(async () => {
    if (!currentPosition) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const token = getAuthToken();
      if (!token) {
        setError('Authentication required');
        return;
      }
      
      // Get current price (simplified - would use real-time price)
      const currentPrice = currentPosition.entry_price * 1.02; // Simulated
      const currentDate = new Date().toISOString();
      
      const response = await fetch(
        getApiUrl('/strategy/confluence/analyze-exit'),
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            symbol: currentPosition.symbol,
            entry_price: currentPosition.entry_price,
            entry_date: currentPosition.entry_date,
            current_price: currentPrice,
            current_date: currentDate,
            interval: selectedInterval,
            portfolio_value: 10000,
            risk_per_trade: 0.02,
          }),
        }
      );
      
      if (!response.ok) {
        throw new Error(`Failed to fetch exit signal: ${response.statusText}`);
      }
      
      const data = await response.json();
      setExitSignal(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch exit signal');
      setExitSignal(null);
    } finally {
      setLoading(false);
    }
  }, [currentPosition, selectedInterval]);
  
  const runBacktest = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const token = getAuthToken();
      if (!token) {
        setError('Authentication required');
        return;
      }
      
      // Default backtest period: last 90 days
      const endDate = new Date().toISOString();
      const startDate = new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString();
      
      const response = await fetch(
        getApiUrl('/strategy/confluence/backtest'),
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            symbol: selectedSymbol,
            start_date: startDate,
            end_date: endDate,
            initial_capital: 10000,
            interval: selectedInterval,
            risk_per_trade: 0.02,
            min_confluence_score: 4,
            min_confidence: 0.7,
          }),
        }
      );
      
      if (!response.ok) {
        throw new Error(`Backtest failed: ${response.statusText}`);
      }
      
      const data = await response.json();
      setBacktestResult(data);
    } catch (err: any) {
      setError(err.message || 'Backtest failed');
      setBacktestResult({ status: 'error', error: err.message });
    } finally {
      setLoading(false);
    }
  };
  
  // DISABLED: Automatic signal fetching - now manual only via buttons
  // useEffect(() => {
  //   if (tabValue === 0) {
  //     fetchEntrySignal();
  //   } else if (tabValue === 1 && currentPosition) {
  //     fetchExitSignal();
  //   }
  // }, [tabValue, selectedSymbol, selectedInterval, fetchEntrySignal, fetchExitSignal, currentPosition]);
  
  const renderEntryPanel = () => (
    <Stack component="section" spacing={3} aria-labelledby="entry-panel-heading">
      <Typography id="entry-panel-heading" variant="h5" sx={srOnlyStyles}>
        Entry signal analysis
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap', alignItems: 'center' }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Symbol</InputLabel>
            <Select
              value={selectedSymbol}
              label="Symbol"
              onChange={(e) => setSelectedSymbol(e.target.value)}
            >
              {symbols.map((sym) => (
                <MenuItem key={sym} value={sym}>{sym}</MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Interval</InputLabel>
            <Select
              value={selectedInterval}
              label="Interval"
              onChange={(e) => setSelectedInterval(e.target.value)}
            >
              {intervals.map((int) => (
                <MenuItem key={int} value={int}>{int}</MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <Button
            variant="contained"
            onClick={fetchEntrySignal}
            disabled={loading}
          >
            Analyze Entry
          </Button>
        </Box>
        
        {loading && <CircularProgress size={24} sx={{ mb: 2 }} />}
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        
        {entrySignal && (
          <Box>
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, gap: 2, mb: 3 }}>
              <Card>
                <CardContent>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Entry Signal
                  </Typography>
                  <Typography variant="h4" color={entrySignal.entry_signal === 'buy' ? 'success.main' : 'text.primary'}>
                    {entrySignal.entry_signal.toUpperCase()}
                  </Typography>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Confidence
                  </Typography>
                  <Typography variant="h4">
                    {(entrySignal.confidence * 100).toFixed(1)}%
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={entrySignal.confidence * 100}
                    sx={{ mt: 1 }}
                  />
                </CardContent>
              </Card>
              
              <Card>
                <CardContent>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Confluence Score
                  </Typography>
                  <Typography variant="h4">
                    {entrySignal.confluence_score}/6
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={(entrySignal.confluence_score / 6) * 100}
                    sx={{ mt: 1 }}
                  />
                </CardContent>
              </Card>
              
              <Card>
                <CardContent>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Entry Price
                  </Typography>
                  <Typography variant="h4">
                    ${entrySignal.entry_price.toFixed(2)}
                  </Typography>
                  <Chip
                    label={entrySignal.risk_level}
                    color={entrySignal.risk_level === 'low' ? 'success' : entrySignal.risk_level === 'medium' ? 'warning' : 'error'}
                    size="small"
                    sx={{ mt: 1 }}
                  />
                </CardContent>
              </Card>
            </Box>
            
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Confluence Conditions
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableBody>
                      {entrySignal.confluence_conditions.map((condition, idx) => (
                        <TableRow key={idx}>
                          <TableCell>
                            {condition.startsWith('✅') ? (
                              <CheckCircle color="success" sx={{ mr: 1, verticalAlign: 'middle' }} />
                            ) : (
                              <Cancel color="error" sx={{ mr: 1, verticalAlign: 'middle' }} />
                            )}
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {condition.replace('✅', '').replace('❌', '').trim()}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
            
            {entrySignal.entry_reasons.length > 0 && (
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Entry Reasons
                  </Typography>
                  <Box component="ul" sx={{ pl: 2 }}>
                    {entrySignal.entry_reasons.map((reason, idx) => (
                      <li key={idx}>
                        <Typography variant="body2">{reason.replace('✅', '').trim()}</Typography>
                      </li>
                    ))}
                  </Box>
                </CardContent>
              </Card>
            )}
          </Box>
        )}
      </Paper>
    </Stack>
  );
  
  const renderExitPanel = () => (
    <Stack component="section" spacing={3} aria-labelledby="management-panel-heading">
      <Typography id="management-panel-heading" variant="h5" sx={srOnlyStyles}>
        Position management and exit signals
      </Typography>
      <Paper sx={{ p: 3 }}>
        {!currentPosition ? (
          <Alert severity="info">
            No active position. Entry signals will create a simulated position for testing.
          </Alert>
        ) : (
          <Box>
            <Typography variant="h6" gutterBottom>
              Position Management
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' }, gap: 2, mb: 3 }}>
              <Card>
                <CardContent>
                  <Typography variant="body2" color="text.secondary">Entry Price</Typography>
                  <Typography variant="h6">${currentPosition.entry_price.toFixed(2)}</Typography>
                </CardContent>
              </Card>
              <Card>
                <CardContent>
                  <Typography variant="body2" color="text.secondary">Current Price</Typography>
                  <Typography variant="h6">
                    ${exitSignal?.current_price.toFixed(2) || 'N/A'}
                  </Typography>
                </CardContent>
              </Card>
              <Card>
                <CardContent>
                  <Typography variant="body2" color="text.secondary">P&L</Typography>
                  <Typography variant="h6" color={exitSignal?.current_return && exitSignal.current_return > 0 ? 'success.main' : 'error.main'}>
                    {exitSignal?.current_return ? `${exitSignal.current_return.toFixed(2)}%` : 'N/A'}
                  </Typography>
                </CardContent>
              </Card>
            </Box>
            
            {exitSignal && (
              <Box>
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 2 }}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>Stop Loss</Typography>
                      <Typography variant="h5" color="error">
                        ${exitSignal.stop_loss.toFixed(2)}
                      </Typography>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>Take Profit 1 (R:R 1:2)</Typography>
                      <Typography variant="h5" color="success.main">
                        ${exitSignal.take_profit_1.toFixed(2)}
                      </Typography>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>Take Profit 2 (R:R 1:3)</Typography>
                      <Typography variant="h5" color="success.main">
                        ${exitSignal.take_profit_2.toFixed(2)}
                      </Typography>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>Trailing Stop</Typography>
                      <Typography variant="h5">
                        {exitSignal.trailing_stop ? `$${exitSignal.trailing_stop.toFixed(2)}` : 'Not active'}
                      </Typography>
                    </CardContent>
                  </Card>
                </Box>
                
                <Card sx={{ mt: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Exit Signal</Typography>
                    <Chip
                      label={exitSignal.exit_signal}
                      color={exitSignal.exit_signal === 'hold' ? 'default' : 'warning'}
                      sx={{ mb: 2 }}
                    />
                    {exitSignal.exit_reason && (
                      <Typography variant="body2" color="text.secondary">
                        Reason: {exitSignal.exit_reason}
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Box>
            )}
          </Box>
        )}
      </Paper>
    </Stack>
  );
  
  const renderBacktestPanel = () => (
    <Stack component="section" spacing={3} aria-labelledby="backtest-panel-heading">
      <Typography id="backtest-panel-heading" variant="h5" sx={srOnlyStyles}>
        Backtesting results and trade history
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap', alignItems: 'center' }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Symbol</InputLabel>
            <Select
              value={selectedSymbol}
              label="Symbol"
              onChange={(e) => setSelectedSymbol(e.target.value)}
            >
              {symbols.map((sym) => (
                <MenuItem key={sym} value={sym}>{sym}</MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Interval</InputLabel>
            <Select
              value={selectedInterval}
              label="Interval"
              onChange={(e) => setSelectedInterval(e.target.value)}
            >
              {intervals.map((int) => (
                <MenuItem key={int} value={int}>{int}</MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <Button
            variant="contained"
            onClick={runBacktest}
            disabled={loading}
          >
            Run Backtest
          </Button>
        </Box>
        
        {loading && <CircularProgress size={24} sx={{ mb: 2 }} />}
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        
        {backtestResult && (
          <Box>
            {backtestResult.status === 'error' ? (
              <Alert severity="error">{backtestResult.error}</Alert>
            ) : (
              <Box>
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, gap: 2 }}>
                  <Card>
                    <CardContent>
                      <Typography variant="body2" color="text.secondary">Total Return</Typography>
                      <Typography variant="h5" color={backtestResult.total_return && backtestResult.total_return > 0 ? 'success.main' : 'error.main'}>
                        {backtestResult.total_return?.toFixed(2)}%
                      </Typography>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent>
                      <Typography variant="body2" color="text.secondary">CAGR</Typography>
                      <Typography variant="h5">
                        {backtestResult.cagr?.toFixed(2)}%
                      </Typography>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent>
                      <Typography variant="body2" color="text.secondary">Sharpe Ratio</Typography>
                      <Typography variant="h5">
                        {backtestResult.sharpe_ratio?.toFixed(3)}
                      </Typography>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent>
                      <Typography variant="body2" color="text.secondary">Win Rate</Typography>
                      <Typography variant="h5">
                        {backtestResult.win_rate?.toFixed(2)}%
                      </Typography>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent>
                      <Typography variant="body2" color="text.secondary">Profit Factor</Typography>
                      <Typography variant="h5">
                        {backtestResult.profit_factor?.toFixed(2)}
                      </Typography>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent>
                      <Typography variant="body2" color="text.secondary">Max Drawdown</Typography>
                      <Typography variant="h5" color="error">
                        {backtestResult.max_drawdown?.toFixed(2)}%
                      </Typography>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent>
                      <Typography variant="body2" color="text.secondary">Total Trades</Typography>
                      <Typography variant="h5">
                        {backtestResult.total_trades || 0}
                      </Typography>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent>
                      <Typography variant="body2" color="text.secondary">Winning Trades</Typography>
                      <Typography variant="h5" color="success.main">
                        {backtestResult.winning_trades || 0}
                      </Typography>
                    </CardContent>
                  </Card>
                </Box>
                
                {backtestResult.equity_curve && backtestResult.equity_curve.length > 0 && (
                  <Box sx={{ mt: 2 }}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>Equity Curve</Typography>
                        <ResponsiveContainer width="100%" height={300}>
                          <LineChart data={backtestResult.equity_curve}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis 
                              dataKey="date" 
                              tick={{ fontSize: 12 }}
                              angle={-45}
                              textAnchor="end"
                              height={80}
                            />
                            <YAxis 
                              tick={{ fontSize: 12 }}
                              tickFormatter={(value) => `$${value.toFixed(0)}`}
                            />
                            <Tooltip 
                              formatter={(value: number) => `$${value.toFixed(2)}`}
                              labelFormatter={(label) => `Date: ${label}`}
                            />
                            <Line 
                              type="monotone" 
                              dataKey="value" 
                              stroke="#2563eb" 
                              strokeWidth={2}
                              dot={false}
                              name="Portfolio Value"
                            />
                            <ReferenceLine 
                              y={backtestResult.initial_capital} 
                              stroke="#666" 
                              strokeDasharray="3 3"
                              label="Initial Capital"
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>
                  </Box>
                )}
                
                {backtestResult.trade_history && backtestResult.trade_history.length > 0 && (
                  <Box sx={{ mt: 2 }}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>Trade History</Typography>
                        <TableContainer>
                          <Table size="small">
                            <TableHead>
                              <TableRow>
                                <TableCell>Date</TableCell>
                                <TableCell>Action</TableCell>
                                <TableCell>Price</TableCell>
                                <TableCell>Shares</TableCell>
                                <TableCell>Value</TableCell>
                                <TableCell>Return %</TableCell>
                                <TableCell>Reason</TableCell>
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {backtestResult.trade_history.slice(0, 20).map((trade: any, idx: number) => (
                                <TableRow key={idx}>
                                  <TableCell>{trade.date}</TableCell>
                                  <TableCell>
                                    <Chip
                                      label={trade.action}
                                      color={trade.action === 'buy' ? 'primary' : 'secondary'}
                                      size="small"
                                    />
                                  </TableCell>
                                  <TableCell>${trade.price?.toFixed(2)}</TableCell>
                                  <TableCell>{trade.shares?.toFixed(4)}</TableCell>
                                  <TableCell>${trade.value?.toFixed(2)}</TableCell>
                                  <TableCell>
                                    {trade.return_pct ? (
                                      <Typography
                                        color={trade.return_pct > 0 ? 'success.main' : 'error.main'}
                                      >
                                        {trade.return_pct.toFixed(2)}%
                                      </Typography>
                                    ) : '-'}
                                  </TableCell>
                                  <TableCell>{trade.reason || '-'}</TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </TableContainer>
                      </CardContent>
                    </Card>
                  </Box>
                )}
              </Box>
            )}
          </Box>
        )}
      </Paper>
    </Stack>
  );
  
  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Stack spacing={3}>
        <Box component="header">
          <Typography variant="h4" component="h1" gutterBottom>
            Confluence Strategy Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Advanced trading strategy based on confluence of multiple technical indicators
          </Typography>
        </Box>

        <Paper>
          <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)} aria-label="Confluence dashboard sections">
            <Tab label="Entry Signals" id="confluence-tab-0" aria-controls="confluence-panel-0" />
            <Tab label="Position Management" id="confluence-tab-1" aria-controls="confluence-panel-1" />
            <Tab label="Backtesting" id="confluence-tab-2" aria-controls="confluence-panel-2" />
          </Tabs>
        </Paper>

        <Box>
          {tabValue === 0 && (
            <Box id="confluence-panel-0" role="tabpanel" aria-labelledby="confluence-tab-0">
              {renderEntryPanel()}
            </Box>
          )}
          {tabValue === 1 && (
            <Box id="confluence-panel-1" role="tabpanel" aria-labelledby="confluence-tab-1">
              {renderExitPanel()}
            </Box>
          )}
          {tabValue === 2 && (
            <Box id="confluence-panel-2" role="tabpanel" aria-labelledby="confluence-tab-2">
              {renderBacktestPanel()}
            </Box>
          )}
        </Box>
      </Stack>
    </Container>
  );
};

export default ConfluenceStrategyDashboard;

