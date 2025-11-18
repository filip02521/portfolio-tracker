import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Box,
  Drawer,
  Typography,
  IconButton,
  Chip,
  Divider,
  Button,
  LinearProgress,
  CircularProgress,
  Card,
  CardContent,
  useTheme,
  Stack,
  Alert,
  AlertTitle,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ButtonGroup,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Skeleton,
  Collapse,
  Tooltip,
} from '@mui/material';
import { Close, NotificationsNone, ShowChart, ErrorOutline, Insights } from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip as RechartsTooltip, Area } from 'recharts';
import { portfolioService } from '../../services/portfolioService';
import type { Asset as PortfolioServiceAsset, DueDiligenceSummary } from '../../services/portfolioService';
import { logger } from '../../utils/logger';
import { TrendIndicator } from '../common/TrendIndicator';
import { Toast, useToast } from '../common/Toast';

type Asset = PortfolioServiceAsset;

interface AssetDetailsDrawerProps {
  open: boolean;
  onClose: () => void;
  asset: Asset | null;
}

export const AssetDetailsDrawer: React.FC<AssetDetailsDrawerProps> = ({ open, onClose, asset }) => {
  const theme = useTheme();
  const [historyRange, setHistoryRange] = useState<7 | 30 | 90>(7);
  const [historyData, setHistoryData] = useState<Array<{ date: string; price: number }>>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [chartDialogOpen, setChartDialogOpen] = useState(false);
  const [chartHistory, setChartHistory] = useState<Array<{ date: string; price: number }>>([]);
  const [chartLoading, setChartLoading] = useState(false);
  const [priceAlertOpen, setPriceAlertOpen] = useState(false);
  const [alertPrice, setAlertPrice] = useState<number | ''>('');
  const [alertCondition, setAlertCondition] = useState<'above' | 'below'>('above');
  const [alertSubmitting, setAlertSubmitting] = useState(false);
  const [roiOpen, setRoiOpen] = useState(false);
  const [roiLoading, setRoiLoading] = useState(false);
  const [roiStats, setRoiStats] = useState<{
    invested?: number;
    currentValue?: number;
    realized?: number;
    unrealized?: number;
    roiPercent?: number;
  } | null>(null);
  const [dueDiligence, setDueDiligence] = useState<DueDiligenceSummary | null>(null);
  const [dueDiligenceLoading, setDueDiligenceLoading] = useState(false);
  const [dueDiligenceError, setDueDiligenceError] = useState<string | null>(null);
  const { toast, showToast, hideToast } = useToast();

  const fetchHistory = useCallback(async (days: number) => {
    if (!asset) return;

    setLoadingHistory(true);
    try {
      const data = await portfolioService.getSymbolHistory(asset.symbol, days);
      if (data && data.length > 0) {
        setHistoryData(
          data.map((point) => ({
            date: point.date.split('T')[0],
            price: point.close,
          }))
        );
      } else {
        setHistoryData([]);
      }
    } catch (error) {
      logger.error('Error fetching asset history:', error);
      setHistoryData([]);
    } finally {
      setLoadingHistory(false);
    }
  }, [asset]);

  const loadChartHistory = useCallback(async () => {
    if (!asset) return;
    setChartLoading(true);
    try {
      const data = await portfolioService.getSymbolHistory(asset.symbol, 180);
      setChartHistory(
        data.map((point) => ({
          date: point.date.split('T')[0],
          price: point.close,
        }))
      );
    } catch (error) {
      logger.error('Error loading extended chart history:', error);
      showToast('Failed to load extended price history', 'error');
      setChartHistory([]);
    } finally {
      setChartLoading(false);
    }
  }, [asset, showToast]);

  const computeRoiStats = useCallback(() => {
    if (!asset) return;
    setRoiLoading(true);
    try {
      const invested =
        typeof asset.average_price === 'number' && Number.isFinite(asset.average_price)
          ? asset.average_price * asset.amount
          : undefined;
      const currentValue = asset.value_usd;
      const realized = asset.realized_pnl ?? undefined;
      const unrealized =
        typeof asset.pnl === 'number' && Number.isFinite(asset.pnl) ? asset.pnl : undefined;
      const roiPercent =
        typeof asset.pnl_percent === 'number' && Number.isFinite(asset.pnl_percent)
          ? asset.pnl_percent
          : undefined;
      setRoiStats({
        invested,
        currentValue,
        realized,
        unrealized,
        roiPercent,
      });
    } finally {
      setRoiLoading(false);
    }
  }, [asset]);

  const fetchDueDiligence = useCallback(
    async (refresh = false) => {
      if (!asset) return;
      setDueDiligenceLoading(true);
      setDueDiligenceError(null);
      try {
        const result = await portfolioService.getDueDiligence(asset.symbol, refresh);
        setDueDiligence(result);
      } catch (error) {
        logger.error('Error fetching due diligence:', error);
        setDueDiligence(null);
        setDueDiligenceError('Unable to load long-term due diligence analysis.');
      } finally {
        setDueDiligenceLoading(false);
      }
    },
    [asset]
  );

  useEffect(() => {
    setHistoryData([]);
    if (asset && open) {
      fetchHistory(historyRange);
    }
  }, [asset, open, historyRange, fetchHistory]);

  useEffect(() => {
    if (asset && open) {
      fetchDueDiligence(false);
    } else {
      setDueDiligence(null);
      setDueDiligenceError(null);
    }
  }, [asset, open, fetchDueDiligence]);

  const getAssetIcon = (symbol: string) => {
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

  const formatCurrency = (amount?: number, currency: string = 'USD') => {
    if (typeof amount !== 'number' || !Number.isFinite(amount)) {
      return '—';
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
    }).format(amount);
  };

  const formatNumber = (value?: number, fractionDigits = 2) => {
    if (typeof value !== 'number' || !Number.isFinite(value)) {
      return '—';
    }
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: fractionDigits,
      maximumFractionDigits: fractionDigits,
    }).format(value);
  };

  const normalizeDueScore = (score?: number | null) => {
    if (typeof score !== 'number' || !Number.isFinite(score)) {
      return null;
    }
    return Math.max(0, Math.min(score, 100));
  };

  const getDueScoreColor = (score?: number | null) => {
    const normalized = normalizeDueScore(score);
    if (normalized === null) {
      return 'text.secondary';
    }
    if (normalized >= 75) {
      return 'success.main';
    }
    if (normalized >= 55) {
      return 'warning.main';
    }
    return 'error.main';
  };

  const formatPillarName = (name: string) =>
    name
      .split(/[_\s]+/)
      .filter(Boolean)
      .map((chunk) => chunk.charAt(0).toUpperCase() + chunk.slice(1))
      .join(' ');

  const formatPercentage = (value?: number) =>
    typeof value === 'number' && Number.isFinite(value)
      ? `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
      : '—';

  const currentPrice = asset?.current_price ?? asset?.exchange_price ?? null;
  const averagePrice = asset?.average_price ?? null;
  const costBasis =
    averagePrice !== null && asset
      ? averagePrice * asset.amount
      : null;
  const realizedPnl = asset?.realized_pnl ?? null;
  const pnlValue = typeof asset?.pnl === 'number' && Number.isFinite(asset.pnl) ? asset.pnl : null;
  const pnlPercent = typeof asset?.pnl_percent === 'number' && Number.isFinite(asset.pnl_percent)
    ? asset.pnl_percent
    : null;
  const priceSource = asset?.price_source ?? null;
  const priceSourceLabel = useMemo(() => {
    if (!priceSource) return null;
    const source = priceSource.toLowerCase();
    if (source === 'exchange') return 'Exchange price';
    if (source === 'reference') return 'Reference market price';
    return priceSource;
  }, [priceSource]);

  const historyRangeOptions: Array<{ label: string; value: 7 | 30 | 90 }> = [
    { label: '7D', value: 7 },
    { label: '30D', value: 30 },
    { label: '90D', value: 90 },
  ];

  const exchangeList = useMemo(() => {
    if (!asset) {
      return [] as string[];
    }
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
  }, [asset]);

  const exchangeTooltipContent = useMemo(() => {
    if (!asset) {
      return 'No exchange data';
    }
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
    if (exchangeList.length > 0) {
      return exchangeList.join(', ');
    }
    return 'No exchange data';
  }, [asset, exchangeList]);

  if (!asset) return null;

  const hasMultipleExchanges = exchangeList.length > 1;
  const primaryExchange = exchangeList[0] || asset.exchange || '—';
  const normalizedPrimary = primaryExchange.toLowerCase();
  const isAggregateExchange =
    hasMultipleExchanges || normalizedPrimary === 'multi' || normalizedPrimary === 'multiple';
  const exchangeChipLabel = hasMultipleExchanges
    ? `${exchangeList.length} exchanges`
    : normalizedPrimary === 'multi'
    ? 'Multi'
    : primaryExchange;
  const exchangeChipStyles = isAggregateExchange
    ? {
        borderColor: theme.palette.divider,
        color: theme.palette.text.primary,
        backgroundColor: 'rgba(148, 163, 184, 0.18)',
      }
    : {
        backgroundColor: getExchangeColor(primaryExchange),
        color: '#fff',
      };

  const pnlIsPositive = pnlValue !== null && pnlValue >= 0;
  const pnlBorderColor = pnlValue === null ? theme.palette.divider : (pnlIsPositive ? theme.palette.success.main : theme.palette.error.main);
  const exchangeValueUsd = asset?.exchange_value_usd ?? null;

  return (
    <Drawer 
      anchor="right" 
      open={open} 
      onClose={onClose} 
      PaperProps={{ 
        sx: { 
          width: { xs: '100%', sm: 420 },
          backgroundColor: 'background.default'
        } 
      }}
    >
      <Box sx={{ p: 3 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="h5" sx={{ fontWeight: 700, fontSize: '1.5rem' }}>
              {getAssetIcon(asset.symbol)}
            </Typography>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              {asset.symbol}
            </Typography>
            <Tooltip title={exchangeTooltipContent} arrow placement="top">
              <Chip
                label={exchangeChipLabel}
                size="small"
                sx={{
                  borderRadius: '12px',
                  fontWeight: 600,
                  ...exchangeChipStyles,
                }}
                variant={isAggregateExchange ? 'outlined' : 'filled'}
              />
            </Tooltip>
            {priceSourceLabel && (
              <Chip
                label={priceSourceLabel}
                size="small"
                variant="outlined"
                sx={{ fontWeight: 600 }}
              />
            )}
          </Box>
          <IconButton onClick={onClose} size="small">
            <Close />
          </IconButton>
        </Box>

        <Divider sx={{ mb: 3 }} />

        {/* Key Metrics */}
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, minmax(0, 1fr))' },
            gap: 2,
            mb: 3,
          }}
        >
          <Card variant="outlined" sx={{ bgcolor: 'background.paper' }}>
            <CardContent>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                Current Value
              </Typography>
              <Typography variant="h6" sx={{ fontWeight: 700 }}>
                {formatCurrency(asset.value_usd)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {formatCurrency(asset.value_pln, 'PLN')}
              </Typography>
            </CardContent>
          </Card>
          <Card variant="outlined" sx={{ bgcolor: 'background.paper' }}>
            <CardContent>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                Amount
              </Typography>
              <Typography variant="h6" sx={{ fontWeight: 700 }}>
                {formatNumber(asset.amount, 6)}
              </Typography>
            </CardContent>
          </Card>
          <Card 
            variant="outlined" 
            sx={{ 
              bgcolor: 'background.paper',
              border: `2px solid ${pnlBorderColor}`,
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                    Total P&L
                  </Typography>
                  <Typography 
                    variant="h6" 
                    sx={{ 
                      fontWeight: 700,
                      color: pnlValue === null ? 'text.primary' : (pnlIsPositive ? 'success.main' : 'error.main')
                    }}
                  >
                    {formatCurrency(pnlValue ?? undefined)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    ROI {formatPercentage(pnlPercent ?? undefined)}
                  </Typography>
                </Box>
                <TrendIndicator 
                  value={pnlPercent ?? 0}
                  showIcon 
                  showPercent 
                  size="medium"
                />
              </Box>
            </CardContent>
          </Card>
          <Card variant="outlined" sx={{ bgcolor: 'background.paper' }}>
            <CardContent>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                Exchange Value
              </Typography>
              <Typography variant="h6" sx={{ fontWeight: 700 }}>
                {formatCurrency(exchangeValueUsd ?? undefined)}
              </Typography>
            </CardContent>
          </Card>
        </Box>

        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, minmax(0, 1fr))' },
            gap: 2,
            mb: 3,
          }}
        >
          {currentPrice !== null && (
            <Card variant="outlined" sx={{ bgcolor: 'background.paper' }}>
              <CardContent>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                  Current Price
                </Typography>
                <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                  {formatCurrency(currentPrice)}
                </Typography>
              </CardContent>
            </Card>
          )}
          {averagePrice !== null && (
            <Card variant="outlined" sx={{ bgcolor: 'background.paper' }}>
              <CardContent>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                  Avg. Cost
                </Typography>
                <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                  {formatCurrency(averagePrice)}
                </Typography>
              </CardContent>
            </Card>
          )}
          {costBasis !== null && (
            <Card variant="outlined" sx={{ bgcolor: 'background.paper' }}>
              <CardContent>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                  Cost Basis
                </Typography>
                <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                  {formatCurrency(costBasis)}
                </Typography>
              </CardContent>
            </Card>
          )}
          {realizedPnl !== null && (
            <Card variant="outlined" sx={{ bgcolor: 'background.paper' }}>
              <CardContent>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                  Realized P&L
                </Typography>
                <Typography
                  variant="subtitle1"
                  sx={{ fontWeight: 700, color: realizedPnl >= 0 ? 'success.main' : 'error.main' }}
                >
                  {formatCurrency(realizedPnl)}
                </Typography>
              </CardContent>
            </Card>
          )}
        </Box>

        {asset.issues && asset.issues.length > 0 && (
          <Alert severity="warning" sx={{ mb: 3 }}>
            <AlertTitle>Data quality warnings</AlertTitle>
            <List dense disablePadding>
              {asset.issues.map((issue, idx) => (
                <ListItem key={idx} disableGutters sx={{ alignItems: 'flex-start' }}>
                  <ListItemIcon sx={{ minWidth: 28, color: 'warning.main', mt: 0.25 }}>
                    <ErrorOutline fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primaryTypographyProps={{ variant: 'body2' }}
                    primary={issue}
                  />
                </ListItem>
              ))}
            </List>
          </Alert>
        )}

        <Card variant="outlined" sx={{ mb: 3, bgcolor: 'background.paper' }}>
          <CardContent>
            <Stack spacing={1.5}>
              <Stack direction="row" alignItems="center" justifyContent="space-between">
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Due Diligence 360°
                </Typography>
                <Stack direction="row" alignItems="center" spacing={1}>
                  {dueDiligence?.verdict && (
                    <Chip
                      size="small"
                      sx={{ textTransform: 'uppercase', fontWeight: 600 }}
                      label={dueDiligence.verdict.replace(/_/g, ' ')}
                    />
                  )}
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={() => fetchDueDiligence(true)}
                    disabled={dueDiligenceLoading}
                  >
                    Refresh
                  </Button>
                </Stack>
              </Stack>

              {dueDiligenceLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
                  <CircularProgress size={24} />
                </Box>
              ) : dueDiligenceError ? (
                <Alert severity="warning">{dueDiligenceError}</Alert>
              ) : dueDiligence ? (
                <Stack spacing={2}>
                  <Stack direction="row" spacing={3} alignItems="center">
                    <Box
                      sx={{
                        position: 'relative',
                        width: 84,
                        height: 84,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <CircularProgress
                        variant="determinate"
                        value={normalizeDueScore(dueDiligence.score) ?? 0}
                        size={84}
                        thickness={5}
                        sx={{ color: getDueScoreColor(dueDiligence.score) }}
                      />
                      <Box
                        sx={{
                          position: 'absolute',
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                        }}
                      >
                        <Typography variant="h6" sx={{ fontWeight: 700, color: getDueScoreColor(dueDiligence.score) }}>
                          {normalizeDueScore(dueDiligence.score)?.toFixed(1) ?? '—'}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Score
                        </Typography>
                      </Box>
                    </Box>
                    <Stack spacing={0.5}>
                      <Typography variant="body2" color="text.secondary">
                        Confidence {formatPercentage(dueDiligence.confidence ?? undefined)}
                      </Typography>
                      {dueDiligence.cachedAt && (
                        <Typography variant="caption" color="text.secondary">
                          Cached at {new Date(dueDiligence.cachedAt).toLocaleString()}
                        </Typography>
                      )}
                      {dueDiligence.validUntil && (
                        <Typography variant="caption" color="text.secondary">
                          Valid until {new Date(dueDiligence.validUntil).toLocaleString()}
                        </Typography>
                      )}
                    </Stack>
                  </Stack>

                  {normalizeDueScore(dueDiligence.score) !== null && normalizeDueScore(dueDiligence.score)! < 45 && (
                    <Alert severity="warning">
                      Long-term fundamentals appear weak. Review position sizing and risk controls.
                    </Alert>
                  )}
                  {normalizeDueScore(dueDiligence.score) !== null && normalizeDueScore(dueDiligence.score)! >= 75 && (
                    <Alert severity="success">
                      Strong long-term fundamentals detected across Core Due Diligence pillars.
                    </Alert>
                  )}

                  <Stack spacing={1}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Pillar breakdown
                    </Typography>
                    <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                      {dueDiligence.pillars.length > 0 ? (
                        dueDiligence.pillars.map((pillar) => {
                          const score = normalizeDueScore(pillar.score);
                          const chipColor = getDueScoreColor(score);
                          return (
                            <Tooltip
                              key={pillar.name}
                              title={`Weight ${(pillar.weight * 100).toFixed(0)}% • Confidence ${formatPercentage(
                                pillar.confidence
                              )}`}
                            >
                              <Chip
                                label={`${formatPillarName(pillar.name)} ${score !== null ? `${score.toFixed(1)}` : '—'}`}
                                sx={{
                                  borderColor: chipColor,
                                  color: chipColor,
                                  fontWeight: 600,
                                }}
                                variant="outlined"
                                size="small"
                              />
                            </Tooltip>
                          );
                        })
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          No pillar data available.
                        </Typography>
                      )}
                    </Stack>
                  </Stack>

                  {dueDiligence.warnings && dueDiligence.warnings.length > 0 && (
                    <Alert severity="info">
                      <Stack spacing={0.5}>
                        {dueDiligence.warnings.map((warning, idx) => (
                          <Typography key={idx} variant="body2">
                            {warning}
                          </Typography>
                        ))}
                      </Stack>
                    </Alert>
                  )}
                </Stack>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  Due diligence analysis not available for this asset yet.
                </Typography>
              )}
            </Stack>
          </CardContent>
        </Card>

        <Divider sx={{ mb: 3 }} />

        {/* Price Chart */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
            Price History
          </Typography>
          <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
            <ButtonGroup size="small" color="primary" variant="outlined">
              {historyRangeOptions.map((option) => (
                <Button
                  key={option.value}
                  onClick={() => setHistoryRange(option.value)}
                  variant={historyRange === option.value ? 'contained' : 'outlined'}
                >
                  {option.label}
                </Button>
              ))}
            </ButtonGroup>
          </Stack>
          {loadingHistory ? (
            <Box sx={{ height: 150, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <LinearProgress sx={{ width: '100%' }} />
            </Box>
          ) : historyData.length > 0 ? (
            <Box sx={{ height: 150 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={historyData}>
                  <defs>
                    <linearGradient id={`priceGradient-${asset.symbol}`} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#2563EB" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="#2563EB" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis 
                    dataKey="date" 
                    stroke={theme.palette.text.secondary}
                    tick={{ fontSize: 10, fill: theme.palette.text.secondary }}
                  />
                  <YAxis 
                    stroke={theme.palette.text.secondary}
                    tick={{ fontSize: 10, fill: theme.palette.text.secondary }}
                    tickFormatter={(value) => `$${value.toFixed(0)}`}
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
                    formatter={(value: number) => formatCurrency(value)}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="price" 
                    fill={`url(#priceGradient-${asset.symbol})`} 
                    stroke="none"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="price" 
                    stroke="#2563EB" 
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Box>
          ) : (
            <Box sx={{ 
              height: 150, 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              border: '1px dashed',
              borderColor: 'divider',
              borderRadius: 1,
              color: 'text.secondary'
            }}>
              No historical data available
            </Box>
          )}
        </Box>

        <Divider sx={{ mb: 3 }} />

        {/* Quick Actions */}
        <Box>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
            Quick Actions
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<NotificationsNone />}
              fullWidth
              sx={{ justifyContent: 'flex-start' }}
              onClick={() => {
                if (!asset) return;
                setAlertPrice(
                  typeof asset.current_price === 'number' && Number.isFinite(asset.current_price)
                    ? Number(asset.current_price.toFixed(2))
                    : ''
                );
                setAlertCondition('above');
                setPriceAlertOpen(true);
              }}
            >
              Set Price Alert
            </Button>
            <Button
              variant="outlined"
              startIcon={<ShowChart />}
              fullWidth
              sx={{ justifyContent: 'flex-start' }}
              onClick={() => {
                setChartDialogOpen(true);
                loadChartHistory();
              }}
            >
              View Full Chart
            </Button>
            <Button
              variant="outlined"
              startIcon={<Insights />}
              fullWidth
              sx={{ justifyContent: 'flex-start' }}
              onClick={() => {
                setRoiOpen((prev) => !prev);
                if (!roiOpen) {
                  computeRoiStats();
                }
              }}
            >
              {roiOpen ? 'Hide ROI Analysis' : 'Analyze ROI'}
            </Button>
          </Box>
          <Collapse in={roiOpen} unmountOnExit>
            <Box sx={{ mt: 2 }}>
              {roiLoading ? (
                <Box
                  sx={{
                    display: 'grid',
                    gap: 2,
                    gridTemplateColumns: { xs: 'repeat(1, minmax(0, 1fr))', sm: 'repeat(2, minmax(0, 1fr))' },
                  }}
                >
                  {[0, 1, 2, 3].map((item) => (
                    <Skeleton key={item} variant="rounded" height={72} />
                  ))}
                </Box>
              ) : (
                <Box
                  sx={{
                    display: 'grid',
                    gap: 2,
                    gridTemplateColumns: { xs: 'repeat(1, minmax(0, 1fr))', sm: 'repeat(2, minmax(0, 1fr))' },
                  }}
                >
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="caption" color="text.secondary">
                        Invested
                      </Typography>
                      <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                        {formatCurrency(roiStats?.invested)}
                      </Typography>
                    </CardContent>
                  </Card>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="caption" color="text.secondary">
                        Current value
                      </Typography>
                      <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                        {formatCurrency(roiStats?.currentValue)}
                      </Typography>
                    </CardContent>
                  </Card>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="caption" color="text.secondary">
                        Realized P&L
                      </Typography>
                      <Typography
                        variant="subtitle1"
                        sx={{
                          fontWeight: 700,
                          color:
                            typeof roiStats?.realized === 'number' && Number.isFinite(roiStats?.realized)
                              ? roiStats.realized >= 0
                                ? 'success.main'
                                : 'error.main'
                              : 'text.primary',
                        }}
                      >
                        {formatCurrency(roiStats?.realized)}
                      </Typography>
                    </CardContent>
                  </Card>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="caption" color="text.secondary">
                        Unrealized P&L
                      </Typography>
                      <Typography
                        variant="subtitle1"
                        sx={{
                          fontWeight: 700,
                          color:
                            typeof roiStats?.unrealized === 'number' && Number.isFinite(roiStats?.unrealized)
                              ? roiStats.unrealized >= 0
                                ? 'success.main'
                                : 'error.main'
                              : 'text.primary',
                        }}
                      >
                        {formatCurrency(roiStats?.unrealized)}
                      </Typography>
                    </CardContent>
                  </Card>
                  <Card variant="outlined" sx={{ gridColumn: '1 / -1' }}>
                    <CardContent>
                      <Typography variant="caption" color="text.secondary">
                        ROI
                      </Typography>
                      <Typography
                        variant="h6"
                        sx={{
                          fontWeight: 700,
                          color:
                            typeof roiStats?.roiPercent === 'number' && Number.isFinite(roiStats?.roiPercent)
                              ? roiStats.roiPercent >= 0
                                ? 'success.main'
                                : 'error.main'
                              : 'text.primary',
                        }}
                      >
                        {formatPercentage(roiStats?.roiPercent)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        ROI is based on unrealized + realized P&amp;L relative to invested amount.
                      </Typography>
                    </CardContent>
                  </Card>
                </Box>
              )}
            </Box>
          </Collapse>
        </Box>
      </Box>
      <Dialog open={priceAlertOpen} onClose={() => !alertSubmitting && setPriceAlertOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Set price alert</DialogTitle>
        <DialogContent dividers>
          <Stack spacing={2}>
            <TextField label="Symbol" value={asset?.symbol ?? ''} fullWidth disabled />
            <FormControl fullWidth>
              <InputLabel>Condition</InputLabel>
              <Select
                value={alertCondition}
                label="Condition"
                onChange={(event) => setAlertCondition(event.target.value as 'above' | 'below')}
                disabled={alertSubmitting}
              >
                <MenuItem value="above">Price rises above</MenuItem>
                <MenuItem value="below">Price drops below</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Target price (USD)"
              type="number"
              value={alertPrice}
              onChange={(event) => setAlertPrice(event.target.value === '' ? '' : Number(event.target.value))}
              disabled={alertSubmitting}
              inputProps={{ step: '0.01', min: '0' }}
            />
            <Typography variant="body2" color="text.secondary">
              Current price: {formatCurrency(currentPrice ?? undefined)}
            </Typography>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => setPriceAlertOpen(false)}
            disabled={alertSubmitting}
          >
            Cancel
          </Button>
          <Button
            onClick={async () => {
              if (!asset || alertPrice === '' || alertPrice <= 0) {
                showToast('Provide a valid target price', 'warning');
                return;
              }
              setAlertSubmitting(true);
              try {
                await portfolioService.createPriceAlert({
                  symbol: asset.symbol,
                  price: alertPrice,
                  condition: alertCondition,
                  name: `${asset.symbol} ${alertCondition === 'above' ? '>' : '<'} ${alertPrice}`,
                });
                showToast('Price alert created', 'success');
                setPriceAlertOpen(false);
              } catch (error) {
                logger.error('Failed to create price alert', error);
                showToast('Failed to create price alert', 'error');
              } finally {
                setAlertSubmitting(false);
              }
            }}
            variant="contained"
            disabled={alertSubmitting}
          >
            {alertSubmitting ? 'Creating...' : 'Create alert'}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog
        open={chartDialogOpen}
        onClose={() => setChartDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Extended price history ({asset?.symbol})</DialogTitle>
        <DialogContent dividers>
          {chartLoading ? (
            <Box sx={{ height: 360 }}>
              <Skeleton variant="rounded" height="100%" />
            </Box>
          ) : chartHistory.length > 0 ? (
            <Box sx={{ height: 360 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartHistory}>
                  <XAxis
                    dataKey="date"
                    stroke={theme.palette.text.secondary}
                    tick={{ fontSize: 11, fill: theme.palette.text.secondary }}
                  />
                  <YAxis
                    stroke={theme.palette.text.secondary}
                    tick={{ fontSize: 11, fill: theme.palette.text.secondary }}
                    tickFormatter={(value) => formatCurrency(value)}
                  />
                  <RechartsTooltip
                    contentStyle={{
                      backgroundColor:
                        theme.palette.mode === 'dark'
                          ? 'rgba(45, 55, 72, 0.98)'
                          : 'rgba(255, 255, 255, 0.98)',
                      border: `1px solid ${theme.palette.divider}`,
                      borderRadius: '12px',
                      padding: '12px 16px',
                      fontSize: 14,
                      boxShadow: '0 8px 24px rgba(0, 0, 0, 0.2)',
                    }}
                    labelStyle={{
                      color: theme.palette.text.primary,
                      fontWeight: 600,
                    }}
                    formatter={(value: number) => formatCurrency(value)}
                  />
                  <Area
                    type="monotone"
                    dataKey="price"
                    fill="rgba(37, 99, 235, 0.12)"
                    stroke="none"
                  />
                  <Line type="monotone" dataKey="price" stroke="#2563EB" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </Box>
          ) : (
            <Box
              sx={{
                height: 360,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '1px dashed',
                borderColor: 'divider',
                borderRadius: 1,
                color: 'text.secondary',
              }}
            >
              No price history available
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setChartDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      <Toast open={toast.open} message={toast.message} severity={toast.severity} onClose={hideToast} />
    </Drawer>
  );
};

