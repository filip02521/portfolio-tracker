"""
Settings management module for Portfolio Tracker Pro
Handles per-user API credentials, validation, and app configuration
"""
import os
import json
import logging
from typing import Dict, Optional, Any, Tuple, List

logger = logging.getLogger(__name__)

from config import Config
from exchanges.binance_client import BinanceClient
from exchanges.bybit_client import BybitClient
from exchanges.xtb_client import XTBClient
from exchanges.coinbase_client import CoinbaseClient
from exchanges.kraken_client import KrakenClient


class SettingsManager:
    """Manages application settings including per-user API keys"""

    SETTINGS_FILE = "app_settings.json"
    USER_SETTINGS_FILE = "user_settings.json"

    # Supported exchanges and required credential fields
    EXCHANGE_FIELDS: Dict[str, Tuple[str, ...]] = {
        "binance": ("api_key", "secret_key"),
        "bybit": ("api_key", "secret_key"),
        "coinbase": ("api_key", "secret_key"),
        "kraken": ("api_key", "secret_key"),
        "xtb": ("username", "password"),
        "alpha_vantage": ("api_key",),
        "polygon": ("api_key",),
        "finnhub": ("api_key",),
    }

    def load_settings(self) -> Dict[str, Any]:
        """Load global application settings from file"""
        if os.path.exists(self.SETTINGS_FILE):
            try:
                with open(self.SETTINGS_FILE, "r") as f:
                    return json.load(f)
            except Exception as exc:
                logger.warning("Error loading settings: %s", exc)
                return {}
        return {}

    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """Save global application settings to file"""
        try:
            with open(self.SETTINGS_FILE, "w") as f:
                json.dump(settings, f, indent=2)
            return True
        except Exception as exc:
            logger.error("Error saving settings: %s", exc)
            return False

    # ------------------------------------------------------------------
    # User API credential handling
    # ------------------------------------------------------------------
    def _load_user_settings(self) -> Dict[str, Any]:
        """Load per-user settings from file"""
        if os.path.exists(self.USER_SETTINGS_FILE):
            try:
                with open(self.USER_SETTINGS_FILE, "r") as f:
                    return json.load(f)
            except Exception as exc:
                logger.warning("Error loading user settings: %s", exc)
                return {}
        return {}

    def _save_user_settings(self, data: Dict[str, Any]) -> bool:
        """Persist per-user settings to file"""
        try:
            with open(self.USER_SETTINGS_FILE, "w") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as exc:
            logger.error("Error saving user settings: %s", exc)
            return False

    def _mask_key(self, key: Optional[str]) -> Optional[str]:
        """Mask API key for display (show only first 4 and last 4 characters)"""
        if not key:
            return None
        if len(key) < 8:
            return "****"
        return f"{key[:4]}...{key[-4:]}"

    def _get_env_credentials(self) -> Dict[str, Dict[str, str]]:
        """Load credentials from environment for backward compatibility"""
        Config.init()
        env_credentials: Dict[str, Dict[str, str]] = {}

        if Config.BINANCE_API_KEY and Config.BINANCE_SECRET_KEY:
            env_credentials["binance"] = {
                "api_key": Config.BINANCE_API_KEY,
                "secret_key": Config.BINANCE_SECRET_KEY,
            }
        if Config.BYBIT_API_KEY and Config.BYBIT_SECRET_KEY:
            env_credentials["bybit"] = {
                "api_key": Config.BYBIT_API_KEY,
                "secret_key": Config.BYBIT_SECRET_KEY,
            }
        if Config.COINBASE_API_KEY and Config.COINBASE_SECRET_KEY:
            env_credentials["coinbase"] = {
                "api_key": Config.COINBASE_API_KEY,
                "secret_key": Config.COINBASE_SECRET_KEY,
            }
        if Config.KRAKEN_API_KEY and Config.KRAKEN_SECRET_KEY:
            env_credentials["kraken"] = {
                "api_key": Config.KRAKEN_API_KEY,
                "secret_key": Config.KRAKEN_SECRET_KEY,
            }
        if Config.XTB_USER_ID and Config.XTB_PASSWORD:
            env_credentials["xtb"] = {
                "username": Config.XTB_USER_ID,
                "password": Config.XTB_PASSWORD,
            }
        if Config.ALPHA_VANTAGE_API_KEY:
            env_credentials["alpha_vantage"] = {
                "api_key": Config.ALPHA_VANTAGE_API_KEY,
            }
        if getattr(Config, "POLYGON_API_KEY", ""):
            env_credentials["polygon"] = {
                "api_key": Config.POLYGON_API_KEY,
            }
        if getattr(Config, "FINNHUB_API_KEY", ""):
            env_credentials["finnhub"] = {
                "api_key": Config.FINNHUB_API_KEY,
            }

        return env_credentials

    def get_user_api_credentials(self, username: str) -> Dict[str, Dict[str, str]]:
        """Return raw API credential dictionary for a user"""
        data = self._load_user_settings()
        user_settings = data.get(username, {})
        credentials = user_settings.get("api_keys", {}).copy()

        # Merge with environment credentials if user-specific credentials missing
        env_credentials = self._get_env_credentials()
        for exchange, env_values in env_credentials.items():
            if exchange not in credentials or not all(credentials[exchange].get(field) for field in env_values):
                credentials.setdefault(exchange, {}).update(env_values)

        return credentials

    def get_api_keys_status(self, username: str) -> Dict[str, Any]:
        """Get masked status of API keys for a specific user"""
        credentials = self.get_user_api_credentials(username)

        status: Dict[str, Any] = {}
        for exchange, fields in self.EXCHANGE_FIELDS.items():
            stored = credentials.get(exchange, {})
            configured = all(stored.get(field) for field in fields)

            entry: Dict[str, Any] = {"configured": configured}
            if "api_key" in fields:
                entry["api_key_masked"] = self._mask_key(stored.get("api_key"))
            if "username" in fields:
                entry["username"] = stored.get("username")

            status[exchange] = entry

        return status

    def update_api_keys(
        self,
        username: str,
        exchange: str,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        username_field: Optional[str] = None,
        password: Optional[str] = None,
    ) -> bool:
        """Update stored API keys for a user"""
        normalized_exchange = exchange.lower()
        if normalized_exchange not in self.EXCHANGE_FIELDS:
            raise ValueError(f"Unsupported exchange '{exchange}'")

        field_values = {
            "api_key": api_key,
            "secret_key": secret_key,
            "username": username_field,
            "password": password,
        }

        required_fields = self.EXCHANGE_FIELDS[normalized_exchange]

        data = self._load_user_settings()
        user_settings = data.setdefault(username, {})
        api_keys = user_settings.setdefault("api_keys", {})
        exchange_entry = api_keys.setdefault(normalized_exchange, {})

        for field in required_fields:
            value = field_values.get(field)
            if value is not None:
                if value == "":
                    exchange_entry.pop(field, None)
                else:
                    exchange_entry[field] = value.strip()

        # Remove exchange entry if empty
        if not exchange_entry:
            api_keys.pop(normalized_exchange, None)

        # Clean up user if no settings remain
        if not api_keys and "app_settings" not in user_settings:
            data.pop(username, None)

        return self._save_user_settings(data)

    def test_connection(self, username: str, exchange: str) -> Dict[str, Any]:
        """Test connection to exchange API using stored credentials"""
        normalized_exchange = exchange.lower()
        credentials = self.get_user_api_credentials(username).get(normalized_exchange, {})

        try:
            if normalized_exchange == "binance":
                client = BinanceClient(
                    api_key=credentials.get("api_key"),
                    secret_key=credentials.get("secret_key"),
                )
                account = client.get_account_info()
                return {
                    "success": True,
                    "message": "Binance connection successful",
                    "account_info": account or {},
                }

            if normalized_exchange == "bybit":
                client = BybitClient(
                    api_key=credentials.get("api_key"),
                    secret_key=credentials.get("secret_key"),
                )
                balance = client.get_wallet_balance()
                return {
                    "success": True,
                    "message": "Bybit connection successful",
                    "account_info": balance or {},
                }

            if normalized_exchange == "xtb":
                client = XTBClient(
                    user_id=credentials.get("username"),
                    password=credentials.get("password"),
                )
                if client.login():
                    return {"success": True, "message": "XTB connection successful"}
                return {"success": False, "error": "XTB login failed"}

            if normalized_exchange == "coinbase":
                client = CoinbaseClient(
                    api_key=credentials.get("api_key"),
                    api_secret=credentials.get("secret_key"),
                )
                portfolio = client.get_portfolio()
                return {
                    "success": True,
                    "message": "Coinbase connection successful",
                    "account_info": {"asset_count": len(portfolio or [])},
                }

            if normalized_exchange == "kraken":
                client = KrakenClient(
                    api_key=credentials.get("api_key"),
                    api_secret=credentials.get("secret_key"),
                )
                balance = client.get_account_balance()
                return {
                    "success": True,
                    "message": "Kraken connection successful",
                    "account_info": balance or {},
                }

            if normalized_exchange in {"alpha_vantage", "polygon", "finnhub"}:
                api_key_value = credentials.get("api_key")
                if not api_key_value:
                    return {
                        "success": False,
                        "error": f"{exchange} API key not configured",
                    }

                import requests

                if normalized_exchange == "alpha_vantage":
                    response = requests.get(
                        "https://www.alphavantage.co/query",
                        params={
                            "function": "GLOBAL_QUOTE",
                            "symbol": "AAPL",
                            "apikey": api_key_value,
                        },
                        timeout=5,
                    )
                    if response.status_code == 200 and response.json().get("Global Quote"):
                        return {"success": True, "message": "Alpha Vantage connection successful"}
                    return {
                        "success": False,
                        "error": f"Alpha Vantage validation failed: {response.text[:120]}",
                    }

                if normalized_exchange == "polygon":
                    response = requests.get(
                        "https://api.polygon.io/v2/aggs/ticker/AAPL/prev",
                        params={"adjusted": "true", "apiKey": api_key_value},
                        timeout=5,
                    )
                    if response.status_code == 200 and response.json().get("results"):
                        return {"success": True, "message": "Polygon connection successful"}
                    return {
                        "success": False,
                        "error": f"Polygon validation failed: {response.text[:120]}",
                    }

                if normalized_exchange == "finnhub":
                    response = requests.get(
                        "https://finnhub.io/api/v1/quote",
                        params={"symbol": "AAPL", "token": api_key_value},
                        timeout=5,
                    )
                    if response.status_code == 200 and "c" in response.json():
                        return {"success": True, "message": "Finnhub connection successful"}
                    return {
                        "success": False,
                        "error": f"Finnhub validation failed: {response.text[:120]}",
                    }

            return {"success": False, "error": f"Unknown exchange: {exchange}"}

        except Exception as exc:
            return {"success": False, "error": f"Connection test failed: {exc}"}

    # ------------------------------------------------------------------
    # General app settings (shared)
    # ------------------------------------------------------------------
    def get_app_settings(self) -> Dict[str, Any]:
        """Get application-wide (non-user) settings"""
        settings = self.load_settings()
        return {
            "cache_enabled": settings.get("cache_enabled", True),
            "auto_refresh_enabled": settings.get("auto_refresh_enabled", True),
            "refresh_interval": settings.get("refresh_interval", 30),
            "theme": settings.get("theme", "dark"),
            "currency": settings.get("currency", "USD"),
        }

    def update_app_settings(self, settings: Dict[str, Any]) -> bool:
        """Update application-wide settings"""
        current_settings = self.load_settings()
        current_settings.update(settings)
        return self.save_settings(current_settings)

    def list_users(self) -> List[str]:
        """List users that have stored settings"""
        return list(self._load_user_settings().keys())

