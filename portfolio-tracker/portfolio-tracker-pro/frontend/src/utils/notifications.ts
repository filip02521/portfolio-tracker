/**
 * Browser Notifications Utility
 * Handles browser notification permission and sending notifications
 */

export class NotificationManager {
  private static instance: NotificationManager | null = null;
  private permission: NotificationPermission = 'default';

  private constructor() {
    // Check if browser supports notifications
    if ('Notification' in window) {
      this.permission = Notification.permission;
    }
  }

  public static getInstance(): NotificationManager {
    if (!NotificationManager.instance) {
      NotificationManager.instance = new NotificationManager();
    }
    return NotificationManager.instance;
  }

  /**
   * Request notification permission from user
   */
  public async requestPermission(): Promise<NotificationPermission> {
    if (!('Notification' in window)) {
      console.warn('This browser does not support notifications');
      return 'denied';
    }

    if (this.permission === 'default') {
      this.permission = await Notification.requestPermission();
    }

    return this.permission;
  }

  /**
   * Check if notifications are allowed
   */
  public isAllowed(): boolean {
    return 'Notification' in window && Notification.permission === 'granted';
  }

  /**
   * Send a notification
   */
  public sendNotification(
    title: string,
    options?: NotificationOptions
  ): Notification | null {
    if (!this.isAllowed()) {
      console.warn('Notifications are not allowed. Request permission first.');
      return null;
    }

    const defaultOptions: NotificationOptions = {
      icon: '/favicon.ico',
      badge: '/favicon.ico',
      tag: 'price-alert',
      requireInteraction: false,
      silent: false,
      ...options,
    };

    try {
      const notification = new Notification(title, defaultOptions);
      
      // Auto-close after 5 seconds (unless requireInteraction is true)
      if (!defaultOptions.requireInteraction) {
        setTimeout(() => {
          notification.close();
        }, 5000);
      }

      // Handle notification click
      notification.onclick = () => {
        window.focus();
        notification.close();
      };

      return notification;
    } catch (error) {
      console.error('Error sending notification:', error);
      return null;
    }
  }

  /**
   * Send price alert notification
   */
  public sendPriceAlert(
    symbol: string,
    message: string,
    currentPrice: number,
    targetPrice: number,
    condition: 'above' | 'below'
  ): Notification | null {
    const title = `${symbol} Price Alert`;
    const body = `${symbol} price is now $${currentPrice.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })} - ${message}`;

    return this.sendNotification(title, {
      body,
      icon: '/favicon.ico',
      badge: '/favicon.ico',
      tag: `price-alert-${symbol}`,
      requireInteraction: true,
      data: {
        symbol,
        currentPrice,
        targetPrice,
        condition,
        type: 'price-alert',
      },
    });
  }

  /**
   * Request permission with user-friendly context
   */
  public async requestPermissionWithContext(
    context?: string
  ): Promise<boolean> {
    if (this.isAllowed()) {
      return true;
    }

    const defaultMessage =
      context ||
      'Enable notifications to get instant alerts when prices reach your target levels.';

    // You can show a custom dialog here before requesting permission
    // For now, we'll just request directly

    const permission = await this.requestPermission();
    return permission === 'granted';
  }
}

export const notificationManager = NotificationManager.getInstance();


