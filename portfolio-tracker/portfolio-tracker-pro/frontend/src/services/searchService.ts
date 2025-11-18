import { portfolioService, Asset as PortfolioAsset } from './portfolioService';
import { logger } from '../utils/logger';

export interface SearchResult {
  id: string;
  type: 'asset' | 'transaction' | 'page' | 'action';
  title: string;
  subtitle?: string;
  icon?: string;
  action: () => void;
  score: number; // Relevance score (0-100)
}

interface SearchOptions {
  limit?: number;
  minScore?: number;
}

/**
 * Search service for finding assets, transactions, pages, and actions
 */
class SearchService {
  private assetCache: PortfolioAsset[] = [];
  private cacheTimestamp: number = 0;
  private readonly CACHE_TTL = 30000; // 30 seconds

  /**
   * Get cached assets or fetch fresh ones
   */
  private async getAssets(): Promise<PortfolioAsset[]> {
    const now = Date.now();
    if (this.assetCache.length > 0 && now - this.cacheTimestamp < this.CACHE_TTL) {
      return this.assetCache;
    }

    try {
      const assets = await portfolioService.getAssets(false);
      this.assetCache = assets;
      this.cacheTimestamp = now;
      return assets;
    } catch (error) {
      logger.error('Failed to fetch assets for search', error);
      return this.assetCache; // Return stale cache on error
    }
  }

  /**
   * Calculate relevance score for a search query
   */
  private calculateScore(query: string, text: string, type: SearchResult['type']): number {
    const lowerQuery = query.toLowerCase().trim();
    const lowerText = text.toLowerCase();

    // Exact match gets highest score
    if (lowerText === lowerQuery) {
      return 100;
    }

    // Starts with query
    if (lowerText.startsWith(lowerQuery)) {
      return 90;
    }

    // Contains query
    if (lowerText.includes(lowerQuery)) {
      // Calculate position-based score (earlier matches score higher)
      const position = lowerText.indexOf(lowerQuery);
      const positionScore = Math.max(0, 80 - (position / lowerText.length) * 20);
      
      // Type bonus
      const typeBonus = type === 'asset' ? 10 : type === 'action' ? 5 : 0;
      
      return positionScore + typeBonus;
    }

    // Fuzzy match (check if all query characters appear in order)
    let queryIndex = 0;
    for (let i = 0; i < lowerText.length && queryIndex < lowerQuery.length; i++) {
      if (lowerText[i] === lowerQuery[queryIndex]) {
        queryIndex++;
      }
    }
    
    if (queryIndex === lowerQuery.length) {
      return 50; // Partial fuzzy match
    }

    return 0;
  }

  /**
   * Search assets
   */
  async searchAssets(query: string, options: SearchOptions = {}): Promise<SearchResult[]> {
    const { limit = 10, minScore = 20 } = options;
    const assets = await this.getAssets();
    const results: SearchResult[] = [];

    for (const asset of assets) {
      const symbol = asset.symbol?.toUpperCase() || '';
      const exchange = asset.exchange?.toUpperCase() || '';
      const searchText = `${symbol} ${exchange}`.trim();
      
      const score = Math.max(
        this.calculateScore(query, symbol, 'asset'),
        this.calculateScore(query, exchange, 'asset'),
        this.calculateScore(query, searchText, 'asset')
      );

      if (score >= minScore) {
        results.push({
          id: `asset-${asset.symbol}-${asset.exchange}`,
          type: 'asset',
          title: symbol,
          subtitle: exchange ? `On ${exchange}` : undefined,
          icon: '💰',
          action: () => {
            // Navigate to asset details or focus on asset in dashboard
            logger.debug('Navigate to asset', { symbol, exchange });
            // This will be handled by the Command Palette component
          },
          score,
        });
      }
    }

    // Sort by score descending
    results.sort((a, b) => b.score - a.score);
    return results.slice(0, limit);
  }

