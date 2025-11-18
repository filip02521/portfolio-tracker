import React, { useMemo, useState } from 'react';
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
  AlertTitle,
  Stack,
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
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
import { useToast, Toast } from './common/Toast';

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

interface SkippedSymbolInfo {
  symbol: string;
  reason?: string;
  details?: string;
  value?: number;
  threshold?: number;
}

interface DataIssueInfo {
  symbol: string;
  issue: string;
}

interface ScreeningErrorInfo {
  symbol?: string;
  error: string;
}

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

type FilterConfig = {
  min_f_score: number;
  min_z_score: number;
  max_accrual_ratio: number;
  auto_universe: boolean;
  universe_index: string;
  value_percentile: number;
};

type FilterPresetValues = Partial<FilterConfig>;

interface FilterPreset {
  id: string;
  label: string;
  helper: string;
  values: FilterPresetValues;
}

// API_URL should NOT include /api suffix - we add it in the endpoints
const API_URL = process.env.REACT_APP_API_URL?.replace(/\/api$/, '') || 'http://localhost:8000';

interface BenchmarkEntry {
  symbol: string;
  name: string;
  total_return: number;
  annual_volatility: number | null;
  relative_return?: number | null;
  alpha?: number | null;
  beta?: number | null;
  tracking_error?: number | null;
  correlation?: number | null;
}

