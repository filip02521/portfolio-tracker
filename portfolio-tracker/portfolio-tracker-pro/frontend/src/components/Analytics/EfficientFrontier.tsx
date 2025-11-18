import React from 'react';
import { Card, CardContent, Typography, Box, useTheme } from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ScatterChart,
  Scatter
} from 'recharts';

interface EfficientFrontierProps {
  data: Array<{
    return: number;
    risk: number;
    sharpe: number;
  }>;
}

export const EfficientFrontier: React.FC<EfficientFrontierProps> = ({ data }) => {
  const theme = useTheme();
  
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardContent>
          <Typography variant="body2" color="text.secondary">
            Insufficient data for efficient frontier. Need at least 2 assets.
          </Typography>
        </CardContent>
      </Card>
    );
  }
  
  // Find maximum Sharpe ratio point (optimal portfolio)
  const optimalPoint = data.reduce((max, point) => 
    point.sharpe > max.sharpe ? point : max, data[0]
  );
  
  return (
    <Card>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
          Efficient Frontier
        </Typography>
        <Box sx={{ height: 400 }}>
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart
              margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
              <XAxis
                type="number"
                dataKey="risk"
                name="Risk (Volatility %)"
                label={{ value: 'Risk (Annualized Volatility %)', position: 'insideBottom', offset: -5 }}
                stroke={theme.palette.text.secondary}
              />
              <YAxis
                type="number"
                dataKey="return"
                name="Return (%)"
                label={{ value: 'Return (Annualized %)', angle: -90, position: 'insideLeft' }}
                stroke={theme.palette.text.secondary}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: theme.palette.mode === 'dark' 
                    ? 'rgba(45, 55, 72, 0.98)' 
                    : 'rgba(255, 255, 255, 0.98)',
                  border: `1px solid ${theme.palette.divider}`,
                  borderRadius: 2,
                }}
                formatter={(value: number, name: string) => {
                  if (name === 'return') return [`${value.toFixed(2)}%`, 'Return'];
                  if (name === 'risk') return [`${value.toFixed(2)}%`, 'Risk'];
                  if (name === 'sharpe') return [value.toFixed(3), 'Sharpe Ratio'];
                  return [value, name];
                }}
              />
              <Scatter
                name="Portfolio Combinations"
                data={data}
                fill={theme.palette.primary.main}
                fillOpacity={0.6}
              />
              <Scatter
                name="Optimal Portfolio"
                data={[optimalPoint]}
                fill={theme.palette.success.main}
                shape="star"
              />
            </ScatterChart>
          </ResponsiveContainer>
        </Box>
        <Box sx={{ mt: 2, p: 2, bgcolor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.02)', borderRadius: 2 }}>
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
            Optimal Portfolio (Max Sharpe Ratio)
          </Typography>
          <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
            <Typography variant="body2">
              <strong>Return:</strong> {optimalPoint.return.toFixed(2)}%
            </Typography>
            <Typography variant="body2">
              <strong>Risk:</strong> {optimalPoint.risk.toFixed(2)}%
            </Typography>
            <Typography variant="body2">
              <strong>Sharpe Ratio:</strong> {optimalPoint.sharpe.toFixed(3)}
            </Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

