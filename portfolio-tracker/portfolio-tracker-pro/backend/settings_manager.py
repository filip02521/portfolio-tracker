"""
Settings management module for Portfolio Tracker Pro
Handles API keys storage, validation, and cache management
"""
import os
import json
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)
from config import Config
from exchanges.binance_client import BinanceClient
from exchanges.bybit_client import BybitClient
from exchanges.xtb_client import XTBClient

class SettingsManager:
    """Manages application settings including API keys"""
    
    SETTINGS_FILE = "app_settings.json"
    
    def __init__(self):
        """Initialize settings manager"""
        self.load_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file or environment"""
        if os.path.exists(self.SETTINGS_FILE):
            try:
                with open(self.SETTINGS_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading settings: {e}")
                return {}
        return {}
    
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """Save settings to file"""
        try:
            with open(self.SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return False
    
    def get_api_keys_status(self) -> Dict[str, Any]:
        """Get status of API keys (without showing actual keys)"""
        Config.init()
        
        return {
            "binance": {
                "configured": bool(Config.BINANCE_API_KEY and Config.BINANCE_SECRET_KEY),
                "api_key_masked": self._mask_key(Config.BINANCE_API_KEY) if Config.BINANCE_API_KEY else None
            },
            "bybit": {
                "configured": bool(Config.BYBIT_API_KEY and Config.BYBIT_SECRET_KEY),
                "api_key_masked": self._mask_key(Config.BYBIT_API_KEY) if Config.BYBIT_API_KEY else None
            },
            "xtb": {
                "configured": bool(Config.XTB_USER_ID and Config.XTB_PASSWORD),
                "username": Config.XTB_USER_ID if Config.XTB_USER_ID else None
            },
            "alpha_vantage": {
                "configured": bool(Config.ALPHA_VANTAGE_API_KEY),
                "api_key_masked": self._mask_key(Config.ALPHA_VANTAGE_API_KEY) if Config.ALPHA_VANTAGE_API_KEY else None
            },
            "polygon": {
                "configured": bool(getattr(Config, "POLYGON_API_KEY", "")),
                "api_key_masked": self._mask_key(getattr(Config, "POLYGON_API_KEY", "")) if getattr(Config, "POLYGON_API_KEY", "") else None
            }
        }
    
    def _mask_key(self, key: str) -> str:
        """Mask API key for display (show only first 4 and last 4 characters)"""
        if not key or len(key) < 8:
            return "****"
        return f"{key[:4]}...{key[-4:]}"
    
    def update_api_keys(self, exchange: str, api_key: Optional[str] = None, 
                       secret_key: Optional[str] = None,
                       username: Optional[str] = None,
                       password: Optional[str] = None) -> bool:
        """Update API keys in .env file"""
        env_file = ".env"
        env_lines = []
        
        # Read existing .env file
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                env_lines = f.readlines()
        
        # Update or add keys
        keys_to_update = {}
        if exchange.lower() == "binance":
            if api_key:
                keys_to_update["BINANCE_API_KEY"] = api_key
            if secret_key:
                keys_to_update["BINANCE_SECRET_KEY"] = secret_key
        elif exchange.lower() == "bybit":
            if api_key:
                keys_to_update["BYBIT_API_KEY"] = api_key
            if secret_key:
                keys_to_update["BYBIT_SECRET_KEY"] = secret_key
        elif exchange.lower() == "xtb":
            if username:
                keys_to_update["XTB_USER_ID"] = username
            if password:
                keys_to_update["XTB_PASSWORD"] = password
        elif exchange.lower() == "alpha_vantage":
            if api_key:
                keys_to_update["ALPHA_VANTAGE_API_KEY"] = api_key
        elif exchange.lower() == "polygon":
            if api_key:
                keys_to_update["POLYGON_API_KEY"] = api_key
        
        # Update existing lines or add new ones
        updated_keys = set()
        for key, value in keys_to_update.items():
            found = False
            for i, line in enumerate(env_lines):
                if line.strip().startswith(f"{key}="):
                    env_lines[i] = f"{key}={value}\n"
                    found = True
                    updated_keys.add(key)
                    break
            if not found:
                env_lines.append(f"{key}={value}\n")
                updated_keys.add(key)
        
        # Write back to .env file
        try:
            with open(env_file, 'w') as f:
                f.writelines(env_lines)
            
            # Update environment variables immediately
            for key, value in keys_to_update.items():
                os.environ[key] = value
            
            # Reload config
            Config.init()
            return True
        except Exception as e:
            logger.error(f"Error updating API keys: {e}")
            return False
    
    def test_connection(self, exchange: str) -> Dict[str, Any]:
        """Test connection to exchange API"""
        try:
            Config.init()
            
            if exchange.lower() == "binance":
                if not Config.BINANCE_API_KEY or not Config.BINANCE_SECRET_KEY:
                    return {
                        "success": False,
                        "error": "Binance API keys not configured"
                    }
                try:
                    client = BinanceClient()
                    # Try to get account info
                    account = client._make_request_with_retry(
                        lambda: client.client.get_account()
                    )
                    return {
                        "success": True,
                        "message": "Binance connection successful",
                        "account_info": {
                            "can_trade": account.get("canTrade", False),
                            "can_withdraw": account.get("canWithdraw", False),
                            "can_deposit": account.get("canDeposit", False)
                        }
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Binance connection failed: {str(e)}"
                    }
            
            elif exchange.lower() == "bybit":
                if not Config.BYBIT_API_KEY or not Config.BYBIT_SECRET_KEY:
                    return {
                        "success": False,
                        "error": "Bybit API keys not configured"
                    }
                try:
                    client = BybitClient()
                    # Try to get wallet balance
                    balance = client._make_request_with_retry(
                        lambda: client.session.get_wallet_balance(category="spot")
                    )
                    return {
                        "success": True,
                        "message": "Bybit connection successful",
                        "account_info": {
                            "wallet_balance": balance.get("result", {}).get("list", [])[0].get("totalEquity", "0") if balance.get("result", {}).get("list") else "N/A"
                        }
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Bybit connection failed: {str(e)}"
                    }
            
            elif exchange.lower() == "xtb":
                if not Config.XTB_USER_ID or not Config.XTB_PASSWORD:
                    return {
                        "success": False,
                        "error": "XTB credentials not configured"
                    }
                try:
                    client = XTBClient()
                    # Try to login
                    login_result = client.login()
                    if login_result:
                        return {
                            "success": True,
                            "message": "XTB connection successful"
                        }
                    else:
                        return {
                            "success": False,
                            "error": "XTB login failed"
                        }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"XTB connection failed: {str(e)}"
                    }
            
            elif exchange.lower() == "alpha_vantage":
                if not Config.ALPHA_VANTAGE_API_KEY:
                    return {
                        "success": False,
                        "error": "Alpha Vantage API key not configured"
                    }
                # Simple validation by calling a lightweight endpoint
                try:
                    import requests
                    resp = requests.get(
                        "https://www.alphavantage.co/query",
                        params={
                            "function": "GLOBAL_QUOTE",
                            "symbol": "AAPL",
                            "apikey": Config.ALPHA_VANTAGE_API_KEY
                        },
                        timeout=5
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("Global Quote"):
                            return {"success": True, "message": "Alpha Vantage connection successful"}
                    return {"success": False, "error": f"Alpha Vantage validation failed: {resp.text[:120]}"}
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Alpha Vantage connection failed: {str(e)}"
                    }
            
            elif exchange.lower() == "polygon":
                if not getattr(Config, "POLYGON_API_KEY", ""):
                    return {
                        "success": False,
                        "error": "Polygon API key not configured"
                    }
                try:
                    import requests
                    resp = requests.get(
                        f"https://api.polygon.io/v2/aggs/ticker/AAPL/prev",
                        params={"adjusted": "true", "apiKey": Config.POLYGON_API_KEY},
                        timeout=5
                    )
                    if resp.status_code == 200 and (resp.json() or {}).get("results"):
                        return {"success": True, "message": "Polygon connection successful"}
                    return {"success": False, "error": f"Polygon validation failed: {resp.text[:120]}"}
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Polygon connection failed: {str(e)}"
                    }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown exchange: {exchange}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Connection test failed: {str(e)}"
            }
    
    def get_app_settings(self) -> Dict[str, Any]:
        """Get application settings"""
        settings = self.load_settings()
        return {
            "cache_enabled": settings.get("cache_enabled", True),
            "auto_refresh_enabled": settings.get("auto_refresh_enabled", True),
            "refresh_interval": settings.get("refresh_interval", 30),
            "theme": settings.get("theme", "dark"),
            "currency": settings.get("currency", "USD")
        }
    
    def update_app_settings(self, settings: Dict[str, Any]) -> bool:
        """Update application settings"""
        current_settings = self.load_settings()
        current_settings.update(settings)
        return self.save_settings(current_settings)