  /**
   * Search pages (routes)
   */
  searchPages(query: string, options: SearchOptions = {}): SearchResult[] {
    const { limit = 10, minScore = 20 } = options;
    const pages: Array<{ path: string; title: string; description: string }> = [
      { path: '/', title: 'Dashboard', description: 'Main portfolio dashboard' },
      { path: '/portfolio', title: 'Portfolio', description: 'Portfolio overview and details' },
      { path: '/transactions', title: 'Transactions', description: 'View and manage transactions' },
      { path: '/analytics', title: 'Analytics', description: 'Performance analytics and insights' },
      { path: '/price-alerts', title: 'Price Alerts', description: 'Manage price alerts' },
      { path: '/risk-management', title: 'Risk Management', description: 'Risk analysis and management' },
      { path: '/goals', title: 'Goals', description: 'Investment goals and targets' },
      { path: '/settings', title: 'Settings', description: 'Application settings' },
      { path: '/ai-insights', title: 'AI Insights', description: 'AI-powered portfolio insights' },
    ];

    const results: SearchResult[] = [];

    for (const page of pages) {
      const searchText = `${page.title} ${page.description}`.toLowerCase();
      const score = this.calculateScore(query, searchText, 'page');

      if (score >= minScore) {
        results.push({
          id: `page-${page.path}`,
          type: 'page',
          title: page.title,
          subtitle: page.description,
          icon: '📄',
          action: () => {
            window.location.href = page.path;
          },
          score,
        });
      }
    }

    results.sort((a, b) => b.score - a.score);
    return results.slice(0, limit);
  }

  /**
   * Search actions (quick actions)
   */
  searchActions(query: string, options: SearchOptions = {}): SearchResult[] {
    const { limit = 10, minScore = 20 } = options;
    const actions: Array<{ id: string; title: string; description: string; icon: string }> = [
      { id: 'add-transaction', title: 'Add Transaction', description: 'Record a new trade or transaction', icon: '➕' },
      { id: 'set-alert', title: 'Set Price Alert', description: 'Create a price alert for an asset', icon: '🔔' },
      { id: 'view-analytics', title: 'View Analytics', description: 'Open analytics dashboard', icon: '📊' },
      { id: 'export-pdf', title: 'Export PDF', description: 'Download portfolio report as PDF', icon: '📥' },
      { id: 'refresh', title: 'Refresh Data', description: 'Refresh portfolio data', icon: '🔄' },
      { id: 'sync-trades', title: 'Sync Trades', description: 'Sync trades from exchanges', icon: '🔄' },
    ];

    const results: SearchResult[] = [];

    for (const action of actions) {
      const searchText = `${action.title} ${action.description}`.toLowerCase();
      const score = this.calculateScore(query, searchText, 'action');

      if (score >= minScore) {
        results.push({
          id: `action-${action.id}`,
          type: 'action',
          title: action.title,
          subtitle: action.description,
          icon: action.icon,
          action: () => {
            logger.debug('Execute action', { actionId: action.id });
            // Actions will be handled by Command Palette component
          },
          score,
        });
      }
    }

    results.sort((a, b) => b.score - a.score);
    return results.slice(0, limit);
  }

  /**
   * Perform a global search across all categories
   */
  async search(query: string, options: SearchOptions = {}): Promise<SearchResult[]> {
    if (!query || query.trim().length === 0) {
      return [];
    }

    const { limit = 20 } = options;
    const allResults: SearchResult[] = [];

    // Search all categories in parallel
    const [assets, pages, actions] = await Promise.all([
      this.searchAssets(query, { ...options, limit: 10 }),
      Promise.resolve(this.searchPages(query, { ...options, limit: 5 })),
      Promise.resolve(this.searchActions(query, { ...options, limit: 5 })),
    ]);

    allResults.push(...assets, ...pages, ...actions);

    // Sort by score and type priority (actions > assets > pages)
    const typePriority: Record<SearchResult['type'], number> = {
      action: 3,
      asset: 2,
      page: 1,
      transaction: 2,
    };

    allResults.sort((a, b) => {
      const priorityDiff = typePriority[b.type] - typePriority[a.type];
      if (priorityDiff !== 0) {
        return priorityDiff;
      }
      return b.score - a.score;
    });

    return allResults.slice(0, limit);
  }

  /**
   * Clear search cache
   */
  clearCache(): void {
    this.assetCache = [];
    this.cacheTimestamp = 0;
  }
}

export const searchService = new SearchService();

