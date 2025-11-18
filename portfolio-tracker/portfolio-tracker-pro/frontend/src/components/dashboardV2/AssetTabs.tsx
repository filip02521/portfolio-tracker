import React from 'react';
import {
  Box,
  Tabs,
  Tab,
  Stack,
  Typography,
  Card,
  CardContent,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Chip,
  Divider,
  useTheme,
  Tooltip,
  useMediaQuery,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
} from '@mui/material';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  Tooltip as RechartsTooltip,
} from 'recharts';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';

import { AssetTabData, TrendBar, NewsItem, HeatmapCell } from './types';
import { dashboardPalette } from '../../theme/dashboardTokens';
import { SectionHeader } from '../common/SectionHeader';

const usdFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 2,
});

const amountFormatter = new Intl.NumberFormat('en-US', {
  maximumFractionDigits: 6,
});

const formatUsd = (value: number | undefined) =>
  usdFormatter.format(Number.isFinite(value ?? NaN) ? (value ?? 0) : 0);

const formatAmount = (value: number | undefined) =>
  amountFormatter.format(Number.isFinite(value ?? NaN) ? (value ?? 0) : 0);

const renderSourcesTooltip = (
  sources?:
    | Array<{
        exchange?: string;
        amount?: number;
        value_usd?: number;
        pnl?: number;
        pnl_percent?: number;
        average_price?: number;
      }>
    | null
) => {
  if (!sources || sources.length === 0) {
    return null;
  }

  return (
    <Stack spacing={1} sx={{ p: 0.5 }}>
      {sources.map((source, index) => (
        <Box key={`${source.exchange || 'unknown'}-${index}`}>
          <Typography variant="caption" sx={{ fontWeight: 600 }}>
            {source.exchange || 'Unknown'}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {`${formatAmount(source.amount)} • ${formatUsd(source.value_usd)} • P/L ${formatUsd(source.pnl)} (${Number.isFinite(source.pnl_percent) ? source.pnl_percent!.toFixed(2) : '0.00'}%)`}
          </Typography>
          {Number.isFinite(source.average_price) && (source.average_price ?? 0) > 0 ? (
            <Typography variant="caption" color="text.secondary">
              Avg cost {formatUsd(source.average_price)}
            </Typography>
          ) : null}
        </Box>
      ))}
    </Stack>
  );
};

interface AssetTabsProps {
  stocks: AssetTabData;
  crypto: AssetTabData;
  assetIssueLookup?: Record<string, string[]>;
  defaultTab?: 'stocks' | 'crypto';
  viewMode: 'table' | 'cards' | 'chart';
  changeLookup?: Record<string, { direction: 'up' | 'down'; deltaPercent: number; deltaValue: number }>;
}

