import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Typography,
  CardContent,
  IconButton,
  Stack,
  Divider,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  NavigateNext,
} from '@mui/icons-material';
import { portfolioService, Asset } from '../../services/portfolioService';
import { useNavigate } from 'react-router-dom';
import { logger } from '../../utils/logger';
import { AnimatedCard } from '../common/AnimatedCard';
import { TrendIndicator } from '../common/TrendIndicator';

interface TopMover {
  symbol: string;
  change: number;
  currentPrice: number;
}

const TopMovers: React.FC = () => {
  const navigate = useNavigate();
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAssets = async () => {
      try {
        const data = await portfolioService.getAssets();
        setAssets(data);
      } catch (error) {
        logger.error('Error fetching assets for top movers:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAssets();
  }, []);

  const topMovers = useMemo(() => {
    if (!assets || assets.length === 0) return { gainers: [], losers: [] };

    // Sort by pnl_percent (high to low)
    const sorted = [...assets].sort((a, b) => b.pnl_percent - a.pnl_percent);
    
    const gainers: TopMover[] = sorted
      .filter(a => a.pnl_percent > 0)
      .slice(0, 3)
      .map(a => ({
        symbol: a.symbol,
        change: a.pnl_percent,
        currentPrice: a.value_usd / a.amount,
      }));

    const losers: TopMover[] = sorted
      .filter(a => a.pnl_percent < 0)
      .slice(-3)
      .reverse()
      .map(a => ({
        symbol: a.symbol,
        change: a.pnl_percent,
        currentPrice: a.value_usd / a.amount,
      }));

    return { gainers, losers };
  }, [assets]);

  if (loading) {
    return (
      <AnimatedCard>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
            Top Movers
          </Typography>
          <Stack spacing={2}>
            {[1, 2, 3].map((i) => (
              <Box key={i} sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box sx={{ width: 32, height: 32, borderRadius: 1, bgcolor: 'rgba(255,255,255,0.05)' }} />
                <Box sx={{ flex: 1 }}>
                  <Box sx={{ width: '60%', height: 16, borderRadius: 1, bgcolor: 'rgba(255,255,255,0.05)', mb: 0.5 }} />
                  <Box sx={{ width: '40%', height: 12, borderRadius: 1, bgcolor: 'rgba(255,255,255,0.05)' }} />
                </Box>
              </Box>
            ))}
          </Stack>
        </CardContent>
      </AnimatedCard>
    );
  }

  if (assets.length === 0) {
    return null;
  }

  return (
    <AnimatedCard>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Top Movers
          </Typography>
          <IconButton size="small" onClick={() => navigate('/portfolio')}>
            <NavigateNext />
          </IconButton>
        </Box>

        {/* Top Gainers */}
        {topMovers.gainers.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <TrendingUp sx={{ fontSize: 18, color: 'success.main' }} />
              <Typography variant="subtitle2" color="success.main" sx={{ fontWeight: 600 }}>
                Top Gainers
              </Typography>
            </Box>
            <Stack spacing={1}>
              {topMovers.gainers.map((mover) => (
                <Box
                  key={mover.symbol}
                  onClick={() => navigate('/portfolio')}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    p: 1,
                    borderRadius: 1,
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    '&:hover': {
                      bgcolor: 'rgba(16, 185, 129, 0.05)',
                    },
                  }}
                >
                  <Box>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.25 }}>
                      {mover.symbol}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      ${mover.currentPrice.toFixed(2)}
                    </Typography>
                  </Box>
                  <TrendIndicator value={mover.change} showIcon showPercent size="small" />
                </Box>
              ))}
            </Stack>
          </Box>
        )}

        {/* Top Losers */}
        {topMovers.losers.length > 0 && (
          <Box>
            {topMovers.gainers.length > 0 && <Divider sx={{ my: 2 }} />}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <TrendingDown sx={{ fontSize: 18, color: 'error.main' }} />
              <Typography variant="subtitle2" color="error.main" sx={{ fontWeight: 600 }}>
                Top Losers
              </Typography>
            </Box>
            <Stack spacing={1}>
              {topMovers.losers.map((mover) => (
                <Box
                  key={mover.symbol}
                  onClick={() => navigate('/portfolio')}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    p: 1,
                    borderRadius: 1,
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    '&:hover': {
                      bgcolor: 'rgba(239, 68, 68, 0.05)',
                    },
                  }}
                >
                  <Box>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.25 }}>
                      {mover.symbol}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      ${mover.currentPrice.toFixed(2)}
                    </Typography>
                  </Box>
                  <TrendIndicator value={mover.change} showIcon showPercent size="small" />
                </Box>
              ))}
            </Stack>
          </Box>
        )}

        {topMovers.gainers.length === 0 && topMovers.losers.length === 0 && (
          <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
            No price changes available
          </Typography>
        )}
      </CardContent>
    </AnimatedCard>
  );
};

export default React.memo(TopMovers);

