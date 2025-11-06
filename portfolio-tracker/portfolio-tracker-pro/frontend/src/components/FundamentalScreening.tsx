import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  TextField,
  Button,
  Grid,
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
import { useAuth } from '../contexts/AuthContext';

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

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

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
  });

  const handleAnalyze = async () => {
    if (!symbol.trim()) {
      setError('Please enter a symbol');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/fundamental/full-analysis/${symbol}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getToken()}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to analyze symbol');
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
          symbols: symbolsList,
          min_f_score: filters.min_f_score,
          max_z_score: filters.min_z_score, // Note: API uses max_z_score as min threshold
          max_accrual_ratio: filters.max_accrual_ratio,
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
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} sm={8}>
                <TextField
                  fullWidth
                  label="Stock Symbol"
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                  placeholder="e.g., AAPL, TSLA, MSFT"
                  onKeyPress={(e) => e.key === 'Enter' && handleAnalyze()}
                />
              </Grid>
              <Grid item xs={12} sm={4}>
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
              </Grid>
            </Grid>
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
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6} md={3}>
                      <Typography variant="body2" color="text.secondary">
                        F-Score
                      </Typography>
                      <Chip
                        label={`${analysisResult.summary.f_score_value}/9`}
                        color={getScoreColor(analysisResult.summary.f_score_value, 9) as any}
                        sx={{ mt: 1 }}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Typography variant="body2" color="text.secondary">
                        Z-Score
                      </Typography>
                      <Chip
                        label={analysisResult.summary.z_score_value.toFixed(2)}
                        color={getRiskColor(analysisResult.summary.z_score_risk) as any}
                        sx={{ mt: 1 }}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Typography variant="body2" color="text.secondary">
                        ROIC
                      </Typography>
                      <Typography variant="h6" color={analysisResult.summary.roic > 0 ? 'success.main' : 'error.main'}>
                        {analysisResult.summary.roic.toFixed(2)}%
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Typography variant="body2" color="text.secondary">
                        Recommendation
                      </Typography>
                      <Chip
                        label={analysisResult.overall_recommendation}
                        color={analysisResult.passes_vq_plus_filters ? 'success' : 'warning'}
                        sx={{ mt: 1 }}
                      />
                    </Grid>
                  </Grid>
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
                  <Box sx={{ mb: 2 }}>
                    <LinearProgress
                      variant="determinate"
                      value={(analysisResult.f_score.score / analysisResult.f_score.max_score) * 100}
                      color={getScoreColor(analysisResult.f_score.score, analysisResult.f_score.max_score) as any}
                      sx={{ height: 10, borderRadius: 5 }}
                    />
                  </Box>
                  <Box>
                    {analysisResult.f_score.details.map((detail, idx) => (
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
                  <Grid container spacing={2}>
                    {Object.entries(analysisResult.z_score.components).map(([key, value]) => (
                      <Grid item xs={6} sm={4} key={key}>
                        <Typography variant="body2" color="text.secondary">
                          Component {key}
                        </Typography>
                        <Typography variant="h6">{value.toFixed(4)}</Typography>
                      </Grid>
                    ))}
                  </Grid>
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
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="body2" color="text.secondary">
                        Return on Invested Capital (ROIC)
                      </Typography>
                      <Typography variant="h5" color={analysisResult.magic_formula.roic > 0 ? 'success.main' : 'error.main'}>
                        {analysisResult.magic_formula.roic.toFixed(2)}%
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="body2" color="text.secondary">
                        Earnings Yield (EBIT/EV)
                      </Typography>
                      <Typography variant="h5" color={analysisResult.magic_formula.ebit_ev > 0 ? 'success.main' : 'error.main'}>
                        {analysisResult.magic_formula.ebit_ev.toFixed(2)}%
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Typography variant="body2" color="text.secondary">
                        Current Price
                      </Typography>
                      <Typography variant="h6">${analysisResult.magic_formula.current_price.toFixed(2)}</Typography>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Typography variant="body2" color="text.secondary">
                        Enterprise Value
                      </Typography>
                      <Typography variant="h6">${(analysisResult.magic_formula.enterprise_value / 1e9).toFixed(2)}B</Typography>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Typography variant="body2" color="text.secondary">
                        Invested Capital
                      </Typography>
                      <Typography variant="h6">${(analysisResult.magic_formula.invested_capital / 1e9).toFixed(2)}B</Typography>
                    </Grid>
                  </Grid>
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
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={4}>
                      <Typography variant="body2" color="text.secondary">
                        Accrual Ratio
                      </Typography>
                      <Typography variant="h6">{analysisResult.accrual_ratio.accrual_ratio.toFixed(2)}%</Typography>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Typography variant="body2" color="text.secondary">
                        Net Income
                      </Typography>
                      <Typography variant="h6">${(analysisResult.accrual_ratio.net_income / 1e6).toFixed(2)}M</Typography>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Typography variant="body2" color="text.secondary">
                        Operating Cash Flow
                      </Typography>
                      <Typography variant="h6">${(analysisResult.accrual_ratio.operating_cash_flow / 1e6).toFixed(2)}M</Typography>
                    </Grid>
                  </Grid>
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
            <Grid container spacing={2} sx={{ mb: 3 }}>
              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  label="Min F-Score"
                  type="number"
                  value={filters.min_f_score}
                  onChange={(e) => setFilters({ ...filters, min_f_score: parseInt(e.target.value) || 7 })}
                  inputProps={{ min: 0, max: 9 }}
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  label="Min Z-Score"
                  type="number"
                  value={filters.min_z_score}
                  onChange={(e) => setFilters({ ...filters, min_z_score: parseFloat(e.target.value) || 3.0 })}
                  inputProps={{ min: 0, step: 0.1 }}
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  label="Max Accrual Ratio"
                  type="number"
                  value={filters.max_accrual_ratio}
                  onChange={(e) => setFilters({ ...filters, max_accrual_ratio: parseFloat(e.target.value) || 5.0 })}
                  inputProps={{ min: 0, step: 0.1 }}
                />
              </Grid>
            </Grid>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} sm={8}>
                <TextField
                  fullWidth
                  label="Symbols to Screen (comma-separated)"
                  value={screeningSymbols}
                  onChange={(e) => setScreeningSymbols(e.target.value.toUpperCase())}
                  placeholder="e.g., AAPL, TSLA, MSFT, GOOGL, AMZN"
                  multiline
                  rows={3}
                />
              </Grid>
              <Grid item xs={12} sm={4}>
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
              </Grid>
            </Grid>
          </Paper>

          {screeningResults.length > 0 && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Screening Results ({screeningResults.length} stocks passed filters)
                </Typography>
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
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {screeningResults.map((result) => (
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
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          )}
        </Box>
      )}
    </Container>
  );
};

export default FundamentalScreening;

