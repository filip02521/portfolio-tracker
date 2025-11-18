import React, { useState, useEffect, useMemo, useCallback, Suspense } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Chip,
  IconButton,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Avatar,
  Alert,
  AlertTitle,
  useMediaQuery,
  useTheme,
  Tooltip,
  TextField,
  InputAdornment,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Stack,
  CircularProgress,
  ToggleButton,
  ToggleButtonGroup,
  Slider,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  AccountBalance,
  ShowChart,
  Refresh,
  Visibility,
  VisibilityOff,
  Search,
  Download,
  ArrowUpward,
  ArrowDownward,
  Clear,
  Sync,
} from '@mui/icons-material';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip } from 'recharts';
import { Tabs, Tab } from '@mui/material';
import { portfolioService } from '../services/portfolioService';
import type { Asset as PortfolioServiceAsset } from '../services/portfolioService';
import { logger } from '../utils/logger';
import { Toast, useToast } from './common/Toast';
// Virtual scrolling for large asset lists
// eslint-disable-next-line @typescript-eslint/no-var-requires
const { FixedSizeList } = require('react-window');

const STABLECOIN_SYMBOLS = new Set(['USDT', 'USDC', 'BUSD', 'DAI', 'TUSD', 'USDP', 'FDUSD']);
const CRYPTO_EXCHANGES = new Set(['binance', 'bybit', 'coinbase', 'kraken']);
const AssetDetailsDrawer = React.lazy(() => import('./portfolio/AssetDetailsDrawer').then(mod => ({ default: mod.AssetDetailsDrawer })));
const TreemapAllocation = React.lazy(() => import('./portfolio/TreemapAllocation'));
const SunburstComposition = React.lazy(() => import('./portfolio/SunburstComposition'));

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

const ChartPlaceholder: React.FC<{ height?: number }> = ({ height = 320 }) => (
  <Card sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: height }}>
    <CircularProgress size={24} aria-label="Loading visualization" />
  </Card>
);

type Asset = PortfolioServiceAsset;

interface AllocationData {
  by_asset: Record<string, number>;
  by_exchange: Record<string, number>;
  by_type: Record<string, number>;
}

