import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  Typography,
  Chip,
  CircularProgress,
  Alert,
  Autocomplete,
  Card,
  CardContent,
  Divider,
  Stack,
} from '@mui/material';
import { Add, TrendingUp, TrendingDown, Close } from '@mui/icons-material';
import { portfolioService } from '../services/portfolioService';
import { TrendIndicator } from './common/TrendIndicator';
import { logger } from '../utils/logger';

interface WatchlistAddDialogProps {
  open: boolean;
  onClose: () => void;
  onAdd: (symbol: string) => Promise<void>;
  existingSymbols: string[];
}

interface SymbolPreview {
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
}

export const WatchlistAddDialog: React.FC<WatchlistAddDialogProps> = ({
  open,
  onClose,
  onAdd,
  existingSymbols,
}) => {
  const [symbol, setSymbol] = useState('');
  const [suggestions, setSuggestions] = useState<Array<{ symbol: string; name?: string; type?: string }>>([]);
  const [preview, setPreview] = useState<SymbolPreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);
  const suggestTimerRef = React.useRef<number | null>(null);

  useEffect(() => {
    if (!open) {
      setSymbol('');
      setPreview(null);
      setError(null);
      setSuggestions([]);
    }
  }, [open]);

  const handleSearch = useCallback(async (query: string) => {
    if (suggestTimerRef.current) {
      window.clearTimeout(suggestTimerRef.current);
    }
    
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }

    suggestTimerRef.current = window.setTimeout(async () => {
      try {
        const results = await portfolioService.searchSymbols(query, 10);
        setSuggestions(results || []);
      } catch (err: any) {
        logger.error('Error searching symbols:', err);
        setSuggestions([]);
      }
    }, 300);
  }, []);

  const handleSymbolChange = useCallback((value: string) => {
    // Extract symbol from autocomplete format "SYMBOL — NAME" if present
    const extractedSymbol = value.includes(' — ') 
      ? value.split(' — ')[0].trim().toUpperCase()
      : value.toUpperCase().trim();
    
    setSymbol(extractedSymbol);
    setError(null);
    setPreview(null);
    
    if (extractedSymbol.length >= 2) {
      handleSearch(extractedSymbol);
    } else {
      setSuggestions([]);
    }
  }, [handleSearch]);

  const loadPreview = useCallback(async (sym: string) => {
    if (!sym || sym.length < 1) {
      setPreview(null);
      return;
    }

    const normalizedSym = sym.toUpperCase().trim();
    
    // Check if already in watchlist
    if (existingSymbols.includes(normalizedSym)) {
      setError('Symbol already in watchlist');
      setPreview(null);
      return;
    }

    setPreviewLoading(true);
    setError(null);

    try {
      // First validate
      const validation = await portfolioService.validateSymbol(normalizedSym);
      if (!validation.valid || !validation.exists) {
        setError(validation.error || 'Symbol not found or invalid');
        setPreview(null);
        return;
      }

      // Then get preview
      const previewData = await portfolioService.getSymbolPreview(normalizedSym);
      if (previewData) {
        setPreview(previewData);
      } else {
        setError('Unable to load preview data');
      }
    } catch (err: any) {
      logger.error('Error loading preview:', err);
      setError(err?.message || 'Failed to load preview');
      setPreview(null);
    } finally {
      setPreviewLoading(false);
    }
  }, [existingSymbols]);

  const handleSymbolSelect = useCallback((selectedSymbol: string) => {
    setSymbol(selectedSymbol);
    loadPreview(selectedSymbol);
  }, [loadPreview]);

  const handleAdd = useCallback(async () => {
    if (!symbol || !preview) {
      setError('Please select a valid symbol');
      return;
    }

    if (existingSymbols.includes(symbol.toUpperCase())) {
      setError('Symbol already in watchlist');
      return;
    }

    setAdding(true);
    setError(null);

    try {
      await onAdd(symbol.toUpperCase());
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to add symbol');
    } finally {
      setAdding(false);
    }
  }, [symbol, preview, existingSymbols, onAdd, onClose]);

  const renderMiniChart = useMemo(() => {
    if (!preview?.chart_data || preview.chart_data.length < 2) {
      return (
        <Box sx={{ height: 60, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'text.secondary' }}>
          <Typography variant="caption">No chart data</Typography>
        </Box>
      );
    }

    const data = preview.chart_data;
    const width = 200;
    const height = 60;
    const min = Math.min(...data.map(d => d.close));
    const max = Math.max(...data.map(d => d.close));
    const span = max - min || 1;
    const stepX = width / (data.length - 1);
    
    const points = data.map((d, i) => {
      const x = i * stepX;
      const y = height - ((d.close - min) / span) * height;
      return `${x},${y}`;
    }).join(' ');

    const isUp = data[data.length - 1].close >= data[0].close;

    return (
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
        <defs>
          <linearGradient id={`grad-${preview.symbol}`} x1="0" y1="0" x2="1" y2="0">
            {isUp ? (
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
          stroke={`url(#grad-${preview.symbol})`}
          strokeWidth="2"
          strokeLinecap="round"
          points={points}
        />
      </svg>
    );
  }, [preview]);

  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
      maxWidth="md" 
      fullWidth
      onKeyDown={(e) => {
        if (e.key === 'Escape') {
          onClose();
        }
      }}
      PaperProps={{
        sx: {
          maxWidth: { xs: 'calc(100vw - 32px)', sm: '600px' },
          width: '100%',
          m: { xs: 2, sm: 3 }
        }
      }}
    >
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          Add to Watchlist
        </Typography>
        <Button 
          onClick={onClose} 
          size="small" 
          sx={{ 
            minWidth: { xs: 44, sm: 'auto' },
            minHeight: { xs: 44, sm: 'auto' },
            p: 1 
          }}
          aria-label="Close dialog"
        >
          <Close />
        </Button>
      </DialogTitle>
      
      <DialogContent dividers>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {/* Symbol Search */}
          <Box>
            <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
              Search Symbol
            </Typography>
            <Autocomplete
              freeSolo
              options={suggestions.map(s => `${s.symbol}${s.name ? ` — ${s.name}` : ''}`)}
              inputValue={symbol}
              onInputChange={(_, value) => handleSymbolChange(value)}
              onChange={(_, value) => {
                if (value) {
                  const selectedSymbol = value.split(' — ')[0].trim().toUpperCase();
                  handleSymbolSelect(selectedSymbol);
                }
              }}
              renderInput={(params) => (
                <TextField
                  {...params}
                  placeholder="Enter symbol (e.g., BTC, ETH, AAPL)"
                  fullWidth
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && symbol && !previewLoading) {
                      // Extract symbol if in autocomplete format
                      const symToLoad = symbol.includes(' — ') 
                        ? symbol.split(' — ')[0].trim().toUpperCase()
                        : symbol.toUpperCase().trim();
                      if (symToLoad) {
                        setSymbol(symToLoad);
                        loadPreview(symToLoad);
                      }
                    }
                  }}
                  InputProps={{
                    ...params.InputProps,
                    endAdornment: (
                      <>
                        {previewLoading && <CircularProgress size={20} />}
                        {params.InputProps.endAdornment}
                      </>
                    ),
                  }}
                />
              )}
            />
            <Button
              variant="outlined"
              size="small"
              onClick={() => {
                // Extract symbol if in autocomplete format
                const symToLoad = symbol.includes(' — ') 
                  ? symbol.split(' — ')[0].trim().toUpperCase()
                  : symbol.toUpperCase().trim();
                if (symToLoad) {
                  setSymbol(symToLoad);
                  loadPreview(symToLoad);
                }
              }}
              disabled={!symbol || previewLoading}
              sx={{ 
                mt: 1,
                minWidth: { xs: 44, sm: 'auto' },
                minHeight: { xs: 44, sm: 'auto' }
              }}
              aria-label="Load preview for symbol"
            >
              Load Preview
            </Button>
          </Box>

          {/* Error Display */}
          {error && (
            <Alert severity="error" onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {/* Preview Panel */}
          {preview && (
            <Card variant="outlined">
              <CardContent>
                <Stack spacing={2}>
                  {/* Header */}
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Box>
                      <Typography variant="h6" sx={{ fontWeight: 700 }}>
                        {preview.symbol}
                      </Typography>
                      <Chip
                        label={preview.type === 'crypto' ? 'Crypto' : 'Stock'}
                        size="small"
                        sx={{
                          mt: 0.5,
                          height: 20,
                          fontSize: '0.65rem',
                          bgcolor: preview.type === 'crypto' 
                            ? 'rgba(245, 158, 11, 0.15)' 
                            : 'rgba(59, 130, 246, 0.15)',
                          color: preview.type === 'crypto' ? 'warning.main' : 'info.main'
                        }}
                      />
                    </Box>
                    <Box sx={{ textAlign: 'right' }}>
                      <Typography variant="h5" sx={{ fontWeight: 700 }}>
                        ${preview.price?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || 'N/A'}
                      </Typography>
                      {preview.change_percent_24h !== undefined && preview.change_percent_24h !== null && (
                        <TrendIndicator
                          value={preview.change_percent_24h}
                          showIcon
                          showPercent
                        />
                      )}
                    </Box>
                  </Box>

                  <Divider />

                  {/* Metrics Grid */}
                  <Box
                    sx={{
                      display: 'grid',
                      gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(4, 1fr)' },
                      gap: 2,
                    }}
                  >
                    {preview.high_24h !== undefined && preview.high_24h !== null && (
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          24h High
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          ${preview.high_24h.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </Typography>
                      </Box>
                    )}
                    {preview.low_24h !== undefined && preview.low_24h !== null && (
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          24h Low
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          ${preview.low_24h.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </Typography>
                      </Box>
                    )}
                    {preview.volume_24h !== undefined && preview.volume_24h !== null && preview.volume_24h > 0 && (
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          24h Volume
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          ${(preview.volume_24h / 1e6).toFixed(2)}M
                        </Typography>
                      </Box>
                    )}
                    {preview.market_cap !== undefined && preview.market_cap !== null && preview.market_cap > 0 && (
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Market Cap
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          ${(preview.market_cap / 1e9).toFixed(2)}B
                        </Typography>
                      </Box>
                    )}
                  </Box>

                  {/* Mini Chart */}
                  {preview.chart_data && preview.chart_data.length > 0 && (
                    <>
                      <Divider />
                      <Box>
                        <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                          7-Day Price Trend
                        </Typography>
                        {renderMiniChart}
                      </Box>
                    </>
                  )}
                </Stack>
              </CardContent>
            </Card>
          )}
        </Box>
      </DialogContent>

      <DialogActions>
        <Button 
          onClick={onClose}
          onKeyDown={(e) => {
            if (e.key === 'Escape') {
              onClose();
            }
          }}
          aria-label="Cancel adding symbol"
        >
          Cancel
        </Button>
        <Button
          variant="contained"
          onClick={handleAdd}
          disabled={!preview || adding || existingSymbols.includes(symbol.toUpperCase())}
          startIcon={adding ? <CircularProgress size={16} /> : <Add />}
          aria-label={adding ? 'Adding symbol to watchlist' : 'Add symbol to watchlist'}
        >
          {adding ? 'Adding...' : 'Add to Watchlist'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default WatchlistAddDialog;