const FundamentalScreening: React.FC = () => {
  const getToken = () => localStorage.getItem('authToken');
  const [activeTab, setActiveTab] = useState(0);
  const [symbol, setSymbol] = useState('');
  const [screeningSymbols, setScreeningSymbols] = useState('');
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<FullAnalysisResult | null>(null);
  const [screeningResults, setScreeningResults] = useState<ScreeningResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [skippedSymbols, setSkippedSymbols] = useState<SkippedSymbolInfo[]>([]);
  const [dataIssues, setDataIssues] = useState<DataIssueInfo[]>([]);
  const [screeningErrors, setScreeningErrors] = useState<ScreeningErrorInfo[]>([]);
  
  const UNIVERSE_OPTIONS = useMemo(() => (
    [
      { value: 'SP500', label: 'S&P 500 (500 large-cap stocks)' },
      { value: 'DOWJONES', label: 'Dow Jones Industrial Average (30 mega-cap stocks)' },
      { value: 'NASDAQ100', label: 'Nasdaq 100 (top non-financial Nasdaq stocks)' },
      { value: 'RUSSELL2000', label: 'Sample Russell 2000 (small-cap representative)' },
    ]
  ), []);

  const { toast, showToast, hideToast } = useToast();

  const defaultFilterValues = useMemo<FilterConfig>(() => ({
    min_f_score: 7,
    min_z_score: 3.0,
    max_accrual_ratio: 5.0,
    auto_universe: false,
    universe_index: UNIVERSE_OPTIONS[0].value,
    value_percentile: 0.2,
  }), [UNIVERSE_OPTIONS]);

  const [filters, setFilters] = useState<FilterConfig>(defaultFilterValues);
  const [activePreset, setActivePreset] = useState<string | null>(null);

  const filterPresets = useMemo<FilterPreset[]>(() => [
    {
      id: 'quality',
      label: 'Quality Bias',
      helper: 'High F-score, resilient balance sheet',
      values: { min_f_score: 8, min_z_score: 3.5, max_accrual_ratio: 4.0, auto_universe: false },
    },
    {
      id: 'balanced',
      label: 'Balanced Core',
      helper: 'Blend of value and safety',
      values: { min_f_score: 7, min_z_score: 3.0, max_accrual_ratio: 5.0, auto_universe: false },
    },
    {
      id: 'value',
      label: 'Deep Value',
      helper: 'Focus on cheapest quintile',
      values: { min_f_score: 6, min_z_score: 2.5, max_accrual_ratio: 6.0, auto_universe: true, value_percentile: 0.15 },
    },
  ], []);

  const [capitalAllocation, setCapitalAllocation] = useState<number | null>(null);
  const [allocatedStocks, setAllocatedStocks] = useState<any[]>([]);
  const [rebalanceScenarios, setRebalanceScenarios] = useState<any[]>([]);
  const [rebalanceLoading, setRebalanceLoading] = useState(false);
  const [rebalanceError, setRebalanceError] = useState<string | null>(null);

  const groupedDataIssues = useMemo(() => {
    const grouped: Record<string, string[]> = {};
    dataIssues.forEach(({ symbol: issueSymbol, issue }) => {
      if (!issueSymbol || !issue) {
        return;
      }
      if (!grouped[issueSymbol]) {
        grouped[issueSymbol] = [];
      }
      if (!grouped[issueSymbol].includes(issue)) {
        grouped[issueSymbol].push(issue);
      }
    });
    return grouped;
  }, [dataIssues]);

  const skippedReasonLabel = (reason?: string) => {
    switch (reason) {
      case 'no_fundamental_data':
        return 'No fundamental data returned';
      case 'invalid_fundamentals':
        return 'Failed fundamental sanity checks';
      case 'f_score_below_threshold':
        return 'F-Score below minimum threshold';
      case 'z_score_below_threshold':
        return 'Z-Score below minimum threshold';
      case 'accrual_ratio_above_threshold':
        return 'Accrual ratio above limit';
      default:
        return reason || 'Filter criteria not met';
    }
  };

  const applyFilterPreset = (presetId: string) => {
    const preset = filterPresets.find((p) => p.id === presetId);
    if (!preset) {
      return;
    }
    setFilters((prev) => ({
      ...prev,
      ...preset.values,
      auto_universe: preset.values.auto_universe ?? false,
      universe_index: preset.values.universe_index ?? prev.universe_index,
    }));
    setActivePreset(presetId);
    showToast(`${preset.label} preset applied`, 'info');
  };

  const resetFilters = () => {
    setFilters({ ...defaultFilterValues });
    setActivePreset(null);
    showToast('Filters reset to defaults', 'info');
  };

  const handleAnalyze = async () => {
    if (!symbol.trim()) {
      setError('Please enter a symbol');
      showToast('Please enter a symbol to analyze', 'warning');
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
      showToast(`Analysis updated for ${data.symbol || symbol.toUpperCase()}`, 'success');
    } catch (err: any) {
      setError(err.message || 'Error analyzing symbol');
      showToast(err.message || 'Error analyzing symbol', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleScreen = async () => {
    if (!filters.auto_universe && !screeningSymbols.trim()) {
      setError('Please enter symbols to screen (comma-separated)');
      showToast('Provide symbols or enable auto universe before screening', 'warning');
      return;
    }

    const symbolsList = filters.auto_universe
      ? []
      : screeningSymbols
          .split(',')
          .map(s => s.trim().toUpperCase())
          .filter(s => s.length > 0);

    if (!filters.auto_universe && symbolsList.length === 0) {
      setError('Please enter at least one valid symbol');
      showToast('Need at least one valid symbol', 'warning');
      return;
    }

    setLoading(true);
    setError(null);
    setSkippedSymbols([]);
    setDataIssues([]);
    setScreeningErrors([]);

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
      setSkippedSymbols(data.skipped || []);
      setDataIssues(data.data_issues || []);
      setScreeningErrors(data.errors || []);
      setRebalanceScenarios([]);
      setRebalanceError(null);
      const screenedCount = (data.results || []).length;
      showToast(`Screening completed${screenedCount ? ` • ${screenedCount} matches` : ''}`, 'success');
    } catch (err: any) {
      setError(err.message || 'Error screening symbols');
      showToast(err.message || 'Error screening symbols', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateScenarios = async () => {
    if (!filters.auto_universe && (!screeningSymbols.trim() || screeningResults.length === 0)) {
      setError('Run VQ+ screening before simulating scenarios');
      showToast('Run VQ+ screening before simulating scenarios', 'warning');
      return;
    }
    if (screeningResults.length === 0) {
      setError('No screening results available. Please screen stocks first.');
      showToast('Screen stocks before running simulations', 'warning');
      return;
    }
    if (!capitalAllocation || capitalAllocation <= 0) {
      setError('Please enter a valid capital amount before running simulations.');
      showToast('Enter a valid capital amount before simulations', 'warning');
      return;
    }

    const token = getToken();
    if (!token) {
      setError('Authentication required. Please login.');
      showToast('Login required to simulate scenarios', 'warning');
      return;
    }

    const currentHoldingsMap: Record<string, number> = {};
    if (allocatedStocks && allocatedStocks.length > 0) {
      allocatedStocks.forEach((stock) => {
        if (stock && stock.symbol) {
          const value =
            typeof stock.allocation_amount === 'number'
              ? stock.allocation_amount
              : typeof stock.value === 'number'
              ? stock.value
              : 0;
          if (value > 0) {
            currentHoldingsMap[stock.symbol] = value;
          }
        }
      });
    }

    setRebalanceLoading(true);
    setRebalanceError(null);

    try {
      const response = await fetch(`${API_URL}/api/fundamental/rebalance/simulate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          screened_stocks: screeningResults,
          total_capital: capitalAllocation,
          max_positions_options: [5, 10, 20],
          strategies: ['equal_weight', 'momentum', 'quality'],
          transaction_cost: 0.001,
          current_holdings: currentHoldingsMap,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to simulate rebalance scenarios');
      }

      const data = await response.json();
      setRebalanceScenarios(data.scenarios || []);
      showToast('Rebalance scenarios ready', 'success');
    } catch (err: any) {
      setRebalanceError(err.message || 'Error simulating rebalance scenarios');
      showToast(err.message || 'Error simulating rebalance scenarios', 'error');
    } finally {
      setRebalanceLoading(false);
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
      <Stack spacing={3}>
        <Box component="header">
          <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 'bold' }}>
            <Assessment sx={{ mr: 1, verticalAlign: 'middle' }} />
            Fundamental Screening & Analysis
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Analyze single tickers, run VQ+ screens, and backtest strategies in one place.
          </Typography>
        </Box>

        <Paper>
          <Tabs
            value={activeTab}
            onChange={(e, newValue) => setActiveTab(newValue)}
            aria-label="Fundamental screening sections"
          >
            <Tab label="Single Symbol Analysis" id="fs-tab-0" aria-controls="fs-panel-0" />
            <Tab label="VQ+ Strategy Screening" id="fs-tab-1" aria-controls="fs-panel-1" />
            <Tab label="Backtest Strategy" id="fs-tab-2" aria-controls="fs-panel-2" />
          </Tabs>
        </Paper>

        {error && (
          <Alert severity="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Single Symbol Analysis Tab */}
        {activeTab === 0 && (
          <Box id="fs-panel-0" role="tabpanel" aria-labelledby="fs-tab-0">
            <Typography variant="h5" sx={srOnlyStyles}>
              Single Symbol Analysis
            </Typography>
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
                    <Typography variant="body2">{analysisResult.f_score.details.join(' ')}
                    </Typography>
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
          <Box id="fs-panel-1" role="tabpanel" aria-labelledby="fs-tab-1">
            <Typography variant="h5" sx={srOnlyStyles}>
              VQ+ Strategy Screening
            </Typography>
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
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                    Quick presets
                  </Typography>
                  <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                    {filterPresets.map((preset) => (
                      <Chip
                        key={preset.id}
                        label={preset.label}
                        color={activePreset === preset.id ? 'primary' : 'default'}
                        variant={activePreset === preset.id ? 'filled' : 'outlined'}
                        onClick={() => applyFilterPreset(preset.id)}
                        aria-label={`${preset.label} preset`}
                      />
                    ))}
                    <Chip
                      label="Reset"
                      variant="outlined"
                      onClick={resetFilters}
                      aria-label="Reset filters"
                    />
                  </Stack>
                  {activePreset && (
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                      {filterPresets.find((preset) => preset.id === activePreset)?.helper}
                    </Typography>
                  )}
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
                      {UNIVERSE_OPTIONS.map(option => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
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
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 3 }}>
                    <Typography variant="body2" color="text.secondary">
                      Screening will automatically pull the full index constituents and rank by EBIT/EV before applying filters.
                    </Typography>
                    <Button
                      fullWidth
                      variant="contained"
                      size="large"
                      onClick={handleScreen}
                      disabled={loading}
                      startIcon={loading ? <CircularProgress size={20} /> : <Search />}
                    >
                      Screen {UNIVERSE_OPTIONS.find(opt => opt.value === filters.universe_index)?.label.split('(')[0].trim() || 'Index'}
                    </Button>
                  </Box>
                )}
              </Paper>

              {!loading && screeningResults.length === 0 && filters.auto_universe && (
                <Alert severity="info" sx={{ mb: 3 }}>
                  No stocks passed the current VQ+ filters for the selected index. Try relaxing F-Score or Accrual Ratio thresholds.
                </Alert>
              )}

              {screeningResults.length > 0 && (
                <Box>
                  {screeningErrors.length > 0 && (
                    <Alert severity="error" sx={{ mb: 3 }}>
                      <AlertTitle>Some symbols failed during screening</AlertTitle>
                      {screeningErrors.map((entry, idx) => (
                        <Typography variant="body2" key={`${entry.symbol || 'unknown'}-${idx}`}>
                          {entry.symbol ? `${entry.symbol}: ` : ''}{entry.error || 'Unknown error'}
                        </Typography>
                      ))}
                    </Alert>
                  )}

                  {skippedSymbols.length > 0 && (
                    <Card sx={{ mb: 3, borderLeft: 4, borderLeftColor: 'warning.main' }}>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Skipped Symbols ({skippedSymbols.length})
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                          These tickers did not pass VQ+ filters or lacked sufficient data. Adjust thresholds to include them.
                        </Typography>
                        <TableContainer>
                          <Table size="small">
                            <TableHead>
                              <TableRow>
                                <TableCell>Symbol</TableCell>
                                <TableCell>Reason</TableCell>
                                <TableCell>Details</TableCell>
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {skippedSymbols.map((entry) => (
                                <TableRow key={entry.symbol}>
                                  <TableCell>
                                    <Typography variant="body2" fontWeight="bold">
                                      {entry.symbol}
                                    </Typography>
                                  </TableCell>
                                  <TableCell>
                                    <Typography variant="body2">
                                      {skippedReasonLabel(entry.reason)}
                                    </Typography>
                                  </TableCell>
                                  <TableCell>
                                    <Typography variant="body2" color="text.secondary">
                                      {entry.details ||
                                        (typeof entry.value === 'number' && typeof entry.threshold === 'number'
                                          ? `Value ${entry.value?.toFixed?.(2) ?? entry.value} vs threshold ${entry.threshold}`
                                          : '—')}
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

                  {dataIssues.length > 0 && (
                    <Card sx={{ mb: 3, borderLeft: 4, borderLeftColor: 'info.main' }}>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Data Warnings
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                          The following symbols passed filters but had partial data (e.g., fallback pricing). Review before allocating capital.
                        </Typography>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                          {Object.entries(groupedDataIssues).map(([symbolKey, issues]) => (
                            <Box key={symbolKey} sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, alignItems: 'center' }}>
                              <Typography variant="body2" fontWeight="bold" sx={{ mr: 1 }}>
                                {symbolKey}
                              </Typography>
                              {issues.map((issue) => (
                                <Chip key={`${symbolKey}-${issue}`} label={issue} size="small" color="warning" variant="outlined" />
                              ))}
                            </Box>
                          ))}
                        </Box>
                      </CardContent>
                    </Card>
                  )}

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
                  
                  <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, gap: 2, mb: 3 }}>
                    <Button
                      variant="outlined"
                      fullWidth
                      onClick={handleSimulateScenarios}
                      disabled={rebalanceLoading}
                    >
                      {rebalanceLoading ? 'Simulating scenarios...' : 'Simulate Rebalance Scenarios'}
                    </Button>
                  </Box>
                  {rebalanceError && (
                    <Alert severity="error" sx={{ mb: 3 }} onClose={() => setRebalanceError(null)}>
                      {rebalanceError}
                    </Alert>
                  )}
                  {rebalanceLoading && <LinearProgress sx={{ mb: 3 }} />}
                  {rebalanceScenarios.length > 0 && (
                    <Card sx={{ mb: 3 }}>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Rebalance Scenario Comparisons
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                          Each scenario highlights target allocations, estimated turnover, and factor-weighted metrics for the selected strategy.
                        </Typography>
                        {rebalanceScenarios.map((scenario, idx) => (
                          <Accordion key={`${scenario.strategy}-${scenario.max_positions}-${idx}`} sx={{ mb: 1 }}>
                            <AccordionSummary expandIcon={<ExpandMore />}>
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', mr: 2 }}>
                                <Typography variant="subtitle1" fontWeight="bold">
                                  {scenario.strategy.replace('_', ' ').toUpperCase()} • {scenario.max_positions} positions
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                  Turnover: {(scenario.turnover * 100).toFixed(2)}% | Est. Cost: ${scenario.transaction_cost?.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                                </Typography>
                              </Box>
                            </AccordionSummary>
                            <AccordionDetails>
                              {scenario.weighted_scores && (
                                <Box sx={{ mb: 2, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                  {Object.entries(scenario.weighted_scores).map(([key, value]) => {
                                    const numericValue = typeof value === 'number' ? value : 0;
                                    return (
                                      <Chip
                                        key={key}
                                        label={`${key.replace('_', ' ').toUpperCase()}: ${numericValue.toFixed(2)}`}
                                        size="small"
                                        color="primary"
                                        variant="outlined"
                                      />
                                    );
                                  })}
                                </Box>
                              )}
                              <TableContainer>
                                <Table size="small">
                                  <TableHead>
                                    <TableRow>
                                      <TableCell>Symbol</TableCell>
                                      <TableCell>Weight %</TableCell>
                                      <TableCell align="right">Target Value</TableCell>
                                      <TableCell align="right">Current Value</TableCell>
                                      <TableCell align="right">Trade Value</TableCell>
                                      <TableCell align="right">Trade Cost</TableCell>
                                      <TableCell align="right">Combined</TableCell>
                                      <TableCell align="right">F-Score</TableCell>
                                      <TableCell align="right">Z-Score</TableCell>
                                      <TableCell align="right">EBIT/EV</TableCell>
                                    </TableRow>
                                  </TableHead>
                                  <TableBody>
                                    {scenario.allocations.map((allocation: any) => (
                                      <TableRow key={allocation.symbol}>
                                        <TableCell>
                                          <Typography variant="body2" fontWeight="bold">
                                            {allocation.symbol}
                                          </Typography>
                                          <Typography variant="caption" color="text.secondary">
                                            {allocation.company_name}
                                          </Typography>
                                        </TableCell>
                                        <TableCell>{allocation.target_weight.toFixed(2)}%</TableCell>
                                        <TableCell align="right">${allocation.target_value.toLocaleString(undefined, { maximumFractionDigits: 2 })}</TableCell>
                                        <TableCell align="right">${allocation.current_value.toLocaleString(undefined, { maximumFractionDigits: 2 })}</TableCell>
                                        <TableCell align="right" sx={{ color: allocation.trade_value >= 0 ? 'success.main' : 'error.main' }}>
                                          {allocation.trade_value >= 0 ? '+' : ''}${allocation.trade_value.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                                        </TableCell>
                                        <TableCell align="right">${allocation.transaction_cost.toLocaleString(undefined, { maximumFractionDigits: 2 })}</TableCell>
                                        <TableCell align="right">{allocation.metrics?.combined_score?.toFixed(2) ?? 'N/A'}</TableCell>
                                        <TableCell align="right">{allocation.metrics?.f_score ?? 'N/A'}</TableCell>
                                        <TableCell align="right">{allocation.metrics?.z_score?.toFixed(2) ?? 'N/A'}</TableCell>
                                        <TableCell align="right">{allocation.metrics?.ebit_ev?.toFixed(2) ?? 'N/A'}</TableCell>
                                      </TableRow>
                                    ))}
                                  </TableBody>
                                </Table>
                              </TableContainer>
                            </AccordionDetails>
                          </Accordion>
                        ))}
                      </CardContent>
                    </Card>
                  )}

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
          </Box>
        )}

        {/* Backtest Strategy Tab */}
        {activeTab === 2 && (
          <Box id="fs-panel-2" role="tabpanel" aria-labelledby="fs-tab-2">
            <Typography variant="h5" sx={srOnlyStyles}>
              Backtest Strategy
            </Typography>
            <BacktestTab 
              getToken={getToken}
              loading={loading}
              setLoading={setLoading}
              error={error}
              setError={setError}
            />
          </Box>
        )}

        <Toast open={toast.open} message={toast.message} severity={toast.severity} onClose={hideToast} />
      </Stack>
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
  const [benchmarkSummary, setBenchmarkSummary] = useState<BenchmarkEntry[]>([]);
  const [benchmarkLoading, setBenchmarkLoading] = useState(false);
  const [benchmarkError, setBenchmarkError] = useState<string | null>(null);

  const fetchBenchmarkSummary = async (equityCurve: Array<{ date: string; value: number }>) => {
    try {
      setBenchmarkLoading(true);
      setBenchmarkError(null);
      const token = getToken();
      if (!token) {
        setBenchmarkError('Authentication required');
        setBenchmarkLoading(false);
        return;
      }
      const response = await fetch(`${API_URL}/api/benchmarks/summary`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          days: 365,
          equity_curve: equityCurve,
        }),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to fetch benchmark summary');
      }
      const data = await response.json();
      setBenchmarkSummary(data.benchmarks || []);
    } catch (err: any) {
      setBenchmarkError(err.message || 'Error fetching benchmark summary');
    } finally {
      setBenchmarkLoading(false);
    }
  };

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
    setBenchmarkSummary([]);
    setBenchmarkError(null);

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
      if (data && data.status !== 'error' && Array.isArray(data.equity_curve) && data.equity_curve.length > 1) {
        fetchBenchmarkSummary(data.equity_curve);
      } else {
        setBenchmarkSummary([]);
      }
    } catch (err: any) {
      setError(err.message || 'Error running backtest');
      setBacktestResult({ status: 'error', error: err.message });
      setBenchmarkSummary([]);
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

              {benchmarkLoading && (
                <LinearProgress sx={{ mb: 3 }} />
              )}

              {benchmarkError && (
                <Alert severity="warning" sx={{ mb: 3 }} onClose={() => setBenchmarkError(null)}>
                  {benchmarkError}
                </Alert>
              )}

              {benchmarkSummary.length > 0 && (
                <Card sx={{ mb: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Benchmark Comparison
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      How the strategy stacks up versus major indices over the same period.
                    </Typography>
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Benchmark</TableCell>
                            <TableCell>Name</TableCell>
                            <TableCell align="right">Total Return</TableCell>
                            <TableCell align="right">Relative Return</TableCell>
                            <TableCell align="right">Alpha</TableCell>
                            <TableCell align="right">Beta</TableCell>
                            <TableCell align="right">Volatility</TableCell>
                            <TableCell align="right">Tracking Error</TableCell>
                            <TableCell align="right">Correlation</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {benchmarkSummary.map((entry) => (
                            <TableRow key={entry.symbol}>
                              <TableCell>{entry.symbol}</TableCell>
                              <TableCell>{entry.name}</TableCell>
                              <TableCell align="right">{entry.total_return !== null && entry.total_return !== undefined ? `${entry.total_return.toFixed(2)}%` : '—'}</TableCell>
                              <TableCell align="right">{entry.relative_return !== null && entry.relative_return !== undefined ? `${entry.relative_return.toFixed(2)}%` : '—'}</TableCell>
                              <TableCell align="right">{entry.alpha !== null && entry.alpha !== undefined ? entry.alpha.toFixed(2) : '—'}</TableCell>
                              <TableCell align="right">{entry.beta !== null && entry.beta !== undefined ? entry.beta.toFixed(2) : '—'}</TableCell>
                              <TableCell align="right">{entry.annual_volatility !== null && entry.annual_volatility !== undefined ? `${entry.annual_volatility.toFixed(2)}%` : '—'}</TableCell>
                              <TableCell align="right">{entry.tracking_error !== null && entry.tracking_error !== undefined ? `${entry.tracking_error.toFixed(2)}%` : '—'}</TableCell>
                              <TableCell align="right">{entry.correlation !== null && entry.correlation !== undefined ? entry.correlation.toFixed(2) : '—'}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </CardContent>
                </Card>
              )}
 
              {/* Equity Curve */}
              {backtestResult.equity_curve && backtestResult.equity_curve.length > 0 && (
                <Card sx={{ mb: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Equity Curve
                    </Typography>
                    <Box sx={{ mt: 2, height: 400 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart
                          data={backtestResult.equity_curve.map((point) => ({
                            ...point,
                            date: new Date(point.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
                            fullDate: point.date,
                          }))}
                          margin={{ top: 5, right: 30, left: 20, bottom: 60 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis
                            dataKey="date"
                            angle={-45}
                            textAnchor="end"
                            height={80}
                            tick={{ fontSize: 12 }}
                          />
                          <YAxis
                            tick={{ fontSize: 12 }}
                            tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                          />
                          <Tooltip
                            formatter={(value: number) => [`$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`, 'Portfolio Value']}
                            labelFormatter={(label) => `Date: ${label}`}
                            contentStyle={{
                              backgroundColor: 'rgba(255, 255, 255, 0.95)',
                              border: '1px solid #ccc',
                              borderRadius: '4px',
                            }}
                          />
                          <ReferenceLine
                            y={backtestResult.initial_capital || backtestResult.equity_curve[0]?.value}
                            stroke="#666"
                            strokeDasharray="3 3"
                            label={{ value: 'Initial Capital', position: 'right' }}
                          />
                          <Line
                            type="monotone"
                            dataKey="value"
                            stroke="#2563eb"
                            strokeWidth={2}
                            dot={false}
                            activeDot={{ r: 6 }}
                            name="Portfolio Value"
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </Box>
                    <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
                      <Typography variant="caption" color="text.secondary">
                        Data points: {backtestResult.equity_curve.length}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Start: ${backtestResult.equity_curve[0]?.value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} | 
                        End: ${backtestResult.equity_curve[backtestResult.equity_curve.length - 1]?.value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              )}
 
              {/* Trade History */}
              {backtestResult.trade_history && backtestResult.trade_history.length > 0 && (
                <Card sx={{ mt: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Trade History
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
                            <TableCell align="right">Profit</TableCell>
                            <TableCell align="right">Reason</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {backtestResult.trade_history.map((trade, index) => (
                            <TableRow key={index}>
                              <TableCell>{new Date(trade.date).toLocaleDateString()}</TableCell>
                              <TableCell>{trade.action}</TableCell>
                              <TableCell>{trade.symbol}</TableCell>
                              <TableCell align="right">${trade.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</TableCell>
                              <TableCell align="right">{trade.shares}</TableCell>
                              <TableCell align="right">${trade.value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</TableCell>
                              <TableCell align="right">{trade.return_pct !== undefined ? `${trade.return_pct.toFixed(2)}%` : '—'}</TableCell>
                              <TableCell align="right">${trade.profit !== undefined ? trade.profit.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '—'}</TableCell>
                              <TableCell align="right">{trade.reason || '—'}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </CardContent>
                </Card>
              )}
 
              {/* Portfolio Compositions */}
              {backtestResult.portfolio_compositions && backtestResult.portfolio_compositions.length > 0 && (
                <Card sx={{ mt: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Portfolio Compositions
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      How the portfolio composition evolved over time.
                    </Typography>
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Date</TableCell>
                            <TableCell>Cash</TableCell>
                            <TableCell>Total Value</TableCell>
                            <TableCell>Positions</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {backtestResult.portfolio_compositions.slice(0, 5).map((composition, index) => (
                            <TableRow key={index}>
                              <TableCell>{new Date(composition.date).toLocaleDateString()}</TableCell>
                              <TableCell>${composition.cash.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</TableCell>
                              <TableCell>${composition.total_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</TableCell>
                              <TableCell>
                                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                  {composition.positions.map((pos) => (
                                    <Chip
                                      key={pos.symbol}
                                      label={`${pos.symbol} (${pos.shares})`}
                                      size="small"
                                      variant="outlined"
                                    />
                                  ))}
                                </Box>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
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
 