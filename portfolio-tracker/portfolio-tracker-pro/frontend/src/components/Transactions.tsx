import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Chip,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Avatar,
  Autocomplete,
  CircularProgress,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Pagination,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  AlertTitle,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Tooltip,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  AccountBalance,
  ShowChart,
  Refresh,
  FilterList,
  Search,
  Add,
  Edit,
  Delete,
} from '@mui/icons-material';
import { alpha } from '@mui/material/styles';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';
import { portfolioService, Transaction, UpdateTransactionRequest, CreateTransactionRequest, SymbolSearchResult, Asset as PortfolioAsset } from '../services/portfolioService';
import { logger } from '../utils/logger';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import SyncIcon from '@mui/icons-material/Sync';
import { notificationsService } from '../services/notificationsService';
import { indexTransactions } from '../services/indexingService';

const NEW_TRADES_STORAGE_KEY = 'portfolio:new-trades';
const NEW_TRADES_EVENT = 'portfolio:new-trades';
const TWENTY_FOUR_HOURS = 24 * 60 * 60 * 1000;

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

const buildAssetKey = (exchange?: string, symbol?: string) => {
  const normalizedExchange = normalizeString(exchange);
  const normalizedSymbol = normalizeString(symbol);
  if (!normalizedExchange || !normalizedSymbol) {
    return null;
  }
  return `${normalizedExchange}:${normalizedSymbol}`;
};

