import React, { useMemo } from 'react';
import { Card, CardContent, Typography, Box, useTheme } from '@mui/material';

interface CorrelationMatrixProps {
  data: Record<string, Record<string, number>>;
}

export const CorrelationMatrix: React.FC<CorrelationMatrixProps> = ({ data }) => {
  const theme = useTheme();
  
  const matrixData = useMemo(() => {
    const symbols = Object.keys(data).sort();
    if (symbols.length === 0) return [];
    
    const result: Array<{ x: string; y: string; value: number }> = [];
    for (const symbol1 of symbols) {
      for (const symbol2 of symbols) {
        result.push({
          x: symbol1,
          y: symbol2,
          value: data[symbol1]?.[symbol2] ?? 0
        });
      }
    }
    return result;
  }, [data]);
  
  const symbols = useMemo(() => Object.keys(data).sort(), [data]);
  
  if (symbols.length === 0) {
    return (
      <Card>
        <CardContent>
          <Typography variant="body2" color="text.secondary">
            Insufficient data for correlation matrix. Need at least 2 assets.
          </Typography>
        </CardContent>
      </Card>
    );
  }
  
  // Color scale: -1 (red) to 1 (green), 0 (neutral)
  const getColor = (value: number) => {
    if (value >= 0.7) return theme.palette.success.main;
    if (value >= 0.3) return theme.palette.success.light;
    if (value >= -0.3) return theme.palette.grey[400];
    if (value >= -0.7) return theme.palette.error.light;
    return theme.palette.error.main;
  };
  
  return (
    <Card>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
          Asset Correlation Matrix
        </Typography>
        <Box sx={{ overflowX: 'auto' }}>
          <Box sx={{ display: 'grid', gridTemplateColumns: `auto repeat(${symbols.length}, 1fr)`, gap: 0.5 }}>
            {/* Header row */}
            <Box></Box>
            {symbols.map(symbol => (
              <Box
                key={symbol}
                sx={{
                  p: 1,
                  textAlign: 'center',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  color: 'text.secondary'
                }}
              >
                {symbol}
              </Box>
            ))}
            
            {/* Data rows */}
            {symbols.map(symbol1 => (
              <React.Fragment key={symbol1}>
                <Box
                  sx={{
                    p: 1,
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    color: 'text.secondary',
                    display: 'flex',
                    alignItems: 'center'
                  }}
                >
                  {symbol1}
                </Box>
                {symbols.map(symbol2 => {
                  const value = data[symbol1]?.[symbol2] ?? 0;
                  return (
                    <Box
                      key={`${symbol1}-${symbol2}`}
                      sx={{
                        p: 1,
                        backgroundColor: getColor(value),
                        color: 'white',
                        textAlign: 'center',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        borderRadius: 1,
                        minWidth: 60,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}
                    >
                      {value.toFixed(2)}
                    </Box>
                  );
                })}
              </React.Fragment>
            ))}
          </Box>
        </Box>
        <Box sx={{ mt: 2, display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box sx={{ width: 20, height: 20, bgcolor: theme.palette.error.main, borderRadius: 1 }} />
            <Typography variant="caption">Negative (-1 to -0.3)</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box sx={{ width: 20, height: 20, bgcolor: theme.palette.grey[400], borderRadius: 1 }} />
            <Typography variant="caption">Neutral (-0.3 to 0.3)</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box sx={{ width: 20, height: 20, bgcolor: theme.palette.success.main, borderRadius: 1 }} />
            <Typography variant="caption">Positive (0.3 to 1)</Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

