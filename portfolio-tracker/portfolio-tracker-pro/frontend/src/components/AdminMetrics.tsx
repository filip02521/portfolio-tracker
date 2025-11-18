import React, { useEffect, useState, useCallback } from 'react';
import { Box, Card, CardContent, Typography, Chip, LinearProgress, Divider } from '@mui/material';

const AdminMetrics: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [raw, setRaw] = useState<string>('');
  const [counters, setCounters] = useState<Record<string, number>>({});

  const fetchMetrics = useCallback(async () => {
    try {
      setLoading(true);
      const base = (process.env.REACT_APP_API_URL || 'http://localhost:8000/api').replace(/\/api$/, '');
      const res = await fetch(`${base}/metrics`, { cache: 'no-store' });
      const text = await res.text();
      setRaw(text);
      const summary: Record<string, number> = {};
      text.split('\n').forEach((line) => {
        if (line.startsWith('#') || line.trim() === '') return;
        const m = line.match(/^(\w+)(?:\{[^}]*\})?\s+(\d+(?:\.\d+)?)/);
        if (m) {
          const key = m[1];
          const val = parseFloat(m[2]);
          summary[key] = (summary[key] || 0) + val;
        }
      });
      setCounters(summary);
    } catch (e) {
      setRaw('');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMetrics();
    const id = setInterval(fetchMetrics, 10000);
    return () => clearInterval(id);
  }, [fetchMetrics]);

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>System Metrics</Typography>
        <Chip label={loading ? 'Refreshing...' : 'Live'} color={loading ? 'default' : 'success'} size="small" />
      </Box>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 1 }}>Market Data</Typography>
          <Typography variant="body2" color="text.secondary">Provider requests total (by sum of labels)</Typography>
          <Box sx={{ mt: 2, display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}>
            <Metric name="market_provider_requests_total" value={counters['market_provider_requests_total']} />
            <Metric name="market_cache_hits_total" value={counters['market_cache_hits_total']} />
            <Metric name="market_watchlist_requests_total" value={counters['market_watchlist_requests_total']} />
          </Box>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 1 }}>Raw Prometheus</Typography>
          <Divider sx={{ mb: 2 }} />
          <Box component="pre" sx={{ maxHeight: 320, overflow: 'auto', fontSize: 12, whiteSpace: 'pre-wrap' }}>{raw || 'No data'}</Box>
        </CardContent>
      </Card>
    </Box>
  );
};

const Metric: React.FC<{ name: string, value?: number }> = ({ name, value }) => (
  <Box sx={{ p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 2 }}>
    <Typography variant="subtitle2" color="text.secondary">{name}</Typography>
    <Typography variant="h6" sx={{ fontWeight: 700 }}>{value ?? 0}</Typography>
  </Box>
);

export default AdminMetrics;


