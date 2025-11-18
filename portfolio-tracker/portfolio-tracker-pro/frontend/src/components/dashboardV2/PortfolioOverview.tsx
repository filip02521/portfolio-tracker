import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  ToggleButtonGroup,
  ToggleButton,
  Stack,
  Chip,
  useTheme,
  Slider,
  Tooltip,
} from '@mui/material';
import {
  AreaChart,
  Area,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
  CartesianGrid,
  XAxis,
  YAxis,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  ReferenceLine,
} from 'recharts';
import {
  AllocationBreakdownData,
  EquityCurveConfig,
  SummaryModule,
} from './types';
import { dashboardPalette } from '../../theme/dashboardTokens';
import { SectionHeader } from '../common/SectionHeader';

export interface PortfolioOverviewProps {
  stocksSummary: SummaryModule;
  cryptoSummary: SummaryModule;
  allocation: AllocationBreakdownData;
  equityCurve: EquityCurveConfig;
  onEquityFilterChange: (filter: EquityCurveConfig['filter']) => void;
  onToggleBenchmark: (id: string) => void;
}

const MiniSparkline: React.FC<{ data: number[]; color: string }> = ({ data, color }) => {
  const points = data.map((value, index) => ({ index, value }));
  return (
    <ResponsiveContainer width="100%" height={64}>
      <AreaChart data={points}>
        <defs>
          <linearGradient id={`${color}-spark`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.4} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <Area
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={2}
          fill={`url(#${color}-spark)`}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
};

const SummaryCard: React.FC<{ module: SummaryModule }> = ({ module }) => {
  const accentColor = module.accent === 'stocks' ? dashboardPalette.stocksAccent : dashboardPalette.cryptoAccent;
  const tooltipText = module.accent === 'stocks' 
    ? `Total value of all stock holdings across all connected exchanges. Shows current value and percentage change over the selected time period.`
    : `Total value of all cryptocurrency holdings across all connected exchanges. Shows current value and percentage change over the selected time period.`;

  return (
    <Tooltip title={tooltipText} arrow placement="top">
      <Card variant="outlined" sx={{ height: '100%', borderRadius: 2 }}>
        <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, p: 3.5 }}>
          <Box>
            <Typography variant="overline" sx={{ letterSpacing: 0.5, color: 'text.secondary', fontSize: '0.75rem', fontWeight: 600 }}>
              {module.title}
            </Typography>
            <Typography variant="h4" sx={{ fontWeight: 700, mt: 1, lineHeight: 1.2, fontSize: { xs: '1.75rem', md: '2rem' } }}>
              {module.value}
            </Typography>
            <Stack direction="row" spacing={1} alignItems="center" sx={{ mt: 1.5 }}>
              <Chip
                size="small"
                label={`${module.changePercent >= 0 ? '+' : ''}${module.changePercent.toFixed(2)}%`}
                sx={{
                  fontWeight: 600,
                  color: '#fff',
                  backgroundColor: module.changePercent >= 0 ? dashboardPalette.accent.positive : dashboardPalette.accent.negative,
                  borderRadius: 1.5,
                  height: 26,
                  fontSize: '0.8125rem',
                }}
              />
              <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.8125rem', fontWeight: 500 }}>
                {module.changeLabel}
              </Typography>
            </Stack>
          </Box>
          <MiniSparkline data={module.trend} color={accentColor} />
        </CardContent>
      </Card>
    </Tooltip>
  );
};

