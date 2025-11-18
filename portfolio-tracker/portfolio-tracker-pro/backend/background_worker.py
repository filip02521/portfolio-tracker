"""
Background Worker for Monitoring Price Alerts
Runs periodically to check if any price alerts should be triggered
"""
import asyncio
import logging
import schedule
import threading
from datetime import datetime
from typing import Dict, List
from price_alert_service import PriceAlertService
from market_data_service import MarketDataService
from backup_service import BackupService
from logging_config import get_logger

logger = get_logger(__name__)

class PriceAlertWorker:
    def __init__(
        self,
        alert_service: PriceAlertService,
        market_service: MarketDataService,
        check_interval: int = 60  # Check every 60 seconds
    ):
        self.alert_service = alert_service
        self.market_service = market_service
        self.check_interval = check_interval
        self.running = False
        self._task = None
        
    async def check_all_alerts(self):
        """Check all active alerts for all users"""
        try:
            # Get all users (in production, this would come from a database)
            # For now, we'll use a simple approach - check alerts stored in service
            # This is a simplified version - in production, you'd query a database
            
            # Get all users from alert service (stored in _alerts dict)
            users = list(self.alert_service._alerts.keys())
            
            if not users:
                logger.debug("No users with alerts to check")
                return
            
            triggered_count = 0
            
            for user_id in users:
                try:
                    alerts = self.alert_service.get_alerts(user_id)
                    active_alerts = [a for a in alerts if a.get('active') and not a.get('triggered')]
                    
                    if not active_alerts:
                        continue
                    
                    # Get unique symbols from active alerts
                    symbols = list(set([a['symbol'] for a in active_alerts]))
                    
                    # Fetch current prices and market data
                    current_prices = {}
                    market_data = {}
                    dd_scores = {}
                    for symbol in symbols:
                        try:
                            # Get price
                            price_data = self.market_service.get_price(symbol, priority='low')
                            if price_data:
                                current_prices[symbol] = price_data['price']
                                # Get extended market data for RSI, volume, etc.
                                extended_data = self.market_service.get_market_data(symbol)
                                if extended_data:
                                    market_data[symbol] = extended_data
                        except Exception as e:
                            logger.warning(f"Error fetching data for {symbol}: {e}")
                            continue
                    
                    # Fetch DD scores if needed (check if any alerts require DD scores)
                    alerts_needing_dd = [a for a in active_alerts if a.get('condition') == 'dd_score_below']
                    if alerts_needing_dd:
                        from due_diligence_service import DueDiligenceService
                        dd_service = DueDiligenceService(market_data_service=self.market_service)
                        for symbol in symbols:
                            try:
                                dd_result = dd_service.evaluate(symbol, force_refresh=False)
                                if dd_result and dd_result.normalized_score is not None:
                                    dd_scores[symbol] = dd_result.normalized_score
                            except Exception as e:
                                logger.warning(f"Error fetching DD score for {symbol}: {e}")
                                continue
                    
                    # Check alerts for this user
                    if current_prices:
                        triggered = self.alert_service.check_alerts(
                            user_id, 
                            current_prices,
                            market_data=market_data if market_data else None,
                            dd_scores=dd_scores if dd_scores else None
                        )
                        if triggered:
                            triggered_count += len(triggered)
                            logger.info(f"User {user_id}: {len(triggered)} alert(s) triggered")
                            
                            # In production, you would:
                            # 1. Send push notification to user
                            # 2. Send email notification
                            # 3. Store notification in database
                            # 4. Update user's notification preferences
                            
                except Exception as e:
                    logger.error(f"Error checking alerts for user {user_id}: {e}")
                    continue
            
            if triggered_count > 0:
                logger.info(f"Total alerts triggered: {triggered_count}")
                
        except Exception as e:
            logger.error(f"Error in check_all_alerts: {e}")
    
    async def run(self):
        """Main worker loop"""
        self.running = True
        logger.info(f"Price Alert Worker started (check interval: {self.check_interval}s)")
        
        while self.running:
            try:
                await self.check_all_alerts()
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
            
            # Wait before next check
            await asyncio.sleep(self.check_interval)
    
    def start(self):
        """Start the worker in background"""
        if not self.running:
            self._task = asyncio.create_task(self.run())
            logger.info("Background worker task created")
    
    def stop(self):
        """Stop the worker"""
        self.running = False
        if self._task:
            self._task.cancel()
            logger.info("Background worker stopped")
    
    async def check_once(self):
        """Perform a single check (for testing)"""
        await self.check_all_alerts()

# Global worker instance
_worker: PriceAlertWorker = None

def initialize_worker(
    alert_service: PriceAlertService,
    market_service: MarketDataService,
    check_interval: int = 60
) -> PriceAlertWorker:
    """Initialize and start the background worker"""
    global _worker
    if _worker is None:
        _worker = PriceAlertWorker(alert_service, market_service, check_interval)
        _worker.start()
    return _worker

def get_worker() -> PriceAlertWorker:
    """Get the global worker instance"""
    return _worker

def stop_worker():
    """Stop the global worker"""
    global _worker
    if _worker:
        _worker.stop()
        _worker = None


class BackupScheduler:
    """Scheduler for automated backups"""
    
    def __init__(self, backup_service: BackupService, backup_time: str = "02:00"):
        """
        Initialize backup scheduler
        
        Args:
            backup_service: BackupService instance
            backup_time: Time to run daily backup (HH:MM format, default: 02:00)
        """
        self.backup_service = backup_service
        self.backup_time = backup_time
        self.running = False
        self._thread = None
        logger.info(f"BackupScheduler initialized (daily backup at {backup_time})")
    
    def _run_backup(self):
        """Run backup job"""
        try:
            logger.info("Starting scheduled backup...")
            result = self.backup_service.create_backup(description="Scheduled daily backup")
            if result.get('success'):
                logger.info(f"Scheduled backup completed: {result['backup_id']}")
            else:
                logger.error(f"Scheduled backup failed: {result.get('error')}")
        except Exception as e:
            logger.error(f"Error in scheduled backup: {e}", exc_info=True)
    
    def _cleanup_old_backups(self):
        """Cleanup old backups job"""
        try:
            logger.info("Starting scheduled backup cleanup...")
            result = self.backup_service.delete_old_backups(days=30, keep_minimum=5)
            logger.info(f"Backup cleanup completed: {result['deleted_count']} deleted, {result['kept_count']} kept")
        except Exception as e:
            logger.error(f"Error in backup cleanup: {e}", exc_info=True)
    
    def _scheduler_loop(self):
        """Main scheduler loop (runs in separate thread)"""
        # Schedule daily backup
        schedule.every().day.at(self.backup_time).do(self._run_backup)
        
        # Schedule weekly cleanup (every Sunday at 03:00)
        schedule.every().sunday.at("03:00").do(self._cleanup_old_backups)
        
        logger.info("Backup scheduler started")
        
        while self.running:
            schedule.run_pending()
            import time
            time.sleep(60)  # Check every minute
    
    def start(self):
        """Start the scheduler in a background thread"""
        if self.running:
            logger.warning("Backup scheduler already running")
            return
        
        self.running = True
        self._thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._thread.start()
        logger.info("Backup scheduler thread started")
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        schedule.clear()
        logger.info("Backup scheduler stopped")


