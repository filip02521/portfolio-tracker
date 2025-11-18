import React, { useEffect, useMemo, useState } from 'react';
import {
  Box,
  Drawer,
  Typography,
  IconButton,
  Chip,
  Divider,
  Tabs,
  Tab,
  Button,
  CircularProgress,
  useTheme,
} from '@mui/material';
import { Close, NotificationsOutlined } from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { portfolioService } from '../services/portfolioService';

export interface MarketWatchDrawerItem {
  symbol: string;
  name: string;
  price: number;
  changePercent24h: number;
  change24h?: number;
  volume?: number;
  volume_24h?: number;
  marketCap?: number;
  market_cap?: number;
  high_24h?: number;
  low_24h?: number;
  type: 'crypto' | 'stock';
}

interface MarketWatchDrawerProps {
  open: boolean;
  onClose: () => void;
  item: MarketWatchDrawerItem | null;
  series7d?: number[];
  provider?: string;
  lastUpdatedTs?: number | null;
}

export const MarketWatchDrawer: React.FC<MarketWatchDrawerProps> = ({ open, onClose, item, series7d, provider, lastUpdatedTs }) => {
  const theme = useTheme();
  const [tab, setTab] = useState<'7d' | '1m' | '3m' | '1y'>('7d');
  const [chartData, setChartData] = useState<Array<{ date: string; close: number; timestamp: number }>>([]);
  const [loadingChart, setLoadingChart] = useState(false);
  const [chartError, setChartError] = useState<string | null>(null);

  // Persist last opened section (tab)
  useEffect(() => {
    try {
      const saved = localStorage.getItem('mw_drawer_tab');
      if (saved === '7d' || saved === '1m' || saved === '3m' || saved === '1y') setTab(saved);
    } catch {}
  }, []);
  useEffect(() => {
    try { localStorage.setItem('mw_drawer_tab', tab); } catch {}
  }, [tab]);

  // Fetch chart data when item or tab changes
  useEffect(() => {
    if (!item || !open) {
      setChartData([]);
      return;
    }

    const fetchChartData = async () => {
      setLoadingChart(true);
      setChartError(null);
      try {
        const days = tab === '7d' ? 7 : tab === '1m' ? 30 : tab === '3m' ? 90 : 365;
        const history = await portfolioService.getSymbolHistory(item.symbol, days, true);
        
        const formatted = history.map((point: { date: string; close: number }) => ({
          date: new Date(point.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
          close: point.close,
          timestamp: new Date(point.date).getTime(),
        }));
        
        setChartData(formatted);
      } catch (err: any) {
        setChartError(err.message || 'Failed to load chart data');
        setChartData([]);
      } finally {
        setLoadingChart(false);
      }
    };

    fetchChartData();
  }, [item?.symbol, tab, open]);

  const pctColor = useMemo(() => (item && item.changePercent24h >= 0 ? 'success.main' : 'error.main'), [item]);
  
  const chartColor = useMemo(() => {
    if (!item) return theme.palette.primary.main;
    return item.changePercent24h >= 0 ? theme.palette.success.main : theme.palette.error.main;
  }, [item, theme]);

  return (
    <Drawer 
      anchor="right" 
      open={open} 
      onClose={onClose} 
      PaperProps={{ sx: { width: { xs: '100%', sm: 420 } } }}
      onKeyDown={(e) => {
        if (e.key === 'Escape') {
          onClose();
        }
      }}
    >
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            {item?.symbol || ''}
          </Typography>
          {item && (
            <Chip
              size="small"
              label={item.type === 'crypto' ? 'Crypto' : 'Stock'}
              sx={{
                height: 20,
                fontSize: '0.65rem',
                bgcolor: item.type === 'crypto' ? 'rgba(245, 158, 11, 0.15)' : 'rgba(59, 130, 246, 0.15)',
                color: item.type === 'crypto' ? 'warning.main' : 'info.main'
              }}
            />
          )}
        </Box>
        <IconButton aria-label="Close details" onClick={onClose}>
          <Close />
        </IconButton>
      </Box>
      <Box sx={{ p: 2 }}>
        <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1.5 }}>
          {item?.name || ''}
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1, mb: 1.5 }}>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            {item ? new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(item.price) : ''}
          </Typography>
          {item && (
            <Typography variant="subtitle2" sx={{ color: pctColor }}>
              {(item.changePercent24h >= 0 ? '+' : '') + item.changePercent24h.toFixed(2) + '%'}
            </Typography>
          )}
        </Box>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
          {lastUpdatedTs ? `Updated ${new Date(lastUpdatedTs).toLocaleTimeString()}` : ''}
        </Typography>
        {/* Extended Metrics */}
        {item && (
          <Box sx={{ mb: 2, display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 1.5 }}>
            {item.high_24h !== undefined && (
              <Box sx={{ p: 1.5, borderRadius: 1, bgcolor: 'rgba(0, 0, 0, 0.02)' }}>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                  24h High
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  {new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(item.high_24h)}
                </Typography>
              </Box>
            )}
            {item.low_24h !== undefined && (
              <Box sx={{ p: 1.5, borderRadius: 1, bgcolor: 'rgba(0, 0, 0, 0.02)' }}>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                  24h Low
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  {new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(item.low_24h)}
                </Typography>
              </Box>
            )}
            {item.volume_24h !== undefined && item.volume_24h > 0 && (
              <Box sx={{ p: 1.5, borderRadius: 1, bgcolor: 'rgba(0, 0, 0, 0.02)' }}>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                  24h Volume
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  ${(item.volume_24h / 1e6).toFixed(2)}M
                </Typography>
              </Box>
            )}
            {item.market_cap !== undefined && item.market_cap > 0 && (
              <Box sx={{ p: 1.5, borderRadius: 1, bgcolor: 'rgba(0, 0, 0, 0.02)' }}>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                  Market Cap
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  ${(item.market_cap / 1e9).toFixed(2)}B
                </Typography>
              </Box>
            )}
          </Box>
        )}

        <Divider sx={{ my: 2 }} />

        <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ minHeight: 36 }}>
          <Tab label="7d" value="7d" sx={{ minHeight: 36 }} />
          <Tab label="1m" value="1m" sx={{ minHeight: 36 }} />
          <Tab label="3m" value="3m" sx={{ minHeight: 36 }} />
          <Tab label="1y" value="1y" sx={{ minHeight: 36 }} />
        </Tabs>

        {/* Advanced Chart */}
        <Box sx={{ mb: 2, height: 280, borderRadius: 1, position: 'relative' }}>
          {loadingChart ? (
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
              <CircularProgress size={32} />
            </Box>
          ) : chartError ? (
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'text.secondary' }}>
              <Typography variant="body2">{chartError}</Typography>
            </Box>
          ) : chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                <defs>
                  <linearGradient id={`gradient-${item?.symbol}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={chartColor} stopOpacity={0.3} />
                    <stop offset="100%" stopColor={chartColor} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
                <XAxis
                  dataKey="date"
                  stroke={theme.palette.text.secondary}
                  tick={{ fontSize: 11, fill: theme.palette.text.secondary }}
                  interval="preserveStartEnd"
                />
                <YAxis
                  stroke={theme.palette.text.secondary}
                  tick={{ fontSize: 11, fill: theme.palette.text.secondary }}
                  tickFormatter={(value) => `$${value.toFixed(item && item.price > 100 ? 0 : 2)}`}
                  domain={['auto', 'auto']}
                />
                <RechartsTooltip
                  contentStyle={{
                    backgroundColor: theme.palette.background.paper,
                    border: `1px solid ${theme.palette.divider}`,
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                  formatter={(value: number) => [
                    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value),
                    'Price'
                  ]}
                  labelStyle={{ fontWeight: 600, marginBottom: 4 }}
                />
                {item && (
                  <ReferenceLine
                    y={item.price}
                    stroke={theme.palette.text.secondary}
                    strokeDasharray="2 2"
                    strokeOpacity={0.5}
                  />
                )}
                <Area
                  type="monotone"
                  dataKey="close"
                  stroke={chartColor}
                  strokeWidth={2}
                  fill={`url(#gradient-${item?.symbol})`}
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'text.secondary' }}>
              <Typography variant="body2">No chart data available</Typography>
            </Box>
          )}
        </Box>

        <Divider sx={{ my: 2 }} />
        <Typography variant="subtitle2" sx={{ mb: 1.5 }}>Quick alerts</Typography>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
          {[1,2,5].map(p => (
            <Button key={p} size="small" variant="outlined" startIcon={<NotificationsOutlined />}>
              {p > 0 ? `+${p}%` : `${p}%`}
            </Button>
          ))}
          {[1,2,5].map(p => (
            <Button key={-p} size="small" variant="outlined" startIcon={<NotificationsOutlined />}>-{p}%</Button>
          ))}
        </Box>

        <Divider sx={{ my: 2 }} />
        <Typography variant="subtitle2" sx={{ mb: 1.5 }}>Details</Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1.5, mb: 2 }}>
          {item?.type === 'stock' ? (
            <>
              <Chip size="small" label="Market cap: —" />
              <Chip size="small" label="P/E: —" />
              <Chip size="small" label="52w range: —" />
              <Chip size="small" label="Div yield: —" />
            </>
          ) : (
            <>
              <Chip size="small" label="24h vol: —" />
              <Chip size="small" label="Dominance: —" />
              <Chip size="small" label="Volatility: —" />
              <Chip size="small" label="Pairs: —" />
            </>
          )}
        </Box>

        <Divider sx={{ my: 2 }} />
        <Typography variant="subtitle2" sx={{ mb: 1 }}>Activity</Typography>
        <Typography variant="caption" color="text.secondary">
          Source: {provider || 'auto'}
        </Typography>
      </Box>
    </Drawer>
  );
};

export default MarketWatchDrawer;



