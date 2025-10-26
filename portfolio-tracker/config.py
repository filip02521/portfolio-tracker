"""
Configuration module for API credentials management
"""
import os
from dotenv import load_dotenv

# Try to load from Streamlit Secrets first (for cloud deployment)
try:
    import streamlit as st
    # Streamlit Cloud provides secrets through st.secrets
    secrets_available = True
except (ImportError, RuntimeError):
    # Not running in Streamlit Cloud or Streamlit not available
    secrets_available = False
    load_dotenv()  # Load from .env file for local development

class Config:
    """Configuration class for API credentials"""
    
    @classmethod
    def _get_env(cls, key):
        """Get environment variable from Streamlit Secrets or .env file"""
        if secrets_available:
            try:
                return st.secrets.get(key, '')
            except (AttributeError, Exception):
                # Fallback to os.getenv if secrets not configured
                return os.getenv(key, '')
        else:
            return os.getenv(key, '')
    
    # Binance
    BINANCE_API_KEY = ''
    BINANCE_SECRET_KEY = ''
    
    # Bybit
    BYBIT_API_KEY = ''
    BYBIT_SECRET_KEY = ''
    
    # XTB
    XTB_USER_ID = ''
    XTB_PASSWORD = ''
    
    @classmethod
    def init(cls):
        """Initialize configuration - load values when accessed"""
        cls.BINANCE_API_KEY = cls._get_env('BINANCE_API_KEY')
        cls.BINANCE_SECRET_KEY = cls._get_env('BINANCE_SECRET_KEY')
        cls.BYBIT_API_KEY = cls._get_env('BYBIT_API_KEY')
        cls.BYBIT_SECRET_KEY = cls._get_env('BYBIT_SECRET_KEY')
        cls.XTB_USER_ID = cls._get_env('XTB_USER_ID')
        cls.XTB_PASSWORD = cls._get_env('XTB_PASSWORD')
    
    @classmethod
    def validate(cls):
        """Validate that all required credentials are present"""
        cls.init()  # Make sure config is loaded
        missing = []
        
        if not cls.BINANCE_API_KEY or not cls.BINANCE_SECRET_KEY:
            missing.append('Binance')
        if not cls.BYBIT_API_KEY or not cls.BYBIT_SECRET_KEY:
            missing.append('Bybit')
        if not cls.XTB_USER_ID or not cls.XTB_PASSWORD:
            missing.append('XTB')
            
        return missing

