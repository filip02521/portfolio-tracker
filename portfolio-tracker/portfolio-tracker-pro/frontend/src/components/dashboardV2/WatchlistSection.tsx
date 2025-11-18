import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Stack,
  IconButton,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  ListItemSecondaryAction,
  Tooltip,
  useTheme,
  Button,
  Drawer,
} from '@mui/material';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import NotificationsOffIcon from '@mui/icons-material/NotificationsOff';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import { useNavigate } from 'react-router-dom';
import { WatchItem, RecentAlert } from './types';
import { dashboardPalette } from '../../theme/dashboardTokens';
import { SectionHeader } from '../common/SectionHeader';

export interface WatchlistSectionProps {
  items: WatchItem[];
  alerts: RecentAlert[];
  onToggleAlert: (id: string) => void;
}

const getStatusDescription = (status: RecentAlert['status']): string => {
  const descriptions: Record<RecentAlert['status'], string> = {
    'new': 'New alerts require your attention. They indicate price targets have been reached or portfolio conditions have changed.',
    'acknowledged': 'Acknowledged alerts have been reviewed but not yet resolved. They remain in your log for reference.',
    'resolved': 'Resolved alerts have been handled and no longer require action. They are kept for historical reference.',
  };
  return descriptions[status];
};

const WatchlistCard: React.FC<{ item: WatchItem; onToggle: () => void }> = ({ item, onToggle }) => {
  return (
    <Card variant="outlined" sx={{ height: '100%', borderRadius: 2 }}>
      <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, p: 3.5 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
          <Box>
            <Typography variant="subtitle2" sx={{ color: 'text.secondary' }}>
              {item.label}
            </Typography>
            <Typography variant="h5" sx={{ fontWeight: 700 }}>
              {item.price}
            </Typography>
          </Box>
          <Tooltip title={item.alertActive ? 'Disable price alerts for this asset. You will no longer receive notifications when price targets are reached.' : 'Enable price alerts for this asset. You will receive notifications when price reaches your configured targets.'} arrow>
            <IconButton
              color={item.alertActive ? 'primary' : 'default'}
              onClick={onToggle}
              sx={{
                borderRadius: 1.5,
                border: item.alertActive ? `1px solid ${dashboardPalette.primary}` : '1px solid rgba(148, 163, 184, 0.2)',
              }}
            >
              {item.alertActive ? <NotificationsActiveIcon /> : <NotificationsOffIcon />}
            </IconButton>
          </Tooltip>
        </Stack>

        <Tooltip title={`24-hour price change: ${item.change24h >= 0 ? 'increased' : 'decreased'} by ${Math.abs(item.change24h).toFixed(2)}%. This shows the price movement over the last 24 hours.`} arrow>
          <Stack direction="row" spacing={1.5} alignItems="center">
            <Chip
              size="small"
              label={`${item.change24h >= 0 ? '+' : ''}${item.change24h.toFixed(2)}%`}
              sx={{
                borderRadius: 1.5,
                color: '#fff',
                backgroundColor: item.change24h >= 0 ? dashboardPalette.accent.positive : dashboardPalette.accent.negative,
                fontWeight: 600,
                cursor: 'help',
              }}
            />
            <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
              24h change
            </Typography>
          </Stack>
        </Tooltip>

        <Stack direction="row" justifyContent="space-between">
          <Typography variant="caption" color="text.secondary">
            Symbol
          </Typography>
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            {item.symbol}
          </Typography>
        </Stack>

        <Stack direction="row" justifyContent="space-between">
          <Typography variant="caption" color="text.secondary">
            Volume
          </Typography>
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            {item.volume}
          </Typography>
        </Stack>
      </CardContent>
    </Card>
  );
};

