import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Stack,
  MenuItem,
  TextField,
  Chip,
  Alert,
  useTheme,
  LinearProgress,
  Tooltip,
} from '@mui/material';
import {
  BarChart,
  Bar,
  ResponsiveContainer,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  LineChart,
  Line,
  Cell,
} from 'recharts';
import { RoiAnalyticsData } from './types';
import { dashboardPalette } from '../../theme/dashboardTokens';
import { SectionHeader } from '../common/SectionHeader';

export interface RoiAnalyticsProps {
  data: RoiAnalyticsData;
  onSelectAsset: (symbol: string) => void;
}

const RoiContributionChart: React.FC<{
  globalPL: number;
  contributions: RoiAnalyticsData['contributions'];
}> = ({ globalPL, contributions }) => {
  const theme = useTheme();
  return (
    <Card variant="outlined" sx={{ height: '100%', borderRadius: 2 }}>
      <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, height: '100%', p: 3.5 }}>
        <Box sx={{ mb: 1 }}>
          <SectionHeader
            title="ROI & P/L Contributions"
            description="Global portfolio return with breakdown showing how each asset contributes to total profit or loss."
            tooltip="This chart shows your total portfolio return (global P/L) and how each asset contributes. Positive bars indicate assets that increased portfolio value, negative bars show assets that decreased it. Bar height represents contribution percentage."
          />
        </Box>
        <Box>
          <Typography variant="h3" sx={{ fontWeight: 700 }}>
            {globalPL >= 0 ? '+' : ''}
            {globalPL.toFixed(2)}%
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Total return
          </Typography>
        </Box>
        <Box sx={{ flexGrow: 1, minHeight: 220, minWidth: 0 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={contributions}>
              <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
              <XAxis dataKey="asset" axisLine={false} tickLine={false} />
              <YAxis axisLine={false} tickLine={false} tickFormatter={(value) => `${value.toFixed(1)}%`} />
              <RechartsTooltip
                formatter={(value: number) => [`${value.toFixed(2)}%`, 'Contribution']}
                contentStyle={{
                  backgroundColor: theme.palette.background.paper,
                  borderRadius: 2,
                  border: `1px solid ${theme.palette.divider}`,
                  padding: '12px 16px',
                }}
              />
              <Bar dataKey="contribution" radius={[8, 8, 0, 0]} minPointSize={3}>
                {contributions.map((entry) => (
                  <Cell key={entry.asset} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Box>
      </CardContent>
    </Card>
  );
};

const TopMoversList: React.FC<{
  title: string;
  movers: RoiAnalyticsData['topGainers'];
}> = ({ title, movers }) => {
  const isGainers = title.includes('Gainers');
  const tooltipText = isGainers
    ? 'Assets with the highest positive returns. These are your best performing holdings contributing most to portfolio gains.'
    : 'Assets with the lowest returns or losses. These holdings are dragging down portfolio performance and may need review.';
  
  return (
    <Card variant="outlined" sx={{ borderRadius: 2 }}>
      <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, p: 3.5 }}>
        <Box sx={{ mb: 1 }}>
          <SectionHeader
            title={title}
            description={isGainers 
              ? 'Assets with the highest positive returns contributing to portfolio gains.'
              : 'Assets with the lowest returns or losses impacting portfolio performance.'}
            tooltip={tooltipText}
          />
        </Box>
        <Stack spacing={1.5}>
          {movers.map((mover) => (
            <Stack
              key={mover.asset}
              direction="row"
              justifyContent="space-between"
              alignItems="center"
            >
              <Stack direction="row" spacing={1.5} alignItems="center">
                <Chip size="small" label={mover.asset} sx={{ borderRadius: 2 }} />
                <Typography variant="body2" color="text.secondary">
                  {mover.value}
                </Typography>
              </Stack>
              <Typography
                variant="body2"
                sx={{
                  color:
                    mover.direction === 'up'
                      ? dashboardPalette.accent.positive
                      : dashboardPalette.accent.negative,
                  fontWeight: 600,
                }}
              >
                {mover.direction === 'up' ? '+' : ''}
                {mover.percent.toFixed(2)}%
              </Typography>
            </Stack>
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
};

const ForecastWidget: React.FC<{ forecasts?: RoiAnalyticsData['forecast'] }> = ({ forecasts }) => {
  if (!forecasts || forecasts.length === 0) {
    return null;
  }
  return (
    <Card variant="outlined" sx={{ borderRadius: 2 }}>
      <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, p: 3.5 }}>
        <Box sx={{ mb: 1 }}>
          <SectionHeader
            title="AI Forecast (Beta)"
            description="Forward-looking return outlook with heuristic confidence. Forecasts are based on historical patterns and market analysis."
            tooltip="AI Forecast provides predictive insights about potential future returns for your assets. Confidence percentage indicates how reliable the forecast is. These are experimental predictions and should be validated before making investment decisions."
          />
        </Box>
        <Stack spacing={1.75}>
          {forecasts.map((forecast) => (
            <Box
              key={`${forecast.symbol}-${forecast.horizon}`}
              sx={{
                borderRadius: 2,
                border: '1px solid rgba(148, 163, 184, 0.18)',
                p: 1.5,
                display: 'flex',
                flexDirection: 'column',
                gap: 1,
              }}
            >
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Stack direction="row" spacing={1.5} alignItems="center">
                  <Chip size="small" label={forecast.symbol} sx={{ borderRadius: 2 }} />
                  <Typography variant="body2" color="text.secondary">
                    {forecast.horizon}
                  </Typography>
                </Stack>
                <Typography
                  variant="subtitle1"
                  sx={{
                    fontWeight: 700,
                    color:
                      forecast.expectedReturn >= 0
                        ? dashboardPalette.accent.positive
                        : dashboardPalette.accent.negative,
                  }}
                >
                  {forecast.expectedReturn >= 0 ? '+' : ''}
                  {forecast.expectedReturn.toFixed(1)}%
                </Typography>
              </Stack>
              <Box>
                <LinearProgress
                  variant="determinate"
                  value={Math.min(100, Math.max(0, forecast.confidence))}
                  sx={{
                    height: 6,
                    borderRadius: 3,
                    backgroundColor: 'rgba(148, 163, 184, 0.16)',
                    '& .MuiLinearProgress-bar': {
                      borderRadius: 3,
                      backgroundColor:
                        forecast.expectedReturn >= 0
                          ? dashboardPalette.accent.positive
                          : dashboardPalette.accent.negative,
                    },
                  }}
                />
                <Typography variant="caption" color="text.secondary">
                  Confidence ~{forecast.confidence.toFixed(0)}%
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                {forecast.narrative}
              </Typography>
            </Box>
          ))}
        </Stack>
        <Alert severity="info" sx={{ borderRadius: 2, mt: 1 }}>
          <Typography variant="caption">
            Forecasts use blended heuristics and should be validated before acting. These are experimental predictions.
          </Typography>
        </Alert>
      </CardContent>
    </Card>
  );
};

const DrilldownPanel: React.FC<{
  data: RoiAnalyticsData;
  onSelectAsset: (symbol: string) => void;
}> = ({ data, onSelectAsset }) => {
  const theme = useTheme();
  return (
    <Card variant="outlined" sx={{ borderRadius: 2 }}>
      <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, p: 3.5 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} justifyContent="space-between" alignItems={{ xs: 'flex-start', md: 'center' }}>
          <Box sx={{ mb: 1 }}>
            <SectionHeader
              title="Project Drill-down"
              description="Explore ROI timeline and risk metrics (Beta, Volatility, Sharpe ratio) for a selected asset."
              tooltip="Select any asset from the dropdown to view its ROI timeline and risk-adjusted performance metrics. Beta measures sensitivity to market movements, Volatility shows price swing magnitude, and Sharpe ratio indicates risk-adjusted returns."
            />
          </Box>
          <Tooltip title="Select an asset to view detailed ROI timeline and risk metrics. This helps analyze individual asset performance and risk characteristics." arrow>
            <TextField
              select
              label="Asset"
              size="small"
              value={data.selectedDrilldown}
              onChange={(event) => onSelectAsset(event.target.value)}
              sx={{ minWidth: 200 }}
            >
              {data.drilldownOptions.map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </TextField>
          </Tooltip>
        </Stack>

        <Box sx={{ height: 240, minHeight: 240, minWidth: 0 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data.drilldown.roiTimeline}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.18)" />
              <XAxis dataKey="date" />
              <YAxis tickFormatter={(value) => `${value.toFixed(1)}%`} />
              <RechartsTooltip
                formatter={(value: number) => [`${value.toFixed(2)}%`, 'ROI']}
                contentStyle={{
                  backgroundColor: theme.palette.background.paper,
                  borderRadius: 2,
                  border: `1px solid ${theme.palette.divider}`,
                  padding: '12px 16px',
                }}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke={dashboardPalette.primary}
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </Box>
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, minmax(0, 1fr))' },
            gap: { xs: 2.5, sm: 3 },
          }}
        >
          <Tooltip title="Beta measures how much an asset's price moves relative to the overall market. Beta > 1 means more volatile than market, Beta < 1 means less volatile. Beta = 1 means moves with the market." arrow>
            <Card variant="outlined" sx={{ height: '100%', borderRadius: 2, cursor: 'help' }}>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="overline" sx={{ letterSpacing: 0.6, fontWeight: 600 }}>
                  Beta
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 700, mt: 0.5 }}>
                  {data.drilldown.metrics.beta.toFixed(2)}
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                  Sensitivity to market movements
                </Typography>
              </CardContent>
            </Card>
          </Tooltip>
          <Tooltip title="Volatility measures the degree of price variation over time. Higher volatility means larger price swings. Annualized standard deviation shows expected price movement range." arrow>
            <Card variant="outlined" sx={{ height: '100%', borderRadius: 2, cursor: 'help' }}>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="overline" sx={{ letterSpacing: 0.6, fontWeight: 600 }}>
                  Volatility
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 700, mt: 0.5 }}>
                  {data.drilldown.metrics.volatility.toFixed(2)}%
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                  Annualized standard deviation
                </Typography>
              </CardContent>
            </Card>
          </Tooltip>
          <Tooltip title="Sharpe ratio measures risk-adjusted returns. Higher Sharpe ratio means better returns relative to risk taken. Generally, Sharpe > 1 is good, > 2 is very good, > 3 is excellent." arrow>
            <Card variant="outlined" sx={{ height: '100%', borderRadius: 2, cursor: 'help' }}>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="overline" sx={{ letterSpacing: 0.6, fontWeight: 600 }}>
                  Sharpe
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 700, mt: 0.5 }}>
                  {data.drilldown.metrics.sharpe.toFixed(2)}
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                  Risk-adjusted performance
                </Typography>
              </CardContent>
            </Card>
          </Tooltip>
        </Box>
      </CardContent>
    </Card>
  );
};

