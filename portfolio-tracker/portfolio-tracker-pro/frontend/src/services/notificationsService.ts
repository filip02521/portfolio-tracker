import { logger } from '../utils/logger';

export interface Notification {
  id: string;
  type: 'alert' | 'sync' | 'info' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  actionUrl?: string;
  actionLabel?: string;
  metadata?: Record<string, unknown>;
}

interface NotificationsStorage {
  notifications: Notification[];
  lastSync: string;
}

class NotificationsService {
  private readonly STORAGE_KEY = 'portfolio_notifications';
  private readonly MAX_NOTIFICATIONS = 100;
  private listeners: Set<(notifications: Notification[]) => void> = new Set();

  /**
   * Get all notifications from storage
   */
  getNotifications(): Notification[] {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
      if (!stored) {
        return [];
      }
      const data: NotificationsStorage = JSON.parse(stored);
      return data.notifications || [];
    } catch (error) {
      logger.error('Failed to load notifications from storage', error);
      return [];
    }
  }

  /**
   * Save notifications to storage
   */
  private saveNotifications(notifications: Notification[]): void {
    try {
      const data: NotificationsStorage = {
        notifications: notifications.slice(0, this.MAX_NOTIFICATIONS),
        lastSync: new Date().toISOString(),
      };
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(data));
      this.notifyListeners(notifications);
    } catch (error) {
      logger.error('Failed to save notifications to storage', error);
    }
  }

  /**
   * Add a new notification
   */
  addNotification(notification: Omit<Notification, 'id' | 'timestamp' | 'read'>): Notification {
    const newNotification: Notification = {
      ...notification,
      id: `notification-${Date.now()}-${Math.random().toString(36).slice(2)}`,
      timestamp: new Date().toISOString(),
      read: false,
    };

    const notifications = this.getNotifications();
    notifications.unshift(newNotification); // Add to beginning
    this.saveNotifications(notifications);

    return newNotification;
  }

  /**
   * Mark notification as read
   */
  markAsRead(notificationId: string): void {
    const notifications = this.getNotifications();
    const notification = notifications.find((n) => n.id === notificationId);
    if (notification) {
      notification.read = true;
      this.saveNotifications(notifications);
    }
  }

  /**
   * Mark all notifications as read
   */
  markAllAsRead(): void {
    const notifications = this.getNotifications();
    notifications.forEach((n) => {
      n.read = true;
    });
    this.saveNotifications(notifications);
  }

  /**
   * Delete a notification
   */
  deleteNotification(notificationId: string): void {
    const notifications = this.getNotifications();
    const filtered = notifications.filter((n) => n.id !== notificationId);
    this.saveNotifications(filtered);
  }

  /**
   * Clear all notifications
   */
  clearAll(): void {
    this.saveNotifications([]);
  }

  /**
   * Get unread count
   */
  getUnreadCount(): number {
    return this.getNotifications().filter((n) => !n.read).length;
  }

  /**
   * Get notifications by type
   */
  getNotificationsByType(type: Notification['type']): Notification[] {
    return this.getNotifications().filter((n) => n.type === type);
  }

  /**
   * Get notifications grouped by date
   */
  getNotificationsGroupedByDate(): Record<string, Notification[]> {
    const notifications = this.getNotifications();
    const grouped: Record<string, Notification[]> = {};

    notifications.forEach((notification) => {
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
  }

  /**
   * Subscribe to notifications changes
   */
  subscribe(listener: (notifications: Notification[]) => void): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  /**
   * Notify all listeners
   */
  private notifyListeners(notifications: Notification[]): void {
    this.listeners.forEach((listener) => {
      try {
        listener(notifications);
      } catch (error) {
        logger.error('Error in notification listener', error);
      }
    });
  }

  /**
   * Sync notifications from external sources (price alerts, sync summary, etc.)
   */
  syncFromExternalSources(priceAlerts: any[], syncSummary: any): void {
    const notifications: Notification[] = [];

    // Add price alert notifications
    if (priceAlerts && priceAlerts.length > 0) {
      priceAlerts
        .filter((alert) => alert?.triggered && !alert?.read)
        .forEach((alert) => {
          notifications.push({
            id: `price-alert-${alert.id}`,
            type: 'alert',
            title: 'Price Alert Triggered',
            message: `${alert.symbol} ${alert.condition === 'below' ? '≤' : '≥'} ${alert.price}`,
            timestamp: alert.triggered_at || alert.updated_at || new Date().toISOString(),
            read: false,
            actionUrl: '/price-alerts',
            actionLabel: 'View Alerts',
            metadata: { alertId: alert.id, symbol: alert.symbol },
          });
        });
    }

    // Add sync summary notification
    if (syncSummary && syncSummary.count > 0) {
      notifications.push({
        id: 'sync-summary',
        type: 'sync',
        title: 'New Trades Detected',
        message: `${syncSummary.count} new trade${syncSummary.count === 1 ? '' : 's'} imported from ${syncSummary.exchanges?.join(', ') || 'exchanges'}`,
        timestamp: new Date().toISOString(),
        read: false,
        actionUrl: '/transactions',
        actionLabel: 'View Transactions',
        metadata: { count: syncSummary.count, exchanges: syncSummary.exchanges },
      });
    }

    // Merge with existing notifications (avoid duplicates)
    const existing = this.getNotifications();
    const existingIds = new Set(existing.map((n) => n.id));
    const newNotifications = notifications.filter((n) => !existingIds.has(n.id));

    if (newNotifications.length > 0) {
      const allNotifications = [...newNotifications, ...existing];
      this.saveNotifications(allNotifications);
    }
  }
}

export const notificationsService = new NotificationsService();