const Heatmap: React.FC<{ data: AssetTabData['heatmap']; accent: 'stocks' | 'crypto' }> = ({ data, accent }) => {
  const theme = useTheme();
  const isSmallScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const accentColor = accent === 'stocks' ? dashboardPalette.stocksAccent : dashboardPalette.cryptoAccent;
  const displayData = isSmallScreen ? data.slice(0, 6) : data;

  const getColor = (cell: HeatmapCell) => {
    const value = cell.value ?? 0;
    if (!Number.isFinite(value)) {
      return theme.palette.mode === 'dark' ? 'rgba(148, 163, 184, 0.2)' : 'rgba(148, 163, 184, 0.16)';
    }
    if (value === 0) {
      return theme.palette.mode === 'dark' ? 'rgba(148, 163, 184, 0.2)' : 'rgba(148, 163, 184, 0.16)';
    }
    const riskComponent = Math.min((cell.riskScore ?? Math.min(Math.abs(value) * 4, 100)) / 100, 1);
    const intensity = Math.min(Math.abs(value) / 8 + riskComponent * 0.5, 1);
    if (value > 0) {
      return `rgba(34, 197, 94, ${0.25 + intensity * 0.55})`;
    }
    return `rgba(239, 68, 68, ${0.25 + intensity * 0.55})`;
  };

  return (
    <Card variant="outlined" sx={{ borderRadius: 2 }}>
      <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, p: 3.5 }}>
        <Box sx={{ mb: 1 }}>
          <SectionHeader
            title="Daily Heatmap"
            description={`Visual representation of ${accent === 'stocks' ? 'stock' : 'crypto'} asset performance. Color intensity indicates P/L percentage and risk level.`}
            tooltip="Green cells indicate positive returns, red cells indicate negative returns. Darker colors represent larger moves or higher risk. Hover over cells to see detailed metrics."
          />
        </Box>
        <Stack direction="row" justifyContent="flex-end" alignItems="center" sx={{ mb: 1 }}>
          <Chip
            size="small"
            label={`${accent === 'stocks' ? 'Stocks' : 'Crypto'} moves`}
            sx={{ borderRadius: 2, backgroundColor: accentColor, color: '#fff', fontWeight: 600 }}
          />
        </Stack>

        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: {
              xs: 'repeat(2, minmax(0, 1fr))',
              sm: 'repeat(3, minmax(0, 1fr))',
              md: 'repeat(4, minmax(0, 1fr))',
            },
            gap: 1,
          }}
        >
          {displayData.map((cell) => (
            <Box key={cell.id}>
              <Stack
                sx={{
                  borderRadius: 2,
                  p: 1.5,
                  backgroundColor: getColor(cell),
                }}
                spacing={0.5}
              >
                <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                  {cell.label}
                </Typography>
                <Typography
                  variant="caption"
                  sx={{
                    color: cell.value >= 0 ? dashboardPalette.accent.positive : dashboardPalette.accent.negative,
                    fontWeight: 600,
                  }}
                >
                  {cell.value >= 0 ? '+' : ''}
                  {cell.value.toFixed(2)}%
                </Typography>
                {(cell.riskScore !== undefined || cell.allocation !== undefined || cell.volatility !== undefined) && (
                  <Typography variant="caption" color="text.secondary">
                    {cell.riskScore !== undefined ? `Risk ${cell.riskScore.toFixed(0)}` : ''}
                    {cell.volatility !== undefined ? ` • Vol ${cell.volatility.toFixed(1)}%` : ''}
                    {cell.allocation !== undefined ? ` • Alloc ${cell.allocation.toFixed(1)}%` : ''}
                  </Typography>
                )}
              </Stack>
            </Box>
          ))}
        </Box>
      </CardContent>
    </Card>
  );
};