export const RoiAnalytics: React.FC<RoiAnalyticsProps> = ({ data, onSelectAsset }) => {
  return (
    <Box component="section" aria-label="ROI Analytics" sx={{ display: 'flex', flexDirection: 'column', gap: { xs: 3.5, md: 4.5 } }}>
      <Box sx={{ mb: 1 }}>
        <SectionHeader
          title="ROI Analytics"
          description="Comprehensive return on investment analysis with asset-level contributions, top movers, and AI-powered forecasts. Use drill-down to explore individual asset performance."
          variant="h4"
          tooltip="ROI Analytics shows how each asset contributes to your total portfolio return. Top Gainers/Losers highlight best and worst performers. AI Forecast (Beta) provides predictive insights based on historical patterns. Drill-down lets you explore detailed metrics for any asset."
        />
      </Box>
      {data.notice && (
        <Alert severity="info" sx={{ borderRadius: 2 }}>
          {data.notice}
          {typeof data.sampleCount === 'number' ? ` • Samples: ${data.sampleCount}` : null}
        </Alert>
      )}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', md: 'minmax(0, 7fr) minmax(0, 5fr)' },
          gap: { xs: 2, md: 3 },
        }}
      >
        <Box sx={{ minWidth: 0 }}>
          <RoiContributionChart globalPL={data.globalPL} contributions={data.contributions} />
        </Box>
        <Box sx={{ minWidth: 0 }}>
          <Stack spacing={2}>
            <ForecastWidget forecasts={data.forecast} />
            <TopMoversList title="Top Gainers" movers={data.topGainers} />
            <TopMoversList title="Top Losers" movers={data.topLosers} />
          </Stack>
        </Box>
      </Box>
      <Box mt={{ xs: 2, md: 3 }} sx={{ minWidth: 0 }}>
        <DrilldownPanel data={data} onSelectAsset={onSelectAsset} />
      </Box>
    </Box>
  );
};


