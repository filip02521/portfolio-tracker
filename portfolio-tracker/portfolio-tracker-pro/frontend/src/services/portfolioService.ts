import axios from 'axios';
import { logger } from '../utils/logger';

// API URL - try proxy first, fallback to direct connection
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000, // 10 seconds default - most endpoints should respond faster. PDF generation uses per-request timeout override.
  headers: {
    'Content-Type': 'application/json',
  },
});

// Ensure timeout is always respected - override any global axios defaults
if (typeof axios.defaults !== 'undefined') {
  axios.defaults.timeout = 10000;
}

// Request interceptor for auth tokens
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const message = error.response.data?.detail || error.response.data?.message || error.message;
      
      if (status === 401) {
        // Handle unauthorized access - prevent redirect loop
        // Only redirect if not already on login/register page
        const currentPath = window.location.pathname;
        
        // Always remove token first
        localStorage.removeItem('authToken');
        
        if (currentPath !== '/login' && currentPath !== '/register') {
          // Set flag to prevent loops
          sessionStorage.setItem('auth:invalid_token', 'true');
          // Use event to trigger navigation instead of full page reload
          // This prevents redirect loops and allows React Router to handle it
          window.dispatchEvent(new CustomEvent('auth:logout', { detail: { reason: 'unauthorized' } }));
        } else {
          // Already on login page - just clear flags
          sessionStorage.removeItem('auth:invalid_token');
        }
      } else if (status === 503) {
        // Service unavailable - timeout or connection errors
        logger.error('Service temporarily unavailable:', message);
        error.userMessage = 'Exchange APIs are temporarily unavailable. Please try again in a moment.';
      } else if (status === 502) {
        // Bad gateway - request failed
        logger.error('Bad gateway:', message);
        error.userMessage = 'Failed to fetch data from exchange. Please check your internet connection.';
      } else if (status === 500) {
        // Internal server error
        logger.error('Internal server error:', message);
        error.userMessage = 'An unexpected error occurred. Please try again later.';
      } else {
        error.userMessage = message || 'An error occurred while fetching data.';
      }
    } else if (error.request) {
      // Request was made but no response received
      logger.error('No response received:', error.message);
      
      // Check if it's a timeout
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        error.userMessage = 'Request timeout. The server is taking too long to respond. Please try again.';
      } else if (error.message?.includes('Network Error') || error.code === 'ERR_NETWORK') {
        error.userMessage = 'Cannot connect to server. Please check your internet connection.';
      } else {
        error.userMessage = 'Cannot connect to server. Please check if the backend is running on http://localhost:8000';
      }
    } else {
      // Something else happened
      logger.error('Request setup error:', error.message);
      error.userMessage = error.message || 'An error occurred while setting up the request.';
    }
    
    return Promise.reject(error);
  }
);

export interface PortfolioSummary {
  total_value_usd: number;
  total_value_pln: number;
  total_pnl: number;
  total_pnl_percent: number;
  active_exchanges: number;
  total_assets: number;
  last_updated: string;
  warnings?: string[];
}

export interface AssetSource {
  exchange: string;
  amount: number;
  value_usd: number;
  value_pln: number;
  average_price: number;
  current_price: number;
  pnl: number;
  pnl_percent: number;
  realized_pnl: number;
  price_source?: string;
  issues?: string[];
  cost_basis_usd?: number;
}

export interface Asset {
  symbol: string;
  amount: number;
  value_usd: number;
  value_pln: number;
  pnl: number;
  pnl_percent: number;
  exchange: string;
  average_price?: number;
  current_price?: number;
  realized_pnl?: number;
  exchange_price?: number;
  exchange_value_usd?: number;
  price_source?: string;
  issues?: string[];
  asset_type?: string;
  sources?: AssetSource[];
  source_count?: number;
  cost_basis_usd?: number;
  exchanges?: string[];
}

export interface DueDiligencePillar {
  name: string;
  score?: number;
  weight: number;
  confidence: number;
  missingMetrics?: string[];
}

export interface DueDiligenceSummary {
  symbol: string;
  score?: number;
  verdict?: string;
  confidence: number;
  cachedAt?: string | null;
  validUntil?: string | null;
  pillars: DueDiligencePillar[];
  warnings?: string[];
  missingPillars?: string[];
  rawScore?: number;
}

export interface Transaction {
  id: string;
  symbol: string;
  type: string;
  amount: number;
  price: number;
  date: string;
  exchange: string;
  commission: number;
  commission_currency: string;
  asset_name?: string;
  isin?: string;
}

export interface CreateTransactionRequest {
  symbol: string;
  type: string;
  amount: number;
  price: number;
  date: string;
  exchange: string;
  commission?: number;
  commission_currency?: string;
  asset_name?: string;
  isin?: string;
}

export interface UpdateTransactionRequest {
  symbol?: string;
  type?: string;
  amount?: number;
  price?: number;
  date?: string;
  exchange?: string;
  commission?: number;
  commission_currency?: string;
  asset_name?: string;
  isin?: string;
}

export interface SymbolSearchResult {
  symbol: string;
  name?: string;
  type?: string;
  exchange?: string;
  currency?: string;
  isin?: string;
  source?: string;
}

export interface ExchangeStatus {
  exchange: string;
  connected: boolean;
  total_value: number;
  error?: string;
}

export interface PerformanceAnalytics {
  period: string;
  total_return: number;
  daily_returns: number[];
  volatility: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  message?: string;
  data_points?: number;
}

export interface AllocationAnalytics {
  by_asset: Record<string, number>;
  by_exchange: Record<string, number>;
  by_type: Record<string, number>;
}

export interface PortfolioInsight {
  type: string;
  title: string;
  message: string;
  value?: number;
  asset?: string;
  data?: any;
  status?: string;
}

export interface PortfolioAlert {
  type: 'critical' | 'warning' | 'info';
  title: string;
  message: string;
  severity: 'high' | 'medium' | 'low';
}

export interface PortfolioRecommendation {
  type: string;
  priority: 'high' | 'medium' | 'low';
  action: string;
  details: string;
  asset?: string;
  current_percentage?: number;
  target_percentage?: number;
  current_assets?: number;
  recommended_assets?: number;
}

