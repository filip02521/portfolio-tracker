import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  CardContent,
  IconButton,
  Chip,
  Stack,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  NavigateNext,
  Notifications,
} from '@mui/icons-material';
import { portfolioService, Transaction } from '../../services/portfolioService';
import { useNavigate } from 'react-router-dom';
import { logger } from '../../utils/logger';
import { AnimatedCard } from '../common/AnimatedCard';

const RecentActivity: React.FC = () => {
  const navigate = useNavigate();
  const [recentTransactions, setRecentTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRecent = async () => {
      try {
        // Fetch last 5 transactions
        const data = await portfolioService.getTransactions(5, 0, false);
        setRecentTransactions(data);
      } catch (error) {
        logger.error('Error fetching recent transactions:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchRecent();
  }, []);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 2,
    }).format(amount);
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) {
      return `${diffMins}m ago`;
    } else if (diffHours < 24) {
      return `${diffHours}h ago`;
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return `${diffDays}d ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  if (loading || recentTransactions.length === 0) {
    return (
      <AnimatedCard>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Recent Activity
            </Typography>
            {recentTransactions.length > 0 && (
              <IconButton size="small" onClick={() => navigate('/transactions')}>
                <NavigateNext />
              </IconButton>
            )}
          </Box>
          
          {recentTransactions.length === 0 && !loading && (
            <Box sx={{ textAlign: 'center', py: 3 }}>
              <Notifications sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
              <Typography variant="body2" color="text.secondary">
                No recent transactions
              </Typography>
            </Box>
          )}
          
          {loading && (
            <Stack spacing={2}>
              {[1, 2, 3].map((i) => (
                <Box key={i} sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box sx={{ width: 40, height: 40, borderRadius: 1, bgcolor: 'rgba(255,255,255,0.05)' }} />
                  <Box sx={{ flex: 1 }}>
                    <Box sx={{ width: '60%', height: 16, borderRadius: 1, bgcolor: 'rgba(255,255,255,0.05)', mb: 1 }} />
                    <Box sx={{ width: '40%', height: 12, borderRadius: 1, bgcolor: 'rgba(255,255,255,0.05)' }} />
                  </Box>
                </Box>
              ))}
            </Stack>
          )}
        </CardContent>
      </AnimatedCard>
    );
  }

  return (
    <AnimatedCard>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Recent Activity
          </Typography>
          <IconButton size="small" onClick={() => navigate('/transactions')}>
            <NavigateNext />
          </IconButton>
        </Box>

        <Stack spacing={1.5}>
          {recentTransactions.map((tx) => {
            const isBuy = tx.type.toLowerCase() === 'buy';
            const Icon = isBuy ? TrendingUp : TrendingDown;
            const color = isBuy ? 'success.main' : 'error.main';
            const bgColor = isBuy ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)';

            return (
              <Box
                key={tx.id}
                onClick={() => navigate('/transactions')}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 2,
                  p: 1.5,
                  borderRadius: 1,
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  '&:hover': {
                    bgcolor: 'rgba(37, 99, 235, 0.05)',
                  },
                }}
              >
                <Box
                  sx={{
                    width: 40,
                    height: 40,
                    borderRadius: 1.5,
                    bgcolor: bgColor,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <Icon sx={{ fontSize: 20, color }} />
                </Box>
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                      {tx.symbol}
                    </Typography>
                    <Chip
                      label={tx.type.toUpperCase()}
                      size="small"
                      sx={{
                        height: 18,
                        fontSize: '0.65rem',
                        bgcolor: bgColor,
                        color,
                        fontWeight: 700,
                      }}
                    />
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    {formatCurrency(tx.amount * tx.price)} • {formatDate(tx.date)}
                  </Typography>
                </Box>
              </Box>
            );
          })}
        </Stack>
      </CardContent>
    </AnimatedCard>
  );
};

export default React.memo(RecentActivity);

