"""
NBP API integration for fetching USD/PLN exchange rates
"""
import requests
import json
from datetime import datetime, timedelta
from typing import Optional, Dict
import time

class NBPAPI:
    """NBP API client for exchange rates"""
    
    def __init__(self):
        self.base_url = "https://api.nbp.pl/api/exchangerates/rates/A/USD"
        self.cache = {}  # Simple cache to avoid repeated requests
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 500ms between requests to respect NBP limits
    
    def _wait_for_rate_limit(self):
        """Respect NBP rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()
    
    def get_usd_rate(self, date: str) -> Optional[float]:
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
        
        # Respect rate limits
        self._wait_for_rate_limit()
        
        try:
            url = f"{self.base_url}/{date}/?format=json"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                rate = data['rates'][0]['mid']
                self.cache[date] = rate
                return rate
            elif response.status_code == 404:
                # No data for this date (weekend/holiday)
                # Try previous business day
                return self._get_previous_business_day_rate(date)
            else:
                print(f"Error fetching rate for {date}: HTTP {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Request error for {date}: {e}")
            return None
    
    def _get_previous_business_day_rate(self, date: str) -> Optional[float]:
        """Try to get rate from previous business days"""
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        
        # Try up to 7 previous days
        for i in range(1, 8):
            prev_date = date_obj - timedelta(days=i)
            prev_date_str = prev_date.strftime("%Y-%m-%d")
            
            self._wait_for_rate_limit()
            
            try:
                url = f"{self.base_url}/{prev_date_str}/?format=json"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    rate = data['rates'][0]['mid']
                    self.cache[date] = rate  # Cache for original date
                    return rate
                    
            except requests.exceptions.RequestException:
                continue
        
        print(f"No rate found for {date} and previous 7 days")
        return None
    
    def get_multiple_rates(self, dates: list) -> Dict[str, float]:
        """
        Get rates for multiple dates
        
        Args:
            dates: List of dates in YYYY-MM-DD format
            
        Returns:
            Dictionary mapping dates to rates
        """
        results = {}
        
        for date in dates:
            rate = self.get_usd_rate(date)
            if rate:
                results[date] = rate
        
        return results
    
    def test_connection(self) -> bool:
        """Test if NBP API is accessible"""
        try:
            # Try to get today's rate
            today = datetime.now().strftime("%Y-%m-%d")
            rate = self.get_usd_rate(today)
            return rate is not None
        except Exception:
            return False

# Example usage
if __name__ == "__main__":
    nbp = NBPAPI()
    
    # Test connection
    if nbp.test_connection():
        print("✅ NBP API connection successful")
        
        # Test getting a rate
        test_date = "2024-01-15"
        rate = nbp.get_usd_rate(test_date)
        if rate:
            print(f"USD rate on {test_date}: {rate} PLN")
        else:
            print(f"Could not get rate for {test_date}")
    else:
        print("❌ NBP API connection failed")
