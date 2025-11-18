import { useEffect, useCallback, useRef } from 'react';
import { portfolioService } from '../services/portfolioService';
import { notificationManager } from '../utils/notifications';

interface TriggeredAlert {
  alert_id: number;
  symbol: string;
  condition: 'above' | 'below';
  target_price: number;
  current_price: number;
  message: string;
}

export const usePriceAlerts = (enabled: boolean = true, interval: number = 60000) => {
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const checkedAlertsRef = useRef<Set<number>>(new Set());

  const checkAlerts = useCallback(async () => {
    try {
      const result = await portfolioService.checkPriceAlerts();
      const triggered = result.triggered || [];

      triggered.forEach((alert: TriggeredAlert) => {
        // Avoid duplicate notifications for the same alert
        if (checkedAlertsRef.current.has(alert.alert_id)) {
          return;
        }

        checkedAlertsRef.current.add(alert.alert_id);

        // Send browser notification
        if (notificationManager.isAllowed()) {
          notificationManager.sendPriceAlert(
            alert.symbol,
            alert.message,
            alert.current_price,
            alert.target_price,
            alert.condition
          );
        }

      // Log notification (toast will be handled by parent component if needed)
      console.log(`${alert.symbol} Alert: ${alert.message}`);
    });
  } catch (error: any) {
    console.error('Error checking price alerts:', error);
    // Don't show error toast to avoid spamming
  }
}, []);

  const startMonitoring = useCallback(() => {
    if (!enabled) {
      return;
    }

    // Request notification permission on first start
    if (notificationManager.isAllowed() === false && Notification.permission === 'default') {
      notificationManager.requestPermissionWithContext(
        'Enable notifications to receive price alerts when your targets are reached.'
      );
    }

    // Check immediately
    checkAlerts();

    // Then check at intervals
    intervalRef.current = setInterval(() => {
      checkAlerts();
    }, interval);
  }, [enabled, interval, checkAlerts]);

  const stopMonitoring = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    checkedAlertsRef.current.clear();
  }, []);

  useEffect(() => {
    if (enabled) {
      startMonitoring();
    } else {
      stopMonitoring();
    }

    return () => {
      stopMonitoring();
    };
  }, [enabled, startMonitoring, stopMonitoring]);

  return {
    checkAlerts,
    startMonitoring,
    stopMonitoring,
    isMonitoring: intervalRef.current !== null,
  };
};

