import { useEffect, useRef } from 'react';
import { portfolioService } from '../services/portfolioService';
import { logger } from '../utils/logger';

type PrefetchFunction = () => Promise<unknown>;
type PrefetchKey = string;

interface PrefetchOptions {
  delay?: number; // Delay before prefetching (ms)
  enabled?: boolean;
}

const prefetchCache = new Map<PrefetchKey, Promise<unknown>>();
const prefetchTimers = new Map<PrefetchKey, NodeJS.Timeout>();

/**
 * Hook for prefetching data on hover or focus
 * Prevents duplicate prefetch requests and cancels prefetch if user leaves before delay
 */
export function usePrefetch(
  prefetchFn: PrefetchFunction,
  key: PrefetchKey,
  options: PrefetchOptions = {}
) {
  const { delay = 200, enabled = true } = options;
  const isPrefetchingRef = useRef(false);

  const prefetch = () => {
    if (!enabled || isPrefetchingRef.current) {
      return;
    }

    // Cancel any existing timer
    const existingTimer = prefetchTimers.get(key);
    if (existingTimer) {
      clearTimeout(existingTimer);
    }

    // Check if already prefetched
    if (prefetchCache.has(key)) {
      return;
    }

    // Set timer for delayed prefetch
    const timer = setTimeout(() => {
      isPrefetchingRef.current = true;
      const promise = prefetchFn()
        .then((data) => {
          prefetchCache.set(key, Promise.resolve(data));
          return data;
        })
        .catch((error) => {
          logger.debug(`Prefetch failed for ${key}:`, error);
          prefetchCache.delete(key);
          throw error;
        })
        .finally(() => {
          isPrefetchingRef.current = false;
        });

      prefetchCache.set(key, promise);
      prefetchTimers.delete(key);
    }, delay);

    prefetchTimers.set(key, timer);
  };

  const cancel = () => {
    const timer = prefetchTimers.get(key);
    if (timer) {
      clearTimeout(timer);
      prefetchTimers.delete(key);
    }
  };

  useEffect(() => {
    return () => {
      cancel();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  return { prefetch, cancel };
}

/**
 * Prefetch portfolio data for a specific route
 */
export function useRoutePrefetch(route: string, options: PrefetchOptions = {}) {
  const prefetchMap: Record<string, PrefetchFunction> = {
    '/portfolio': () => portfolioService.getAssets(false),
    '/analytics': () => portfolioService.getPerformanceAnalytics(),
    '/transactions': () => portfolioService.getTransactions(50, 0, false),
    '/price-alerts': () => portfolioService.getPriceAlerts(),
    '/risk-management': () => portfolioService.getRiskAlerts(),
    // Disabled automatic prefetch for /goals - it's a heavy operation that causes timeouts
    // '/goals': () => portfolioService.getGoals(),
    '/market-watch': () => portfolioService.getWatchlistPrices([]),
  };

  // Always call usePrefetch hook (React rules), but use no-op function if route not found
  const prefetchFn = prefetchMap[route] || (() => Promise.resolve(null));
  
  return usePrefetch(prefetchFn, `route:${route}`, options);
}

/**
 * Prefetch asset details when hovering over an asset symbol
 */
export function useAssetPrefetch(symbol: string | null, options: PrefetchOptions = {}) {
  return usePrefetch(
    async () => {
      if (!symbol) {
        return null;
      }
      // Prefetch asset history and preview
      await Promise.allSettled([
        portfolioService.getSymbolHistory(symbol, 30),
        portfolioService.getSymbolPreview(symbol).catch(() => null),
      ]);
      return symbol;
    },
    `asset:${symbol}`,
    { ...options, delay: options.delay ?? 300 }
  );
}

/**
 * Clear prefetch cache (useful after mutations)
 */
export function clearPrefetchCache(pattern?: string) {
  if (pattern) {
    const keysToDelete: string[] = [];
    prefetchCache.forEach((_, key) => {
      if (key.includes(pattern)) {
        keysToDelete.push(key);
      }
    });
    keysToDelete.forEach((key) => prefetchCache.delete(key));
  } else {
    prefetchCache.clear();
  }
}

