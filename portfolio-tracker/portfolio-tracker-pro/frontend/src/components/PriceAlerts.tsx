import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  IconButton,
  Chip,
  Switch,
  FormControlLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import {
  Add,
  Edit,
  Delete,
  TrendingUp,
  TrendingDown,
} from '@mui/icons-material';
import { useToast, Toast } from './common/Toast';
import { EmptyState } from './common/EmptyState';
import { portfolioService } from '../services/portfolioService';
import { notificationManager } from '../utils/notifications';
import { logger } from '../utils/logger';

interface PriceAlert {
  id: number;
  symbol: string;
  name: string;
  condition: 'above' | 'below';
  price: number;
  active: boolean;
  triggered: boolean;
}

const PriceAlerts: React.FC = () => {
  const { toast, showToast, hideToast } = useToast();
  const [alerts, setAlerts] = useState<PriceAlert[]>([]);
  const [open, setOpen] = useState(false);
  const [editingAlert, setEditingAlert] = useState<PriceAlert | null>(null);
  const [notificationPermission, setNotificationPermission] = useState<NotificationPermission>(
    'Notification' in window ? Notification.permission : 'denied'
  );
  const [formData, setFormData] = useState({
    symbol: '',
    condition: 'above' as 'above' | 'below',
    price: '',
  });

  const fetchAlerts = useCallback(async () => {
    try {
      const alertsData = await portfolioService.getPriceAlerts();
      setAlerts(alertsData);
    } catch (error: any) {
      logger.error('Error fetching alerts:', error);
      showToast('Failed to load price alerts', 'error');
      // Fallback to empty array
      setAlerts([]);
    }
  }, [showToast]);

  useEffect(() => {
    fetchAlerts();
    
    // Request notification permission if not already granted/denied
    if ('Notification' in window && Notification.permission === 'default') {
      // Don't auto-request, wait for user to create an alert
    } else if ('Notification' in window) {
      setNotificationPermission(Notification.permission);
    }
  }, [fetchAlerts]);

  const handleRequestNotificationPermission = async () => {
    const granted = await notificationManager.requestPermissionWithContext(
      'Enable browser notifications to receive instant alerts when your price targets are reached.'
    );
    setNotificationPermission(Notification.permission);
    
    if (granted) {
      showToast('Notifications enabled! You will receive alerts when prices reach your targets.', 'success');
    } else {
      showToast('Notification permission denied. You can enable it later in your browser settings.', 'info');
    }
  };

  const handleOpen = (alert?: PriceAlert) => {
    if (alert) {
      setEditingAlert(alert);
      setFormData({
        symbol: alert.symbol,
        condition: alert.condition,
        price: alert.price.toString(),
      });
    } else {
      setEditingAlert(null);
      setFormData({
        symbol: '',
        condition: 'above',
        price: '',
      });
    }
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    setEditingAlert(null);
  };

  const handleSubmit = async () => {
    try {
      if (!formData.symbol || !formData.price) {
        showToast('Please fill in all required fields', 'warning');
        return;
      }

      if (editingAlert) {
        // Update alert
        await portfolioService.updatePriceAlert(editingAlert.id, {
          condition: formData.condition,
          price: parseFloat(formData.price),
        });
        showToast('Price alert updated successfully', 'success');
      } else {
        // Create new alert
        await portfolioService.createPriceAlert({
          symbol: formData.symbol,
          condition: formData.condition,
          price: parseFloat(formData.price),
        });
        
        // Request notification permission when creating first alert if not already requested
        if (notificationPermission === 'default' && 'Notification' in window) {
          const granted = await notificationManager.requestPermissionWithContext(
            'Enable notifications to get instant alerts when prices reach your target levels.'
          );
          setNotificationPermission(Notification.permission);
          if (granted) {
            showToast('Price alert created! Notifications enabled - you will be notified when the target is reached.', 'success');
          } else {
            showToast('Price alert created! Enable notifications in browser settings to receive alerts.', 'info');
          }
        } else {
          showToast('Price alert created successfully', 'success');
        }
      }
      
      await fetchAlerts();
      
      handleClose();
    } catch (error: any) {
      logger.error('Error saving alert:', error);
      showToast(error?.message || 'Failed to save price alert', 'error');
    }
  };

  const handleToggle = async (alertId: number) => {
    try {
      const alert = alerts.find(a => a.id === alertId);
      if (!alert) return;
      
      await portfolioService.updatePriceAlert(alertId, {
        active: !alert.active
      });
      
      await fetchAlerts();
      showToast(
        `Price alert ${alert.active ? 'disabled' : 'enabled'}`,
        'success'
      );
    } catch (error: any) {
      logger.error('Error toggling alert:', error);
      showToast('Failed to update alert', 'error');
    }
  };

  const handleDelete = async (alertId: number) => {
    if (window.confirm('Are you sure you want to delete this price alert?')) {
      try {
        await portfolioService.deletePriceAlert(alertId);
        await fetchAlerts();
        showToast('Price alert deleted successfully', 'success');
      } catch (error: any) {
        logger.error('Error deleting alert:', error);
        showToast('Failed to delete alert', 'error');
      }
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h5" sx={{ fontWeight: 600, mb: 1 }}>
            Price Alerts
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Get notified when prices reach your target levels
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          {notificationPermission !== 'granted' && (
            <Button
              variant="outlined"
              size="small"
              onClick={handleRequestNotificationPermission}
              sx={{ whiteSpace: 'nowrap' }}
            >
              Enable Notifications
            </Button>
          )}
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => handleOpen()}
          >
            Create Alert
          </Button>
        </Box>
      </Box>

      {alerts.length === 0 ? (
        <Card>
          <CardContent>
            <EmptyState
              type="insights"
              title="No Price Alerts"
              message="Create price alerts to get notified when your watched assets reach specific price levels."
              actionLabel="Create Your First Alert"
              onAction={() => handleOpen()}
            />
          </CardContent>
        </Card>
      ) : (
        <TableContainer component={Paper} sx={{ bgcolor: 'background.paper' }}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 600 }}>Asset</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Condition</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Target Price</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Status</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {alerts.map((alert) => (
                <TableRow key={alert.id} hover>
                  <TableCell>
                    <Box>
                      <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                        {alert.symbol}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {alert.name}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip
                      icon={alert.condition === 'above' ? <TrendingUp /> : <TrendingDown />}
                      label={alert.condition === 'above' ? 'Above' : 'Below'}
                      size="small"
                      color={alert.condition === 'above' ? 'success' : 'error'}
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      ${alert.price.toLocaleString()}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={alert.active}
                          onChange={() => handleToggle(alert.id)}
                          size="small"
                          color="primary"
                        />
                      }
                      label={alert.active ? 'Active' : 'Inactive'}
                      sx={{ m: 0 }}
                    />
                  </TableCell>
                  <TableCell align="right">
                    <IconButton
                      size="small"
                      onClick={() => handleOpen(alert)}
                      sx={{ mr: 1 }}
                    >
                      <Edit fontSize="small" />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => handleDelete(alert.id)}
                      color="error"
                    >
                      <Delete fontSize="small" />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingAlert ? 'Edit Price Alert' : 'Create Price Alert'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, pt: 1 }}>
            <TextField
              label="Asset Symbol"
              value={formData.symbol}
              onChange={(e) => setFormData({ ...formData, symbol: e.target.value.toUpperCase() })}
              placeholder="e.g., BTC, ETH, AAPL"
              fullWidth
              required
            />
            <TextField
              select
              label="Alert Condition"
              value={formData.condition}
              onChange={(e) => setFormData({ ...formData, condition: e.target.value as 'above' | 'below' })}
              fullWidth
              required
            >
              <MenuItem value="above">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <TrendingUp fontSize="small" />
                  <Typography>Alert when price goes above</Typography>
                </Box>
              </MenuItem>
              <MenuItem value="below">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <TrendingDown fontSize="small" />
                  <Typography>Alert when price goes below</Typography>
                </Box>
              </MenuItem>
            </TextField>
            <TextField
              label="Target Price (USD)"
              type="number"
              value={formData.price}
              onChange={(e) => setFormData({ ...formData, price: e.target.value })}
              placeholder="0.00"
              fullWidth
              required
              InputProps={{
                startAdornment: <Typography sx={{ mr: 1 }}>$</Typography>,
              }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingAlert ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      <Toast
        open={toast.open}
        message={toast.message}
        severity={toast.severity}
        onClose={hideToast}
      />
    </Box>
  );
};

export default PriceAlerts;