export interface SmartInsights {
  insights: PortfolioInsight[];
  alerts: PortfolioAlert[];
  recommendations: PortfolioRecommendation[];
  health_score: number;
  risk_level: 'Low' | 'Medium' | 'High' | 'Very High' | 'Unknown' | 'Empty';
  total_value: number;
  timestamp: string;
}

export interface PortfolioHistoryPoint {
  date: string;
  value_usd: number;
  value_pln: number;
  total_assets: number;
  active_exchanges: number;
}

// Cache interface
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number; // Time to live in milliseconds
  version?: string; // Cache version for schema changes
}

interface PersistentCacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
  version: string;
}

// Simple in-memory cache with localStorage persistence for transactions
class Cache {
  private cache: Map<string, CacheEntry<any>> = new Map();
  private readonly STORAGE_KEY_PREFIX = 'portfolio:cache:';
  private readonly CACHE_VERSION = '1.0'; // Increment on schema changes
  private readonly PERSISTENT_KEYS = new Set(['transactions:50:0:']); // Keys that should persist

  private getStorageKey(key: string): string {
    return `${this.STORAGE_KEY_PREFIX}${key}`;
  }

  set<T>(key: string, data: T, ttl: number = 30000): void {
    const entry: CacheEntry<T> = {
      data,
      timestamp: Date.now(),
      ttl,
      version: this.CACHE_VERSION
    };
    
    this.cache.set(key, entry);
    
    // Persist to localStorage for transaction cache
    if (this.PERSISTENT_KEYS.has(key) || key.startsWith('transactions:')) {
      try {
        const persistentEntry: PersistentCacheEntry<T> = {
          data,
          timestamp: Date.now(),
          ttl,
          version: this.CACHE_VERSION
        };
        localStorage.setItem(this.getStorageKey(key), JSON.stringify(persistentEntry));
      } catch (error) {
        // localStorage might be full or unavailable - silently fail
        logger.debug('Failed to persist cache to localStorage', error);
      }
    }
  }

  get<T>(key: string): T | null {
    // Try in-memory cache first
    const entry = this.cache.get(key);
    if (entry) {
      const age = Date.now() - entry.timestamp;
      if (age <= entry.ttl) {
        return entry.data as T;
      }
      // Expired - remove from memory
      this.cache.delete(key);
    }

    // Try localStorage for persistent keys
    if (this.PERSISTENT_KEYS.has(key) || key.startsWith('transactions:')) {
      try {
        const stored = localStorage.getItem(this.getStorageKey(key));
        if (stored) {
          const persistentEntry: PersistentCacheEntry<T> = JSON.parse(stored);
          
          // Check version compatibility
          if (persistentEntry.version !== this.CACHE_VERSION) {
            localStorage.removeItem(this.getStorageKey(key));
            return null;
          }
          
          const age = Date.now() - persistentEntry.timestamp;
          if (age <= persistentEntry.ttl) {
            // Restore to memory cache
            this.cache.set(key, {
              data: persistentEntry.data,
              timestamp: persistentEntry.timestamp,
              ttl: persistentEntry.ttl,
              version: persistentEntry.version
            });
            return persistentEntry.data as T;
          } else {
            // Expired - remove from localStorage
            localStorage.removeItem(this.getStorageKey(key));
          }
        }
      } catch (error) {
        // Invalid JSON or localStorage error - remove corrupted entry
        try {
          localStorage.removeItem(this.getStorageKey(key));
        } catch {
          // Ignore removal errors
        }
        logger.debug('Failed to read from localStorage cache', error);
      }
    }

    return null;
  }

  clear(): void {
    this.cache.clear();
    // Clear persistent cache
    try {
      const keysToRemove: string[] = [];
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith(this.STORAGE_KEY_PREFIX)) {
          keysToRemove.push(key);
        }
      }
      keysToRemove.forEach(key => localStorage.removeItem(key));
    } catch (error) {
      logger.debug('Failed to clear localStorage cache', error);
    }
  }

  invalidate(key: string): void {
    this.cache.delete(key);
    // Remove from localStorage
    try {
      localStorage.removeItem(this.getStorageKey(key));
    } catch (error) {
      logger.debug('Failed to invalidate localStorage cache', error);
    }
  }

  clearTransactionCache(): void {
    // Clear all transaction-related cache entries
    const keysToRemove: string[] = [];
    this.cache.forEach((_, key) => {
      if (key.startsWith('transactions:')) {
        keysToRemove.push(key);
      }
    });
    keysToRemove.forEach(key => this.invalidate(key));
  }
}

const cache = new Cache();

// Request deduplication: track in-flight requests
class RequestDeduplicator {
  private inflight: Map<string, Promise<any>> = new Map();

  async deduplicate<T>(key: string, fn: () => Promise<T>): Promise<T> {
    const existing = this.inflight.get(key);
    if (existing) {
      return existing;
    }

    const promise = fn().finally(() => {
      this.inflight.delete(key);
    });
    
    this.inflight.set(key, promise);
    return promise;
  }
}

const requestDeduplicator = new RequestDeduplicator();

// Cache keys
const CACHE_KEYS = {
  SUMMARY: 'portfolio:summary',
  ASSETS: 'portfolio:assets',
  HISTORY: (days: number) => `portfolio:history:${days}`,
  ALLOCATION: 'portfolio:allocation',
  PERFORMANCE: (days: number) => `analytics:performance:${days}`,
  EXCHANGE_STATUS: 'exchanges:status',
  DUE_DILIGENCE: (symbol: string) => `due_diligence:${symbol.toUpperCase()}`,
};

class PortfolioService {
  // Lightweight retry helper with exponential backoff and per-call timeout override
  private async withRetry<T>(fn: () => Promise<T>, retries = 2, baseDelayMs = 500): Promise<T> {
    let attempt = 0;
    // eslint-disable-next-line no-constant-condition
    while (true) {
      try {
        return await fn();
      } catch (err: any) {
        attempt += 1;
        const isTimeout = err?.code === 'ECONNABORTED' || err?.message?.includes('timeout');
        const isNetwork = err?.message?.includes('Network Error') || err?.code === 'ERR_NETWORK';
        if (attempt > retries || (!isTimeout && !isNetwork)) {
          throw err;
        }
        const delay = baseDelayMs * Math.pow(2, attempt - 1);
        await new Promise((r) => setTimeout(r, delay));
      }
    }
  }

