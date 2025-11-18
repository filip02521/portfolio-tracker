import React, { useState, useMemo } from 'react';
import { Card, CardContent, Typography, Box, Button, ButtonGroup, CircularProgress, Alert, useTheme } from '@mui/material';
import { ZoomIn, ZoomOut, Refresh } from '@mui/icons-material';
import { LineChart, Line, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Brush, ReferenceLine } from 'recharts';
import { portfolioService, PortfolioHistoryPoint } from '../../services/portfolioService';
import { logger } from '../../utils/logger';
import { EmptyState } from '../common/EmptyState';

interface InteractivePerformanceChartProps {
  days?: number;
  height?: number;
  showBrush?: boolean;
}

const InteractivePerformanceChart: React.FC<InteractivePerformanceChartProps> = ({
  days = 30,
  height = 400,
  showBrush = true,
}) => {
  const theme = useTheme();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [historyData, setHistoryData] = useState<PortfolioHistoryPoint[]>([]);
  const [benchmarkData, setBenchmarkData] = useState<any[]>([]);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [brushStart, setBrushStart] = useState(0);
  const [brushEnd, setBrushEnd] = useState(100);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [portfolioHistory, benchmark] = await Promise.all([
        portfolioService.getPortfolioHistory(days, true),
        portfolioService.getBenchmarkHistory('SPY', days).catch(() => []),
      ]);

      setHistoryData(portfolioHistory);
      setBenchmarkData(benchmark);
    } catch (err: any) {
      logger.error('Error fetching performance data:', err);
      setError(err?.userMessage || 'Failed to load performance data');
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    fetchData();
  }, [days]);

  const chartData = useMemo(() => {
    if (!historyData || historyData.length === 0) return [];

    // Normalize data to base value
    const baseValue = historyData[0]?.value_usd || 1;
    
    // Create benchmark map
    const benchmarkMap = new Map<string, number>();
    if (benchmarkData && benchmarkData.length > 0) {
      benchmarkData.forEach((point) => {
        const dateKey = new Date(point.date).toISOString().split('T')[0];
        benchmarkMap.set(dateKey, point.normalized_value || point.value);
      });
    }

    return historyData.map((point) => {
      const dateKey = new Date(point.date).toISOString().split('T')[0];
      const portfolioNormalized = baseValue > 0 ? ((point.value_usd / baseValue) * 100) : 100;
      const benchmarkNormalized = benchmarkMap.get(dateKey) || null;

      return {
        date: new Date(point.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        fullDate: point.date,
        portfolio: portfolioNormalized,
        benchmark: benchmarkNormalized,
        value_usd: point.value_usd,
      };
    });
  }, [historyData, benchmarkData]);

  const displayedData = useMemo(() => {
    if (!showBrush || chartData.length === 0) return chartData;
    
    const startIndex = Math.floor((brushStart / 100) * chartData.length);
    const endIndex = Math.ceil((brushEnd / 100) * chartData.length);
    return chartData.slice(startIndex, endIndex);
  }, [chartData, brushStart, brushEnd, showBrush]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const handleZoomIn = () => {
    setZoomLevel((prev) => Math.min(prev + 0.2, 2));
  };

  const handleZoomOut = () => {
    setZoomLevel((prev) => Math.max(prev - 0.2, 0.5));
  };

  const handleBrushChange = (domain: any) => {
    if (domain && domain.startIndex !== undefined && domain.endIndex !== undefined) {
      const totalLength = chartData.length;
      setBrushStart((domain.startIndex / totalLength) * 100);
      setBrushEnd((domain.endIndex / totalLength) * 100);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: height }}>
            <CircularProgress />
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent>
          <Alert severity="error" onClose={() => setError(null)} action={<Button onClick={fetchData} startIcon={<Refresh />}>Retry</Button>}>
            {error}
          </Alert>
        </CardContent>
      </Card>
    );
  }

  if (chartData.length === 0) {
    return (
      <Card>
        <CardContent>
          <EmptyState type="performance" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Interactive Performance Chart
          </Typography>
          <ButtonGroup size="small">
            <Button onClick={handleZoomOut} startIcon={<ZoomOut />} disabled={zoomLevel <= 0.5}>
              Zoom Out
            </Button>
            <Button onClick={handleZoomIn} startIcon={<ZoomIn />} disabled={zoomLevel >= 2}>
              Zoom In
            </Button>
            <Button onClick={fetchData} startIcon={<Refresh />}>
              Refresh
            </Button>
          </ButtonGroup>
        </Box>
        <Box sx={{ height: height, mb: showBrush ? 2 : 0 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={displayedData}>
              <defs>
                <linearGradient id="portfolioGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#2563EB" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#2563EB" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
              <XAxis
                dataKey="date"
                stroke={theme.palette.text.secondary}
                tick={{ fontSize: 11, fill: theme.palette.text.secondary }}
                interval="preserveStartEnd"
                minTickGap={40}
              />
              <YAxis
                stroke={theme.palette.text.secondary}
                tick={{ fontSize: 12, fill: theme.palette.text.secondary }}
                tickFormatter={(value) => `${(value - 100).toFixed(0)}%`}
                domain={['auto', 'auto']}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: theme.palette.mode === 'dark' ? 'rgba(45, 55, 72, 0.98)' : 'rgba(255, 255, 255, 0.98)',
                  border: `1px solid ${theme.palette.divider}`,
                  borderRadius: '12px',
                  padding: '12px 16px',
                  fontSize: 14,
                  boxShadow: '0 8px 24px rgba(0, 0, 0, 0.2)',
                }}
                labelStyle={{
                  color: theme.palette.text.primary,
                  fontWeight: 600,
                  marginBottom: '4px',
                }}
                formatter={(value: number, name: string, props: any) => {
                  if (name === 'portfolio' || name === 'benchmark') {
                    return [`${(value - 100).toFixed(2)}%`, name === 'portfolio' ? 'Portfolio' : 'Benchmark'];
                  }
                  return [formatCurrency(props.payload.value_usd), 'Value'];
                }}
              />
              <ReferenceLine y={100} stroke={theme.palette.divider} strokeDasharray="2 2" />
              <Area
                type="monotone"
                dataKey="portfolio"
                fill="url(#portfolioGradient)"
                stroke="none"
              />
              <Line
                type="monotone"
                dataKey="portfolio"
                stroke="#2563EB"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 5 }}
              />
              {benchmarkData.length > 0 && (
                <Line
                  type="monotone"
                  dataKey="benchmark"
                  stroke="#764ba2"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={false}
                  activeDot={{ r: 5 }}
                />
              )}
              {showBrush && (
                <Brush
                  dataKey="date"
                  height={30}
                  stroke={theme.palette.primary.main}
                  fill={theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'}
                  onChange={handleBrushChange}
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        </Box>
        <Typography variant="caption" color="text.secondary">
          Click and drag on the brush below to zoom into specific time periods. Values are normalized to start at 100%.
        </Typography>
      </CardContent>
    </Card>
  );
};

export default InteractivePerformanceChart;














