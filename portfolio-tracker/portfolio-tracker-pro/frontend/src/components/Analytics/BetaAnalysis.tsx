import React from 'react';
import { Card, CardContent, Typography, Box, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip, useTheme } from '@mui/material';
import { TrendingUp, TrendingDown, Remove } from '@mui/icons-material';

interface BetaAnalysisProps {
  data: Record<string, {
    beta: number;
    correlation: number;
    alpha: number;
  }>;
  benchmark: string;
}

export const BetaAnalysis: React.FC<BetaAnalysisProps> = ({ data, benchmark }) => {
  const theme = useTheme();
  
  const entries = Object.entries(data).sort((a, b) => b[1].beta - a[1].beta);
  
  if (entries.length === 0) {
    return (
      <Card>
        <CardContent>
          <Typography variant="body2" color="text.secondary">
            Insufficient data for beta analysis.
          </Typography>
        </CardContent>
      </Card>
    );
  }
  
  const getBetaColor = (beta: number) => {
    if (beta > 1.2) return 'error';
    if (beta > 0.8) return 'warning';
    if (beta > 0.5) return 'info';
    return 'success';
  };
  
  const getBetaIcon = (beta: number) => {
    if (beta > 1) return <TrendingUp fontSize="small" />;
    if (beta < 1) return <TrendingDown fontSize="small" />;
    return <Remove fontSize="small" />;
  };
  
  return (
    <Card>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
          Beta Analysis vs {benchmark}
        </Typography>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell><strong>Symbol</strong></TableCell>
                <TableCell align="right"><strong>Beta</strong></TableCell>
                <TableCell align="right"><strong>Correlation</strong></TableCell>
                <TableCell align="right"><strong>Alpha (%)</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {entries.map(([symbol, metrics]) => (
                <TableRow key={symbol} hover>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {symbol}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Chip
                      icon={getBetaIcon(metrics.beta)}
                      label={metrics.beta.toFixed(3)}
                      color={getBetaColor(metrics.beta)}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Typography variant="body2">
                      {metrics.correlation.toFixed(3)}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Typography
                      variant="body2"
                      sx={{
                        color: metrics.alpha >= 0 ? 'success.main' : 'error.main',
                        fontWeight: 600
                      }}
                    >
                      {metrics.alpha >= 0 ? '+' : ''}{metrics.alpha.toFixed(2)}%
                    </Typography>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        <Box sx={{ mt: 2, p: 2, bgcolor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.02)', borderRadius: 2 }}>
          <Typography variant="caption" color="text.secondary">
            <strong>Beta:</strong> Measures sensitivity to market movements. β &gt; 1 = more volatile than market, β &lt; 1 = less volatile.
            <br />
            <strong>Alpha:</strong> Excess return vs benchmark. Positive = outperforming, Negative = underperforming.
            <br />
            <strong>Correlation:</strong> How closely asset moves with benchmark. 1 = perfect correlation, -1 = inverse.
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