  // Telemetry: track lightweight UI events (exposed in Prometheus /metrics)
  async trackEvent(event: string): Promise<void> {
    try {
      if (!event) return;
      await apiClient.post('/metrics/track', { event });
    } catch (e) {
      // best-effort, swallow errors
      return;
    }
  }
  // Cache TTL in milliseconds - optimized for better performance
  private readonly CACHE_TTL = {
    SUMMARY: 30000, // 30 seconds - summary can be cached longer
    ASSETS: 45000, // 45 seconds - assets change less frequently
    HISTORY: 300000, // 5 minutes - history is very stable (historical data)
    ALLOCATION: 60000, // 60 seconds - allocation changes slowly
    PERFORMANCE: 120000, // 2 minutes - analytics don't change often
    ANALYTICS: 120000, // 2 minutes - analytics don't change often
    EXCHANGE_STATUS: 30000, // 30 seconds - exchange status updates moderately
    MARKET_PRICES: 10000, // 10 seconds - market prices change frequently
    SYMBOL_HISTORY: 300000, // 5 minutes - historical data is very stable
  DUE_DILIGENCE: 3600000, // 1 hour - due diligence is long-horizon
  };

  // Prefetch methods for intelligent data loading
  /**
   * Prefetch critical dashboard data in the background
   * This method doesn't wait for results and doesn't throw errors
   */
  prefetchDashboardData(): void {
    // Prefetch summary, assets, and history in parallel (fire and forget)
    Promise.all([
      this.getSummary().catch(() => {}),
      this.getAssets().catch(() => {}),
      this.getPortfolioHistory(30).catch(() => {}),
    ]).catch(() => {
      // Silently fail - prefetch should never block or show errors
    });
  }

  /**
   * Prefetch likely-needed data based on current context
   * @param context - Current page/component context
   */
  prefetchContextualData(context: 'dashboard' | 'market-watch' | 'analytics' | 'portfolio'): void {
    switch (context) {
      case 'dashboard':
        // Prefetch data that's likely to be needed on dashboard
        Promise.all([
          this.getPriceAlerts().catch(() => []),
          this.getUserWatchlist().catch(() => []),
          this.getPerformanceAnalytics(30).catch(() => null),
          this.getRiskAnalysis().catch(() => null),
        ]).catch(() => {});
        break;
      case 'market-watch':
        // Prefetch watchlist prices
        this.getUserWatchlist()
          .then((watchlist) => {
            if (watchlist) {
              const symbols = Array.isArray(watchlist) 
                ? watchlist 
                : (watchlist as any)?.symbols || [];
              if (symbols.length > 0) {
                this.getWatchlistPricesBatch(symbols.slice(0, 50)).catch(() => {});
              }
            }
          })
          .catch(() => {});
        break;
      case 'analytics':
        // Prefetch analytics data
        Promise.all([
          this.getPerformanceAnalytics(30).catch(() => null),
          this.getAllocationAnalytics().catch(() => null),
          this.getPortfolioHistory(365).catch(() => []),
        ]).catch(() => {});
        break;
      case 'portfolio':
        // Prefetch portfolio data
        Promise.all([
          this.getAssets().catch(() => []),
          this.getAllocationAnalytics().catch(() => null),
        ]).catch(() => {});
        break;
    }
  }

  async getSummary(forceRefresh = false, signal?: AbortSignal): Promise<PortfolioSummary> {
    const cacheKey = CACHE_KEYS.SUMMARY;
    
    if (!forceRefresh) {
      const cached = cache.get<PortfolioSummary>(cacheKey);
      if (cached) return cached;
    }

    return requestDeduplicator.deduplicate(`summary:${forceRefresh}`, async () => {
    const response = await apiClient.get('/portfolio/summary', { 
      signal,
      timeout: 45000 // 45s timeout (backend may exceed 15s budget but still return data after ~21s)
    });
      cache.set(cacheKey, response.data, this.CACHE_TTL.SUMMARY);
      return response.data;
    });
  }

  async getAssets(forceRefresh = false, signal?: AbortSignal): Promise<Asset[]> {
    const cacheKey = CACHE_KEYS.ASSETS;
    
    if (!forceRefresh) {
      const cached = cache.get<Asset[]>(cacheKey);
      if (cached) return cached;
    }

    const response = await apiClient.get('/portfolio/assets', { 
      signal,
      timeout: 45000 // 45s timeout (backend has 15s budget but may need more for large portfolios, returns after ~21s)
    });
    cache.set(cacheKey, response.data, this.CACHE_TTL.ASSETS);
    return response.data;
  }

  async getTransactions(
    limit = 50, 
    offset = 0, 
    forceRefresh = false,
    filters?: {
      type?: string;
      symbol?: string;
      exchange?: string;
      search?: string;
      date_from?: string;
      date_to?: string;
    }
  ): Promise<Transaction[]> {
    // Build cache key with filters for proper cache invalidation
    const filterKey = filters ? JSON.stringify(filters) : '';
    const cacheKey = `transactions:${limit}:${offset}:${filterKey}`;
    
    if (!forceRefresh && offset === 0 && !filters) {
      // Only cache first page when no filters - check persistent cache
      const cached = cache.get<Transaction[]>(cacheKey);
      if (cached) return cached;
    }

    // Build query params
    const params: any = { limit, offset };
    if (filters) {
      if (filters.type) params.type = filters.type;
      if (filters.symbol) params.symbol = filters.symbol;
      if (filters.exchange) params.exchange = filters.exchange;
      if (filters.search) params.search = filters.search;
      if (filters.date_from) params.date_from = filters.date_from;
      if (filters.date_to) params.date_to = filters.date_to;
    }

    const response = await apiClient.get('/transactions', { 
      params,
      timeout: 30000 // 30s timeout for transactions (increased due to backend filtering operations)
    });
    
    // Only cache if no filters and first page - use longer TTL for persistent cache
    if (!filters && offset === 0) {
      cache.set(cacheKey, response.data, 3600000); // 1 hour for first page (persistent)
    } else if (!filters) {
      // Cache other pages with shorter TTL (in-memory only)
      cache.set(cacheKey, response.data, 300000); // 5 minutes for paginated results
    }
    
    return response.data;
  }

