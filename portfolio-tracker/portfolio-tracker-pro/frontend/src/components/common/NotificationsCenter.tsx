import React, { useState, useEffect, useMemo } from 'react';
import {
  Drawer,
  Box,
  Typography,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  IconButton,
  Chip,
  Divider,
  Button,
  Stack,
  useTheme,
  alpha,
  Badge,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import NotificationsIcon from '@mui/icons-material/Notifications';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WarningIcon from '@mui/icons-material/Warning';
import ErrorIcon from '@mui/icons-material/Error';
import InfoIcon from '@mui/icons-material/Info';
import SyncIcon from '@mui/icons-material/Sync';
import DeleteIcon from '@mui/icons-material/Delete';
import { notificationsService, Notification } from '../../services/notificationsService';
import { useNavigate } from 'react-router-dom';

export interface NotificationsCenterProps {
  open: boolean;
  onClose: () => void;
}

const getNotificationIcon = (type: Notification['type']): React.ReactNode => {
  switch (type) {
    case 'alert':
      return <NotificationsActiveIcon fontSize="small" />;
    case 'sync':
      return <SyncIcon fontSize="small" />;
    case 'warning':
      return <WarningIcon fontSize="small" />;
    case 'error':
      return <ErrorIcon fontSize="small" />;
    case 'info':
    default:
      return <InfoIcon fontSize="small" />;
  }
};

const getNotificationColor = (type: Notification['type'], theme: any): string => {
  switch (type) {
    case 'alert':
      return theme.palette.warning.main;
    case 'sync':
      return theme.palette.info.main;
    case 'warning':
      return theme.palette.warning.main;
    case 'error':
      return theme.palette.error.main;
    case 'info':
    default:
      return theme.palette.info.main;
  }
};

export const NotificationsCenter: React.FC<NotificationsCenterProps> = ({ open, onClose }) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [filter, setFilter] = useState<'all' | 'unread' | Notification['type']>('all');

  // Load notifications and subscribe to changes
  useEffect(() => {
    setNotifications(notificationsService.getNotifications());

    const unsubscribe = notificationsService.subscribe((updatedNotifications) => {
      setNotifications(updatedNotifications);
    });

    return unsubscribe;
  }, []);

  // Filter notifications
  const filteredNotifications = useMemo(() => {
    let filtered = notifications;

    if (filter === 'unread') {
      filtered = filtered.filter((n) => !n.read);
    } else if (filter !== 'all') {
      filtered = filtered.filter((n) => n.type === filter);
    }

    return filtered;
  }, [notifications, filter]);

  // Group by date
  const groupedNotifications = useMemo(() => {
    const grouped: Record<string, Notification[]> = {};
    filteredNotifications.forEach((notification) => {
      const date = new Date(notification.timestamp);
      const today = new Date();
      const yesterday = new Date(today);
      yesterday.setDate(yesterday.getDate() - 1);

      let key: string;
      if (date.toDateString() === today.toDateString()) {
        key = 'Today';
      } else if (date.toDateString() === yesterday.toDateString()) {
        key = 'Yesterday';
      } else {
        key = date.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
      }

      if (!grouped[key]) {
        grouped[key] = [];
      }
      grouped[key].push(notification);
    });

    return grouped;
  }, [filteredNotifications]);

  const unreadCount = useMemo(() => {
    return notifications.filter((n) => !n.read).length;
  }, [notifications]);

  const handleMarkAsRead = (notificationId: string) => {
    notificationsService.markAsRead(notificationId);
  };

  const handleMarkAllAsRead = () => {
    notificationsService.markAllAsRead();
  };

  const handleDelete = (notificationId: string) => {
    notificationsService.deleteNotification(notificationId);
  };

  const handleClearAll = () => {
    notificationsService.clearAll();
  };

  const handleNotificationClick = (notification: Notification) => {
    handleMarkAsRead(notification.id);
    if (notification.actionUrl) {
      navigate(notification.actionUrl);
      onClose();
    }
  };

  const formatTime = (timestamp: string): string => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) {
      return 'Just now';
    } else if (diffMins < 60) {
      return `${diffMins}m ago`;
    } else if (diffHours < 24) {
      return `${diffHours}h ago`;
    } else if (diffDays < 7) {
      return `${diffDays}d ago`;
    } else {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
  };

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      PaperProps={{
        sx: {
          width: { xs: '100%', sm: 400 },
          borderRadius: { xs: 0, sm: '16px 0 0 16px' },
        },
      }}
    >
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        {/* Header */}
        <Box
          sx={{
            p: 2,
            borderBottom: `1px solid ${theme.palette.divider}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <Stack direction="row" spacing={1.5} alignItems="center">
            <Badge badgeContent={unreadCount} color="error">
              <NotificationsIcon />
            </Badge>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              Notifications
            </Typography>
          </Stack>
          <Stack direction="row" spacing={1}>
            {unreadCount > 0 && (
              <Button size="small" onClick={handleMarkAllAsRead} sx={{ textTransform: 'none' }}>
                Mark all read
              </Button>
            )}
            <IconButton size="small" onClick={onClose}>
              <CloseIcon />
            </IconButton>
          </Stack>
        </Box>

        {/* Filters */}
        <Box sx={{ p: 2, borderBottom: `1px solid ${theme.palette.divider}` }}>
          <Stack direction="row" spacing={1} flexWrap="wrap">
            {(['all', 'unread', 'alert', 'sync', 'info'] as const).map((filterOption) => (
              <Chip
                key={filterOption}
                label={filterOption.charAt(0).toUpperCase() + filterOption.slice(1)}
                onClick={() => setFilter(filterOption)}
                color={filter === filterOption ? 'primary' : 'default'}
                size="small"
                sx={{ textTransform: 'capitalize' }}
              />
            ))}
          </Stack>
        </Box>

        {/* Notifications List */}
        <Box sx={{ flex: 1, overflow: 'auto' }}>
          {Object.keys(groupedNotifications).length === 0 ? (
            <Box sx={{ p: 3, textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                No notifications
              </Typography>
            </Box>
          ) : (
            <List sx={{ p: 0 }}>
              {Object.entries(groupedNotifications).map(([dateKey, dateNotifications]) => (
                <React.Fragment key={dateKey}>
                  <Box sx={{ px: 2, py: 1 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                      {dateKey}
                    </Typography>
                  </Box>
                  {dateNotifications.map((notification) => {
                    const color = getNotificationColor(notification.type, theme);
                    return (
                      <ListItem
                        key={notification.id}
                        disablePadding
                        sx={{
                          backgroundColor: notification.read
                            ? 'transparent'
                            : alpha(color, 0.05),
                          borderLeft: notification.read ? undefined : `3px solid ${color}`,
                        }}
                      >
                        <ListItemButton
                          onClick={() => handleNotificationClick(notification)}
                          sx={{ py: 1.5, px: 2 }}
                        >
                          <ListItemIcon sx={{ minWidth: 40 }}>
                            <Box sx={{ color }}>{getNotificationIcon(notification.type)}</Box>
                          </ListItemIcon>
                          <ListItemText
                            primary={
                              <Stack direction="row" spacing={1} alignItems="center">
                                <Typography variant="body2" sx={{ fontWeight: notification.read ? 400 : 600 }}>
                                  {notification.title}
                                </Typography>
                                {!notification.read && (
                                  <Chip
                                    label="New"
                                    size="small"
                                    sx={{
                                      height: 16,
                                      fontSize: '0.65rem',
                                      backgroundColor: color,
                                      color: 'white',
                                    }}
                                  />
                                )}
                              </Stack>
                            }
                            secondary={
                              <Stack spacing={0.5}>
                                <Typography variant="caption" color="text.secondary">
                                  {notification.message}
                                </Typography>
                                <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                                  {formatTime(notification.timestamp)}
                                </Typography>
                              </Stack>
                            }
                          />
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDelete(notification.id);
                            }}
                            sx={{ ml: 1 }}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </ListItemButton>
                      </ListItem>
                    );
                  })}
                  <Divider />
                </React.Fragment>
              ))}
            </List>
          )}
        </Box>

        {/* Footer */}
        {notifications.length > 0 && (
          <Box
            sx={{
              p: 2,
              borderTop: `1px solid ${theme.palette.divider}`,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <Typography variant="caption" color="text.secondary">
              {notifications.length} notification{notifications.length !== 1 ? 's' : ''}
            </Typography>
            <Button size="small" onClick={handleClearAll} color="error" sx={{ textTransform: 'none' }}>
              Clear all
            </Button>
          </Box>
        )}
      </Box>
    </Drawer>
  );
};