const AlertsWidget: React.FC<{
  alerts: RecentAlert[];
  onSelect: (alert: RecentAlert) => void;
  onViewAll: () => void;
}> = ({ alerts, onSelect, onViewAll }) => {
  const theme = useTheme();

  return (
    <Card variant="outlined" sx={{ borderRadius: 2 }}>
      <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, p: 3.5 }}>
        <Box sx={{ mb: 1 }}>
          <SectionHeader
            title="Recent Alerts"
            description="Price alerts and portfolio notifications. Click any alert to view details and manage its status."
            tooltip="Alerts notify you when assets reach price targets or when portfolio conditions change. Status colors: Red (new), Blue (acknowledged), Gray (resolved)."
          />
        </Box>
        <List dense sx={{ py: 0 }}>
          {alerts.map((alert) => (
            <Tooltip key={alert.id} title={`${getStatusDescription(alert.status)} Click to view details and manage status.`} arrow placement="left">
              <ListItem disablePadding>
                <ListItemButton sx={{ px: 0, py: 1.5, borderRadius: 1.5 }} onClick={() => onSelect(alert)}>
                  <ListItemText
                    primary={
                      <Typography variant="body2" sx={{ fontWeight: 600, fontSize: '0.875rem' }}>
                        {alert.message}
                      </Typography>
                    }
                    secondary={
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                        {alert.timestamp}
                      </Typography>
                    }
                  />
                  <ListItemSecondaryAction>
                    <Tooltip title={getStatusDescription(alert.status)} arrow>
                      <Chip
                        size="small"
                        label={alert.status}
                        sx={{
                          textTransform: 'capitalize',
                          borderRadius: 1.5,
                          fontWeight: 600,
                          fontSize: '0.75rem',
                          backgroundColor:
                            alert.status === 'new'
                              ? dashboardPalette.accent.negative
                              : alert.status === 'acknowledged'
                                ? dashboardPalette.primary
                                : theme.palette.mode === 'dark'
                                  ? 'rgba(148, 163, 184, 0.2)'
                                  : 'rgba(148, 163, 184, 0.16)',
                          color: alert.status === 'resolved' ? 'text.secondary' : '#fff',
                        }}
                      />
                    </Tooltip>
                  </ListItemSecondaryAction>
                </ListItemButton>
              </ListItem>
            </Tooltip>
          ))}
        </List>
        <Button 
          variant="outlined" 
          size="small" 
          onClick={onViewAll} 
          disabled={!alerts.length}
          sx={{ borderRadius: 2, minHeight: 36, textTransform: 'none' }}
        >
          View alert log
        </Button>
      </CardContent>
    </Card>
  );
};