  async syncTransactions(limit = 50): Promise<{ summary: { imported_count: number; imported_by_exchange: Record<string, number>; errors: Array<{ exchange: string; trade: string; error: string }> } }> {
    // Long timeout for sync - can take several minutes for multiple exchanges
    const response = await apiClient.post('/sync/exchanges/import', { limit }, { timeout: 300000 }); // 5 minutes timeout
    // Clear transaction cache after sync
    cache.clearTransactionCache();
    // Also invalidate assets and summary as they depend on transactions
    cache.invalidate(CACHE_KEYS.ASSETS);
    cache.invalidate(CACHE_KEYS.SUMMARY);
    return response.data;
  }

  async createTransaction(data: CreateTransactionRequest): Promise<Transaction> {
    const response = await apiClient.post('/transactions', data);
    // Invalidate transaction cache
    cache.clearTransactionCache();
    cache.invalidate(CACHE_KEYS.ASSETS); // Assets might change
    cache.invalidate(CACHE_KEYS.SUMMARY);
    return response.data;
  }

  async updateTransaction(id: string, data: UpdateTransactionRequest): Promise<Transaction> {
    const response = await apiClient.put(`/transactions/${id}`, data);
    // Invalidate relevant caches
    cache.clearTransactionCache();
    cache.invalidate(CACHE_KEYS.ASSETS);
    cache.invalidate(CACHE_KEYS.SUMMARY);
    return response.data;
  }

  async deleteTransaction(id: string): Promise<void> {
    await apiClient.delete(`/transactions/${id}`);
    // Invalidate relevant caches
    cache.clearTransactionCache();
    cache.invalidate(CACHE_KEYS.ASSETS);
    cache.invalidate(CACHE_KEYS.SUMMARY);
  }

  async exportTransactions(format: 'csv' | 'json' = 'csv'): Promise<Blob> {
    const response = await apiClient.get('/transactions/export', {
      params: { format },
      responseType: 'blob'
    });
    return response.data;
  }

  async getExchangeStatus(forceRefresh = false): Promise<ExchangeStatus[]> {
    const cacheKey = CACHE_KEYS.EXCHANGE_STATUS;
    
    if (!forceRefresh) {
      const cached = cache.get<ExchangeStatus[]>(cacheKey);
      if (cached) return cached;
    }

    const response = await apiClient.get('/exchanges/status');
    cache.set(cacheKey, response.data, this.CACHE_TTL.EXCHANGE_STATUS);
    return response.data;
  }

  async getPerformanceAnalytics(days = 30, forceRefresh = false): Promise<PerformanceAnalytics> {
    const cacheKey = CACHE_KEYS.PERFORMANCE(days);
    
    if (!forceRefresh) {
      const cached = cache.get<PerformanceAnalytics>(cacheKey);
      if (cached) return cached;
    }

    const response = await this.withRetry(
      () => apiClient.get('/analytics/performance', { params: { days }, timeout: 15000 }),
      2,
      400
    );
    cache.set(cacheKey, response.data, this.CACHE_TTL.PERFORMANCE);
    return response.data;
  }

  async getSmartInsights(forceRefresh = false): Promise<SmartInsights> {
    const cacheKey = 'insights:smart';
    
    if (!forceRefresh) {
      const cached = cache.get<SmartInsights>(cacheKey);
      if (cached) return cached;
    }

    const response = await this.withRetry(
      () => apiClient.get('/insights', { timeout: 12000 }),
      2,
      400
    );
    cache.set(cacheKey, response.data, this.CACHE_TTL.ANALYTICS);
    return response.data;
  }

  async getRiskAlerts(days: number = 90, forceRefresh = false): Promise<any> {
    const cacheKey = `risk_alerts:${days}`;
    if (!forceRefresh) {
      const cached = cache.get<any>(cacheKey);
      if (cached) {
        return cached;
      }
    }

    const response = await this.withRetry(
      () => apiClient.get('/insights/risk-alerts', { 
        params: { days },
        timeout: 30000 
      }),
      2,
      1000
    );
    // Cache for 5 minutes (risk can change quickly)
    cache.set(cacheKey, response.data, 300);
    return response.data;
  }

  async getRebalancingSuggestions(
    threshold: number = 5,
    maxSuggestions: number = 5,
    forceRefresh = false
  ): Promise<any> {
    const cacheKey = `rebalancing:${threshold}:${maxSuggestions}`;
    if (!forceRefresh) {
      const cached = cache.get<any>(cacheKey);
      if (cached) {
        return cached;
      }
    }

    const response = await this.withRetry(
      () =>
        apiClient.get('/insights/rebalancing-suggestions', {
          params: { threshold, max_suggestions: maxSuggestions },
          timeout: 30000,
        }),
      2,
      800
    );

    // Cache for 60 seconds (portfolio allocation can change relatively quickly)
    cache.set(cacheKey, response.data, 60);
    return response.data;
  }

  async getPortfolioHealth(forceRefresh = false): Promise<any> {
    const cacheKey = 'insights:health-score';
    if (!forceRefresh) {
      const cached = cache.get<any>(cacheKey);
      if (cached) {
        return cached;
      }
    }

    const response = await this.withRetry(
      () =>
        apiClient.get('/insights/health-score', {
          timeout: 15000,
        }),
      2,
      500
    );

    // Health score zmienia się relatywnie wolno – cache 5 minut
    cache.set(cacheKey, response.data, 300);
    return response.data;
  }

