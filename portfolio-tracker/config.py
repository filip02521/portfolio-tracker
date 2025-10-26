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
        """Get environment variable from Streamlit Secrets or .env file"""
        # First try to get from Streamlit Secrets (for cloud deployment)
        try:
            import streamlit as st
            if hasattr(st, 'secrets'):
                try:
                    value = st.secrets.get(key, '')
                    if value:
                        return value
                except (AttributeError, Exception):
                    pass
        except (ImportError, RuntimeError):
            pass
        
        # Fallback to environment variables
        return os.getenv(key, '')
    
    # Binance
    BINANCE_API_KEY = ''
    BINANCE_SECRET_KEY = ''
    
    # Bybit
    BYBIT_API_KEY = ''
    BYBIT_SECRET_KEY = ''
    
    @classmethod
    def init(cls):
        """Initialize configuration - load values when accessed"""
        cls.BINANCE_API_KEY = cls._get_env('BINANCE_API_KEY')
        cls.BINANCE_SECRET_KEY = cls._get_env('BINANCE_SECRET_KEY')
        cls.BYBIT_API_KEY = cls._get_env('BYBIT_API_KEY')
        cls.BYBIT_SECRET_KEY = cls._get_env('BYBIT_SECRET_KEY')
    
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