const HoldingsTable: React.FC<{
  data: AssetTabData['holdings'];
  accent: 'stocks' | 'crypto';
  issueLookup?: Record<string, string[]>;
  changeLookup?: Record<string, { direction: 'up' | 'down'; deltaPercent: number; deltaValue: number }>;
}> = ({ data, accent, issueLookup = {}, changeLookup = {} }) => {
  const columnTooltips: Record<string, string> = {
    'Ticker / Symbol': 'Asset symbol and exchange information. Click to view details.',
    'Position': 'Total quantity of the asset held across all exchanges.',
    'Average Price': 'Average purchase price (cost basis) calculated from all transactions.',
    'Current Price': 'Current market price of the asset from the latest data update.',
    'Value': 'Total current value of the position (quantity × current price).',
    'P/L ($)': 'Profit or loss in USD. Positive values indicate profit, negative indicate loss.',
    'P/L %': 'Profit or loss as a percentage of the average purchase price.',
    'ROI': 'Return on Investment - total return percentage based on cost basis.',
    'Last Update': 'Timestamp of the last price update from market data providers.',
  };

  return (
    <Card variant="outlined" sx={{ borderRadius: 2 }}>
      <CardContent sx={{ p: 3.5 }}>
        <Box sx={{ mb: 2.5 }}>
          <SectionHeader
            title="Holdings"
            description="Detailed breakdown of all asset positions. Shows position size, prices, values, and profit/loss metrics."
            tooltip="This table displays all your holdings with key metrics. Green P/L values indicate profit, red indicates loss. Warning icons indicate data quality issues."
          />
        </Box>
        <Box sx={{ overflowX: 'auto' }}>
          <Table size="small" sx={{ minWidth: 840 }}>
            <TableHead>
              <TableRow>
                {Object.entries(columnTooltips).map(([label, tooltip]) => (
                  <Tooltip key={label} title={tooltip} arrow placement="top">
                    <TableCell sx={{ fontWeight: 600, fontSize: '0.875rem', py: 1.5 }}>
                      {label}
                    </TableCell>
                  </Tooltip>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {data.map((row) => {
                const issueKey = `${row.exchange}:${row.symbol}`;
                const issues = issueLookup[issueKey] ?? [];
                const change = changeLookup[row.symbol.toUpperCase()];
                const exchangeCount = row.exchangeList?.length ?? 0;
                const hasMultipleSources = exchangeCount > 1;
                const tooltipContent = renderSourcesTooltip(row.sources);
                const tooltipTitle =
                  tooltipContent ??
                  (row.exchangeList && row.exchangeList.length ? row.exchangeList.join(', ') : 'Exchange breakdown unavailable');
                return (
                  <TableRow
                    key={`${row.exchange}-${row.symbol}`}
                    hover
                    selected={issues.length > 0}
                    sx={{
                      borderLeft: change
                        ? `3px solid ${
                            change.direction === 'up' ? dashboardPalette.accent.positive : dashboardPalette.accent.negative
                          }`
                        : undefined,
                      backgroundColor: change
                        ? change.direction === 'up'
                          ? 'rgba(34, 197, 94, 0.08)'
                          : 'rgba(239, 68, 68, 0.08)'
                        : undefined,
                    }}
                  >
                    <TableCell>
                      <Stack direction="row" spacing={1} alignItems="center">
                        <Chip
                          size="small"
                          label={row.symbol}
                          sx={{
                            fontWeight: 600,
                            borderRadius: 2,
                            backgroundColor:
                              accent === 'stocks' ? 'rgba(37, 99, 235, 0.12)' : 'rgba(124, 58, 237, 0.12)',
                          }}
                        />
                        <Typography variant="body2" color="text.secondary">
                          {row.position}
                        </Typography>
                        {row.exchangeList && row.exchangeList.length > 0 && (
                          <Tooltip title={tooltipTitle} arrow placement="top">
                            <Chip
                              size="small"
                              label={hasMultipleSources ? `${exchangeCount} exchanges` : row.exchangeList[0]}
                              sx={{
                                borderRadius: 2,
                                fontWeight: 600,
                                backgroundColor: hasMultipleSources
                                  ? accent === 'stocks'
                                    ? 'rgba(37, 99, 235, 0.16)'
                                    : 'rgba(124, 58, 237, 0.16)'
                                  : 'transparent',
                                borderColor: hasMultipleSources ? 'transparent' : 'divider',
                              }}
                              variant={hasMultipleSources ? 'filled' : 'outlined'}
                            />
                          </Tooltip>
                        )}
                        {change && (
                          <Tooltip title={`${change.direction === 'up' ? 'Price increased' : 'Price decreased'} by ${Math.abs(change.deltaPercent).toFixed(1)}% since last update. This indicates recent price movement for this asset.`} arrow>
                            <Chip
                              size="small"
                              icon={
                                change.direction === 'up' ? (
                                  <ArrowUpwardIcon fontSize="inherit" />
                                ) : (
                                  <ArrowDownwardIcon fontSize="inherit" />
                                )
                              }
                              label={`${change.direction === 'up' ? '+' : '-'}${Math.abs(change.deltaPercent).toFixed(1)}%`}
                              sx={{
                                borderRadius: 2,
                                backgroundColor:
                                  change.direction === 'up'
                                    ? 'rgba(34, 197, 94, 0.2)'
                                    : 'rgba(239, 68, 68, 0.2)',
                                fontWeight: 600,
                                cursor: 'help',
                              }}
                            />
                          </Tooltip>
                        )}
                        {issues.length > 0 && (
                          <Tooltip title={`Data quality issues detected: ${issues.join('; ')}. This may affect accuracy of calculations.`} arrow>
                            <WarningAmberIcon color="warning" fontSize="small" sx={{ cursor: 'help' }} />
                          </Tooltip>
                        )}
                      </Stack>
                    </TableCell>
                    <TableCell>{row.position}</TableCell>
                    <TableCell>{row.avgPrice}</TableCell>
                    <TableCell>{row.currentPrice}</TableCell>
                    <TableCell>{row.value}</TableCell>
                    <TableCell
                      sx={{
                        color: row.plValueRaw >= 0 ? dashboardPalette.accent.positive : dashboardPalette.accent.negative,
                        fontWeight: 600,
                      }}
                    >
                      {row.plValue}
                    </TableCell>
                    <TableCell
                      sx={{
                        color: row.plPercent >= 0 ? dashboardPalette.accent.positive : dashboardPalette.accent.negative,
                        fontWeight: 600,
                      }}
                    >
                      {row.plPercent >= 0 ? '+' : ''}
                      {row.plPercent.toFixed(2)}%
                    </TableCell>
                    <TableCell sx={{ fontWeight: 600 }}>{row.roi.toFixed(2)}%</TableCell>
                    <TableCell>{row.lastUpdated}</TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </Box>
      </CardContent>
    </Card>
  );
};

const TrendsPanel: React.FC<{ data: TrendBar[]; accent: 'stocks' | 'crypto' }> = ({ data, accent }) => {
  const accentColor = accent === 'stocks' ? dashboardPalette.stocksAccent : dashboardPalette.cryptoAccent;
  return (
    <Card variant="outlined" sx={{ borderRadius: 2 }}>
      <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, p: 3.5 }}>
        <Box sx={{ mb: 1 }}>
          <SectionHeader
            title="ROI Trends"
            description="Historical return on investment across different time periods (1 week, 1 month, 3 months)."
            tooltip="Shows how ROI has changed over different time horizons. Helps identify performance trends and time periods of strong or weak returns."
          />
        </Box>
        <Box
          sx={{
            height: 220,
            minHeight: 220,
            minWidth: 0,
          }}
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <XAxis dataKey="label" axisLine={false} tickLine={false} />
              <RechartsTooltip
                contentStyle={{
                  borderRadius: 2,
                  border: '1px solid rgba(148, 163, 184, 0.12)',
                }}
              />
              <Bar dataKey="roi" radius={[8, 8, 0, 0]} fill={accentColor} />
            </BarChart>
          </ResponsiveContainer>
        </Box>
      </CardContent>
    </Card>
  );
};

const NewsList: React.FC<{ data?: NewsItem[] }> = ({ data }) => {
  const [selected, setSelected] = React.useState<NewsItem | null>(null);

  if (!data || data.length === 0) {
    return null;
  }

  const getSentimentColor = (sentiment?: string) => {
    if (sentiment === 'positive') {
      return dashboardPalette.accent.positive;
    }
    if (sentiment === 'negative') {
      return dashboardPalette.accent.negative;
    }
    return 'rgba(148, 163, 184, 0.32)';
  };

  return (
    <Card variant="outlined" sx={{ borderRadius: 2 }}>
      <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, p: 3.5 }}>
        <Box sx={{ mb: 1 }}>
          <SectionHeader
            title="Market Headlines"
            description="Recent news and headlines related to your portfolio assets. Click any headline to read the full article."
            tooltip="News articles are filtered for relevance to your holdings. Sentiment indicators show whether news is positive, negative, or neutral."
          />
        </Box>
        <Stack spacing={1.5}>
          {data.map((news) => (
            <Box key={news.id}>
              <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
                <Typography
                  variant="subtitle2"
                  sx={{
                    fontWeight: 600,
                    flexGrow: 1,
                    cursor: 'pointer',
                    textDecoration: 'none',
                    color: 'text.primary',
                  }}
                  onClick={() => setSelected(news)}
                >
                  {news.title}
                </Typography>
                <Stack direction="row" spacing={1} alignItems="center">
                  {news.sentiment && (
                    <Chip
                      size="small"
                      label={news.sentiment}
                      sx={{
                        textTransform: 'capitalize',
                        borderRadius: 2,
                        color: '#fff',
                        backgroundColor: getSentimentColor(news.sentiment),
                      }}
                    />
                  )}
                  <Chip size="small" label={news.source} sx={{ borderRadius: 2 }} />
                </Stack>
              </Stack>
              <Typography variant="caption" color="text.secondary">
                {news.timestamp}
              </Typography>
              {news.summary && (
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                  {news.summary}
                </Typography>
              )}
            </Box>
          ))}
        </Stack>
      </CardContent>
      <Dialog
        open={Boolean(selected)}
        onClose={() => setSelected(null)}
        fullWidth
        maxWidth="sm"
      >
        {selected && (
          <>
            <DialogTitle sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Typography variant="subtitle2" color="text.secondary">
                {new Date(selected.timestamp).toLocaleString()}
              </Typography>
              <Typography variant="h6" sx={{ fontWeight: 700 }}>
                {selected.title}
              </Typography>
              <Chip
                size="small"
                label={selected.source}
                sx={{ alignSelf: 'flex-start', borderRadius: 2, fontWeight: 600 }}
              />
            </DialogTitle>
            <DialogContent dividers>
              <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                {selected.summary || 'No summary available for this article.'}
              </Typography>
            </DialogContent>
            <DialogActions sx={{ justifyContent: 'space-between', px: 3 }}>
              <Typography variant="body2" color="text.secondary">
                Powiązany symbol: {selected.symbol ?? '—'}
              </Typography>
              <Stack direction="row" spacing={1}>
                <Button onClick={() => setSelected(null)} color="inherit">
                  Zamknij
                </Button>
                {selected.url && (
                  <Button
                    href={selected.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    variant="contained"
                  >
                    Czytaj źródło
                  </Button>
                )}
              </Stack>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Card>
  );
};

const HoldingsCards: React.FC<{
  data: AssetTabData['holdings'];
  accent: 'stocks' | 'crypto';
  issueLookup?: Record<string, string[]>;
  changeLookup?: Record<string, { direction: 'up' | 'down'; deltaPercent: number; deltaValue: number }>;
}> = ({ data, accent, issueLookup = {}, changeLookup = {} }) => {
  return (
    <Box
      sx={{
        display: 'grid',
        gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, minmax(0, 1fr))' },
        gap: 2,
      }}
    >
      {data.map((row) => {
        const issues = issueLookup[`${row.exchange}:${row.symbol}`] ?? [];
        const change = changeLookup[row.symbol.toUpperCase()];
        const exchangeCount = row.exchangeList?.length ?? 0;
        const hasMultipleSources = exchangeCount > 1;
        const tooltipContent = renderSourcesTooltip(row.sources);
        const tooltipTitle =
          tooltipContent ??
          (row.exchangeList && row.exchangeList.length ? row.exchangeList.join(', ') : 'Exchange breakdown unavailable');
        return (
          <Card key={`${row.exchange}-${row.symbol}`} variant="outlined" sx={{ borderRadius: 2 }}>
            <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, p: 3.5 }}>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Stack direction="row" spacing={1} alignItems="center">
                  <Chip
                    size="small"
                    label={row.symbol}
                    sx={{
                      borderRadius: 2,
                      fontWeight: 600,
                      backgroundColor:
                        accent === 'stocks' ? 'rgba(37, 99, 235, 0.12)' : 'rgba(124, 58, 237, 0.12)',
                    }}
                  />
                  <Typography variant="body2" color="text.secondary">
                    {row.lastUpdated}
                  </Typography>
                  {row.exchangeList && row.exchangeList.length > 0 && (
                    <Tooltip title={tooltipTitle} arrow placement="top">
                      <Chip
                        size="small"
                        label={hasMultipleSources ? `${exchangeCount} exchanges` : row.exchangeList[0]}
                        sx={{
                          borderRadius: 2,
                          fontWeight: 600,
                          backgroundColor: hasMultipleSources
                            ? accent === 'stocks'
                              ? 'rgba(37, 99, 235, 0.16)'
                              : 'rgba(124, 58, 237, 0.16)'
                            : 'transparent',
                          borderColor: hasMultipleSources ? 'transparent' : 'divider',
                        }}
                        variant={hasMultipleSources ? 'filled' : 'outlined'}
                      />
                    </Tooltip>
                  )}
                  {change && (
                    <Chip
                      size="small"
                      icon={
                        change.direction === 'up' ? (
                          <ArrowUpwardIcon fontSize="inherit" />
                        ) : (
                          <ArrowDownwardIcon fontSize="inherit" />
                        )
                      }
                      label={`${change.direction === 'up' ? '+' : '-'}${Math.abs(change.deltaPercent).toFixed(1)}%`}
                      sx={{
                        borderRadius: 2,
                        fontWeight: 600,
                        backgroundColor:
                          change.direction === 'up'
                            ? 'rgba(34, 197, 94, 0.16)'
                            : 'rgba(239, 68, 68, 0.16)',
                      }}
                    />
                  )}
                  {issues.length > 0 && (
                    <Tooltip title={`Data quality issues detected: ${issues.join('; ')}. This may affect accuracy of calculations.`} arrow>
                      <WarningAmberIcon color="warning" fontSize="small" sx={{ cursor: 'help' }} />
                    </Tooltip>
                  )}
                </Stack>
                <Stack spacing={0.5} alignItems="flex-end">
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>
                    {row.value}
                  </Typography>
                  <Typography
                    variant="body2"
                    sx={{
                      fontWeight: 600,
                      color: row.plValueRaw >= 0 ? dashboardPalette.accent.positive : dashboardPalette.accent.negative,
                    }}
                  >
                    {row.plValue}
                  </Typography>
                </Stack>
              </Stack>
              <Divider />
              <Stack direction="row" justifyContent="space-between">
                <Stack spacing={0.5}>
                  <Typography variant="caption" color="text.secondary">
                    Position
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 600 }}>
                    {row.position}
                  </Typography>
                </Stack>
                <Stack spacing={0.5}>
                  <Typography variant="caption" color="text.secondary">
                    Avg / Current
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 600 }}>
                    {row.avgPrice} • {row.currentPrice}
                  </Typography>
                </Stack>
                <Stack spacing={0.5} alignItems="flex-end">
                  <Typography variant="caption" color="text.secondary">
                    P/L %
                  </Typography>
                  <Typography
                    variant="body1"
                    sx={{
                      fontWeight: 700,
                      color: row.plPercent >= 0 ? dashboardPalette.accent.positive : dashboardPalette.accent.negative,
                    }}
                  >
                    {row.plPercent >= 0 ? '+' : ''}
                    {row.plPercent.toFixed(2)}%
                  </Typography>
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        );
      })}
    </Box>
  );
};