  async getDueDiligence(symbol: string, refresh = false): Promise<DueDiligenceSummary> {
    const normalized = (symbol || '').toUpperCase();
    const cacheKey = CACHE_KEYS.DUE_DILIGENCE(normalized);

    if (!refresh) {
      const cached = cache.get<DueDiligenceSummary>(cacheKey);
      if (cached) {
        return cached;
      }
    }

    const response = await this.withRetry(
      () =>
        apiClient.get(`/analysis/due-diligence/${encodeURIComponent(normalized)}`, {
          params: { refresh },
          timeout: 15000,
        }),
      1,
      500
    );

    const payload = response.data?.result ?? {};
    const pillarsRaw = Array.isArray(payload?.pillar_scores) ? payload.pillar_scores : [];
    const summary: DueDiligenceSummary = {
      symbol: response.data?.symbol ?? normalized,
      score: typeof payload?.normalized_score === 'number' ? payload.normalized_score : undefined,
    rawScore: typeof payload?.total_score === 'number' ? payload.total_score : undefined,
      verdict: payload?.verdict ?? undefined,
      confidence: typeof payload?.confidence === 'number' ? payload.confidence : 0,
      cachedAt: payload?.cached_at ?? payload?.cachedAt ?? null,
      validUntil: payload?.valid_until ?? payload?.validUntil ?? null,
      pillars: pillarsRaw.map((pillar: any) => ({
        name:
          typeof pillar?.name === 'string'
            ? pillar.name
            : pillar?.name?.value ?? pillar?.name ?? 'unknown',
        score: typeof pillar?.score === 'number' ? pillar.score * 100 : undefined,
        weight: typeof pillar?.weight === 'number' ? pillar.weight : 0,
        confidence: typeof pillar?.confidence === 'number' ? pillar.confidence : 0,
      missingMetrics: Array.isArray(pillar?.missing_metrics) ? pillar.missing_metrics : undefined,
      })),
      warnings: Array.isArray(payload?.global_warnings) ? payload.global_warnings : undefined,
      missingPillars: Array.isArray(payload?.missing_pillars) ? payload.missing_pillars : undefined,
    };

    cache.set(cacheKey, summary, this.CACHE_TTL.DUE_DILIGENCE);
    return summary;
  }

  // Goals API
  async getGoals(): Promise<any[]> {
    const response = await apiClient.get('/goals', { timeout: 30000 }); // 30s timeout (increased due to heavy portfolio summary calculation)
    return response.data;
  }

  async getMigrationStatus(): Promise<{
    status: {
      transactions: { migrated: boolean; count: number };
      watchlist: { migrated: boolean; count: number };
      goals: { migrated: boolean; count: number };
      portfolio_history: { migrated: boolean; count: number };
      users: { migrated: boolean; count: number };
    };
    all_migrated: boolean;
    total_items: number;
    migration_complete: boolean;
  }> {
    const response = await apiClient.get('/migration/status');
    return response.data;
  }

  async createGoal(goalData: any): Promise<any> {
    const response = await apiClient.post('/goals', goalData);
    return response.data;
  }

  async updateGoal(goalId: number, updates: any): Promise<any> {
    const response = await apiClient.put(`/goals/${goalId}`, updates);
    return response.data;
  }

  async deleteGoal(goalId: number): Promise<void> {
    await apiClient.delete(`/goals/${goalId}`);
  }

  async getGoalProjections(goalId: number): Promise<any> {
    const response = await apiClient.get(`/goals/${goalId}/projections`);
    return response.data;
  }

  // Tax Optimization API
  async getTaxCalculation(year?: number): Promise<any> {
    const url = year ? `/tax/calculation?year=${year}` : '/tax/calculation';
    const response = await apiClient.get(url);
    return response.data;
  }

  async getTaxSuggestions(): Promise<any> {
    const response = await apiClient.get('/tax/suggestions');
    return response.data;
  }

  async getTaxDeadline(): Promise<any> {
    const response = await apiClient.get('/tax/deadline');
    return response.data;
  }

  async calculateTaxScenario(additionalLosses: number): Promise<any> {
    const response = await apiClient.post('/tax/scenario', null, {
      params: { additional_losses: additionalLosses }
    });
    return response.data;
  }

  // Price Alerts API
  async getPriceAlerts(): Promise<any[]> {
    const response = await apiClient.get('/price-alerts');
    return response.data;
  }

  async createPriceAlert(alertData: {
    symbol: string;
    condition: 'above' | 'below';
    price: number;
    name?: string;
  }): Promise<any> {
    const response = await apiClient.post('/price-alerts', alertData);
    return response.data;
  }

  async updatePriceAlert(alertId: number, updates: {
    condition?: 'above' | 'below';
    price?: number;
    active?: boolean;
  }): Promise<any> {
    const response = await apiClient.put(`/price-alerts/${alertId}`, updates);
    return response.data;
  }

  async deletePriceAlert(alertId: number): Promise<void> {
    await apiClient.delete(`/price-alerts/${alertId}`);
  }

  async checkPriceAlerts(): Promise<any> {
    const response = await apiClient.get('/price-alerts/check');
    return response.data;
  }

  // Market Data API
  async getWatchlistPrices(symbols?: string[], forceRefresh = false): Promise<any> {
    // Cache watchlist prices with shorter TTL (market data changes frequently)
    const symbolsKey = symbols ? symbols.sort().join(',') : 'default';
    const cacheKey = `watchlist:${symbolsKey}`;
    
    if (!forceRefresh) {
      const cached = cache.get<any>(cacheKey);
      if (cached) return cached;
    }
    
    const params = symbols ? { symbols: symbols.join(',') } : {};
    const response = await this.withRetry(
      () => apiClient.get('/market/watchlist', { params, timeout: 12000 }),
      2,
      400
    );
    
    // Cache for 10 seconds (market prices change frequently)
    cache.set(cacheKey, response.data, this.CACHE_TTL.MARKET_PRICES);
    return response.data;
  }

  async getWatchlistPricesBatch(symbols?: string[], limit: number = 50, forceRefresh = false, includeDdScores: boolean = false): Promise<any> {
    // Batch endpoint for large watchlists (up to 50 symbols)
    const symbolsKey = symbols ? symbols.sort().join(',') : 'default';
    const cacheKey = `watchlist:batch:${symbolsKey}:${limit}`;
    
    if (!forceRefresh) {
      const cached = cache.get<any>(cacheKey);
      if (cached) return cached;
    }
    
    const params: any = { limit };
    if (symbols) {
      params.symbols = symbols.join(',');
    }
    if (includeDdScores) {
      params.include_dd_scores = true;
    }
    const response = await this.withRetry(
      () => apiClient.get('/market/watchlist/batch', { params, timeout: 20000 }),
      2,
      400
    );
    
    // Cache for 10 seconds (market prices change frequently)
    cache.set(cacheKey, response.data, this.CACHE_TTL.MARKET_PRICES);
    return response.data;
  }

  async getNews(symbols?: string[], limit = 5): Promise<any[]> {
    const params: Record<string, any> = { limit };
    if (symbols && symbols.length > 0) {
      params.symbols = symbols.join(',');
    }
    const response = await apiClient.get('/market/news', { params, timeout: 12000 });
    if (Array.isArray(response.data)) {
      return response.data;
    }
    if (Array.isArray(response.data?.items)) {
      return response.data.items;
    }
    return [];
  }