const buildTradeKey = (
  exchange?: string,
  symbol?: string,
  side?: string,
  amount?: unknown,
  price?: unknown,
  timestamp?: string
) => {
  const normalizedExchange = normalizeString(exchange);
  const normalizedSymbol = normalizeString(symbol);
  if (!normalizedExchange || !normalizedSymbol) {
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

const Transactions: React.FC = () => {
  const theme = useTheme();
  const isSmallScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState({
    type: '',
    symbol: '',
    exchange: '',
    search: ''
  });
  const [debouncedFilters, setDebouncedFilters] = useState(filters);
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [addOpen, setAddOpen] = useState(false);
  const [editForm, setEditForm] = useState<UpdateTransactionRequest>({});
  const [addForm, setAddForm] = useState<{
    symbol: string;
    assetName: string;
    isin: string;
    type: string;
    amount: number | '';
    price: number | '';
    date: string;
    exchange: string;
    commission: number | '';
    commission_currency: string;
  }>({
    symbol: '',
    assetName: '',
    isin: '',
    type: 'buy',
    amount: '',
    price: '',
    date: new Date().toISOString().split('T')[0],
    exchange: 'Manual',
    commission: '',
    commission_currency: 'USD'
  });
  const [selectedSymbolOption, setSelectedSymbolOption] = useState<SymbolSearchResult | null>(null);
  const [symbolInputValue, setSymbolInputValue] = useState('');
  const [symbolOptions, setSymbolOptions] = useState<SymbolSearchResult[]>([]);
  const [symbolSearchLoading, setSymbolSearchLoading] = useState(false);
  const [symbolSearchError, setSymbolSearchError] = useState<string | null>(null);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [transactionToDelete, setTransactionToDelete] = useState<Transaction | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [stats, setStats] = useState({
    totalTransactions: 0,
    totalVolume: 0,
    buyCount: 0,
    sellCount: 0,
    avgTransactionSize: 0
  });
  const [summaryWarnings, setSummaryWarnings] = useState<string[]>([]);
  const [assetIssueLookup, setAssetIssueLookup] = useState<Record<string, string[]>>({});
  const [newTradeKeyList, setNewTradeKeyList] = useState<string[]>([]);

  const newTradeKeySet = useMemo(() => new Set(newTradeKeyList), [newTradeKeyList]);

  useEffect(() => {
    const fetchOverviewData = async () => {
      try {
        const [summaryData, assetsData] = await Promise.all([
          portfolioService
            .getSummary(true)
            .catch((error) => {
              logger.warn('Transactions: failed to fetch summary warnings', error);
              return null;
            }),
          portfolioService
            .getAssets()
            .catch((error) => {
              logger.warn('Transactions: failed to fetch assets for issue lookup', error);
              return [] as PortfolioAsset[];
            }),
        ]);

        if (summaryData) {
          setSummaryWarnings(summaryData.warnings ?? []);
        }

        const typedAssets: PortfolioAsset[] = Array.isArray(assetsData) ? assetsData : [];
        if (typedAssets.length === 0) {
          setAssetIssueLookup({});
        } else {
          const issues: Record<string, string[]> = {};
          typedAssets.forEach((asset) => {
            if (!asset?.issues?.length) {
              return;
            }
            const key = buildAssetKey(asset.exchange, asset.symbol);
            if (key) {
              issues[key] = asset.issues;
            }
          });
          setAssetIssueLookup(issues);
        }
      } catch (error) {
        logger.error('Transactions: failed to load summary and asset issues', error);
      }
    };

    fetchOverviewData();
  }, []);

  const loadNewTradeMarkers = useCallback(() => {
    if (typeof window === 'undefined') {
      return;
    }

    try {
      const raw = window.localStorage.getItem(NEW_TRADES_STORAGE_KEY);
      if (!raw) {
        setNewTradeKeyList([]);
        return;
      }

      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) {
        setNewTradeKeyList([]);
        return;
      }

      const now = Date.now();
      const filtered = parsed.filter((entry) => {
        if (!entry?.key || !entry?.recordedAt) {
          return false;
        }
        const recordedAt = new Date(entry.recordedAt).getTime();
        return Number.isFinite(recordedAt) && now - recordedAt <= TWENTY_FOUR_HOURS;
      });

      setNewTradeKeyList(filtered.map((entry) => entry.key));

      if (filtered.length !== parsed.length) {
        window.localStorage.setItem(NEW_TRADES_STORAGE_KEY, JSON.stringify(filtered));
      }
    } catch (error) {
      logger.debug('Transactions: failed to load new trade markers', error);
    }
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    loadNewTradeMarkers();

    const handleStorage = (event: StorageEvent) => {
      if (event.key === NEW_TRADES_STORAGE_KEY) {
        loadNewTradeMarkers();
      }
    };

    window.addEventListener(NEW_TRADES_EVENT, loadNewTradeMarkers);
    window.addEventListener('storage', handleStorage);

    return () => {
      window.removeEventListener(NEW_TRADES_EVENT, loadNewTradeMarkers);
      window.removeEventListener('storage', handleStorage);
    };
  }, [loadNewTradeMarkers]);

  const itemsPerPage = 20;

  const selectedAssetKey = useMemo(() => {
    if (!selectedTransaction) {
      return null;
    }
    return buildAssetKey(selectedTransaction.exchange, selectedTransaction.symbol);
  }, [selectedTransaction]);

  const selectedAssetIssues = useMemo(() => {
    if (!selectedAssetKey) {
      return [] as string[];
    }
    return assetIssueLookup[selectedAssetKey] ?? [];
  }, [assetIssueLookup, selectedAssetKey]);

  const selectedTradeKey = useMemo(() => {
    if (!selectedTransaction) {
      return null;
    }
    return buildTradeKey(
      selectedTransaction.exchange,
      selectedTransaction.symbol,
      selectedTransaction.type,
      selectedTransaction.amount,
      selectedTransaction.price,
      selectedTransaction.date
    );
  }, [selectedTransaction]);

  const selectedIsNewTrade = useMemo(() => {
    if (!selectedTradeKey) {
      return false;
    }
    return newTradeKeySet.has(selectedTradeKey);
  }, [newTradeKeySet, selectedTradeKey]);

  // Debounce filters (300ms delay)
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedFilters(filters);
      setPage(1); // Reset to first page when filters change
    }, 300);

    return () => clearTimeout(timer);
  }, [filters]);

  // DISABLED: Automatic data fetching - now manual only via refresh button
  // useEffect(() => {
  //   fetchTransactions();
  // }, [page, debouncedFilters]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!addOpen) {
      return;
    }

    const query = symbolInputValue.trim();
    const isinRegex = /^[A-Za-z]{2}[A-Za-z0-9]{9}[0-9]$/;

    if (!query) {
      setSymbolOptions([]);
      setSymbolSearchLoading(false);
      return;
    }

    if (query.length < 2 && !isinRegex.test(query.toUpperCase())) {
      setSymbolOptions([]);
      setSymbolSearchLoading(false);
      return;
    }

    let active = true;
    setSymbolSearchLoading(true);

    const handler = setTimeout(async () => {
      try {
        const suggestions = await portfolioService.searchSymbols(query, 12);
        if (!active) return;
        setSymbolOptions(suggestions);
        setSymbolSearchError(null);
      } catch (err: any) {
        if (!active) return;
        logger.error('Transactions: symbol search failed', err);
        setSymbolSearchError(err?.userMessage || err?.message || 'Failed to search symbols');
        setSymbolOptions([]);
      } finally {
        if (active) {
          setSymbolSearchLoading(false);
        }
      }
    }, 250);

    return () => {
      active = false;
      clearTimeout(handler);
    };
  }, [symbolInputValue, addOpen]);

  const fetchTransactions = async () => {
    try {
      setLoading(true);
      const offset = (page - 1) * itemsPerPage;
      
      // Build filter params for backend
      const filterParams: {
        type?: string;
        symbol?: string;
        exchange?: string;
        search?: string;
      } = {};
      
      if (debouncedFilters.type) {
        filterParams.type = debouncedFilters.type;
      }
      if (debouncedFilters.symbol) {
        filterParams.symbol = debouncedFilters.symbol;
      }
      if (debouncedFilters.exchange) {
        filterParams.exchange = debouncedFilters.exchange;
      }
      if (debouncedFilters.search) {
        filterParams.search = debouncedFilters.search;
      }
      
      // Fetch with backend filtering (filters applied server-side)
      const data = await portfolioService.getTransactions(
        itemsPerPage, 
        offset, 
        page === 1,
        Object.keys(filterParams).length > 0 ? filterParams : undefined
      );
      
      setTransactions(data);
      
      // Index transactions for fast search
      if (page === 1 && !debouncedFilters.search) {
        indexTransactions(data);
      }
      
      // Calculate stats from returned data (already filtered by backend)
      const totalVolume = data.reduce((sum, tx) => sum + (tx.amount * tx.price), 0);
      const buyCount = data.filter(tx => tx.type.toLowerCase() === 'buy').length;
      const sellCount = data.filter(tx => tx.type.toLowerCase() === 'sell').length;
      
      // Note: totalPages estimation - if we got full page, assume there might be more
      // In future, backend should return total count for accurate pagination
      setStats({
        totalTransactions: data.length,
        totalVolume,
        buyCount,
        sellCount,
        avgTransactionSize: data.length > 0 ? totalVolume / data.length : 0
      });
      
      // Estimate total pages (if we got full page, there might be more)
      setTotalPages(data.length < itemsPerPage ? page : page + 1);
    } catch (error) {
      logger.error('Error fetching transactions:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatNumber = (value: number, decimals: number = 6) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(value);
  };

  const getTransactionIcon = (type: string) => {
    return type.toLowerCase() === 'buy' ? '📈' : '📉';
  };

  const getTransactionColor = (type: string) => {
    return type.toLowerCase() === 'buy' ? 'success' : 'error';
  };

  const getExchangeColor = (exchange: string) => {
    const colors: Record<string, string> = {
      'Binance': '#F0B90B',
      'Bybit': '#F7A600',
      'XTB': '#00A651',
      'Coinbase': '#0052FF',
    };
    return colors[exchange] || '#666';
  };

  const handleTransactionClick = (transaction: Transaction) => {
    setSelectedTransaction(transaction);
    setDetailsOpen(true);
  };

  const handleFilterChange = useCallback((field: string, value: string) => {
    setFilters(prev => ({ ...prev, [field]: value }));
    // Page reset is handled in debounce effect
  }, []);

  const handlePageChange = (event: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
  };

  const handleEditClick = (transaction: Transaction, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent row click
    setSelectedTransaction(transaction);
    setEditForm({
      symbol: transaction.symbol,
      type: transaction.type,
      amount: transaction.amount,
      price: transaction.price,
      date: transaction.date.split('T')[0], // Format date for input
      exchange: transaction.exchange,
      commission: transaction.commission,
      commission_currency: transaction.commission_currency,
      asset_name: transaction.asset_name || '',
      isin: transaction.isin || '',
    });
    setEditOpen(true);
    setDetailsOpen(false);
  };

  const handleSaveEdit = async () => {
    if (!selectedTransaction) return;
    
    try {
      setError(null);
      setSuccess(null);

      // Validate symbol if provided
      if (editForm.symbol !== undefined && (!editForm.symbol || !editForm.symbol.trim())) {
        setError('Symbol cannot be empty');
        setTimeout(() => setError(null), 5000);
        return;
      }

      // Validate type if provided
      if (editForm.type !== undefined && !['buy', 'sell'].includes(editForm.type)) {
        setError('Transaction type must be "buy" or "sell"');
        setTimeout(() => setError(null), 5000);
        return;
      }

      // Validate date format if provided
      if (editForm.date !== undefined) {
        if (!editForm.date) {
          setError('Date cannot be empty');
          setTimeout(() => setError(null), 5000);
          return;
        }
        
        const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
        if (!dateRegex.test(editForm.date)) {
          setError('Invalid date format. Please use YYYY-MM-DD format');
          setTimeout(() => setError(null), 5000);
          return;
        }

        // Validate date is not in the future
        const transactionDate = new Date(editForm.date);
        const today = new Date();
        today.setHours(23, 59, 59, 999);
        if (transactionDate > today) {
          setError('Transaction date cannot be in the future');
          setTimeout(() => setError(null), 5000);
          return;
        }
      }

      // Validate numeric values if provided
      if (editForm.amount !== undefined) {
        const amountValue = typeof editForm.amount === 'number' 
          ? editForm.amount 
          : parseFloat(String(editForm.amount));
        
        if (isNaN(amountValue)) {
          setError('Amount must be a valid number');
          setTimeout(() => setError(null), 5000);
          return;
        }
        
        if (amountValue <= 0) {
          setError('Amount must be greater than 0');
          setTimeout(() => setError(null), 5000);
          return;
        }

        if (amountValue > 1000000) {
          setError('Amount cannot exceed 1,000,000');
          setTimeout(() => setError(null), 5000);
          return;
        }
      }

      if (editForm.price !== undefined) {
        const priceValue = typeof editForm.price === 'number' 
          ? editForm.price 
          : parseFloat(String(editForm.price));
        
        if (isNaN(priceValue)) {
          setError('Price must be a valid number');
          setTimeout(() => setError(null), 5000);
          return;
        }
        
        if (priceValue <= 0) {
          setError('Price must be greater than 0');
          setTimeout(() => setError(null), 5000);
          return;
        }

        if (priceValue > 1000000) {
          setError('Price cannot exceed 1,000,000');
          setTimeout(() => setError(null), 5000);
          return;
        }
      }

      if (editForm.commission !== undefined) {
        const commissionValue = typeof editForm.commission === 'number' 
          ? editForm.commission 
          : parseFloat(String(editForm.commission));
        
        if (!isNaN(commissionValue) && commissionValue < 0) {
          setError('Commission cannot be negative');
          setTimeout(() => setError(null), 5000);
          return;
        }
      }

      const payload: UpdateTransactionRequest = { ...editForm };

      if (payload.symbol !== undefined && payload.symbol !== null) {
        payload.symbol = payload.symbol.trim().toUpperCase();
      }

      if (payload.asset_name !== undefined) {
        const trimmedName = typeof payload.asset_name === 'string' ? payload.asset_name.trim() : '';
        payload.asset_name = trimmedName || undefined;
      }

      if (payload.isin !== undefined) {
        const trimmedIsin = typeof payload.isin === 'string' ? payload.isin.trim().toUpperCase() : '';
        if (trimmedIsin && !/^[A-Z]{2}[A-Z0-9]{9}[0-9]$/.test(trimmedIsin)) {
          setError('ISIN must be a 12-character alphanumeric code (e.g., US0378331005)');
          setTimeout(() => setError(null), 5000);
          return;
        }
        payload.isin = trimmedIsin || undefined;
      }

      await portfolioService.updateTransaction(selectedTransaction.id, payload);
      setSuccess('Transaction updated successfully');
      setEditOpen(false);
      fetchTransactions();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err?.userMessage || err?.message || 'Failed to update transaction');
      setTimeout(() => setError(null), 5000);
    }
  };

  const handleDeleteClick = (transaction: Transaction, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent row click
    setTransactionToDelete(transaction);
    setDeleteConfirmOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!transactionToDelete) return;
    
    try {
      setError(null);
      setSuccess(null);
      await portfolioService.deleteTransaction(transactionToDelete.id);
      setSuccess('Transaction deleted successfully');
      setDeleteConfirmOpen(false);
      setTransactionToDelete(null);
      fetchTransactions();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err?.userMessage || err?.message || 'Failed to delete transaction');
      setTimeout(() => setError(null), 5000);
    }
  };

  const handleSyncTransactions = async () => {
    try {
      setSyncing(true);
      setError(null);
      setSuccess(null);

      // Show initial message that sync may take time
      setSuccess('Synchronizing transactions... This may take several minutes for multiple exchanges.');

      logger.debug('Starting transaction sync...');
      const result = await portfolioService.syncTransactions(50);
      logger.debug('Transaction sync result:', result);
      
      const importedCount = result?.summary?.imported_count || 0;
      const importedByExchange = result?.summary?.imported_by_exchange || {};
      const errors = result?.summary?.errors || [];
      const checkedExchanges = (result?.summary as any)?.checked_exchanges || [];

      logger.debug(`Sync completed: ${importedCount} imported, ${errors.length} errors, checked: ${checkedExchanges.join(', ')}`);

      if (importedCount > 0) {
        const exchangeList = Object.entries(importedByExchange)
          .map(([exchange, count]) => `${exchange}: ${count}`)
          .join(', ');
        
        setSuccess(`Successfully imported ${importedCount} new transaction${importedCount !== 1 ? 's' : ''} from ${exchangeList}`);
        
        // Add notification
        notificationsService.addNotification({
          type: 'sync',
          title: 'Transactions Synced',
          message: `Imported ${importedCount} new transaction${importedCount !== 1 ? 's' : ''} from ${Object.keys(importedByExchange).join(', ')}`,
        });

        // Trigger dashboard refresh event
        window.dispatchEvent(new CustomEvent('dashboard:refresh'));

        // Refresh transactions list
        await fetchTransactions();
      } else {
        if (checkedExchanges.length === 0) {
          setError('No exchanges configured. Please add API credentials in Settings.');
          notificationsService.addNotification({
            type: 'warning',
            title: 'No Exchanges Configured',
            message: 'Please add API credentials in Settings to sync transactions.',
          });
        } else {
          setSuccess('No new transactions found. All transactions are up to date.');
        }
      }

      if (errors.length > 0) {
        const errorMessages = errors.map((e: any) => {
          const exchange = e.exchange || 'Unknown';
          const error = e.error || 'Unknown error';
          // Check for rate limit errors
          if (error.toLowerCase().includes('rate limit') || error.toLowerCase().includes('429')) {
            return `${exchange}: Rate limit exceeded. Please try again later.`;
          }
          return `${exchange}: ${error}`;
        }).join('; ');
        
        logger.warn('Transaction sync completed with errors', errors);
        // Show warning but don't override success message if we imported something
        if (importedCount === 0) {
          setError(`Sync failed: ${errorMessages}`);
        } else {
          notificationsService.addNotification({
            type: 'warning',
            title: 'Sync Completed with Errors',
            message: `Some transactions could not be imported: ${errorMessages}`,
          });
        }
      }

      setTimeout(() => {
        setSuccess(null);
        setError(null);
      }, 5000);
    } catch (err: any) {
      logger.error('Transaction sync failed', err);
      
      // Check for specific error types
      let errorMessage = 'Failed to sync transactions';
      if (err?.response?.status === 429) {
        errorMessage = 'Rate limit exceeded. Please try again in a few minutes.';
      } else if (err?.response?.status === 401) {
        errorMessage = 'Authentication failed. Please log in again.';
      } else if (err?.code === 'ECONNABORTED' || err?.message?.includes('timeout')) {
        errorMessage = 'Synchronization is taking longer than expected. This is normal for multiple exchanges. Please wait or try again later.';
      } else if (err?.userMessage) {
        errorMessage = err.userMessage;
      } else if (err?.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
      
      // Add error notification
      notificationsService.addNotification({
        type: 'error',
        title: 'Sync Failed',
        message: errorMessage,
      });
      
      setTimeout(() => setError(null), 8000);
    } finally {
      setSyncing(false);
    }
  };

  const handleExportCSV = async () => {
    try {
      setError(null);
      const blob = await portfolioService.exportTransactions('csv');
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `transactions_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      setSuccess('Transactions exported successfully');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err?.userMessage || err?.message || 'Failed to export transactions');
      setTimeout(() => setError(null), 5000);
    }
  };

  const handleAddTransaction = () => {
    setAddForm({
      symbol: '',
      assetName: '',
      isin: '',
      type: 'buy',
      amount: '',
      price: '',
      date: new Date().toISOString().split('T')[0],
      exchange: 'Manual',
      commission: '',
      commission_currency: 'USD'
    });
    setSelectedSymbolOption(null);
    setSymbolInputValue('');
    setSymbolOptions([]);
    setSymbolSearchError(null);
    setAddOpen(true);
  };

  const handleSaveAdd = async () => {
    try {
      setError(null);
      setSuccess(null);

      // Validate required fields
      if (!addForm.symbol || !addForm.symbol.trim()) {
        setError('Symbol is required and cannot be empty');
        setTimeout(() => setError(null), 5000);
        return;
      }

      const symbolValue = addForm.symbol.trim().toUpperCase();

      if (!addForm.type || !['buy', 'sell'].includes(addForm.type)) {
        setError('Transaction type must be "buy" or "sell"');
        setTimeout(() => setError(null), 5000);
        return;
      }

      if (!addForm.date) {
        setError('Date is required');
        setTimeout(() => setError(null), 5000);
        return;
      }

      // Validate date format (YYYY-MM-DD)
      const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
      if (!dateRegex.test(addForm.date)) {
        setError('Invalid date format. Please use YYYY-MM-DD format');
        setTimeout(() => setError(null), 5000);
        return;
      }

      // Validate date is not in the future
      const transactionDate = new Date(addForm.date);
      const today = new Date();
      today.setHours(23, 59, 59, 999); // Allow today
      if (transactionDate > today) {
        setError('Transaction date cannot be in the future');
        setTimeout(() => setError(null), 5000);
        return;
      }

      if (!addForm.exchange) {
        setError('Exchange is required');
        setTimeout(() => setError(null), 5000);
        return;
      }

      const isinValue = addForm.isin ? addForm.isin.trim().toUpperCase() : '';
      if (isinValue && !/^[A-Z]{2}[A-Z0-9]{9}[0-9]$/.test(isinValue)) {
        setError('ISIN must be a 12-character alphanumeric code (e.g., US0378331005)');
        setTimeout(() => setError(null), 5000);
        return;
      }

      // Parse and validate numeric values
      const amountValue = typeof addForm.amount === 'number' 
        ? addForm.amount 
        : (addForm.amount === '' ? 0 : parseFloat(String(addForm.amount)));
      
      const priceValue = typeof addForm.price === 'number' 
        ? addForm.price 
        : (addForm.price === '' ? 0 : parseFloat(String(addForm.price)));
      
      const commissionValue = typeof addForm.commission === 'number' 
        ? addForm.commission 
        : (addForm.commission === '' ? 0 : parseFloat(String(addForm.commission)));

      // Validate amount
      if (!addForm.amount || amountValue <= 0) {
        setError('Amount must be greater than 0');
        setTimeout(() => setError(null), 5000);
        return;
      }

      if (amountValue > 1000000) {
        setError('Amount cannot exceed 1,000,000');
        setTimeout(() => setError(null), 5000);
        return;
      }

      // Validate price
      if (!addForm.price || priceValue <= 0) {
        setError('Price must be greater than 0');
        setTimeout(() => setError(null), 5000);
        return;
      }

      if (priceValue > 1000000) {
        setError('Price cannot exceed 1,000,000');
        setTimeout(() => setError(null), 5000);
        return;
      }

      // Validate commission (optional but must be non-negative)
      if (commissionValue < 0) {
        setError('Commission cannot be negative');
        setTimeout(() => setError(null), 5000);
        return;
      }

      if (isNaN(amountValue) || isNaN(priceValue) || isNaN(commissionValue)) {
        setError('Amount, price, and commission must be valid numbers');
        setTimeout(() => setError(null), 5000);
        return;
      }

      // Format date with time for API
      const dateWithTime = addForm.date ? `${addForm.date}T00:00:00` : new Date().toISOString();

      const transactionData: CreateTransactionRequest = {
        symbol: symbolValue,
        type: addForm.type,
        amount: amountValue,
        price: priceValue,
        date: dateWithTime,
        exchange: addForm.exchange,
        commission: commissionValue,
        commission_currency: addForm.commission_currency
      };

      if (addForm.assetName && addForm.assetName.trim().length > 0) {
        transactionData.asset_name = addForm.assetName.trim();
      }

      if (isinValue) {
        transactionData.isin = isinValue;
      }

      await portfolioService.createTransaction(transactionData);
      setSuccess('Transaction added successfully');
      setAddOpen(false);
      fetchTransactions();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err?.userMessage || err?.message || 'Failed to add transaction');
      setTimeout(() => setError(null), 5000);
    }
  };

  // Memoize chart data calculation
  const chartData = useMemo(() => {
    return transactions
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
      .map(tx => ({
        date: formatDate(tx.date),
        volume: tx.amount * tx.price,
        type: tx.type
      }));
  }, [transactions]);

  if (loading) {
    return (
      <Box sx={{ width: '100%', mt: 2 }}>
        <LinearProgress />
      </Box>
    );
  }

  return (
    <Box>
      {summaryWarnings.length > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <AlertTitle>Data validation warnings</AlertTitle>
          <List dense>
            {summaryWarnings.map((warning) => (
              <ListItem key={warning} sx={{ px: 0 }}>
                <ListItemIcon sx={{ minWidth: 32 }}>
                  <WarningAmberIcon color="warning" />
                </ListItemIcon>
                <ListItemText primary={warning} />
              </ListItem>
            ))}
          </List>
        </Alert>
      )}

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
            sx={{ 
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              mb: 1,
              fontSize: { xs: '1.75rem', sm: '2rem', md: '2.5rem' }
            }}
          >
            Transaction History
          </Typography>
          <Typography 
            variant="h5" 
            color="text.secondary"
            sx={{ fontSize: { xs: '0.875rem', sm: '1rem', md: '1.25rem' } }}
          >
            Complete transaction log and analytics
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1, width: { xs: '100%', sm: 'auto' }, flexWrap: 'wrap' }}>
          <Tooltip title="Refresh transaction list" arrow>
            <IconButton 
              onClick={fetchTransactions} 
              color="primary" 
              size="medium"
              aria-label="refresh transactions"
            >
              <Refresh />
            </IconButton>
          </Tooltip>
          <Tooltip title="Sync transactions from connected exchanges. This may take several minutes for multiple exchanges - the process runs in the background." arrow>
            <span>
              <Button
                variant="outlined"
                startIcon={syncing ? <CircularProgress size={16} /> : <SyncIcon />}
                onClick={handleSyncTransactions}
                disabled={syncing}
                sx={{ borderRadius: '12px' }}
              >
                {syncing ? 'Syncing... (may take a few minutes)' : 'Sync Transactions'}
              </Button>
            </span>
          </Tooltip>
          <Button
            variant="outlined"
            onClick={handleExportCSV}
            sx={{ borderRadius: '12px' }}
          >
            Export CSV
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={handleAddTransaction}
            sx={{ borderRadius: '12px', flex: { xs: 1, sm: 'none' } }}
          >
            <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>
              Add Transaction
            </Box>
            <Box component="span" sx={{ display: { xs: 'inline', sm: 'none' } }}>
              Add
            </Box>
          </Button>
        </Box>
      </Box>

      {/* Success/Error Alerts */}
      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Stats Cards */}
      <Box sx={{ 
        display: 'grid', 
        gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(5, 1fr)' },
        gap: 3, 
        mb: 4 
      }}>
        <Card sx={{ height: '100%' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <AccountBalance sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6" color="text.secondary">
                Total Transactions
              </Typography>
            </Box>
            <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
              {stats.totalTransactions}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              All time
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ height: '100%' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <ShowChart sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6" color="text.secondary">
                Total Volume
              </Typography>
            </Box>
            <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
              {formatCurrency(stats.totalVolume)}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Traded amount
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ height: '100%' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <TrendingUp sx={{ mr: 1, color: 'success.main' }} />
              <Typography variant="h6" color="text.secondary">
                Buy Orders
              </Typography>
            </Box>
            <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
              {stats.buyCount}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Purchase transactions
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ height: '100%' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <TrendingDown sx={{ mr: 1, color: 'error.main' }} />
              <Typography variant="h6" color="text.secondary">
                Sell Orders
              </Typography>
            </Box>
            <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
              {stats.sellCount}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Sale transactions
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ height: '100%' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <AccountBalance sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6" color="text.secondary">
                Avg Size
              </Typography>
            </Box>
            <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
              {formatCurrency(stats.avgTransactionSize)}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Per transaction
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <FilterList sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Filters
            </Typography>
          </Box>
          
          <Box sx={{ 
            display: 'grid', 
            gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' },
            gap: 2 
          }}>
            <TextField
              label="Search"
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              InputProps={{
                startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />
              }}
              size="small"
            />
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)' }, gap: { xs: 2, sm: 3 } }}>
              <TextField
                label="Asset name"
                value={editForm.asset_name || ''}
                onChange={(e) => setEditForm({ ...editForm, asset_name: e.target.value })}
                fullWidth
              />
              <TextField
                label="ISIN"
                value={editForm.isin || ''}
                onChange={(e) => setEditForm({ ...editForm, isin: e.target.value.toUpperCase() })}
                placeholder="US0378331005"
                fullWidth
                inputProps={{ maxLength: 12 }}
              />
            </Box>
            
            <FormControl size="small">
              <InputLabel>Type</InputLabel>
              <Select
                value={filters.type}
                label="Type"
                onChange={(e) => handleFilterChange('type', e.target.value)}
              >
                <MenuItem value="">All Types</MenuItem>
                <MenuItem value="buy">Buy</MenuItem>
                <MenuItem value="sell">Sell</MenuItem>
              </Select>
            </FormControl>
            
            <TextField
              label="Symbol"
              value={filters.symbol}
              onChange={(e) => handleFilterChange('symbol', e.target.value)}
              size="small"
            />
            
            <FormControl size="small">
              <InputLabel>Exchange</InputLabel>
              <Select
                value={filters.exchange}
                label="Exchange"
                onChange={(e) => handleFilterChange('exchange', e.target.value)}
              >
                <MenuItem value="">All Exchanges</MenuItem>
                <MenuItem value="Binance">Binance</MenuItem>
                <MenuItem value="Bybit">Bybit</MenuItem>
                <MenuItem value="XTB">XTB</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </CardContent>
      </Card>

      {/* Transaction Volume Chart */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
            Transaction Volume Over Time
          </Typography>
          <Box sx={{ height: 300, minWidth: 0, minHeight: 0 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis 
                  dataKey="date" 
                  stroke={theme.palette.text.secondary}
                  tick={{ fontSize: 12, fill: theme.palette.text.secondary }}
                />
                <YAxis 
                  stroke={theme.palette.text.secondary}
                  tick={{ fontSize: 12, fill: theme.palette.text.secondary }}
                  tickFormatter={(value) => `$${value.toLocaleString()}`}
                />
                <RechartsTooltip 
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
                  formatter={(value: number) => [formatCurrency(value), 'Volume']}
                />
                <Line 
                  type="monotone" 
                  dataKey="volume" 
                  stroke="#667eea" 
                  strokeWidth={2}
                  dot={{ fill: '#667eea', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, stroke: '#667eea', strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </Box>
        </CardContent>
      </Card>

      {/* Transactions Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
            Transaction Details
          </Typography>

          <TableContainer 
            component={Paper} 
            sx={{ 
              backgroundColor: 'transparent',
              maxHeight: { xs: '60vh', md: 'none' },
              overflowX: 'auto',
              scrollBehavior: 'smooth',
              '& .MuiTable-root': {
                minWidth: { xs: 900, sm: 'auto' }
              }
            }}
          >
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ 
                    position: { xs: 'sticky', md: 'static' }, 
                    left: { xs: 0, md: 'auto' }, 
                    zIndex: { xs: 1, md: 'auto' }, 
                    backgroundColor: { xs: 'background.paper', md: 'transparent' },
                    py: { xs: 1.5, md: 2 }
                  }}>Type</TableCell>
                  <TableCell>Symbol</TableCell>
                  <TableCell align="right" sx={{ display: { xs: 'none', md: 'table-cell' } }}>Amount</TableCell>
                  <TableCell align="right">Price</TableCell>
                  <TableCell align="right">Total</TableCell>
                  <TableCell align="right" sx={{ display: { xs: 'none', lg: 'table-cell' } }}>Commission</TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>Date</TableCell>
                  <TableCell align="center">Exchange</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {transactions.map((transaction, index) => {
                  const assetKey = buildAssetKey(transaction.exchange, transaction.symbol);
                  const issues = assetKey ? assetIssueLookup[assetKey] ?? [] : [];
                  const tradeKey = buildTradeKey(
                    transaction.exchange,
                    transaction.symbol,
                    transaction.type,
                    transaction.amount,
                    transaction.price,
                    transaction.date
                  );
                  const isNewTrade = tradeKey ? newTradeKeySet.has(tradeKey) : false;
                  const highlightColor = isNewTrade
                    ? alpha(theme.palette.primary.main, theme.palette.mode === 'dark' ? 0.28 : 0.12)
                    : issues.length > 0
                    ? alpha(theme.palette.warning.main, theme.palette.mode === 'dark' ? 0.25 : 0.12)
                    : 'transparent';
                  const highlightBorder = isNewTrade
                    ? theme.palette.primary.main
                    : issues.length > 0
                    ? theme.palette.warning.main
                    : 'transparent';

                  return (
                    <TableRow
                      key={transaction.id ?? index}
                      hover
                      onClick={() => handleTransactionClick(transaction)}
                      sx={{
                        cursor: 'pointer',
                        backgroundColor: highlightColor,
                        borderLeft: highlightBorder !== 'transparent' ? '3px solid' : undefined,
                        borderLeftColor: highlightBorder,
                        transition: 'background-color 0.2s ease, border-left-color 0.2s ease',
                      }}
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
                            {getTransactionIcon(transaction.type)}
                          </Avatar>
                          <Chip
                            label={transaction.type.toUpperCase()}
                            color={getTransactionColor(transaction.type)}
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: { xs: '0.7rem', sm: '0.75rem' } }}
                          />
                          {isNewTrade && (
                            <Chip
                              label="New"
                              color="secondary"
                              size="small"
                              sx={{
                                fontSize: { xs: '0.65rem', sm: '0.7rem' },
                                fontWeight: 600,
                              }}
                            />
                          )}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body1" sx={{ fontWeight: 600, fontSize: { xs: '0.875rem', sm: '1rem' } }}>
                          {transaction.symbol}
                        </Typography>
                        {transaction.asset_name && (
                          <Typography variant="body2" color="text.secondary">
                            {transaction.asset_name}
                          </Typography>
                        )}
                        {transaction.isin && (
                          <Typography variant="caption" color="text.secondary">
                            ISIN: {transaction.isin}
                          </Typography>
                        )}
                        {issues.length > 0 && (
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.5 }}>
                            <Tooltip title={issues.join('\n')} arrow>
                              <WarningAmberIcon color="warning" fontSize="small" />
                            </Tooltip>
                            <Typography variant="caption" color="warning.main" sx={{ fontWeight: 600 }}>
                              Data warning
                            </Typography>
                          </Box>
                        )}
                      </TableCell>
                      <TableCell align="right" sx={{ display: { xs: 'none', md: 'table-cell' } }}>
                        <Typography variant="body1" sx={{ fontFamily: 'monospace', fontSize: { xs: '0.875rem', sm: '1rem' } }}>
                          {formatNumber(transaction.amount)}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body1" sx={{ fontWeight: 600, fontSize: { xs: '0.875rem', sm: '1rem' } }}>
                          {formatCurrency(transaction.price)}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body1" sx={{ fontWeight: 600, fontSize: { xs: '0.875rem', sm: '1rem' } }}>
                          {formatCurrency(transaction.amount * transaction.price)}
                        </Typography>
                      </TableCell>
                      <TableCell align="right" sx={{ display: { xs: 'none', lg: 'table-cell' } }}>
                        <Typography variant="body1">
                          {formatCurrency(transaction.commission)} {transaction.commission_currency}
                        </Typography>
                      </TableCell>
                      <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>
                        <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                          {formatDate(transaction.date)}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Chip
                          label={transaction.exchange}
                          sx={{
                            backgroundColor: getExchangeColor(transaction.exchange),
                            color: 'white',
                            fontWeight: 600,
                            fontSize: { xs: '0.7rem', sm: '0.75rem' }
                          }}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Box sx={{ display: 'flex', gap: { xs: 1, sm: 0.5 } }}>
                          <IconButton
                            size="small"
                            color="primary"
                            sx={{
                              padding: { xs: 1, sm: '8px' },
                              minWidth: { xs: 48, sm: 'auto' },
                              minHeight: { xs: 48, sm: 'auto' }
                            }}
                            onClick={(e) => handleEditClick(transaction, e)}
                            aria-label="edit transaction"
                          >
                            <Edit fontSize="small" />
                          </IconButton>
                          <IconButton
                            size="small"
                            color="error"
                            sx={{
                              padding: { xs: 1, sm: '8px' },
                              minWidth: { xs: 48, sm: 'auto' },
                              minHeight: { xs: 48, sm: 'auto' }
                            }}
                            onClick={(e) => handleDeleteClick(transaction, e)}
                            aria-label="delete transaction"
                          >
                            <Delete fontSize="small" />
                          </IconButton>
                        </Box>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>

          {/* Pagination */}
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: { xs: 2, sm: 3 } }}>
            <Pagination
              count={totalPages}
              page={page}
              onChange={handlePageChange}
              color="primary"
              size={isSmallScreen ? 'small' : 'large'}
            />
          </Box>
        </CardContent>
      </Card>

      {/* Transaction Details Dialog */}
      <Dialog 
        open={detailsOpen} 
        onClose={() => setDetailsOpen(false)} 
        maxWidth="md" 
        fullWidth
        fullScreen={isSmallScreen}
      >
        <DialogTitle>
          Transaction Details
        </DialogTitle>
        <DialogContent>
          {selectedTransaction && (
            <Box sx={{ mt: 2 }}>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
                {selectedIsNewTrade && (
                  <Chip label="New (last sync)" color="secondary" size="small" />
                )}
                {selectedAssetIssues.length > 0 && (
                  <Tooltip title={selectedAssetIssues.join('\n')} arrow>
                    <Chip
                      icon={<WarningAmberIcon fontSize="small" />}
                      label="Data warning"
                      color="warning"
                      variant="outlined"
                      size="small"
                    />
                  </Tooltip>
                )}
              </Box>
              <Box sx={{
                display: 'grid',
                gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' },
                gap: 3
              }}>
                <Box>
                  <Typography variant="h6" sx={{ mb: 2 }}>Transaction Info</Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <Typography><strong>ID:</strong> {selectedTransaction.id}</Typography>
                    <Typography><strong>Type:</strong> {selectedTransaction.type.toUpperCase()}</Typography>
                    <Typography><strong>Symbol:</strong> {selectedTransaction.symbol}</Typography>
                    {selectedTransaction.asset_name && (
                      <Typography><strong>Asset name:</strong> {selectedTransaction.asset_name}</Typography>
                    )}
                    {selectedTransaction.isin && (
                      <Typography><strong>ISIN:</strong> {selectedTransaction.isin}</Typography>
                    )}
                    <Typography><strong>Amount:</strong> {formatNumber(selectedTransaction.amount)}</Typography>
                    <Typography><strong>Price:</strong> {formatCurrency(selectedTransaction.price)}</Typography>
                    <Typography><strong>Total:</strong> {formatCurrency(selectedTransaction.amount * selectedTransaction.price)}</Typography>
                  </Box>
                </Box>
                <Box>
                  <Typography variant="h6" sx={{ mb: 2 }}>Exchange Info</Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <Typography><strong>Exchange:</strong> {selectedTransaction.exchange}</Typography>
                    <Typography><strong>Commission:</strong> {formatCurrency(selectedTransaction.commission)} {selectedTransaction.commission_currency}</Typography>
                    <Typography><strong>Date:</strong> {formatDate(selectedTransaction.date)}</Typography>
                  </Box>
                </Box>
              </Box>
              {selectedAssetIssues.length > 0 && (
                <Alert severity="warning" sx={{ mt: 3 }}>
                  <AlertTitle>Data quality issues</AlertTitle>
                  <List dense sx={{ m: 0, pt: 0 }}>
                    {selectedAssetIssues.map((issue, issueIndex) => (
                      <ListItem key={issueIndex} disableGutters>
                        <ListItemIcon sx={{ minWidth: 32 }}>
                          <WarningAmberIcon color="warning" fontSize="small" />
                        </ListItemIcon>
                        <ListItemText primary={issue} />
                      </ListItem>
                    ))}
                  </List>
                </Alert>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)} size={isSmallScreen ? 'large' : 'medium'}>Close</Button>
          <Button 
            variant="contained" 
            startIcon={<Edit />}
            size={isSmallScreen ? 'large' : 'medium'}
            onClick={() => {
              if (selectedTransaction) {
                handleEditClick(selectedTransaction, { stopPropagation: () => {} } as any);
              }
            }}
          >
            Edit
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Transaction Dialog */}
      <Dialog 
        open={editOpen} 
        onClose={() => setEditOpen(false)} 
        maxWidth="md" 
        fullWidth
        fullScreen={isSmallScreen}
      >
        <DialogTitle>Edit Transaction</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: { xs: 2, sm: 3 } }}>
            <TextField
              label="Symbol"
              value={editForm.symbol || ''}
              onChange={(e) => setEditForm({ ...editForm, symbol: e.target.value.toUpperCase() })}
              fullWidth
            />
            
            <FormControl fullWidth>
              <InputLabel>Type</InputLabel>
              <Select
                value={editForm.type || ''}
                label="Type"
                onChange={(e) => setEditForm({ ...editForm, type: e.target.value })}
                MenuProps={{
                  PaperProps: {
                    style: { maxHeight: 300 }
                  }
                }}
              >
                <MenuItem value="buy">Buy</MenuItem>
                <MenuItem value="sell">Sell</MenuItem>
              </Select>
            </FormControl>

            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)' }, gap: { xs: 2, sm: 3 } }}>
              <TextField
                label="Amount"
                type="number"
                value={editForm.amount || ''}
                onChange={(e) => setEditForm({ ...editForm, amount: parseFloat(e.target.value) })}
                fullWidth
              />
              <TextField
                label="Price (USD)"
                type="number"
                value={editForm.price || ''}
                onChange={(e) => setEditForm({ ...editForm, price: parseFloat(e.target.value) })}
                fullWidth
              />
            </Box>

            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)' }, gap: { xs: 2, sm: 3 } }}>
              <TextField
                label="Date"
                type="date"
                value={editForm.date || ''}
                onChange={(e) => setEditForm({ ...editForm, date: e.target.value })}
                InputLabelProps={{ shrink: true }}
                fullWidth
              />
              <FormControl fullWidth>
                <InputLabel>Exchange</InputLabel>
                <Select
                  value={editForm.exchange || ''}
                  label="Exchange"
                  onChange={(e) => setEditForm({ ...editForm, exchange: e.target.value })}
                  MenuProps={{
                    PaperProps: {
                      style: { maxHeight: 300 }
                    }
                  }}
                >
                  <MenuItem value="Binance">Binance</MenuItem>
                  <MenuItem value="Bybit">Bybit</MenuItem>
                  <MenuItem value="XTB">XTB</MenuItem>
                  <MenuItem value="Manual">Manual</MenuItem>
                </Select>
              </FormControl>
            </Box>

            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)' }, gap: { xs: 2, sm: 3 } }}>
              <TextField
                label="Commission"
                type="number"
                value={editForm.commission || ''}
                onChange={(e) => setEditForm({ ...editForm, commission: parseFloat(e.target.value) })}
                fullWidth
              />
              <FormControl fullWidth>
                <InputLabel>Commission Currency</InputLabel>
                <Select
                  value={editForm.commission_currency || 'USD'}
                  label="Commission Currency"
                  onChange={(e) => setEditForm({ ...editForm, commission_currency: e.target.value })}
                  MenuProps={{
                    PaperProps: {
                      style: { maxHeight: 300 }
                    }
                  }}
                >
                  <MenuItem value="USD">USD</MenuItem>
                  <MenuItem value="EUR">EUR</MenuItem>
                  <MenuItem value="PLN">PLN</MenuItem>
                </Select>
              </FormControl>
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditOpen(false)} size={isSmallScreen ? 'large' : 'medium'}>Cancel</Button>
          <Button variant="contained" onClick={handleSaveEdit} size={isSmallScreen ? 'large' : 'medium'}>Save</Button>
        </DialogActions>
      </Dialog>

      {/* Add Transaction Dialog */}
      <Dialog 
        open={addOpen} 
        onClose={() => setAddOpen(false)} 
        maxWidth="md" 
        fullWidth
        fullScreen={isSmallScreen}
      >
        <DialogTitle>Add New Transaction</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: { xs: 2, sm: 3 } }}>
            <Autocomplete<SymbolSearchResult, false, false, true>
              freeSolo
              options={symbolOptions}
              loading={symbolSearchLoading}
              value={selectedSymbolOption}
              onChange={(event, newValue) => {
                if (!newValue) {
                  setSelectedSymbolOption(null);
                  setAddForm((prev) => ({
                    ...prev,
                    symbol: '',
                    assetName: '',
                    isin: ''
                  }));
                  setSymbolInputValue('');
                  return;
                }

                if (typeof newValue === 'string') {
                  setAddForm((prev) => ({ ...prev, symbol: newValue.toUpperCase(), assetName: '', isin: '' }));
                  setSelectedSymbolOption(null);
                  return;
                }

                setSelectedSymbolOption(newValue);
                setAddForm((prev) => ({
                  ...prev,
                  symbol: (newValue.symbol || prev.symbol).toUpperCase(),
                  assetName: newValue.name || '',
                  isin: newValue.isin || ''
                }));
                if (newValue.symbol) {
                  setSymbolInputValue(newValue.symbol);
                }
              }}
              inputValue={symbolInputValue}
              onInputChange={(event, newInputValue, reason) => {
                setSymbolInputValue(newInputValue);
                if (reason === 'input') {
                  setAddForm((prev) => ({
                    ...prev,
                    symbol: newInputValue.toUpperCase()
                  }));
                  setSelectedSymbolOption(null);
                }
                if (reason === 'clear') {
                  setAddForm((prev) => ({
                    ...prev,
                    symbol: '',
                    assetName: '',
                    isin: ''
                  }));
                  setSelectedSymbolOption(null);
                  setSymbolOptions([]);
                }
              }}
              filterOptions={(x) => x}
              getOptionLabel={(option) => (typeof option === 'string' ? option : option.symbol || '')}
              isOptionEqualToValue={(option, value) => option.symbol === value.symbol}
              renderOption={(props, option) => (
                <Box
                  component="li"
                  {...props}
                  key={`${option.symbol}-${option.isin || option.source || 'opt'}`}
                  sx={{ flexDirection: 'column', alignItems: 'flex-start' }}
                >
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {option.symbol}
                    {option.name ? ` • ${option.name}` : ''}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {(option.exchange || option.source || 'Unknown exchange') +
                      (option.currency ? ` • ${option.currency}` : '') +
                      (option.isin ? ` • ISIN: ${option.isin}` : '')}
                  </Typography>
                </Box>
              )}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Symbol / company name / ISIN *"
                  required
                  helperText={symbolSearchError || 'Type at least 2 characters or paste an ISIN to search'}
                  error={Boolean(symbolSearchError)}
                  InputProps={{
                    ...params.InputProps,
                    endAdornment: (
                      <>
                        {symbolSearchLoading ? <CircularProgress color="inherit" size={20} /> : null}
                        {params.InputProps.endAdornment}
                      </>
                    ),
                  }}
                />
              )}
            />

            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)' }, gap: { xs: 2, sm: 3 } }}>
              <TextField
                label="Asset name"
                value={addForm.assetName}
                onChange={(e) => setAddForm((prev) => ({ ...prev, assetName: e.target.value }))}
                placeholder="e.g., Apple Inc."
                fullWidth
              />
              <TextField
                label="ISIN"
                value={addForm.isin}
                onChange={(e) => setAddForm((prev) => ({ ...prev, isin: e.target.value.toUpperCase() }))}
                placeholder="US0378331005"
                fullWidth
                inputProps={{ maxLength: 12 }}
              />
            </Box>
            
            <FormControl fullWidth required>
              <InputLabel>Type</InputLabel>
              <Select
                value={addForm.type}
                label="Type"
                onChange={(e) => setAddForm({ ...addForm, type: e.target.value })}
                MenuProps={{
                  PaperProps: {
                    style: { maxHeight: 300 }
                  }
                }}
              >
                <MenuItem value="buy">Buy</MenuItem>
                <MenuItem value="sell">Sell</MenuItem>
              </Select>
            </FormControl>

            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)' }, gap: { xs: 2, sm: 3 } }}>
              <TextField
                label="Amount *"
                type="number"
                value={addForm.amount}
                onChange={(e) => setAddForm((prev) => ({ ...prev, amount: e.target.value ? parseFloat(e.target.value) : '' }))}
                fullWidth
                required
                inputProps={{ step: 'any', min: 0 }}
              />
              <TextField
                label="Price (USD) *"
                type="number"
                value={addForm.price}
                onChange={(e) => setAddForm((prev) => ({ ...prev, price: e.target.value ? parseFloat(e.target.value) : '' }))}
                fullWidth
                required
                inputProps={{ step: 'any', min: 0 }}
              />
            </Box>

            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)' }, gap: { xs: 2, sm: 3 } }}>
              <TextField
                label="Date *"
                type="date"
                value={addForm.date}
                onChange={(e) => setAddForm((prev) => ({ ...prev, date: e.target.value }))}
                InputLabelProps={{ shrink: true }}
                fullWidth
                required
              />
              <FormControl fullWidth required>
                <InputLabel>Exchange</InputLabel>
                <Select
                  value={addForm.exchange}
                  label="Exchange"
                  onChange={(e) => setAddForm((prev) => ({ ...prev, exchange: e.target.value }))}
                  MenuProps={{
                    PaperProps: {
                      style: { maxHeight: 300 }
                    }
                  }}
                >
                  <MenuItem value="Binance">Binance</MenuItem>
                  <MenuItem value="Bybit">Bybit</MenuItem>
                  <MenuItem value="XTB">XTB</MenuItem>
                <MenuItem value="Manual">Manual</MenuItem>
                </Select>
              </FormControl>
            </Box>

            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)' }, gap: { xs: 2, sm: 3 } }}>
              <TextField
                label="Commission"
                type="number"
                value={addForm.commission}
                onChange={(e) => setAddForm((prev) => ({ ...prev, commission: e.target.value ? parseFloat(e.target.value) : '' }))}
                fullWidth
                inputProps={{ step: 'any', min: 0 }}
              />
              <FormControl fullWidth>
                <InputLabel>Commission Currency</InputLabel>
                <Select
                  value={addForm.commission_currency}
                  label="Commission Currency"
                  onChange={(e) => setAddForm((prev) => ({ ...prev, commission_currency: e.target.value }))}
                  MenuProps={{
                    PaperProps: {
                      style: { maxHeight: 300 }
                    }
                  }}
                >
                  <MenuItem value="USD">USD</MenuItem>
                  <MenuItem value="EUR">EUR</MenuItem>
                  <MenuItem value="PLN">PLN</MenuItem>
                </Select>
              </FormControl>
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddOpen(false)} size={isSmallScreen ? 'large' : 'medium'}>Cancel</Button>
          <Button variant="contained" onClick={handleSaveAdd} size={isSmallScreen ? 'large' : 'medium'}>Add Transaction</Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog 
        open={deleteConfirmOpen} 
        onClose={() => setDeleteConfirmOpen(false)}
        fullScreen={isSmallScreen}
      >
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete this transaction?
            <br />
            {transactionToDelete && (
              <strong>
                {transactionToDelete.type.toUpperCase()} {transactionToDelete.amount} {transactionToDelete.symbol} @ {formatCurrency(transactionToDelete.price)}
              </strong>
            )}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirmOpen(false)} size={isSmallScreen ? 'large' : 'medium'}>Cancel</Button>
          <Button variant="contained" color="error" onClick={handleConfirmDelete} size={isSmallScreen ? 'large' : 'medium'}>
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Transactions;