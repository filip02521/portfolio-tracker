import React from 'react';
import { Card, CardContent, Typography, Box, useTheme } from '@mui/material';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';

interface RiskReturnScatterProps {
  data: Array<{
    symbol: string;
    return: number;
    risk: number;
    value: number;
    type: string;
  }>;
}

export const RiskReturnScatter: React.FC<RiskReturnScatterProps> = ({ data }) => {
  const theme = useTheme();
  
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardContent>
          <Typography variant="body2" color="text.secondary">
            Insufficient data for risk-return scatter plot.
          </Typography>
        </CardContent>
      </Card>
    );
  }
  
  const getColor = (type: string) => {
    return type === 'crypto' ? theme.palette.primary.main : theme.palette.secondary.main;
  };
  
  return (
    <Card>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
          Risk-Return Scatter Plot
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
                formatter={(value: number, name: string, props: any) => {
                  if (name === 'return') return [`${value.toFixed(2)}%`, 'Return'];
                  if (name === 'risk') return [`${value.toFixed(2)}%`, 'Risk'];
                  return [value, name];
                }}
                labelFormatter={(label) => `Symbol: ${label}`}
              />
              <Scatter
                name="Assets"
                data={data}
                fill={theme.palette.primary.main}
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getColor(entry.type)} />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </Box>
        <Box sx={{ mt: 2, display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box sx={{ width: 16, height: 16, bgcolor: theme.palette.primary.main, borderRadius: '50%' }} />
            <Typography variant="caption">Crypto</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box sx={{ width: 16, height: 16, bgcolor: theme.palette.secondary.main, borderRadius: '50%' }} />
            <Typography variant="caption">Stocks</Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

