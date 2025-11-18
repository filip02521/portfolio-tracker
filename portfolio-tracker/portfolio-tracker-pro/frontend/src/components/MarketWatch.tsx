import React, { useState, useEffect, useRef, useMemo, useCallback, Suspense } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  IconButton,
  Chip,
  Tooltip,
  Alert,
  TextField,
  InputAdornment,
  Popover,
  RadioGroup,
  Radio,
  FormControlLabel,
  Button,
  Autocomplete,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tabs,
  Tab,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip as MuiChip,
  useMediaQuery,
  useTheme,
  Checkbox,
  FormGroup,
  Divider,
  CircularProgress,
} from '@mui/material';
import {
  Add,
  Refresh,
  NotificationsOutlined,
  DeleteOutline,
  FileDownload,
  FileUpload,
  AccountBalance,
  ArrowUpward,
  ArrowDownward,
  ViewCompactAlt,
} from '@mui/icons-material';
import { TrendIndicator } from './common/TrendIndicator';
import { SkeletonLoader } from './common/SkeletonLoader';
import { useToast, Toast } from './common/Toast';
import { portfolioService } from '../services/portfolioService';
import { logger } from '../utils/logger';
// Lazy load heavy components for better code splitting
const MarketWatchDrawer = React.lazy(() => import('./MarketWatchDrawer').then(module => ({ default: module.MarketWatchDrawer })));
const WatchlistAddDialog = React.lazy(() => import('./WatchlistAddDialog').then(module => ({ default: module.WatchlistAddDialog })));
// Virtualized list (keep after all import statements to satisfy import/first)
// eslint-disable-next-line @typescript-eslint/no-var-requires
const RW: any = require('react-window');
const List: any = RW.List || RW.FixedSizeList;

interface WatchlistItem {
  symbol: string;
  name: string;
  price: number;
  change24h: number;
  changePercent24h: number;
  volume?: number;
  volume_24h?: number;
  marketCap?: number;
  market_cap?: number;
  high_24h?: number;
  low_24h?: number;
  type: 'crypto' | 'stock';
  categories?: string[];
  tags?: string[];
  ddScore?: number;
  ddVerdict?: string;
  ddConfidence?: number;
}

// Style constants - extracted from inline styles for performance
const styles = {
  cardContent: { p: 3 },
  headerContainer: { 
    display: 'flex', 
    justifyContent: 'space-between', 
    alignItems: { xs: 'flex-start', sm: 'center' },
    flexDirection: { xs: 'column', sm: 'row' },
    mb: 3, 
    flexWrap: 'wrap', 
    gap: { xs: 1.5, sm: 2 },
    '& > *': {
      minWidth: 0, // Prevent overflow
    }
  },
  titleContainer: { 
    display: 'flex', 
    alignItems: 'center', 
    gap: 1.5 
  },
  statusContainer: { 
    display: 'flex', 
    alignItems: 'center', 
    gap: 1, 
    flex: { xs: 'none', sm: 1 }, 
    justifyContent: { xs: 'flex-start', sm: 'center' }, 
    minWidth: { xs: 'auto', sm: 200 },
    width: { xs: '100%', sm: 'auto' },
    order: { xs: 3, sm: 2 }
  },
  actionsContainer: { 
    display: 'flex', 
    alignItems: 'center', 
    gap: { xs: 1, sm: 2 },
    flexWrap: 'wrap',
    width: { xs: '100%', sm: 'auto' },
    order: { xs: 2, sm: 3 },
    justifyContent: { xs: 'flex-start', sm: 'flex-end' }
  },
  actionsGroup: { 
    display: 'flex', 
    alignItems: 'center', 
    gap: 1, 
    pl: 2, 
    borderLeft: '1px solid', 
    borderColor: 'divider' 
  },
  filtersContainer: { 
    display: 'flex', 
    justifyContent: 'space-between', 
    alignItems: { xs: 'flex-start', sm: 'center' },
    flexDirection: { xs: 'column', sm: 'row' },
    mb: 3, 
    gap: { xs: 1.5, sm: 2 }, 
    flexWrap: 'wrap' 
  },
  quickFiltersContainer: { 
    display: 'flex', 
    gap: { xs: 0.5, sm: 0.5 },
    flexWrap: 'wrap'
  },
  filtersRow: { 
    display: 'flex', 
    alignItems: 'center', 
    gap: { xs: 1, sm: 2 },
    flexWrap: 'wrap',
    width: { xs: '100%', sm: 'auto' }
  },
  chipCrypto: { 
    bgcolor: 'rgba(245, 158, 11, 0.15)', 
    color: 'warning.main' 
  },
  chipStock: { 
    bgcolor: 'rgba(59, 130, 246, 0.15)', 
    color: 'info.main' 
  },
  rowBase: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderRadius: 2,
    border: '1px solid',
    borderColor: 'divider',
    bgcolor: 'background.paper',
    transition: 'all 0.2s ease-in-out',
    cursor: 'pointer',
    minWidth: 0, // Prevent overflow
    overflow: 'hidden', // Prevent content from overflowing
  },
  rowHover: {
    borderColor: 'primary.main',
    bgcolor: 'rgba(37, 99, 235, 0.05)',
    boxShadow: '0 2px 8px rgba(37, 99, 235, 0.1)',
    transform: 'translateX(4px)',
  },
  sparklineContainer: {
    p: 0.5,
    borderRadius: 1,
    bgcolor: 'rgba(0, 0, 0, 0.02)',
    mr: { xs: 1, sm: 2 },
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0
  },
  iconButtonAlert: {
    color: 'text.secondary',
    '&:hover': { 
      color: 'warning.main',
      bgcolor: 'rgba(245, 158, 11, 0.1)'
    }
  },
  iconButtonDelete: {
    color: 'text.secondary',
    '&:hover': { 
      color: 'error.main',
      bgcolor: 'rgba(239, 68, 68, 0.1)'
    }
  },
  symbolContainer: { 
    flex: 1, 
    minWidth: 0 
  },
  priceContainer: { 
    textAlign: 'right', 
    mr: { xs: 1, sm: 2 },
    minWidth: 0,
    flexShrink: 0
  },
  actionsBox: { 
    display: 'flex', 
    alignItems: 'center', 
    gap: 0.5 
  },
  manageDialogContent: { 
    display: 'flex', 
    flexDirection: 'column', 
    gap: 3 
  },
  symbolItem: {
    display: 'flex', 
    alignItems: 'center', 
    justifyContent: 'space-between', 
    p: 1.5, 
    border: '1px solid', 
    borderColor: 'divider', 
    borderRadius: 1.5,
    '&:hover': { bgcolor: 'rgba(0, 0, 0, 0.02)' }
  },
  importButtons: { 
    display: 'flex', 
    gap: 1, 
    mt: 2, 
    flexWrap: 'wrap' 
  },
  advancedFiltersContainer: {
    display: 'flex', 
    flexDirection: 'column', 
    gap: 1.5, 
    mb: 1, 
    p: 1.5, 
    bgcolor: 'rgba(0, 0, 0, 0.02)', 
    borderRadius: 1 
  },
  priceGrid: { 
    display: 'grid', 
    gridTemplateColumns: '1fr 1fr', 
    gap: 1 
  },
  popoverPaper: { 
    p: 2, 
    width: { xs: 'calc(100vw - 32px)', sm: 300 },
    maxWidth: { xs: 'calc(100vw - 32px)', sm: 300 }
  },
  emptyStateContainer: { 
    textAlign: 'center', 
    py: 4 
  },
  emptyStateInput: { 
    width: 220 
  },
} as const;

