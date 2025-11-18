import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Box,
  Stack,
  Typography,
  Alert,
  AlertTitle,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Card,
  CardContent,
  Tooltip,
  Button,
  Container,
} from '@mui/material';
import CircularProgress from '@mui/material/CircularProgress';
import { useNavigate } from 'react-router-dom';
import {
  KPIItem,
  SummaryModule,
  AllocationBreakdownData,
  EquityCurveConfig,
  AssetTabData,
  NewsItem,
  WatchItem,
  RecentAlert,
  RoiAnalyticsData,
  DrilldownMetrics,
  FiltersState,
  EquityCurvePoint,
  HeatmapCell,
} from './dashboardV2/types';
import { TimeRange } from '../theme/dashboardTokens';
import { 
  portfolioService, 
  PortfolioSummary,
  PortfolioHistoryPoint,
  Asset as PortfolioAsset,
  PerformanceAnalytics,
} from '../services/portfolioService';
import { logger } from '../utils/logger';
import { SkeletonLoader } from './common/SkeletonLoader';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import { Toast, useToast } from './common/Toast';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import RefreshIcon from '@mui/icons-material/Refresh';
import { useKeyboardShortcuts, COMMON_SHORTCUTS, KeyboardShortcut } from '../hooks/useKeyboardShortcuts';
import { KeyboardShortcutsDialog } from './common/KeyboardShortcutsDialog';
import { OnboardingTour, useOnboardingStatus } from './common/OnboardingTour';
import { dashboardOnboardingSteps } from '../config/onboardingSteps';
import { QuickActionsToolbar } from './common/QuickActionsToolbar';
import { notificationsService } from '../services/notificationsService';

// Lazy load dashboard sub-components for better code splitting
const GlobalStatusBar = React.lazy(() => import('./dashboardV2/GlobalStatusBar').then(module => ({ default: module.GlobalStatusBar })));
const PortfolioOverview = React.lazy(() => import('./dashboardV2/PortfolioOverview').then(module => ({ default: module.PortfolioOverview })));
const AssetTabs = React.lazy(() => import('./dashboardV2/AssetTabs').then(module => ({ default: module.AssetTabs })));
const WatchlistSection = React.lazy(() => import('./dashboardV2/WatchlistSection').then(module => ({ default: module.WatchlistSection })));
const RoiAnalytics = React.lazy(() => import('./dashboardV2/RoiAnalytics').then(module => ({ default: module.RoiAnalytics })));
const FiltersPanel = React.lazy(() => import('./dashboardV2/FiltersPanel').then(module => ({ default: module.FiltersPanel })));
const RiskAlertsPanel = React.lazy(() => import('./dashboardV2/RiskAlertsPanel').then(module => ({ default: module.RiskAlertsPanel })));
const RebalancingSuggestionsPanel = React.lazy(() => import('./dashboardV2/RebalancingSuggestionsPanel').then(module => ({ default: module.RebalancingSuggestionsPanel })));
const HealthScorePanel = React.lazy(() => import('./dashboardV2/HealthScorePanel').then(module => ({ default: module.HealthScorePanel })));

const defaultFilters: FiltersState = {
  assetType: ['Stocks', 'Crypto'],
  sector: [],
  region: [],
  tags: [],
  stablecoinsOnly: false,
  viewMode: 'table',
  timeRange: '24h',
};

const FILTER_STORAGE_KEY = 'dashboard:filters';
const VALID_TIME_RANGES: TimeRange[] = ['24h', '7d', 'MTD', 'YTD', 'Max'];

const NEW_TRADES_STORAGE_KEY = 'portfolio:new-trades';
const NEW_TRADES_EVENT = 'portfolio:new-trades';

const normalizeString = (value?: string, mode: 'upper' | 'lower' = 'upper') => {
  const normalized = (value ?? '').trim();
  return mode === 'upper' ? normalized.toUpperCase() : normalized.toLowerCase();
};

const normalizeNumber = (value: unknown) => {
  const numeric = Number(value ?? 0);
  if (!Number.isFinite(numeric)) {
    return 0;
  }
  return Number(numeric.toFixed(8));
};

const normalizeTimestamp = (value?: string) => {
  try {
    return value ? new Date(value).toISOString() : new Date().toISOString();
  } catch (error) {
    return new Date().toISOString();
  }
};

const buildTradeKey = (
  exchange?: string,
  symbol?: string,
  side?: string,
  amount?: unknown,
  price?: unknown,
  timestamp?: string
) => {
  const normalizedSymbol = normalizeString(symbol);
  const normalizedExchange = normalizeString(exchange);
  if (!normalizedSymbol || !normalizedExchange) {
    return null;
  }

  const iso = normalizeTimestamp(timestamp).slice(0, 19);
  return [
    normalizedExchange,
    normalizedSymbol,
    normalizeString(side, 'lower'),
    normalizeNumber(amount),
    normalizeNumber(price),
    iso,
  ].join('|');
};

const loadStoredFilters = (): FiltersState => {
  if (typeof window === 'undefined') {
    return defaultFilters;
  }

  try {
    const raw = window.localStorage.getItem(FILTER_STORAGE_KEY);
    if (!raw) {
      return defaultFilters;
    }

    const parsed = JSON.parse(raw);
    return {
      ...defaultFilters,
      ...parsed,
      assetType:
        Array.isArray(parsed?.assetType) && parsed.assetType.length > 0
          ? parsed.assetType
          : defaultFilters.assetType,
      sector: Array.isArray(parsed?.sector) ? parsed.sector : defaultFilters.sector,
      region: Array.isArray(parsed?.region) ? parsed.region : defaultFilters.region,
      tags: Array.isArray(parsed?.tags) ? parsed.tags : defaultFilters.tags,
      stablecoinsOnly:
        typeof parsed?.stablecoinsOnly === 'boolean'
          ? parsed.stablecoinsOnly
          : defaultFilters.stablecoinsOnly,
      viewMode:
        parsed?.viewMode === 'cards' || parsed?.viewMode === 'chart'
          ? parsed.viewMode
          : defaultFilters.viewMode,
      timeRange:
        parsed?.timeRange && VALID_TIME_RANGES.includes(parsed.timeRange)
          ? parsed.timeRange
          : defaultFilters.timeRange,
    };
    } catch (error) {
      logger.warn('Failed to load stored dashboard filters', error);
      return defaultFilters;
    }
};

const palette = [
  '#2563EB',
  '#22C55E',
  '#7C3AED',
  '#F97316',
  '#0EA5E9',
  '#F59E0B',
  '#10B981',
];

const benchmarkSymbolMap: Record<string, string> = {
  sp500: 'SPY',
  btc: 'BTC',
  eth: 'ETH',
};

const resolveDaysForRangeValue = (range: TimeRange): number => {
  const now = new Date();
  switch (range) {
    case '24h':
      return 2;
    case '7d':
      return 7;
    case 'MTD':
      return now.getDate();
    case 'YTD': {
      const start = new Date(now.getFullYear(), 0, 1);
      const diffDays = Math.floor((now.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
      return Math.max(1, diffDays + 1);
    }
    case 'Max':
      return 365 * 5;
    default:
      return 30;
  }
};

const stablecoinSymbols = new Set(['USDT', 'USDC', 'BUSD', 'DAI', 'TUSD', 'USDP', 'EUR', 'USD', 'USDD']);

const stockSectorMap: Record<string, { sector: string; region: string; tags: string[] }> = {
  AAPL: { sector: 'Technology', region: 'North America', tags: ['Blue Chip', 'AI'] },
  MSFT: { sector: 'Technology', region: 'North America', tags: ['Blue Chip', 'Cloud'] },
  GOOGL: { sector: 'Technology', region: 'North America', tags: ['Growth', 'AI'] },
  TSLA: { sector: 'Consumer', region: 'North America', tags: ['Growth', 'EV'] },
  BP: { sector: 'Energy', region: 'Europe', tags: ['Dividend', 'Blue Chip'] },
  RIG: { sector: 'Energy', region: 'North America', tags: ['Energy', 'Value'] },
  CRCL: { sector: 'Healthcare', region: 'North America', tags: ['Healthcare'] },
};

const formatCurrency = (value: number | undefined, currency: string = 'USD') =>
  new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    maximumFractionDigits: value && value >= 1000 ? 0 : 2,
  }).format(value ?? 0);

const sanitizeNumber = (value: number | undefined) =>
  Number.isFinite(value) ? (value as number) : 0;

type QuickInsight = {
  id: string;
  label: string;
  primary: string;
  helper?: string;
  delta?: number;
  positive?: boolean;
  icon?: React.ReactNode;
  onClick?: () => void;
  severity?: 'warning' | 'info';
};