export const WatchlistSection: React.FC<WatchlistSectionProps> = ({ items, alerts, onToggleAlert }) => {
  const theme = useTheme();
  const [alertLog, setAlertLog] = React.useState<RecentAlert[]>(alerts);
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [activeAlert, setActiveAlert] = React.useState<RecentAlert | null>(null);

  React.useEffect(() => {
    setAlertLog(alerts);
  }, [alerts]);

  const handleSelectAlert = (alert: RecentAlert) => {
    setActiveAlert(alert);
    setDrawerOpen(true);
  };

  const handleViewAll = () => {
    if (alertLog.length === 0) {
      return;
    }
    setActiveAlert(alertLog[0]);
    setDrawerOpen(true);
  };

  const updateAlertStatus = (status: RecentAlert['status']) => {
    if (!activeAlert) {
      return;
    }
    setAlertLog((prev) =>
      prev.map((alert) =>
        alert.id === activeAlert.id
          ? {
              ...alert,
              status,
              timestamp: new Date().toLocaleString(),
            }
          : alert
      )
    );
    setActiveAlert((prev) => (prev ? { ...prev, status } : prev));
  };

  const navigate = useNavigate();

  return (
    <Box component="section" aria-label="Watchlist & Alerts" sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Box sx={{ mb: 1 }}>
        <SectionHeader
          title="Watchlist & Alerts"
          description="Track assets you're monitoring and manage price alerts. Quick access to recent alert triggers and watchlist items."
          variant="h4"
          tooltip="The watchlist lets you track assets without holding them. Alerts notify you when prices reach targets or portfolio conditions change. Click any alert to view details and manage its status."
        />
      </Box>
      <Stack 
        direction={{ xs: 'column', sm: 'row' }} 
        justifyContent="flex-end" 
        alignItems={{ xs: 'flex-start', sm: 'center' }}
        spacing={{ xs: 1.5, sm: 2 }}
        sx={{ width: '100%' }}
      >
        <Tooltip title="Open the full watchlist page to add/remove assets, configure price targets, and manage all alerts." arrow>
          <Button
            variant="outlined"
            size="small"
            endIcon={<ArrowForwardIcon />}
            onClick={() => navigate('/market-watch')}
            sx={{ 
              whiteSpace: 'nowrap', 
              width: { xs: '100%', sm: 'auto' },
              minWidth: { xs: '100%', sm: 'auto' },
              borderRadius: 2,
              textTransform: 'none',
              minHeight: 36,
            }}
          >
            View Full Watchlist
          </Button>
        </Tooltip>
      </Stack>

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', md: '2fr 1fr' },
          gap: { xs: 2.5, md: 3.5 },
        }}
      >
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, minmax(0, 1fr))' },
            gap: { xs: 2.5, md: 3 },
          }}
        >
          {items.map((item) => (
            <Box key={item.id}>
              <WatchlistCard item={item} onToggle={() => onToggleAlert(item.id)} />
            </Box>
          ))}
        </Box>
        <Box>
          <AlertsWidget alerts={alertLog} onSelect={handleSelectAlert} onViewAll={handleViewAll} />
        </Box>
      </Box>

      <Divider />

      <Drawer
        anchor="right"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        PaperProps={{
          sx: {
            width: { xs: '100%', sm: 360 },
            borderRadius: { xs: 0, sm: '16px 0 0 16px' }, // Keep special drawer border
            overflow: 'hidden',
          },
        }}
      >
        <Box sx={{ p: 3.5, display: 'flex', flexDirection: 'column', gap: 2.5, height: '100%' }}>
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              Alert Details
            </Typography>
            <Tooltip title={activeAlert ? getStatusDescription(activeAlert.status) : 'Alert status information'} arrow>
              <Chip
                size="medium"
                label={activeAlert?.status ?? '—'}
                sx={{
                  textTransform: 'capitalize',
                  borderRadius: 1.5,
                  fontWeight: 600,
                  backgroundColor:
                    activeAlert?.status === 'new'
                      ? dashboardPalette.accent.negative
                      : activeAlert?.status === 'acknowledged'
                        ? dashboardPalette.primary
                        : theme.palette.mode === 'dark'
                          ? 'rgba(148, 163, 184, 0.2)'
                          : 'rgba(148, 163, 184, 0.16)',
                  color: activeAlert?.status === 'resolved' ? 'text.secondary' : '#fff',
                }}
              />
            </Tooltip>
          </Stack>

          {activeAlert ? (
            <>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                {activeAlert.message}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Last updated: {activeAlert.timestamp}
              </Typography>

              <Divider />

              <Stack spacing={1.5}>
                <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Suggested action</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.6 }}>
                  Use "Dismiss" when the alert has been handled or "Snooze" to keep it in the log but mark as acknowledged.
                </Typography>
              </Stack>

              <Stack direction="row" spacing={1.5} sx={{ mt: 'auto' }}>
                <Tooltip title="Mark alert as acknowledged. It will remain in your log but won't be highlighted as new. Useful when you've reviewed the alert but want to keep it for reference." arrow>
                  <Button
                    variant="outlined"
                    fullWidth
                    onClick={() => updateAlertStatus('acknowledged')}
                    disabled={activeAlert.status === 'acknowledged'}
                    sx={{ borderRadius: 2, minHeight: 36, textTransform: 'none', fontWeight: 500 }}
                  >
                    Snooze
                  </Button>
                </Tooltip>
                <Tooltip title="Mark alert as resolved and remove it from active alerts. Use this when you've taken action on the alert or it's no longer relevant." arrow>
                  <Button
                    variant="contained"
                    color="success"
                    fullWidth
                    onClick={() => updateAlertStatus('resolved')}
                    disabled={activeAlert.status === 'resolved'}
                    sx={{ borderRadius: 2, minHeight: 36, textTransform: 'none', fontWeight: 600 }}
                  >
                    Dismiss
                  </Button>
                </Tooltip>
              </Stack>
            </>
          ) : (
            <Typography variant="body2" color="text.secondary">
              Select an alert to view details.
            </Typography>
          )}
        </Box>
      </Drawer>
    </Box>
  );
};


