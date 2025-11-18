import React from 'react';
import {
  Box,
  Typography,
  Stack,
  Chip,
  Button,
  IconButton,
  ToggleButton,
  ToggleButtonGroup,
  useTheme,
  useMediaQuery,
  Tooltip,
  CircularProgress,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import RefreshIcon from '@mui/icons-material/Refresh';
import SyncIcon from '@mui/icons-material/Sync';
import { dashboardPalette, timeRangeOptions, TimeRange } from '../../theme/dashboardTokens';
import { KPIItem } from './types';

export interface GlobalStatusBarProps {
  portfolioName: string;
  lastUpdated: string;
  kpis: KPIItem[];
  timeRange: TimeRange;
  onTimeRangeChange: (value: TimeRange) => void;
  onAddAsset: () => void;
  onAlertsClick: () => void;
  onRefresh?: () => void;
  refreshing?: boolean;
  onSyncTrades?: () => void;
  syncing?: boolean;
}

export const GlobalStatusBar: React.FC<GlobalStatusBarProps> = ({
  portfolioName,
  lastUpdated,
  kpis,
  timeRange,
  onTimeRangeChange,
  onAddAsset,
  onAlertsClick,
  onRefresh,
  refreshing = false,
  onSyncTrades,
  syncing = false,
}) => {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';
  const palette = isDark ? dashboardPalette.dark : dashboardPalette.light;
  const isSmallScreen = useMediaQuery(theme.breakpoints.down('sm'));

  return (
    <Box
      component="header"
      sx={{
        display: 'flex',
        flexDirection: 'column',
        gap: { xs: 2, md: 3 },
        py: { xs: 2, md: 3 },
        px: { xs: 0, md: 1 },
      }}
    >
      <Stack
        direction={{ xs: 'column', md: 'row' }}
        spacing={{ xs: 2, md: 3 }}
        alignItems={{ xs: 'flex-start', md: 'center' }}
        justifyContent="space-between"
      >
        <Box>
          <Typography
            variant="h3"
            sx={{
              fontWeight: 700,
              fontSize: { xs: '1.75rem', sm: '2rem', md: '2.5rem' },
              color: palette.textPrimary,
            }}
          >
            {portfolioName}
          </Typography>
          <Stack direction="row" spacing={1} alignItems="center" mt={0.5}>
            <AccessTimeIcon fontSize="small" sx={{ color: dashboardPalette.primary }} />
            <Typography variant="body2" sx={{ color: palette.textSecondary }}>
              Last updated {lastUpdated}
            </Typography>
          </Stack>
        </Box>

        <Stack
          direction="row"
          spacing={1}
          alignItems="center"
          flexWrap="wrap"
          sx={{ display: { xs: 'none', md: 'flex' } }}
        >
          {onRefresh && (
            <Tooltip title="Manually refresh portfolio data from all connected exchanges. This updates balances, prices, and analytics without waiting for the scheduled sync." arrow>
              <span>
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={
                    refreshing ? (
                      <CircularProgress color="inherit" size={16} sx={{ mr: -0.5 }} />
                    ) : (
                      <RefreshIcon fontSize="small" />
                    )
                  }
                  onClick={onRefresh}
                  disabled={refreshing}
                  sx={{ borderRadius: 2, textTransform: 'none', minHeight: 36 }}
                >
                  Refresh
                </Button>
              </span>
            </Tooltip>
          )}
          {onSyncTrades && (
            <Tooltip title="Check all connected exchanges for new trades and transactions. This will import any trades that haven't been synced yet." arrow>
              <span>
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={
                    syncing ? (
                      <CircularProgress color="inherit" size={16} sx={{ mr: -0.5 }} />
                    ) : (
                      <SyncIcon fontSize="small" />
                    )
                  }
                  onClick={onSyncTrades}
                  disabled={syncing}
                  sx={{ borderRadius: 2, textTransform: 'none', minHeight: 36 }}
                >
                  Sync
                </Button>
              </span>
            </Tooltip>
          )}
          <Tooltip title="Select the time period for portfolio performance charts and analytics. This affects the equity curve, returns, and historical data displayed throughout the dashboard." arrow>
            <span>
              <ToggleButtonGroup
                exclusive
                size="small"
                value={timeRange}
                onChange={(_, nextValue) => {
                  if (nextValue) {
                    onTimeRangeChange(nextValue);
                  }
                }}
                sx={{
                  backgroundColor: isDark ? 'rgba(15, 23, 42, 0.6)' : 'rgba(148, 163, 184, 0.12)',
                  borderRadius: 3,
                  p: 0.5,
                  '.MuiToggleButton-root': {
                    border: 'none',
                    textTransform: 'none',
                    borderRadius: 2.5,
                    px: 2,
                    py: 0.75,
                    minHeight: 36,
                    color: palette.textSecondary,
                    fontWeight: 500,
                    '&.Mui-selected': {
                      color: palette.textPrimary,
                      backgroundColor: dashboardPalette.primary,
                      fontWeight: 600,
                    },
                  },
                }}
              >
                {timeRangeOptions.map((option) => (
                  <ToggleButton key={option} value={option}>
                    {option.toUpperCase()}
                  </ToggleButton>
                ))}
              </ToggleButtonGroup>
            </span>
          </Tooltip>
          <Tooltip title="Add a new asset or transaction to your portfolio. This opens the transactions page where you can manually enter trades or import from exchanges." arrow>
            <span>
              <Button
                variant="contained"
                size="small"
                startIcon={<AddIcon />}
                onClick={onAddAsset}
                sx={{ borderRadius: 2, textTransform: 'none', minHeight: 36 }}
              >
                Add asset
              </Button>
            </span>
          </Tooltip>
          <Tooltip title="View and manage price alerts. Set notifications for when assets reach specific price targets or thresholds." arrow>
            <IconButton
              color="primary"
              onClick={onAlertsClick}
              sx={{
                borderRadius: 2,
                border: `1px solid ${dashboardPalette.primary}`,
                width: 44,
                height: 44,
                minWidth: 44,
                minHeight: 44,
              }}
            >
              <NotificationsActiveIcon />
            </IconButton>
          </Tooltip>
        </Stack>
      </Stack>

      {isSmallScreen && (
        <Box
          sx={{
            position: 'sticky',
            bottom: 16,
            zIndex: 15,
            width: '100%',
            px: 0.5,
          }}
        >
          <Stack
            direction="row"
            spacing={1}
            alignItems="center"
            justifyContent="space-between"
            sx={{
              borderRadius: 2.5,
              backdropFilter: 'blur(12px)',
              backgroundColor:
                theme.palette.mode === 'dark'
                  ? 'rgba(15, 23, 42, 0.92)'
                  : 'rgba(255, 255, 255, 0.9)',
              border: `1px solid ${theme.palette.divider}`,
              p: 1.5,
              boxShadow: theme.palette.mode === 'dark'
                ? '0 12px 32px rgba(15, 23, 42, 0.45)'
                : '0 12px 32px rgba(15, 23, 42, 0.18)',
            }}
          >
            {onRefresh && (
              <Tooltip title="Manually refresh portfolio data from all connected exchanges. This updates balances, prices, and analytics without waiting for the scheduled sync." arrow>
                <span>
                  <IconButton
                    color="primary"
                    onClick={onRefresh}
                    disabled={refreshing}
                    sx={{ borderRadius: 2, width: 44, height: 44, minWidth: 44, minHeight: 44 }}
                  >
                    {refreshing ? <CircularProgress size={18} /> : <RefreshIcon />}
                  </IconButton>
                </span>
              </Tooltip>
            )}
            {onSyncTrades && (
              <Tooltip title="Check all connected exchanges for new trades and transactions. This will import any trades that haven't been synced yet." arrow>
                <span>
                  <IconButton
                    color="primary"
                    onClick={onSyncTrades}
                    disabled={syncing}
                    sx={{ borderRadius: 2, width: 44, height: 44, minWidth: 44, minHeight: 44 }}
                  >
                    {syncing ? <CircularProgress size={18} /> : <SyncIcon />}
                  </IconButton>
                </span>
              </Tooltip>
            )}
            <Tooltip title="Add a new asset or transaction to your portfolio. This opens the transactions page where you can manually enter trades or import from exchanges." arrow>
              <span>
                <Button
                  variant="contained"
                  size="small"
                  startIcon={<AddIcon />}
                  onClick={onAddAsset}
                  sx={{ borderRadius: 2, flexGrow: 1, textTransform: 'none', minHeight: 36 }}
                >
                  Add asset
                </Button>
              </span>
            </Tooltip>
            <Tooltip title="View and manage price alerts. Set notifications for when assets reach specific price targets or thresholds." arrow>
              <IconButton
                color="primary"
                onClick={onAlertsClick}
                sx={{
                  borderRadius: 2,
                  width: 44,
                  height: 44,
                  minWidth: 44,
                  minHeight: 44,
                  border: `1px solid ${dashboardPalette.primary}`,
                }}
              >
                <NotificationsActiveIcon />
              </IconButton>
            </Tooltip>
          </Stack>
        </Box>
      )}

      <Stack
        direction={{ xs: 'column', md: 'row' }}
        spacing={{ xs: 2, md: 2.5 }}
        flexWrap="wrap"
      >
        {kpis.map((kpi) => {
          const deltaColor =
            kpi.delta !== undefined
              ? kpi.delta >= 0
                ? dashboardPalette.accent.positive
                : dashboardPalette.accent.negative
              : palette.textSecondary;
          return (
            <Chip
              key={kpi.id}
              label={
                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                  <Typography variant="caption" sx={{ color: palette.textSecondary }}>
                    {kpi.label}
                  </Typography>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600, color: palette.textPrimary }}>
                    {kpi.value}
                  </Typography>
                  {kpi.delta !== undefined && (
                    <Typography variant="caption" sx={{ color: deltaColor }}>
                      {kpi.delta >= 0 ? '+' : ''}
                      {kpi.delta.toFixed(2)}% {kpi.deltaLabel ?? ''}
                    </Typography>
                  )}
                  {kpi.secondary && (
                    <Typography variant="caption" sx={{ color: palette.textSecondary }}>
                      {kpi.secondary}
                    </Typography>
                  )}
                </Box>
              }
              sx={{
                py: 1.25,
                px: 1.75,
                background: isDark
                  ? 'rgba(15, 23, 42, 0.6)'
                  : 'rgba(37, 99, 235, 0.08)',
                borderRadius: 2,
                border: 'none',
              }}
            />
          );
        })}
      </Stack>
    </Box>
  );
};