const Portfolio: React.FC = () => {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [allocationData, setAllocationData] = useState<AllocationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [showSmallAssets, setShowSmallAssets] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('');
  const [exchangeFilter, setExchangeFilter] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('value');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [allocationView, setAllocationView] = useState<'traditional' | 'treemap' | 'sunburst'>('traditional');
  const [assetTypeFilter, setAssetTypeFilter] = useState<string[]>([]);
  const [minValueFilter, setMinValueFilter] = useState<number>(1);
  const [pnlFilter, setPnlFilter] = useState<'all' | 'positive' | 'negative'>('all');
  const [filtering, setFiltering] = useState(false);
  const theme = useTheme();
  const isSmallScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const FILTER_STORAGE_KEY = 'portfolio:filters';
  const { toast, showToast, hideToast } = useToast();

  useEffect(() => {
    try {
      const stored = localStorage.getItem(FILTER_STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (typeof parsed.showSmallAssets === 'boolean') {
          setShowSmallAssets(parsed.showSmallAssets);
        }
        if (typeof parsed.exchangeFilter === 'string') {
          setExchangeFilter(parsed.exchangeFilter);
        }
        if (typeof parsed.sortBy === 'string') {
          setSortBy(parsed.sortBy);
        }
        if (parsed.sortOrder === 'asc' || parsed.sortOrder === 'desc') {
          setSortOrder(parsed.sortOrder);
        }
        if (Array.isArray(parsed.assetTypeFilter)) {
          setAssetTypeFilter(parsed.assetTypeFilter);
        }
        if (typeof parsed.minValueFilter === 'number') {
          setMinValueFilter(parsed.minValueFilter);
        }
        if (['all', 'positive', 'negative'].includes(parsed.pnlFilter)) {
          setPnlFilter(parsed.pnlFilter);
        }
      }
    } catch (err) {
      logger.warn('Portfolio: failed to restore filters', err);
    }
  }, []);

  // Debounce search term
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  useEffect(() => {
    try {
      const payload = {
        showSmallAssets,
        exchangeFilter,
        sortBy,
        sortOrder,
        assetTypeFilter,
        minValueFilter,
        pnlFilter,
      };
      localStorage.setItem(FILTER_STORAGE_KEY, JSON.stringify(payload));
    } catch (err) {
      logger.debug('Portfolio: failed to persist filters', err);
    }
  }, [showSmallAssets, exchangeFilter, sortBy, sortOrder, assetTypeFilter, minValueFilter, pnlFilter]);

  useEffect(() => {
    if (loading) return;
    setFiltering(true);
    const handle = window.setTimeout(() => setFiltering(false), 200);
    return () => window.clearTimeout(handle);
  }, [debouncedSearchTerm, exchangeFilter, showSmallAssets, sortBy, sortOrder, assetTypeFilter, minValueFilter, pnlFilter, loading]);

  const fetchData = useCallback(async (showLoading = true) => {
    let success = false;
    try {
      if (showLoading) {
        setLoading(true);
      }
      setError(null); // Clear previous errors
      
      logger.log('Portfolio: Starting to fetch data...');
      logger.log('Portfolio: API URL:', 'http://localhost:8000/api');
      
      const startTime = Date.now();
      
      // Fetch assets first (critical data)
      logger.log('Portfolio: Fetching assets...');
      let assetsData: Asset[] = [];
      try {
        assetsData = await portfolioService.getAssets();
        logger.log('Portfolio: Assets fetched successfully:', assetsData.length);
      } catch (err: any) {
        logger.error('Portfolio: Error fetching assets:', err);
        throw err; // Re-throw because we need assets data
      }
      
      // Fetch allocation separately (less critical)
      logger.log('Portfolio: Fetching allocation...');
      let allocationData: AllocationData | null = null;
      try {
        allocationData = await portfolioService.getAllocationAnalytics();
        logger.log('Portfolio: Allocation fetched successfully');
      } catch (err: any) {
        logger.warn('Portfolio: Error fetching allocation (non-critical):', err);
        // Don't throw - allocation is not critical
      }
      
      const endTime = Date.now();
      logger.log(`Portfolio: Data fetched in ${endTime - startTime}ms`);
      
      logger.log('Portfolio: Assets data received:', assetsData?.length || 0, 'assets');
      logger.log('Portfolio: Sample asset:', assetsData?.[0]);
      
      if (assetsData && assetsData.length > 0) {
        setAssets(assetsData);
        setAllocationData(allocationData);
        logger.log('Portfolio: Data set successfully');
        success = true;
      } else {
        logger.warn('Portfolio: No assets received');
        setAssets([]);
        setAllocationData(allocationData);
      }
      setLastUpdate(new Date());
    } catch (error: any) {
      logger.error('Portfolio: Error fetching portfolio data:', error);
      // Only show error if it's a manual refresh (not auto-refresh)
      if (showLoading) {
        logger.error('Portfolio: Error details:', {
          message: error?.message,
          code: error?.code,
          response: error?.response?.data,
          request: error?.request,
          userMessage: error?.userMessage
        });
        
        const errorMessage = error?.userMessage || error?.message || 'Failed to load portfolio data. Please try again.';
        setError(errorMessage);
      }
      
      // Set empty data to prevent UI breakage
      if (assets.length === 0) {
        setAssets([]);
        setAllocationData(null);
      }
    } finally {
      if (showLoading) {
        setLoading(false);
      }
      logger.log('Portfolio: Fetch completed');
    }
    return success;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty deps - fetchData doesn't depend on props or state

  const formatCurrency = (amount?: number, currency: string = 'USD') => {
    if (typeof amount !== 'number' || !Number.isFinite(amount)) {
      return '—';
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
    }).format(amount);
  };

  const formatPercentage = (value?: number) => {
    if (typeof value !== 'number' || !Number.isFinite(value)) {
      return '—';
    }
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const formatNumber = (value?: number, decimals: number = 2) => {
    if (typeof value !== 'number' || !Number.isFinite(value)) {
      return '—';
    }
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(value);
  };

  const getAssetIcon = (symbol: string) => {
    // Simple icon based on symbol
    const icons: Record<string, string> = {
      'BTC': '₿',
      'ETH': 'Ξ',
      'ADA': '₳',
      'DOT': '●',
      'LINK': '🔗',
      'UNI': '🦄',
      'AAVE': '👻',
      'SOL': '◎',
    };
    return icons[symbol] || '💰';
  };

  const getExchangeColor = (exchange: string) => {
    const colors: Record<string, string> = {
      binance: '#F0B90B',
      bybit: '#F7A600',
      xtb: '#00A651',
      coinbase: '#0052FF',
    };
    const normalized = (exchange || '').toLowerCase();
    if (normalized === 'multi' || normalized === 'multiple') {
      return 'rgba(148, 163, 184, 0.32)';
    }
    return colors[normalized] || '#666';
  };

  const deriveAssetType = useCallback(
    (asset: Asset) => {
      const explicitType = (asset.asset_type || '').toLowerCase();
      if (explicitType === 'crypto') {
        return 'crypto';
      }
      if (explicitType === 'stock') {
        return 'stock';
      }

      const symbol = (asset.symbol || '').toUpperCase();
      if (STABLECOIN_SYMBOLS.has(symbol)) {
        return 'stablecoin';
      }

      const primaryExchange = (asset.exchange || '').toLowerCase();
      if (CRYPTO_EXCHANGES.has(primaryExchange)) {
        return 'crypto';
      }
      const hasCryptoSource =
        Array.isArray(asset.sources) &&
        asset.sources.some((source) => CRYPTO_EXCHANGES.has((source.exchange || '').toLowerCase()));
      if (hasCryptoSource) {
        return 'crypto';
      }

      if (symbol && /^[A-Z.]{1,5}$/.test(symbol) && !STABLECOIN_SYMBOLS.has(symbol)) {
        return 'stock';
      }
      return 'other';
    },
    []
  );

  const getExchangeList = (asset: Asset): string[] => {
    if (Array.isArray(asset.exchanges) && asset.exchanges.length > 0) {
      return asset.exchanges;
    }
    if (Array.isArray(asset.sources) && asset.sources.length > 0) {
      const seen = new Set<string>();
      const list: string[] = [];
      asset.sources.forEach((source) => {
        const name = source.exchange;
        if (name && !seen.has(name)) {
          seen.add(name);
          list.push(name);
        }
      });
      if (list.length > 0) {
        return list;
      }
    }
    return asset.exchange ? [asset.exchange] : [];
  };

  const buildSourceTooltipContent = (asset: Asset) => {
    if (Array.isArray(asset.sources) && asset.sources.length > 0) {
      return (
        <Stack spacing={0.5}>
          {asset.sources.map((source, index) => (
            <Box key={`${source.exchange || 'unknown'}-${index}`}>
              <Typography variant="caption" sx={{ fontWeight: 600 }}>
                {source.exchange || 'Unknown'}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {`Amount ${formatNumber(source.amount ?? 0, 4)} • Value ${formatCurrency(source.value_usd ?? 0)}`}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {`P/L ${formatCurrency(source.pnl ?? 0)} (${formatPercentage(source.pnl_percent ?? undefined)})`}
              </Typography>
            </Box>
          ))}
        </Stack>
      );
    }
    const exchanges = getExchangeList(asset);
    if (exchanges.length > 0) {
      return exchanges.join(', ');
    }
    return 'No exchange data';
  };

  const exchangeOptions = useMemo(() => {
    const set = new Set<string>();
    assets.forEach((asset) => {
      if (asset.exchange) {
        set.add(asset.exchange);
      }
      if (Array.isArray(asset.exchanges)) {
        asset.exchanges.forEach((exchange) => {
          if (exchange) {
            set.add(exchange);
          }
        });
      } else if (Array.isArray(asset.sources)) {
        asset.sources.forEach((source) => {
          if (source.exchange) {
            set.add(source.exchange);
          }
        });
      }
    });
    return Array.from(set).sort((a, b) => a.localeCompare(b));
  }, [assets]);

  // Memoize filtered and sorted assets
  const filteredAssets = useMemo(() => {
    let filtered = showSmallAssets 
      ? assets 
      : assets.filter(asset => asset.value_usd > 0.01); // Show only assets > $0.01

    if (assetTypeFilter.length > 0) {
      filtered = filtered.filter(asset => assetTypeFilter.includes(deriveAssetType(asset)));
    }

    if (minValueFilter > 0) {
      filtered = filtered.filter(asset => asset.value_usd >= minValueFilter);
    }

    if (pnlFilter === 'positive') {
      filtered = filtered.filter(asset => asset.pnl >= 0);
    } else if (pnlFilter === 'negative') {
      filtered = filtered.filter(asset => asset.pnl < 0);
    }

    // Apply search filter
    if (debouncedSearchTerm) {
      filtered = filtered.filter(asset =>
        asset.symbol.toLowerCase().includes(debouncedSearchTerm.toLowerCase())
      );
    }

    // Apply exchange filter
    if (exchangeFilter) {
      const normalizedFilter = exchangeFilter.toLowerCase();
      filtered = filtered.filter((asset) => {
        const primary = (asset.exchange || '').toLowerCase();
        if (primary === normalizedFilter) {
          return true;
        }
        if (Array.isArray(asset.exchanges) && asset.exchanges.some((exchange) => (exchange || '').toLowerCase() === normalizedFilter)) {
          return true;
        }
        if (Array.isArray(asset.sources) && asset.sources.some((source) => (source.exchange || '').toLowerCase() === normalizedFilter)) {
          return true;
        }
        return false;
      });
    }

    // Apply sorting
    filtered = [...filtered].sort((a, b) => {
      let aVal: number, bVal: number;
      
      switch (sortBy) {
        case 'symbol':
          return sortOrder === 'asc' 
            ? a.symbol.localeCompare(b.symbol)
            : b.symbol.localeCompare(a.symbol);
        case 'value':
          aVal = a.value_usd;
          bVal = b.value_usd;
          break;
        case 'pnl':
          aVal = a.pnl;
          bVal = b.pnl;
          break;
        case 'pnl_percent':
          aVal = a.pnl_percent;
          bVal = b.pnl_percent;
          break;
        case 'amount':
          aVal = a.amount;
          bVal = b.amount;
          break;
        default:
          return 0;
      }
      
      if (sortOrder === 'asc') {
        return aVal - bVal;
      } else {
        return bVal - aVal;
      }
    });

    return filtered;
  }, [assets, showSmallAssets, debouncedSearchTerm, exchangeFilter, sortBy, sortOrder, assetTypeFilter, deriveAssetType, minValueFilter, pnlFilter]);

  // Memoize total calculations
  const totalValue = useMemo(() => {
    return assets.reduce((sum, asset) => sum + asset.value_usd, 0);
  }, [assets]);

  const totalPnl = useMemo(() => {
    return assets.reduce((sum, asset) => sum + asset.pnl, 0);
  }, [assets]);

  // Memoize chart data
  const assetChartData = useMemo(() => {
    return Object.entries(allocationData?.by_asset || {}).map(([name, value]) => ({
      name,
      value,
      percentage: value.toFixed(1)
    }));
  }, [allocationData?.by_asset]);

  const exchangeChartData = useMemo(() => {
    return Object.entries(allocationData?.by_exchange || {}).map(([name, value]) => ({
      name,
      value,
      percentage: value.toFixed(1)
    }));
  }, [allocationData?.by_exchange]);

  const COLORS = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe'];

  // Export to CSV
  const handleExportCSV = useCallback(() => {
    const headers = ['Symbol', 'Amount', 'Value (USD)', 'Value (PLN)', 'P&L', 'P&L %', 'Exchange'];
    const rows = filteredAssets.map(asset => [
      asset.symbol,
      asset.amount.toFixed(6),
      asset.value_usd.toFixed(2),
      asset.value_pln.toFixed(2),
      asset.pnl.toFixed(2),
      asset.pnl_percent.toFixed(2),
      asset.exchange
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `portfolio-export-${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  }, [filteredAssets]);

  // Initial fetch on mount - only once
  useEffect(() => {
    fetchData(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty deps - only fetch once on mount, fetchData is stable

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      const success = await fetchData(true);
      showToast(success ? 'Portfolio data refreshed' : 'Portfolio refreshed with partial data', success ? 'success' : 'warning');
    } catch (error) {
      logger.error('Portfolio: manual refresh failed', error);
      showToast('Failed to refresh portfolio data', 'error');
    } finally {
      setRefreshing(false);
    }
  }, [fetchData, showToast]);

  const handleSyncTrades = useCallback(async () => {
    setSyncing(true);
    try {
      const result = await portfolioService.checkExchangeSync(200);
      const newTrades = result?.summary?.new_trades ?? 0;
      if (newTrades > 0) {
        showToast(`${newTrades} new trade${newTrades === 1 ? '' : 's'} detected`, 'success');
      } else {
        showToast('No new trades detected', 'info');
      }
    } catch (error) {
      logger.error('Portfolio: sync trades failed', error);
      showToast('Failed to check exchanges for new trades', 'error');
    } finally {
      setSyncing(false);
    }
  }, [showToast]);

  const formattedLastUpdate = useMemo(() => {
    if (!lastUpdate) return '—';
    return lastUpdate.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }, [lastUpdate]);

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
      <Box sx={{ 
        display: 'flex', 
        flexDirection: { xs: 'column', sm: 'row' },
        justifyContent: 'space-between', 
        alignItems: { xs: 'flex-start', sm: 'center' },
        gap: { xs: 2, sm: 0 },
        mb: { xs: 3, md: 4 } 
      }}>
        <Box>
          <Typography 
            variant="h1" 
            component="h1"
            sx={{ 
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              mb: 1,
              fontSize: { xs: '1.75rem', sm: '2rem', md: '2.5rem' }
            }}
          >
            Portfolio Overview
          </Typography>
          <Typography 
            variant="h5" 
            color="text.secondary"
            sx={{ fontSize: { xs: '0.875rem', sm: '1rem', md: '1.25rem' } }}
          >
            Detailed asset allocation and performance
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Stack direction="row" spacing={1}>
            <Tooltip title="Refresh balances">
              <span>
                <Button
                  variant="outlined"
                  startIcon={refreshing ? <CircularProgress size={18} /> : <Refresh />}
                  onClick={handleRefresh}
                  disabled={refreshing || syncing}
                  sx={{ textTransform: 'none', minWidth: 120 }}
                >
                  Refresh
                </Button>
              </span>
            </Tooltip>
            <Tooltip title="Check exchanges for new trades">
              <span>
                <Button
                  variant="outlined"
                  startIcon={syncing ? <CircularProgress size={18} /> : <Sync />}
                  onClick={handleSyncTrades}
                  disabled={refreshing || syncing}
                  sx={{ textTransform: 'none', minWidth: 120 }}
                >
                  Sync
                </Button>
              </span>
            </Tooltip>
          </Stack>
          <Tooltip title="Export holdings to CSV">
            <span>
              <Button
                variant="contained"
                startIcon={<Download />}
                onClick={handleExportCSV}
                sx={{ textTransform: 'none' }}
              >
                Export CSV
              </Button>
            </span>
          </Tooltip>
        </Box>
        {lastUpdate && (
          <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
            Updated: {formattedLastUpdate}
          </Typography>
        )}
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert 
          severity="warning" 
          sx={{ mb: 4 }}
          action={
            <IconButton
              aria-label="retry"
              color="inherit"
              size="small"
              onClick={() => fetchData(true)}
            >
              <Refresh />
            </IconButton>
          }
        >
          <AlertTitle>Warning</AlertTitle>
          {error}
        </Alert>
      )}

      {/* Summary Cards */}
      <Box component="section" aria-labelledby="portfolio-summary-cards">
        <Typography id="portfolio-summary-cards" variant="h2" sx={srOnlyStyles}>
          Portfolio summary metrics
        </Typography>
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' },
            gap: { xs: 2, sm: 3, md: 4 },
            mb: { xs: 3, sm: 4, md: 5 }
          }}
        >
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <AccountBalance sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6" component="h3" color="text.secondary">
                  Total Value
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 700, mb: 1, fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' } }}>
                {formatCurrency(totalValue)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {formatCurrency(totalValue * 4, 'PLN')}
              </Typography>
            </CardContent>
          </Card>

          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                {totalPnl >= 0 ? (
                  <TrendingUp sx={{ mr: 1, color: 'success.main' }} />
                ) : (
                  <TrendingDown sx={{ mr: 1, color: 'error.main' }} />
                )}
                <Typography variant="h6" component="h3" color="text.secondary">
                  Total P&L
                </Typography>
              </Box>
              <Typography 
                variant="h4" 
                sx={{ 
                  fontWeight: 700, 
                  mb: 1,
                  fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' },
                  color: totalPnl >= 0 ? 'success.main' : 'error.main'
                }}
              >
                {formatCurrency(totalPnl)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {totalValue > 0 ? formatPercentage((totalPnl / totalValue) * 100) : '0.00%'}
              </Typography>
            </CardContent>
          </Card>

          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <ShowChart sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6" component="h3" color="text.secondary">
                  Total Assets
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 700, mb: 1, fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' } }}>
                {assets.length}
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
                <Typography variant="h6" component="h3" color="text.secondary">
                  Exchanges
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 700, mb: 1, fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' } }}>
                {exchangeOptions.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Connected platforms
              </Typography>
            </CardContent>
          </Card>
        </Box>
      </Box>

      <Stack
        direction="row"
        spacing={1.5}
        sx={{ mb: { xs: 3, sm: 4 }, flexWrap: 'wrap', alignItems: 'center' }}
        aria-label="Portfolio quick summary chips"
      >
        <Chip
          icon={<AccountBalance fontSize="small" />}
          label={`Total ${formatCurrency(totalValue)}`}
          variant="outlined"
        />
        <Chip
          icon={(totalPnl >= 0 ? <TrendingUp fontSize="small" /> : <TrendingDown fontSize="small" />)}
          label={`P&L ${formatCurrency(totalPnl)}`}
          color={totalPnl >= 0 ? 'success' : 'warning'}
          variant="outlined"
        />
        <Chip
          icon={<ShowChart fontSize="small" />}
          label={`${assets.length} assets`}
          variant="outlined"
        />
      </Stack>

      {/* Charts with Tabs */}
      <Card sx={{ mb: { xs: 3, sm: 4, md: 5 } }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs 
            value={allocationView} 
            onChange={(e, newValue) => setAllocationView(newValue)}
            variant="scrollable"
            scrollButtons="auto"
          >
            <Tab label="Traditional Charts" value="traditional" />
            <Tab label="Treemap View" value="treemap" />
            <Tab label="Sunburst View" value="sunburst" />
          </Tabs>
        </Box>

        {allocationView === 'traditional' && (
          <Box
            component="section"
            aria-labelledby="portfolio-allocation-traditional"
            sx={{ 
              display: 'grid', 
              gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' },
              gap: { xs: 2, sm: 3, md: 4 }, 
              p: { xs: 2, sm: 3, md: 4 }
            }}
          >
            <Typography id="portfolio-allocation-traditional" variant="h3" sx={srOnlyStyles}>
              Traditional allocation charts
            </Typography>
            <Box>
              <Typography variant="h6" component="h4" sx={{ mb: { xs: 2, sm: 3 }, fontWeight: 600 }}>
                Asset Allocation
              </Typography>
              <Box sx={{ height: { xs: 250, sm: 300, md: 400 } }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart role="img" aria-label="Portfolio allocation by asset">
                    <Pie
                      data={assetChartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percentage }) => `${name} ${percentage}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {assetChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <RechartsTooltip 
                      contentStyle={{ fontSize: 14 }}
                      formatter={(value: number) => [formatCurrency(value), 'Value']}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </Box>
            </Box>

            <Box>
              <Typography variant="h6" component="h4" sx={{ mb: { xs: 2, sm: 3 }, fontWeight: 600 }}>
                Exchange Distribution
              </Typography>
              <Box sx={{ height: { xs: 250, sm: 300, md: 400 } }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={exchangeChartData} role="img" aria-label="Portfolio allocation by exchange">
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis 
                      dataKey="name" 
                      stroke="#b0b0b0"
                      tick={{ fontSize: 12 }}
                    />
                    <YAxis 
                      stroke="#b0b0b0"
                      tick={{ fontSize: 12 }}
                      tickFormatter={(value) => `${value}%`}
                    />
                    <RechartsTooltip 
                      contentStyle={{ fontSize: 14 }}
                      formatter={(value: number) => [`${value.toFixed(1)}%`, 'Allocation']}
                    />
                    <Bar dataKey="value" fill="#667eea" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </Box>
          </Box>
        )}

        {allocationView === 'treemap' && (
          <Box
            component="section"
            aria-label="Treemap representation of portfolio allocation"
            sx={{ p: { xs: 2, sm: 3, md: 4 } }}
          >
            <Suspense fallback={<ChartPlaceholder height={isSmallScreen ? 360 : 600} />}>
              <TreemapAllocation
                assets={assets}
                width={isSmallScreen ? 320 : 820}
                height={isSmallScreen ? 360 : 600}
                onAssetClick={(asset) => {
                  setSelectedAsset(asset);
                  setDrawerOpen(true);
                }}
              />
            </Suspense>
          </Box>
        )}

        {allocationView === 'sunburst' && (
          <Box
            component="section"
            aria-label="Sunburst representation of portfolio allocation"
            sx={{ p: { xs: 2, sm: 3, md: 4 } }}
          >
            <Suspense fallback={<ChartPlaceholder height={isSmallScreen ? 360 : 560} />}>
              <SunburstComposition
                assets={assets}
                width={isSmallScreen ? 320 : 560}
                height={isSmallScreen ? 360 : 560}
                onSegmentClick={(path) => {
                  logger.log('Segment clicked:', path);
                }}
              />
            </Suspense>
          </Box>
        )}
      </Card>

      {/* Assets Table */}
      <Card>
        <CardContent sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
          <Box sx={{ 
            display: 'flex', 
            flexDirection: { xs: 'column', sm: 'row' },
            justifyContent: 'space-between', 
            alignItems: { xs: 'flex-start', sm: 'center' },
            gap: { xs: 2, sm: 0 },
            mb: { xs: 2, sm: 3 }
          }}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Asset Details
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Stack direction="row" spacing={1} alignItems="center">
              <Typography variant="body2" color="text.secondary" sx={{ display: { xs: 'none', sm: 'block' } }}>
                Show small assets
              </Typography>
              <IconButton
                onClick={() => setShowSmallAssets(!showSmallAssets)}
                color="primary"
                size="small"
                sx={{
                  minWidth: { xs: 40, sm: 'auto' },
                  minHeight: { xs: 40, sm: 'auto' }
                }}
                aria-label="toggle small assets"
              >
                {showSmallAssets ? <Visibility /> : <VisibilityOff />}
              </IconButton>
            </Stack>
            </Box>
          </Box>

          {/* Filters and Search */}
          <Box sx={{ 
            display: 'grid', 
            gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' },
            gap: { xs: 2, sm: 2 },
            mb: { xs: 2, sm: 3 }
          }}>
            <TextField
              size="small"
              placeholder="Search assets..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
                endAdornment: searchTerm && (
                  <InputAdornment position="end">
                    <IconButton size="small" onClick={() => setSearchTerm('')}>
                      <Clear />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
            <FormControl size="small">
              <InputLabel>Exchange</InputLabel>
              <Select
                value={exchangeFilter}
                label="Exchange"
                onChange={(e) => setExchangeFilter(e.target.value)}
              >
                <MenuItem value="">All Exchanges</MenuItem>
                {exchangeOptions.map((exchange) => (
                  <MenuItem key={exchange} value={exchange}>
                    {exchange}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl size="small">
              <InputLabel>Sort By</InputLabel>
              <Select
                value={sortBy}
                label="Sort By"
                onChange={(e) => setSortBy(e.target.value)}
              >
                <MenuItem value="value">Value</MenuItem>
                <MenuItem value="symbol">Symbol</MenuItem>
                <MenuItem value="pnl">P&L</MenuItem>
                <MenuItem value="pnl_percent">P&L %</MenuItem>
                <MenuItem value="amount">Amount</MenuItem>
              </Select>
            </FormControl>
          </Box>

          <Stack
            direction={{ xs: 'column', md: 'row' }}
            spacing={2}
            sx={{ mb: { xs: 2, sm: 3 } }}
          >
            <Box>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                Asset Type
              </Typography>
              <ToggleButtonGroup
                value={assetTypeFilter}
                onChange={(_, value) => setAssetTypeFilter(value)}
                size="small"
                color="primary"
                aria-label="asset type filter"
              >
                <ToggleButton value="crypto">Crypto</ToggleButton>
                <ToggleButton value="stock">Stocks</ToggleButton>
                <ToggleButton value="stablecoin">Stablecoin</ToggleButton>
                <ToggleButton value="other">Other</ToggleButton>
              </ToggleButtonGroup>
            </Box>

            <Box sx={{ minWidth: 180 }}>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                Minimum Value (USD)
              </Typography>
              <Stack direction="row" spacing={2} alignItems="center">
                <Slider
                  min={0}
                  max={1000}
                  step={10}
                  value={Math.min(Math.max(minValueFilter, 0), 1000)}
                  onChange={(_, value) => setMinValueFilter(Array.isArray(value) ? value[0] : value)}
                  valueLabelDisplay="auto"
                  aria-label="minimum value filter"
                />
                <Typography variant="body2" sx={{ minWidth: 64, textAlign: 'right' }}>
                  {formatCurrency(minValueFilter)}
                </Typography>
              </Stack>
            </Box>

            <FormControl size="small" sx={{ minWidth: 160 }}>
              <InputLabel>P&L Filter</InputLabel>
              <Select
                value={pnlFilter}
                label="P&L Filter"
                onChange={(e) => setPnlFilter(e.target.value as typeof pnlFilter)}
              >
                <MenuItem value="all">All</MenuItem>
                <MenuItem value="positive">Profitable</MenuItem>
                <MenuItem value="negative">Losing</MenuItem>
              </Select>
            </FormControl>
          </Stack>
          
          {/* Sort Order Toggle */}
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
            <Tooltip title={sortOrder === 'desc' ? 'Sort Descending' : 'Sort Ascending'}>
              <IconButton
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                size="small"
                color="primary"
              >
                {sortOrder === 'desc' ? <ArrowDownward /> : <ArrowUpward />}
              </IconButton>
            </Tooltip>
          </Box>

          {filtering && (
            <LinearProgress sx={{ mb: 2 }} aria-label="Applying filters" />
          )}

          {!isSmallScreen ? (
            <TableContainer 
              component={Paper} 
              sx={{ 
                backgroundColor: 'transparent',
                maxHeight: { xs: '60vh', md: 'none' },
                overflowX: 'auto',
                scrollBehavior: 'smooth',
                '& .MuiTable-root': {
                  minWidth: { xs: 800, sm: 'auto' }
                }
              }}
            >
              <Table aria-label="Portfolio asset holdings">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ 
                      position: { xs: 'sticky', md: 'static' }, 
                      left: { xs: 0, md: 'auto' }, 
                      zIndex: { xs: 1, md: 'auto' }, 
                      backgroundColor: { xs: 'background.paper', md: 'transparent' },
                      py: { xs: 1.5, md: 2 }
                    }}>Asset</TableCell>
                    <TableCell align="right" sx={{ display: { xs: 'none', md: 'table-cell' } }}>Amount</TableCell>
                    <TableCell align="right">Value (USD)</TableCell>
                    <TableCell align="right" sx={{ display: { xs: 'none', lg: 'table-cell' } }}>Value (PLN)</TableCell>
                    <TableCell align="right">P&L</TableCell>
                    <TableCell align="right" sx={{ display: { xs: 'none', sm: 'table-cell' } }}>P&L %</TableCell>
                    <TableCell align="center">Exchange</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredAssets.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} align="center" sx={{ py: 4, display: { xs: 'table-cell', md: 'table-cell' } }}>
                        <Typography variant="body1" color="text.secondary">
                          {assets.length === 0 
                            ? 'No assets found. Make sure your API keys are configured correctly.'
                            : `No assets shown. ${assets.length} asset(s) hidden (value < $0.01). Toggle "Show small assets" to view them.`
                          }
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredAssets.map((asset, index) => {
                      const pnlValue = typeof asset.pnl === 'number' && Number.isFinite(asset.pnl) ? asset.pnl : null;
                      const pnlPercent = typeof asset.pnl_percent === 'number' && Number.isFinite(asset.pnl_percent)
                        ? asset.pnl_percent
                        : null;
                      const exchangeList = getExchangeList(asset);
                      const hasMultipleExchanges = exchangeList.length > 1;
                      const primaryExchange = exchangeList[0] || asset.exchange || '—';
                      const normalizedPrimary = primaryExchange.toLowerCase();
                      const isAggregateExchange =
                        hasMultipleExchanges || normalizedPrimary === 'multi' || normalizedPrimary === 'multiple';
                      const chipLabel = hasMultipleExchanges
                        ? `${exchangeList.length} exchanges`
                        : normalizedPrimary === 'multi'
                        ? 'Multi'
                        : primaryExchange;
                      const exchangeChipStyles = isAggregateExchange
                        ? {
                            borderColor: 'divider',
                            color: 'text.primary',
                            backgroundColor: 'rgba(148, 163, 184, 0.18)',
                          }
                        : {
                            backgroundColor: getExchangeColor(primaryExchange),
                            color: '#fff',
                          };
                      const exchangeTooltip = buildSourceTooltipContent(asset);
                      return (
                    <TableRow 
                      key={index} 
                      hover
                      onClick={() => {
                        setSelectedAsset(asset);
                        setDrawerOpen(true);
                      }}
                      sx={{ cursor: 'pointer' }}
                    >
                      <TableCell sx={{ 
                        position: { xs: 'sticky', md: 'static' }, 
                        left: { xs: 0, md: 'auto' }, 
                        zIndex: { xs: 1, md: 'auto' }, 
                        backgroundColor: { xs: 'background.paper', md: 'transparent' },
                        py: { xs: 1.5, md: 2 }
                      }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Avatar sx={{ width: { xs: 24, sm: 32 }, height: { xs: 24, sm: 32 }, fontSize: { xs: '0.8rem', sm: '1rem' } }}>
                            {getAssetIcon(asset.symbol)}
                          </Avatar>
                          <Typography variant="body1" sx={{ fontWeight: 600, fontSize: { xs: '0.875rem', sm: '1rem' } }}>
                            {asset.symbol}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="right" sx={{ display: { xs: 'none', md: 'table-cell' } }}>
                        <Typography variant="body1" sx={{ fontFamily: 'monospace', fontSize: { xs: '0.875rem', sm: '1rem' } }}>
                          {formatNumber(asset.amount, 6)}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body1" sx={{ fontWeight: 600, fontSize: { xs: '0.875rem', sm: '1rem' } }}>
                          {formatCurrency(asset.value_usd)}
                        </Typography>
                      </TableCell>
                      <TableCell align="right" sx={{ display: { xs: 'none', lg: 'table-cell' } }}>
                        <Typography variant="body1" sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}>
                          {formatCurrency(asset.value_pln, 'PLN')}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography 
                          variant="body1" 
                          sx={{ 
                            fontWeight: 600,
                            color: pnlValue === null ? 'text.primary' : (pnlValue >= 0 ? 'success.main' : 'error.main'),
                            fontSize: { xs: '0.875rem', sm: '1rem' }
                          }}
                        >
                          {formatCurrency(asset.pnl)}
                        </Typography>
                      </TableCell>
                      <TableCell align="right" sx={{ display: { xs: 'none', sm: 'table-cell' } }}>
                        <Chip
                          label={formatPercentage(pnlPercent ?? undefined)}
                          color={
                            pnlPercent === null
                              ? 'default'
                              : pnlPercent >= 0
                              ? 'success'
                              : 'error'
                          }
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Tooltip title={exchangeTooltip} arrow placement="top">
                          <Chip
                            label={chipLabel}
                            sx={{
                              borderRadius: '12px',
                              fontWeight: 600,
                              fontSize: { xs: '0.7rem', sm: '0.75rem' },
                              ...exchangeChipStyles,
                            }}
                            size="small"
                            variant={isAggregateExchange ? 'outlined' : 'filled'}
                          />
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                    );})
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Stack spacing={2}>
              {filteredAssets.length === 0 ? (
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="body1" color="text.secondary">
                      {assets.length === 0 
                        ? 'No assets found. Make sure your API keys are configured correctly.'
                        : `No assets shown. ${assets.length} asset(s) hidden (value < $0.01). Toggle "Show small assets" to view them.`
                      }
                    </Typography>
                  </CardContent>
                </Card>
              ) : (
                filteredAssets.map((asset, index) => {
                  const pnlValue = typeof asset.pnl === 'number' && Number.isFinite(asset.pnl) ? asset.pnl : null;
                  const pnlPercent = typeof asset.pnl_percent === 'number' && Number.isFinite(asset.pnl_percent)
                    ? asset.pnl_percent
                    : null;
                  const exchangeList = getExchangeList(asset);
                  const hasMultipleExchanges = exchangeList.length > 1;
                  const primaryExchange = exchangeList[0] || asset.exchange || '—';
                  const normalizedPrimary = primaryExchange.toLowerCase();
                  const isAggregateExchange =
                    hasMultipleExchanges || normalizedPrimary === 'multi' || normalizedPrimary === 'multiple';
                  const chipLabel = hasMultipleExchanges
                    ? `${exchangeList.length} exchanges`
                    : normalizedPrimary === 'multi'
                    ? 'Multi'
                    : primaryExchange;
                  const exchangeChipStyles = isAggregateExchange
                    ? {
                        borderColor: 'divider',
                        color: 'text.primary',
                        backgroundColor: 'rgba(148, 163, 184, 0.18)',
                      }
                    : {
                        backgroundColor: getExchangeColor(primaryExchange),
                        color: '#fff',
                      };
                  const exchangeTooltip = buildSourceTooltipContent(asset);
                  return (
                  <Card
                    key={`${asset.symbol}-${index}`}
                    variant="outlined"
                    sx={{ cursor: 'pointer' }}
                    onClick={() => {
                      setSelectedAsset(asset);
                      setDrawerOpen(true);
                    }}
                    aria-label={`View details for ${asset.symbol}`}
                  >
                    <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Stack direction="row" spacing={1} alignItems="center">
                          <Avatar sx={{ width: 28, height: 28, fontSize: '0.85rem' }}>
                            {getAssetIcon(asset.symbol)}
                          </Avatar>
                          <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                            {asset.symbol}
                          </Typography>
                          <Tooltip title={exchangeTooltip} arrow placement="top">
                            <Chip
                              label={chipLabel}
                              size="small"
                              sx={{
                                borderRadius: '12px',
                                fontWeight: 600,
                                ...exchangeChipStyles,
                              }}
                              variant={isAggregateExchange ? 'outlined' : 'filled'}
                            />
                          </Tooltip>
                        </Stack>
                        <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                          {formatCurrency(asset.value_usd)}
                        </Typography>
                      </Box>
                      <Stack direction="row" spacing={2} sx={{ fontSize: '0.85rem' }}>
                        <Typography color="text.secondary">
                          Amount: <Box component="span" sx={{ fontWeight: 600 }}>{formatNumber(asset.amount, 4)}</Box>
                        </Typography>
                        <Typography color="text.secondary">
                          P&L:{' '}
                          <Box
                            component="span"
                            sx={{
                              fontWeight: 600,
                              color: pnlValue === null ? 'text.secondary' : (pnlValue >= 0 ? 'success.main' : 'error.main'),
                            }}
                          >
                            {formatCurrency(asset.pnl)}
                          </Box>
                        </Typography>
                        <Typography color="text.secondary">
                          ROI:{' '}
                          <Box
                            component="span"
                            sx={{
                              fontWeight: 600,
                              color: pnlPercent === null ? 'text.secondary' : (pnlPercent >= 0 ? 'success.main' : 'error.main'),
                            }}
                          >
                            {formatPercentage(pnlPercent ?? undefined)}
                          </Box>
                        </Typography>
                      </Stack>
                      {asset.issues && asset.issues.length > 0 && (
                        <Chip
                          label="Data warning"
                          color="warning"
                          size="small"
                          variant="outlined"
                        />
                      )}
                      <Typography variant="body2" color="primary" sx={{ fontWeight: 600 }}>
                        Tap to open details →
                      </Typography>
                    </CardContent>
                  </Card>
                );})
              )}
            </Stack>
          )}

          {!showSmallAssets && assets.length > filteredAssets.length && (
            <Box sx={{ mt: 2, textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                {assets.length - filteredAssets.length} small assets hidden
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Asset Details Drawer */}
      <Suspense fallback={<LinearProgress />}>
        <AssetDetailsDrawer
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          asset={selectedAsset}
        />
      </Suspense>
      <Toast
        open={toast.open}
        message={toast.message}
        severity={toast.severity}
        onClose={hideToast}
      />
    </Box>
  );
};

export default Portfolio;