const AssetPanel: React.FC<{
  data: AssetTabData;
  accent: 'stocks' | 'crypto';
  viewMode: 'table' | 'cards' | 'chart';
  issueLookup?: Record<string, string[]>;
  changeLookup?: Record<string, { direction: 'up' | 'down'; deltaPercent: number; deltaValue: number }>;
}> = ({ data, accent, viewMode, issueLookup, changeLookup }) => {
  return (
    <Stack spacing={2.5}>
      {viewMode !== 'chart' && <Heatmap data={data.heatmap} accent={accent} />}
      {viewMode === 'cards' ? (
        <HoldingsCards data={data.holdings} accent={accent} issueLookup={issueLookup} changeLookup={changeLookup} />
      ) : (
        <HoldingsTable data={data.holdings} accent={accent} issueLookup={issueLookup} changeLookup={changeLookup} />
      )}
      <Stack direction={{ xs: 'column', md: 'row' }} spacing={2.5}>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <TrendsPanel data={data.trends} accent={accent} />
        </Box>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <NewsList data={data.news} />
        </Box>
      </Stack>
    </Stack>
  );
};

export const AssetTabs: React.FC<AssetTabsProps> = ({
  stocks,
  crypto,
  assetIssueLookup = {},
  defaultTab = 'stocks',
  viewMode,
  changeLookup,
}) => {
  const [tab, setTab] = React.useState<'stocks' | 'crypto'>(defaultTab);

  const handleChange = (_: React.SyntheticEvent, value: 'stocks' | 'crypto') => {
    if (value) {
      setTab(value);
    }
  };

  const activeData = tab === 'stocks' ? stocks : crypto;
  const accent = tab === 'stocks' ? 'stocks' : 'crypto';

  return (
    <Box component="section" aria-label="Asset Details" sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Box sx={{ mb: 1 }}>
        <SectionHeader
          title="Asset Details"
          description="Detailed view of your holdings with performance metrics, trends, and market news. Switch between Stocks and Crypto tabs to view different asset classes."
          variant="h4"
          tooltip="This section provides comprehensive information about each asset including position size, prices, profit/loss, ROI trends, and relevant market news. Use the view mode toggle in filters to switch between table, cards, or chart view."
        />
      </Box>
      <Stack direction="row" justifyContent="flex-end" alignItems="center">
        <Tooltip title="Switch between viewing stock holdings or cryptocurrency holdings. Each tab shows assets specific to that asset class." arrow>
          <Tabs
            value={tab}
            onChange={handleChange}
            sx={{
              '.MuiTabs-indicator': { display: 'none' },
              '.MuiButtonBase-root': {
                textTransform: 'none',
                px: 3,
                borderRadius: 2,
                color: 'text.secondary',
                fontWeight: 500,
              },
              '.Mui-selected': {
                backgroundColor: 'rgba(59, 130, 246, 0.12)',
                color: 'text.primary',
                fontWeight: 600,
              },
            }}
          >
            <Tab value="stocks" label="Stocks" />
            <Tab value="crypto" label="Crypto" />
          </Tabs>
        </Tooltip>
      </Stack>

      <AssetPanel
        data={activeData}
        accent={accent}
        viewMode={viewMode}
        issueLookup={assetIssueLookup}
        changeLookup={changeLookup}
      />
    </Box>
  );
};