const MarketWatch: React.FC = () => {
  const { toast, showToast, hideToast } = useToast();
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [usingFallback, setUsingFallback] = useState(false);
  const esRef = useRef<EventSource | null>(null);
  const [userSymbols, setUserSymbols] = useState<string[]>([]);
  const [newSymbol, setNewSymbol] = useState<string>('');
  const [adding, setAdding] = useState(false);
  const [priceSeries, setPriceSeries] = useState<Record<string, number[]>>({});
  const [alertAnchor, setAlertAnchor] = useState<HTMLElement | null>(null);
  const [alertSymbol, setAlertSymbol] = useState<string>('');
  const [alertCond, setAlertCond] = useState<'above' | 'below'>('above');
  const [alertPrice, setAlertPrice] = useState<string>('');
  const [manageOpen, setManageOpen] = useState(false);
  const [batchAlertsOpen, setBatchAlertsOpen] = useState(false);
  const [selectedBatchSymbols, setSelectedBatchSymbols] = useState<Set<string>>(new Set());
  const [batchAlertCond, setBatchAlertCond] = useState<'above' | 'below'>('above');
  const [batchAlertPrice, setBatchAlertPrice] = useState<string>('');
  const [batchAlertType, setBatchAlertType] = useState<'price' | 'percent'>('price');
  const [batchCreating, setBatchCreating] = useState(false);
  const [bulkSelectMode, setBulkSelectMode] = useState(false);
  const [selectedSymbols, setSelectedSymbols] = useState<Set<string>>(new Set());
  const [bulkOperationOpen, setBulkOperationOpen] = useState(false);
  const [pricesMap, setPricesMap] = useState<Record<string, WatchlistItem>>({});
  const [batchIndex, setBatchIndex] = useState(0);
  const [tab, setTab] = useState<'all'|'stocks'|'crypto'>('all');
  const [sortKey, setSortKey] = useState<'symbol'|'price'|'change'>('symbol');
  const [sortDir, setSortDir] = useState<'asc'|'desc'>('asc');
  const [quickFilter, setQuickFilter] = useState<'none'|'gainers'|'losers'|'gt2'|'lt-2'>('none');
  const [advancedFiltersOpen, setAdvancedFiltersOpen] = useState(false);
  const [filterCategory, setFilterCategory] = useState<string>('');
  const [filterPriceMin, setFilterPriceMin] = useState<string>('');
  const [filterPriceMax, setFilterPriceMax] = useState<string>('');
  const [filterChangeMin, setFilterChangeMin] = useState<string>('');
  const [filterChangeMax, setFilterChangeMax] = useState<string>('');
  const [filterDdScoreMin, setFilterDdScoreMin] = useState<string>('');
  const [filterDdScoreMax, setFilterDdScoreMax] = useState<string>('');
  const [availableCategories, setAvailableCategories] = useState<string[]>([]);
  const [suggestions, setSuggestions] = useState<Array<{ symbol: string; name?: string; type?: string }>>([]);
  const suggestTimer = useRef<number | null>(null);
  const [compact, setCompact] = useState(false);
  const [connStatus, setConnStatus] = useState<'idle'|'live'|'retry'|'rotating'>('idle');
  const [retryIn, setRetryIn] = useState<number>(0);
  const retryTimerRef = useRef<number | null>(null);
  const sseFailCountRef = useRef<number>(0);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const MAX_RETRIES = 3;
  const INITIAL_RETRY_DELAY = 1000; // 1 second
  const MAX_RETRY_DELAY = 30000; // 30 seconds
  const [hoverInfo, setHoverInfo] = useState<{ symbol: string; value: number; date: string } | null>(null);
  const [lastUpdated, setLastUpdated] = useState<number | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerSymbol, setDrawerSymbol] = useState<string | null>(null);
  const [filtersAnchor, setFiltersAnchor] = useState<HTMLElement | null>(null);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const hoverThrottleRef = useRef<number>(0);
  const fileInputRef = useRef<HTMLInputElement>(null);
  // Persist UI
  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem('mw_ui') || '{}');
      if (saved.tab) setTab(saved.tab);
      if (saved.sortKey) setSortKey(saved.sortKey);
      if (saved.sortDir) setSortDir(saved.sortDir);
      if (saved.quickFilter) setQuickFilter(saved.quickFilter);
      if (typeof saved.compact === 'boolean') setCompact(saved.compact);
      const lastSym = localStorage.getItem('mw_last_symbol');
      if (lastSym) setNewSymbol(lastSym);
    } catch {}
  }, []);
  useEffect(() => {
    const data = { tab, sortKey, sortDir, quickFilter, compact };
    try { localStorage.setItem('mw_ui', JSON.stringify(data)); } catch {}
  }, [tab, sortKey, sortDir, quickFilter, compact]);

  // DISABLED: Automatic data loading - now manual only via refresh button
  // useEffect(() => {
  //   bootstrap();
  //   // Try SSE after initial load
  //   if (userSymbols.length <= 4) {
  //     tryStartSSE();
  //   }
  //   return () => {
  //     cleanupSSE();
  //     // Clean up rotation timer
  //     if ((esRef as any).rotationTimer) {
  //       window.clearInterval((esRef as any).rotationTimer);
  //       (esRef as any).rotationTimer = null;
  //     }
  //     // Clean up suggest timer
  //     if (suggestTimer.current) {
  //       window.clearTimeout(suggestTimer.current);
  //       suggestTimer.current = null;
  //     }
  //   };
  // }, []);

  const bootstrap = async () => {
    try {
      const data = await portfolioService.getUserWatchlist(true);
      setUserSymbols(data.symbols);
      // Extract available categories from metadata and update watchlist items
      if (data.metadata) {
        const categories = new Set<string>();
        Object.values(data.metadata).forEach((meta: any) => {
          if (meta.categories) {
            meta.categories.forEach((cat: string) => categories.add(cat));
          }
        });
        setAvailableCategories(Array.from(categories).sort());
        
        // Update watchlist items with metadata
        setWatchlist(prev => prev.map(item => ({
          ...item,
          categories: data.metadata?.[item.symbol]?.categories || [],
          tags: data.metadata?.[item.symbol]?.tags || []
        })));
      }
    } catch (err: any) {
      // If not authenticated, show fallback data instead of failing silently
      logger.log('Could not load user watchlist (may need login):', err?.userMessage || err?.message);
      if (err?.response?.status === 401 || err?.userMessage?.includes('authenticated')) {
        // User not logged in - will show fallback data
        setUserSymbols([]);
      }
    }
    await fetchWatchlist();
    // Preload history for sparkline (up to first 8 symboli, 7 dni) - using batch request
    try {
      const baseData = await portfolioService.getUserWatchlist();
      const base = baseData.symbols.slice(0, 8);
      if (base && base.length) {
        try {
          // Use batch endpoint instead of individual requests
          const histories = await portfolioService.getSymbolHistoryBatch(base, 7);
          setPriceSeries((prev) => {
            const next = { ...prev } as Record<string, number[]>;
            Object.entries(histories).forEach(([sym, series]) => {
              if (series && series.length > 0) {
                next[sym] = series.map(p => p.close);
              }
            });
            return next;
          });
        } catch {}
      }
    } catch {}
    // Start rotation polling if mamy >4 symboli
    // For larger watchlists, use batch endpoint with larger chunks
    if (userSymbols.length > 4) {
      setConnStatus('rotating');
      const batchSize = userSymbols.length > 20 ? 20 : 4; // Use larger batches for large watchlists
      const id = window.setInterval(async () => {
        if (!userSymbols.length) return;
        setBatchIndex((idx) => {
          const start = (idx * batchSize) % userSymbols.length;
          const batch = userSymbols.slice(start, start + batchSize);
          (async () => {
            try {
              // Use batch endpoint for larger batches
              const data = batch.length > 4 
                ? await portfolioService.getWatchlistPricesBatch(batch, batchSize)
                : await portfolioService.getWatchlistPrices(batch);
              const updated: WatchlistItem[] = (data.prices || []).map((p: any) => ({
                symbol: p.symbol,
                name: p.name || p.symbol,
                price: p.price,
                change24h: p.change_24h || 0,
                changePercent24h: p.change_percent_24h || 0,
                volume: p.volume_24h || p.volume,
                volume_24h: p.volume_24h || p.volume,
                marketCap: p.market_cap || p.marketCap,
                market_cap: p.market_cap || p.marketCap,
                high_24h: p.high_24h,
                low_24h: p.low_24h,
                type: p.type || 'stock'
              }));
              setPricesMap((prev) => {
                const next = { ...prev } as Record<string, WatchlistItem>;
                for (const it of updated) next[it.symbol] = it;
                return next;
              });
              setWatchlist((prev) => {
                const next = userSymbols.map(sym => {
                  const existing = pricesMap[sym];
                  if (existing) return existing;
                  const updatedItem = updated.find(u => u.symbol === sym);
                  if (updatedItem) return updatedItem;
                  const prevItem = prev.find(w => w.symbol === sym);
                  if (prevItem) return prevItem;
                  return { symbol: sym, name: sym, price: 0, change24h: 0, changePercent24h: 0, type: 'stock' } as WatchlistItem;
                });
                return next.filter(item => item !== null && item !== undefined);
              });
            } catch {}
          })();
          return idx + 1;
        });
      }, 8000);
      // store timer on ref
      (esRef as any).rotationTimer = id;
    }
  };

  const cleanupSSE = useCallback(() => {
    if (esRef.current) {
      esRef.current.close();
      esRef.current = null;
    }
    if (retryTimerRef.current) {
      window.clearInterval(retryTimerRef.current);
      retryTimerRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      window.clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    // Clean up rotation timer if it exists
    if ((esRef as any).rotationTimer) {
      window.clearInterval((esRef as any).rotationTimer);
      (esRef as any).rotationTimer = null;
    }
    // Clean up suggest timer if it exists
    if (suggestTimer.current) {
      window.clearTimeout(suggestTimer.current);
      suggestTimer.current = null;
    }
  }, []);

  const startPollingFallback = useCallback(() => {
    // Clear any existing polling
    if ((esRef as any).rotationTimer) {
      window.clearInterval((esRef as any).rotationTimer);
    }
    
    const allSymbols = userSymbols.length ? userSymbols : watchlist.map(w => w.symbol);
    const batchSize = allSymbols.length > 20 ? 20 : (allSymbols.length > 4 ? 10 : 4);
    const symbols = allSymbols.slice(0, batchSize);
    if (symbols.length === 0) return;
    
    let batchIndex = 0;
    const id = window.setInterval(async () => {
      if (!userSymbols.length && watchlist.length === 0) {
        window.clearInterval(id);
        return;
      }
      
      try {
        // Rotate through batches for large watchlists
        const currentBatch = allSymbols.length > batchSize
          ? allSymbols.slice(batchIndex * batchSize, (batchIndex + 1) * batchSize)
          : symbols;
        batchIndex = (batchIndex + 1) % Math.ceil(allSymbols.length / batchSize);
        
        const data = currentBatch.length > 4
          ? await portfolioService.getWatchlistPricesBatch(currentBatch, batchSize)
          : await portfolioService.getWatchlistPrices(currentBatch);
        const updated: WatchlistItem[] = (data.prices || []).map((p: any) => ({
          symbol: p.symbol,
          name: p.name || p.symbol,
          price: p.price,
          change24h: p.change_24h || 0,
          changePercent24h: p.change_percent_24h || 0,
          type: p.type || 'stock'
        }));
        setPricesMap((prev) => {
          const next = { ...prev } as Record<string, WatchlistItem>;
          for (const it of updated) next[it.symbol] = it;
          return next;
        });
        setWatchlist((curr) => {
          const syms = allSymbols.length ? allSymbols : curr.map(w => w.symbol);
          return syms.map(sym => {
            const existing = pricesMap[sym];
            if (existing) return existing;
            const updatedItem = updated.find(u => u.symbol === sym);
            if (updatedItem) return updatedItem;
            const currItem = curr.find(w => w.symbol === sym);
            if (currItem) return currItem;
            return { symbol: sym, name: sym, price: 0, change24h: 0, changePercent24h: 0, type: 'stock' } as WatchlistItem;
          }).filter(item => item !== null && item !== undefined);
        });
        setLastUpdated(Date.now());
      } catch (error) {
        logger.error('Polling fallback error:', error);
      }
    }, 8000);
    
    (esRef as any).rotationTimer = id;
  }, [userSymbols, watchlist, pricesMap]);

  const tryStartSSE = useCallback(() => {
    // Cleanup any existing connection first
    cleanupSSE();
    
    const base = userSymbols.length > 0 ? userSymbols : (watchlist.length > 0 ? watchlist.map(w => w.symbol) : ['AAPL','MSFT','TSLA','GOOGL']);
    const symbols = base.slice(0, 4);
    
    if (symbols.length === 0) {
      setConnStatus('idle');
      return;
    }
    
    try {
      const es = portfolioService.openMarketStream(symbols, 10);
      if (!es) {
        logger.warn('SSE: Failed to create EventSource');
        // Inline error handling to avoid circular dependency
        cleanupSSE();
        sseFailCountRef.current += 1;
        if (sseFailCountRef.current >= MAX_RETRIES) {
          setConnStatus('rotating');
          startPollingFallback();
          return;
        }
        const delay = Math.min(INITIAL_RETRY_DELAY * Math.pow(2, sseFailCountRef.current - 1), MAX_RETRY_DELAY);
        reconnectTimeoutRef.current = window.setTimeout(() => tryStartSSE(), delay);
        return;
      }
      
      esRef.current = es;
      
      es.onopen = () => {
        logger.log('SSE: Connection opened');
        setConnStatus('live');
        if (retryTimerRef.current) { 
          window.clearInterval(retryTimerRef.current); 
          retryTimerRef.current = null; 
        }
        if (reconnectTimeoutRef.current) {
          window.clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
        sseFailCountRef.current = 0;
      };
      
      es.onmessage = (evt) => {
        setConnStatus('live');
        try {
          const payload = JSON.parse(evt.data);
          const prices = payload?.prices || [];
          if (Array.isArray(prices) && prices.length) {
            const updated: WatchlistItem[] = prices.map((p: any) => ({
              symbol: p.symbol,
              name: p.name || p.symbol,
              price: p.price,
              change24h: p.change_24h || 0,
              changePercent24h: p.change_percent_24h || 0,
              type: p.type || 'crypto'
            }));
            // merge into prices map
            setPricesMap((prev) => {
              const next = { ...prev };
              for (const it of updated) next[it.symbol] = it;
              return next;
            });
            // rebuild list from userSymbols if available
            if (userSymbols.length) {
              setWatchlist(userSymbols.map(sym => {
                const existing = pricesMap[sym];
                if (existing) return existing;
                const updatedItem = updated.find(u => u.symbol === sym);
                if (updatedItem) return updatedItem;
                return { symbol: sym, name: sym, price: 0, change24h: 0, changePercent24h: 0, type: 'stock' } as WatchlistItem;
              }).filter(item => item !== null && item !== undefined));
            } else {
              setWatchlist(updated.filter(item => item !== null && item !== undefined));
            }
            setUsingFallback(false);
            // update sparkline series
            setPriceSeries((prev) => {
              const next = { ...prev };
              for (const it of updated) {
                const arr = (next[it.symbol] || []).slice(-29); // keep last 29, will push new for 30 total
                arr.push(it.price);
                next[it.symbol] = arr;
              }
              return next;
            });
            setLastUpdated(Date.now());
          }
        } catch (error) {
          logger.error('SSE: Error parsing message', error);
        }
      };
      
      es.onerror = (error) => {
        logger.warn('SSE: Connection error', error);
        cleanupSSE();
        sseFailCountRef.current += 1;
        
        if (sseFailCountRef.current >= MAX_RETRIES) {
          logger.log(`SSE: Max retries (${MAX_RETRIES}) reached, falling back to polling`);
          setConnStatus('rotating');
          startPollingFallback();
          return;
        }
        
        // Exponential backoff: delay = INITIAL_RETRY_DELAY * (2 ^ (failCount - 1))
        const delay = Math.min(
          INITIAL_RETRY_DELAY * Math.pow(2, sseFailCountRef.current - 1),
          MAX_RETRY_DELAY
        );
        
        setConnStatus(userSymbols.length > 4 ? 'rotating' : 'retry');
        setRetryIn(Math.ceil(delay / 1000));
        
        // Schedule reconnect with exponential backoff
        reconnectTimeoutRef.current = window.setTimeout(() => {
          logger.log(`SSE: Retrying connection (attempt ${sseFailCountRef.current + 1}/${MAX_RETRIES})`);
          tryStartSSE();
        }, delay);
        
        // Update countdown UI
        if (retryTimerRef.current) { 
          window.clearInterval(retryTimerRef.current); 
          retryTimerRef.current = null; 
        }
        
        if (userSymbols.length <= 4) {
          retryTimerRef.current = window.setInterval(() => {
            setRetryIn((n) => {
              if (n <= 1) {
                if (retryTimerRef.current) { 
                  window.clearInterval(retryTimerRef.current); 
                  retryTimerRef.current = null; 
                }
                return 0;
              }
              return n - 1;
            });
          }, 1000);
        }
      };
    } catch (error: any) {
      logger.error('SSE: Failed to start', error);
      cleanupSSE();
      sseFailCountRef.current += 1;
      if (sseFailCountRef.current >= MAX_RETRIES) {
        setConnStatus('rotating');
        startPollingFallback();
      } else {
        const delay = Math.min(INITIAL_RETRY_DELAY * Math.pow(2, sseFailCountRef.current - 1), MAX_RETRY_DELAY);
        reconnectTimeoutRef.current = window.setTimeout(() => tryStartSSE(), delay);
      }
    }
  }, [userSymbols, watchlist, cleanupSSE, startPollingFallback]);

  const fetchWatchlist = async () => {
    try {
      setLoading(true);
      
      // Try to fetch from API
      try {
        const symbols = userSymbols && userSymbols.length ? userSymbols : undefined;
        // Use batch endpoint for larger watchlists (>4 symbols)
        let data;
        if (symbols && symbols.length > 4) {
          data = await portfolioService.getWatchlistPricesBatch(symbols, 50, false, true); // Include DD scores
        } else {
          data = await portfolioService.getWatchlistPrices(symbols);
        }
        if (!data.prices || data.prices.length === 0) {
          // Try default popular stocks if portfolio symbols returned empty
          data = await portfolioService.getWatchlistPrices(['AAPL','MSFT','TSLA','GOOGL']);
        }
        if (data.prices && data.prices.length > 0) {
          // Fetch metadata to enrich watchlist items
          let metadata: Record<string, { categories: string[]; tags: string[] }> = {};
          try {
            const watchlistDataWithMeta = await portfolioService.getUserWatchlist(true);
            if (watchlistDataWithMeta.metadata) {
              metadata = watchlistDataWithMeta.metadata;
              // Update available categories
              const categories = new Set<string>();
              Object.values(metadata).forEach((meta: any) => {
                if (meta.categories) {
                  meta.categories.forEach((cat: string) => categories.add(cat));
                }
              });
              setAvailableCategories(Array.from(categories).sort());
            }
          } catch (metaError) {
            // Metadata fetch failed, continue without it
            logger.log('Could not fetch metadata:', metaError);
          }
          
          // Extract DD scores if available
          const ddScores = data.dd_scores || {};
          
          const watchlistData: WatchlistItem[] = data.prices.map((p: any) => {
            const symbol = p.symbol;
            const ddData = ddScores[symbol];
            return {
              symbol: symbol,
              name: p.name || symbol, // Use name from API if available, fallback to symbol
              price: p.price,
              change24h: p.change_24h || 0,
              changePercent24h: p.change_percent_24h || 0,
              volume: p.volume_24h || p.volume,
              volume_24h: p.volume_24h || p.volume,
              marketCap: p.market_cap || p.marketCap,
              market_cap: p.market_cap || p.marketCap,
              high_24h: p.high_24h,
              low_24h: p.low_24h,
              type: p.type || 'crypto',
              categories: metadata[symbol]?.categories || [],
              tags: metadata[symbol]?.tags || [],
              ddScore: ddData?.score,
              ddVerdict: ddData?.verdict,
              ddConfidence: ddData?.confidence
            };
          });
          setWatchlist(watchlistData);
          setUsingFallback(false);
          // if we were in retry, but dane mamy, przełącz status na idle
          setConnStatus((s) => (s === 'retry' ? (userSymbols.length > 4 ? 'rotating' : 'idle') : s));
          // initialize series if empty
          setPriceSeries((prev) => {
            if (Object.keys(prev).length) return prev;
            const next: Record<string, number[]> = {};
            for (const it of watchlistData) next[it.symbol] = [it.price];
            return next;
          });
          setLastUpdated(Date.now());
          return;
        }
      } catch (apiError: any) {
        logger.log('API fetch failed, using mock data:', apiError);
        // If authentication error, show message but continue with fallback
        if (apiError?.response?.status === 401 || apiError?.userMessage?.includes('authenticated')) {
          // Don't show toast immediately, will show mock data
          logger.log('Authentication required - showing sample data');
        }
      }
      
      // Fallback to mock data - ALWAYS show something
      const mockWatchlist: WatchlistItem[] = [
        {
          symbol: 'BTC',
          name: 'Bitcoin',
          price: 43250.50,
          change24h: 1250.30,
          changePercent24h: 2.98,
          volume: 18500000000,
          marketCap: 850000000000,
          type: 'crypto'
        },
        {
          symbol: 'ETH',
          name: 'Ethereum',
          price: 2650.75,
          change24h: -45.20,
          changePercent24h: -1.67,
          volume: 8500000000,
          marketCap: 320000000000,
          type: 'crypto'
        },
        {
          symbol: 'AAPL',
          name: 'Apple Inc.',
          price: 175.43,
          change24h: 2.15,
          changePercent24h: 1.24,
          type: 'stock'
        },
        {
          symbol: 'TSLA',
          name: 'Tesla Inc.',
          price: 248.90,
          change24h: -5.20,
          changePercent24h: -2.05,
          type: 'stock'
        },
      ];
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 300));
      setWatchlist(mockWatchlist);
      setUsingFallback(true);
      setConnStatus('idle');
      // Initialize price series for mock data
      setPriceSeries((prev) => {
        if (Object.keys(prev).length) return prev;
        const next: Record<string, number[]> = {};
        for (const it of mockWatchlist) {
          // Create simple series: current price with slight variations
          next[it.symbol] = Array.from({ length: 7 }, (_, i) => {
            const variation = (Math.random() - 0.5) * 0.02; // ±1% variation
            return it.price * (1 + variation * (1 - i / 7));
          });
        }
        return next;
      });
      setLastUpdated(Date.now());
    } catch (error: any) {
      logger.error('Error fetching watchlist:', error);
      showToast('Failed to load market data', 'error');
    } finally {
      setLoading(false);
    }
  };

  const theme = useTheme();
  const isXs = useMediaQuery(theme.breakpoints.down('sm'));

  const renderSparkline = useCallback((symbol: string) => {
    let series = priceSeries[symbol] || [];
    if (series.length < 2) {
      const it = watchlist.find(w => w.symbol === symbol);
      if (it) {
        // fallback: flat line using current price so something is visible immediately
        series = [it.price, it.price];
      }
    }
    if (series.length < 2) return null;
    const width = isXs ? 56 : 80;
    const height = 24;
    const min = Math.min(...series);
    const max = Math.max(...series);
    const span = max - min || 1;
    const stepX = width / (series.length - 1);
    const points = series.map((v, i) => {
      const x = i * stepX;
      const y = height - ((v - min) / span) * height;
      return `${x},${y}`;
    }).join(' ');
    const up = series[series.length - 1] >= series[0];
    const gradId = `spark-${symbol}`;
    const handleMove = (evt: React.MouseEvent<SVGSVGElement>) => {
      const now = Date.now();
      if (now - hoverThrottleRef.current < 50) return; // throttle ~20fps
      hoverThrottleRef.current = now;
      const bbox = (evt.currentTarget as SVGSVGElement).getBoundingClientRect();
      const x = Math.max(0, Math.min(width, evt.clientX - bbox.left));
      const idx = Math.max(0, Math.min(series.length - 1, Math.round(x / stepX)));
      const delta = series.length - 1 - idx;
      const d = new Date();
      d.setDate(d.getDate() - delta);
      const dateStr = d.toISOString().slice(0, 10);
      setHoverInfo({ symbol, value: series[idx], date: dateStr });
    };
    const handleLeave = () => setHoverInfo((info: { symbol: string; value: number; date: string } | null) => (info && info.symbol === symbol ? null : info));
    return (
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        aria-hidden
        onMouseMove={handleMove}
        onMouseLeave={handleLeave}
      >
        <defs>
          <linearGradient id={gradId} x1="0" y1="0" x2="1" y2="0">
            {up ? (
              <>
                <stop offset="0%" stopColor="#34D399" />
                <stop offset="100%" stopColor="#10B981" />
              </>
            ) : (
              <>
                <stop offset="0%" stopColor="#F87171" />
                <stop offset="100%" stopColor="#EF4444" />
              </>
            )}
          </linearGradient>
        </defs>
        <polyline
          fill="none"
          stroke={`url(#${gradId})`}
          strokeWidth="2"
          strokeLinecap="round"
          points={points}
        />
      </svg>
    );
  }, [priceSeries, watchlist, isXs]);

  const validateSymbol = (sym: string) => /^[A-Z0-9.-]{1,15}$/.test(sym);

  const handleAdd = async () => {
    const sym = (newSymbol || '').trim().toUpperCase();
    if (!validateSymbol(sym)) {
      showToast('Invalid symbol (allowed: A-Z, 0-9, dot, dash)', 'error');
      return;
    }
    if (userSymbols.includes(sym)) {
      showToast('Symbol already in watchlist', 'info');
      return;
    }
    try {
      setAdding(true);
      const updated = await portfolioService.addToWatchlist(sym);
      setUserSymbols(updated.symbols);
      setNewSymbol('');
      // Update metadata and categories
      if (updated.metadata) {
        const categories = new Set<string>();
        Object.values(updated.metadata).forEach((meta: any) => {
          if (meta.categories) {
            meta.categories.forEach((cat: string) => categories.add(cat));
          }
        });
        setAvailableCategories(Array.from(categories).sort());
      }
      // refresh prices and SSE
      await fetchWatchlist();
      // Update watchlist items with metadata after fetch
      if (updated.metadata) {
        setWatchlist(prev => prev.map(item => ({
          ...item,
          categories: updated.metadata?.[item.symbol]?.categories || [],
          tags: updated.metadata?.[item.symbol]?.tags || []
        })));
      }
      setPriceSeries({});
      cleanupSSE();
      tryStartSSE();
    } catch (e: any) {
      showToast(e?.userMessage || e?.message || 'Failed to add symbol', 'error');
    } finally {
      setAdding(false);
    }
  };

  const handleRemove = async (sym: string) => {
    try {
      const updated = await portfolioService.removeFromWatchlist(sym);
      setUserSymbols(updated.symbols);
      // Update metadata and categories
      if (updated.metadata) {
        const categories = new Set<string>();
        Object.values(updated.metadata).forEach((meta: any) => {
          if (meta.categories) {
            meta.categories.forEach((cat: string) => categories.add(cat));
          }
        });
        setAvailableCategories(Array.from(categories).sort());
      }
      await fetchWatchlist();
      // Update watchlist items with metadata after fetch
      if (updated.metadata) {
        setWatchlist(prev => prev.map(item => ({
          ...item,
          categories: updated.metadata?.[item.symbol]?.categories || [],
          tags: updated.metadata?.[item.symbol]?.tags || []
        })));
      }
      setPriceSeries({});
      if (esRef.current) { esRef.current.close(); esRef.current = null; }
      tryStartSSE();
    } catch (e: any) {
      showToast(e?.userMessage || e?.message || 'Failed to remove symbol', 'error');
    }
  };

  const handleExportCSV = () => {
    try {
      if (userSymbols.length === 0) {
        showToast('No symbols to export', 'info');
        return;
      }
      const csv = userSymbols.join('\n');
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `watchlist_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      portfolioService.trackEvent('mw_export_csv');
      showToast('Watchlist exported to CSV', 'success');
    } catch (error: any) {
      logger.error('Error exporting CSV:', error);
      showToast('Failed to export CSV: ' + (error?.message || 'Unknown error'), 'error');
    }
  };

  const handleExportJSON = () => {
    try {
      if (userSymbols.length === 0) {
        showToast('No symbols to export', 'info');
        return;
      }
      const json = JSON.stringify({ symbols: userSymbols, exported: new Date().toISOString() }, null, 2);
      const blob = new Blob([json], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `watchlist_${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      portfolioService.trackEvent('mw_export_json');
      showToast('Watchlist exported to JSON', 'success');
    } catch (error: any) {
      logger.error('Error exporting JSON:', error);
      showToast('Failed to export JSON: ' + (error?.message || 'Unknown error'), 'error');
    }
  };

  const handleImportFile = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    const fileExt = file.name.split('.').pop()?.toLowerCase();
    if (!['csv', 'json'].includes(fileExt || '')) {
      showToast('Please select a CSV or JSON file', 'error');
      return;
    }

    try {
      const text = await file.text();
      let symbols: string[] = [];
      
      if (fileExt === 'csv') {
        // Parse CSV - one symbol per line or comma-separated
        symbols = text
          .split(/\n|,/)
          .map(s => s.trim().toUpperCase())
          .filter(s => s && /^[A-Z0-9.-]+$/.test(s));
      } else if (fileExt === 'json') {
        // Parse JSON - expect { symbols: string[] } or array of strings
        const parsed = JSON.parse(text);
        if (Array.isArray(parsed)) {
          symbols = parsed.map(s => String(s).trim().toUpperCase()).filter(s => s && /^[A-Z0-9.-]+$/.test(s));
        } else if (parsed.symbols && Array.isArray(parsed.symbols)) {
          symbols = parsed.symbols.map((s: string) => String(s).trim().toUpperCase()).filter((s: string) => s && /^[A-Z0-9.-]+$/.test(s));
        } else {
          showToast('Invalid JSON format. Expected array or object with "symbols" array', 'error');
          return;
        }
      }

      if (symbols.length === 0) {
        showToast('No valid symbols found in file', 'error');
        return;
      }

      // Add symbols (skip duplicates)
      let added = 0;
      let skipped = 0;
      let errors = 0;
      const currentSymbols = [...userSymbols];
      const errorsList: string[] = [];
      
      for (const sym of symbols) {
        if (!currentSymbols.includes(sym)) {
          try {
            const validateSymbol = (s: string) => /^[A-Z0-9.-]{1,15}$/.test(s);
            if (!validateSymbol(sym)) {
              skipped++;
              errorsList.push(`${sym}: Invalid format`);
              continue;
            }
            const updated = await portfolioService.addToWatchlist(sym);
            currentSymbols.push(sym);
            setUserSymbols(updated.symbols);
            added++;
          } catch (e: any) {
            skipped++;
            errors++;
            errorsList.push(`${sym}: ${e?.userMessage || e?.message || 'Failed to add'}`);
            logger.error(`Failed to add symbol ${sym}:`, e);
          }
        } else {
          skipped++;
        }
      }

      // Refresh watchlist after import
      if (added > 0) {
        // Fetch metadata after batch import
        try {
          const watchlistDataWithMeta = await portfolioService.getUserWatchlist(true);
          if (watchlistDataWithMeta.metadata) {
            const categories = new Set<string>();
            Object.values(watchlistDataWithMeta.metadata).forEach((meta: any) => {
              if (meta.categories) {
                meta.categories.forEach((cat: string) => categories.add(cat));
              }
            });
            setAvailableCategories(Array.from(categories).sort());
          }
        } catch (metaError) {
          logger.log('Could not fetch metadata after batch import:', metaError);
        }
        await fetchWatchlist();
        setPriceSeries({});
        if (esRef.current) { esRef.current.close(); esRef.current = null; }
        tryStartSSE();
      }

      const message = errors > 0 
        ? `Imported ${added} symbols, ${skipped} skipped, ${errors} errors. Check console for details.`
        : `Imported ${added} symbols${skipped > 0 ? `, ${skipped} already in watchlist or invalid` : ''}`;
      showToast(message, added > 0 ? (errors > 0 ? 'warning' : 'success') : 'info');
      if (errors > 0 && errorsList.length > 0) {
        logger.error('Import errors:', errorsList);
      }
      portfolioService.trackEvent('mw_import_file');
      
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (e: any) {
      logger.error('Error importing file:', e);
      showToast(e?.message || 'Failed to import file. Please check file format and try again.', 'error');
      // Reset file input on error
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleCreateAlert = async () => {
    const p = parseFloat(alertPrice);
    if (!p || isNaN(p)) {
      showToast('Enter valid price', 'error');
      return;
    }
    try {
      await portfolioService.createPriceAlert({ symbol: alertSymbol, condition: alertCond, price: p });
      showToast('Alert created', 'success');
      setAlertAnchor(null);
    } catch (e: any) {
      showToast(e?.userMessage || e?.message || 'Failed to create alert', 'error');
    }
  };

  const handleCreateBatchAlerts = async () => {
    if (selectedBatchSymbols.size === 0) {
      showToast('Select at least one symbol', 'error');
      return;
    }
    const val = parseFloat(batchAlertPrice);
    if (!val || isNaN(val)) {
      showToast(`Enter valid ${batchAlertType === 'price' ? 'price' : 'percentage'}`, 'error');
      return;
    }

    try {
      setBatchCreating(true);
      let created = 0;
      let errors = 0;

      for (const sym of Array.from(selectedBatchSymbols)) {
        try {
          const item = pricesMap[sym] || watchlist.find(w => w.symbol === sym);
          if (!item || !item.price || isNaN(item.price)) {
            errors++;
            continue;
          }

          let targetPrice: number;
          if (batchAlertType === 'price') {
            targetPrice = val;
          } else {
            // Percentage - calculate from current price
            const change = (val / 100) * item.price;
            targetPrice = batchAlertCond === 'above' ? item.price + change : item.price - change;
          }

          await portfolioService.createPriceAlert({
            symbol: sym,
            condition: batchAlertCond,
            price: targetPrice,
          });
          created++;
        } catch (e: any) {
          errors++;
          logger.error(`Failed to create alert for ${sym}:`, e);
        }
      }

      showToast(
        `Created ${created} alerts${errors > 0 ? `, ${errors} failed` : ''}`,
        created > 0 ? 'success' : 'error'
      );
      portfolioService.trackEvent('mw_batch_alerts_create');
      
      // Reset state
      setBatchAlertsOpen(false);
      setSelectedBatchSymbols(new Set());
      setBatchAlertPrice('');
    } catch (e: any) {
      showToast(e?.userMessage || e?.message || 'Failed to create batch alerts', 'error');
    } finally {
      setBatchCreating(false);
    }
  };

  const handleToggleBatchSymbol = (sym: string) => {
    const newSet = new Set(selectedBatchSymbols);
    if (newSet.has(sym)) {
      newSet.delete(sym);
    } else {
      newSet.add(sym);
    }
    setSelectedBatchSymbols(newSet);
  };

  const handleSelectAllBatch = () => {
    if (selectedBatchSymbols.size === userSymbols.length) {
      setSelectedBatchSymbols(new Set());
    } else {
      setSelectedBatchSymbols(new Set(userSymbols));
    }
  };

  const handleToggleBulkSelect = (sym: string) => {
    const newSet = new Set(selectedSymbols);
    if (newSet.has(sym)) {
      newSet.delete(sym);
    } else {
      newSet.add(sym);
    }
    setSelectedSymbols(newSet);
  };

  const handleSelectAllBulk = () => {
    const syms = filteredAndSortedSymbols;
    if (selectedSymbols.size === syms.length && syms.length > 0) {
      setSelectedSymbols(new Set());
    } else {
      setSelectedSymbols(new Set(syms));
    }
  };

  const handleBulkRemove = async () => {
    if (selectedSymbols.size === 0) return;
    
    try {
      const result = await portfolioService.batchRemoveFromWatchlist(Array.from(selectedSymbols));
      if (result.results.removed.length > 0) {
        showToast(`Removed ${result.results.removed.length} symbol(s) from watchlist`, 'success');
        setUserSymbols(result.symbols);
        setSelectedSymbols(new Set());
        setBulkSelectMode(false);
        await fetchWatchlist();
      }
      if (result.results.failed.length > 0) {
        showToast(`Failed to remove ${result.results.failed.length} symbol(s)`, 'warning');
      }
      portfolioService.trackEvent('mw_bulk_remove');
    } catch (e: any) {
      showToast(e?.userMessage || e?.message || 'Failed to remove symbols', 'error');
    }
  };

  const handleBulkAddCategories = async () => {
    if (selectedSymbols.size === 0) return;
    setBulkOperationOpen(true);
  };

  const formatPrice = useCallback((price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(price);
  }, []);

  // Memoized filtered and sorted symbols
  const filteredAndSortedSymbols = useMemo(() => {
    let syms = (userSymbols.length ? userSymbols : watchlist.map(w => w.symbol));
    
    // Filter by tab
    syms = syms.filter(sym => {
      if (tab === 'all') return true;
      const it = pricesMap[sym] || watchlist.find(w => w.symbol === sym);
      if (!it) return true;
      return tab === 'stocks' ? it.type === 'stock' : it.type === 'crypto';
    });
    
    // Advanced filters: category
    if (filterCategory) {
      syms = syms.filter(sym => {
        const it = pricesMap[sym] || watchlist.find(w => w.symbol === sym);
        return it?.categories?.includes(filterCategory) ?? false;
      });
    }
    
    // Advanced filters: price range
    if (filterPriceMin || filterPriceMax) {
      const minPrice = filterPriceMin ? parseFloat(filterPriceMin) : -Infinity;
      const maxPrice = filterPriceMax ? parseFloat(filterPriceMax) : Infinity;
      syms = syms.filter(sym => {
        const it = pricesMap[sym] || watchlist.find(w => w.symbol === sym);
        const price = it?.price ?? 0;
        return price >= minPrice && price <= maxPrice;
      });
    }
    
    // Advanced filters: change % range
    if (filterChangeMin || filterChangeMax) {
      const minChange = filterChangeMin ? parseFloat(filterChangeMin) : -Infinity;
      const maxChange = filterChangeMax ? parseFloat(filterChangeMax) : Infinity;
      syms = syms.filter(sym => {
        const it = pricesMap[sym] || watchlist.find(w => w.symbol === sym);
        const change = it?.changePercent24h ?? 0;
        return change >= minChange && change <= maxChange;
      });
    }
    
    // Advanced filters: DD score range
    if (filterDdScoreMin || filterDdScoreMax) {
      const minDd = filterDdScoreMin ? parseFloat(filterDdScoreMin) : -Infinity;
      const maxDd = filterDdScoreMax ? parseFloat(filterDdScoreMax) : Infinity;
      syms = syms.filter(sym => {
        const it = pricesMap[sym] || watchlist.find(w => w.symbol === sym);
        const ddScore = it?.ddScore;
        if (ddScore === undefined || ddScore === null) return false; // Only show items with DD scores
        return ddScore >= minDd && ddScore <= maxDd;
      });
    }
    
    // Quick filters
    if (quickFilter !== 'none') {
      const byChange = (sym: string) => (pricesMap[sym]?.changePercent24h ?? watchlist.find(w => w.symbol === sym)?.changePercent24h ?? 0);
      if (quickFilter === 'gainers') {
        syms = syms.slice().sort((a, b) => byChange(b) - byChange(a)).slice(0, Math.min(10, syms.length));
      } else if (quickFilter === 'losers') {
        syms = syms.slice().sort((a, b) => byChange(a) - byChange(b)).slice(0, Math.min(10, syms.length));
      } else if (quickFilter === 'gt2') {
        syms = syms.filter(sym => byChange(sym) >= 2);
      } else if (quickFilter === 'lt-2') {
        syms = syms.filter(sym => byChange(sym) <= -2);
      }
    }
    
    // Sort
    syms.sort((a, b) => {
      const ia = pricesMap[a] || watchlist.find(w => w.symbol === a);
      const ib = pricesMap[b] || watchlist.find(w => w.symbol === b);
      const sa = ia?.symbol || a;
      const sb = ib?.symbol || b;
      const pa = ia?.price ?? 0;
      const pb = ib?.price ?? 0;
      const ca = ia?.changePercent24h ?? 0;
      const cb = ib?.changePercent24h ?? 0;
      let cmp = 0;
      if (sortKey === 'symbol') cmp = sa.localeCompare(sb);
      else if (sortKey === 'price') cmp = pa - pb;
      else cmp = ca - cb;
      return sortDir === 'asc' ? cmp : -cmp;
    });
    
    return syms;
  }, [userSymbols, watchlist, pricesMap, tab, quickFilter, sortKey, sortDir, filterCategory, filterPriceMin, filterPriceMax, filterChangeMin, filterChangeMax]);

  // Page Visibility API: pause/resume polling when tab is hidden/visible
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden') {
        // Pause polling and close SSE when tab is hidden
        cleanupSSE();
        if ((esRef as any).rotationTimer) {
          window.clearInterval((esRef as any).rotationTimer);
          (esRef as any).rotationTimer = null;
        }
        setConnStatus('idle');
      } else if (document.visibilityState === 'visible') {
        // Resume when tab becomes visible
        if (userSymbols.length <= 4) {
          tryStartSSE();
        } else if (connStatus === 'rotating') {
          startPollingFallback();
        }
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [userSymbols.length, connStatus, tryStartSSE, startPollingFallback, cleanupSSE]);

  // Memoized styles that depend on state
  const rowStyles = useMemo(() => ({
    ...styles.rowBase,
    p: compact ? 1.5 : 2,
    '&:hover': styles.rowHover,
  }), [compact]);

  const getChipStyles = useCallback((type: 'crypto' | 'stock') => ({
    height: compact ? 18 : 20,
    fontSize: compact ? '0.6rem' : '0.65rem',
    ...(type === 'crypto' ? styles.chipCrypto : styles.chipStock),
  }), [compact]);

  const priceContainerStyles = useMemo(() => ({
    ...styles.priceContainer,
    minWidth: compact ? 120 : 180,
  }), [compact]);

  const sparklineBoxStyles = useMemo(() => ({
    ...styles.sparklineContainer,
    width: compact ? 60 : 80,
    height: compact ? 30 : 40,
  }), [compact]);

  return (
    <Box component="section" aria-labelledby="market-watch-heading">
      <Card sx={{ mb: 4 }}>
        <CardContent sx={styles.cardContent}>
          <Box sx={styles.headerContainer}>
            {/* Left: Title + Count */}
            <Box sx={styles.titleContainer}>
              <Typography id="market-watch-heading" variant="h6" sx={{ fontWeight: 600 }}>
                Market Watch
              </Typography>
              <Chip 
                label={`${watchlist.length} assets`}
                size="small"
                sx={{ bgcolor: 'rgba(37, 99, 235, 0.1)', color: 'primary.main' }}
              />
            </Box>

            {/* Center: Status + Timestamp */}
            <Box sx={styles.statusContainer}>
              <Tooltip 
                title={connStatus==='rotating' 
                  ? 'Using polling due to >4 symbols or SSE issues' 
                  : connStatus==='live' 
                    ? 'Live updates via SSE' 
                    : connStatus==='retry' 
                      ? 'Reconnecting to live stream' 
                      : 'Idle'}>
                <Chip
                  size="small"
                  label={connStatus==='live' ? 'Live' : connStatus==='retry' ? `Retry in ${retryIn}s` : connStatus==='rotating' ? 'Live (polling)' : 'Idle'}
                  color={connStatus==='live' ? 'success' : connStatus==='retry' ? 'warning' : 'default'}
                  sx={{ height: 22 }}
                  role="status"
                  aria-live="polite"
                />
              </Tooltip>
              {!!lastUpdated && (
                <Typography variant="caption" color="text.secondary">
                  Updated {new Date(lastUpdated).toLocaleTimeString()}
                </Typography>
              )}
            </Box>

            {/* Right: Actions grouped */}
            <Box sx={styles.actionsContainer}>
              <Box sx={styles.actionsGroup}>
                <Tooltip title="Refresh prices">
                  <IconButton 
                    size="small" 
                    onClick={fetchWatchlist}
                    disabled={loading}
                    sx={{
                      minWidth: { xs: 44, sm: 'auto' },
                      minHeight: { xs: 44, sm: 'auto' }
                    }}
                    aria-label="Refresh prices"
                  >
                    <Refresh />
                  </IconButton>
                </Tooltip>
                <Button
                  size="small"
                  variant="contained"
                  startIcon={<Add />}
                  onClick={() => { setAddDialogOpen(true); portfolioService.trackEvent('mw_add_dialog_open'); }}
                >
                  Add Symbol
                </Button>
                <Button
                  size="small"
                  variant={bulkSelectMode ? "contained" : "outlined"}
                  onClick={() => {
                    setBulkSelectMode(!bulkSelectMode);
                    if (bulkSelectMode) {
                      setSelectedSymbols(new Set());
                    }
                    portfolioService.trackEvent('mw_bulk_select_toggle');
                  }}
                  aria-label={bulkSelectMode ? "Exit bulk select mode" : "Enter bulk select mode"}
                >
                  {bulkSelectMode ? "Cancel" : "Bulk Select"}
                </Button>
              </Box>
              <Box sx={{ display: 'flex', gap: 1 }}>
                {bulkSelectMode && selectedSymbols.size > 0 && (
                  <>
                    <Button 
                      size="small" 
                      variant="outlined" 
                      color="error"
                      startIcon={<DeleteOutline />}
                      onClick={handleBulkRemove}
                      aria-label={`Remove ${selectedSymbols.size} selected symbols`}
                    >
                      Remove ({selectedSymbols.size})
                    </Button>
                    <Button 
                      size="small" 
                      variant="outlined"
                      onClick={handleBulkAddCategories}
                      aria-label="Add categories to selected symbols"
                    >
                      Add Categories ({selectedSymbols.size})
                    </Button>
                  </>
                )}
                {!bulkSelectMode && (
                  <>
                    <Button 
                      size="small" 
                      variant="outlined" 
                      onClick={() => { portfolioService.trackEvent('mw_manage_open'); setManageOpen(true); }}
                      aria-label="Manage watchlist"
                    >
                      Manage
                    </Button>
                  </>
                )}
                <Button 
                  size="small" 
                  variant="outlined" 
                  startIcon={<NotificationsOutlined />} 
                  onClick={() => { setBatchAlertsOpen(true); portfolioService.trackEvent('mw_batch_alerts_open'); }} 
                  disabled={userSymbols.length === 0}
                  aria-label="Create batch alerts"
                >
                  Batch Alerts
                </Button>
              </Box>
            </Box>
          </Box>

          {bulkSelectMode && selectedSymbols.size > 0 && (
            <Box sx={{ mb: 2, p: 1.5, bgcolor: 'primary.light', borderRadius: 1, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 1 }}>
              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                {selectedSymbols.size} symbol{selectedSymbols.size !== 1 ? 's' : ''} selected
              </Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button size="small" variant="outlined" onClick={handleSelectAllBulk}>
                  {selectedSymbols.size === filteredAndSortedSymbols.length ? 'Deselect All' : 'Select All'}
                </Button>
              </Box>
            </Box>
          )}
          <Box sx={styles.filtersContainer}>
            <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ minHeight: 36 }}>
              <Tab label="All" value="all" sx={{ minHeight: 36 }} />
              <Tab label="Stocks" value="stocks" sx={{ minHeight: 36 }} />
              <Tab label="Crypto" value="crypto" sx={{ minHeight: 36 }} />
            </Tabs>
            
            {!isXs ? (
              <Box sx={styles.filtersRow}>
                {/* Quick Filters */}
                <Box sx={styles.quickFiltersContainer}>
                  <MuiChip
                    label="Top gainers"
                    size="small"
                    color={quickFilter==='gainers' ? 'success' : 'default'}
                    variant={quickFilter==='gainers' ? 'filled' : 'outlined'}
                    onClick={() => { setQuickFilter(quickFilter==='gainers'?'none':'gainers'); portfolioService.trackEvent('mw_quick_filter'); }}
                  />
                  <MuiChip
                    label="Top losers"
                    size="small"
                    color={quickFilter==='losers' ? 'error' : 'default'}
                    variant={quickFilter==='losers' ? 'filled' : 'outlined'}
                    onClick={() => { setQuickFilter(quickFilter==='losers'?'none':'losers'); portfolioService.trackEvent('mw_quick_filter'); }}
                  />
                  <MuiChip
                    label="> +2%"
                    size="small"
                    variant={quickFilter==='gt2' ? 'filled' : 'outlined'}
                    color={quickFilter==='gt2' ? 'success' : 'default'}
                    onClick={() => { setQuickFilter(quickFilter==='gt2'?'none':'gt2'); portfolioService.trackEvent('mw_quick_filter'); }}
                  />
                  <MuiChip
                    label="< -2%"
                    size="small"
                    variant={quickFilter==='lt-2' ? 'filled' : 'outlined'}
                    color={quickFilter==='lt-2' ? 'error' : 'default'}
                    onClick={() => { setQuickFilter(quickFilter==='lt-2'?'none':'lt-2'); portfolioService.trackEvent('mw_quick_filter'); }}
                  />
                </Box>
                <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />
                {/* Sort Options */}
                <FormControl size="small" sx={{ minWidth: 120 }}>
                  <InputLabel id="sort-by-label">Sort by</InputLabel>
                  <Select labelId="sort-by-label" value={sortKey} label="Sort by" onChange={(e) => setSortKey(e.target.value as any)}>
                    <MenuItem value="symbol">Symbol</MenuItem>
                    <MenuItem value="price">Price</MenuItem>
                    <MenuItem value="change">Change %</MenuItem>
                  </Select>
                </FormControl>
                <Tooltip title={sortDir === 'asc' ? 'Sort ascending' : 'Sort descending'}>
                  <IconButton 
                    size="small" 
                    onClick={() => { setSortDir(d => d==='asc'?'desc':'asc'); portfolioService.trackEvent('mw_sort_toggle'); }}
                    sx={{ 
                      border: '1px solid', 
                      borderColor: 'divider',
                      minWidth: { xs: 44, sm: 'auto' },
                      minHeight: { xs: 44, sm: 'auto' }
                    }}
                    aria-label={sortDir === 'asc' ? 'Sort ascending' : 'Sort descending'}
                  >
                    {sortDir === 'asc' ? <ArrowUpward fontSize="small" /> : <ArrowDownward fontSize="small" />}
                  </IconButton>
                </Tooltip>
                <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />
                <Tooltip title={compact ? "Switch to normal view" : "Switch to compact view"}>
                  <IconButton 
                    size="small" 
                    onClick={() => { setCompact(v=>!v); portfolioService.trackEvent('mw_compact_toggle'); }}
                    sx={{ 
                      border: '1px solid', 
                      borderColor: compact ? 'primary.main' : 'divider',
                      minWidth: { xs: 44, sm: 'auto' },
                      minHeight: { xs: 44, sm: 'auto' }
                    }}
                    aria-label={compact ? "Switch to normal view" : "Switch to compact view"}
                  >
                    <ViewCompactAlt fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Box>
            ) : (
              <Button size="small" variant="outlined" onClick={(e) => { setFiltersAnchor(e.currentTarget); portfolioService.trackEvent('mw_filters_open'); }} aria-label="Open filters">
                Filters
              </Button>
            )}
          </Box>
          {/* Filters Popover for small screens */}
          <Popover
            open={Boolean(filtersAnchor)}
            anchorEl={filtersAnchor}
            onClose={() => setFiltersAnchor(null)}
            anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
            transformOrigin={{ vertical: 'top', horizontal: 'right' }}
            PaperProps={{ sx: styles.popoverPaper }}
          >
            <Typography variant="subtitle2" sx={{ mb: 1 }}>Filters & sorting</Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap', mb: 1 }}>
              <MuiChip
                label="Top gainers"
                size="small"
                color={quickFilter==='gainers' ? 'success' : 'default'}
                variant={quickFilter==='gainers' ? 'filled' : 'outlined'}
                onClick={() => setQuickFilter(quickFilter==='gainers'?'none':'gainers')}
                aria-label="Filter top gainers"
              />
              <MuiChip
                label="Top losers"
                size="small"
                color={quickFilter==='losers' ? 'error' : 'default'}
                variant={quickFilter==='losers' ? 'filled' : 'outlined'}
                onClick={() => setQuickFilter(quickFilter==='losers'?'none':'losers')}
                aria-label="Filter top losers"
              />
              <MuiChip
                label="> +2%"
                size="small"
                variant={quickFilter==='gt2' ? 'filled' : 'outlined'}
                color={quickFilter==='gt2' ? 'success' : 'default'}
                onClick={() => setQuickFilter(quickFilter==='gt2'?'none':'gt2')}
                aria-label="Filter greater than 2 percent"
              />
              <MuiChip
                label="< -2%"
                size="small"
                variant={quickFilter==='lt-2' ? 'filled' : 'outlined'}
                color={quickFilter==='lt-2' ? 'error' : 'default'}
                onClick={() => setQuickFilter(quickFilter==='lt-2'?'none':'lt-2')}
                aria-label="Filter less than minus 2 percent"
              />
            </Box>
            
            {/* Advanced Filters */}
            <Divider sx={{ my: 1 }} />
            <Button 
              size="small" 
              variant={advancedFiltersOpen ? 'contained' : 'outlined'}
              onClick={() => setAdvancedFiltersOpen(!advancedFiltersOpen)}
              sx={{ mb: advancedFiltersOpen ? 1 : 0 }}
            >
              {advancedFiltersOpen ? 'Hide' : 'Show'} Advanced Filters
            </Button>
            {advancedFiltersOpen && (
              <Box sx={styles.advancedFiltersContainer}>
                {availableCategories.length > 0 && (
                  <FormControl size="small" fullWidth>
                    <InputLabel>Category</InputLabel>
                    <Select
                      value={filterCategory}
                      label="Category"
                      onChange={(e) => setFilterCategory(e.target.value)}
                    >
                      <MenuItem value="">All Categories</MenuItem>
                      {availableCategories.map(cat => (
                        <MenuItem key={cat} value={cat}>{cat}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                )}
                <Box sx={styles.priceGrid}>
                  <TextField
                    size="small"
                    label="Min Price"
                    type="number"
                    value={filterPriceMin}
                    onChange={(e) => setFilterPriceMin(e.target.value)}
                    InputProps={{ startAdornment: <InputAdornment position="start">$</InputAdornment> }}
                  />
                  <TextField
                    size="small"
                    label="Max Price"
                    type="number"
                    value={filterPriceMax}
                    onChange={(e) => setFilterPriceMax(e.target.value)}
                    InputProps={{ startAdornment: <InputAdornment position="start">$</InputAdornment> }}
                  />
                </Box>
                <Box sx={styles.priceGrid}>
                  <TextField
                    size="small"
                    label="Min Change %"
                    type="number"
                    value={filterChangeMin}
                    onChange={(e) => setFilterChangeMin(e.target.value)}
                    InputProps={{ startAdornment: <InputAdornment position="start">%</InputAdornment> }}
                  />
                  <TextField
                    size="small"
                    label="Max Change %"
                    type="number"
                    value={filterChangeMax}
                    onChange={(e) => setFilterChangeMax(e.target.value)}
                    InputProps={{ startAdornment: <InputAdornment position="start">%</InputAdornment> }}
                  />
                </Box>
                <Box sx={styles.priceGrid}>
                  <TextField
                    size="small"
                    label="Min DD Score"
                    type="number"
                    value={filterDdScoreMin}
                    onChange={(e) => setFilterDdScoreMin(e.target.value)}
                    InputProps={{ inputProps: { min: 0, max: 100 } }}
                    helperText="Due Diligence 360° score (0-100)"
                  />
                  <TextField
                    size="small"
                    label="Max DD Score"
                    type="number"
                    value={filterDdScoreMax}
                    onChange={(e) => setFilterDdScoreMax(e.target.value)}
                    InputProps={{ inputProps: { min: 0, max: 100 } }}
                    helperText="Due Diligence 360° score (0-100)"
                  />
                </Box>
                <Button 
                  size="small" 
                  variant="outlined" 
                  onClick={() => {
                    setFilterCategory('');
                    setFilterPriceMin('');
                    setFilterPriceMax('');
                    setFilterChangeMin('');
                    setFilterChangeMax('');
                    setFilterDdScoreMin('');
                    setFilterDdScoreMax('');
                  }}
                >
                  Clear Filters
                </Button>
              </Box>
            )}
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <FormControl size="small" sx={{ minWidth: 140 }}>
                <InputLabel id="sort-by-label-sm">Sort by</InputLabel>
                <Select labelId="sort-by-label-sm" value={sortKey} label="Sort by" onChange={(e) => setSortKey(e.target.value as any)}>
                  <MenuItem value="symbol">Symbol</MenuItem>
                  <MenuItem value="price">Price</MenuItem>
                  <MenuItem value="change">Change %</MenuItem>
                </Select>
              </FormControl>
              <Button size="small" onClick={() => { setSortDir(d => d==='asc'?'desc':'asc'); portfolioService.trackEvent('mw_sort_toggle'); }} aria-label="Toggle sort direction">{sortDir==='asc'?'Asc':'Desc'}</Button>
            </Box>
            <Button size="small" variant={compact ? 'contained' : 'outlined'} onClick={() => { setCompact(v=>!v); portfolioService.trackEvent('mw_compact_toggle'); }} aria-label="Toggle compact mode">
              {compact ? 'Compact: On' : 'Compact: Off'}
            </Button>
          </Popover>

          {usingFallback && !loading && (
            <Alert severity="info" sx={{ mb: 2 }}>
              Showing sample prices due to API limits or missing data. Click refresh to retry.
            </Alert>
          )}
          {!loading && (
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
              {`Last updated: ${new Date().toLocaleTimeString()}`}
            </Typography>
          )}

          {loading ? (
            <SkeletonLoader type="watchlist-row" rows={3} />
          ) : watchlist.length === 0 ? (
            <Box sx={styles.emptyStateContainer}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                No assets in your watchlist
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                <TextField
                  size="small"
                  placeholder="Add symbol (e.g., AAPL)"
                  value={newSymbol}
                  onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
                  sx={styles.emptyStateInput}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton size="small" onClick={handleAdd} disabled={adding || !newSymbol} aria-label="Add symbol">
                          <Add />
                        </IconButton>
                      </InputAdornment>
                    )
                  }}
                />
              </Box>
            </Box>
          ) : (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
              {(() => {
                const syms = filteredAndSortedSymbols;
                const renderRow = (sym: string, style?: React.CSSProperties) => {
                  const item = pricesMap[sym] || watchlist.find(w=>w.symbol===sym) || { symbol: sym, name: sym, price: 0, change24h: 0, changePercent24h: 0, type: 'stock' } as WatchlistItem;
                  if (!item) return null;
                  return (
                <Box
                  key={sym}
                  style={style}
                  sx={rowStyles}
                  role="button"
                  tabIndex={0}
                  aria-label={`Open details for ${item.symbol}`}
                  onClick={() => {
                    if (bulkSelectMode) {
                      handleToggleBulkSelect(sym);
                    } else {
                      portfolioService.trackEvent('mw_row_open');
                      setDrawerSymbol(item.symbol);
                      setDrawerOpen(true);
                    }
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      if (bulkSelectMode) {
                        handleToggleBulkSelect(sym);
                      } else {
                        portfolioService.trackEvent('mw_row_open');
                        setDrawerSymbol(item.symbol);
                        setDrawerOpen(true);
                      }
                    }
                  }}
                >
                  {/* Checkbox for bulk select mode */}
                  {bulkSelectMode && (
                    <Checkbox
                      checked={selectedSymbols.has(sym)}
                      onChange={() => handleToggleBulkSelect(sym)}
                      onClick={(e) => e.stopPropagation()}
                      size="small"
                      sx={{ mr: 1 }}
                      aria-label={`Select ${item.symbol}`}
                    />
                  )}
                  {/* Symbol + Type Chip */}
                  <Box sx={styles.symbolContainer}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: compact ? 0 : 0.5, flexWrap: 'wrap' }}>
                      <Typography variant={compact ? 'body2' : 'subtitle1'} sx={{ fontWeight: 600 }}>
                        {item.symbol}
                      </Typography>
                      <Chip
                        label={item.type === 'crypto' ? 'Crypto' : 'Stock'}
                        size="small"
                        sx={getChipStyles(item.type)}
                      />
                      {item.ddScore !== undefined && item.ddScore !== null && (
                        <Tooltip title={`Due Diligence 360° Score: ${item.ddScore.toFixed(1)}${item.ddVerdict ? ` (${item.ddVerdict.replace(/_/g, ' ')})` : ''}${item.ddConfidence ? ` | Confidence: ${(item.ddConfidence * 100).toFixed(0)}%` : ''}`}>
                          <Chip
                            label={`DD: ${item.ddScore.toFixed(0)}`}
                            size="small"
                            sx={{
                              bgcolor: item.ddScore >= 75 ? 'success.light' : item.ddScore >= 50 ? 'warning.light' : 'error.light',
                              color: item.ddScore >= 75 ? 'success.dark' : item.ddScore >= 50 ? 'warning.dark' : 'error.dark',
                              fontWeight: 600,
                              fontSize: '0.7rem',
                              height: 20
                            }}
                          />
                        </Tooltip>
                      )}
                    </Box>
                    {!compact && (
                      <Typography variant="caption" color="text.secondary">
                        {item.name || item.symbol}
                      </Typography>
                    )}
                  </Box>

                  {/* Price + Change + Extended Metrics */}
                  <Box sx={priceContainerStyles}>
                    <Typography variant={compact ? 'body1' : 'h6'} sx={{ fontWeight: 600, mb: compact ? 0 : 0.5 }}>
                      {formatPrice(item.price)}
                    </Typography>
                    <TrendIndicator 
                      value={item.changePercent24h}
                      showIcon
                      showPercent
                      size={'small'}
                    />
                    {!compact && (
                      <Box sx={{ mt: 1, display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                        {item.high_24h !== undefined && item.low_24h !== undefined && (
                          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                            H: {formatPrice(item.high_24h)} | L: {formatPrice(item.low_24h)}
                          </Typography>
                        )}
                        {item.volume_24h !== undefined && item.volume_24h > 0 && (
                          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                            Vol: ${(item.volume_24h / 1e6).toFixed(2)}M
                          </Typography>
                        )}
                        {item.market_cap !== undefined && item.market_cap > 0 && (
                          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                            MCap: ${(item.market_cap / 1e9).toFixed(2)}B
                          </Typography>
                        )}
                      </Box>
                    )}
                  </Box>

                  {/* Sparkline with subtle background */}
                  <Box sx={sparklineBoxStyles}>
                    <Tooltip title={(() => {
                      if (hoverInfo && hoverInfo.symbol === item.symbol) {
                        return `${hoverInfo.date}: ${formatPrice(hoverInfo.value)}`;
                      }
                      const s = priceSeries[item.symbol] || [];
                      if (s.length) {
                        const first = s[0];
                        const last = s[s.length - 1];
                        const pct = first ? (((last - first) / first) * 100).toFixed(2) : '0.00';
                        return `${item.symbol}: ${formatPrice(last)} (${pct}%) over 7d`;
                      }
                      return `${item.symbol}: ${formatPrice(item.price)}`;
                    })()}>
                      <Box sx={{ opacity: 0.85 }}>
                        {renderSparkline(item.symbol)}
                      </Box>
                    </Tooltip>
                  </Box>

                  {/* Actions */}
                  <Box sx={styles.actionsBox}>
                    <Tooltip title="Set price alert">
                      <IconButton 
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          setAlertAnchor(e.currentTarget as HTMLElement);
                          setAlertSymbol(item.symbol);
                          setAlertCond('above');
                          setAlertPrice(String(item.price));
                          portfolioService.trackEvent('mw_alert_open');
                        }}
                        sx={{
                          ...styles.iconButtonAlert,
                          minWidth: { xs: 44, sm: 'auto' },
                          minHeight: { xs: 44, sm: 'auto' },
                          width: { xs: 44, sm: 'auto' },
                          height: { xs: 44, sm: 'auto' }
                        }}
                        aria-label={`Create alert for ${item.symbol}`}
                      >
                        <NotificationsOutlined fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Remove from watchlist">
                      <IconButton 
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRemove(item.symbol);
                        }}
                        sx={{
                          ...styles.iconButtonDelete,
                          minWidth: { xs: 44, sm: 'auto' },
                          minHeight: { xs: 44, sm: 'auto' },
                          width: { xs: 44, sm: 'auto' },
                          height: { xs: 44, sm: 'auto' }
                        }}
                        aria-label={`Remove ${item.symbol}`}
                      >
                        <DeleteOutline fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </Box>
                );
                };

                if (syms.length > 30) {
                  const itemSize = compact ? 56 : 72;
                  const height = Math.min(560, syms.length * itemSize);
                  const renderVirtualRow = ({ index, style }: { index: number; style: React.CSSProperties }) => (
                    renderRow(syms[index], style)
                  );
                  return (
                    <List height={height} itemCount={syms.length} itemSize={itemSize} width={"100%"} children={renderVirtualRow as any} />
                  );
                }
                return syms.map((sym) => renderRow(sym));
              })()}
            </Box>
          )}
        </CardContent>
      </Card>

      <Toast
        open={toast.open}
        message={toast.message}
        severity={toast.severity}
        onClose={hideToast}
      />

      {/* Manage Watchlist Dialog */}
      <Dialog open={manageOpen} onClose={() => setManageOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AccountBalance sx={{ color: 'primary.main' }} />
          Manage Watchlist
        </DialogTitle>
        <DialogContent dividers sx={styles.manageDialogContent}>
          {/* Symbols List */}
          {userSymbols.length > 0 && (
            <Box>
              <Typography variant="subtitle2" sx={{ mb: 1.5 }}>Your Symbols ({userSymbols.length})</Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, maxHeight: 200, overflowY: 'auto' }}>
                {userSymbols.map(sym => (
                  <Box 
                    key={sym} 
                    sx={styles.symbolItem}
                  >
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>{sym}</Typography>
                    <IconButton 
                      size="small" 
                      onClick={() => handleRemove(sym)}
                      sx={{
                        minWidth: { xs: 44, sm: 'auto' },
                        minHeight: { xs: 44, sm: 'auto' }
                      }}
                      aria-label={`Remove ${sym}`}
                    >
                      <DeleteOutline fontSize="small" />
                    </IconButton>
                  </Box>
                ))}
              </Box>
            </Box>
          )}

          {/* Import Section */}
          <Divider />
          <Box>
            <Typography variant="subtitle2" sx={{ mb: 1.5 }}>Import Symbols</Typography>
            <TextField
              fullWidth
              size="small"
              placeholder="AAPL,MSFT,BTC,ETH"
              helperText="Paste comma-separated symbols and press Enter"
              onKeyDown={async (e) => {
                if (e.key === 'Enter') {
                  const val = (e.currentTarget as HTMLInputElement).value || '';
                  const parts = val.split(',').map(s => s.trim().toUpperCase()).filter(Boolean);
                  for (const p of parts) {
                    setNewSymbol(p);
                    await handleAdd();
                  }
                  (e.currentTarget as HTMLInputElement).value = '';
                }
              }}
            />
            <Box sx={styles.importButtons}>
              <Button
                size="small"
                variant="outlined"
                startIcon={<FileUpload />}
                onClick={() => fileInputRef.current?.click()}
                disabled={userSymbols.length === 0}
                aria-label="Import watchlist from file"
              >
                Import File
              </Button>
              <Button
                size="small"
                variant="outlined"
                startIcon={<FileDownload />}
                onClick={handleExportCSV}
                disabled={userSymbols.length === 0}
                aria-label="Export watchlist to CSV"
              >
                Export CSV
              </Button>
              <Button
                size="small"
                variant="outlined"
                startIcon={<FileDownload />}
                onClick={handleExportJSON}
                disabled={userSymbols.length === 0}
                aria-label="Export watchlist to JSON"
              >
                Export JSON
              </Button>
            </Box>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.json"
              style={{ display: 'none' }}
              onChange={handleImportFile}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => setManageOpen(false)}
            onKeyDown={(e) => {
              if (e.key === 'Escape') {
                setManageOpen(false);
              }
            }}
            aria-label="Close manage watchlist dialog"
          >
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Batch Alerts Dialog */}
      <Dialog open={batchAlertsOpen} onClose={() => setBatchAlertsOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create Batch Price Alerts</DialogTitle>
        <DialogContent dividers>
          {userSymbols.length === 0 ? (
            <Typography variant="body2" color="text.secondary">Add symbols to your watchlist first.</Typography>
          ) : (
            <>
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="subtitle2">Select symbols ({selectedBatchSymbols.size} selected)</Typography>
                  <Button 
                    size="small" 
                    onClick={handleSelectAllBatch}
                    aria-label={selectedBatchSymbols.size === userSymbols.length ? 'Deselect all symbols' : 'Select all symbols'}
                  >
                    {selectedBatchSymbols.size === userSymbols.length ? 'Deselect All' : 'Select All'}
                  </Button>
                </Box>
                <Box sx={{ maxHeight: 200, overflowY: 'auto', border: '1px solid', borderColor: 'divider', borderRadius: 1, p: 1 }}>
                  <FormGroup>
                    {userSymbols.map(sym => {
                      const item = pricesMap[sym] || watchlist.find(w => w.symbol === sym);
                      return (
                        <FormControlLabel
                          key={sym}
                          control={
                            <Checkbox
                              checked={selectedBatchSymbols.has(sym)}
                              onChange={() => handleToggleBatchSymbol(sym)}
                              size="small"
                            />
                          }
                          label={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Typography variant="body2" sx={{ fontWeight: 600 }}>{sym}</Typography>
                              {item && (
                                <Typography variant="caption" color="text.secondary">
                                  ${item.price.toFixed(2)}
                                </Typography>
                              )}
                            </Box>
                          }
                        />
                      );
                    })}
                  </FormGroup>
                </Box>
              </Box>
              <Divider sx={{ my: 2 }} />
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <FormControl>
                  <RadioGroup
                    row
                    value={batchAlertType}
                    onChange={(e) => setBatchAlertType(e.target.value as 'price' | 'percent')}
                  >
                    <FormControlLabel value="price" control={<Radio size="small" />} label="Price" />
                    <FormControlLabel value="percent" control={<Radio size="small" />} label="Percent change" />
                  </RadioGroup>
                </FormControl>
                <RadioGroup
                  row
                  value={batchAlertCond}
                  onChange={(e) => setBatchAlertCond((e.target as HTMLInputElement).value as 'above' | 'below')}
                >
                  <FormControlLabel value="above" control={<Radio size="small" />} label="Above" />
                  <FormControlLabel value="below" control={<Radio size="small" />} label="Below" />
                </RadioGroup>
                <TextField
                  label={batchAlertType === 'price' ? 'Target Price ($)' : 'Percent Change (%)'}
                  size="small"
                  fullWidth
                  value={batchAlertPrice}
                  onChange={(e) => setBatchAlertPrice(e.target.value)}
                  type="number"
                  inputProps={{ step: batchAlertType === 'price' ? '0.01' : '0.1' }}
                  helperText={
                    batchAlertType === 'percent' && batchAlertPrice
                      ? `Alert when price ${batchAlertCond === 'above' ? 'rises' : 'drops'} by ${batchAlertPrice}%`
                      : undefined
                  }
                />
              </Box>
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBatchAlertsOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleCreateBatchAlerts}
            disabled={batchCreating || selectedBatchSymbols.size === 0 || !batchAlertPrice}
          >
            {batchCreating ? 'Creating...' : `Create ${selectedBatchSymbols.size} Alert${selectedBatchSymbols.size !== 1 ? 's' : ''}`}
          </Button>
        </DialogActions>
      </Dialog>

      <Popover
        open={Boolean(alertAnchor)}
        anchorEl={alertAnchor}
        onClose={() => setAlertAnchor(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
        PaperProps={{ sx: { p: 2, width: 260, minWidth: 260 } }}
      >
        <Typography variant="subtitle2" sx={{ mb: 1 }}>
          Create alert for {alertSymbol}
        </Typography>
        <RadioGroup
          row
          value={alertCond}
          onChange={(e) => setAlertCond((e.target as HTMLInputElement).value as 'above' | 'below')}
          sx={{ mb: 1 }}
        >
          <FormControlLabel value="above" control={<Radio size="small" />} label="Above" />
          <FormControlLabel value="below" control={<Radio size="small" />} label="Below" />
        </RadioGroup>
        <TextField
          label="Price"
          size="small"
          fullWidth
          value={alertPrice}
          onChange={(e) => setAlertPrice(e.target.value)}
          sx={{ mb: 1 }}
          type="number"
          inputProps={{ step: '0.01' }}
        />
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
          <Button size="small" onClick={() => setAlertAnchor(null)}>Cancel</Button>
          <Button size="small" variant="contained" onClick={async () => { await handleCreateAlert(); portfolioService.trackEvent('mw_alert_create'); }}>Create</Button>
        </Box>
      </Popover>
      <Suspense fallback={<Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}><CircularProgress /></Box>}>
        <MarketWatchDrawer
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          item={drawerSymbol ? (pricesMap[drawerSymbol] || watchlist.find(w=>w.symbol===drawerSymbol) || null) as any : null}
          series7d={drawerSymbol ? priceSeries[drawerSymbol] : undefined}
          provider={usingFallback ? 'fallback' : 'live'}
          lastUpdatedTs={lastUpdated}
        />
      </Suspense>
      
      <Suspense fallback={<Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}><CircularProgress /></Box>}>
        <WatchlistAddDialog
          open={addDialogOpen}
          onClose={() => setAddDialogOpen(false)}
          onAdd={async (symbol) => {
          const updated = await portfolioService.addToWatchlist(symbol);
          setUserSymbols(updated.symbols);
          setNewSymbol('');
          // Update metadata and categories
          if (updated.metadata) {
            const categories = new Set<string>();
            Object.values(updated.metadata).forEach((meta: any) => {
              if (meta.categories) {
                meta.categories.forEach((cat: string) => categories.add(cat));
              }
            });
            setAvailableCategories(Array.from(categories).sort());
          }
          await fetchWatchlist();
          // Update watchlist items with metadata after fetch
          if (updated.metadata) {
            setWatchlist(prev => prev.map(item => ({
              ...item,
              categories: updated.metadata?.[item.symbol]?.categories || [],
              tags: updated.metadata?.[item.symbol]?.tags || []
            })));
          }
          setPriceSeries({});
          cleanupSSE();
          tryStartSSE();
        }}
        existingSymbols={userSymbols}
      />
      </Suspense>
    </Box>
  );
};

export default React.memo(MarketWatch);

// Render alert popover near the end of the file inside JSX return earlier
// We append Popover right after CardContent so it's part of the component tree

// Alert popover
// Placed at end to avoid cluttering row JSX
// Using anchor & state declared above
// Render element appended to body via portal automatically by MUI
// This component content is included within MarketWatch return below