  // User Watchlist API
  async getUserWatchlist(includeMetadata = false): Promise<{ symbols: string[]; metadata?: Record<string, { categories: string[]; tags: string[] }> }> {
    const res = await apiClient.get('/watchlist', { params: { include_metadata: includeMetadata } });
    return res.data || { symbols: [] };
  }

  async addToWatchlist(symbol: string, categories?: string[], tags?: string[]): Promise<{ symbols: string[]; metadata: Record<string, { categories: string[]; tags: string[] }> }> {
    const res = await apiClient.post('/watchlist', { symbol, categories, tags });
    return res.data || { symbols: [], metadata: {} };
  }

  async removeFromWatchlist(symbol: string): Promise<{ symbols: string[]; metadata: Record<string, { categories: string[]; tags: string[] }> }> {
    const res = await apiClient.delete(`/watchlist/${encodeURIComponent(symbol)}`);
    return res.data || { symbols: [], metadata: {} };
  }

  async updateWatchlistMetadata(symbol: string, categories?: string[], tags?: string[]): Promise<{ symbols: string[]; metadata: Record<string, { categories: string[]; tags: string[] }> }> {
    const res = await apiClient.put(`/watchlist/${encodeURIComponent(symbol)}/metadata`, { categories, tags });
    return res.data || { symbols: [], metadata: {} };
  }

  async batchAddToWatchlist(symbols: string[], categories?: string[], tags?: string[]): Promise<{ symbols: string[]; metadata: Record<string, { categories: string[]; tags: string[] }>; results: { added: string[]; failed: Array<{ symbol: string; error: string }> } }> {
    const res = await apiClient.post('/watchlist/batch-add', { symbols, categories, tags });
    return res.data || { symbols: [], metadata: {}, results: { added: [], failed: [] } };
  }

  async batchRemoveFromWatchlist(symbols: string[]): Promise<{ symbols: string[]; metadata: Record<string, { categories: string[]; tags: string[] }>; results: { removed: string[]; failed: Array<{ symbol: string; error: string }> } }> {
    const res = await apiClient.post('/watchlist/batch-remove', { symbols });
    return res.data || { symbols: [], metadata: {}, results: { removed: [], failed: [] } };
  }

  async batchUpdateWatchlistMetadata(symbols: string[], categories?: string[], tags?: string[]): Promise<{ symbols: string[]; metadata: Record<string, { categories: string[]; tags: string[] }>; results: { updated: string[]; failed: Array<{ symbol: string; error: string }> } }> {
    const res = await apiClient.post('/watchlist/batch-metadata', { symbols, categories, tags });
    return res.data || { symbols: [], metadata: {}, results: { updated: [], failed: [] } };
  }

  // SSE stream for market prices (falls back to polling if unavailable)
  openMarketStream(symbols: string[], intervalSeconds: number = 10): EventSource | null {
    try {
      const token = localStorage.getItem('authToken');
      const base = API_BASE_URL; // already ends with /api
      const url = `${base}/market/stream?symbols=${encodeURIComponent(symbols.join(','))}&interval=${intervalSeconds}${token ? `&token=${encodeURIComponent(token)}` : ''}`;
      const es = new EventSource(url);
      return es;
    } catch (e) {
      logger.warn('SSE not available:', e);
      return null;
    }
  }

  async getAssetPrice(symbol: string, assetType?: string): Promise<any> {
    const params = assetType ? { asset_type: assetType } : {};
    const response = await apiClient.get(`/market/price/${symbol}`, { params });
    return response.data;
  }

  async getSymbolHistory(symbol: string, days: number = 7, forceRefresh = false): Promise<Array<{ date: string; close: number }>> {
    // Cache history data (very stable - historical data doesn't change)
    const cacheKey = `history:${symbol}:${days}`;
    
    if (!forceRefresh) {
      const cached = cache.get<Array<{ date: string; close: number }>>(cacheKey);
      if (cached) return cached;
    }
    
    const res = await apiClient.get(`/market/history/${encodeURIComponent(symbol)}`, { params: { days }, timeout: 12000 });
    const data = res.data?.series || [];
    
    // Cache for 5 minutes (historical data is very stable)
    cache.set(cacheKey, data, this.CACHE_TTL.SYMBOL_HISTORY);
    return data;
  }

  async getSymbolHistoryBatch(symbols: string[], days: number = 7): Promise<Record<string, Array<{ date: string; close: number }>>> {
    // Get history for multiple symbols in a single batch request
    if (!symbols || symbols.length === 0) {
      return {};
    }
    
    // Limit batch size to 10 to match backend limit
    const batch = symbols.slice(0, 10);
    const symbolsParam = batch.join(',');
    
    try {
      const res = await apiClient.get('/market/history/batch', {
        params: { symbols: symbolsParam, days },
        timeout: 15000
      });
      return res.data?.results || {};
    } catch (error: any) {
      logger.error('Batch history fetch failed, falling back to individual requests:', error);
      // Fallback to individual requests
      const results: Record<string, Array<{ date: string; close: number }>> = {};
      const promises = batch.map(async (symbol) => {
        try {
          const history = await this.getSymbolHistory(symbol, days);
          if (history.length > 0) {
            results[symbol] = history;
          }
        } catch (e) {
          logger.warn(`Failed to fetch history for ${symbol}:`, e);
        }
      });
      await Promise.all(promises);
      return results;
    }
  }

  async checkExchangeSync(limit = 50): Promise<{ summary: any; details: any }> {
    const response = await apiClient.post('/sync/exchanges/check', { limit });
    return response.data;
  }

  async searchSymbols(query: string, limit: number = 10): Promise<SymbolSearchResult[]> {
    const res = await apiClient.get(`/market/search`, { params: { q: query, limit }, timeout: 10000 });
    return res.data?.results || [];
  }

  async validateSymbol(symbol: string): Promise<{ valid: boolean; exists: boolean; symbol: string; type?: string; name?: string; error?: string }> {
    const res = await apiClient.get(`/market/symbol/validate/${symbol}`, { timeout: 10000 });
    return res.data;
  }

