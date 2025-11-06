import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  TextField,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Checkbox,
  FormControlLabel,
  FormControl,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Assessment,
  Search,
  FilterList,
  ExpandMore,
  CheckCircle,
  Cancel,
  Warning,
} from '@mui/icons-material';

interface FundamentalData {
  symbol: string;
  company_name: string;
  market_cap: number;
  total_assets: number;
  total_liabilities: number;
  net_income: number;
  operating_cash_flow: number;
  revenue: number;
  ebit: number;
  current_assets: number;
  current_liabilities: number;
  long_term_debt: number;
  book_value: number;
  shares_outstanding: number;
}

interface FScoreResult {
  score: number;
  max_score: number;
  breakdown: Record<string, number>;
  details: string[];
  interpretation: string;
}

interface ZScoreResult {
  z_score: number;
  components: {
    A: number;
    B: number;
    C: number;
    D: number;
    E: number;
  };
  interpretation: string;
  risk_level: 'safe' | 'moderate' | 'high' | 'unknown';
  recommendation: string;
}

interface MagicFormulaResult {
  roic: number;
  ebit_ev: number;
  combined_score: number;
  current_price: number;
  enterprise_value: number;
  invested_capital: number;
}

interface AccrualRatioResult {
  accrual_ratio: number;
  accrual_amount: number;
  net_income: number;
  operating_cash_flow: number;
  interpretation: string;
  quality_flag: 'excellent' | 'good' | 'acceptable' | 'warning' | 'danger' | 'unknown';
  recommendation: string;
}

interface FullAnalysisResult {
  symbol: string;
  fundamental_data: FundamentalData;
  f_score: FScoreResult;
  z_score: ZScoreResult;
  magic_formula: MagicFormulaResult;
  accrual_ratio: AccrualRatioResult;
  overall_recommendation: string;
  passes_vq_plus_filters: boolean;
  summary: {
    f_score_value: number;
    z_score_value: number;
    z_score_risk: string;
    roic: number;
    ebit_ev: number;
    accrual_ratio_value: number;
    accrual_quality: string;
  };
}

interface ScreeningResult {
  symbol: string;
  company_name: string;
  f_score: number;
  z_score: number;
  roic: number;
  ebit_ev: number;
  accrual_ratio: number;
  combined_score: number;
  rank: number;
  market_cap: number;
  current_price: number;
  f_score_details: string[];
  z_score_risk: string;
  accrual_quality: string;
  passes_all_filters: boolean;
}

// API_URL should NOT include /api suffix - we add it in the endpoints
const API_URL = process.env.REACT_APP_API_URL?.replace(/\/api$/, '') || 'http://localhost:8000';

