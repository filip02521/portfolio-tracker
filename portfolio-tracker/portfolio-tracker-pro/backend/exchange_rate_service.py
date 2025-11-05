"""
Exchange Rate Service for Portfolio Tracker Pro
Manages USD to PLN exchange rates with caching and multiple API sources
"""
import requests
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
import time
import logging

logger = logging.getLogger(__name__)

class ExchangeRateService:
    """Service for managing USD/PLN exchange rates"""
    
    def __init__(self):
        self.cache: Dict[str, float] = {}
        self.cache_timestamp: Optional[float] = None
        self.cache_ttl = 3600  # Cache for 1 hour
        self.fallback_rate = 4.0
        
        # API endpoints
        self.exchangerate_api = "https://api.exchangerate-api.com/v4/latest/USD"
        self.nbp_api_base = "https://api.nbp.pl/api/exchangerates/rates/A/USD"
        self.last_request_time = 0
        self.min_request_interval = 0.5  # NBP rate limit
    
    def _wait_for_rate_limit(self):
        """Respect API rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()
    
    def get_current_rate(self) -> float:
        """
        Get current USD to PLN exchange rate
        Uses cached value if available and fresh
        
        Returns:
            Exchange rate as float
        """
        # Check cache first
        if self.cache_timestamp:
            age = time.time() - self.cache_timestamp
            if age < self.cache_ttl and 'current' in self.cache:
                return self.cache['current']
        
        # Try exchangerate-api.com first (free, no auth needed)
        try:
            response = requests.get(self.exchangerate_api, timeout=5)
            if response.status_code == 200:
                data = response.json()
                rate = data['rates'].get('PLN')
                if rate:
                    self.cache['current'] = rate
                    self.cache_timestamp = time.time()
                    return rate
        except Exception as e:
            logger.warning(f"Error fetching rate from exchangerate-api: {e}")
        
        # Fallback to NBP API (Polish National Bank - more reliable for PLN)
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            rate = self.get_rate_for_date(today)
            if rate:
                self.cache['current'] = rate
                self.cache_timestamp = time.time()
                return rate
        except Exception as e:
            logger.warning(f"Error fetching rate from NBP API: {e}")
        
        # Last resort: use cached value if available (even if stale)
        if 'current' in self.cache:
            logger.warning("Using stale cached exchange rate")
            return self.cache['current']
        
        # Final fallback
        logger.warning(f"Using fallback exchange rate: {self.fallback_rate}")
        return self.fallback_rate
    
    def get_rate_for_date(self, date: str) -> Optional[float]:
        """
        Get USD/PLN exchange rate for a specific date
        
        Args:
            date: Date in YYYY-MM-DD format
            
        Returns:
            Exchange rate as float or None if not found
        """
        # Check cache first
        if date in self.cache:
            return self.cache[date]
        
        # Use NBP API for historical rates
        self._wait_for_rate_limit()
        
        try:
            url = f"{self.nbp_api_base}/{date}/?format=json"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                rate = data['rates'][0]['mid']
                self.cache[date] = rate
                return rate
            elif response.status_code == 404:
                # No data for this date (weekend/holiday)
                return self._get_previous_business_day_rate(date)
            else:
                logger.warning(f"Error fetching rate for {date}: HTTP {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {date}: {e}")
            return None
    
    def _get_previous_business_day_rate(self, date: str) -> Optional[float]:
        """Try to get rate from previous business days"""
        from datetime import datetime, timedelta
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        
        # Try up to 7 previous days
        for i in range(1, 8):
            prev_date = date_obj - timedelta(days=i)
            prev_date_str = prev_date.strftime("%Y-%m-%d")
            
            self._wait_for_rate_limit()
            
            try:
                url = f"{self.nbp_api_base}/{prev_date_str}/?format=json"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    rate = data['rates'][0]['mid']
                    self.cache[date] = rate  # Cache for original date
                    return rate
                    
            except requests.exceptions.RequestException:
                continue
        
        return None
    
    def clear_cache(self):
        """Clear exchange rate cache"""
        self.cache.clear()
        self.cache_timestamp = None

# Singleton instance
_exchange_rate_service: Optional[ExchangeRateService] = None

def get_exchange_rate_service() -> ExchangeRateService:
    """Get singleton instance of ExchangeRateService"""
    global _exchange_rate_service
    if _exchange_rate_service is None:
        _exchange_rate_service = ExchangeRateService()
    return _exchange_rate_service