  async getSymbolPreview(symbol: string): Promise<{
    symbol: string;
    price: number;
    change_24h?: number;
    change_percent_24h?: number;
    type: string;
    volume_24h?: number;
    market_cap?: number;
    high_24h?: number;
    low_24h?: number;
    chart_data?: Array<{ date: string; close: number }>;
    timestamp?: string;
  }> {
    const res = await apiClient.get(`/market/symbol/preview/${symbol}`, { timeout: 15000 });
    return res.data;
  }

  async getBenchmarkHistory(symbol: string, days: number = 30): Promise<Array<{ date: string; value: number; normalized_value: number }>> {
    // Get benchmark history for comparison (S&P500, BTC, etc.)
    const cacheKey = `benchmark:${symbol}:${days}`;
    
    const cached = cache.get<Array<{ date: string; value: number; normalized_value: number }>>(cacheKey);
    if (cached) return cached;
    
    const res = await apiClient.get(`/benchmark/${symbol}`, { params: { days }, timeout: 12000 });
    const data = res.data || [];
    
    // Cache for 5 minutes
    cache.set(cacheKey, data, this.CACHE_TTL.SYMBOL_HISTORY);
    return data;
  }

  // Risk Management API
  async getRiskAnalysis(): Promise<any> {
    const response = await this.withRetry(
      () => apiClient.get('/risk/analysis', { timeout: 12000 }),
      2,
      400
    );
    return response.data;
  }

  async getStopLossSuggestion(
    symbol: string,
    entryPrice: number,
    currentPrice: number,
    assetType?: string
  ): Promise<any> {
    const params: any = {
      entry_price: entryPrice,
      current_price: currentPrice,
    };
    if (assetType) params.asset_type = assetType;
    
    const response = await apiClient.get(`/risk/stop-loss/${symbol}`, { params });
    return response.data;
  }

  async getTakeProfitSuggestion(
    symbol: string,
    entryPrice: number,
    currentPrice: number,
    assetType?: string
  ): Promise<any> {
    const params: any = {
      entry_price: entryPrice,
      current_price: currentPrice,
    };
    if (assetType) params.asset_type = assetType;
    
    const response = await apiClient.get(`/risk/take-profit/${symbol}`, { params });
    return response.data;
  }

  async calculatePositionSize(
    portfolioValue: number,
    riskPerTrade: number = 2.0,
    entryPrice: number,
    stopLossPrice: number
  ): Promise<any> {
    const params = {
      portfolio_value: portfolioValue,
      risk_per_trade: riskPerTrade,
      entry_price: entryPrice,
      stop_loss_price: stopLossPrice,
    };
    const response = await apiClient.get('/risk/position-size', { params });
    return response.data;
  }

  async getAllocationAnalytics(forceRefresh = false): Promise<AllocationAnalytics> {
    const cacheKey = CACHE_KEYS.ALLOCATION;
    
    if (!forceRefresh) {
      const cached = cache.get<AllocationAnalytics>(cacheKey);
      if (cached) return cached;
    }

    const response = await apiClient.get('/analytics/allocation');
    cache.set(cacheKey, response.data, this.CACHE_TTL.ALLOCATION);
    return response.data;
  }

  async getPortfolioHistory(days: number = 30, forceRefresh = false, signal?: AbortSignal): Promise<PortfolioHistoryPoint[]> {
    const cacheKey = CACHE_KEYS.HISTORY(days);
    
    if (!forceRefresh) {
      const cached = cache.get<PortfolioHistoryPoint[]>(cacheKey);
      if (cached) return cached;
    }

    const response = await apiClient.get(`/portfolio/history?days=${days}`, { 
      signal,
      timeout: 45000 // 45s timeout (backend may need time to process transactions, may exceed budget)
    });
    cache.set(cacheKey, response.data, this.CACHE_TTL.HISTORY);
    return response.data;
  }

  async refreshData(): Promise<void> {
    await apiClient.post('/portfolio/refresh');
    // Clear all caches after refresh
    cache.clear();
  }

  // Clear cache manually (local only - use clearCache() from settings for backend)
  clearLocalCache(): void {
    cache.clear();
  }

  async downloadTaxReportPDF(year?: number): Promise<Blob> {
    const params = year ? { year } : {};
    const response = await apiClient.get('/reports/tax-pdf', {
      params,
      responseType: 'blob',
      timeout: 120000 // 120 seconds for PDF generation
    });
    return response.data;
  }

  async downloadPortfolioSummaryPDF(): Promise<Blob> {
    const response = await apiClient.get('/reports/portfolio-pdf', {
      responseType: 'blob',
      timeout: 120000 // 120 seconds for PDF generation
    });
    return response.data;
  }

  // Risk Analytics API
  async getRiskAnalytics(days: number, confidence: number, sharpeWindow: number): Promise<any> {
    const params = { days, confidence, sharpe_window: sharpeWindow } as any;
    const response = await this.withRetry(
      () => apiClient.get('/analytics/risk', { params, timeout: 15000 }),
      2,
      400
    );
    return response.data;
  }

  // Settings methods
  async getApiKeysStatus(): Promise<any> {
    const response = await apiClient.get('/settings/api-keys');
    return response.data;
  }

  async updateApiKeys(exchange: string, keys: {
    api_key?: string;
    secret_key?: string;
    username?: string;
    password?: string;
  }): Promise<any> {
    const response = await apiClient.put(`/settings/api-keys/${exchange}`, keys);
    return response.data;
  }

  async testConnection(exchange: string): Promise<any> {
    const response = await apiClient.post(`/settings/test-connection/${exchange}`);
    return response.data;
  }

  async getAppSettings(): Promise<any> {
    const response = await apiClient.get('/settings/app');
    return response.data;
  }

  async updateAppSettings(settings: {
    cache_enabled?: boolean;
    auto_refresh_enabled?: boolean;
    refresh_interval?: number;
    theme?: string;
    currency?: string;
  }): Promise<any> {
    const response = await apiClient.put('/settings/app', settings);
    return response.data;
  }

  async clearCache(): Promise<any> {
    const response = await apiClient.post('/settings/clear-cache');
    return response.data;
  }

