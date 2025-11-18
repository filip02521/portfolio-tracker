import React, { useState, useCallback } from 'react';
import { Card, CardContent, Box, Typography, Select, MenuItem, Button } from '@mui/material';
import { Calculate } from '@mui/icons-material';
import { portfolioService } from '../services/portfolioService';

const RiskMiniWidget: React.FC = () => {
  const [days, setDays] = useState(180);
  const [confidence] = useState(0.95);
  const [sharpeWindow, setSharpeWindow] = useState(30);
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const res = await portfolioService.getRiskAnalytics(days, confidence, sharpeWindow);
      setData(res);
    } catch (e) {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [days, confidence, sharpeWindow]);

  // Removed automatic useEffect - now manual only via button or when filters change

  return (
    <Card>
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>Risk Overview</Typography>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Select size="small" value={days} onChange={(e) => setDays(e.target.value as number)}>
              <MenuItem value={90}>90d</MenuItem>
              <MenuItem value={180}>180d</MenuItem>
              <MenuItem value={365}>365d</MenuItem>
            </Select>
            <Select size="small" value={sharpeWindow} onChange={(e) => setSharpeWindow(e.target.value as number)}>
              <MenuItem value={30}>S30</MenuItem>
              <MenuItem value={90}>S90</MenuItem>
            </Select>
            {!data && (
              <Button
                size="small"
                variant="contained"
                startIcon={<Calculate />}
                onClick={fetchData}
                disabled={loading}
              >
                Calculate
              </Button>
            )}
            {data && (
              <Button
                size="small"
                variant="outlined"
                startIcon={<Calculate />}
                onClick={fetchData}
                disabled={loading}
              >
                Refresh
              </Button>
            )}
          </Box>
        </Box>

        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' }, gap: 2 }}>
          <Box sx={{ p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
            <Typography variant="caption" color="text.secondary">VaR ({Math.round((confidence)*100)}%, 1d)</Typography>
            <Typography variant="h5" sx={{ fontWeight: 700 }}>
              {loading ? '—' : `${(data?.var ?? 0).toFixed(2)}%`}
            </Typography>
          </Box>
          <Box sx={{ p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
            <Typography variant="caption" color="text.secondary">CVaR (Expected Shortfall)</Typography>
            <Typography variant="h5" sx={{ fontWeight: 700 }}>
              {loading ? '—' : `${(data?.cvar ?? 0).toFixed(2)}%`}
            </Typography>
          </Box>
          <Box sx={{ p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
            <Typography variant="caption" color="text.secondary">Rolling Sharpe</Typography>
            <Typography variant="h5" sx={{ fontWeight: 700, color: (data?.rolling_sharpe_latest ?? 0) >= 1 ? 'success.main' : 'text.primary' }}>
              {loading ? '—' : (data?.rolling_sharpe_latest ?? 0).toFixed(2)}
            </Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

export default React.memo(RiskMiniWidget);