type AssetChangeSummary = {
  symbol: string;
  direction: 'up' | 'down';
  deltaPercent: number;
  deltaValue: number;
};

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false); // Changed to false - manual loading only
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [assets, setAssets] = useState<PortfolioAsset[]>([]);
  const [history, setHistory] = useState<PortfolioHistoryPoint[]>([]);
  const [previousHistory, setPreviousHistory] = useState<PortfolioHistoryPoint[]>([]);
  const [filters, setFilters] = useState<FiltersState>(() => loadStoredFilters());
  const [timeRange, setTimeRange] = useState<TimeRange>(filters.timeRange);
  const [historyDays, setHistoryDays] = useState<number>(resolveDaysForRangeValue(filters.timeRange));
  const [equityFilter, setEquityFilter] = useState<EquityCurveConfig['filter']>('total');
  const [benchmarks, setBenchmarks] = useState([
    { id: 'sp500', label: 'S&P 500', color: '#F97316', active: true },
    { id: 'btc', label: 'BTC', color: '#FACC15', active: false },
    { id: 'eth', label: 'ETH', color: '#A855F7', active: false },
  ]);
  const [watchlistSymbols, setWatchlistSymbols] = useState<string[]>([]);
  const [watchlistMap, setWatchlistMap] = useState<Record<string, WatchItem>>({});
  const [priceAlerts, setPriceAlerts] = useState<any[]>([]);
  const [tradeSyncSummary, setTradeSyncSummary] = useState<{ count: number; exchanges: string[]; trades: any[] } | null>(null);
  const [selectedDrilldown, setSelectedDrilldown] = useState<string>('');
  const [assetHistory, setAssetHistory] = useState<Record<string, Array<{ date: string; close: number }>>>({});
  const [benchmarkSeries, setBenchmarkSeries] = useState<
    Record<string, { days: number; series: Array<{ date: string; normalized_value?: number; value?: number }> }>
  >({});
  const [performanceAnalytics, setPerformanceAnalytics] = useState<PerformanceAnalytics | null>(null);
  const [newsMap, setNewsMap] = useState<Record<string, AssetTabData['news']>>({});
  const [changeHighlights, setChangeHighlights] = useState<Record<string, AssetChangeSummary>>({});
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [heatmapByType, setHeatmapByType] = useState<{ stocks: HeatmapCell[]; crypto: HeatmapCell[] }>({
    stocks: [],
    crypto: [],
  });
  const [riskOverview, setRiskOverview] = useState<{ score: number; level?: string; timestamp?: string } | null>(null);
  // new local state for warnings extracted from backend summary
  const summaryWarnings = useMemo(() => summary?.warnings ?? [], [summary?.warnings]);
  const { toast, showToast, hideToast } = useToast();
  const [migrationStatus, setMigrationStatus] = useState<{
    all_migrated: boolean;
    total_items: number;
    migration_complete: boolean;
  } | null>(null);
  const [showMigrationBanner, setShowMigrationBanner] = useState(false);
  const [shortcutsDialogOpen, setShortcutsDialogOpen] = useState(false);
  const onboardingCompleted = useOnboardingStatus('dashboard_onboarding_completed');
  const [onboardingTourOpen, setOnboardingTourOpen] = useState(false);
  const formatPercent = useCallback(
    (value: number | undefined) =>
      Number.isFinite(value) ? `${value! >= 0 ? '+' : ''}${value!.toFixed(2)}%` : '—',
    []
  );
  const assetsRef = useRef<PortfolioAsset[]>([]);
  const shouldSummarizeChangesRef = useRef(false);
  const changeHighlightsRef = useRef<Record<string, AssetChangeSummary>>({});
  const refreshInProgressRef = useRef(false);
  const previousTimeRangeRef = useRef<TimeRange | null>(null); // Initialize with null to trigger first fetch
  const previousHistoryDaysRef = useRef<number | null>(null); // Track previous historyDays to prevent loops
  
  // Check if user is authenticated before making requests
  // Use ref to track auth state and prevent loops
  const isAuthenticatedRef = useRef(false);
  const isAuthenticated = portfolioService.isAuthenticated();
  
  // Update ref when auth state changes
  useEffect(() => {
    isAuthenticatedRef.current = isAuthenticated;
    logger.debug('Dashboard: isAuthenticated changed to:', isAuthenticated);
  }, [isAuthenticated]);

  const persistNewTrades = useCallback((trades: any[]) => {
    if (typeof window === 'undefined') {
      return;
    }

    try {
      const now = new Date();
      const cutoff = now.getTime() - 24 * 60 * 60 * 1000;
      const existingRaw = window.localStorage.getItem(NEW_TRADES_STORAGE_KEY);
      const existing: Array<{ key: string; recordedAt: string }> = existingRaw ? JSON.parse(existingRaw) : [];
      const filteredExisting = Array.isArray(existing)
        ? existing.filter((entry) => {
            if (!entry?.key || !entry?.recordedAt) {
              return false;
            }
            const recordedAt = new Date(entry.recordedAt).getTime();
            return Number.isFinite(recordedAt) && recordedAt >= cutoff;
          })
        : [];

      const nextMap = new Map<string, { key: string; recordedAt: string }>(
        filteredExisting.map((entry) => [entry.key, entry])
      );

      (trades ?? []).forEach((trade) => {
        const key = buildTradeKey(
          trade?.exchange,
          trade?.symbol ?? trade?.asset,
          trade?.side,
          trade?.amount,
          trade?.price,
          trade?.timestamp
        );
        if (!key) {
          return;
        }
        nextMap.set(key, { key, recordedAt: now.toISOString() });
      });

      const next = Array.from(nextMap.values());
      window.localStorage.setItem(NEW_TRADES_STORAGE_KEY, JSON.stringify(next));
      window.dispatchEvent(new Event(NEW_TRADES_EVENT));
    } catch (error) {
      logger.debug('Dashboard: failed to persist new trades', error);
    }
  }, []);

  const parsePriceString = useCallback((value: string | undefined) => {
    if (!value) return 0;
    const numeric = Number(value.replace(/[^\d.-]/g, ''));
    return Number.isFinite(numeric) ? numeric : 0;
  }, []);

  const watchlistItems = useMemo<WatchItem[]>(() => {
    if (!watchlistSymbols.length) {
      return [];
    }
    return watchlistSymbols.map((symbol) => {
      const item = watchlistMap[symbol.toUpperCase()];
      if (item) {
        return item;
      }
      return {
        id: symbol,
        label: symbol,
        symbol,
        price: '—',
        change24h: 0,
        volume: '—',
        alertActive: false,
      };
    });
  }, [watchlistMap, watchlistSymbols]);

  const recentAlerts = useMemo<RecentAlert[]>(() => {
    const entries: RecentAlert[] = [];

    if (priceAlerts.length) {
      const sorted = [...priceAlerts].sort((a, b) => {
        const getTime = (entry: any) =>
          new Date(entry?.triggered_at || entry?.updated_at || entry?.created_at || '').getTime();
        return getTime(b) - getTime(a);
      });
      sorted.slice(0, 4).forEach((alert, idx) => {
        const status: RecentAlert['status'] = alert?.triggered ? 'resolved' : alert?.active ? 'new' : 'acknowledged';
        const message =
          alert?.message ||
          `${alert?.symbol ?? 'Asset'} ${alert?.condition === 'below' ? '≤' : '≥'} ${formatCurrency(alert?.price ?? 0)}`;
        entries.push({
          id: alert?.id?.toString?.() ?? `alert-${idx}`,
          message,
          status,
          timestamp: alert?.triggered_at || alert?.updated_at || alert?.created_at || '',
        });
      });
    }

    if (tradeSyncSummary && tradeSyncSummary.count > 0) {
      const { count, exchanges, trades } = tradeSyncSummary;
      const status: RecentAlert['status'] = count > 0 ? 'new' : 'acknowledged';
      entries.push({
        id: 'sync-summary',
        message:
          count > 0
            ? `${count} new trade${count === 1 ? '' : 's'} detected across ${exchanges.join(', ') || 'exchanges'}`
            : `No new trades detected (${exchanges.join(', ') || 'n/a'})`,
        status,
        timestamp: new Date().toISOString(),
      });
      trades.slice(0, Math.max(0, 4 - entries.length + 1)).forEach((trade: any, idx: number) => {
        entries.push({
          id: `sync-trade-${idx}`,
          message: `${trade.exchange ?? 'Exchange'} ${trade.symbol ?? trade.asset ?? ''} ${trade.side?.toUpperCase?.() || ''} ${sanitizeNumber(trade.amount).toFixed(4)} @ ${formatCurrency(trade.price ?? 0)}`,
          status: 'new',
          timestamp: trade.timestamp || '',
        });
      });
    }

    return entries.slice(0, 5);
  }, [priceAlerts, tradeSyncSummary]);

  const getAssetPerformancePercent = useCallback(
    (asset: PortfolioAsset) => {
      const pnlPercent = sanitizeNumber(asset.pnl_percent);
      if (Math.abs(pnlPercent) > 0.0001) {
        return pnlPercent;
      }
      const symbolKey = asset.symbol?.toUpperCase() ?? '';
      const fallbackChange = sanitizeNumber(watchlistMap[symbolKey]?.change24h);
      return Math.abs(fallbackChange) > 0.0001 ? fallbackChange : 0;
    },
    [watchlistMap]
  );

  const getAssetPnlValue = useCallback(
    (asset: PortfolioAsset) => {
      const pnlValue = sanitizeNumber(asset.pnl);
      if (Math.abs(pnlValue) > 0.0001) {
        return pnlValue;
      }
      const performance = getAssetPerformancePercent(asset);
      if (performance !== 0) {
        return (sanitizeNumber(asset.value_usd) * performance) / 100;
      }
      return 0;
    },
    [getAssetPerformancePercent]
  );

  const computeSignificantChanges = useCallback(
    (previous: PortfolioAsset[], next: PortfolioAsset[]): AssetChangeSummary[] => {
      const threshold = 5;
      if (!previous.length || !next.length) {
        return [];
      }
      const previousMap = new Map<string, PortfolioAsset>();
      previous.forEach((asset) => {
        if (asset?.symbol) {
          previousMap.set(asset.symbol.toUpperCase(), asset);
        }
      });
      const changes: AssetChangeSummary[] = [];
      next.forEach((asset) => {
        if (!asset?.symbol) {
          return;
        }
        const symbol = asset.symbol.toUpperCase();
        const prior = previousMap.get(symbol);
        if (!prior) {
          return;
        }
        const previousValue = sanitizeNumber(prior.value_usd);
        const currentValue = sanitizeNumber(asset.value_usd);
        if (previousValue <= 0) {
          return;
        }
        const deltaValue = currentValue - previousValue;
        const deltaPercent = (deltaValue / previousValue) * 100;
        if (Math.abs(deltaPercent) >= threshold) {
          changes.push({
            symbol,
            direction: deltaPercent >= 0 ? 'up' : 'down',
            deltaPercent,
            deltaValue,
          });
        }
      });
      return changes
        .sort((a, b) => Math.abs(b.deltaPercent) - Math.abs(a.deltaPercent))
        .slice(0, 4);
    },
    []
  );

  const fetchDashboardData = useCallback(async (range: TimeRange, options?: { silent?: boolean; signal?: AbortSignal }) => {
    // Guard: don't fetch if not authenticated to prevent 401 loops
    if (!portfolioService.isAuthenticated()) {
      logger.debug('Skipping fetchDashboardData - user not authenticated');
      return { success: false, changes: [] };
    }
    
    const isSilent = options?.silent;
    const abortSignal = options?.signal;
    if (!isSilent) {
      setLoading(true);
    }
    const days = resolveDaysForRangeValue(range);
    const historyRequestDays = Math.min(days * 2, days + 365);
    let summaryError = false;
    let assetsError = false;
    let historyError = false;
    let significantChanges: AssetChangeSummary[] = [];
    const shouldSummarize = shouldSummarizeChangesRef.current;

    // Set a timeout to clear loading state if requests take too long
    const loadingTimeout = setTimeout(() => {
      if (!isSilent) {
        setLoading(false);
      }
    }, 50000); // 50s timeout - longer than API timeouts (45s) to allow requests to complete

    try {
      // Check if already aborted before starting requests
      if (abortSignal?.aborted) {
        return { success: false, changes: [] };
      }

      // Fetch critical data first (summary, assets, history)
      // Use Promise.allSettled to avoid blocking - each request can fail independently
      const results = await Promise.allSettled([
        portfolioService.getSummary(false, abortSignal),
        portfolioService.getAssets(false, abortSignal),
        portfolioService.getPortfolioHistory(historyRequestDays, false, abortSignal),
      ]);
      
      const summaryData = results[0].status === 'fulfilled' ? results[0].value : null;
      const assetsData = results[1].status === 'fulfilled' ? results[1].value : [];
      const historyData = results[2].status === 'fulfilled' ? results[2].value : [];
      
      // Check if aborted after requests
      if (abortSignal?.aborted) {
        return { success: false, changes: [] };
      }

      if (results[0].status === 'rejected') {
        // Don't log if aborted
        if (!abortSignal?.aborted && !(results[0].reason as any)?.code?.includes('ABORT')) {
          logger.warn('Summary unavailable', results[0].reason);
        }
        summaryError = true;
      }
      if (results[1].status === 'rejected') {
        if (!abortSignal?.aborted && !(results[1].reason as any)?.code?.includes('ABORT')) {
          logger.warn('Assets unavailable', results[1].reason);
        }
        assetsError = true;
      }
      if (results[2].status === 'rejected') {
        if (!abortSignal?.aborted && !(results[2].reason as any)?.code?.includes('ABORT')) {
          logger.warn('History unavailable', results[2].reason);
        }
        historyError = true;
      }

      // Set critical data immediately to show UI faster
      // Only update if we got valid data (don't reset to null/empty on errors)
      if (summaryData) {
        setSummary(summaryData);
      } else if (summaryError && !isSilent) {
        // Only log error, don't reset summary on silent refresh
        logger.warn('Summary fetch failed, keeping previous data');
      }
      
      // Process assets: filter by issues and value (will be set later after processing)
      const filteredAssets = (assetsData ?? []).filter(
        (asset) => 
          (!asset.issues || asset.issues.length === 0) &&
          sanitizeNumber(asset.value_usd) >= 1
      );
      
      if (assetsError && !isSilent && (!assetsData || assetsData.length === 0)) {
        logger.warn('Assets fetch failed, keeping previous data');
      }
      
      // Don't set history here - it will be set later after processing
      // if (historyData && Array.isArray(historyData)) {
      //   setHistory(historyData);
      // } else if (historyError && !isSilent) {
      //   logger.warn('History fetch failed, keeping previous data');
      // }

      // Fetch non-critical data in parallel (don't block UI)
      // NOTE: Performance analytics and risk analysis are now manual (on-demand) to avoid backend overload
      // Use Promise.allSettled with timeout wrapper to avoid blocking
      // Add timeout wrapper to prevent infinite waiting
      const createTimeoutPromise = (ms: number) => 
        new Promise((_, reject) => setTimeout(() => reject(new Error(`Timeout after ${ms}ms`)), ms));
      
      const nonCriticalResults = await Promise.allSettled([
        Promise.race([
          portfolioService.getPriceAlerts(),
          createTimeoutPromise(8000) // 8s timeout
        ]).catch(err => { throw err; }),
        Promise.race([
          portfolioService.getUserWatchlist(),
          createTimeoutPromise(8000) // 8s timeout
        ]).catch(err => { throw err; }),
        // Performance analytics and risk analysis removed - now manual only
        // Users can trigger these via buttons when needed
      ]);
      
      const alertsData = nonCriticalResults[0].status === 'fulfilled' ? (nonCriticalResults[0].value as any[]) : [];
      const watchlistResponse = nonCriticalResults[1].status === 'fulfilled' ? (nonCriticalResults[1].value as any) : {};
      // Performance analytics and risk data are now null by default - loaded on demand
      const performanceData: PerformanceAnalytics | null = null;
      const riskData: any | null = null;
      
      // Log errors but don't block
      nonCriticalResults.forEach((result, index) => {
        if (result.status === 'rejected') {
          const names = ['Price alerts', 'Watchlist'];
          logger.debug(`${names[index]} unavailable`, result.reason);
        }
      });
      if (shouldSummarize) {
        significantChanges = computeSignificantChanges(assetsRef.current, filteredAssets);
        const newHighlights = significantChanges.reduce((acc, change) => {
          acc[change.symbol] = change;
          return acc;
        }, {} as Record<string, AssetChangeSummary>);
        setChangeHighlights(newHighlights);
        changeHighlightsRef.current = newHighlights;
      } else if (Object.keys(changeHighlightsRef.current).length) {
        setChangeHighlights({});
        changeHighlightsRef.current = {};
      }
      
      // Only update assets if they actually changed to prevent loops
      const assetsChanged = 
        assetsRef.current.length !== filteredAssets.length ||
        assetsRef.current.some((asset, idx) => {
          const newAsset = filteredAssets[idx];
          return !newAsset || 
                 asset.symbol !== newAsset.symbol ||
                 Math.abs(sanitizeNumber(asset.value_usd) - sanitizeNumber(newAsset.value_usd)) > 0.01;
        });
      
      if (assetsChanged || filteredAssets.length === 0) {
        setAssets(filteredAssets);
        assetsRef.current = filteredAssets;
      }
      const orderedHistory = Array.isArray(historyData)
        ? [...historyData].sort(
            (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
          )
        : [];
      const windowDays = Math.max(days, 1);
      const windowMs = windowDays * 24 * 60 * 60 * 1000;
      const nowMs = Date.now();

      const selectWindow = (startMs: number, endMs: number) =>
        orderedHistory.filter((point) => {
          const timestamp = new Date(point.date).getTime();
          return Number.isFinite(timestamp) && timestamp >= startMs && timestamp < endMs;
        });

      let effectiveHistory = selectWindow(nowMs - windowMs, nowMs);

      if (!effectiveHistory.length && orderedHistory.length) {
        const fallbackCount = Math.min(orderedHistory.length, windowDays * 4);
        effectiveHistory = orderedHistory.slice(-fallbackCount);
      }

      let previousSlice: typeof effectiveHistory = [];
      if (effectiveHistory.length) {
        const windowStart = new Date(effectiveHistory[0].date).getTime();
        previousSlice = selectWindow(windowStart - windowMs, windowStart);

        if (!previousSlice.length) {
          const fallbackCount = Math.min(
            orderedHistory.length - effectiveHistory.length,
            effectiveHistory.length || windowDays
          );
          previousSlice =
            fallbackCount > 0
              ? orderedHistory.slice(
                  Math.max(orderedHistory.length - effectiveHistory.length - fallbackCount, 0),
                  Math.max(orderedHistory.length - effectiveHistory.length, 0)
                )
              : [];
        }
      }

      setHistory(effectiveHistory);
      setPreviousHistory(previousSlice);
      // Only update historyDays if it actually changed to prevent loops
      // Use ref to track previous value and only update if truly changed
      if (previousHistoryDaysRef.current !== windowDays) {
        previousHistoryDaysRef.current = windowDays;
        setHistoryDays(windowDays);
      }
      setPriceAlerts(alertsData ?? []);

      const fallbackSymbols = filteredAssets
        .filter((asset) => sanitizeNumber(asset.value_usd) > 0)
        .slice(0, 6)
        .map((asset) => asset.symbol?.toUpperCase())
        .filter(Boolean) as string[];
      const watchlistSymbols = Array.isArray(watchlistResponse) 
        ? watchlistResponse 
        : ((watchlistResponse as any)?.symbols ?? []);
      const uniqueWatchlist = Array.from(
        new Set([
          ...watchlistSymbols.map((symbol: string) => symbol.toUpperCase()),
          ...fallbackSymbols,
        ])
      ).slice(0, 4);
      const finalWatchlist = uniqueWatchlist.length ? uniqueWatchlist : ['AAPL', 'MSFT', 'BTC', 'ETH'];
      
      // Only update watchlistSymbols if it actually changed to prevent loops
      setWatchlistSymbols((prev) => {
        if (prev.length === finalWatchlist.length && 
            prev.every((sym, idx) => sym === finalWatchlist[idx])) {
          return prev; // No change, return previous to prevent re-render
        }
        return finalWatchlist;
      });
      // Performance analytics now loaded manually - don't set here
      // setPerformanceAnalytics(performanceData as any);
      if (riskData && typeof riskData === 'object') {
        const assetTypeMap = new Map<string, string>();
        filteredAssets.forEach((asset) => {
          const symbolKey = asset.symbol?.toUpperCase();
          if (!symbolKey) {
            return;
          }
          const explicitType = (asset.asset_type || '').toLowerCase();
          if (explicitType === 'crypto' || explicitType === 'stock') {
            assetTypeMap.set(symbolKey, explicitType);
            return;
          }
          const exchangeLower = (asset.exchange || '').toLowerCase();
          const isCryptoExchange =
            exchangeLower.includes('binance') ||
            exchangeLower.includes('bybit') ||
            exchangeLower.includes('kraken') ||
            exchangeLower.includes('coinbase') ||
            exchangeLower.includes('crypto');
          assetTypeMap.set(symbolKey, isCryptoExchange ? 'crypto' : 'stock');
        });

        const rawHeatmap = riskData && Array.isArray((riskData as any)?.heatmap?.heatmap) ? (riskData as any).heatmap.heatmap : [];
        const normalizedHeatmap = rawHeatmap
          .map((item: any, index: number) => {
            const symbol = (item?.symbol || item?.name || `asset-${index}`).toString();
            const upperSymbol = symbol.toUpperCase();
            const typeHint =
              typeof item?.type === 'string' ? item.type.toLowerCase() : assetTypeMap.get(upperSymbol);
            const normalizedType = typeHint === 'crypto' || typeHint === 'stock' ? typeHint : undefined;
            if (!normalizedType) {
              return null;
            }
            const pnlPercent = Number(item?.pnl_percent);
            const riskScore = Number(item?.risk_score);
            const allocation = Number(item?.allocation);
            const volatility = Number(item?.volatility);
            return {
              id: upperSymbol,
              label: upperSymbol,
              value: Number.isFinite(pnlPercent) ? pnlPercent : 0,
              trend: [],
              riskScore: Number.isFinite(riskScore) ? riskScore : undefined,
              allocation: Number.isFinite(allocation) ? allocation : undefined,
              volatility: Number.isFinite(volatility) ? volatility : undefined,
              type: normalizedType,
            } as HeatmapCell;
          })
          .filter((cell: HeatmapCell | null): cell is HeatmapCell => Boolean(cell));

        const sortHeatmap = (cells: HeatmapCell[]) =>
          cells
            .slice()
            .sort(
              (a, b) =>
                Math.abs(b.value) + (b.allocation ?? 0) - (Math.abs(a.value) + (a.allocation ?? 0))
            )
            .slice(0, 12);

        const stocksHeatmap = sortHeatmap(
          normalizedHeatmap.filter((cell: HeatmapCell) => cell.type === 'stock')
        );
        const cryptoHeatmap = sortHeatmap(
          normalizedHeatmap.filter((cell: HeatmapCell) => cell.type === 'crypto')
        );

        if (stocksHeatmap.length || cryptoHeatmap.length) {
          setHeatmapByType({
            stocks: stocksHeatmap,
            crypto: cryptoHeatmap,
          });
        } else {
          setHeatmapByType({ stocks: [], crypto: [] });
        }

        if (riskData && (riskData as any).risk_analysis) {
          const riskDataTyped = riskData as any;
          setRiskOverview({
            score: Number(riskDataTyped.risk_analysis.risk_score ?? 0),
            level: riskDataTyped.risk_analysis.risk_level,
            timestamp: riskDataTyped.heatmap?.timestamp,
          });
        } else {
          setRiskOverview(null);
        }
      } else {
        setHeatmapByType({ stocks: [], crypto: [] });
        setRiskOverview(null);
      }
      setTradeSyncSummary(null);
      
      // Only update lastUpdated if data actually changed to prevent loops
      // Use ref to track last update time and prevent rapid updates
      const newLastUpdated = new Date().toISOString();
      setLastUpdated((prev) => {
        // Only update if more than 2 seconds have passed to prevent rapid updates
        if (prev && new Date(newLastUpdated).getTime() - new Date(prev).getTime() < 2000) {
          return prev; // Return previous to prevent re-render
        }
        return newLastUpdated;
      });

      return { success: !(summaryError || assetsError || historyError), changes: significantChanges };
    } catch (error) {
      logger.error('Failed to load dashboard data', error);
      // Don't reset data on error - keep previous values to avoid showing 0
      if (!isSilent) {
        setTradeSyncSummary(null);
        setLoading(false);
      }
      return { success: false, changes: [] };
    } finally {
      clearTimeout(loadingTimeout);
      if (!isSilent) {
        setLoading(false);
      }
    }
  },
    [computeSignificantChanges]
  );

  // Use ref to prevent re-registration on every fetchDashboardData change
  const fetchDashboardDataRefForEffect = useRef(fetchDashboardData);
  useEffect(() => {
    fetchDashboardDataRefForEffect.current = fetchDashboardData;
  }, [fetchDashboardData]);

  // Track last fetch time to prevent rapid successive fetches
  const lastFetchTimeRef = useRef<number>(0);
  const FETCH_DEBOUNCE_MS = 1000; // Minimum 1 second between fetches

  // DISABLED: Main useEffect for fetching data when timeRange changes
  // All API calls are now manual only - user must click refresh button
  // useEffect(() => {
  //   // Guard: don't fetch if not authenticated to prevent 401 loops
  //   // Double-check with ref to avoid race conditions
  //   if (!isAuthenticated || !isAuthenticatedRef.current) {
  //     logger.debug('Skipping fetch - user not authenticated', { isAuthenticated, ref: isAuthenticatedRef.current });
  //     return;
  //   }
  //   
  //   // Check if timeRange actually changed
  //   if (previousTimeRangeRef.current === timeRange) {
  //     logger.debug('Skipping fetch - timeRange unchanged:', timeRange);
  //     return;
  //   }
  //   
  //   // Prevent rapid successive fetches
  //   const now = Date.now();
  //   const timeSinceLastFetch = now - lastFetchTimeRef.current;
  //   if (timeSinceLastFetch < FETCH_DEBOUNCE_MS) {
  //     logger.debug('Skipping fetch - too soon since last fetch:', timeSinceLastFetch, 'ms');
  //     return;
  //   }
  //   
  //   logger.debug('Dashboard useEffect triggered:', { timeRange, previous: previousTimeRangeRef.current, refreshInProgress: refreshInProgressRef.current, isAuthenticated });
  //   
  //   // Update previous value
  //   previousTimeRangeRef.current = timeRange;
  //   
  //   // Skip if already fetching to prevent loops
  //   if (refreshInProgressRef.current) {
  //     logger.warn('Skipping fetch - refresh already in progress');
  //     return;
  //   }
  //   
  //   // Create AbortController for this effect
  //   const abortController = new AbortController();
  //   
  //   // Mark as in progress and update last fetch time
  //   refreshInProgressRef.current = true;
  //   lastFetchTimeRef.current = now;
  //   logger.debug('Starting fetchDashboardData for timeRange:', timeRange);
  //   
  //   // Use ref to avoid stale closure issues
  //   void fetchDashboardDataRefForEffect.current(timeRange, { signal: abortController.signal })
  //     .then((result) => {
  //       logger.debug('fetchDashboardData completed:', result);
  //       refreshInProgressRef.current = false;
  //     })
  //     .catch((error) => {
  //       logger.error('fetchDashboardData failed:', error?.response?.status, error?.message);
  //       // If 401, don't reset refreshInProgress - let interceptor handle redirect
  //       // This prevents multiple redirect attempts
  //       if (error?.response?.status === 401) {
  //         logger.warn('Dashboard: Got 401, stopping fetches - interceptor will handle redirect');
  //         // Don't reset refreshInProgress - it will be reset on unmount
  //       } else {
  //         refreshInProgressRef.current = false;
  //         logger.debug('fetchDashboardData finally - refreshInProgress set to false');
  //       }
  //     });
  //   
  //   // Prefetch contextual data in the background (only if authenticated)
  //   // Note: prefetchContextualData returns void, so we can't catch errors here
  //   if (isAuthenticated && isAuthenticatedRef.current) {
  //     try {
  //       portfolioService.prefetchContextualData('dashboard');
  //     } catch (err) {
  //       logger.debug('prefetchContextualData error (non-critical):', err);
  //     }
  //   }
  //   
  //   // Cleanup: abort requests when component unmounts or dependencies change
  //   return () => {
  //     logger.debug('Dashboard useEffect cleanup - aborting requests');
  //     abortController.abort();
  //     if (refreshInProgressRef.current) {
  //       refreshInProgressRef.current = false;
  //     }
  //   };
  // }, [timeRange, isAuthenticated]); // Include isAuthenticated to prevent fetching when logged out

  // Show onboarding tour on first visit
  useEffect(() => {
    if (!onboardingCompleted && !loading && summary) {
      // Wait a bit for UI to render before showing tour
      const timeout = setTimeout(() => {
        setOnboardingTourOpen(true);
      }, 1000);
      return () => clearTimeout(timeout);
    }
  }, [onboardingCompleted, loading, summary]);

  // Sync notifications from price alerts and sync summary
  useEffect(() => {
    notificationsService.syncFromExternalSources(priceAlerts, tradeSyncSummary);
  }, [priceAlerts, tradeSyncSummary]);

  // DISABLED: Check migration status on mount - now manual only
  // useEffect(() => {
  //   const checkMigrationStatus = async () => {
  //     try {
  //       const status = await portfolioService.getMigrationStatus();
  //       setMigrationStatus(status);
  //       // Show banner if migration is complete (first time success message)
  //       if (status.migration_complete) {
  //         const migrationShown = localStorage.getItem('migration_status_shown');
  //         if (!migrationShown) {
  //           setShowMigrationBanner(true);
  //           localStorage.setItem('migration_status_shown', 'true');
  //           // Auto-hide after 10 seconds
  //           setTimeout(() => setShowMigrationBanner(false), 10000);
  //         }
  //       }
  //     } catch (error) {
  //       logger.warn('Failed to check migration status:', error);
  //     }
  //   };
  //   checkMigrationStatus();
  // }, []);

  // Auto-refresh dashboard data every 60 seconds (silent mode to avoid UI flicker)
  // Use ref to track if refresh is in progress to avoid overlapping requests
  // Use refs to avoid recreating interval on every fetchDashboardData/timeRange change
  const fetchDashboardDataRef = useRef(fetchDashboardData);
  const timeRangeRef = useRef(timeRange);
  
  useEffect(() => {
    fetchDashboardDataRef.current = fetchDashboardData;
  }, [fetchDashboardData]);
  
  useEffect(() => {
    timeRangeRef.current = timeRange;
  }, [timeRange]);

  // Auto-refresh dashboard data every 60 seconds (silent mode to avoid UI flicker)
  // Use refs to track refreshing/syncing state without re-creating interval
  const refreshingRef = useRef(false);
  const syncingRef = useRef(false);
  
  useEffect(() => {
    refreshingRef.current = refreshing;
  }, [refreshing]);
  
  useEffect(() => {
    syncingRef.current = syncing;
  }, [syncing]);

  // DISABLED: Auto-refresh dashboard data every 60 seconds - now manual only
  // useEffect(() => {
  //   const intervalId = setInterval(() => {
  //     // Skip if not authenticated to prevent 401 loops
  //     if (!portfolioService.isAuthenticated()) {
  //       logger.debug('Skipping auto-refresh - user not authenticated');
  //       return;
  //     }
  //     // Skip if previous refresh is still in progress
  //     if (refreshInProgressRef.current) {
  //       logger.debug('Skipping auto-refresh - previous refresh still in progress');
  //       return;
  //     }
  //     // Skip if manual refresh or sync is in progress
  //     if (refreshingRef.current || syncingRef.current) {
  //       logger.debug('Skipping auto-refresh - manual refresh or sync in progress');
  //       return;
  //     }
  //     refreshInProgressRef.current = true;
  //     fetchDashboardDataRef.current(timeRangeRef.current, { silent: true })
  //       .catch((error) => {
  //         // Don't reset refreshInProgress on 401 - let interceptor handle redirect
  //         if (error?.response?.status !== 401) {
  //           refreshInProgressRef.current = false;
  //         }
  //       })
  //       .finally(() => {
  //         // Only clear if not a 401 (401 will redirect)
  //         if (refreshInProgressRef.current) {
  //           refreshInProgressRef.current = false;
  //         }
  //       });
  //   }, 60000); // 60 seconds - less frequent to reduce load

  //   return () => {
  //     clearInterval(intervalId);
  //   };
  // }, []); // Empty deps - only create interval once

  // Memoize symbols array to prevent unnecessary re-fetches
  const newsSymbols = useMemo(() => {
    if (!assets.length) {
      return [];
    }
    return Array.from(
      new Set(
        assets
          .slice(0, 8)
          .map((asset) => asset.symbol?.toUpperCase())
          .filter((symbol): symbol is string => Boolean(symbol))
      )
    );
  }, [assets]);

  useEffect(() => {
    if (!newsSymbols.length) {
      setNewsMap({});
      return;
    }

    let cancelled = false;
    const normalizeSentiment = (value: any): 'positive' | 'negative' | 'neutral' | undefined => {
      const normalized = typeof value === 'string' ? value.toLowerCase() : '';
      if (normalized === 'positive' || normalized === 'negative' || normalized === 'neutral') {
        return normalized;
      }
      return undefined;
    };

    // Debounce news fetch to prevent rapid successive calls
    const timeoutId = setTimeout(() => {
      portfolioService
        .getNews(newsSymbols, 12)
        .then((items) => {
          if (cancelled) {
            return;
          }
          const grouped: Record<string, AssetTabData['news']> = {};
          const globalList: AssetTabData['news'] = [];
          (items ?? []).forEach((entry: any) => {
            const symbol =
              (entry?.symbol ?? entry?.ticker ?? entry?.asset ?? newsSymbols[0] ?? '')
                .toString()
                .toUpperCase();
            if (!symbol) {
              return;
            }
            const list = grouped[symbol] ?? [];
            const normalizedEntry: NewsItem = {
              id:
                entry?.id?.toString() ??
                `${symbol}-${entry?.url ?? entry?.title ?? entry?.timestamp ?? Math.random().toString(36).slice(2)}`,
              title: entry?.title ?? entry?.headline ?? 'Untitled headline',
              source: entry?.source ?? entry?.publisher ?? 'Unknown source',
              timestamp:
                entry?.timestamp ??
                entry?.published_at ??
                entry?.datetime ??
                new Date().toLocaleString(),
              url: entry?.url,
              summary: entry?.summary ?? entry?.description ?? '',
              sentiment: normalizeSentiment(entry?.sentiment ?? entry?.sentiment_score_label),
              symbol,
            };
            list.push(normalizedEntry);
            globalList.push(normalizedEntry);
            grouped[symbol] = list.slice(0, 5);
          });
          if (globalList.length > 0) {
            grouped.__GLOBAL__ = globalList
              .slice()
              .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
              .slice(0, 12);
          }
          setNewsMap(grouped);
        })
        .catch((error) => {
          if (!cancelled) {
            logger.debug('Failed to load market news', error);
          }
        });
    }, 300); // 300ms debounce

    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
    };
  }, [newsSymbols]);

  // Persist filters to localStorage (debounced to prevent excessive writes)
  const filtersPersistTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }
    
    // Clear previous timeout
    if (filtersPersistTimeoutRef.current) {
      clearTimeout(filtersPersistTimeoutRef.current);
    }
    
    // Debounce localStorage writes to prevent loops
    filtersPersistTimeoutRef.current = setTimeout(() => {
      const payload = { ...filters, timeRange };
      try {
        window.localStorage.setItem(FILTER_STORAGE_KEY, JSON.stringify(payload));
      } catch (error) {
        logger.debug('Failed to persist dashboard filters', error);
      }
    }, 500); // 500ms debounce
    
    return () => {
      if (filtersPersistTimeoutRef.current) {
        clearTimeout(filtersPersistTimeoutRef.current);
      }
    };
  }, [filters, timeRange]);

  const deriveAssetMetadata = useCallback((asset: PortfolioAsset) => {
    const symbol = asset.symbol?.toUpperCase() || '';
    const explicitType = (asset.asset_type || '').toLowerCase();
    const exchangeName = (asset.exchange || '').toLowerCase();
    const inferredFromType =
      explicitType === 'crypto' ? 'Crypto' : explicitType === 'stock' ? 'Stocks' : null;

    const isCryptoExchange =
      exchangeName.includes('binance') ||
      exchangeName.includes('bybit') ||
      exchangeName.includes('kraken') ||
      exchangeName.includes('coinbase') ||
      exchangeName.includes('crypto');

    const assetType = inferredFromType ?? (isCryptoExchange ? 'Crypto' : 'Stocks');

    if (assetType === 'Stocks') {
      const mapping = stockSectorMap[symbol] || {
        sector: 'Technology',
        region: 'North America',
        tags: ['Blue Chip'],
      };
      return {
        assetType,
        sector: mapping.sector,
        region: mapping.region,
        tags: mapping.tags,
        isStablecoin: false,
      };
    }

    const cryptoTags =
      symbol === 'BTC'
        ? ['Blue Chip', 'Store of Value']
        : symbol === 'ETH'
        ? ['Blue Chip', 'Smart Contracts']
        : ['DeFi'];

    return {
      assetType: 'Crypto',
      sector: 'Digital Assets',
      region: 'Global',
      tags: stablecoinSymbols.has(symbol) ? ['Stablecoin'] : cryptoTags,
      isStablecoin: stablecoinSymbols.has(symbol),
    };
  }, []);

  const filteredAssets = useMemo(() => {
    return assets.filter((asset) => {
      const metadata = deriveAssetMetadata(asset);
      if (filters.assetType.length > 0 && !filters.assetType.includes(metadata.assetType)) {
        return false;
      }
      if (filters.stablecoinsOnly && !metadata.isStablecoin) {
        return false;
      }
      if (filters.sector.length > 0 && !filters.sector.includes(metadata.sector)) {
        return false;
      }
      if (filters.region.length > 0 && !filters.region.includes(metadata.region)) {
        return false;
      }
      if (
        filters.tags.length > 0 &&
        (!metadata.tags || !metadata.tags.some((tag) => filters.tags.includes(tag)))
      ) {
        return false;
      }
      return true;
    });
  }, [assets, deriveAssetMetadata, filters]);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    shouldSummarizeChangesRef.current = true;
    try {
      const { success, changes } = await fetchDashboardData(timeRange, { silent: true });
      // Don't set lastUpdated here - fetchDashboardData handles it with debounce
      if (success) {
        if (changes.length > 0) {
          const summary = changes
            .slice(0, 2)
            .map(
              (change) =>
                `${change.symbol} ${change.deltaPercent >= 0 ? '+' : ''}${change.deltaPercent.toFixed(1)}%`
            )
            .join(', ');
          const summaryMessage =
            changes.length > 1
              ? `${changes.length} assets moved >5%: ${summary}`
              : `Top move ${changes[0].symbol} ${changes[0].deltaPercent >= 0 ? '+' : ''}${changes[0].deltaPercent.toFixed(1)}%`;
          showToast(summaryMessage, 'success');
        } else {
          showToast('Dashboard data refreshed', 'success');
        }
      } else {
        showToast('Dashboard refreshed with partial data', 'warning');
      }
    } catch (error) {
      logger.error('Failed to refresh dashboard data', error);
      showToast('Failed to refresh dashboard data', 'error');
    } finally {
      shouldSummarizeChangesRef.current = false;
      setRefreshing(false);
    }
  }, [fetchDashboardData, showToast, timeRange]);

  const handleSyncTrades = useCallback(async () => {
    // Guard: skip if already syncing to prevent multiple simultaneous syncs
    if (syncing || refreshInProgressRef.current) {
      logger.debug('Skipping sync - already in progress');
      return;
    }
    
    setSyncing(true);
    try {
      const result = await portfolioService.checkExchangeSync(200);
      let dedupedTrades: any[] = [];
      if (result) {
        const rawTrades = Object.values(result.details || {}).flatMap((detail: any) => detail?.new || []);
        const seenTradeKeys = new Set<string>();
        dedupedTrades = rawTrades
          .filter((trade: any) => {
            const key = `${trade.exchange ?? ''}-${trade.symbol ?? trade.asset ?? ''}-${trade.side ?? ''}-${trade.amount ?? ''}-${trade.timestamp ?? ''}`;
            if (seenTradeKeys.has(key)) {
              return false;
            }
            seenTradeKeys.add(key);
            return true;
          })
          .slice(0, 20);
        setTradeSyncSummary({
          count: result.summary?.new_trades ?? dedupedTrades.length,
          exchanges: result.summary?.checked_exchanges ?? [],
          trades: dedupedTrades,
        });
        // Don't set lastUpdated here - let fetchDashboardData handle it with debounce
        const newTrades = result.summary?.new_trades ?? dedupedTrades.length;
        showToast(
          newTrades > 0
            ? `${newTrades} new trade${newTrades === 1 ? '' : 's'} imported`
            : 'No new trades detected',
          newTrades > 0 ? 'success' : 'info'
        );
      }
      persistNewTrades(dedupedTrades);
    } catch (error) {
      logger.error('Failed to sync trades', error);
      showToast('Failed to sync trades', 'error');
    } finally {
      setSyncing(false);
    }
  }, [persistNewTrades, showToast, syncing]);

  const { stocksAssets, cryptoAssets } = useMemo(() => {
    const stocks: PortfolioAsset[] = [];
    const crypto: PortfolioAsset[] = [];

    filteredAssets.forEach((asset) => {
      const metadata = deriveAssetMetadata(asset);
      if (metadata.assetType === 'Crypto') {
        crypto.push(asset);
      } else {
        stocks.push(asset);
      }
    });

    return { stocksAssets: stocks, cryptoAssets: crypto };
  }, [deriveAssetMetadata, filteredAssets]);

  const stocksTotal = useMemo(
    () => stocksAssets.reduce((acc, asset) => acc + sanitizeNumber(asset.value_usd), 0),
    [stocksAssets]
  );
  const cryptoTotal = useMemo(
    () => cryptoAssets.reduce((acc, asset) => acc + sanitizeNumber(asset.value_usd), 0),
    [cryptoAssets]
  );
  // Use frontend calculation (filtered assets) as primary source
  // Backend total_value_usd includes all portfolios/exchanges, but frontend shows only filtered assets
  // This ensures Total Portfolio Value matches what user sees (Stocks + Crypto summaries)
  const totalValue = stocksTotal + cryptoTotal || sanitizeNumber(summary?.total_value_usd);
  
  // Validation: Log discrepancies for debugging
  // Disabled to prevent potential loop - only log once when data changes significantly
  // useEffect(() => {
  //   if (summary?.total_value_usd && Math.abs(summary.total_value_usd - (stocksTotal + cryptoTotal)) > 1) {
  //     logger.warn('Dashboard data discrepancy detected', {
  //       backendTotal: summary.total_value_usd,
  //       frontendTotal: stocksTotal + cryptoTotal,
  //       difference: summary.total_value_usd - (stocksTotal + cryptoTotal),
  //       filteredAssetsCount: assets.length,
  //       stocksCount: stocksAssets.length,
  //       cryptoCount: cryptoAssets.length,
  //     });
  //   }
  // }, [summary?.total_value_usd, stocksTotal, cryptoTotal, assets.length, stocksAssets.length, cryptoAssets.length]);

  const benchmarkValueMap = useMemo(() => {
    const map: Record<string, Record<string, number>> = {};
    Object.entries(benchmarkSeries).forEach(([id, payload]) => {
      if (!payload || payload.days !== historyDays) {
        return;
      }
      const seriesMap: Record<string, number> = {};
      payload.series.forEach((point) => {
        if (!point?.date) {
          return;
        }
        const key = point.date.slice(0, 10);
        const normalized = typeof point.normalized_value === 'number' ? point.normalized_value : undefined;
        const raw = typeof point.value === 'number' ? point.value : undefined;
        if (normalized !== undefined) {
          seriesMap[key] = normalized;
        } else if (raw !== undefined) {
          seriesMap[key] = raw;
        }
      });
      map[id] = seriesMap;
    });
    return map;
  }, [benchmarkSeries, historyDays]);

  const equityCurvePoints = useMemo<EquityCurvePoint[]>(() => {
    const totalCurrentValue = stocksTotal + cryptoTotal;
    const stockShare = totalCurrentValue > 0 ? stocksTotal / totalCurrentValue : 0.5;
    const cryptoShare = 1 - stockShare;

    return history.map((point) => {
      const isoDate = point.date.slice(0, 10);
      const benchmarkValues: Record<string, number> = {};
      Object.entries(benchmarkValueMap).forEach(([id, values]) => {
        const benchmarkValue = values[isoDate];
        if (benchmarkValue !== undefined) {
          benchmarkValues[id] = Number(benchmarkValue.toFixed(2));
        }
      });
      const totalValue = Math.round(point.value_usd);
      return {
        date: new Date(point.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        value: totalValue,
        stocks: Math.round(totalValue * stockShare),
        crypto: Math.round(totalValue * cryptoShare),
        benchmarkValues,
      };
    });
  }, [benchmarkValueMap, cryptoTotal, history, stocksTotal]);

  const previousEquityCurvePoints = useMemo<EquityCurvePoint[]>(() => {
    if (!previousHistory.length) {
      return [];
    }
    return previousHistory.map((point) => ({
      date: new Date(point.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      value: Math.round(point.value_usd),
    }));
  }, [previousHistory]);

  const equityComparison = useMemo(() => {
    if (!history.length || !previousHistory.length) {
      return null;
    }
    const currentLatest = history[history.length - 1];
    const previousLatest = previousHistory[previousHistory.length - 1];
    if (!currentLatest || !previousLatest) {
      return null;
    }
    const currentValue = sanitizeNumber(currentLatest.value_usd);
    const previousValue = sanitizeNumber(previousLatest.value_usd);
    if (previousValue === 0) {
      return null;
    }
    const deltaValue = currentValue - previousValue;
    const deltaPercent = (deltaValue / previousValue) * 100;
    const label =
      timeRange === '24h'
        ? 'Previous 24h'
        : timeRange === '7d'
        ? 'Previous 7 days'
        : 'Previous period';
    return {
      label,
      currentValue,
      previousValue,
      deltaValue,
      deltaPercent,
      formattedDeltaValue: formatCurrency(deltaValue),
      formattedDeltaPercent: formatPercent(deltaPercent),
    };
  }, [formatPercent, history, previousHistory, timeRange]);

  // Calculate daily change: compare latest value with previous day (not first day)
  const dailyChange = useMemo(() => {
    if (equityCurvePoints.length < 2) {
      return { deltaValue: 0, deltaPercent: 0 };
    }
    const latest = equityCurvePoints[equityCurvePoints.length - 1];
    const previous = equityCurvePoints[equityCurvePoints.length - 2];
    if (!latest || !previous) {
      return { deltaValue: 0, deltaPercent: 0 };
    }
    const deltaValue = latest.value - previous.value;
    const deltaPercent = previous.value ? (deltaValue / previous.value) * 100 : 0;
    return { deltaValue, deltaPercent };
  }, [equityCurvePoints]);

  const topPerformer = useMemo(() => {
    if (!assets.length) {
      return null;
    }
    return assets.reduce((best, current) => {
      const currentPnl = sanitizeNumber(current.pnl_percent);
      const bestPnl = sanitizeNumber(best?.pnl_percent);
      return currentPnl > bestPnl ? current : best;
    }, assets[0]);
  }, [assets]);
  const topPerformerSymbol = topPerformer?.symbol?.toUpperCase() ?? null;

  const handleFocusTopPerformer = useCallback(() => {
    if (topPerformerSymbol) {
      setSelectedDrilldown(topPerformerSymbol);
      showToast(`Focused on ${topPerformerSymbol}`, 'info');
    }
  }, [setSelectedDrilldown, showToast, topPerformerSymbol]);

  const handleNavigateWarnings = useCallback(() => {
    if (summaryWarnings.length > 0) {
      navigate('/price-alerts');
    }
  }, [navigate, summaryWarnings.length]);

  const quickInsights: QuickInsight[] = useMemo(() => {
    const items: QuickInsight[] = [
      {
        id: 'daily-cashflow',
        label: 'Daily Cashflow',
        primary: formatCurrency(dailyChange.deltaValue),
        helper: `vs prev day (${formatPercent(dailyChange.deltaPercent)})`,
        delta: dailyChange.deltaPercent,
        positive: dailyChange.deltaValue >= 0,
        icon:
          dailyChange.deltaValue >= 0 ? (
            <ArrowUpwardIcon color="success" fontSize="small" />
          ) : (
            <ArrowDownwardIcon color="error" fontSize="small" />
          ),
      },
    ];

    if (topPerformer) {
      const pnlPercent = sanitizeNumber(topPerformer.pnl_percent);
      items.push({
        id: 'top-performer',
        label: 'Top Performer',
        primary: topPerformer.symbol ?? '—',
        helper: `${formatCurrency(topPerformer.value_usd)} • ${formatPercent(pnlPercent)}`,
        delta: pnlPercent,
        positive: pnlPercent >= 0,
        icon:
          pnlPercent >= 0 ? (
            <ArrowUpwardIcon color="success" fontSize="small" />
          ) : (
            <ArrowDownwardIcon color="error" fontSize="small" />
          ),
        onClick: handleFocusTopPerformer,
      });
    }

    if (summaryWarnings.length > 0) {
      items.push({
        id: 'warnings',
        label: 'Data Warnings',
        primary: summaryWarnings.length.toString(),
        helper: 'Tap to review',
        severity: 'warning',
        icon: <ErrorOutlineIcon color="warning" fontSize="small" />,
        onClick: handleNavigateWarnings,
      });
    }

    return items;
  }, [
    dailyChange.deltaPercent,
    dailyChange.deltaValue,
    formatPercent,
    handleFocusTopPerformer,
    handleNavigateWarnings,
    summaryWarnings.length,
    topPerformer,
  ]);

  const kpis: KPIItem[] = useMemo(() => {
    const ytd = sanitizeNumber(summary?.total_pnl_percent);
    const base: KPIItem[] = [
      {
        id: 'total-value',
        label: 'Total Portfolio Value',
        value: formatCurrency(totalValue),
        secondary:
          summary?.total_value_usd && summary.total_value_usd > 0 && summary?.total_value_pln !== undefined
            ? formatCurrency((totalValue / summary.total_value_usd) * summary.total_value_pln, 'PLN')
            : '—',
      },
      {
        id: 'daily-pl',
        label: 'Daily P/L',
        value: formatCurrency(dailyChange.deltaValue),
        delta: dailyChange.deltaPercent,
        deltaLabel: 'vs prev day',
      },
      {
        id: 'ytd-roi',
        label: 'YTD ROI',
        value: `${ytd.toFixed(2)}%`,
        delta: ytd,
        deltaLabel: 'year-to-date',
      },
      {
        id: 'active-assets',
        label: 'Active Holdings',
        value: `${summary?.total_assets ?? assets.length}`,
        secondary: `${stocksAssets.length} stocks · ${cryptoAssets.length} crypto`,
      },
    ];
    if (riskOverview) {
      base.push({
        id: 'risk-score',
        label: 'Risk Score',
        value: `${sanitizeNumber(riskOverview.score).toFixed(0)}`,
        secondary: riskOverview.level ? riskOverview.level.toUpperCase() : undefined,
      });
    }
    return base;
  }, [
    assets.length,
    cryptoAssets.length,
    dailyChange.deltaPercent,
    dailyChange.deltaValue,
    riskOverview,
    stocksAssets.length,
    summary?.total_pnl_percent,
    summary?.total_value_pln,
    summary?.total_value_usd,
    totalValue,
  ]);

  const stocksSummary: SummaryModule = useMemo(() => {
    const trend = equityCurvePoints.slice(-20).map((point) => point.stocks ?? 0);
    const totalPnL = stocksAssets.reduce((acc, asset) => acc + getAssetPnlValue(asset), 0);
    const changePercent = stocksTotal > 0 ? (totalPnL / stocksTotal) * 100 : 0;

    return {
      id: 'stocks',
      title: 'Stocks Summary',
      value: formatCurrency(stocksTotal),
      changePercent,
      changeLabel: 'Realized/unrealized P&L',
      trend,
      accent: 'stocks',
    };
  }, [equityCurvePoints, getAssetPnlValue, stocksAssets, stocksTotal]);

  const cryptoSummary: SummaryModule = useMemo(() => {
    const trend = equityCurvePoints.slice(-20).map((point) => point.crypto ?? 0);
    const totalPnL = cryptoAssets.reduce((acc, asset) => acc + getAssetPnlValue(asset), 0);
    const changePercent = cryptoTotal > 0 ? (totalPnL / cryptoTotal) * 100 : 0;

    return {
      id: 'crypto',
      title: 'Crypto Summary',
      value: formatCurrency(cryptoTotal),
      changePercent,
      changeLabel: 'Realized/unrealized P&L',
      trend,
      accent: 'crypto',
    };
  }, [cryptoAssets, cryptoTotal, equityCurvePoints, getAssetPnlValue]);

  const allocation: AllocationBreakdownData = useMemo(() => {
    const total = stocksTotal + cryptoTotal || 1;
    const topAssets = [...stocksAssets, ...cryptoAssets]
      .sort((a, b) => sanitizeNumber(b.value_usd) - sanitizeNumber(a.value_usd))
      .slice(0, 6);

    const allSlices = topAssets.map((asset, index) => ({
      label: asset.symbol,
      value: ((sanitizeNumber(asset.value_usd) / total) * 100),
      color: palette[index % palette.length],
    }));

    const byAssetClass = [
      { label: 'Stocks', value: (stocksTotal / total) * 100, color: palette[0] },
      { label: 'Crypto', value: (cryptoTotal / total) * 100, color: palette[2] },
    ];

    return { all: allSlices, byAssetClass };
  }, [cryptoAssets, cryptoTotal, stocksAssets, stocksTotal]);

  const symbolMetaMap = useMemo(() => {
    const map: Record<string, { exchange?: string }> = {};
    assets.forEach((asset) => {
      const symbol = asset.symbol?.toUpperCase?.() ?? '';
      if (!symbol) {
        return;
      }
      const meta = deriveAssetMetadata(asset);
      map[symbol] = {
        exchange: asset.exchange,
        ...meta,
      };
    });
    return map;
  }, [assets, deriveAssetMetadata]);

  useEffect(() => {
    const alertSet = new Set(
      priceAlerts
        .filter((alert: any) => alert?.active)
        .map((alert: any) => (alert?.symbol ?? '').toUpperCase())
    );

    setWatchlistMap((prev) => {
      const next: Record<string, WatchItem> = {};
      watchlistSymbols.forEach((symbol) => {
        const key = symbol.toUpperCase();
        const prevItem = prev[key];
        const meta = symbolMetaMap[key];
        next[key] = {
          id: symbol,
          label: meta?.exchange ? `${symbol} · ${meta.exchange.toUpperCase()}` : symbol,
          symbol,
          price: prevItem?.price ?? '—',
          change24h: prevItem?.change24h ?? 0,
          volume: prevItem?.volume ?? '—',
          alertActive: alertSet.has(key),
        };
      });
      return next;
    });
  }, [priceAlerts, symbolMetaMap, watchlistSymbols]);

  useEffect(() => {
    if (!watchlistSymbols.length) {
      setWatchlistMap({});
      return;
    }

    let cancelled = false;
    const symbols = watchlistSymbols.map((symbol) => symbol.toUpperCase());
    portfolioService
      .getWatchlistPrices(symbols)
      .then((response) => {
        if (cancelled) {
          return;
        }
        const list = Array.isArray(response) ? response : response?.prices ?? [];
        const priceMap = new Map<string, any>();
        list.forEach((entry: any) => {
          if (entry?.symbol) {
            priceMap.set(entry.symbol.toUpperCase(), entry);
          }
        });
        setWatchlistMap((prev) => {
          const next = { ...prev };
          priceMap.forEach((price, key) => {
            const existing = next[key];
            next[key] = {
              id: key,
              label: existing?.label ?? key,
              symbol: key,
              price:
                typeof price.price === 'number'
                  ? formatCurrency(price.price)
                  : existing?.price ?? '—',
              change24h:
                typeof price.change_percent_24h === 'number'
                  ? price.change_percent_24h
                  : existing?.change24h ?? 0,
              volume:
                typeof price.volume === 'number'
                  ? price.volume.toLocaleString()
                  : existing?.volume ?? '—',
              alertActive: existing?.alertActive ?? false,
            };
          });
          return next;
        });
      })
      .catch((error) => {
        logger.debug('Failed to load watchlist prices', error);
      });

    return () => {
      cancelled = true;
    };
  }, [watchlistSymbols]);

  const buildHeatmap = useCallback(
    (assetGroup: PortfolioAsset[], assetType: 'stocks' | 'crypto') => {
      const riskDriven = heatmapByType[assetType];
      if (riskDriven && riskDriven.length) {
        return riskDriven;
      }
      const groupTotalValue = assetGroup.reduce((acc, asset) => acc + sanitizeNumber(asset.value_usd), 0) || 1;
      return assetGroup
        .slice()
        .sort((a, b) => getAssetPerformancePercent(b) - getAssetPerformancePercent(a))
        .slice(0, 12)
        .map((asset) => {
          const valuePercent = getAssetPerformancePercent(asset);
          const allocationShare = (sanitizeNumber(asset.value_usd) / groupTotalValue) * 100;
          return {
            id: asset.symbol,
            label: asset.symbol,
            value: valuePercent,
            trend: [],
            riskScore: Math.min(100, Math.abs(valuePercent) * 3 + allocationShare * 0.5),
            allocation: Number.isFinite(allocationShare) ? allocationShare : undefined,
            volatility: Math.abs(valuePercent) * 1.2,
            type: assetType,
          } as HeatmapCell;
        });
    },
    [getAssetPerformancePercent, heatmapByType]
  );

  const buildHoldings = useCallback(
    (assetGroup: PortfolioAsset[]) =>
      assetGroup.map((asset) => {
        const normalizedExchange = (asset.exchange || '').toUpperCase();
        const pnlValue = getAssetPnlValue(asset);
        const sourceCount = asset.source_count ?? asset.sources?.length ?? 0;
        const exchangeList =
          asset.exchanges && asset.exchanges.length
            ? asset.exchanges
            : (asset.sources ?? []).map((source) => (source.exchange || 'Unknown').toUpperCase());

        return {
          symbol: asset.symbol,
          exchange: normalizedExchange || (exchangeList.length === 1 ? exchangeList[0] : 'MULTI'),
          position: `${sanitizeNumber(asset.amount).toLocaleString(undefined, {
            maximumFractionDigits: 4,
          })}`,
          avgPrice: formatCurrency(
            sanitizeNumber(asset.average_price ?? 0) > 0
              ? sanitizeNumber(asset.average_price ?? 0)
              : sanitizeNumber(asset.value_usd) / Math.max(sanitizeNumber(asset.amount), 1)
          ),
          currentPrice: formatCurrency(
            sanitizeNumber(asset.current_price ?? 0) > 0
              ? sanitizeNumber(asset.current_price ?? 0)
              : sanitizeNumber(asset.value_usd) / Math.max(sanitizeNumber(asset.amount), 1)
          ),
          value: formatCurrency(asset.value_usd),
          plPercent: (() => {
            const pnlPercent = sanitizeNumber(asset.pnl_percent);
            return Math.abs(pnlPercent) > 0.0001 ? pnlPercent : getAssetPerformancePercent(asset);
          })(),
          plValue: formatCurrency(pnlValue),
          plValueRaw: pnlValue,
          roi: getAssetPerformancePercent(asset),
          lastUpdated: lastUpdated
            ? new Date(lastUpdated).toLocaleString('en-US', { hour: '2-digit', minute: '2-digit' })
            : '—',
          sources: asset.sources,
          sourceCount: sourceCount || undefined,
          exchangeList: exchangeList.length ? exchangeList : undefined,
        };
      }),
    // Removed lastUpdated from dependencies to prevent re-renders on every update
    // lastUpdated is read from closure and will update when component re-renders
    // This prevents unnecessary useMemo recalculation that could trigger loops
    [getAssetPerformancePercent, getAssetPnlValue, assets]
  );

  const buildTrends = useCallback(
    (assetGroup: PortfolioAsset[]) => {
      const avg = assetGroup.length
        ? assetGroup.reduce((acc, asset) => acc + getAssetPerformancePercent(asset), 0) / assetGroup.length
        : 0;
      return [
        { label: '1W', roi: avg * 0.3 },
        { label: '1M', roi: avg * 0.6 },
        { label: '3M', roi: avg },
      ];
    },
    [getAssetPerformancePercent]
  );

  const composeNews = useCallback(
    (assetGroup: PortfolioAsset[]) => {
      const symbols = assetGroup
        .map((asset) => asset.symbol?.toUpperCase())
        .filter((symbol): symbol is string => Boolean(symbol));
      const collected = symbols.flatMap((symbol) => newsMap[symbol] ?? []);
      if (collected.length > 0) {
        return collected.slice(0, 6);
      }
      const globalFallback = newsMap.__GLOBAL__ ?? [];
      if (globalFallback.length > 0) {
        return globalFallback.slice(0, 6);
      }
      const fallback = assetGroup
        .filter((asset) => sanitizeNumber(asset.value_usd) > 0)
        .slice(0, 4)
        .map((asset, index) => {
          const pnlPercent = sanitizeNumber(asset.pnl_percent);
          const sentiment =
            pnlPercent > 1
              ? ('positive' as const)
              : pnlPercent < -1
                ? ('negative' as const)
                : ('neutral' as const);
          return {
            id: `fallback-${asset.symbol}-${index}`,
            title: `${asset.symbol} ${pnlPercent >= 0 ? 'gains' : 'pulls back'} ${Math.abs(pnlPercent).toFixed(2)}%`,
            source: 'Portfolio Insight',
            timestamp: new Date().toLocaleString(),
            url: undefined,
            summary:
              pnlPercent >= 0
                ? `${asset.symbol} extended its advance with unrealized P/L at ${pnlPercent.toFixed(2)}%. Monitor for continuation opportunities.`
                : `${asset.symbol} is under pressure (${pnlPercent.toFixed(2)}%). Review stop levels and downside protection.`,
            sentiment,
            symbol: asset.symbol?.toUpperCase(),
          };
        });
      return fallback;
    },
    [newsMap]
  );

  const stocksTabData: AssetTabData = useMemo(
    () => ({
      heatmap: buildHeatmap(stocksAssets, 'stocks'),
      holdings: buildHoldings(stocksAssets),
      trends: buildTrends(stocksAssets),
      news: composeNews(stocksAssets),
    }),
    [buildHeatmap, buildHoldings, buildTrends, composeNews, stocksAssets]
  );

  const cryptoTabData: AssetTabData = useMemo(
    () => ({
      heatmap: buildHeatmap(cryptoAssets, 'crypto'),
      holdings: buildHoldings(cryptoAssets),
      trends: buildTrends(cryptoAssets),
      news: composeNews(cryptoAssets),
    }),
    [buildHeatmap, buildHoldings, buildTrends, composeNews, cryptoAssets]
  );

  const handleToggleAlert = useCallback(
    async (symbol: string) => {
      const upperSymbol = symbol.toUpperCase();
      const existing = priceAlerts.find(
        (alert) => (alert?.symbol ?? '').toUpperCase() === upperSymbol
      );
      try {
        if (existing) {
          const updated = await portfolioService.updatePriceAlert(existing.id, {
            active: !existing.active,
          });
          setPriceAlerts((prev) => prev.map((alert) => (alert.id === existing.id ? updated : alert)));
        } else {
          const basePrice = parsePriceString(watchlistMap[upperSymbol]?.price);
          const created = await portfolioService.createPriceAlert({
            symbol: upperSymbol,
            condition: 'above',
            price: basePrice || 0,
            name: `${upperSymbol} auto alert`,
          });
          setPriceAlerts((prev) => [...prev, created]);
        }
      } catch (error) {
        logger.error('Failed to toggle alert', error);
      }
    },
    [parsePriceString, priceAlerts, watchlistMap]
  );

  const handleSelectDrilldown = useCallback((symbol: string) => {
    setSelectedDrilldown(symbol.toUpperCase());
  }, []);

  const drilldownOptions = useMemo(() => {
    const seen = new Set<string>();
    const options: string[] = [];
    assets.forEach((asset) => {
      const symbol = asset.symbol?.toUpperCase();
      if (!symbol || symbol === 'USD') {
        return;
      }
      if (sanitizeNumber(asset.value_usd) <= 0) {
        return;
      }
      if (!seen.has(symbol) && options.length < 10) {
        seen.add(symbol);
        options.push(symbol);
      }
    });
    return options;
  }, [assets]);

  useEffect(() => {
    if (!drilldownOptions.length) {
      setSelectedDrilldown('');
      return;
    }
    if (!selectedDrilldown || !drilldownOptions.includes(selectedDrilldown)) {
      setSelectedDrilldown(drilldownOptions[0]);
    }
  }, [drilldownOptions, selectedDrilldown]);

  // DISABLED: Automatic symbol history fetching - now manual only
  // useEffect(() => {
  //   if (!selectedDrilldown) {
  //     return;
  //   }
  //   const key = selectedDrilldown.toUpperCase();
  //   // Reset assetHistory for current symbol when historyDays changes
  //   // This ensures fresh data is fetched for the new time range
  //   setAssetHistory((prev) => {
  //     const updated = { ...prev };
  //     delete updated[key];
  //     return updated;
  //   });

  //   let cancelled = false;
  //   portfolioService
  //     .getSymbolHistory(key, historyDays)
  //     .then((series) => {
  //       if (!cancelled) {
  //         setAssetHistory((prev) => ({
  //           ...prev,
  //           [key]: series ?? [],
  //         }));
  //       }
  //     })
  //     .catch((error) => {
  //       if (!cancelled) {
  //         logger.debug(`Symbol history unavailable for ${key}`, error);
  //       }
  //     });

  //   return () => {
  //     cancelled = true;
  //   };
  // }, [historyDays, selectedDrilldown]);

  // DISABLED: Automatic benchmark history fetching - now manual only
  // useEffect(() => {
  //   let cancelled = false;
  //   const fetchPromises: Promise<void>[] = [];

  //   benchmarks.forEach((benchmark) => {
  //     if (!benchmark.active) {
  //       return;
  //     }
  //     const symbol = benchmarkSymbolMap[benchmark.id];
  //     if (!symbol) {
  //       return;
  //     }
  //     const existing = benchmarkSeries[benchmark.id];
  //     if (existing && existing.days === historyDays) {
  //       return;
  //     }
  //     const fetchPromise = portfolioService
  //       .getBenchmarkHistory(symbol, historyDays)
  //       .then((series) => {
  //         if (!cancelled) {
  //           setBenchmarkSeries((prev) => ({
  //             ...prev,
  //             [benchmark.id]: { days: historyDays, series: series ?? [] },
  //           }));
  //         }
  //       })
  //       .catch((error) => {
  //         if (!cancelled) {
  //           logger.debug(`Benchmark history unavailable for ${symbol}`, error);
  //         }
  //       });
  //     fetchPromises.push(fetchPromise);
  //   });

  //   return () => {
  //     cancelled = true;
  //   };
  // }, [benchmarks, benchmarkSeries, historyDays]);

  // Listen for dashboard refresh events (e.g., after transaction sync)
  // Use ref to prevent re-registration on every handleRefresh change
  const handleRefreshRef = useRef(handleRefresh);
  useEffect(() => {
    handleRefreshRef.current = handleRefresh;
  }, [handleRefresh]);

  // Track last refresh event time to debounce rapid events
  const lastRefreshEventRef = useRef<number>(0);
  const REFRESH_EVENT_DEBOUNCE_MS = 2000; // Minimum 2 seconds between refresh events

  // DISABLED: Dashboard refresh event listener - now manual only via button
  // useEffect(() => {
  //   const handleDashboardRefresh = () => {
  //     logger.debug('Dashboard refresh event received');
  //     
  //     // Debounce rapid refresh events
  //     const now = Date.now();
  //     const timeSinceLastEvent = now - lastRefreshEventRef.current;
  //     if (timeSinceLastEvent < REFRESH_EVENT_DEBOUNCE_MS) {
  //       logger.debug('Skipping dashboard refresh event - too soon since last event:', timeSinceLastEvent, 'ms');
  //       return;
  //     }
  //     
  //     // Use ref to avoid stale closure issues
  //     // Skip if already refreshing
  //     if (refreshInProgressRef.current) {
  //       logger.debug('Skipping dashboard refresh - already in progress');
  //       return;
  //     }
  //     
  //     lastRefreshEventRef.current = now;
  //     void handleRefreshRef.current();
  //   };

  //   window.addEventListener('dashboard:refresh', handleDashboardRefresh);
  //   logger.debug('Dashboard refresh event listener registered');

  //   return () => {
  //     window.removeEventListener('dashboard:refresh', handleDashboardRefresh);
  //   };
  // }, []); // Empty deps - only register once

  const drilldownTimeline = useMemo(() => {
    const key = selectedDrilldown?.toUpperCase();
    const series = key ? assetHistory[key] ?? [] : [];
    if (series.length > 1) {
      const base = series[0]?.close ?? 0;
      return series.map((point) => {
        const roi = base ? ((point.close - base) / base) * 100 : 0;
        return {
          date: new Date(point.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
          value: Number(roi.toFixed(2)),
        };
      });
    }
    const fallback = equityCurvePoints.slice(-20);
    if (fallback.length > 1) {
      const base = fallback[0]?.value ?? 0;
      return fallback.map((point) => ({
        date: point.date,
        value: base ? Number((((point.value ?? 0) - base) / base * 100).toFixed(2)) : 0,
      }));
    }
    return [];
  }, [assetHistory, equityCurvePoints, selectedDrilldown]);

  const roiAnalyticsData: RoiAnalyticsData = useMemo(() => {
    const totalAbsPnl =
      assets.reduce((acc, asset) => acc + Math.abs(getAssetPnlValue(asset)), 0) || 1;
    const contributions = [...assets]
      .sort((a, b) => Math.abs(getAssetPnlValue(b)) - Math.abs(getAssetPnlValue(a)))
      .slice(0, 8)
      .map((asset, index) => {
        const pnlValue = getAssetPnlValue(asset);
        return {
          asset: asset.symbol,
          contribution: Number(((pnlValue / totalAbsPnl) * 100).toFixed(2)),
          color: palette[index % palette.length],
        };
      });

    const gainers = [...assets]
      .map((asset) => ({
        asset: asset.symbol,
        value: formatCurrency(asset.value_usd),
        percent: getAssetPerformancePercent(asset),
      }))
      .filter((entry) => entry.percent > 0)
      .sort((a, b) => b.percent - a.percent)
      .slice(0, 5)
      .map((entry) => ({
        asset: entry.asset,
        value: entry.value,
        percent: entry.percent,
        direction: 'up' as const,
      }));

    const losers = [...assets]
      .map((asset) => ({
        asset: asset.symbol,
        value: formatCurrency(asset.value_usd),
        percent: getAssetPerformancePercent(asset),
      }))
      .filter((entry) => entry.percent < 0)
      .sort((a, b) => a.percent - b.percent)
      .slice(0, 5)
      .map((entry) => ({
        asset: entry.asset,
        value: entry.value,
        percent: Math.abs(entry.percent),
        direction: 'down' as const,
      }));

    const metricsBase = sanitizeNumber(
      performanceAnalytics?.total_return ?? summary?.total_pnl_percent
    );

    const drilldownMetrics: DrilldownMetrics = {
      beta: 1,
      volatility: sanitizeNumber(performanceAnalytics?.volatility),
      sharpe: sanitizeNumber(performanceAnalytics?.sharpe_ratio),
    };
    const roiTimeline = drilldownTimeline.length
      ? drilldownTimeline
      : [{ date: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric' }), value: 0 }];

    const forecasts = assets
      .filter((asset) => sanitizeNumber(asset.value_usd) > 0)
      .sort((a, b) => sanitizeNumber(b.value_usd) - sanitizeNumber(a.value_usd))
      .slice(0, 4)
      .map((asset) => {
        const performance = getAssetPerformancePercent(asset);
        const baseVol = Math.min(Math.abs(performance), 30);
        const expectedReturn = performance * 0.6;
        const confidence = Math.max(35, Math.min(90, 80 - baseVol));
        const horizon =
          timeRange === '24h'
            ? 'Next 3 days'
            : timeRange === '7d'
              ? 'Next 2 weeks'
              : 'Next month';
        const narrative =
          expectedReturn >= 0
            ? `${asset.symbol} momentum stays constructive. Watch for potential take-profit around ${formatCurrency(
                sanitizeNumber(asset.value_usd) * (1 + expectedReturn / 100)
              )}.`
            : `${asset.symbol} showing downside pressure. Consider tightening stops and monitoring support levels.`;
        return {
          symbol: asset.symbol,
          horizon,
          expectedReturn,
          confidence,
          narrative,
        };
      });

    return {
      globalPL: metricsBase,
      contributions,
      topGainers: gainers,
      topLosers: losers,
      drilldownOptions,
      selectedDrilldown: selectedDrilldown || drilldownOptions[0] || '',
      drilldown: {
        symbol: selectedDrilldown || drilldownOptions[0] || '',
        roiTimeline,
        metrics: drilldownMetrics,
      },
      forecast: forecasts,
      notice: performanceAnalytics?.message || undefined,
      sampleCount: performanceAnalytics?.data_points,
    };
  }, [
    assets,
    drilldownOptions,
    drilldownTimeline,
    getAssetPerformancePercent,
    getAssetPnlValue,
    performanceAnalytics?.sharpe_ratio,
    performanceAnalytics?.total_return,
    performanceAnalytics?.volatility,
    performanceAnalytics?.message,
    performanceAnalytics?.data_points,
    selectedDrilldown,
    summary?.total_pnl_percent,
    timeRange,
  ]);

  const equityCurve: EquityCurveConfig = useMemo(() => {
    const filteredPoints = equityCurvePoints.filter((point) => {
      if (equityFilter === 'stocks') {
        return Number.isFinite(point.stocks);
      }
      if (equityFilter === 'crypto') {
        return Number.isFinite(point.crypto);
      }
      return true;
    });

    const normalizedPoints = filteredPoints.map((point) => ({
      date: point.date,
      value: point.value,
      stocks: equityFilter !== 'crypto' ? point.stocks : undefined,
      crypto: equityFilter !== 'stocks' ? point.crypto : undefined,
      benchmarkValues: point.benchmarkValues,
    }));

    const normalizedPrevious = previousEquityCurvePoints
      ? previousEquityCurvePoints
          .filter((point) => Number.isFinite(point.value))
          .map((point) =>
            point.value === 0
              ? {
                  ...point,
                  value: Number.EPSILON,
                }
              : point
          )
      : undefined;

    return {
      points: normalizedPoints,
      benchmarks,
      filter: equityFilter,
      previousPoints: normalizedPrevious,
      comparison: equityComparison,
    };
  }, [benchmarks, equityComparison, equityCurvePoints, equityFilter, previousEquityCurvePoints]);

  const handleBenchmarkToggle = useCallback((id: string) => {
    setBenchmarks((prev) =>
      prev.map((benchmark) =>
        benchmark.id === id ? { ...benchmark, active: !benchmark.active } : benchmark
      )
    );
  }, []);

  const handleFiltersChange = useCallback((change: Partial<FiltersState>) => {
    setFilters((prev) => ({ ...prev, ...change }));
  }, []);

  const handleTimeRangeChange = useCallback(
    (range: TimeRange) => {
      setTimeRange(range);
      handleFiltersChange({ timeRange: range });
      setEquityFilter('total');
      setHistoryDays(resolveDaysForRangeValue(range));
    },
    [handleFiltersChange]
  );

  const handleResetFilters = useCallback(() => {
    setFilters(defaultFilters);
    setTimeRange(defaultFilters.timeRange);
    setHistoryDays(resolveDaysForRangeValue(defaultFilters.timeRange));
    setEquityFilter('total');
    showToast('Filters reset to default', 'info');
  }, [showToast]);

  const handleAddAsset = useCallback(() => {
    navigate('/transactions');
  }, [navigate]);

  const handleAlertsClick = useCallback(() => {
    navigate('/price-alerts');
  }, [navigate]);

  // Keyboard shortcuts
  const shortcuts = useMemo<KeyboardShortcut[]>(() => [
    COMMON_SHORTCUTS.REFRESH(() => {
      void handleRefresh();
    }),
    COMMON_SHORTCUTS.GOALS(() => {
      navigate('/goals');
    }),
    COMMON_SHORTCUTS.SEARCH(() => {
      // Will be handled by Command Palette in App.tsx
      // This is a placeholder for now
    }),
    COMMON_SHORTCUTS.HELP(() => {
      setShortcutsDialogOpen(true);
    }),
  ], [handleRefresh, navigate]);

  useKeyboardShortcuts({
    enabled: true,
    shortcuts,
  });

  const assetIssueLookup = useMemo(() => {
    const map: Record<string, string[]> = {};
    assets.forEach((asset) => {
      if (asset.issues?.length) {
        map[`${(asset.exchange || '').toUpperCase()}:${asset.symbol}`] = asset.issues;
      }
    });
    return map;
  }, [assets]);

  // Show loading skeleton only when actively loading
  if (loading && !summary) {
    return <SkeletonLoader type="dashboard" />;
  }

  // Show button to load dashboard data if no data is loaded yet
  if (!loading && !summary) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '60vh',
            gap: 3,
            textAlign: 'center',
          }}
        >
          <Typography variant="h5" sx={{ fontWeight: 600, mb: 1 }}>
            Dashboard Ready
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
            Click the button below to load your portfolio data
          </Typography>
          <Button
            variant="contained"
            size="large"
            onClick={() => handleRefresh()}
            disabled={refreshing}
            startIcon={refreshing ? <CircularProgress size={20} /> : <RefreshIcon />}
            sx={{ minWidth: 200 }}
          >
            {refreshing ? 'Loading...' : 'Load Dashboard'}
          </Button>
        </Box>
      </Container>
    );
  }

  return (
    <>
      {/* Migration Status Banner */}
      {showMigrationBanner && migrationStatus?.migration_complete && (
        <Alert
          severity="success"
          onClose={() => setShowMigrationBanner(false)}
          sx={{
            mb: 2,
            mx: 2,
            mt: 2,
            borderRadius: 2,
          }}
        >
          <AlertTitle>Database Migration Complete</AlertTitle>
          All your data has been successfully migrated to the database. 
          {migrationStatus.total_items > 0 && (
            <Typography variant="body2" sx={{ mt: 0.5 }}>
              {migrationStatus.total_items} items migrated successfully.
            </Typography>
          )}
        </Alert>
      )}
        <Box
          sx={{
          display: 'flex',
          flexDirection: { xs: 'column', xl: 'row' },
          gap: { xs: 3, md: 4, xl: 5 },
        }}
      >
        {summaryWarnings.length > 0 && (
          <Alert severity="warning" sx={{ mb: 3, borderRadius: 2 }}>
            <AlertTitle>Data validation warnings</AlertTitle>
            <List dense>
              {summaryWarnings.map((warning) => (
                <ListItem key={warning} sx={{ px: 0, py: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 40 }}>
                    <WarningAmberIcon color="warning" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary={warning} />
                </ListItem>
              ))}
            </List>
          </Alert>
        )}

        <Box 
          component="main"
          aria-label="Dashboard main content"
          sx={{ flex: 1, display: 'flex', flexDirection: 'column', gap: { xs: 3.5, md: 4.5 } }}
        >
          <React.Suspense fallback={<Box sx={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><CircularProgress /></Box>}>
            <GlobalStatusBar
              portfolioName="Global Portfolio"
              lastUpdated={
                lastUpdated
                  ? new Date(lastUpdated).toLocaleString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })
                  : '—'
              }
              kpis={kpis}
              timeRange={timeRange}
              onTimeRangeChange={handleTimeRangeChange}
              onAddAsset={handleAddAsset}
              onAlertsClick={handleAlertsClick}
              onRefresh={handleRefresh}
              refreshing={refreshing}
              onSyncTrades={handleSyncTrades}
              syncing={syncing}
            />
          </React.Suspense>

          {quickInsights.length > 0 && (
            <Box
              component="section"
              aria-label="Quick insights"
              sx={{ px: { xs: 1, md: 0 }, mb: 1 }}
            >
              <Stack
                direction={{ xs: 'column', md: 'row' }}
                spacing={2.5}
                useFlexGap
              >
                {quickInsights.map((insight) => {
                  const cardColor =
                    insight.severity === 'warning'
                      ? 'warning.light'
                      : insight.positive === true
                      ? 'success.light'
                      : insight.positive === false
                      ? 'error.light'
                      : 'background.paper';
                  const iconBgColor =
                    insight.severity === 'warning'
                      ? 'warning.light'
                      : insight.positive === true
                      ? 'success.light'
                      : insight.positive === false
                      ? 'error.light'
                      : 'action.hover';
                  const deltaColor =
                    insight.delta === undefined
                      ? 'text.secondary'
                      : insight.delta >= 0
                      ? 'success.main'
                      : 'error.main';
                  const tooltipText = insight.onClick 
                    ? `Click to view details about ${insight.label.toLowerCase()}. ${insight.helper || ''}`
                    : insight.helper || `Current ${insight.label.toLowerCase()} status`;
                  
                  return (
                    <Tooltip 
                      key={insight.id}
                      title={tooltipText} 
                      arrow 
                      placement="top"
                      disableHoverListener={!insight.onClick && !insight.helper}
                    >
                      <Card
                        variant="outlined"
                        onClick={insight.onClick}
                        aria-label={`${insight.label}: ${insight.primary}. ${insight.helper || ''}`}
                        sx={{
                          flex: '1 1 auto',
                          minWidth: { xs: '100%', md: 200 },
                          cursor: insight.onClick ? 'pointer' : 'default',
                          borderColor:
                            insight.severity === 'warning'
                              ? 'warning.light'
                              : insight.positive === true
                              ? 'success.light'
                              : insight.positive === false
                              ? 'error.light'
                              : 'divider',
                          backgroundColor: cardColor,
                          borderRadius: 2,
                          transition: 'all 0.2s ease-in-out',
                          '&:hover': insight.onClick
                            ? {
                                transform: 'translateY(-2px)',
                                boxShadow: 4,
                              }
                            : undefined,
                        }}
                      >
                        <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, p: 2.5 }}>
                          <Stack direction="row" spacing={1.5} alignItems="center">
                            {insight.icon && (
                              <Box
                                sx={{
                                  width: 44,
                                  height: 44,
                                  borderRadius: '50%',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  backgroundColor: iconBgColor,
                                  opacity: 0.9,
                                }}
                              >
                                {insight.icon}
                              </Box>
                            )}
                            <Box sx={{ flex: 1, minWidth: 0 }}>
                              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5, fontSize: '0.75rem', fontWeight: 500 }}>
                                {insight.label}
                              </Typography>
                              <Typography variant="h6" sx={{ fontWeight: 700, lineHeight: 1.2, fontSize: '1.125rem' }}>
                                {insight.primary}
                              </Typography>
                            </Box>
                          </Stack>
                          {insight.helper && (
                            <Typography variant="body2" color={deltaColor} sx={{ mt: 0.5, fontSize: '0.875rem', fontWeight: 500 }}>
                              {insight.helper}
                            </Typography>
                          )}
                        </CardContent>
                      </Card>
                    </Tooltip>
                  );
                })}
              </Stack>
            </Box>
          )}

          <React.Suspense fallback={<Box sx={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><CircularProgress /></Box>}>
            <HealthScorePanel />
          </React.Suspense>

          <React.Suspense fallback={<Box sx={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><CircularProgress /></Box>}>
            <PortfolioOverview
              stocksSummary={stocksSummary}
              cryptoSummary={cryptoSummary}
              allocation={allocation}
              equityCurve={equityCurve}
              onEquityFilterChange={setEquityFilter}
              onToggleBenchmark={handleBenchmarkToggle}
            />
          </React.Suspense>

          <React.Suspense fallback={<Box sx={{ height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><CircularProgress /></Box>}>
            <AssetTabs
              stocks={stocksTabData}
              crypto={cryptoTabData}
              defaultTab="stocks"
              viewMode={filters.viewMode}
              assetIssueLookup={assetIssueLookup}
              changeLookup={changeHighlights}
            />
          </React.Suspense>

          <React.Suspense fallback={<Box sx={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><CircularProgress /></Box>}>
            <WatchlistSection
              items={watchlistItems}
              alerts={recentAlerts}
              onToggleAlert={handleToggleAlert}
            />
          </React.Suspense>

          <React.Suspense fallback={<Box sx={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><CircularProgress /></Box>}>
            <RiskAlertsPanel />
          </React.Suspense>

          <React.Suspense fallback={<Box sx={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><CircularProgress /></Box>}>
            <RebalancingSuggestionsPanel />
          </React.Suspense>

          <React.Suspense fallback={<Box sx={{ height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><CircularProgress /></Box>}>
            <RoiAnalytics
              data={roiAnalyticsData}
              onSelectAsset={handleSelectDrilldown}
            />
          </React.Suspense>
                  </Box>

        <Box
          component="aside"
          aria-label="Dashboard controls and filters"
          sx={{
            minWidth: { xl: 320 },
            maxWidth: { xl: 360 },
            width: { xs: '100%', xl: '24%' },
            display: 'flex',
            flexDirection: 'column',
            gap: 3.5,
          }}
        >
          <React.Suspense fallback={<Box sx={{ height: 200 }}><CircularProgress /></Box>}>
            <FiltersPanel
              filters={filters}
              onFiltersChange={handleFiltersChange}
              onReset={handleResetFilters}
            />
          </React.Suspense>
          <Stack spacing={1.5} sx={{ display: { xs: 'none', xl: 'flex' }, color: 'text.secondary', px: 1 }}>
            <Typography variant="caption" sx={{ fontSize: '0.8125rem', lineHeight: 1.6 }}>
              Use filters to focus on a region, sector, or asset class. View toggle supports table, cards, and chart views.
            </Typography>
            <Typography variant="caption" sx={{ fontSize: '0.8125rem', lineHeight: 1.6 }}>
              Manual refresh pulls the latest balances and analytics without waiting for the scheduled sync.
            </Typography>
          </Stack>
        </Box>
      </Box>

      <Toast
        open={toast.open}
        message={toast.message}
        severity={toast.severity ?? 'info'}
        onClose={hideToast}
      />
      
      <KeyboardShortcutsDialog
        open={shortcutsDialogOpen}
        onClose={() => setShortcutsDialogOpen(false)}
        shortcuts={shortcuts}
      />
      
      <OnboardingTour
        steps={dashboardOnboardingSteps}
        open={onboardingTourOpen}
        onClose={() => setOnboardingTourOpen(false)}
        storageKey="dashboard_onboarding_completed"
      />
      
      <QuickActionsToolbar newAlertsCount={recentAlerts.filter(a => a.status === 'new').length} />
    </>
  );
};

export default Dashboard;