const FundamentalScreening: React.FC = () => {
  const getToken = () => localStorage.getItem('authToken');
  const [activeTab, setActiveTab] = useState(0);
  const [symbol, setSymbol] = useState('');
  const [screeningSymbols, setScreeningSymbols] = useState('');
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<FullAnalysisResult | null>(null);
  const [screeningResults, setScreeningResults] = useState<ScreeningResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    min_f_score: 7,
    min_z_score: 3.0,
    max_accrual_ratio: 5.0,
    auto_universe: false,
    universe_index: 'SP500',
    value_percentile: 0.2,
  });
  const [capitalAllocation, setCapitalAllocation] = useState<number | null>(null);
  const [allocatedStocks, setAllocatedStocks] = useState<any[]>([]);
  const [rebalanceResult, setRebalanceResult] = useState<any>(null);

  const handleAnalyze = async () => {
    if (!symbol.trim()) {
      setError('Please enter a symbol');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const token = getToken();
      if (!token) {
        setError('Authentication required. Please login.');
        setLoading(false);
        return;
      }

      const url = `${API_URL}/api/fundamental/full-analysis/${symbol}`;
      console.log('Fetching:', url);
      console.log('Token present:', !!token);
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({}),  // POST requires body
      });
      
      console.log('Response status:', response.status, response.statusText);

      if (!response.ok) {
        let errorMessage = 'Failed to analyze symbol';
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch (e) {
          errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        }
        console.error('API Error:', {
          status: response.status,
          statusText: response.statusText,
          url: `${API_URL}/api/fundamental/full-analysis/${symbol}`,
          message: errorMessage
        });
        throw new Error(errorMessage);
      }

      const data = await response.json();
      setAnalysisResult(data);
    } catch (err: any) {
      setError(err.message || 'Error analyzing symbol');
    } finally {
      setLoading(false);
    }
  };

  const handleScreen = async () => {
    if (!screeningSymbols.trim()) {
      setError('Please enter symbols to screen (comma-separated)');
      return;
    }

    const symbolsList = screeningSymbols
      .split(',')
      .map(s => s.trim().toUpperCase())
      .filter(s => s.length > 0);

    if (symbolsList.length === 0) {
      setError('Please enter at least one valid symbol');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/fundamental/screen/vq-plus`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getToken()}`,
        },
        body: JSON.stringify({
          symbols: filters.auto_universe ? [] : symbolsList,
          min_f_score: filters.min_f_score,
          max_z_score: filters.min_z_score, // Note: API uses max_z_score as min threshold
          max_accrual_ratio: filters.max_accrual_ratio,
          auto_universe: filters.auto_universe,
          universe_index: filters.universe_index,
          value_percentile: filters.value_percentile,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to screen symbols');
      }

      const data = await response.json();
      setScreeningResults(data.results || []);
    } catch (err: any) {
      setError(err.message || 'Error screening symbols');
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'safe':
        return 'success';
      case 'moderate':
        return 'warning';
      case 'high':
        return 'error';
      default:
        return 'default';
    }
  };

  const getQualityColor = (quality: string) => {
    switch (quality) {
      case 'excellent':
      case 'good':
        return 'success';
      case 'acceptable':
        return 'info';
      case 'warning':
        return 'warning';
      case 'danger':
        return 'error';
      default:
        return 'default';
    }
  };

  const getScoreColor = (score: number, max: number) => {
    const percentage = (score / max) * 100;
    if (percentage >= 80) return 'success';
    if (percentage >= 60) return 'info';
    if (percentage >= 40) return 'warning';
    return 'error';
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom sx={{ mb: 3, fontWeight: 'bold' }}>
        <Assessment sx={{ mr: 1, verticalAlign: 'middle' }} />
        Fundamental Screening & Analysis
      </Typography>

      <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
        <Tab label="Single Symbol Analysis" />
        <Tab label="VQ+ Strategy Screening" />
        <Tab label="Backtest Strategy" />
      </Tabs>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Single Symbol Analysis Tab */}
      {activeTab === 0 && (
        <Box>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '2fr 1fr' }, gap: 2, alignItems: 'center' }}>
              <TextField
                fullWidth
                label="Stock Symbol"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                placeholder="e.g., AAPL, TSLA, MSFT"
                onKeyPress={(e) => e.key === 'Enter' && handleAnalyze()}
              />
              <Button
                fullWidth
                variant="contained"
                size="large"
                onClick={handleAnalyze}
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} /> : <Search />}
              >
                Analyze
              </Button>
            </Box>
          </Paper>

          {analysisResult && (
            <Box>
              {/* Summary Card */}
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h5" gutterBottom>
                    {analysisResult.symbol} - {analysisResult.fundamental_data.company_name}
                  </Typography>
                  <Divider sx={{ my: 2 }} />
                  <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, gap: 2 }}>
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        F-Score
                      </Typography>
                      <Chip
                        label={`${analysisResult.summary.f_score_value}/9`}
                        color={getScoreColor(analysisResult.summary.f_score_value, 9) as any}
                        sx={{ mt: 1 }}
                      />
                    </Box>
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Z-Score
                      </Typography>
                      <Chip
                        label={analysisResult.summary.z_score_value.toFixed(2)}
                        color={getRiskColor(analysisResult.summary.z_score_risk) as any}
                        sx={{ mt: 1 }}
                      />
                    </Box>
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        ROIC
                      </Typography>
                      <Typography variant="h6" color={analysisResult.summary.roic > 0 ? 'success.main' : 'error.main'}>
                        {analysisResult.summary.roic.toFixed(2)}%
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Recommendation
                      </Typography>
                      <Chip
                        label={analysisResult.overall_recommendation}
                        color={analysisResult.passes_vq_plus_filters ? 'success' : 'warning'}
                        sx={{ mt: 1 }}
                      />
                    </Box>
                  </Box>
                </CardContent>
              </Card>

              {/* F-Score Details */}
              <Accordion defaultExpanded>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="h6">
                    Piotroski F-Score: {analysisResult.f_score.score}/9
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {analysisResult.f_score.interpretation}
                  </Typography>
                  {analysisResult.f_score.breakdown && Object.keys(analysisResult.f_score.breakdown).length > 0 && (
                    <Box sx={{ display: 'grid', gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(3, 1fr)' }, gap: 2, mb: 2 }}>
                      {Object.entries(analysisResult.f_score.breakdown).map(([key, value]) => (
                        <Box key={key}>
                          <Typography variant="body2" color="text.secondary">
                            {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </Typography>
                          <Chip
                            label={value === 1 ? '✓' : '✗'}
                            color={value === 1 ? 'success' : 'default'}
                            size="small"
                            sx={{ mt: 0.5 }}
                          />
                        </Box>
                      ))}
                    </Box>
                  )}
                  <Box sx={{ mb: 2 }}>
                    <LinearProgress
                      variant="determinate"
                      value={(analysisResult.f_score.score / analysisResult.f_score.max_score) * 100}
                      color={getScoreColor(analysisResult.f_score.score, analysisResult.f_score.max_score) as any}
                      sx={{ height: 10, borderRadius: 5 }}
                    />
                  </Box>
                  <Box>
                    {analysisResult.f_score.details && analysisResult.f_score.details.map((detail, idx) => (
                      <Typography key={idx} variant="body2" sx={{ mb: 1 }}>
                        {detail}
                      </Typography>
                    ))}
                  </Box>
                </AccordionDetails>
              </Accordion>

              {/* Z-Score Details */}
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="h6">
                    Altman Z-Score: {analysisResult.z_score.z_score.toFixed(2)} ({analysisResult.z_score.risk_level.toUpperCase()})
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {analysisResult.z_score.interpretation}
                  </Typography>
                  <Box sx={{ display: 'grid', gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(3, 1fr)' }, gap: 2 }}>
                    {Object.entries(analysisResult.z_score.components).map(([key, value]) => (
                      <Box key={key}>
                        <Typography variant="body2" color="text.secondary">
                          Component {key}
                        </Typography>
                        <Typography variant="h6">{value.toFixed(4)}</Typography>
                      </Box>
                    ))}
                  </Box>
                  <Chip
                    label={analysisResult.z_score.recommendation}
                    color={getRiskColor(analysisResult.z_score.risk_level) as any}
                    sx={{ mt: 2 }}
                  />
                </AccordionDetails>
              </Accordion>

              {/* Magic Formula Details */}
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="h6">
                    Magic Formula: ROIC {analysisResult.magic_formula.roic.toFixed(2)}%, EBIT/EV {analysisResult.magic_formula.ebit_ev.toFixed(2)}%
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)' }, gap: 2 }}>
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Return on Invested Capital (ROIC)
                      </Typography>
                      <Typography variant="h5" color={analysisResult.magic_formula.roic > 0 ? 'success.main' : 'error.main'}>
                        {analysisResult.magic_formula.roic.toFixed(2)}%
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Earnings Yield (EBIT/EV)
                      </Typography>
                      <Typography variant="h5" color={analysisResult.magic_formula.ebit_ev > 0 ? 'success.main' : 'error.main'}>
                        {analysisResult.magic_formula.ebit_ev.toFixed(2)}%
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Current Price
                      </Typography>
                      <Typography variant="h6">${analysisResult.magic_formula.current_price.toFixed(2)}</Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Enterprise Value
                      </Typography>
                      <Typography variant="h6">${(analysisResult.magic_formula.enterprise_value / 1e9).toFixed(2)}B</Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Invested Capital
                      </Typography>
                      <Typography variant="h6">${(analysisResult.magic_formula.invested_capital / 1e9).toFixed(2)}B</Typography>
                    </Box>
                  </Box>
                </AccordionDetails>
              </Accordion>

              {/* Accrual Ratio Details */}
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="h6">
                    Accrual Ratio: {analysisResult.accrual_ratio.accrual_ratio.toFixed(2)}% ({analysisResult.accrual_ratio.quality_flag.toUpperCase()})
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {analysisResult.accrual_ratio.interpretation}
                  </Typography>
                  <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' }, gap: 2 }}>
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Accrual Ratio
                      </Typography>
                      <Typography variant="h6">{analysisResult.accrual_ratio.accrual_ratio.toFixed(2)}%</Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Net Income
                      </Typography>
                      <Typography variant="h6">${(analysisResult.accrual_ratio.net_income / 1e6).toFixed(2)}M</Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Operating Cash Flow
                      </Typography>
                      <Typography variant="h6">${(analysisResult.accrual_ratio.operating_cash_flow / 1e6).toFixed(2)}M</Typography>
                    </Box>
                  </Box>
                  <Chip
                    label={analysisResult.accrual_ratio.recommendation}
                    color={getQualityColor(analysisResult.accrual_ratio.quality_flag) as any}
                    sx={{ mt: 2 }}
                  />
                </AccordionDetails>
              </Accordion>
            </Box>
          )}
        </Box>
      )}

      {/* VQ+ Strategy Screening Tab */}
      {activeTab === 1 && (
        <Box>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              <FilterList sx={{ mr: 1, verticalAlign: 'middle' }} />
              Screening Filters
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' }, gap: 2, mb: 3 }}>
              <TextField
                fullWidth
                label="Min F-Score"
                type="number"
                value={filters.min_f_score}
                onChange={(e) => setFilters({ ...filters, min_f_score: parseInt(e.target.value) || 7 })}
                inputProps={{ min: 0, max: 9 }}
              />
              <TextField
                fullWidth
                label="Min Z-Score"
                type="number"
                value={filters.min_z_score}
                onChange={(e) => setFilters({ ...filters, min_z_score: parseFloat(e.target.value) || 3.0 })}
                inputProps={{ min: 0, step: 0.1 }}
              />
              <TextField
                fullWidth
                label="Max Accrual Ratio"
                type="number"
                value={filters.max_accrual_ratio}
                onChange={(e) => setFilters({ ...filters, max_accrual_ratio: parseFloat(e.target.value) || 5.0 })}
                inputProps={{ min: 0, step: 0.1 }}
              />
            </Box>
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'auto' }, gap: 2, mb: 2, alignItems: 'center' }}>
              <FormControl>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={filters.auto_universe}
                      onChange={(e) => setFilters({ ...filters, auto_universe: e.target.checked })}
                    />
                  }
                  label="Auto-select universe (rank by EBIT/EV)"
                />
              </FormControl>
            </Box>
            {filters.auto_universe && (
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)' }, gap: 2, mb: 3 }}>
                <TextField
                  fullWidth
                  select
                  label="Index"
                  value={filters.universe_index}
                  onChange={(e) => setFilters({ ...filters, universe_index: e.target.value })}
                  SelectProps={{ native: true }}
                >
                  <option value="SP500">S&P 500</option>
                  <option value="RUSSELL2000">Russell 2000</option>
                </TextField>
                <TextField
                  fullWidth
                  label="Value Percentile"
                  type="number"
                  value={filters.value_percentile}
                  onChange={(e) => setFilters({ ...filters, value_percentile: parseFloat(e.target.value) || 0.2 })}
                  inputProps={{ min: 0.1, max: 0.5, step: 0.1 }}
                  helperText="0.2 = bottom 20% (highest EBIT/EV)"
                />
              </Box>
            )}
            {!filters.auto_universe && (
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '2fr 1fr' }, gap: 2, mb: 3, alignItems: 'center' }}>
                <TextField
                  fullWidth
                  label="Symbols to Screen (comma-separated)"
                  value={screeningSymbols}
                  onChange={(e) => setScreeningSymbols(e.target.value.toUpperCase())}
                  placeholder="e.g., AAPL, TSLA, MSFT, GOOGL, AMZN"
                  multiline
                  rows={3}
                />
                <Button
                  fullWidth
                  variant="contained"
                  size="large"
                  onClick={handleScreen}
                  disabled={loading}
                  startIcon={loading ? <CircularProgress size={20} /> : <Search />}
                >
                  Screen Stocks
                </Button>
              </Box>
            )}
            {filters.auto_universe && (
              <Button
                fullWidth
                variant="contained"
                size="large"
                onClick={handleScreen}
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} /> : <Search />}
                sx={{ mb: 2 }}
              >
                Screen Stocks
              </Button>
            )}
          </Paper>

          {screeningResults.length > 0 && (
            <Box>
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Screening Results ({screeningResults.length} stocks passed filters)
                  </Typography>
                  
                  {/* Capital Allocation Section */}
                  <Box sx={{ mt: 3, mb: 2 }}>
                    <Typography variant="subtitle1" gutterBottom>
                      Capital Allocation (Equal Weights)
                    </Typography>
                    <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr auto' }, gap: 2, alignItems: 'center' }}>
                      <TextField
                        fullWidth
                        label="Total Capital ($)"
                        type="number"
                        value={capitalAllocation || ''}
                        onChange={(e) => setCapitalAllocation(parseFloat(e.target.value) || null)}
                        InputProps={{ startAdornment: <Typography sx={{ mr: 1 }}>$</Typography> }}
                      />
                      <Button
                        variant="outlined"
                        onClick={async () => {
                          if (!capitalAllocation || capitalAllocation <= 0) {
                            setError('Please enter a valid capital amount');
                            return;
                          }
                          try {
                            const response = await fetch(`${API_URL}/api/fundamental/allocate-capital`, {
                              method: 'POST',
                              headers: {
                                'Content-Type': 'application/json',
                                'Authorization': `Bearer ${getToken()}`,
                              },
                              body: JSON.stringify({
                                screened_stocks: screeningResults,
                                total_capital: capitalAllocation,
                                method: 'equal_weights',
                              }),
                            });
                            if (!response.ok) throw new Error('Failed to allocate capital');
                            const data = await response.json();
                            setAllocatedStocks(data.allocated_stocks || []);
                          } catch (err: any) {
                            setError(err.message || 'Error allocating capital');
                          }
                        }}
                        disabled={!capitalAllocation || capitalAllocation <= 0}
                      >
                        Allocate Capital
                      </Button>
                    </Box>
                  </Box>
                  
                  {allocatedStocks.length > 0 && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="body2" color="text.secondary">
                        Allocation per stock: ${((capitalAllocation || 0) / allocatedStocks.length).toFixed(2)}
                      </Typography>
                    </Box>
                  )}
                </CardContent>
              </Card>
              
              <Card>
                <CardContent>
                  <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Rank</TableCell>
                        <TableCell>Symbol</TableCell>
                        <TableCell>Company</TableCell>
                        <TableCell align="right">F-Score</TableCell>
                        <TableCell align="right">Z-Score</TableCell>
                        <TableCell align="right">ROIC (%)</TableCell>
                        <TableCell align="right">EBIT/EV (%)</TableCell>
                        <TableCell align="right">Accrual Ratio (%)</TableCell>
                        <TableCell align="right">Combined Score</TableCell>
                        <TableCell align="right">Price</TableCell>
                        <TableCell align="right">Market Cap</TableCell>
                        {allocatedStocks.length > 0 && (
                          <>
                            <TableCell align="right">Allocation ($)</TableCell>
                            <TableCell align="right">Shares to Buy</TableCell>
                          </>
                        )}
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {(allocatedStocks.length > 0 ? allocatedStocks : screeningResults).map((result) => (
                        <TableRow key={result.symbol} hover>
                          <TableCell>
                            <Chip label={`#${result.rank}`} color="primary" size="small" />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" fontWeight="bold">
                              {result.symbol}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                              {result.company_name}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Chip
                              label={`${result.f_score}/9`}
                              color={getScoreColor(result.f_score, 9) as any}
                              size="small"
                            />
                          </TableCell>
                          <TableCell align="right">
                            <Chip
                              label={result.z_score.toFixed(2)}
                              color={getRiskColor(result.z_score_risk) as any}
                              size="small"
                            />
                          </TableCell>
                          <TableCell align="right">
                            <Typography
                              variant="body2"
                              color={result.roic > 0 ? 'success.main' : 'error.main'}
                            >
                              {result.roic.toFixed(2)}%
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography
                              variant="body2"
                              color={result.ebit_ev > 0 ? 'success.main' : 'error.main'}
                            >
                              {result.ebit_ev.toFixed(2)}%
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Chip
                              label={`${result.accrual_ratio.toFixed(2)}%`}
                              color={getQualityColor(result.accrual_quality) as any}
                              size="small"
                            />
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2" fontWeight="bold">
                              {result.combined_score.toFixed(2)}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2">
                              ${result.current_price.toFixed(2)}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2">
                              ${(result.market_cap / 1e9).toFixed(2)}B
                            </Typography>
                          </TableCell>
                          {allocatedStocks.length > 0 && (
                            <>
                              <TableCell align="right">
                                <Typography variant="body2" fontWeight="bold">
                                  ${result.allocation_amount?.toFixed(2) || 'N/A'}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {result.allocation_percent?.toFixed(2) || '0'}%
                                </Typography>
                              </TableCell>
                              <TableCell align="right">
                                <Typography variant="body2">
                                  {result.shares_to_buy?.toFixed(2) || 'N/A'}
                                </Typography>
                              </TableCell>
                            </>
                          )}
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

      {/* Backtest Strategy Tab */}
      {activeTab === 2 && (
        <BacktestTab 
          getToken={getToken}
          loading={loading}
          setLoading={setLoading}
          error={error}
          setError={setError}
        />
      )}
    </Container>
  );
};

// Backtest Tab Component
interface BacktestTabProps {
  getToken: () => string | null;
  loading: boolean;
  setLoading: (loading: boolean) => void;
  error: string | null;
  setError: (error: string | null) => void;
}

interface BacktestResult {
  status: string;
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
  trade_history?: Array<{
    date: string;
    action: string;
    symbol: string;
    price: number;
    shares: number;
    value: number;
    return_pct?: number;
    profit?: number;
    reason?: string;
  }>;
  portfolio_compositions?: Array<{
    date: string;
    positions: Array<{
      symbol: string;
      shares: number;
      entry_price: number;
      current_price: number;
      value: number;
      return_pct: number;
    }>;
    cash: number;
    total_value: number;
  }>;
  rebalance_dates?: string[];
  parameters?: {
    rebalance_frequency: string;
    max_positions: number;
    min_f_score: number;
    max_z_score: number;
    max_accrual_ratio: number;
  };
  error?: string;
}

const BacktestTab: React.FC<BacktestTabProps> = ({ getToken, loading, setLoading, error, setError }) => {
  const [symbols, setSymbols] = useState('AAPL,MSFT,GOOGL,AMZN,NVDA');
  const [startDate, setStartDate] = useState(() => {
    const date = new Date();
    date.setFullYear(date.getFullYear() - 1);
    return date.toISOString().split('T')[0];
  });
  const [endDate, setEndDate] = useState(() => new Date().toISOString().split('T')[0]);
  const [initialCapital, setInitialCapital] = useState(100000);
  const [rebalanceFrequency, setRebalanceFrequency] = useState<'quarterly' | 'yearly'>('quarterly');
  const [maxPositions, setMaxPositions] = useState(10);
  const [backtestFilters, setBacktestFilters] = useState({
    min_f_score: 6,
    max_z_score: 2.0,
    max_accrual_ratio: 10.0,
  });
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);

  const handleRunBacktest = async () => {
    const symbolsList = symbols
      .split(',')
      .map(s => s.trim().toUpperCase())
      .filter(s => s.length > 0);

    if (symbolsList.length === 0) {
      setError('Please enter at least one symbol');
      return;
    }

    setLoading(true);
    setError(null);
    setBacktestResult(null);

    try {
      const token = getToken();
      if (!token) {
        setError('Authentication required');
        return;
      }

      const response = await fetch(`${API_URL}/api/fundamental/backtest/vq-plus`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          symbols: symbolsList,
          start_date: startDate,
          end_date: endDate,
          initial_capital: initialCapital,
          rebalance_frequency: rebalanceFrequency,
          max_positions: maxPositions,
          min_f_score: backtestFilters.min_f_score,
          max_z_score: backtestFilters.max_z_score,
          max_accrual_ratio: backtestFilters.max_accrual_ratio,
          auto_universe: false,
          universe_index: 'SP500',
          value_percentile: 0.2,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Backtest failed: ${response.statusText}`);
      }

      const data = await response.json();
      setBacktestResult(data);
    } catch (err: any) {
      setError(err.message || 'Error running backtest');
      setBacktestResult({ status: 'error', error: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          VQ+ Strategy Backtest Configuration
        </Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 2, mt: 2 }}>
          <TextField
            fullWidth
            label="Symbols (comma-separated)"
            value={symbols}
            onChange={(e) => setSymbols(e.target.value)}
            placeholder="AAPL, MSFT, GOOGL"
            helperText="Enter stock symbols to test"
          />
          <TextField
            fullWidth
            type="date"
            label="Start Date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            fullWidth
            type="date"
            label="End Date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            fullWidth
            type="number"
            label="Initial Capital ($)"
            value={initialCapital}
            onChange={(e) => setInitialCapital(Number(e.target.value))}
            inputProps={{ min: 1000, step: 1000 }}
          />
          <FormControl fullWidth>
            <Typography variant="body2" sx={{ mb: 1 }}>Rebalance Frequency</Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant={rebalanceFrequency === 'quarterly' ? 'contained' : 'outlined'}
                onClick={() => setRebalanceFrequency('quarterly')}
                fullWidth
              >
                Quarterly
              </Button>
              <Button
                variant={rebalanceFrequency === 'yearly' ? 'contained' : 'outlined'}
                onClick={() => setRebalanceFrequency('yearly')}
                fullWidth
              >
                Yearly
              </Button>
            </Box>
          </FormControl>
          <TextField
            fullWidth
            type="number"
            label="Max Positions"
            value={maxPositions}
            onChange={(e) => setMaxPositions(Number(e.target.value))}
            inputProps={{ min: 1, max: 50 }}
            helperText="Maximum number of positions in portfolio"
          />
          <TextField
            fullWidth
            type="number"
            label="Min F-Score"
            value={backtestFilters.min_f_score}
            onChange={(e) => setBacktestFilters({ ...backtestFilters, min_f_score: Number(e.target.value) })}
            inputProps={{ min: 0, max: 9 }}
          />
          <TextField
            fullWidth
            type="number"
            label="Min Z-Score"
            value={backtestFilters.max_z_score}
            onChange={(e) => setBacktestFilters({ ...backtestFilters, max_z_score: Number(e.target.value) })}
            inputProps={{ min: 0, step: 0.1 }}
            helperText="Minimum Z-Score threshold"
          />
          <TextField
            fullWidth
            type="number"
            label="Max Accrual Ratio (%)"
            value={backtestFilters.max_accrual_ratio}
            onChange={(e) => setBacktestFilters({ ...backtestFilters, max_accrual_ratio: Number(e.target.value) })}
            inputProps={{ min: 0, step: 0.1 }}
          />
        </Box>
        <Box sx={{ mt: 3 }}>
          <Button
            variant="contained"
            size="large"
            fullWidth
            onClick={handleRunBacktest}
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : <TrendingUp />}
          >
            {loading ? 'Running Backtest...' : 'Run Backtest'}
          </Button>
        </Box>
      </Paper>

      {backtestResult && (
        <Box>
          {backtestResult.status === 'error' ? (
            <Alert severity="error" sx={{ mb: 3 }}>
              {backtestResult.error || 'Backtest failed'}
            </Alert>
          ) : (
            <>
              {/* Performance Metrics */}
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, gap: 2, mb: 3 }}>
                <Card>
                  <CardContent>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Total Return
                    </Typography>
                    <Typography variant="h4" color={backtestResult.total_return && backtestResult.total_return >= 0 ? 'success.main' : 'error.main'}>
                      {backtestResult.total_return?.toFixed(2) || '0.00'}%
                    </Typography>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      CAGR
                    </Typography>
                    <Typography variant="h4" color={backtestResult.cagr && backtestResult.cagr >= 0 ? 'success.main' : 'error.main'}>
                      {backtestResult.cagr?.toFixed(2) || '0.00'}%
                    </Typography>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Sharpe Ratio
                    </Typography>
                    <Typography variant="h4">
                      {backtestResult.sharpe_ratio?.toFixed(3) || '0.000'}
                    </Typography>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Max Drawdown
                    </Typography>
                    <Typography variant="h4" color="error.main">
                      {backtestResult.max_drawdown?.toFixed(2) || '0.00'}%
                    </Typography>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Win Rate
                    </Typography>
                    <Typography variant="h4">
                      {backtestResult.win_rate?.toFixed(2) || '0.00'}%
                    </Typography>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Profit Factor
                    </Typography>
                    <Typography variant="h4" color={backtestResult.profit_factor && backtestResult.profit_factor > 1 ? 'success.main' : 'error.main'}>
                      {backtestResult.profit_factor?.toFixed(2) || '0.00'}
                    </Typography>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Total Trades
                    </Typography>
                    <Typography variant="h4">
                      {backtestResult.total_trades || 0}
                    </Typography>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Final Value
                    </Typography>
                    <Typography variant="h4">
                      ${backtestResult.final_value?.toLocaleString(undefined, { maximumFractionDigits: 2 }) || '0.00'}
                    </Typography>
                  </CardContent>
                </Card>
              </Box>

              {/* Equity Curve */}
              {backtestResult.equity_curve && backtestResult.equity_curve.length > 0 && (
                <Card sx={{ mb: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Equity Curve
                    </Typography>
                    <Box sx={{ mt: 2, p: 2, bgcolor: 'background.default', borderRadius: 1, minHeight: 300 }}>
                      <Typography variant="body2" color="text.secondary">
                        Equity curve visualization would go here
                      </Typography>
                      <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                        Data points: {backtestResult.equity_curve.length}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" display="block">
                        Start: ${backtestResult.equity_curve[0]?.value.toLocaleString()} | 
                        End: ${backtestResult.equity_curve[backtestResult.equity_curve.length - 1]?.value.toLocaleString()}
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              )}

              {/* Trade History */}
              {backtestResult.trade_history && backtestResult.trade_history.length > 0 && (
                <Card sx={{ mb: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Trade History ({backtestResult.trade_history.length} trades)
                    </Typography>
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Date</TableCell>
                            <TableCell>Action</TableCell>
                            <TableCell>Symbol</TableCell>
                            <TableCell align="right">Price</TableCell>
                            <TableCell align="right">Shares</TableCell>
                            <TableCell align="right">Value</TableCell>
                            <TableCell align="right">Return %</TableCell>
                            <TableCell>Reason</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {backtestResult.trade_history.slice(0, 50).map((trade, idx) => (
                            <TableRow key={idx}>
                              <TableCell>{trade.date}</TableCell>
                              <TableCell>
                                <Chip
                                  label={trade.action.toUpperCase()}
                                  color={trade.action === 'buy' ? 'primary' : 'secondary'}
                                  size="small"
                                />
                              </TableCell>
                              <TableCell>{trade.symbol}</TableCell>
                              <TableCell align="right">${trade.price.toFixed(2)}</TableCell>
                              <TableCell align="right">{trade.shares.toFixed(4)}</TableCell>
                              <TableCell align="right">${trade.value.toLocaleString(undefined, { maximumFractionDigits: 2 })}</TableCell>
                              <TableCell align="right">
                                {trade.return_pct !== undefined && (
                                  <Typography
                                    variant="body2"
                                    color={trade.return_pct >= 0 ? 'success.main' : 'error.main'}
                                  >
                                    {trade.return_pct >= 0 ? '+' : ''}{trade.return_pct.toFixed(2)}%
                                  </Typography>
                                )}
                              </TableCell>
                              <TableCell>
                                <Typography variant="caption" color="text.secondary">
                                  {trade.reason || 'N/A'}
                                </Typography>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                    {backtestResult.trade_history.length > 50 && (
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                        Showing first 50 of {backtestResult.trade_history.length} trades
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* Portfolio Compositions */}
              {backtestResult.portfolio_compositions && backtestResult.portfolio_compositions.length > 0 && (
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Portfolio Compositions
                    </Typography>
                    {backtestResult.portfolio_compositions.slice(0, 5).map((composition, idx) => (
                      <Accordion key={idx} sx={{ mb: 1 }}>
                        <AccordionSummary expandIcon={<ExpandMore />}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', mr: 2 }}>
                            <Typography variant="body1" fontWeight="bold">
                              {composition.date}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              Total Value: ${composition.total_value.toLocaleString(undefined, { maximumFractionDigits: 2 })} | 
                              Positions: {composition.positions.length} | 
                              Cash: ${composition.cash.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                            </Typography>
                          </Box>
                        </AccordionSummary>
                        <AccordionDetails>
                          {composition.positions.length > 0 ? (
                            <TableContainer>
                              <Table size="small">
                                <TableHead>
                                  <TableRow>
                                    <TableCell>Symbol</TableCell>
                                    <TableCell align="right">Shares</TableCell>
                                    <TableCell align="right">Entry Price</TableCell>
                                    <TableCell align="right">Current Price</TableCell>
                                    <TableCell align="right">Value</TableCell>
                                    <TableCell align="right">Return %</TableCell>
                                  </TableRow>
                                </TableHead>
                                <TableBody>
                                  {composition.positions.map((pos) => (
                                    <TableRow key={pos.symbol}>
                                      <TableCell>{pos.symbol}</TableCell>
                                      <TableCell align="right">{pos.shares.toFixed(4)}</TableCell>
                                      <TableCell align="right">${pos.entry_price.toFixed(2)}</TableCell>
                                      <TableCell align="right">${pos.current_price.toFixed(2)}</TableCell>
                                      <TableCell align="right">${pos.value.toLocaleString(undefined, { maximumFractionDigits: 2 })}</TableCell>
                                      <TableCell align="right">
                                        <Typography
                                          variant="body2"
                                          color={pos.return_pct >= 0 ? 'success.main' : 'error.main'}
                                        >
                                          {pos.return_pct >= 0 ? '+' : ''}{pos.return_pct.toFixed(2)}%
                                        </Typography>
                                      </TableCell>
                                    </TableRow>
                                  ))}
                                </TableBody>
                              </Table>
                            </TableContainer>
                          ) : (
                            <Typography variant="body2" color="text.secondary">
                              No positions held
                            </Typography>
                          )}
                        </AccordionDetails>
                      </Accordion>
                    ))}
                    {backtestResult.portfolio_compositions.length > 5 && (
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                        Showing first 5 of {backtestResult.portfolio_compositions.length} rebalances
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </Box>
      )}
    </Box>
  );
};

export default FundamentalScreening;