  // Authentication methods
  async register(username: string, email: string, password: string): Promise<any> {
    // Use separate axios instance with longer timeout for register (backend may be slow)
    const registerAxios = axios.create({
      baseURL: API_BASE_URL,
      timeout: 60000, // 60s timeout for register (backend may be slow on first request)
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    const response = await registerAxios.post('/auth/register', {
      username,
      email,
      password
    });
    return response.data;
  }

  async login(username: string, password: string): Promise<any> {
    try {
      logger.debug('Attempting login for user:', username);
      // Use separate axios instance with longer timeout for login
      // Create instance with explicit config to avoid global timeout override
      const loginAxios = axios.create({
        baseURL: API_BASE_URL,
        timeout: 60000, // 60s timeout for login (backend may be slow on first request with AI models)
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      // Ensure timeout is set in request config as well (highest priority)
      const response = await loginAxios.post('/auth/login', {
        username,
        password
      }, {
        timeout: 60000, // Explicitly set timeout in request config (overrides instance config)
      });
      logger.debug('Login successful');
      return response.data;
    } catch (error: any) {
      logger.error('Login error:', {
        message: error.message,
        code: error.code,
        response: error.response?.data,
        status: error.response?.status,
        timeout: error.config?.timeout
      });
      throw error;
    }
  }

  async getCurrentUser(): Promise<any> {
    const response = await apiClient.get('/auth/me');
    return response.data;
  }

  async logout(): Promise<void> {
    // Clear all authentication data first
    localStorage.removeItem('authToken');
    sessionStorage.removeItem('auth:invalid_token');
    
    // Clear local cache
    try {
      cache.clear();
    } catch (e) {
      // Ignore cache clear errors
    }
    
    // Clear backend cache (non-blocking)
    try {
      await this.clearCache();
    } catch (e) {
      // Ignore backend cache clear errors
    }
    
    // Try to call logout endpoint, but don't fail if it doesn't work
    // (user might already be logged out or backend might be unavailable)
    try {
      await apiClient.post('/auth/logout', {}, { timeout: 5000 });
    } catch (error) {
      // Ignore logout endpoint errors - we've already cleared local data
      logger.debug('Logout endpoint error (non-critical):', error);
    }
    
    // Dispatch logout event for other components to react
    window.dispatchEvent(new CustomEvent('auth:logout', { detail: { reason: 'user_logout' } }));
  }

  isAuthenticated(): boolean {
    return !!localStorage.getItem('authToken');
  }

  // AI/ML methods (placeholder for future features)
  async getAIPredictions(symbol: string, assetType: string = 'crypto', daysAhead: number = 7): Promise<any> {
    const response = await apiClient.get('/ai/predictions', {
      params: { symbol, asset_type: assetType, days_ahead: daysAhead }
    });
    return response.data;
  }

  async getAIRecommendations(riskTolerance: string = 'moderate', timeHorizon: string = 'long_term'): Promise<any> {
    const response = await apiClient.get('/ai/recommendations', {
      params: { risk_tolerance: riskTolerance, time_horizon: timeHorizon }
    });
    return response.data;
  }

  // Advanced Analytics
  async getPortfolioFlow(): Promise<any> {
    const cacheKey = 'analytics:flow';
    const cached = cache.get<any>(cacheKey);
    if (cached) return cached;

    const response = await this.withRetry(
      () => apiClient.get('/analytics/portfolio-flow', { timeout: 15000 }),
      2,
      400
    );
    cache.set(cacheKey, response.data, this.CACHE_TTL.ANALYTICS);
    return response.data;
  }

  async getAdvancedAnalytics(days: number = 90, benchmark: string = 'SPY'): Promise<any> {
    const cacheKey = `analytics:advanced:${days}:${benchmark}`;
    const cached = cache.get<any>(cacheKey);
    if (cached) return cached;

    const response = await this.withRetry(
      () => apiClient.get('/analytics/advanced', { 
        params: { days: Math.min(days, 90), benchmark },  // Limit days to 90
        timeout: 30000  // 30 seconds should be enough with optimizations
      }),
      1,  // Reduce retries to 1 to fail faster
      500
    );
    cache.set(cacheKey, response.data, this.CACHE_TTL.ANALYTICS);
    return response.data;
  }

  async getPortfolioProjection(days: number = 30): Promise<any> {
    const cacheKey = `analytics:projection:${days}`;
    const cached = cache.get<any>(cacheKey);
    if (cached) return cached;

    const response = await this.withRetry(
      () => apiClient.get('/analytics/portfolio-projection', { 
        params: { days },
        timeout: 60000  // Longer timeout for AI predictions
      }),
      2,
      500
    );
    cache.set(cacheKey, response.data, this.CACHE_TTL.ANALYTICS);
    return response.data;
  }

  async getEnhancedRecommendations(
    riskTolerance: string = 'moderate',
    timeHorizon: string = 'long_term',
    includeRebalancing: boolean = true,
    includeTaxLoss: boolean = true
  ): Promise<any> {
    const cacheKey = `recommendations:enhanced:${riskTolerance}:${timeHorizon}:${includeRebalancing}:${includeTaxLoss}`;
    const cached = cache.get<any>(cacheKey);
    if (cached) return cached;

    const response = await this.withRetry(
      () => apiClient.get('/ai/recommendations/enhanced', {
        params: { risk_tolerance: riskTolerance, time_horizon: timeHorizon, include_rebalancing: includeRebalancing, include_tax_loss: includeTaxLoss },
        timeout: 30000
      }),
      2,
      500
    );
    cache.set(cacheKey, response.data, this.CACHE_TTL.ANALYTICS);
    return response.data;
  }

  async getPortfolioOptimizer(
    method: 'mpt' | 'risk_parity' = 'mpt',
    riskFreeRate: number = 0.02,
    targetReturn?: number,
    maxWeight: number = 0.4
  ): Promise<any> {
    const cacheKey = `analytics:optimizer:${method}:${riskFreeRate}:${targetReturn || 'none'}:${maxWeight}`;
    const cached = cache.get<any>(cacheKey);
    if (cached) return cached;

    const response = await this.withRetry(
      () => apiClient.get('/analytics/portfolio-optimizer', {
        params: { method, risk_free_rate: riskFreeRate, target_return: targetReturn, max_weight: maxWeight },
        timeout: 30000
      }),
      2,
      500
    );
    cache.set(cacheKey, response.data, this.CACHE_TTL.ANALYTICS);
    return response.data;
  }
}

export const portfolioService = new PortfolioService();
