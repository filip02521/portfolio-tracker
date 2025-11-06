"""
Configuration module for API credentials management
"""
import os
from dotenv import load_dotenv

# Load .env file for local development
load_dotenv()

class Config:
    """Configuration class for API credentials"""
    
    @classmethod
    def _get_env(cls, key):
        """Get environment variable from .env file or environment variables"""
        # On Railway, we use environment variables directly
        # No need to check st.secrets which causes messages about secrets.toml
        value = os.getenv(key, '')
        return value
    
    # Binance
    BINANCE_API_KEY = ''
    BINANCE_SECRET_KEY = ''
    
    # Bybit
    BYBIT_API_KEY = ''
    BYBIT_SECRET_KEY = ''
    
    # XTB
    XTB_USER_ID = ''
    XTB_PASSWORD = ''
    
    # Coinbase
    COINBASE_API_KEY = ''
    COINBASE_SECRET_KEY = ''
    
    # Kraken
    KRAKEN_API_KEY = ''
    KRAKEN_SECRET_KEY = ''
    
    # Alpha Vantage
    ALPHA_VANTAGE_API_KEY = ''
    
    # Polygon.io
    POLYGON_API_KEY = ''
    
    # Finnhub
    FINNHUB_API_KEY = ''
    
    @classmethod
    def init(cls):
        """Initialize configuration - load values when accessed"""
        cls.BINANCE_API_KEY = cls._get_env('BINANCE_API_KEY')
        cls.BINANCE_SECRET_KEY = cls._get_env('BINANCE_SECRET_KEY')
        cls.BYBIT_API_KEY = cls._get_env('BYBIT_API_KEY')
        cls.BYBIT_SECRET_KEY = cls._get_env('BYBIT_SECRET_KEY')
        cls.XTB_USER_ID = cls._get_env('XTB_USER_ID')
        cls.XTB_PASSWORD = cls._get_env('XTB_PASSWORD')
        cls.COINBASE_API_KEY = cls._get_env('COINBASE_API_KEY')
        cls.COINBASE_SECRET_KEY = cls._get_env('COINBASE_SECRET_KEY')
        cls.KRAKEN_API_KEY = cls._get_env('KRAKEN_API_KEY')
        cls.KRAKEN_SECRET_KEY = cls._get_env('KRAKEN_SECRET_KEY')
        cls.ALPHA_VANTAGE_API_KEY = cls._get_env('ALPHA_VANTAGE_API_KEY')
        cls.POLYGON_API_KEY = cls._get_env('POLYGON_API_KEY')
        cls.FINNHUB_API_KEY = cls._get_env('FINNHUB_API_KEY')
    
    @classmethod
    def validate(cls):
        """Validate that all required credentials are present"""
        cls.init()  # Make sure config is loaded
        missing = []
        
        if not cls.BINANCE_API_KEY or not cls.BINANCE_SECRET_KEY:
            missing.append('Binance')
        if not cls.BYBIT_API_KEY or not cls.BYBIT_SECRET_KEY:
            missing.append('Bybit')
            
        return missing

