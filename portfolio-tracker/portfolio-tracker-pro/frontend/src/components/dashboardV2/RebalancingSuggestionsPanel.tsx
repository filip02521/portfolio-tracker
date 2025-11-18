import React, { useCallback, useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  Tooltip,
  Divider,
  Alert,
  AlertTitle,
  Button,
} from '@mui/material';
import SwapHorizIcon from '@mui/icons-material/SwapHoriz';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import { portfolioService } from '../../services/portfolioService';
import { logger } from '../../utils/logger';
import { SectionHeader } from '../common/SectionHeader';

interface RebalancingSuggestion {
  symbol: string;
  action: 'increase' | 'decrease';
  drift_percent: number;
  current_percent: number;
  target_percent: number;
  adjustment_value: number;
  estimated_cost?: number;
}

interface RebalancingResponse {
  current_allocation: Record<string, number>;
  target_allocation: Record<string, number>;
  suggestions: RebalancingSuggestion[];
  total_value: number;
  threshold?: number;
}

const formatCurrency = (value?: number) => {
  if (value === undefined) return 'N/A';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

const formatPercentage = (value?: number) => {
  if (value === undefined) return 'N/A';
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
};

export const RebalancingSuggestionsPanel: React.FC = () => {
  const [data, setData] = useState<RebalancingResponse | null>(null);
  const [loading, setLoading] = useState(false); // Changed to false - manual loading only
  const [error, setError] = useState<string | null>(null);

  const fetchSuggestions = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await portfolioService.getRebalancingSuggestions(5, 6, false);
      setData(response);
    } catch (error) {
      logger.error('Failed to fetch rebalancing suggestions:', error);
      setError('Rebalancing suggestions are temporarily unavailable. You can continue using the dashboard with current allocation.');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  // Removed automatic useEffect - now manual only via button

  if (loading) {
    return (
      <Card variant="outlined" sx={{ borderRadius: 2 }}>
        <CardContent sx={{ p: 3.5 }}>
          <Box sx={{ mb: 3 }}>
            <SectionHeader
              title="Portfolio Rebalancing"
              description="Automatic suggestions to rebalance your portfolio when allocations drift from target. Drift threshold determines when suggestions appear."
              tooltip="Rebalancing helps maintain your target asset allocation. 'Drift' is the difference between current and target allocation. Suggestions appear when drift exceeds the threshold (default 5%)."
              icon={<SwapHorizIcon />}
            />
          </Box>
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 200 }}>
            <CircularProgress size={40} />
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (!data || !data.suggestions || data.suggestions.length === 0) {
    return (
      <Card variant="outlined" sx={{ borderRadius: 2 }}>
        <CardContent sx={{ p: 3.5 }}>
          <Box sx={{ mb: 3 }}>
            <SectionHeader
              title="Portfolio Rebalancing"
              description="Automatic suggestions to rebalance your portfolio when allocations drift from target. Drift threshold determines when suggestions appear."
              tooltip="Rebalancing helps maintain your target asset allocation. 'Drift' is the difference between current and target allocation. Suggestions appear when drift exceeds the threshold (default 5%)."
              icon={<SwapHorizIcon />}
            />
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Alert 
              severity={error ? 'warning' : 'info'} 
              sx={{ borderRadius: 2 }}
            >
              <AlertTitle>{error ? 'Rebalancing unavailable' : 'No rebalancing needed'}</AlertTitle>
              {error
                ? 'Rebalancing engine timed out or is unavailable. No automatic suggestions at the moment.'
                : 'Click the button below to check for rebalancing suggestions.'}
            </Alert>
            <Button
              variant="contained"
              onClick={fetchSuggestions}
              disabled={loading}
              startIcon={loading ? <CircularProgress size={16} /> : <SwapHorizIcon />}
              sx={{ alignSelf: 'flex-start' }}
            >
              {loading ? 'Analyzing...' : 'Check Rebalancing Suggestions'}
            </Button>
          </Box>
        </CardContent>
      </Card>
    );
  }

  const totalValue = data.total_value ?? 0;
  const threshold = data.threshold ?? 5;

  return (
    <Card variant="outlined" sx={{ borderRadius: 2 }}>
      <CardContent sx={{ p: 3.5 }}>
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <SectionHeader
            title="Portfolio Rebalancing"
            description="Automatic suggestions to rebalance your portfolio when allocations drift from target. Drift threshold determines when suggestions appear."
            tooltip="Rebalancing helps maintain your target asset allocation. 'Drift' is the difference between current and target allocation. Suggestions appear when drift exceeds the threshold (default 5%). Increase allocation means buy more, decrease means sell some."
            icon={<SwapHorizIcon />}
          />
          <Button
            variant="outlined"
            size="small"
            onClick={fetchSuggestions}
            disabled={loading}
            startIcon={loading ? <CircularProgress size={14} /> : <SwapHorizIcon />}
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </Button>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 1, mb: 2.5 }}>
          <Chip
            label={`${data.suggestions.length} suggestion${data.suggestions.length !== 1 ? 's' : ''}`}
            size="medium"
            color="primary"
            sx={{ fontWeight: 600 }}
          />
          <Tooltip title={`Suggestions appear when allocation drift exceeds ${threshold.toFixed(1)}%. This threshold can be adjusted in settings.`} arrow>
            <Chip
              label={`Drift ≥ ${threshold.toFixed(1)}%`}
              size="medium"
              variant="outlined"
              sx={{ fontWeight: 600 }}
            />
          </Tooltip>
        </Box>

        <List disablePadding>
          {data.suggestions.map((s, index) => {
            const isIncrease = s.action === 'increase';
            const Icon = isIncrease ? ArrowUpwardIcon : ArrowDownwardIcon;
            const color = isIncrease ? 'success.main' : 'error.main';

            return (
              <React.Fragment key={`${s.symbol}-${index}`}>
                {index > 0 && <Divider component="li" sx={{ my: 0.75 }} />}
                <ListItem
                  sx={{
                    alignItems: 'flex-start',
                    py: 1.25,
                    px: 0,
                  }}
                >
                  <Box sx={{ display: 'flex', flexDirection: 'column', width: '100%', gap: 0.75 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Chip
                          label={s.symbol}
                          size="small"
                          sx={{ fontWeight: 600, letterSpacing: 0.3 }}
                        />
                        <Tooltip title={isIncrease ? 'Buy more of this asset to reach target allocation' : 'Sell some of this asset to reach target allocation'} arrow>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <Icon sx={{ fontSize: 18, color }} />
                            <Typography variant="body2" sx={{ fontWeight: 600, color }}>
                              {isIncrease ? 'Increase' : 'Decrease'} allocation
                            </Typography>
                          </Box>
                        </Tooltip>
                      </Box>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {formatCurrency(Math.abs(s.adjustment_value))}
                      </Typography>
                    </Box>

                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5 }}>
                          <Typography variant="caption" color="text.secondary">
                            Current: {formatPercentage(s.current_percent)}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Target: {formatPercentage(s.target_percent)}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Drift: {formatPercentage(s.drift_percent)}
                          </Typography>
                          {totalValue > 0 && (
                            <Typography variant="caption" color="text.secondary">
                              Portfolio share to move:{' '}
                              {formatPercentage((s.adjustment_value / totalValue) * 100)}
                            </Typography>
                          )}
                        </Box>
                      }
                      secondary={
                        s.estimated_cost !== undefined ? (
                          <Tooltip
                            title="Estimated trading cost assuming 0.1% fee on notional value."
                            arrow
                            placement="right"
                          >
                            <Typography variant="caption" color="text.secondary">
                              Estimated transaction cost: {formatCurrency(s.estimated_cost)}
                            </Typography>
                          </Tooltip>
                        ) : null
                      }
                      sx={{ mt: 0.25 }}
                    />
                  </Box>
                </ListItem>
              </React.Fragment>
            );
          })}
        </List>
      </CardContent>
    </Card>
  );
};


