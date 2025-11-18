import React, { useState, useEffect, useMemo, useCallback, Suspense, lazy } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  CircularProgress,
  Chip,
  IconButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  ToggleButton,
  ToggleButtonGroup,
  useTheme,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  AccountBalance,
  ShowChart,
  Refresh,
  Timeline,
  BarChart,
  PieChart,
  Assessment,
} from '@mui/icons-material';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  BarChart as RechartsBarChart,
  Bar,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  AreaChart,
  Area
} from 'recharts';
import { portfolioService } from '../services/portfolioService';
import { logger } from '../utils/logger';
// Lazy load heavy chart components for better code splitting
const SankeyFlow = lazy(() => import('./Analytics/SankeyFlow'));
const RiskReturnBubble = lazy(() => import('./Analytics/RiskReturnBubble'));
const InteractivePerformanceChart = lazy(() => import('./Analytics/InteractivePerformanceChart'));
const CorrelationMatrix = lazy(() => import('./Analytics/CorrelationMatrix').then(module => ({ default: module.CorrelationMatrix })));
const RiskReturnScatter = lazy(() => import('./Analytics/RiskReturnScatter').then(module => ({ default: module.RiskReturnScatter })));
const EfficientFrontier = lazy(() => import('./Analytics/EfficientFrontier').then(module => ({ default: module.EfficientFrontier })));
const BetaAnalysis = lazy(() => import('./Analytics/BetaAnalysis').then(module => ({ default: module.BetaAnalysis })));

interface PerformanceData {
  period: string;
  total_return: number;
  daily_returns: number[];
  volatility: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
}

interface AllocationData {
  by_asset: Record<string, number>;
  by_exchange: Record<string, number>;
  by_type: Record<string, number>;
}