const AllocationBreakdown: React.FC<{ allocation: AllocationBreakdownData }> = ({ allocation }) => {
  const [tab, setTab] = React.useState<'all' | 'class'>('all');
  const data = tab === 'all' ? allocation.all : allocation.byAssetClass;

  return (
    <Card variant="outlined" sx={{ height: '100%', borderRadius: 2 }}>
      <CardContent sx={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 2.5, p: 3.5 }}>
        <Box sx={{ mb: 1 }}>
          <SectionHeader
            title="Allocation Breakdown"
            description="Portfolio allocation by individual assets or asset classes. Use the tabs to switch between views."
            tooltip={tab === 'all' 
              ? "Shows percentage allocation for each individual asset in your portfolio. Useful for identifying concentration in specific holdings."
              : "Shows percentage allocation grouped by asset class (Stocks, Crypto, etc.). Useful for understanding overall portfolio composition."}
          />
        </Box>
        <Stack direction="row" justifyContent="flex-end" alignItems="center" sx={{ mb: 1 }}>
          <Tooltip title={tab === 'all' ? "View allocation by individual assets" : "View allocation grouped by asset class"} arrow>
            <Tabs
              value={tab}
              onChange={(_, newValue) => setTab(newValue)}
              sx={{
                minHeight: 36,
                '& .MuiTabs-flexContainer': { gap: 1 },
                '& .MuiTab-root': {
                  minHeight: 36,
                  borderRadius: 2.5,
                  textTransform: 'none',
                  fontSize: '0.875rem',
                  px: 2,
                },
              }}
            >
              <Tab value="all" label="All" />
              <Tab value="class" label="By Asset Class" />
            </Tabs>
          </Tooltip>
        </Stack>

        <Box sx={{ flexGrow: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
          <Box sx={{ width: 220, height: 220, minWidth: 0, minHeight: 0 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data}
                  innerRadius="65%"
                  outerRadius="90%"
                  paddingAngle={3}
                  dataKey="value"
                >
                  {data.map((slice) => (
                    <Cell key={slice.label} fill={slice.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </Box>
          <Stack spacing={1.5} sx={{ minWidth: 180, flexGrow: 1 }}>
            {data.map((slice) => (
              <Stack key={slice.label} direction="row" spacing={1.5} alignItems="center" justifyContent="space-between">
                <Stack direction="row" spacing={1.5} alignItems="center">
                  <Box sx={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: slice.color }} />
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {slice.label}
                  </Typography>
                </Stack>
                <Typography variant="body2" color="text.secondary">
                  {slice.value.toFixed(1)}%
                </Typography>
              </Stack>
            ))}
          </Stack>
        </Box>
      </CardContent>
    </Card>
  );
};

type EquityTooltipPayload = {
  value?: number;
  stocks?: number;
  crypto?: number;
  comparisonValue?: number;
} & Record<string, any>;

const LegendItem: React.FC<{
  color: string;
  label: string;
  pattern?: 'solid' | 'dashed' | 'dotted';
}> = ({ color, label, pattern = 'solid' }) => {
  const borderStyle =
    pattern === 'dashed' ? '4px 4px' : pattern === 'dotted' ? '2px 4px' : 'none';

  return (
    <Stack direction="row" spacing={1} alignItems="center">
      <Box
        sx={{
          width: 20,
          height: 3,
          borderRadius: 2.5,
          backgroundColor: borderStyle === 'none' ? color : 'transparent',
          border: borderStyle !== 'none' ? `2px ${pattern === 'dotted' ? 'dotted' : 'dashed'} ${color}` : 'none',
        }}
      />
      <Typography variant="caption" sx={{ fontWeight: 600, color: 'text.secondary' }}>
        {label}
      </Typography>
    </Stack>
  );
};

const BenchmarkPanel: React.FC<{
  benchmarks: EquityCurveConfig['benchmarks'];
  chartData: Array<{ benchmarkValues?: Record<string, number> }>;
}> = ({ benchmarks, chartData }) => {
  const activeBenchmarks = benchmarks.filter((b) => b.active);

  const benchmarkSummaries = React.useMemo(() => {
    if (activeBenchmarks.length === 0 || chartData.length < 2) {
      return [];
    }

    const first = chartData[0];
    const last = chartData[chartData.length - 1];

    return activeBenchmarks.map((benchmark) => {
      const firstValue = first?.benchmarkValues?.[benchmark.id];
      const lastValue = last?.benchmarkValues?.[benchmark.id];

      if (firstValue === undefined || lastValue === undefined) {
        return null;
      }

      const change = lastValue - firstValue;
      const changePercent = firstValue > 0 ? (change / firstValue) * 100 : 0;

      return {
        id: benchmark.id,
        label: benchmark.label,
        color: benchmark.color,
        latestValue: lastValue,
        change,
        changePercent,
      };
    }).filter((summary): summary is NonNullable<typeof summary> => summary !== null);
  }, [activeBenchmarks, chartData]);

  if (benchmarkSummaries.length === 0) {
    return null;
  }

  return (
    <Box
      sx={{
        p: 1.5,
        borderRadius: 2,
        backgroundColor: (theme) =>
          theme.palette.mode === 'dark' ? 'rgba(15, 23, 42, 0.4)' : 'rgba(148, 163, 184, 0.08)',
        border: (theme) => `1px solid ${theme.palette.divider}`,
      }}
    >
      <Typography variant="caption" sx={{ textTransform: 'uppercase', letterSpacing: 0.4, color: 'text.secondary', mb: 1.5, display: 'block' }}>
        Benchmarks
      </Typography>
      <Stack spacing={1.25}>
        {benchmarkSummaries.map((summary) => (
          <Stack key={summary.id} direction="row" justifyContent="space-between" alignItems="center" spacing={1.5}>
            <Stack direction="row" spacing={1} alignItems="center">
              <Box
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  backgroundColor: summary.color,
                }}
              />
              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                {summary.label}
              </Typography>
            </Stack>
            <Stack direction="row" spacing={1} alignItems="center">
              <Typography variant="body2" color="text.secondary">
                ${summary.latestValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </Typography>
              <Chip
                size="small"
                label={`${summary.changePercent >= 0 ? '+' : ''}${summary.changePercent.toFixed(2)}%`}
                sx={{
                  fontWeight: 600,
                  fontSize: '0.75rem',
                  height: 20,
                  backgroundColor: summary.changePercent >= 0 ? dashboardPalette.accent.positive : dashboardPalette.accent.negative,
                  color: '#fff',
                }}
              />
            </Stack>
          </Stack>
        ))}
      </Stack>
    </Box>
  );
};

const EquityCurve: React.FC<{
  config: EquityCurveConfig;
  onFilterChange: (filter: EquityCurveConfig['filter']) => void;
  onToggleBenchmark: (id: string) => void;
}> = ({ config, onFilterChange, onToggleBenchmark }) => {
  const theme = useTheme();
  const [comparisonMode, setComparisonMode] = React.useState<'current' | 'previous'>('current');
  const comparisonActive =
    comparisonMode === 'previous' && Array.isArray(config.previousPoints) && config.previousPoints.length > 0;

  const chartData = React.useMemo(() => {
    if (!comparisonActive || !config.previousPoints) {
      return config.points.map((point, index) => ({
        ...point,
        index,
      }));
    }
    const previous = config.previousPoints;
    const maxLength = Math.min(previous.length, config.points.length);
    return config.points.slice(config.points.length - maxLength).map((point, index) => ({
      ...point,
      index,
      comparisonValue: previous[previous.length - maxLength + index]?.value ?? null,
    }));
  }, [comparisonActive, config.points, config.previousPoints]);

  const tooltipFormatter = React.useCallback(
    (value: number | string | Array<number | string>, name: string) => {
      if (typeof value !== 'number') {
        return value;
      }
      return [`$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`, name];
    },
    []
  );

  const tooltipLabelFormatter = React.useCallback((label: string) => label, []);

  const tooltipContent = React.useCallback(
    ({ active, payload, label }: any) => {
      if (!active || !payload || !payload.length) {
        return null;
      }

      const makeRow = (entry: any, text: string, color: string, bold = false) => (
        <Stack
          key={`${entry?.dataKey || text}`}
          direction="row"
          alignItems="center"
          justifyContent="space-between"
          spacing={1.25}
        >
          <Stack direction="row" spacing={1} alignItems="center">
            <Box
              sx={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: color,
                boxShadow: `0 0 0 1px ${color === 'transparent' ? 'rgba(148,163,184,0.4)' : color}`,
              }}
            />
            <Typography variant="body2" sx={{ fontWeight: bold ? 600 : 500 }}>
              {text}
            </Typography>
          </Stack>
          <Typography variant="body2" sx={{ fontWeight: bold ? 600 : 500 }}>
            {tooltipFormatter(entry?.value ?? 0, '')[0]}
          </Typography>
        </Stack>
      );

      const primary = payload.find((entry: any) => entry.dataKey === 'value');
      const stocks = payload.find((entry: any) => entry.dataKey === 'stocks');
      const crypto = payload.find((entry: any) => entry.dataKey === 'crypto');
      const comparison = payload.find((entry: any) => entry.dataKey === 'comparisonValue');
      const benchmarksPayload = payload.filter((entry: any) => entry.dataKey?.startsWith('benchmarkValues.'));

      return (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.25 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
            {label}
          </Typography>
          <Stack spacing={0.75}>
            {primary && makeRow(primary, 'Total', dashboardPalette.primary, true)}
            {stocks && makeRow(stocks, 'Stocks', dashboardPalette.stocksAccent)}
            {crypto && makeRow(crypto, 'Crypto', dashboardPalette.cryptoAccent)}
            {comparison && makeRow(comparison, 'Previous', theme.palette.text.secondary)}
          </Stack>
          {benchmarksPayload.length > 0 && (
            <Box sx={{ pt: 0.5, borderTop: `1px solid rgba(148, 163, 184, 0.24)` }}>
              <Typography variant="caption" sx={{ textTransform: 'uppercase', letterSpacing: 0.4, color: 'text.secondary' }}>
                Benchmarks
              </Typography>
              <Stack spacing={0.75} sx={{ mt: 0.75 }}>
                {benchmarksPayload.map((entry: any) =>
                  makeRow(entry, entry.name || entry.dataKey.split('.').pop(), entry.color || 'rgba(148,163,184,0.8)')
                )}
              </Stack>
            </Box>
          )}
        </Box>
      );
    },
    [tooltipFormatter]
  );

  const legendItems = React.useMemo(() => {
    const base: Array<{ color: string; label: string; pattern: 'solid' | 'dashed' | 'dotted' }> = [
      { color: dashboardPalette.primary, label: 'Total', pattern: 'solid' },
    ];
    if (config.filter !== 'crypto') {
      base.push({ color: dashboardPalette.stocksAccent, label: 'Stocks', pattern: 'dashed' });
    }
    if (config.filter !== 'stocks') {
      base.push({ color: dashboardPalette.cryptoAccent, label: 'Crypto', pattern: 'dotted' });
    }
    if (comparisonActive) {
      base.push({
        color: theme.palette.mode === 'dark' ? '#94A3B8' : '#64748B',
        label: 'Prev period',
        pattern: 'dashed',
      });
    }
    return base;
  }, [comparisonActive, config.filter, theme.palette.mode]);

  const narrativeBadge = React.useMemo(() => {
    if (chartData.length < 2) {
      return null;
    }

    const first = chartData[0];
    const last = chartData[chartData.length - 1];
    const portfolioChange = last.value - first.value;
    const portfolioChangePercent = first.value > 0 ? (portfolioChange / first.value) * 100 : 0;

    const parts: string[] = [];
    
    if (config.comparison) {
      const comparisonPercent = config.comparison.deltaPercent;
      if (Math.abs(comparisonPercent) > 0.1) {
        parts.push(
          `Portfolio ${portfolioChangePercent >= 0 ? 'gained' : 'lost'} ${Math.abs(portfolioChangePercent).toFixed(1)}%`
        );
        const vsComparison = portfolioChangePercent - comparisonPercent;
        if (Math.abs(vsComparison) > 0.5) {
          parts.push(
            `${vsComparison >= 0 ? 'outperforming' : 'underperforming'} previous period by ${Math.abs(vsComparison).toFixed(1)}%`
          );
        }
      }
    } else {
      parts.push(
        `Portfolio ${portfolioChangePercent >= 0 ? 'up' : 'down'} ${Math.abs(portfolioChangePercent).toFixed(1)}%`
      );
    }

    const activeBenchmarks = config.benchmarks.filter((b) => b.active);
    if (activeBenchmarks.length > 0 && last.benchmarkValues) {
      const benchmarkComparisons = activeBenchmarks
        .map((benchmark) => {
          const firstBench = first?.benchmarkValues?.[benchmark.id];
          const lastBench = last?.benchmarkValues?.[benchmark.id];
          if (firstBench === undefined || lastBench === undefined) {
            return null;
          }
          const benchChange = firstBench > 0 ? ((lastBench - firstBench) / firstBench) * 100 : 0;
          const diff = portfolioChangePercent - benchChange;
          return { label: benchmark.label, diff };
        })
        .filter((comp): comp is NonNullable<typeof comp> => comp !== null);

      if (benchmarkComparisons.length > 0) {
        const bestBench = benchmarkComparisons.reduce((best, current) =>
          Math.abs(current.diff) > Math.abs(best.diff) ? current : best
        );
        if (Math.abs(bestBench.diff) > 1) {
          parts.push(
            `${bestBench.diff >= 0 ? 'beating' : 'trailing'} ${bestBench.label} by ${Math.abs(bestBench.diff).toFixed(1)}%`
          );
        }
      }
    }

    return parts.length > 0 ? parts.join(', ') : null;
  }, [chartData, config.comparison, config.benchmarks]);

  const yAxisDomain = React.useMemo(() => {
    if (chartData.length === 0) {
      return undefined;
    }

    const values: number[] = [];
    chartData.forEach((point) => {
      if (config.filter === 'stocks' && point.stocks !== undefined) {
        values.push(point.stocks);
      } else if (config.filter === 'crypto' && point.crypto !== undefined) {
        values.push(point.crypto);
      } else {
        values.push(point.value);
      }
    });

    if (values.length === 0) {
      return undefined;
    }

    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min;
    const padding = range * 0.1;

    return [Math.max(0, min - padding), max + padding];
  }, [chartData, config.filter]);

  const anomalies = React.useMemo(() => {
    if (chartData.length < 2) {
      return [];
    }

    const threshold = 0.15;
    const detected: Array<{ index: number; date: string; changePercent: number; value: number }> = [];

    for (let i = 1; i < chartData.length; i++) {
      const prev = chartData[i - 1];
      const curr = chartData[i];

      const prevValue = config.filter === 'stocks' 
        ? (prev.stocks ?? prev.value)
        : config.filter === 'crypto'
        ? (prev.crypto ?? prev.value)
        : prev.value;
      
      const currValue = config.filter === 'stocks'
        ? (curr.stocks ?? curr.value)
        : config.filter === 'crypto'
        ? (curr.crypto ?? curr.value)
        : curr.value;

      if (prevValue > 0) {
        const changePercent = Math.abs((currValue - prevValue) / prevValue);
        if (changePercent >= threshold) {
          detected.push({
            index: i,
            date: curr.date,
            changePercent: ((currValue - prevValue) / prevValue) * 100,
            value: currValue,
          });
        }
      }
    }

    return detected;
  }, [chartData, config.filter]);

  return (
    <Card variant="outlined" sx={{ height: '100%', borderRadius: 2 }}>
      <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, height: '100%', p: 3.5 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems={{ xs: 'flex-start', md: 'center' }} justifyContent="space-between">
          <Box>
            <SectionHeader
              title="Total Equity Curve"
              description="Track portfolio value over time and compare with benchmarks. Use filters to view total, stocks only, or crypto only."
              tooltip="The equity curve shows how your portfolio value has changed over the selected time period. You can compare it with benchmarks like S&P 500, BTC, or ETH to see relative performance."
            />
          </Box>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} alignItems={{ xs: 'flex-start', sm: 'center' }}>
            <Tooltip title="Filter the equity curve to show total portfolio value, stocks only, or crypto only. This helps analyze performance by asset class." arrow>
              <span>
                <ToggleButtonGroup
                  exclusive
                  size="small"
                  value={config.filter}
                  onChange={(_, nextValue) => {
                    if (nextValue) {
                      onFilterChange(nextValue);
                    }
                  }}
                  sx={{
                    backgroundColor: theme.palette.mode === 'dark' ? 'rgba(15, 23, 42, 0.6)' : 'rgba(148, 163, 184, 0.12)',
                    borderRadius: 2.5,
                    p: 0.5,
                    '.MuiToggleButton-root': {
                      border: 'none',
                      textTransform: 'none',
                      borderRadius: 2.5,
                      px: 2,
                      py: 0.75,
                      minHeight: 36,
                      fontWeight: 500,
                      '&.Mui-selected': {
                        color: theme.palette.getContrastText(dashboardPalette.primary),
                        backgroundColor: dashboardPalette.primary,
                        fontWeight: 600,
                      },
                    },
                  }}
                >
                  <ToggleButton value="total">Total</ToggleButton>
                  <ToggleButton value="stocks">Stocks only</ToggleButton>
                  <ToggleButton value="crypto">Crypto only</ToggleButton>
                </ToggleButtonGroup>
              </span>
            </Tooltip>

            <Tooltip title="Compare current period performance with the previous equivalent period. This helps identify trends and seasonal patterns." arrow>
              <Box sx={{ minWidth: 160, px: 1 }}>
                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
                  Comparison
                </Typography>
                <Slider
                  value={comparisonMode === 'previous' ? 1 : 0}
                  min={0}
                  max={1}
                  step={1}
                  onChange={(_, value) => setComparisonMode(value === 1 ? 'previous' : 'current')}
                  marks={[
                    { value: 0, label: 'Current' },
                    { value: 1, label: 'Prev period' },
                  ]}
                  sx={{ mt: 1 }}
                />
              </Box>
            </Tooltip>

            <Tooltip title="Toggle benchmark overlays on the chart. Benchmarks help compare your portfolio performance against market indices like S&P 500, BTC, or ETH." arrow>
              <Stack direction="row" spacing={1} flexWrap="wrap">
                {config.benchmarks.map((benchmark) => (
                  <Tooltip key={benchmark.id} title={`${benchmark.active ? 'Hide' : 'Show'} ${benchmark.label} benchmark on chart`} arrow>
                    <Chip
                      clickable
                      onClick={() => onToggleBenchmark(benchmark.id)}
                      label={benchmark.label}
                      variant={benchmark.active ? 'filled' : 'outlined'}
                      sx={{
                        borderRadius: 2,
                        fontSize: '0.8125rem',
                        fontWeight: benchmark.active ? 600 : 500,
                        backgroundColor: benchmark.active ? benchmark.color : 'transparent',
                        color: benchmark.active ? theme.palette.getContrastText(benchmark.color) : 'text.secondary',
                        cursor: 'pointer',
                      }}
                    />
                  </Tooltip>
                ))}
              </Stack>
            </Tooltip>
          </Stack>
        </Stack>

        {config.comparison && (
          <Tooltip title={`Portfolio performance compared to ${config.comparison.label}. ${config.comparison.deltaValue >= 0 ? 'Outperforming' : 'Underperforming'} by ${config.comparison.formattedDeltaPercent}.`} arrow>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5} alignItems={{ xs: 'flex-start', md: 'center' }}>
              <Chip
                label={`${config.comparison.formattedDeltaValue} (${config.comparison.formattedDeltaPercent})`}
                color={config.comparison.deltaValue >= 0 ? 'success' : 'error'}
                sx={{ fontWeight: 600 }}
              />
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
                vs {config.comparison.label}
              </Typography>
            </Stack>
          </Tooltip>
        )}

        {narrativeBadge && (
          <Tooltip title="Summary of portfolio performance based on current data. This narrative provides a quick overview of how your portfolio is performing relative to benchmarks and previous periods." arrow>
            <Box
              sx={{
                p: 2,
                borderRadius: 2,
                backgroundColor: (theme) =>
                  theme.palette.mode === 'dark' ? 'rgba(59, 130, 246, 0.1)' : 'rgba(59, 130, 246, 0.05)',
                border: (theme) => `1px solid ${theme.palette.mode === 'dark' ? 'rgba(59, 130, 246, 0.3)' : 'rgba(59, 130, 246, 0.2)'}`,
                cursor: 'help',
              }}
            >
              <Typography variant="body2" sx={{ fontWeight: 500, color: 'text.primary', lineHeight: 1.6 }}>
                {narrativeBadge}
              </Typography>
            </Box>
          </Tooltip>
        )}

        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '1fr 200px' }, gap: 2 }}>
          <Box sx={{ flexGrow: 1, minHeight: { xs: 240, md: 280 }, minWidth: 0 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <defs>
                <linearGradient id="equity-primary" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={dashboardPalette.primary} stopOpacity={0.32} />
                  <stop offset="100%" stopColor={dashboardPalette.primary} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.18)" />
              <XAxis dataKey="date" stroke={theme.palette.text.secondary} />
              <YAxis
                stroke={theme.palette.text.secondary}
                tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                domain={yAxisDomain}
              />
              <RechartsTooltip
                content={tooltipContent}
                formatter={tooltipFormatter}
                labelFormatter={tooltipLabelFormatter}
                wrapperStyle={{
                  borderRadius: 2,
                  border: `1px solid ${theme.palette.divider}`,
                  boxShadow: theme.palette.mode === 'dark'
                    ? '0 12px 28px rgba(15, 23, 42, 0.45)'
                    : '0 12px 28px rgba(15, 23, 42, 0.18)',
                }}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke={dashboardPalette.primary}
                strokeWidth={2.5}
                dot={false}
                fill="url(#equity-primary)"
              />
              {config.filter !== 'crypto' && (
                <Line
                  type="monotone"
                  dataKey="stocks"
                  stroke={dashboardPalette.stocksAccent}
                  strokeWidth={1.75}
                  dot={false}
                  strokeDasharray="5 5"
                />
              )}
              {config.filter !== 'stocks' && (
                <Line
                  type="monotone"
                  dataKey="crypto"
                  stroke={dashboardPalette.cryptoAccent}
                  strokeWidth={1.75}
                  dot={false}
                  strokeDasharray="2 4"
                />
              )}
              {config.benchmarks
                .filter((benchmark) => benchmark.active)
                .map((benchmark) => (
                  <Line
                    key={benchmark.id}
                    type="monotone"
                    dataKey={`benchmarkValues.${benchmark.id}`}
                    stroke={benchmark.color}
                    strokeWidth={1.4}
                    dot={false}
                  />
                ))}
              {comparisonActive && (
                <Line
                  type="monotone"
                  dataKey="comparisonValue"
                  stroke={theme.palette.mode === 'dark' ? '#94A3B8' : '#64748B'}
                  strokeWidth={1.5}
                  dot={false}
                  strokeDasharray="6 4"
                />
              )}
              {anomalies.map((anomaly) => {
                const point = chartData[anomaly.index];
                if (!point) return null;
                return (
                  <ReferenceLine
                    key={`anomaly-${anomaly.index}`}
                    x={point.date}
                    stroke={anomaly.changePercent >= 0 ? dashboardPalette.accent.positive : dashboardPalette.accent.negative}
                    strokeWidth={2}
                    strokeDasharray="4 4"
                    label={{
                      value: `${anomaly.changePercent >= 0 ? '+' : ''}${anomaly.changePercent.toFixed(1)}%`,
                      position: 'top',
                      fill: anomaly.changePercent >= 0 ? dashboardPalette.accent.positive : dashboardPalette.accent.negative,
                      fontSize: 10,
                      fontWeight: 600,
                    }}
                  />
                );
              })}
            </LineChart>
          </ResponsiveContainer>
          </Box>
          <Box sx={{ display: { xs: 'none', lg: 'block' } }}>
            <BenchmarkPanel benchmarks={config.benchmarks} chartData={chartData} />
          </Box>
        </Box>
        {config.benchmarks.filter((b) => b.active).length > 0 && (
          <Box sx={{ display: { xs: 'block', lg: 'none' } }}>
            <BenchmarkPanel benchmarks={config.benchmarks} chartData={chartData} />
          </Box>
        )}
        {legendItems.length > 0 && (
          <Stack direction="row" spacing={2} flexWrap="wrap" sx={{ pt: 1 }}>
            {legendItems.map((item) => (
              <LegendItem key={item.label} color={item.color} label={item.label} pattern={item.pattern} />
            ))}
          </Stack>
        )}
      </CardContent>
    </Card>
  );
};

