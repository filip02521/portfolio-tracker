import { logger } from '../utils/logger';

/**
 * Indexing service for fast search and filtering
 * Creates in-memory indexes for transactions, assets, and other data
 */

interface IndexEntry<T> {
  id: string;
  data: T;
  searchableText: string;
}

class IndexingService {
  private indexes = new Map<string, Map<string, IndexEntry<unknown>>>();
  private searchableFields = new Map<string, string[]>();

  /**
   * Create or update an index for a collection
   */
  index<T>(
    collectionName: string,
    items: T[],
    getId: (item: T) => string,
    getSearchableText: (item: T) => string,
    searchableFields?: string[]
  ): void {
    const index = new Map<string, IndexEntry<T>>();

    items.forEach((item) => {
      const id = getId(item);
      const searchableText = getSearchableText(item);
      index.set(id, { id, data: item, searchableText });
    });

    this.indexes.set(collectionName, index as Map<string, IndexEntry<unknown>>);
    if (searchableFields) {
      this.searchableFields.set(collectionName, searchableFields);
    }

    logger.debug(`Indexed ${items.length} items in collection: ${collectionName}`);
  }

  /**
   * Search within an indexed collection
   */
  search<T>(
    collectionName: string,
    query: string,
    limit: number = 50
  ): T[] {
    const index = this.indexes.get(collectionName);
    if (!index) {
      logger.warn(`Index not found for collection: ${collectionName}`);
      return [];
    }

    if (!query.trim()) {
      return Array.from(index.values())
        .slice(0, limit)
        .map((entry) => entry.data as T);
    }

    const lowerQuery = query.toLowerCase();
    const results: IndexEntry<T>[] = [];

    const entries = Array.from(index.values());
    for (const entry of entries) {
      if (entry.searchableText.toLowerCase().includes(lowerQuery)) {
        results.push(entry as IndexEntry<T>);
        if (results.length >= limit) {
          break;
        }
      }
    }

    return results.map((entry) => entry.data);
  }

  /**
   * Get item by ID from index
   */
  getById<T>(collectionName: string, id: string): T | null {
    const index = this.indexes.get(collectionName);
    if (!index) {
      return null;
    }

    const entry = index.get(id);
    return entry ? (entry.data as T) : null;
  }

  /**
   * Update a single item in the index
   */
  update<T>(
    collectionName: string,
    item: T,
    getId: (item: T) => string,
    getSearchableText: (item: T) => string
  ): void {
    const index = this.indexes.get(collectionName);
    if (!index) {
      logger.warn(`Index not found for collection: ${collectionName}`);
      return;
    }

    const id = getId(item);
    const searchableText = getSearchableText(item);
    index.set(id, { id, data: item, searchableText });
  }

  /**
   * Remove an item from the index
   */
  remove(collectionName: string, id: string): void {
    const index = this.indexes.get(collectionName);
    if (!index) {
      return;
    }

    index.delete(id);
  }

  /**
   * Clear an index
   */
  clear(collectionName: string): void {
    this.indexes.delete(collectionName);
    this.searchableFields.delete(collectionName);
  }

  /**
   * Clear all indexes
   */
  clearAll(): void {
    this.indexes.clear();
    this.searchableFields.clear();
  }

  /**
   * Get index size
   */
  getSize(collectionName: string): number {
    const index = this.indexes.get(collectionName);
    return index ? index.size : 0;
  }
}

export const indexingService = new IndexingService();

/**
 * Helper to index transactions
 */
export function indexTransactions(transactions: Array<{
  id: string;
  symbol?: string;
  type?: string;
  exchange?: string;
  date?: string;
  amount?: number;
  price?: number;
}>) {
  indexingService.index(
    'transactions',
    transactions,
    (t) => t.id,
    (t) => {
      const parts = [
        t.symbol || '',
        t.type || '',
        t.exchange || '',
        t.date || '',
        t.amount?.toString() || '',
        t.price?.toString() || '',
      ];
      return parts.join(' ').toLowerCase();
    },
    ['symbol', 'type', 'exchange', 'date']
  );
}

/**
 * Helper to index assets
 */
export function indexAssets(assets: Array<{
  symbol?: string;
  exchange?: string;
  amount?: number;
  value_usd?: number;
}>) {
  indexingService.index(
    'assets',
    assets,
    (a) => `${a.symbol || ''}_${a.exchange || ''}`,
    (a) => {
      const parts = [
        a.symbol || '',
        a.exchange || '',
        a.amount?.toString() || '',
        a.value_usd?.toString() || '',
      ];
      return parts.join(' ').toLowerCase();
    },
    ['symbol', 'exchange']
  );
}