const Analytics: React.FC = () => {
  const theme = useTheme();
  const [performanceData, setPerformanceData] = useState<PerformanceData | null>(null);
  const [allocationData, setAllocationData] = useState<AllocationData | null>(null);
  const [portfolioHistory, setPortfolioHistory] = useState<any[]>([]);
  const [benchmarkHistory, setBenchmarkHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('30');
  const [chartType, setChartType] = useState('line');
  const [viewMode, setViewMode] = useState('overview');
  const [advancedAnalytics, setAdvancedAnalytics] = useState<any>(null);
  const [loadingAdvanced, setLoadingAdvanced] = useState(false);
  const [portfolioProjection, setPortfolioProjection] = useState<any>(null);
  const [loadingProjection, setLoadingProjection] = useState(false);
  const [enhancedRecommendations, setEnhancedRecommendations] = useState<any>(null);
  const [loadingRecommendations, setLoadingRecommendations] = useState(false);
  const [portfolioOptimizer, setPortfolioOptimizer] = useState<any>(null);
  const [loadingOptimizer, setLoadingOptimizer] = useState(false);

  const fetchAnalyticsData = useCallback(async () => {
    try {
      setLoading(true);
      const [performance, allocation, history] = await Promise.all([
        portfolioService.getPerformanceAnalytics(parseInt(timeRange), true), // Force refresh to get real data
        portfolioService.getAllocationAnalytics(true),
        portfolioService.getPortfolioHistory(parseInt(timeRange), true) // Get portfolio history with real dates
      ]);
      
      logger.log('Performance data received:', performance);
      logger.log('Allocation data received:', allocation);
      logger.log('Portfolio history received:', history);
      
      setPerformanceData(performance);
      setAllocationData(allocation);
      setPortfolioHistory(history);
      
      // Try to fetch benchmark data (SPY for S&P 500)
      try {
        const benchmark = await portfolioService.getBenchmarkHistory('SPY', parseInt(timeRange));
        logger.log('Benchmark data received:', benchmark);
        setBenchmarkHistory(benchmark);
      } catch (benchmarkError) {
        logger.warn('Could not fetch benchmark data:', benchmarkError);
        setBenchmarkHistory([]);
      }
      
      // Fetch advanced analytics in background
      setLoadingAdvanced(true);
      portfolioService.getAdvancedAnalytics(parseInt(timeRange), 'SPY')
        .then(data => {
          setAdvancedAnalytics(data);
          setLoadingAdvanced(false);
        })
        .catch(error => {
          logger.warn('Could not fetch advanced analytics:', error);
          setLoadingAdvanced(false);
        });

      // Fetch portfolio projection in background
      setLoadingProjection(true);
      portfolioService.getPortfolioProjection(parseInt(timeRange))
        .then(data => {
          setPortfolioProjection(data);
          setLoadingProjection(false);
        })
        .catch(error => {
          logger.warn('Could not fetch portfolio projection:', error);
          setLoadingProjection(false);
        });

      // Fetch enhanced recommendations in background
      setLoadingRecommendations(true);
      portfolioService.getEnhancedRecommendations('moderate', 'long_term', true, true)
        .then(data => {
          setEnhancedRecommendations(data);
          setLoadingRecommendations(false);
        })
        .catch(error => {
          logger.warn('Could not fetch enhanced recommendations:', error);
          setLoadingRecommendations(false);
        });

      // Fetch portfolio optimizer data in background
      setLoadingOptimizer(true);
      portfolioService.getPortfolioOptimizer('mpt', 0.02, undefined, 0.4)
        .then(data => {
          setPortfolioOptimizer(data);
          setLoadingOptimizer(false);
        })
        .catch(error => {
          logger.warn('Could not fetch portfolio optimizer data:', error);
          setLoadingOptimizer(false);
        });
    } catch (error) {
      logger.error('Error fetching analytics data:', error);
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  // DISABLED: Automatic data fetching - now manual only via refresh button
  // useEffect(() => {
  //   fetchAnalyticsData();
  //   // Prefetch contextual data in the background
  //   portfolioService.prefetchContextualData('analytics');
  // }, [fetchAnalyticsData]);

  const formatCurrency = (amount: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  // Get performance chart data with REAL dates from portfolio history and benchmark
  const performanceChartData = useMemo(() => {
    if (!portfolioHistory || portfolioHistory.length === 0) return [];
    
    // Create a map of benchmark dates to normalized values for quick lookup
    const benchmarkMap = new Map<string, number>();
    if (benchmarkHistory && benchmarkHistory.length > 0) {
      benchmarkHistory.forEach(point => {
        const dateKey = new Date(point.date).toISOString().split('T')[0];
        benchmarkMap.set(dateKey, point.normalized_value || point.value);
      });
    }
    
    // Normalize portfolio values (start from 100 = base value)
    const basePortfolioValue = portfolioHistory[0]?.value_usd || 1;
    
    // Only include dates where we have portfolio data AND benchmark data (if benchmark exists)
    const chartData = portfolioHistory
      .filter((point) => {
        const dateKey = new Date(point.date).toISOString().split('T')[0];
        // If no benchmark data, include all portfolio dates
        if (benchmarkMap.size === 0) return true;
        // Otherwise, only include if benchmark has data for this date
        return benchmarkMap.has(dateKey);
      })
      .map((point) => {
        const dateKey = new Date(point.date).toISOString().split('T')[0];
        const benchmarkNormalized = benchmarkMap.get(dateKey) || 0;
        const portfolioNormalized = basePortfolioValue > 0 ? (point.value_usd / basePortfolioValue) * 100 : 0;
        
        return {
          date: new Date(point.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
          value: portfolioNormalized, // Normalized portfolio value
          benchmark: benchmarkNormalized // Normalized benchmark value
        };
      });
    
    return chartData;
  }, [portfolioHistory, benchmarkHistory]);

  // Daily returns with real dates
  const dailyReturnsData = useMemo(() => {
    if (!portfolioHistory || portfolioHistory.length < 2) return [];
    
    return portfolioHistory.slice(1).map((point, index) => {
      const prevValue = portfolioHistory[index].value_usd;
      const currentValue = point.value_usd;
      const dailyReturn = prevValue > 0 ? ((currentValue - prevValue) / prevValue) * 100 : 0;
      
      return {
        day: new Date(point.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        return: dailyReturn
      };
    });
  }, [portfolioHistory]);

  const allocationChartData = useMemo(() => 
    Object.entries(allocationData?.by_asset || {}).map(([name, value]) => ({
    name,
    value,
    percentage: value.toFixed(1)
    }))
  , [allocationData?.by_asset]);

  const exchangeChartData = useMemo(() =>
    Object.entries(allocationData?.by_exchange || {}).map(([name, value]) => ({
    name,
    value,
    percentage: value.toFixed(1)
    }))
  , [allocationData?.by_exchange]);

  const COLORS = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe'];

  if (loading) {
    return (
      <Box sx={{ width: '100%', mt: 2 }}>
        <LinearProgress />
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h1" sx={{ 
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            mb: 1
          }}>
            Analytics Dashboard
          </Typography>
          <Typography variant="h5" color="text.secondary">
            Advanced portfolio performance and risk analysis
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Time Range</InputLabel>
            <Select
              value={timeRange}
              label="Time Range"
              onChange={(e) => setTimeRange(e.target.value)}
            >
              <MenuItem value="7">7 Days</MenuItem>
              <MenuItem value="30">30 Days</MenuItem>
              <MenuItem value="90">90 Days</MenuItem>
              <MenuItem value="365">1 Year</MenuItem>
            </Select>
          </FormControl>
          <IconButton onClick={fetchAnalyticsData} color="primary" size="large">
            <Refresh />
          </IconButton>
        </Box>
      </Box>

      {/* View Mode Toggle */}
      <Box sx={{ mb: 4 }}>
        <ToggleButtonGroup
          value={viewMode}
          exclusive
          onChange={(e, newMode) => newMode && setViewMode(newMode)}
          sx={{ backgroundColor: 'rgba(255, 255, 255, 0.1)' }}
        >
          <ToggleButton value="overview">
            <Assessment sx={{ mr: 1 }} />
            Overview
          </ToggleButton>
          <ToggleButton value="performance">
            <Timeline sx={{ mr: 1 }} />
            Performance
          </ToggleButton>
          <ToggleButton value="risk">
            <BarChart sx={{ mr: 1 }} />
            Risk Analysis
          </ToggleButton>
          <ToggleButton value="allocation">
            <PieChart sx={{ mr: 1 }} />
            Allocation
          </ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {/* Overview Tab - Key Metrics */}
      {viewMode === 'overview' && (
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' },
          gap: { xs: 2, sm: 3, md: 4 }, 
          mb: { xs: 3, sm: 4, md: 5 }
        }}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <TrendingUp sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6" color="text.secondary">
                  Total Return
                </Typography>
              </Box>
              <Typography 
                variant="h4" 
                sx={{ 
                  fontWeight: 700, 
                  mb: 1,
                  fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' },
                  color: performanceData?.total_return && performanceData.total_return >= 0 ? 'success.main' : 'error.main'
                }}
              >
                {formatPercentage(performanceData?.total_return || 0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {timeRange} days
              </Typography>
            </CardContent>
          </Card>

          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <ShowChart sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6" color="text.secondary">
                  Sharpe Ratio
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 700, mb: 1, fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' } }}>
                {performanceData?.sharpe_ratio?.toFixed(2) || '0.00'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Risk-adjusted return
              </Typography>
            </CardContent>
          </Card>

          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <TrendingDown sx={{ mr: 1, color: 'error.main' }} />
                <Typography variant="h6" color="text.secondary">
                  Max Drawdown
                </Typography>
              </Box>
              <Typography 
                variant="h4" 
                sx={{ 
                  fontWeight: 700, 
                  mb: 1,
                  fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' },
                  color: 'error.main'
                }}
              >
                {formatPercentage(performanceData?.max_drawdown || 0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Peak to trough
              </Typography>
            </CardContent>
          </Card>

          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <AccountBalance sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6" color="text.secondary">
                  Win Rate
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 700, mb: 1, fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' } }}>
                {performanceData?.win_rate?.toFixed(1) || '0.0'}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Profitable days
              </Typography>
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Performance Tab - Performance Metrics */}
      {viewMode === 'performance' && (
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)' },
          gap: { xs: 2, sm: 3, md: 4 }, 
          mb: { xs: 3, sm: 4, md: 5 }
        }}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <TrendingUp sx={{ mr: 1, color: 'success.main' }} />
                <Typography variant="h6" color="text.secondary">
                  Period Return
                </Typography>
              </Box>
              <Typography 
                variant="h4" 
                sx={{ 
                  fontWeight: 700, 
                  mb: 1,
                  fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' },
                  color: performanceData?.total_return && performanceData.total_return >= 0 ? 'success.main' : 'error.main'
                }}
              >
                {formatPercentage(performanceData?.total_return || 0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Last {timeRange} days
              </Typography>
            </CardContent>
          </Card>

          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Timeline sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6" color="text.secondary">
                  Daily Average
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 700, mb: 1, fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' } }}>
                {formatPercentage((performanceData?.total_return || 0) / parseInt(timeRange))}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Per day
              </Typography>
            </CardContent>
          </Card>

          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <ShowChart sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6" color="text.secondary">
                  Sharpe Ratio
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 700, mb: 1, fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' } }}>
                {performanceData?.sharpe_ratio?.toFixed(2) || '0.00'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Risk-adjusted return
              </Typography>
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Risk Tab - Risk Metrics */}
      {viewMode === 'risk' && (
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' },
          gap: { xs: 2, sm: 3, md: 4 }, 
          mb: { xs: 3, sm: 4, md: 5 }
        }}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <BarChart sx={{ mr: 1, color: 'warning.main' }} />
                <Typography variant="h6" color="text.secondary">
                  Volatility
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 700, mb: 1, fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' }, color: 'warning.main' }}>
                {performanceData?.volatility?.toFixed(2) || '0.00'}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Annualized
              </Typography>
            </CardContent>
          </Card>

          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <TrendingDown sx={{ mr: 1, color: 'error.main' }} />
                <Typography variant="h6" color="text.secondary">
                  Max Drawdown
                </Typography>
              </Box>
              <Typography 
                variant="h4" 
                sx={{ 
                  fontWeight: 700, 
                  mb: 1,
                  fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' },
                  color: 'error.main'
                }}
              >
                {formatPercentage(performanceData?.max_drawdown || 0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Peak to trough
              </Typography>
            </CardContent>
          </Card>

          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <AccountBalance sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6" color="text.secondary">
                  Win Rate
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 700, mb: 1, fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' } }}>
                {performanceData?.win_rate?.toFixed(1) || '0.0'}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Profitable days
              </Typography>
            </CardContent>
          </Card>

          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <ShowChart sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6" color="text.secondary">
                  Risk Score
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 700, mb: 1, fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' } }}>
                {performanceData?.volatility && performanceData.volatility > 20 ? 'High' : 
                 performanceData?.volatility && performanceData.volatility > 10 ? 'Medium' : 'Low'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Based on volatility
              </Typography>
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Allocation Tab - Allocation Metrics */}
      {viewMode === 'allocation' && (
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' },
          gap: { xs: 2, sm: 3, md: 4 }, 
          mb: { xs: 3, sm: 4, md: 5 }
        }}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <PieChart sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6" color="text.secondary">
                  Total Assets
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 700, mb: 1, fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' } }}>
                {Object.keys(allocationData?.by_asset || {}).length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Different holdings
              </Typography>
            </CardContent>
          </Card>

          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <AccountBalance sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6" color="text.secondary">
                  Active Exchanges
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 700, mb: 1, fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' } }}>
                {Object.keys(allocationData?.by_exchange || {}).length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Connected platforms
              </Typography>
            </CardContent>
          </Card>

          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <TrendingUp sx={{ mr: 1, color: 'success.main' }} />
                <Typography variant="h6" color="text.secondary">
                  Top Asset
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 700, mb: 1, fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' } }}>
                {Object.entries(allocationData?.by_asset || {})
                  .sort(([,a], [,b]) => b - a)[0]?.[0] || 'N/A'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Largest holding
              </Typography>
            </CardContent>
          </Card>

          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <ShowChart sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6" color="text.secondary">
                  Diversification
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 700, mb: 1, fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' } }}>
                {Object.keys(allocationData?.by_asset || {}).length > 10 ? 'High' : 
                 Object.keys(allocationData?.by_asset || {}).length > 5 ? 'Medium' : 'Low'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Asset count
              </Typography>
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Overview Tab - Performance Chart */}
      {viewMode === 'overview' && (
        <Card sx={{ mb: { xs: 3, sm: 4, md: 5 } }}>
          <CardContent sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: { xs: 2, sm: 3 } }}>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Portfolio Performance vs Benchmark
              </Typography>
              <ToggleButtonGroup
                value={chartType}
                exclusive
                onChange={(e, newType) => newType && setChartType(newType)}
                size="small"
              >
                <ToggleButton value="line">
                  <Timeline />
                </ToggleButton>
                <ToggleButton value="area">
                  <ShowChart />
                </ToggleButton>
              </ToggleButtonGroup>
            </Box>
            <Box sx={{ height: { xs: 250, sm: 300, md: 400 } }}>
              <ResponsiveContainer width="100%" height="100%">
                {chartType === 'line' ? (
                  <LineChart data={performanceChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis 
                      dataKey="date" 
                      stroke={theme.palette.text.secondary}
                      tick={{ fontSize: 12, fill: theme.palette.text.secondary }}
                    />
                    <YAxis 
                      stroke={theme.palette.text.secondary}
                      tick={{ fontSize: 12, fill: theme.palette.text.secondary }}
                      tickFormatter={(value) => `${value.toFixed(0)}%`}
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: theme.palette.mode === 'dark' 
                          ? 'rgba(45, 55, 72, 0.98)' 
                          : 'rgba(255, 255, 255, 0.98)',
                        border: `1px solid ${theme.palette.divider}`,
                        borderRadius: '12px',
                        padding: '12px 16px',
                        fontSize: 14,
                        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.2)'
                      }}
                      labelStyle={{ 
                        color: theme.palette.text.primary,
                        fontWeight: 600 
                      }}
                      formatter={(value: number, name: string) => [
                        `${(value - 100).toFixed(1)}%`, 
                        name === 'value' ? 'Portfolio' : 'Benchmark'
                      ]}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="value" 
                      stroke="#667eea" 
                      strokeWidth={3}
                      dot={{ fill: '#667eea', strokeWidth: 2, r: 4 }}
                      activeDot={{ r: 6, stroke: '#667eea', strokeWidth: 2 }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="benchmark" 
                      stroke="#764ba2" 
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      dot={{ fill: '#764ba2', strokeWidth: 2, r: 3 }}
                    />
                  </LineChart>
                ) : (
                  <AreaChart data={performanceChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis 
                      dataKey="date" 
                      stroke={theme.palette.text.secondary}
                      tick={{ fontSize: 12, fill: theme.palette.text.secondary }}
                    />
                    <YAxis 
                      stroke={theme.palette.text.secondary}
                      tick={{ fontSize: 12, fill: theme.palette.text.secondary }}
                      tickFormatter={(value) => `${value.toFixed(0)}%`}
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: theme.palette.mode === 'dark' 
                          ? 'rgba(45, 55, 72, 0.98)' 
                          : 'rgba(255, 255, 255, 0.98)',
                        border: `1px solid ${theme.palette.divider}`,
                        borderRadius: '12px',
                        padding: '12px 16px',
                        fontSize: 14,
                        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.2)'
                      }}
                      labelStyle={{ 
                        color: theme.palette.text.primary,
                        fontWeight: 600 
                      }}
                      formatter={(value: number, name: string) => [
                        `${(value - 100).toFixed(1)}%`, 
                        name === 'value' ? 'Portfolio' : 'Benchmark'
                      ]}
                    />
                    <defs>
                      <linearGradient id="portfolioGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#667eea" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#667eea" stopOpacity={0.05}/>
                      </linearGradient>
                    </defs>
                    <Area 
                      type="monotone" 
                      dataKey="value" 
                      stroke="#667eea" 
                      fill="url(#portfolioGradient)"
                      strokeWidth={2}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="benchmark" 
                      stroke="#764ba2" 
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      dot={false}
                    />
                  </AreaChart>
                )}
              </ResponsiveContainer>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Performance Tab - Daily Returns Chart */}
      {viewMode === 'performance' && (
        <Card sx={{ mb: { xs: 3, sm: 4, md: 5 } }}>
          <CardContent sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
            <Typography variant="h6" sx={{ mb: { xs: 2, sm: 3 }, fontWeight: 600 }}>
              Daily Returns Analysis
            </Typography>
            <Box sx={{ height: { xs: 250, sm: 300, md: 400 } }}>
              <ResponsiveContainer width="100%" height="100%">
                <RechartsBarChart data={dailyReturnsData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis 
                    dataKey="day" 
                    stroke="#b0b0b0"
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis 
                    stroke="#b0b0b0"
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) => `${value}%`}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1a1a1a', 
                      border: '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '8px',
                      fontSize: 14
                    }}
                    formatter={(value: number) => [`${value.toFixed(2)}%`, 'Return']}
                  />
                  <Bar 
                    dataKey="return" 
                    fill="#667eea" 
                    radius={[2, 2, 0, 0]}
                  />
                </RechartsBarChart>
              </ResponsiveContainer>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Risk Tab - Risk Analysis Charts */}
      {viewMode === 'risk' && (
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' },
          gap: { xs: 2, sm: 3, md: 4 }, 
          mb: { xs: 3, sm: 4, md: 5 }
        }}>
          <Card>
            <CardContent sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
              <Typography variant="h6" sx={{ mb: { xs: 2, sm: 3 }, fontWeight: 600 }}>
                Daily Returns Distribution
              </Typography>
              <Box sx={{ height: { xs: 250, sm: 300, md: 400 } }}>
                <ResponsiveContainer width="100%" height="100%">
                  <RechartsBarChart data={dailyReturnsData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis 
                      dataKey="day" 
                      stroke={theme.palette.text.secondary}
                      tick={{ fontSize: 12, fill: theme.palette.text.secondary }}
                    />
                    <YAxis 
                      stroke={theme.palette.text.secondary}
                      tick={{ fontSize: 12, fill: theme.palette.text.secondary }}
                      tickFormatter={(value) => `${value}%`}
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: theme.palette.mode === 'dark' 
                          ? 'rgba(45, 55, 72, 0.98)' 
                          : 'rgba(255, 255, 255, 0.98)',
                        border: `1px solid ${theme.palette.divider}`,
                        borderRadius: '12px',
                        padding: '12px 16px',
                        fontSize: 14,
                        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.2)'
                      }}
                      labelStyle={{ 
                        color: theme.palette.text.primary,
                        fontWeight: 600 
                      }}
                      formatter={(value: number) => [`${value.toFixed(2)}%`, 'Return']}
                    />
                    <Bar 
                      dataKey="return" 
                      fill="#667eea" 
                      radius={[2, 2, 0, 0]}
                    />
                  </RechartsBarChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>

          <Card>
            <CardContent sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
              <Typography variant="h6" sx={{ mb: { xs: 2, sm: 3 }, fontWeight: 600 }}>
                Risk Metrics Summary
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body1">Volatility</Typography>
                  <Chip 
                    label={`${performanceData?.volatility?.toFixed(2) || '0.00'}%`}
                    color="warning"
                    variant="outlined"
                  />
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body1">Sharpe Ratio</Typography>
                  <Chip 
                    label={performanceData?.sharpe_ratio?.toFixed(2) || '0.00'}
                    color={performanceData?.sharpe_ratio && performanceData.sharpe_ratio > 1 ? 'success' : 'warning'}
                    variant="outlined"
                  />
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body1">Max Drawdown</Typography>
                  <Chip 
                    label={`${performanceData?.max_drawdown?.toFixed(2) || '0.00'}%`}
                    color="error"
                    variant="outlined"
                  />
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body1">Win Rate</Typography>
                  <Chip 
                    label={`${performanceData?.win_rate?.toFixed(1) || '0.0'}%`}
                    color={performanceData?.win_rate && performanceData.win_rate > 50 ? 'success' : 'warning'}
                    variant="outlined"
                  />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Allocation Charts */}
      {viewMode === 'allocation' ? (
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' },
          gap: { xs: 2, sm: 3, md: 4 }, 
          mb: { xs: 3, sm: 4, md: 5 }
        }}>
          <Card>
            <CardContent sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
              <Typography variant="h6" sx={{ mb: { xs: 2, sm: 3 }, fontWeight: 600 }}>
                Asset Allocation
              </Typography>
              <Box sx={{ height: { xs: 250, sm: 300, md: 400 } }}>
                <ResponsiveContainer width="100%" height="100%">
                  <RechartsPieChart>
                    <Pie
                      data={allocationChartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percentage }) => `${name} ${percentage}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {allocationChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ fontSize: 14 }}
                      formatter={(value: number) => [`${value.toFixed(1)}%`, 'Allocation']}
                    />
                  </RechartsPieChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>

          <Card>
            <CardContent sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
              <Typography variant="h6" sx={{ mb: { xs: 2, sm: 3 }, fontWeight: 600 }}>
                Exchange Distribution
              </Typography>
              <Box sx={{ height: { xs: 250, sm: 300, md: 400 } }}>
                <ResponsiveContainer width="100%" height="100%">
                  <RechartsBarChart data={exchangeChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis 
                      dataKey="name" 
                      stroke={theme.palette.text.secondary}
                      tick={{ fontSize: 12, fill: theme.palette.text.secondary }}
                    />
                    <YAxis 
                      stroke={theme.palette.text.secondary}
                      tick={{ fontSize: 12, fill: theme.palette.text.secondary }}
                      tickFormatter={(value) => `${value}%`}
                    />
                    <Tooltip 
                      contentStyle={{ fontSize: 14 }}
                      formatter={(value: number) => [`${value.toFixed(1)}%`, 'Allocation']}
                    />
                    <Bar dataKey="value" fill="#667eea" radius={[4, 4, 0, 0]} />
                  </RechartsBarChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Box>
      ) : null}

      {/* Advanced Analytics */}
      <Box sx={{ mb: { xs: 3, sm: 4, md: 5 } }}>
        <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>
          Advanced Analytics
        </Typography>
        
        {loadingAdvanced && (
          <Box sx={{ mb: 3 }}>
            <LinearProgress />
          </Box>
        )}
        
        {advancedAnalytics && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mb: 3 }}>
            {/* Correlation Matrix */}
            {advancedAnalytics.correlation_matrix && Object.keys(advancedAnalytics.correlation_matrix).length > 0 && (
              <Suspense fallback={<Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}><LinearProgress /></Box>}>
                <CorrelationMatrix data={advancedAnalytics.correlation_matrix} />
              </Suspense>
            )}
            
            {/* Risk-Return Scatter */}
            {advancedAnalytics.risk_return_scatter && advancedAnalytics.risk_return_scatter.length > 0 && (
              <Suspense fallback={<Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}><LinearProgress /></Box>}>
                <RiskReturnScatter data={advancedAnalytics.risk_return_scatter} />
              </Suspense>
            )}
            
            {/* Efficient Frontier */}
            {advancedAnalytics.efficient_frontier && advancedAnalytics.efficient_frontier.length > 0 && (
              <Suspense fallback={<Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}><LinearProgress /></Box>}>
                <EfficientFrontier data={advancedAnalytics.efficient_frontier} />
              </Suspense>
            )}
            
            {/* Beta Analysis */}
            {advancedAnalytics.beta_analysis && Object.keys(advancedAnalytics.beta_analysis).length > 0 && (
              <Suspense fallback={<Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}><LinearProgress /></Box>}>
                <BetaAnalysis 
                  data={advancedAnalytics.beta_analysis} 
                  benchmark={advancedAnalytics.benchmark || 'SPY'} 
                />
              </Suspense>
            )}
          </Box>
        )}
        
        <Box sx={{ mb: { xs: 2, sm: 3 } }}>
          <Suspense fallback={<Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}><LinearProgress /></Box>}>
            <RiskReturnBubble />
          </Suspense>
        </Box>
      </Box>

      {/* Portfolio Projection Section */}
      <Box sx={{ mb: { xs: 3, sm: 4, md: 5 } }}>
        <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>
          Portfolio Value Projection ({timeRange} Days)
        </Typography>
        {loadingProjection ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}>
            <CircularProgress />
          </Box>
        ) : portfolioProjection && portfolioProjection.projections && portfolioProjection.projections.length > 0 ? (
          <Card variant="outlined" sx={{ borderRadius: 2 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Total Projected Value: {formatCurrency(portfolioProjection.total_projected_value)}
              </Typography>
              <Typography variant="body1" color={portfolioProjection.projected_change >= 0 ? 'success.main' : 'error.main'} sx={{ mb: 3 }}>
                Projected Change: {formatPercentage(portfolioProjection.projected_change)}
              </Typography>
              <Box sx={{ mt: 3 }}>
                <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 600 }}>Asset Projections:</Typography>
                {portfolioProjection.projections.map((p: any) => (
                  <Box key={p.symbol} sx={{ display: 'flex', justifyContent: 'space-between', mb: 1, p: 1, bgcolor: 'background.default', borderRadius: 1 }}>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>{p.symbol}</Typography>
                    <Typography variant="body2" color={p.change_percent >= 0 ? 'success.main' : 'error.main'}>
                      {formatCurrency(p.projected_value)} ({formatPercentage(p.change_percent)})
                    </Typography>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        ) : (
          <Typography variant="body1" color="text.secondary">
            No portfolio projection data available.
          </Typography>
        )}
      </Box>

      {/* Enhanced Recommendations Section */}
      <Box sx={{ mb: { xs: 3, sm: 4, md: 5 } }}>
        <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>
          Enhanced AI Recommendations
        </Typography>
        {loadingRecommendations ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}>
            <CircularProgress />
          </Box>
        ) : enhancedRecommendations ? (
          <Card variant="outlined" sx={{ borderRadius: 2 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Current Portfolio Value: {formatCurrency(enhancedRecommendations.total_value)}
              </Typography>
              <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 600 }}>Current Allocation:</Typography>
              {Object.entries(enhancedRecommendations.current_allocation || {}).map(([symbol, percent]: [string, any]) => (
                <Typography key={symbol} variant="body2" sx={{ mb: 0.5 }}>{symbol}: {percent.toFixed(2)}%</Typography>
              ))}

              {enhancedRecommendations.rebalancing_suggestions && enhancedRecommendations.rebalancing_suggestions.length > 0 && (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 600 }}>Rebalancing Suggestions:</Typography>
                  {enhancedRecommendations.rebalancing_suggestions.map((s: any) => (
                    <Box key={s.symbol} sx={{ mb: 1, p: 1, bgcolor: 'background.default', borderRadius: 1 }}>
                      <Typography variant="body2" color={s.action === 'increase' ? 'success.main' : 'error.main'}>
                        {s.action === 'increase' ? 'Buy' : 'Sell'} {s.symbol}: {formatCurrency(Math.abs(s.adjustment_value))} ({formatPercentage(s.adjustment_percent)}) - {s.reason}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              )}

              {enhancedRecommendations.tax_loss_opportunities && enhancedRecommendations.tax_loss_opportunities.length > 0 && (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 600 }}>Tax-Loss Harvesting Opportunities:</Typography>
                  {enhancedRecommendations.tax_loss_opportunities.map((o: any) => (
                    <Box key={o.symbol} sx={{ mb: 1, p: 1, bgcolor: 'background.default', borderRadius: 1 }}>
                      <Typography variant="body2" color="info.main">
                        {o.symbol}: Potential Loss {formatCurrency(o.loss_value)} ({formatPercentage(o.loss_percent)}) - Savings: {formatCurrency(o.potential_tax_savings)}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
        ) : (
          <Typography variant="body1" color="text.secondary">
            No enhanced recommendations available.
          </Typography>
        )}
      </Box>

      {/* Portfolio Optimizer Section */}
      <Box sx={{ mb: { xs: 3, sm: 4, md: 5 } }}>
        <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>
          Portfolio Optimizer
        </Typography>
        {loadingOptimizer ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}>
            <CircularProgress />
          </Box>
        ) : portfolioOptimizer ? (
          <Card variant="outlined" sx={{ borderRadius: 2 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Optimization Method: {portfolioOptimizer.method === 'mpt' ? 'Modern Portfolio Theory' : 'Risk Parity'}
              </Typography>
              <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 600 }}>Optimized Weights:</Typography>
              {Object.entries(portfolioOptimizer.optimized_weights || {}).map(([symbol, weight]: [string, any]) => (
                <Typography key={symbol} variant="body2" sx={{ mb: 0.5 }}>{symbol}: {weight.toFixed(2)}%</Typography>
              ))}
              <Typography variant="subtitle1" sx={{ mt: 2, mb: 1, fontWeight: 600 }}>Current Weights:</Typography>
              {Object.entries(portfolioOptimizer.current_weights || {}).map(([symbol, weight]: [string, any]) => (
                <Typography key={symbol} variant="body2" sx={{ mb: 0.5 }}>{symbol}: {weight.toFixed(2)}%</Typography>
              ))}
              <Box sx={{ mt: 3, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                <Typography variant="body1" sx={{ mb: 1 }}>
                  Expected Return: {formatPercentage(portfolioOptimizer.expected_return)}
                </Typography>
                <Typography variant="body1" sx={{ mb: 1 }}>
                  Expected Volatility: {portfolioOptimizer.expected_volatility?.toFixed(2) || '0.00'}%
                </Typography>
                <Typography variant="body1" sx={{ mb: 1 }}>
                  Sharpe Ratio: {portfolioOptimizer.sharpe_ratio?.toFixed(3) || '0.000'}
                </Typography>
                {portfolioOptimizer.rebalancing_needed && (
                  <Typography variant="body1" color="warning.main" sx={{ mt: 2 }}>
                    ⚠️ Rebalancing Needed: Yes (drift {'>'} 5%)
                  </Typography>
                )}
              </Box>
            </CardContent>
          </Card>
        ) : (
          <Typography variant="body1" color="text.secondary">
            No portfolio optimization data available.
          </Typography>
        )}
      </Box>

      {/* Portfolio Flow */}
      <Box sx={{ mb: { xs: 3, sm: 4, md: 5 } }}>
        <Suspense fallback={<Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 600 }}><LinearProgress /></Box>}>
          <SankeyFlow width={1000} height={600} />
        </Suspense>
      </Box>

      {/* Interactive Performance */}
      <Box sx={{ mb: { xs: 3, sm: 4, md: 5 } }}>
        <Suspense fallback={<Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}><LinearProgress /></Box>}>
          <InteractivePerformanceChart days={parseInt(timeRange)} height={400} showBrush={true} />
        </Suspense>
      </Box>

      {/* Additional Analytics */}
      <Card>
        <CardContent sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
          <Typography variant="h6" sx={{ mb: { xs: 2, sm: 3 }, fontWeight: 600 }}>
            Performance Summary
          </Typography>
          <Box sx={{ 
            display: 'grid', 
            gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)' },
            gap: { xs: 2, sm: 3 }
          }}>
            <Box>
              <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                Period Performance
              </Typography>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {formatPercentage(performanceData?.total_return || 0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Over {timeRange} days
              </Typography>
            </Box>
            <Box>
              <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                Risk-Adjusted Return
              </Typography>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {performanceData?.sharpe_ratio?.toFixed(2) || '0.00'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Sharpe Ratio
              </Typography>
            </Box>
            <Box>
              <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                Volatility
              </Typography>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {performanceData?.volatility?.toFixed(2) || '0.00'}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Annualized
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Analytics;