export const PortfolioOverview: React.FC<PortfolioOverviewProps> = ({
  stocksSummary,
  cryptoSummary,
  allocation,
  equityCurve,
  onEquityFilterChange,
  onToggleBenchmark,
}) => {
  return (
    <Box component="section" aria-label="Portfolio Overview" sx={{ display: 'flex', flexDirection: 'column', gap: { xs: 3.5, md: 4.5 } }}>
      <Box sx={{ mb: 1 }}>
        <SectionHeader
          title="Portfolio Overview"
          description="Summary of your portfolio value, allocation, and performance over time. Use the equity curve to track value changes and compare with benchmarks."
          variant="h4"
        />
      </Box>
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', md: 'repeat(2, minmax(0, 1fr))' },
          gap: { xs: 2.5, md: 3 },
        }}
      >
        <Box>
          <SummaryCard module={stocksSummary} />
        </Box>
        <Box>
          <SummaryCard module={cryptoSummary} />
        </Box>
      </Box>

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', md: 'minmax(0, 1fr) minmax(0, 2fr)' },
          gap: { xs: 2.5, md: 3.5 },
        }}
      >
        <Box>
          <AllocationBreakdown allocation={allocation} />
        </Box>
        <Box>
          <EquityCurve
            config={equityCurve}
            onFilterChange={onEquityFilterChange}
            onToggleBenchmark={onToggleBenchmark}
          />
        </Box>
      </Box>
    </Box>
  );
};


