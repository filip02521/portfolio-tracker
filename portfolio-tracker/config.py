"""
Configuration module for API credentials management
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration class for API credentials"""
    
    # Binance
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
    BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY', '')
    
    # Bybit
    BYBIT_API_KEY = os.getenv('BYBIT_API_KEY', '')
    BYBIT_SECRET_KEY = os.getenv('BYBIT_SECRET_KEY', '')
    
    # XTB
    XTB_USER_ID = os.getenv('XTB_USER_ID', '')
    XTB_PASSWORD = os.getenv('XTB_PASSWORD', '')
    
    @classmethod
    def validate(cls):
        """Validate that all required credentials are present"""
        missing = []
        
        if not cls.BINANCE_API_KEY or not cls.BINANCE_SECRET_KEY:
            missing.append('Binance')
        if not cls.BYBIT_API_KEY or not cls.BYBIT_SECRET_KEY:
            missing.append('Bybit')
        if not cls.XTB_USER_ID or not cls.XTB_PASSWORD:
            missing.append('XTB')
            
        return missing

