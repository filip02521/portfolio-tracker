import React, { useState, useEffect, useMemo } from 'react';
// @ts-ignore - react-plotly.js types are complex, using ts-ignore for now
import Plot from 'react-plotly.js';
import { Card, CardContent, Typography, Box, CircularProgress, Alert, FormControl, InputLabel, Select, MenuItem, useTheme } from '@mui/material';
import { portfolioService, Asset } from '../../services/portfolioService';
import { logger } from '../../utils/logger';
import { EmptyState } from '../common/EmptyState';

interface RiskReturnData {
  symbol: string;
  volatility: number;
  return: number;
  value: number;
  exchange: string;
  pnl_percent: number;
}

const RiskReturnBubble: React.FC = () => {
  const theme = useTheme();
  const [assets, setAssets] = useState<Asset[]>([]);
  const [performanceData, setPerformanceData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [colorBy, setColorBy] = useState<'exchange' | 'pnl'>('exchange');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [assetsData, perfData] = await Promise.all([
        portfolioService.getAssets(),
        portfolioService.getPerformanceAnalytics(30),
      ]);
      setAssets(assetsData);
      setPerformanceData(perfData);
    } catch (err: any) {
      logger.error('Error fetching risk-return data:', err);
      setError(err?.userMessage || 'Failed to load risk-return data');
    } finally {
      setLoading(false);
    }
  };

  const bubbleData = useMemo(() => {
    if (!assets || assets.length === 0 || !performanceData) return [];

    // Calculate volatility and return for each asset
    // For simplicity, we'll use P&L % as return proxy and estimate volatility
    // In a real implementation, you'd calculate these from historical data
    return assets.map((asset) => {
      // Use P&L % as a proxy for return
      const returnValue = asset.pnl_percent || 0;
      
      // Estimate volatility based on absolute P&L (simplified)
      // In production, calculate from historical price data
      const volatility = Math.abs(asset.pnl_percent) * 0.5; // Simplified estimate

      return {
        symbol: asset.symbol,
        volatility: Math.max(0, volatility),
        return: returnValue,
        value: asset.value_usd,
        exchange: asset.exchange,
        pnl_percent: asset.pnl_percent,
      } as RiskReturnData;
    });
  }, [assets, performanceData]);

  const exchanges = useMemo(() => {
    return Array.from(new Set(assets.map((a) => a.exchange)));
  }, [assets]);

  const plotData = useMemo(() => {
    if (bubbleData.length === 0) return [];

    const maxValue = Math.max(...bubbleData.map((d) => d.value));
    
    // Calculate colors based on colorBy setting
    const colors = colorBy === 'exchange' 
      ? (() => {
          const exchangeColors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe'];
          return bubbleData.map((d) => {
            const index = exchanges.indexOf(d.exchange);
            return exchangeColors[index % exchangeColors.length];
          });
        })()
      : bubbleData.map((d) => {
          if (d.pnl_percent >= 0) {
            return theme.palette.success.main;
          } else {
            return theme.palette.error.main;
          }
        });

    return [
      {
        x: bubbleData.map((d) => d.volatility),
        y: bubbleData.map((d) => d.return),
        mode: 'markers' as const,
        type: 'scatter' as const,
        text: bubbleData.map((d) => d.symbol),
        hovertemplate: '<b>%{text}</b><br>' +
          'Volatility: %{x:.2f}%<br>' +
          'Return: %{y:.2f}%<br>' +
          'Value: $%{customdata[0]:,.2f}<br>' +
          'Exchange: %{customdata[1]}<extra></extra>',
        customdata: bubbleData.map((d) => [d.value, d.exchange]),
        marker: {
          size: bubbleData.map((d) => Math.max(10, Math.sqrt(d.value / maxValue) * 40)),
          color: colors,
          opacity: 0.7,
          line: {
            color: theme.palette.divider,
            width: 1,
          },
        },
      },
    ];
  }, [bubbleData, colorBy, theme, exchanges]);

  const layout = useMemo(() => ({
    title: {
      text: 'Risk-Return Analysis',
      font: { size: 16, color: theme.palette.text.primary },
    },
    xaxis: {
      title: { text: 'Volatility (%)', font: { color: theme.palette.text.secondary } },
      tickfont: { color: theme.palette.text.secondary },
      gridcolor: theme.palette.divider,
      zeroline: false,
    },
    yaxis: {
      title: { text: 'Return (%)', font: { color: theme.palette.text.secondary } },
      tickfont: { color: theme.palette.text.secondary },
      gridcolor: theme.palette.divider,
      zeroline: true,
      zerolinecolor: theme.palette.divider,
    },
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { color: theme.palette.text.primary },
    showlegend: false,
    height: 500,
    margin: { l: 60, r: 20, t: 60, b: 60 },
  }), [theme]) as any;

  if (loading) {
    return (
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
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
          <Alert severity="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        </CardContent>
      </Card>
    );
  }

  if (bubbleData.length === 0) {
    return (
      <Card>
        <CardContent>
          <EmptyState type="analytics" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Risk-Return Bubble Chart
          </Typography>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Color By</InputLabel>
            <Select value={colorBy} label="Color By" onChange={(e) => setColorBy(e.target.value as 'exchange' | 'pnl')}>
              <MenuItem value="exchange">Exchange</MenuItem>
              <MenuItem value="pnl">P&L</MenuItem>
            </Select>
          </FormControl>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Bubble size = Position value, Position = Risk vs Return
        </Typography>
        <Box sx={{ width: '100%', overflow: 'auto' }}>
          <Plot
            data={plotData}
            layout={layout}
            config={{ displayModeBar: false, responsive: true }}
            style={{ width: '100%', height: '500px' }}
          />
        </Box>
        <Box sx={{ mt: 2, display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
          <Typography variant="caption" color="text.secondary">
            Higher return and lower volatility is better (top-left quadrant)
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default RiskReturnBubble;

