from fastapi import FastAPI, HTTPException, Depends, status, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse, JSONResponse, PlainTextResponse

# Import backup router
try:
    from routes.backup import router as backup_router
except ImportError:
    backup_router = None
from typing import List, Optional, Dict, Any, Tuple, Set
import uvicorn
import os
import csv
import io
from dotenv import load_dotenv
from portfolio_tracker import PortfolioTracker
from transaction_history import TransactionHistory
from portfolio_history import PortfolioHistory
from pdf_report_generator import PDFReportGenerator
from settings_manager import SettingsManager
from auth import AuthManager
from exchange_rate_service import get_exchange_rate_service
from transaction_validator import TransactionValidator
from smart_insights_service import SmartInsightsService
from goal_tracking_service import GoalTrackingService
from tax_optimization_service import TaxOptimizationService
from risk_analytics_service import RiskAnalyticsService
from price_alert_service import PriceAlertService
from market_data_service import MarketDataService
from risk_management_service import RiskManagementService
from logging_config import setup_logging, get_logger
from watchlist_service import WatchlistService
from ai_service import AIService
from backtesting_service import BacktestEngine
from confluence_strategy_service import ConfluenceStrategyService
from due_diligence_service import DueDiligenceService
from fundamental_screening_service import FundamentalScreeningService
from benchmark_service import BenchmarkService
from exchange_manager import ExchangeManager
from exchange_sync import detect_new_trades, import_new_trades
from advanced_analytics_service import AdvancedAnalyticsService
from datetime import datetime
from pydantic import BaseModel
from security_middleware import (
    SecurityHeadersMiddleware,
    limiter,
    get_allowed_origins,
    get_allowed_methods,
    get_allowed_headers
)
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from requests.exceptions import Timeout, ConnectionError, RequestException
from collections import defaultdict
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
import asyncio
import time

# Load environment variables
load_dotenv()

# Setup structured logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logger = setup_logging(log_level)
app_logger = get_logger(__name__)

# Initialize FastAPI app with lifespan context for background worker
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - initialize background worker after all services are created
    global background_worker
    
    # Log ML library availability
    try:
        import ai_service
        app_logger.info(f"ML Libraries Status - Prophet: {ai_service.PROPHET_AVAILABLE}, TA: {ai_service.TA_AVAILABLE}, Transformers: {ai_service.TRANSFORMERS_AVAILABLE}")
    except Exception as e:
        app_logger.warning(f"Could not check ML library status: {e}")
    
    try:
        from background_worker import initialize_worker, BackupScheduler
        from backup_service import BackupService
        
        # Initialize price alert worker
        background_worker = initialize_worker(
            price_alert_service,
            market_data_service,
            check_interval=60  # Check every 60 seconds
        )
        app_logger.info("Background worker initialized and started")
        
        # Initialize backup scheduler
        try:
            backup_service = BackupService()
            backup_scheduler = BackupScheduler(backup_service, backup_time="02:00")
            backup_scheduler.start()
            app_logger.info("Backup scheduler initialized and started")
        except Exception as backup_err:
            app_logger.warning(f"Backup scheduler initialization failed (non-critical): {backup_err}")
    except Exception as e:
        app_logger.error(f"Error initializing background worker: {e}")
    
    yield
    
    # Shutdown
    try:
        from background_worker import stop_worker
        stop_worker()
        app_logger.info("Background worker stopped")
    except Exception as e:
        app_logger.error(f"Error stopping background worker: {e}")

app = FastAPI(
    title="Portfolio Tracker Pro API",
    description="Professional portfolio tracking and analytics API with AI-powered insights, multi-exchange aggregation, and advanced backtesting capabilities.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
    tags_metadata=[
        {
            "name": "Authentication",
            "description": "User authentication and authorization endpoints"
        },
        {
            "name": "Portfolio",
            "description": "Portfolio summary, assets, and multi-exchange aggregation"
        },
        {
            "name": "Transactions",
            "description": "Transaction history and management"
        },
        {
            "name": "Analytics",
            "description": "Performance analytics, charts, and historical data"
        },
        {
            "name": "AI/ML",
            "description": "AI-powered price predictions, recommendations, and sentiment analysis"
        },
        {
            "name": "Backtesting",
            "description": "Investment strategy backtesting and performance simulation"
        },
        {
            "name": "Risk Management",
            "description": "Risk analytics, alerts, and portfolio health monitoring"
        },
        {
            "name": "Settings",
            "description": "User preferences, API keys, and app configuration"
        },
        {
            "name": "Market Data",
            "description": "Real-time prices, watchlists, and market information"
        }
    ]
)

# Add rate limiter
app.state.limiter = limiter

# Include backup router
if backup_router:
    app.include_router(backup_router)

# Rate limit exception handler
# Prometheus metrics (avoid duplicate registration under uvicorn reload by not registering in default REGISTRY)
market_provider_requests = Counter(
    'market_provider_requests_total',
    'Total number of market data provider requests',
    ['provider', 'status'],
    registry=None
)
market_cache_hits = Counter(
    'market_cache_hits_total',
    'Number of cache hits for market data',
    registry=None
)
market_watchlist_requests = Counter(
    'market_watchlist_requests_total',
    'Number of watchlist requests',
    registry=None
)

# UI interaction metrics
ui_interactions = Counter(
    'ui_interactions_total',
    'UI interaction events',
    ['event'],
    registry=None
)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "detail": f"Rate limit exceeded: {exc.detail}. Please try again later."
        },
        headers={"Retry-After": str(exc.retry_after) if hasattr(exc, 'retry_after') else "60"}
    )

# Security headers middleware (must be first)
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware for React frontend (secure configuration)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=get_allowed_methods(),
    allow_headers=get_allowed_headers(),
    expose_headers=["Content-Disposition"],  # For file downloads
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Security
security = HTTPBearer()

# Dependency to get current user from JWT token
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return current user"""
    token = credentials.credentials
    username = auth_manager.verify_token(token)
    
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = auth_manager.get_user(username)
    if user is None or not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


# Initialize portfolio tracker, transaction history, portfolio history, PDF generator, settings manager, and auth manager
settings_manager = SettingsManager()
market_data_service = MarketDataService()  # Initialize market data service (must be before portfolio_tracker)
portfolio_tracker = PortfolioTracker(settings_manager, market_data_service=market_data_service)
transaction_history = TransactionHistory()
portfolio_history = PortfolioHistory()
pdf_generator = PDFReportGenerator()
auth_manager = AuthManager()
exchange_rate_service = get_exchange_rate_service()  # Initialize exchange rate service
smart_insights_service = SmartInsightsService(
    market_data_service=market_data_service,
    portfolio_history=portfolio_history
)  # Initialize smart insights service with dependencies
goal_tracking_service = GoalTrackingService()  # Initialize goal tracking service
tax_optimization_service = TaxOptimizationService()  # Initialize tax optimization service
risk_analytics_service = RiskAnalyticsService()  # Initialize risk analytics service
price_alert_service = PriceAlertService()  # Initialize price alert service
risk_management_service = RiskManagementService()  # Initialize risk management service
watchlist_service = WatchlistService()  # Initialize user watchlist service
due_diligence_service = DueDiligenceService(market_data_service=market_data_service)  # Initialize Due Diligence 360° service
ai_service = AIService(market_data_service=market_data_service, due_diligence_service=due_diligence_service)  # Initialize AI service
backtest_engine = BacktestEngine(market_data_service=market_data_service)  # Initialize backtesting engine
confluence_strategy_service = ConfluenceStrategyService(market_data_service=market_data_service)  # Initialize confluence strategy service
fundamental_screening_service = FundamentalScreeningService(market_data_service=market_data_service)  # Initialize fundamental screening service
benchmark_service = BenchmarkService(market_data_service=market_data_service)
advanced_analytics_service = AdvancedAnalyticsService(
    market_data_service=market_data_service,
    portfolio_tracker=portfolio_tracker,
    portfolio_history=portfolio_history
)

# Initialize background worker for price alerts (will be started in lifespan startup)
background_worker = None

# Pydantic models
class PortfolioSummary(BaseModel):
    total_value_usd: float
    total_value_pln: float
    total_pnl: float
    total_pnl_percent: float
    active_exchanges: int
    total_assets: int
    last_updated: str
    warnings: Optional[List[str]] = None


class SyncRequest(BaseModel):
    limit: Optional[int] = 50

class AssetSource(BaseModel):
    exchange: str
    amount: float
    value_usd: float
    value_pln: float
    average_price: float
    current_price: float
    pnl: float
    pnl_percent: float
    realized_pnl: float
    price_source: Optional[str] = None
    issues: Optional[List[str]] = None
    cost_basis_usd: Optional[float] = None


class Asset(BaseModel):
    symbol: str
    amount: float
    value_usd: float
    value_pln: float
    pnl: float
    pnl_percent: float
    exchange: str
    average_price: float = 0.0
    current_price: float = 0.0
    realized_pnl: float = 0.0
    exchange_price: Optional[float] = None
    exchange_value_usd: Optional[float] = None
    price_source: Optional[str] = None
    issues: Optional[List[str]] = None
    asset_type: Optional[str] = None
    sources: Optional[List[AssetSource]] = None
    source_count: Optional[int] = None
    cost_basis_usd: Optional[float] = None
    exchanges: Optional[List[str]] = None


# Validation constants shared across portfolio endpoints
NEGATIVE_HOLDING_TOLERANCE = 1e-8
PRICE_WARNING_THRESHOLD = 0.15
STABLECOINS = {'USDT', 'USDC', 'BUSD', 'DAI', 'TUSD', 'USDP', 'FDUSD', 'EUR', 'USD'}
CRYPTO_EXCHANGES = {'binance', 'bybit', 'coinbase', 'kraken'}
STOCK_EXCHANGES = {'xtb', 'nyse', 'nasdaq', 'lse', 'amex'}


def _build_assets_with_validation(
    portfolios: List[Dict],
    usd_to_pln_rate: float,
    user_id: Optional[str] = None
) -> Tuple[List[Asset], List[str]]:
    """Construct asset objects from raw portfolio balances and collect validation warnings."""
    assets: List[Asset] = []
    assets_index: Dict[Tuple[str, str], Asset] = {}
    warnings: Set[str] = set()

    price_reference_cache: Dict[str, Optional[float]] = {}

    stock_suffixes = ('.PL', '.US', '.DE', '.L', '.F', '.PA', '.MI', '.VX', '.HK')

    def infer_asset_type(exchange_name: str, symbol: str) -> str:
        exchange_lower = (exchange_name or '').lower()
        if exchange_lower in CRYPTO_EXCHANGES:
            return 'crypto'
        if exchange_lower in STOCK_EXCHANGES:
            return 'stock'

        symbol_upper = (symbol or '').upper()
        if symbol_upper in STABLECOINS:
            return 'crypto'
        if any(symbol_upper.endswith(suffix) for suffix in stock_suffixes):
            return 'stock'
        return 'other'

    def fetch_reference_price(symbol: str, exchange_name: str) -> Optional[float]:
        symbol_upper = (symbol or '').upper()
        if not symbol_upper:
            return None
        if symbol_upper in STABLECOINS:
            return 1.0

        exchange_lower = (exchange_name or '').lower()
        if exchange_lower in CRYPTO_EXCHANGES:
            asset_type_hint = 'crypto'
        elif exchange_lower in STOCK_EXCHANGES:
            asset_type_hint = 'stock'
        else:
            asset_type_hint = 'auto'

        cache_key = f"{asset_type_hint}:{symbol_upper}"
        if cache_key in price_reference_cache:
            return price_reference_cache[cache_key]

        price_data = market_data_service.get_price(symbol_upper, asset_type=asset_type_hint, priority='high')
        reference_price = price_data.get('price') if price_data else None

        if reference_price is None and asset_type_hint != 'auto':
            auto_key = f"auto:{symbol_upper}"
            if auto_key in price_reference_cache:
                reference_price = price_reference_cache[auto_key]
            else:
                auto_data = market_data_service.get_price(symbol_upper, asset_type='auto', priority='high')
                reference_price = auto_data.get('price') if auto_data else None
                price_reference_cache[auto_key] = reference_price

        price_reference_cache[cache_key] = reference_price
        return reference_price

    def get_history_cost_fallback(exchange_name: str, symbol: str) -> Optional[float]:
        try:
            transactions = transaction_history.get_transactions_for_asset(exchange_name, symbol.upper(), user_id=user_id)
        except Exception:
            return None
        if not transactions:
            return None

        buy_transactions = [tx for tx in transactions if (tx.get('type') or '').lower() == 'buy']
        if buy_transactions:
            total_invested = 0.0
            total_amount = 0.0
            for tx in buy_transactions:
                amount = float(tx.get('amount', 0) or 0)
                if amount <= 0:
                    continue
                value_usd = tx.get('value_usd')
                price = tx.get('price_usd') or tx.get('price')
                if value_usd is None and price is not None:
                    value_usd = price * amount
                if value_usd is None:
                    continue
                total_invested += float(value_usd)
                total_amount += amount
            if total_amount > 0 and total_invested > 0:
                return total_invested / total_amount

        # fallback to last known trade price
        last = max(transactions, key=lambda tx: tx.get('date', '')) if transactions else None
        if last:
            price_candidate = last.get('price_usd') or last.get('price')
            if price_candidate and price_candidate > 0:
                return float(price_candidate)
        return None

    for portfolio in portfolios:
        exchange = portfolio.get('exchange', '')
        for balance in portfolio.get('balances', []):
            asset_symbol = balance.get('asset', '')
            if not asset_symbol:
                continue

            current_amount = float(balance.get('total', 0.0) or 0.0)
            exchange_value_usd = float(balance.get('value_usdt', 0.0) or 0.0)

            if current_amount <= 0 and exchange_value_usd <= 0:
                continue

            issues: List[str] = []
            exchange_lower = (exchange or '').lower()
            xtb_exchange = exchange_lower == 'xtb'

            if current_amount < -NEGATIVE_HOLDING_TOLERANCE:
                issues.append(f"Negative quantity reported ({current_amount:.8f})")
                warnings.add(f"{exchange} {asset_symbol}: negative holding reported by exchange feed.")
            elif abs(current_amount) < NEGATIVE_HOLDING_TOLERANCE:
                current_amount = 0.0

            exchange_price = 0.0
            if current_amount > 0:
                try:
                    exchange_price = exchange_value_usd / current_amount if exchange_value_usd > 0 else 0.0
                except ZeroDivisionError:
                    exchange_price = 0.0

            reference_price = fetch_reference_price(asset_symbol, exchange) if current_amount > 0 else None

            final_price = exchange_price if exchange_price > 0 else 0.0
            price_source = 'exchange'

            if current_amount > 0:
                if reference_price and reference_price > 0:
                    if exchange_price <= 0:
                        final_price = reference_price
                        price_source = 'reference'
                        if xtb_exchange:
                            issues.append("Price reconstructed from reference feed (XTB does not expose live API quotes).")
                        else:
                            warnings.add(f"{exchange} {asset_symbol}: missing exchange price, using reference feed.")
                    else:
                        deviation = abs(reference_price - exchange_price) / max(reference_price, exchange_price)
                        if xtb_exchange:
                            final_price = reference_price
                            price_source = 'reference'
                            if deviation > PRICE_WARNING_THRESHOLD:
                                issues.append(
                                    f"Exchange price deviated {deviation*100:.1f}% from reference; normalized to external feed."
                                )
                        elif deviation > PRICE_WARNING_THRESHOLD:
                            final_price = reference_price
                            price_source = 'reference'
                            warnings.add(
                                f"{exchange} {asset_symbol}: exchange price deviated {deviation*100:.1f}% from reference; "
                                "normalized."
                            )
                elif exchange_price <= 0 and exchange_value_usd > 0:
                    final_price = exchange_value_usd / current_amount
                    price_source = 'exchange'
                elif reference_price == 0:
                    final_price = 0.0
                    price_source = 'reference'
                    issues.append("Instrument inactive or delisted in external feeds; price set to 0.")

            if final_price <= 0 and reference_price and reference_price > 0:
                final_price = reference_price
                price_source = 'reference'
                if xtb_exchange:
                    issues.append("Fallback to reference price due to zero valuation in exchange feed.")
                else:
                    warnings.add(f"{exchange} {asset_symbol}: fallback to reference price due to zero valuation.")

            if current_amount > 0 and (final_price is None or final_price <= 0):
                history_price = get_history_cost_fallback(exchange, asset_symbol)
                if history_price and history_price > 0:
                    final_price = history_price
                    price_source = 'history'
                    issues.append("Price estimated from historical transaction cost basis.")

            effective_price = final_price if final_price > 0 else reference_price or exchange_price
            current_value_usd = (
                current_amount * final_price if current_amount > 0 and final_price > 0 else exchange_value_usd
            )

            if current_amount > 0 and effective_price is not None and effective_price <= 0:
                if reference_price == 0:
                    issues.append("Price unavailable across providers; treated as 0 to keep position visible.")
                else:
                    issues.append("Missing price data after normalization.")

            try:
                # Get user_id from context if available (will be passed from calling endpoint)
                pnl_data = transaction_history.calculate_pnl(
                    exchange,
                    asset_symbol,
                    effective_price or 0.0,
                    current_amount,
                    user_id=user_id
                )

                if pnl_data:
                    invested = pnl_data.get('invested', 0)
                    current_position = pnl_data.get('current_amount', current_amount)
                    average_price = (
                        invested / current_position if current_position > 0 else effective_price or 0.0
                    )
                    asset_pnl = pnl_data.get('unrealized_pnl', 0)
                    asset_pnl_percent = pnl_data.get('pnl_percent', 0)
                    realized_pnl = pnl_data.get('realized_pnl', 0)
                else:
                    asset_pnl = 0
                    asset_pnl_percent = 0
                    invested = 0
                    average_price = effective_price or 0.0
                    realized_pnl = 0
            except Exception as exc:
                logger.error(f"Error calculating PNL for {asset_symbol}: {exc}")
                asset_pnl = 0
                asset_pnl_percent = 0
                invested = 0
                average_price = effective_price or 0.0
                realized_pnl = 0
                warnings.add(f"{exchange} {asset_symbol}: PNL calculation failed ({exc}).")

            asset_entry = Asset(
                symbol=asset_symbol,
                amount=current_amount,
                value_usd=current_value_usd,
                value_pln=current_value_usd * usd_to_pln_rate,
                pnl=asset_pnl,
                pnl_percent=asset_pnl_percent,
                exchange=exchange,
                average_price=average_price,
                current_price=effective_price or 0.0,
                realized_pnl=realized_pnl,
                exchange_price=exchange_price if exchange_price > 0 else None,
                exchange_value_usd=exchange_value_usd if exchange_value_usd > 0 else None,
                price_source=price_source,
                issues=issues or None,
            )
            assets.append(asset_entry)
            assets_index[(exchange.lower(), asset_symbol.upper())] = asset_entry

    try:
        transactions_by_asset: Dict[Tuple[str, str], Dict[str, List[Dict]]] = defaultdict(lambda: {'buy': [], 'sell': []})
        for tx in transaction_history.get_all_transactions(user_id=user_id):
            asset = (tx.get('asset') or '').upper()
            exchange = (tx.get('exchange') or '')
            tx_type = (tx.get('type') or '').lower()
            if not asset or not exchange or tx_type not in ('buy', 'sell'):
                continue
            transactions_by_asset[(exchange, asset)][tx_type].append(tx)

        price_cache: Dict[str, Optional[Dict[str, Any]]] = {}

        for (exchange, asset), grouped in transactions_by_asset.items():
            exchange_lower = (exchange or '').lower()
            buys = grouped['buy']
            sells = grouped['sell']
            if not buys:
                continue

            buy_amount = sum(tx.get('amount', 0) for tx in buys)
            sell_amount = sum(tx.get('amount', 0) for tx in sells)
            net_amount = buy_amount - sell_amount

            if net_amount <= 0:
                continue

            existing = assets_index.get((exchange.lower(), asset))
            if existing and existing.amount > 0:
                continue

            invested_total = sum(
                tx.get('value_usd')
                if tx.get('value_usd') is not None
                else tx.get('price', 0) * tx.get('amount', 0)
                for tx in buys
            )
            buy_amount = sum(tx.get('amount', 0) for tx in buys)
            average_cost_price = (invested_total / buy_amount) if buy_amount else None

            if asset not in price_cache:
                price_data = None
                if exchange_lower != 'xtb':
                    price_data = market_data_service.get_price(asset, asset_type='stock', priority='high')
                    if not price_data:
                        price_data = market_data_service.get_price(asset, asset_type='auto', priority='high')
                price_cache[asset] = price_data
            else:
                price_data = price_cache[asset]

            history_fallback_used = False
            if not price_data:
                if average_cost_price and average_cost_price > 0:
                    price_data = {'price': average_cost_price}
                    history_fallback_used = True
                else:
                    warnings.add(f"{exchange} {asset}: unable to fetch price for transaction-history asset.")
                    continue

            current_price = price_data.get('price')
            if not current_price or current_price <= 0:
                if average_cost_price and average_cost_price > 0:
                    current_price = average_cost_price
                    history_fallback_used = True
                else:
                    warnings.add(f"{exchange} {asset}: received non-positive reference price.")
                    continue

            current_value = net_amount * current_price
            if current_value < 1:
                continue

            pnl_data = transaction_history.calculate_pnl(exchange, asset, current_price, net_amount, user_id=user_id)
            asset_pnl = pnl_data.get('unrealized_pnl', 0) if pnl_data else 0
            asset_pnl_percent = pnl_data.get('pnl_percent', 0) if pnl_data else 0
            invested = pnl_data.get('invested', 0) if pnl_data else 0
            realized_pnl = pnl_data.get('realized_pnl', 0) if pnl_data else 0
            average_price = (invested / net_amount) if net_amount > 0 and invested else current_price

            asset_issues = ['Asset reconstructed from transaction history; exchange did not report holdings.']
            if history_fallback_used:
                asset_issues.append('Price estimated from historical transaction cost basis.')

            asset_entry = Asset(
                symbol=asset,
                amount=net_amount,
                value_usd=current_value,
                value_pln=current_value * usd_to_pln_rate,
                pnl=asset_pnl,
                pnl_percent=asset_pnl_percent,
                exchange=exchange,
                average_price=average_price,
                current_price=current_price,
                realized_pnl=realized_pnl,
                exchange_price=None,
                exchange_value_usd=None,
                price_source='history' if history_fallback_used else 'reference',
                issues=asset_issues,
            )
            assets.append(asset_entry)
            assets_index[(exchange.lower(), asset)] = asset_entry
            if exchange_lower != 'xtb':
                warnings.add(f"{exchange} {asset}: reconstructed from transactions (not reported by exchange).")
    except Exception as exc:
        logger.error(f"Error augmenting assets from transaction history: {exc}")
        warnings.add(f"Transaction history augmentation failed: {exc}")

    def compute_cost_basis_usd(asset_entry: Asset) -> float:
        amount = asset_entry.amount or 0.0
        if amount <= 0:
            return 0.0
        average_price = asset_entry.average_price or 0.0
        if average_price > 0:
            return average_price * amount
        value_usd = asset_entry.value_usd or 0.0
        pnl_value = asset_entry.pnl or 0.0
        candidate = value_usd - pnl_value
        return candidate if candidate > 0 else 0.0

    aggregated_map: Dict[Tuple[str, str], Dict[str, Any]] = {}

    for asset_entry in assets:
        symbol = asset_entry.symbol or ''
        asset_type = infer_asset_type(asset_entry.exchange, symbol)
        key = (asset_type, symbol.upper())

        exchange_name = asset_entry.exchange or 'Unknown'
        source_cost_basis = compute_cost_basis_usd(asset_entry)

        entry = aggregated_map.setdefault(
            key,
            {
                'symbol': symbol,
                'asset_type': asset_type,
                'amount': 0.0,
                'value_usd': 0.0,
                'value_pln': 0.0,
                'pnl': 0.0,
                'realized_pnl': 0.0,
                'cost_basis_usd': 0.0,
                'issues': set(),
                'sources': [],
                'price_sources': set(),
                'exchange_order': [],
                'exchange_seen': set(),
            },
        )

        entry['amount'] += asset_entry.amount or 0.0
        entry['value_usd'] += asset_entry.value_usd or 0.0
        entry['value_pln'] += asset_entry.value_pln or 0.0
        entry['pnl'] += asset_entry.pnl or 0.0
        entry['realized_pnl'] += asset_entry.realized_pnl or 0.0
        entry['cost_basis_usd'] += source_cost_basis

        issues = asset_entry.issues or []
        if issues:
            entry['issues'].update(issues)

        if asset_entry.price_source:
            entry['price_sources'].add(asset_entry.price_source)

        exchange_upper = exchange_name.upper()
        if exchange_upper not in entry['exchange_seen']:
            entry['exchange_seen'].add(exchange_upper)
            entry['exchange_order'].append(exchange_name or 'Unknown')

        entry['sources'].append(
            {
                'exchange': exchange_name,
                'amount': asset_entry.amount or 0.0,
                'value_usd': asset_entry.value_usd or 0.0,
                'value_pln': asset_entry.value_pln or 0.0,
                'average_price': asset_entry.average_price or 0.0,
                'current_price': asset_entry.current_price or 0.0,
                'pnl': asset_entry.pnl or 0.0,
                'pnl_percent': asset_entry.pnl_percent or 0.0,
                'realized_pnl': asset_entry.realized_pnl or 0.0,
                'price_source': asset_entry.price_source,
                'issues': list(issues),
                'cost_basis_usd': source_cost_basis,
            }
        )

    aggregated_assets: List[Asset] = []

    for (asset_type, symbol), entry in aggregated_map.items():
        total_amount = entry['amount']
        total_value_usd = entry['value_usd']
        total_value_pln = entry['value_pln']
        total_cost_basis = entry['cost_basis_usd']
        total_pnl = entry['pnl']
        total_realized = entry['realized_pnl']

        average_price = (total_cost_basis / total_amount) if total_amount > 0 else 0.0
        current_price = (total_value_usd / total_amount) if total_amount > 0 else 0.0

        if total_cost_basis > 0:
            pnl_percent = (total_pnl / total_cost_basis) * 100
        else:
            value_weight = sum(max(src['value_usd'], 0.0) for src in entry['sources'])
            if value_weight > 0:
                pnl_percent = (
                    sum((src['pnl_percent'] or 0.0) * max(src['value_usd'], 0.0) for src in entry['sources'])
                    / value_weight
                )
            else:
                pnl_percent = 0.0

        price_source = None
        if entry['price_sources']:
            price_source = next(iter(entry['price_sources']))
            if len(entry['price_sources']) > 1:
                price_source = 'mixed'

        issues_list = sorted(entry['issues']) if entry['issues'] else None

        sources_models = [
            AssetSource(
                exchange=src['exchange'],
                amount=src['amount'],
                value_usd=src['value_usd'],
                value_pln=src['value_pln'],
                average_price=src['average_price'],
                current_price=src['current_price'],
                pnl=src['pnl'],
                pnl_percent=src['pnl_percent'],
                realized_pnl=src['realized_pnl'],
                price_source=src['price_source'],
                issues=src['issues'] or None,
                cost_basis_usd=src['cost_basis_usd'] if src['cost_basis_usd'] > 0 else None,
            )
            for src in sorted(entry['sources'], key=lambda s: s['value_usd'], reverse=True)
        ]

        exchange_label = entry['exchange_order'][0] if len(entry['exchange_order']) == 1 else 'MULTI'

        aggregated_assets.append(
            Asset(
                symbol=symbol,
                amount=total_amount,
                value_usd=total_value_usd,
                value_pln=total_value_pln,
                pnl=total_pnl,
                pnl_percent=pnl_percent,
                exchange=exchange_label,
                average_price=average_price,
                current_price=current_price,
                realized_pnl=total_realized,
                exchange_price=None,
                exchange_value_usd=None,
                price_source=price_source,
                issues=issues_list,
                asset_type=asset_type if asset_type != 'other' else None,
                sources=sources_models or None,
                source_count=len(sources_models) or None,
                cost_basis_usd=total_cost_basis if total_cost_basis > 0 else None,
                exchanges=entry['exchange_order'] if entry['exchange_order'] else None,
            )
        )

    aggregated_assets.sort(key=lambda asset: asset.value_usd, reverse=True)

    return aggregated_assets, sorted(warnings)



class Transaction(BaseModel):
    id: str
    symbol: str
    type: str  # buy/sell
    amount: float
    price: float
    date: str
    exchange: str
    commission: float
    commission_currency: str
    isin: Optional[str] = None
    asset_name: Optional[str] = None

class CreateTransaction(BaseModel):
    symbol: str
    type: str  # buy/sell
    amount: float
    price: float
    date: str
    exchange: str
    commission: float = 0.0
    commission_currency: str = 'USD'
    isin: Optional[str] = None
    asset_name: Optional[str] = None

class UpdateTransaction(BaseModel):
    symbol: Optional[str] = None
    type: Optional[str] = None
    amount: Optional[float] = None
    price: Optional[float] = None
    date: Optional[str] = None
    exchange: Optional[str] = None
    commission: Optional[float] = None
    commission_currency: Optional[str] = None
    isin: Optional[str] = None
    asset_name: Optional[str] = None


def parse_transaction_date(date_str: str) -> datetime:
    """Parse transaction date strings safely for sorting."""
    if not date_str:
        return datetime.min

    cleaned = date_str.strip()

    # Handle ISO format with trailing Z
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"

    # Try ISO formats first
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        pass

    known_formats = [
        "%b %d, %Y at %I:%M %p",
        "%b %d, %Y %I:%M %p",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
    ]

    for fmt in known_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    return datetime.min

class CreateGoal(BaseModel):
    title: str
    type: str  # value, return, diversification
    target_value: Optional[float] = None
    target_percentage: Optional[float] = None
    target_date: Optional[str] = None
    start_value: Optional[float] = None

class UpdateGoal(BaseModel):
    title: Optional[str] = None
    target_value: Optional[float] = None
    target_percentage: Optional[float] = None
    target_date: Optional[str] = None

class ExchangeStatus(BaseModel):
    exchange: str
    connected: bool
    total_value: float
    error: Optional[str] = None

class WatchlistAdd(BaseModel):
    symbol: str
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None

class WatchlistMetadataUpdate(BaseModel):
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None

class BacktestRequest(BaseModel):
    strategy: str
    start_date: str
    end_date: str
    initial_capital: float
    asset_symbol: str
    asset_type: str = 'crypto'
    strategy_params: Optional[Dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "strategy": "buy_and_hold",
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "initial_capital": 10000.0,
                "asset_symbol": "BTC",
                "asset_type": "crypto",
                "strategy_params": {}
            }
        }

# API Routes
@app.get("/")
async def root():
    return {"message": "Portfolio Tracker Pro API", "version": "1.0.0"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat() + "Z"}

@app.get("/api/migration/status")
async def get_migration_status_endpoint(current_user: Dict = Depends(get_current_user)):
    """Get database migration status"""
    try:
        from database import get_migration_status
        status = get_migration_status()
        return status
    except Exception as e:
        app_logger.error(f"Error getting migration status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get migration status: {str(e)}")

@app.get("/api/watchlist")
async def get_user_watchlist(include_metadata: bool = False, current_user: Dict = Depends(get_current_user)):
    """Get user watchlist. Set include_metadata=true to get categories and tags."""
    try:
        username = current_user.get("username", "default")
        if include_metadata:
            data = watchlist_service.get_watchlist_with_metadata(username)
            return data
        else:
            return {"symbols": watchlist_service.get_watchlist(username)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/watchlist")
async def add_user_watchlist(item: WatchlistAdd, current_user: Dict = Depends(get_current_user)):
    try:
        username = current_user.get("username", "default")
        updated = watchlist_service.add_symbol(
            username, 
            item.symbol, 
            categories=item.categories, 
            tags=item.tags
        )
        return {"symbols": updated.get("symbols", []), "metadata": updated.get("metadata", {})}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/watchlist/{symbol}")
async def remove_user_watchlist(symbol: str, current_user: Dict = Depends(get_current_user)):
    try:
        username = current_user.get("username", "default")
        updated = watchlist_service.remove_symbol(username, symbol)
        return {"symbols": updated.get("symbols", []), "metadata": updated.get("metadata", {})}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/watchlist/{symbol}/metadata")
async def update_watchlist_metadata(
    symbol: str, 
    metadata: WatchlistMetadataUpdate, 
    current_user: Dict = Depends(get_current_user)
):
    """Update categories and/or tags for a watchlist symbol"""
    try:
        username = current_user.get("username", "default")
        updated = watchlist_service.update_symbol_metadata(
            username, 
            symbol, 
            categories=metadata.categories, 
            tags=metadata.tags
        )
        return {"symbols": updated.get("symbols", []), "metadata": updated.get("metadata", {})}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class WatchlistBatchAdd(BaseModel):
    symbols: List[str]
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None

class WatchlistBatchRemove(BaseModel):
    symbols: List[str]

class WatchlistBatchMetadata(BaseModel):
    symbols: List[str]
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None

@app.post("/api/watchlist/batch-add")
async def batch_add_watchlist(
    batch: WatchlistBatchAdd,
    current_user: Dict = Depends(get_current_user)
):
    """Add multiple symbols to watchlist at once"""
    try:
        username = current_user.get("username", "default")
        results = {"added": [], "failed": []}
        
        for symbol in batch.symbols:
            try:
                updated = watchlist_service.add_symbol(
                    username,
                    symbol,
                    categories=batch.categories,
                    tags=batch.tags
                )
                results["added"].append(symbol)
            except Exception as e:
                results["failed"].append({"symbol": symbol, "error": str(e)})
        
        # Get final state
        final_data = watchlist_service.get_watchlist_with_metadata(username)
        return {
            "symbols": final_data.get("symbols", []),
            "metadata": final_data.get("metadata", {}),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/watchlist/batch-remove")
async def batch_remove_watchlist(
    batch: WatchlistBatchRemove,
    current_user: Dict = Depends(get_current_user)
):
    """Remove multiple symbols from watchlist at once"""
    try:
        username = current_user.get("username", "default")
        results = {"removed": [], "failed": []}
        
        for symbol in batch.symbols:
            try:
                watchlist_service.remove_symbol(username, symbol)
                results["removed"].append(symbol)
            except Exception as e:
                results["failed"].append({"symbol": symbol, "error": str(e)})
        
        # Get final state
        final_data = watchlist_service.get_watchlist_with_metadata(username)
        return {
            "symbols": final_data.get("symbols", []),
            "metadata": final_data.get("metadata", {}),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/watchlist/batch-metadata")
async def batch_update_metadata(
    batch: WatchlistBatchMetadata,
    current_user: Dict = Depends(get_current_user)
):
    """Update metadata (categories/tags) for multiple symbols at once"""
    try:
        username = current_user.get("username", "default")
        results = {"updated": [], "failed": []}
        
        for symbol in batch.symbols:
            try:
                watchlist_service.update_symbol_metadata(
                    username,
                    symbol,
                    categories=batch.categories,
                    tags=batch.tags
                )
                results["updated"].append(symbol)
            except Exception as e:
                results["failed"].append({"symbol": symbol, "error": str(e)})
        
        # Get final state
        final_data = watchlist_service.get_watchlist_with_metadata(username)
        return {
            "symbols": final_data.get("symbols", []),
            "metadata": final_data.get("metadata", {}),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/exchange-rate")
async def get_exchange_rate(current_user: Dict = Depends(get_current_user)):
    """Get current USD to PLN exchange rate"""
    try:
        rate = exchange_rate_service.get_current_rate()
        return {
            "rate": rate,
            "currency_pair": "USD/PLN",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source": "NBP API / ExchangeRate API"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch exchange rate: {str(e)}"
        )


@app.post("/api/sync/exchanges/check")
async def check_exchange_transactions(
    payload: SyncRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Check exchanges for transactions not yet recorded in local history"""
    try:
        limit = payload.limit or 50
        result = detect_new_trades(portfolio_tracker, transaction_history, current_user["username"], limit=limit)
        return result
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check exchange transactions ({error_type}): {str(e)}"
        )


@app.post("/api/sync/exchanges/import")
async def import_exchange_transactions(
    payload: SyncRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Check exchanges for new transactions and automatically import them into transaction history.
    This operation may take several minutes for multiple exchanges."""
    start_ts = time.time()
    
    try:
        limit = payload.limit or 50
        app_logger.info(f"Starting transaction sync for user {current_user.get('username')} with limit {limit}")
        
        result = import_new_trades(portfolio_tracker, transaction_history, current_user["username"], limit=limit)
        
        elapsed = time.time() - start_ts
        app_logger.info(f"Transaction sync completed in {elapsed:.2f}s: {result.get('summary', {}).get('imported_count', 0)} imported")
        
        return result
    except Exception as e:
        error_type = type(e).__name__
        elapsed = time.time() - start_ts
        app_logger.error(f"Sync exchanges failed after {elapsed:.2f}s: {error_type}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to import exchange transactions ({error_type}): {str(e)}"
        )


@app.get("/api/mobile/dashboard")
async def get_mobile_dashboard(current_user: Dict = Depends(get_current_user)):
    """Get compact mobile dashboard data in a single request"""
    try:
        # Get summary
        portfolios = portfolio_tracker.get_all_portfolios(current_user["username"], use_transactions_only=True)
        if not portfolios:
            summary_dict = {
                "total_value_usd": 0,
                "total_value_pln": 0,
                "total_pnl": 0,
                "total_pnl_percent": 0,
                "active_exchanges": 0,
                "total_assets": 0,
                "last_updated": datetime.utcnow().isoformat() + "Z"
            }
        else:
            total_value_usd = sum(p.get('total_value_usdt', 0) for p in portfolios)
            usd_to_pln_rate = exchange_rate_service.get_current_rate()
            total_value_pln = total_value_usd * usd_to_pln_rate
            active_exchanges = len([p for p in portfolios if p.get('total_value_usdt', 0) > 0])
            total_assets = sum(len(p.get('balances', [])) for p in portfolios)
            try:
                user_id = current_user.get("username")
                realized_pnl = transaction_history.get_total_realized_pnl(user_id=user_id)
                total_pnl = realized_pnl
                total_pnl_percent = (total_pnl / total_value_usd * 100) if total_value_usd > 0 else 0
            except Exception:
                total_pnl = 0
                total_pnl_percent = 0
            
            summary_dict = {
                "total_value_usd": total_value_usd,
                "total_value_pln": total_value_pln,
                "total_pnl": total_pnl,
                "total_pnl_percent": total_pnl_percent,
                "active_exchanges": active_exchanges,
                "total_assets": total_assets,
                "last_updated": datetime.utcnow().isoformat() + "Z"
            }
        
        # Get top 5 assets
        assets = []
        for portfolio in portfolios:
            for balance in portfolio.get('balances', []):
                if balance.get('value_usdt', 0) > 0:
                    asset_symbol = balance.get('asset', '')
                    try:
                        asset_pnl = transaction_history.get_asset_realized_pnl(asset_symbol)
                        asset_pnl_percent = (asset_pnl / balance.get('value_usdt', 1) * 100) if balance.get('value_usdt', 0) > 0 else 0
                    except Exception:
                        asset_pnl = 0
                        asset_pnl_percent = 0
                    
                    assets.append({
                        "symbol": asset_symbol,
                        "amount": balance.get('free', 0) + balance.get('locked', 0),
                        "value_usd": balance.get('value_usdt', 0),
                        "pnl_percent": asset_pnl_percent
                    })
        
        top_assets = sorted(assets, key=lambda x: x['value_usd'], reverse=True)[:5]
        
        # Get recent 5 transactions
        user_id = current_user.get("username")
        all_transactions = transaction_history.get_all_transactions(user_id=user_id)
        recent_tx = [{
            "id": t.get('id', ''),
            "symbol": t.get('asset', ''),
            "type": t.get('type', ''),
            "amount": t.get('amount', 0),
            "price": t.get('price_usd', 0),
            "date": t.get('date', '')
        } for t in all_transactions[:5]]
        
        # Get 7-day performance preview (lite mode)
        history_data = portfolio_history.get_chart_data(days=7, user_id=user_id)
        performance_preview = [
            {
                "date": entry.get('timestamp', ''),
                "value_usd": entry.get('value_usd', 0),
                "value_pln": entry.get('value_pln', 0)
            }
            for entry in history_data
        ][::5]  # Every 5th point for lite mode
        
        return {
            "summary": summary_dict,
            "top_assets": top_assets,
            "recent_transactions": recent_tx,
            "performance_preview": performance_preview[:7] if len(performance_preview) > 7 else performance_preview,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/portfolio/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(current_user: Dict = Depends(get_current_user)):
    """Get portfolio summary with key metrics"""
    start_ts = time.time()
    max_seconds = float(os.getenv("PORTFOLIO_SUMMARY_MAX_SECONDS", "25.0"))  # 25s budget for summary (increased from 15s)
    user_id = current_user.get("username")
    
    try:
        # Get portfolios with error handling
        try:
            app_logger.debug(f"Fetching portfolios for user: {user_id}")
            portfolios = portfolio_tracker.get_all_portfolios(user_id, use_transactions_only=True)
            app_logger.debug(f"Got {len(portfolios)} portfolios for user: {user_id}")
        except Exception as e:
            app_logger.error(f"Error fetching portfolios for user {user_id}: {e}", exc_info=True)
            # Return empty summary instead of crashing
            return PortfolioSummary(
                total_value_usd=0,
                total_value_pln=0,
                total_pnl=0,
                total_pnl_percent=0,
                active_exchanges=0,
                total_assets=0,
                last_updated=datetime.utcnow().isoformat() + "Z",
                warnings=[f"Error fetching portfolios: {str(e)}"],
            )
        
        # Check budget after get_all_portfolios
        if time.time() - start_ts > max_seconds:
            app_logger.warning(f"Portfolio summary exceeded budget ({max_seconds}s) after get_all_portfolios, returning minimal data")
            return PortfolioSummary(
                total_value_usd=0,
                total_value_pln=0,
                total_pnl=0,
                total_pnl_percent=0,
                active_exchanges=0,
                total_assets=0,
                last_updated=datetime.utcnow().isoformat() + "Z",
                warnings=["Summary calculation timeout - data may be incomplete"],
            )
        
        if not portfolios:
            app_logger.debug(f"No portfolios found for user: {user_id}")
            return PortfolioSummary(
                total_value_usd=0,
                total_value_pln=0,
                total_pnl=0,
                total_pnl_percent=0,
                active_exchanges=0,
                total_assets=0,
                last_updated=datetime.utcnow().isoformat() + "Z",
                warnings=None,
            )
        
        # Calculate totals with error handling
        try:
            total_value_usd = sum(p.get('total_value_usdt', 0) for p in portfolios)
            usd_to_pln_rate = exchange_rate_service.get_current_rate()
            assets, asset_warnings = _build_assets_with_validation(portfolios, usd_to_pln_rate, user_id=user_id)
            total_value_pln = total_value_usd * usd_to_pln_rate
            active_exchanges = len([p for p in portfolios if p.get('total_value_usdt', 0) > 0])
            total_assets = len(assets)
        except Exception as e:
            app_logger.error(f"Error calculating portfolio totals for user {user_id}: {e}", exc_info=True)
            # Return minimal data instead of crashing
            return PortfolioSummary(
                total_value_usd=0,
                total_value_pln=0,
                total_pnl=0,
                total_pnl_percent=0,
                active_exchanges=0,
                total_assets=0,
                last_updated=datetime.utcnow().isoformat() + "Z",
                warnings=[f"Error calculating portfolio totals: {str(e)}"],
            )
        
        # Calculate real PNL from transaction history (realized + unrealized)
        try:
            realized_pnl = transaction_history.get_total_realized_pnl(user_id=user_id)
            
            # Calculate unrealized PNL for all assets
            unrealized_pnl = 0.0
            for portfolio in portfolios:
                for balance in portfolio.get('balances', []):
                    if balance.get('value_usdt', 0) > 0:
                        try:
                            asset_symbol = balance.get('asset', '')
                            exchange = portfolio.get('exchange', '')
                            
                            asset_transactions = transaction_history.get_transactions_for_asset(exchange, asset_symbol, user_id=user_id)
                            if asset_transactions:
                                buy_transactions = [t for t in asset_transactions if t.get('type', '').lower() == 'buy']
                                sell_transactions = [t for t in asset_transactions if t.get('type', '').lower() == 'sell']
                                
                                buy_amount = sum(t.get('amount', 0) for t in buy_transactions)
                                sell_amount = sum(t.get('amount', 0) for t in sell_transactions)
                                net_amount = buy_amount - sell_amount
                                
                                if net_amount > 0:
                                    current_price = balance.get('value_usdt', 0) / balance.get('total', 1) if balance.get('total', 0) > 0 else 0
                                    current_value = net_amount * current_price
                                    
                                    total_invested = sum(t.get('value_usd', 0) for t in buy_transactions)
                                    cost_basis = total_invested * (net_amount / buy_amount) if buy_amount > 0 else 0
                                    
                                    asset_unrealized = current_value - cost_basis
                                    unrealized_pnl += asset_unrealized
                        except Exception as e:
                            app_logger.warning(f"Error calculating unrealized PNL for asset {balance.get('asset', 'unknown')}: {e}")
                            continue
            
            total_pnl = realized_pnl + unrealized_pnl
            total_pnl_percent = (total_pnl / total_value_usd * 100) if total_value_usd > 0 else 0
        except Exception as e:
            app_logger.error(f"Error calculating PNL for user {user_id}: {e}", exc_info=True)
            total_pnl = 0
            total_pnl_percent = 0
        
        # Auto-add portfolio snapshot if enough time has passed (throttled to 1/hour)
        try:
            if portfolio_history.should_add_snapshot(min_interval_hours=1, user_id=user_id):
                portfolio_history.add_snapshot(total_value_usd, total_value_pln, user_id=user_id)
        except Exception as e:
            app_logger.warning(f"Could not add portfolio snapshot for user {user_id}: {e}")
        
        return PortfolioSummary(
            total_value_usd=total_value_usd,
            total_value_pln=total_value_pln,
            total_pnl=total_pnl,
            total_pnl_percent=total_pnl_percent,
            active_exchanges=active_exchanges,
            total_assets=total_assets,
            last_updated=datetime.utcnow().isoformat() + "Z",
            warnings=asset_warnings or None,
        )
    except (Timeout, ConnectionError) as e:
        app_logger.error(f"Network error in get_portfolio_summary for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"Service temporarily unavailable: Unable to connect to exchange APIs. Error: {str(e)}"
        )
    except RequestException as e:
        app_logger.error(f"Request error in get_portfolio_summary for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=502,
            detail=f"Bad gateway: Exchange API request failed. Error: {str(e)}"
        )
    except Exception as e:
        error_type = type(e).__name__
        app_logger.error(f"Unexpected error in get_portfolio_summary for user {user_id}: {e}", exc_info=True)
        # Return minimal data instead of crashing
        return PortfolioSummary(
            total_value_usd=0,
            total_value_pln=0,
            total_pnl=0,
            total_pnl_percent=0,
            active_exchanges=0,
            total_assets=0,
            last_updated=datetime.utcnow().isoformat() + "Z",
            warnings=[f"Unexpected error ({error_type}): {str(e)}"],
        )

@app.get("/api/portfolio/assets", response_model=List[Asset])
async def get_portfolio_assets(current_user: Dict = Depends(get_current_user)):
    """Get detailed asset breakdown"""
    start_ts = time.time()
    max_seconds = float(os.getenv("PORTFOLIO_ASSETS_MAX_SECONDS", "25.0"))  # 25s budget for assets (increased from 15s)
    user_id = current_user.get("username")
    
    try:
        # Check budget BEFORE expensive operations
        def check_budget() -> bool:
            elapsed = time.time() - start_ts
            if elapsed > max_seconds:
                app_logger.warning(f"Portfolio assets exceeded budget ({max_seconds}s) after {elapsed:.2f}s, returning partial data")
                return False
            return True
        
        if not check_budget():
            return []
        
        # Get portfolios with error handling
        try:
            app_logger.debug(f"Fetching portfolios for assets for user: {user_id}")
            portfolios = portfolio_tracker.get_all_portfolios(user_id, use_transactions_only=True)
            app_logger.debug(f"Got {len(portfolios)} portfolios for assets for user: {user_id}")
        except Exception as e:
            app_logger.error(f"Error fetching portfolios for assets for user {user_id}: {e}", exc_info=True)
            # Return empty list instead of crashing
            return []
        
        # Check budget again after get_all_portfolios
        if not check_budget():
            return []
        
        try:
            usd_to_pln_rate = exchange_rate_service.get_current_rate()
            assets, warnings = _build_assets_with_validation(portfolios, usd_to_pln_rate, user_id=user_id)

            if warnings:
                app_logger.warning(f"Asset validation warnings for user {user_id}: {'; '.join(warnings)}")

            return assets
        except Exception as e:
            app_logger.error(f"Error building assets for user {user_id}: {e}", exc_info=True)
            # Return empty list instead of crashing
            return []
    except (Timeout, ConnectionError) as e:
        app_logger.error(f"Network error in get_portfolio_assets for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"Service temporarily unavailable: Unable to connect to exchange APIs. Error: {str(e)}"
        )
    except RequestException as e:
        app_logger.error(f"Request error in get_portfolio_assets for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=502,
            detail=f"Bad gateway: Exchange API request failed. Error: {str(e)}"
        )
    except Exception as e:
        error_type = type(e).__name__
        app_logger.error(f"Unexpected error in get_portfolio_assets for user {user_id}: {e}", exc_info=True)
        # Return empty list instead of crashing
        return []

@app.get("/api/transactions", response_model=List[Transaction])
async def get_transactions(
    limit: int = 50, 
    offset: int = 0,
    type: Optional[str] = None,
    symbol: Optional[str] = None,
    exchange: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Get transaction history with pagination and filtering"""
    try:
        # Get ALL transactions for user (without limit/offset) so we can filter and paginate properly
        # Pagination will be applied after filtering in Python
        all_transactions = transaction_history.get_all_transactions(user_id=current_user.get("username"))
        
        # Apply filters before pagination
        filtered_transactions = all_transactions.copy()
        
        # Filter by type
        if type:
            type_lower = type.lower()
            filtered_transactions = [tx for tx in filtered_transactions 
                                   if tx.get('type', '').lower() == type_lower]
        
        # Filter by symbol (asset)
        if symbol:
            symbol_lower = symbol.lower()
            filtered_transactions = [tx for tx in filtered_transactions 
                                   if tx.get('asset', '').lower() == symbol_lower]
        
        # Filter by exchange
        if exchange:
            exchange_lower = exchange.lower()
            filtered_transactions = [tx for tx in filtered_transactions 
                                   if tx.get('exchange', '').lower() == exchange_lower]
        
        # Search filter (searches in symbol/asset and exchange)
        if search:
            search_lower = search.lower()
            filtered_transactions = [tx for tx in filtered_transactions 
                                   if search_lower in tx.get('asset', '').lower() 
                                   or search_lower in tx.get('exchange', '').lower()]
        
        # Filter by date range
        if date_from:
            filtered_transactions = [tx for tx in filtered_transactions 
                                   if tx.get('date', '') >= date_from]
        
        if date_to:
            filtered_transactions = [tx for tx in filtered_transactions 
                                   if tx.get('date', '') <= date_to]
        
        # Sort by date (newest first) before pagination
        filtered_transactions = sorted(
            filtered_transactions,
            key=lambda x: parse_transaction_date(x.get('date', '')),
            reverse=True
        )
        
        # Apply pagination after filtering and sorting
        total_count = len(filtered_transactions)
        paginated_transactions = filtered_transactions[offset:offset + limit]
        
        # Convert to API format
        transactions = []
        for tx in paginated_transactions:
            transactions.append(Transaction(
                id=str(tx.get('id', '')),
                symbol=tx.get('asset', ''),
                type=tx.get('type', ''),
                amount=tx.get('amount', 0.0),
                price=tx.get('price_usd', 0.0),
                date=tx.get('date', ''),
                exchange=tx.get('exchange', ''),
                commission=tx.get('commission', 0.0),
                commission_currency=tx.get('commission_currency', 'USD'),
                isin=tx.get('isin'),
                asset_name=tx.get('asset_name')
            ))
        
        return transactions
    except (Timeout, ConnectionError) as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service temporarily unavailable: Unable to connect to exchange APIs. Error: {str(e)}"
        )
    except RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Bad gateway: Exchange API request failed. Error: {str(e)}"
        )
    except Exception as e:
            error_type = type(e).__name__
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error ({error_type}): {str(e)}"
            )

@app.post("/api/transactions", response_model=Transaction)
async def create_transaction(transaction_data: CreateTransaction, current_user: Dict = Depends(get_current_user)):
    """Create a new transaction"""
    try:
        # Validate transaction data
        validation_data = {
            'symbol': transaction_data.symbol,
            'type': transaction_data.type,
            'amount': transaction_data.amount,
            'price': transaction_data.price,
            'date': transaction_data.date,
            'exchange': transaction_data.exchange,
            'commission': transaction_data.commission
        }

        if transaction_data.asset_name is not None:
            validation_data['asset_name'] = transaction_data.asset_name
        if transaction_data.isin is not None:
            validation_data['isin'] = transaction_data.isin
        
        is_valid, errors = TransactionValidator.validate_create(validation_data)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Validation failed: {'; '.join(errors)}"
            )
        
        new_tx = transaction_history.add_transaction(
            exchange=transaction_data.exchange,
            asset=transaction_data.symbol,
            amount=transaction_data.amount,
            price_usd=transaction_data.price,
            transaction_type=transaction_data.type,
            date=transaction_data.date,
            commission=transaction_data.commission,
            commission_currency=transaction_data.commission_currency,
            isin=transaction_data.isin.strip().upper() if transaction_data.isin else None,
            asset_name=transaction_data.asset_name.strip() if transaction_data.asset_name else None,
            user_id=current_user.get("username")
        )
        
        return Transaction(
            id=str(new_tx['id']),
            symbol=new_tx['asset'],
            type=new_tx['type'],
            amount=new_tx['amount'],
            price=new_tx['price_usd'],
            date=new_tx['date'],
            exchange=new_tx['exchange'],
            commission=new_tx['commission'],
            commission_currency=new_tx['commission_currency']
        )
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.put("/api/transactions/{transaction_id}", response_model=Transaction)
async def update_transaction(transaction_id: int, transaction_data: UpdateTransaction, current_user: Dict = Depends(get_current_user)):
    """Update an existing transaction"""
    try:
        # Get transaction to check if it exists
        user_id = current_user.get("username")
        all_transactions = transaction_history.get_all_transactions(user_id=user_id)
        tx = next((t for t in all_transactions if t['id'] == transaction_id), None)
        
        if not tx:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Validate update data
        validation_data = {}
        if transaction_data.symbol is not None:
            validation_data['symbol'] = transaction_data.symbol
        if transaction_data.type is not None:
            validation_data['type'] = transaction_data.type
        if transaction_data.amount is not None:
            validation_data['amount'] = transaction_data.amount
        if transaction_data.price is not None:
            validation_data['price'] = transaction_data.price
        if transaction_data.date is not None:
            validation_data['date'] = transaction_data.date
        if transaction_data.exchange is not None:
            validation_data['exchange'] = transaction_data.exchange
        if transaction_data.commission is not None:
            validation_data['commission'] = transaction_data.commission
        if transaction_data.isin is not None:
            validation_data['isin'] = transaction_data.isin
        if transaction_data.asset_name is not None:
            validation_data['asset_name'] = transaction_data.asset_name
        
        is_valid, errors = TransactionValidator.validate_update(validation_data)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Validation failed: {'; '.join(errors)}"
            )
        
        # Prepare update dict (only include non-None values)
        update_dict = {}
        if transaction_data.symbol is not None:
            update_dict['asset'] = transaction_data.symbol
        if transaction_data.type is not None:
            update_dict['type'] = transaction_data.type
        if transaction_data.amount is not None:
            update_dict['amount'] = transaction_data.amount
        if transaction_data.price is not None:
            update_dict['price_usd'] = transaction_data.price
        if transaction_data.date is not None:
            update_dict['date'] = transaction_data.date
        if transaction_data.exchange is not None:
            update_dict['exchange'] = transaction_data.exchange
        if transaction_data.commission is not None:
            update_dict['commission'] = transaction_data.commission
        if transaction_data.commission_currency is not None:
            update_dict['commission_currency'] = transaction_data.commission_currency
        if transaction_data.isin is not None:
            stripped_isin = transaction_data.isin.strip().upper() if transaction_data.isin else ''
            update_dict['isin'] = stripped_isin if stripped_isin else None
        if transaction_data.asset_name is not None:
            stripped_name = transaction_data.asset_name.strip() if transaction_data.asset_name else ''
            update_dict['asset_name'] = stripped_name if stripped_name else None
        
        # Update transaction
        user_id = current_user.get("username")
        success = transaction_history.update_transaction(transaction_id, user_id=user_id, **update_dict)
        
        if not success:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Get updated transaction
        user_id = current_user.get("username")
        updated_transactions = transaction_history.get_all_transactions(user_id=user_id)
        updated_tx = next((t for t in updated_transactions if t['id'] == transaction_id), None)
        
        return Transaction(
            id=str(updated_tx['id']),
            symbol=updated_tx['asset'],
            type=updated_tx['type'],
            amount=updated_tx['amount'],
            price=updated_tx['price_usd'],
            date=updated_tx['date'],
            exchange=updated_tx['exchange'],
            commission=updated_tx['commission'],
            commission_currency=updated_tx['commission_currency'],
            isin=updated_tx.get('isin'),
            asset_name=updated_tx.get('asset_name')
        )
    except HTTPException:
        raise
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.delete("/api/transactions/{transaction_id}")
async def delete_transaction(transaction_id: int, current_user: Dict = Depends(get_current_user)):
    """Delete a transaction"""
    try:
        # Check if transaction exists
        user_id = current_user.get("username")
        all_transactions = transaction_history.get_all_transactions(user_id=user_id)
        tx = next((t for t in all_transactions if t['id'] == transaction_id), None)
        
        if not tx:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        user_id = current_user.get("username")
        transaction_history.delete_transaction(transaction_id, user_id=user_id)
        
        return {"message": "Transaction deleted successfully", "id": transaction_id}
    except HTTPException:
        raise
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/transactions/export")
async def export_transactions(format: str = "csv", current_user: Dict = Depends(get_current_user)):
    """Export transactions to CSV or JSON"""
    try:
        user_id = current_user.get("username")
        all_transactions = transaction_history.get_all_transactions(user_id=user_id)
        
        if format.lower() == "csv":
            # Create CSV in memory
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'ID', 'Date', 'Exchange', 'Asset', 'Asset Name', 'ISIN', 'Type', 
                'Amount', 'Price (USD)', 'Total (USD)', 
                'Commission', 'Commission Currency'
            ])
            
            # Write rows
            for tx in all_transactions:
                writer.writerow([
                    tx.get('id', ''),
                    tx.get('date', ''),
                    tx.get('exchange', ''),
                    tx.get('asset', ''),
                    tx.get('asset_name', ''),
                    tx.get('isin', ''),
                    tx.get('type', '').upper(),
                    tx.get('amount', 0.0),
                    tx.get('price_usd', 0.0),
                    tx.get('value_usd', 0.0),
                    tx.get('commission', 0.0),
                    tx.get('commission_currency', 'USD')
                ])
            
            output.seek(0)
            
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f'attachment; filename="transactions_{len(all_transactions)}.csv"'
                }
            )
        else:
            # JSON format (default)
            return {
                "transactions": all_transactions,
                "count": len(all_transactions),
                "format": "json"
            }
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/exchanges/status", response_model=List[ExchangeStatus])
async def get_exchange_status(current_user: Dict = Depends(get_current_user)):
    """Get status of all connected exchanges"""
    try:
        statuses = exchange_manager.get_exchange_status()
        return [ExchangeStatus(**status) for status in statuses]
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/analytics/performance")
async def get_performance_analytics(days: int = 30, current_user: Dict = Depends(get_current_user)):
    """Get portfolio performance analytics"""
    try:
        start_ts = time.time()
        max_seconds = float(os.getenv("PERFORMANCE_ANALYTICS_MAX_SECONDS", "5.0"))
        
        user_id = current_user.get("username")
        history_data = portfolio_history.get_chart_data(days=days, user_id=user_id)
        
        # Enforce time budget early
        if time.time() - start_ts > max_seconds:
            app_logger.warning(f"Performance analytics exceeded budget ({max_seconds}s), returning minimal data")
            return {
                "period": f"{days} days",
                "total_return": 0.0,
                "daily_returns": [],
                "volatility": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "win_rate": 0.0,
                "message": "Analytics computation timeout - insufficient time budget"
            }

        if not history_data:
            # Not enough data for analytics
            return {
                "period": f"{days} days",
                "total_return": 0.0,
                "daily_returns": [],
                "volatility": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "win_rate": 0.0,
                "message": "Insufficient data for analytics"
            }

        # Normalize history to one value per day (latest snapshot wins)
        sorted_history = sorted(
            history_data,
            key=lambda p: p.get('timestamp') or p.get('date') or ""
        )

        daily_points: List[Dict[str, Any]] = []
        day_buckets: Dict[str, Dict[str, Any]] = {}

        for point in sorted_history:
            raw_timestamp = point.get('timestamp') or point.get('date')
            if not raw_timestamp:
                continue
            day_key = raw_timestamp[:10]
            try:
                bucket_timestamp = datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00"))
            except ValueError:
                bucket_timestamp = None

            value_usd = point.get('value_usd') or point.get('value')
            if value_usd is None or value_usd <= 0:
                continue

            bucket = day_buckets.setdefault(day_key, {
                "value": float(value_usd),
                "timestamp": bucket_timestamp,
                "raw": point,
            })

            if bucket_timestamp and bucket.get("timestamp"):
                if bucket_timestamp > bucket["timestamp"]:
                    bucket["value"] = float(value_usd)
                    bucket["timestamp"] = bucket_timestamp
                    bucket["raw"] = point
            else:
                bucket["value"] = float(value_usd)
                bucket["timestamp"] = bucket_timestamp
                bucket["raw"] = point

        for day_key in sorted(day_buckets.keys()):
            bucket = day_buckets[day_key]
            daily_points.append({
                "date": day_key,
                "value": bucket["value"],
                "pln": bucket["raw"].get("value_pln"),
                "assets": bucket["raw"].get("total_assets"),
                "exchanges": bucket["raw"].get("active_exchanges"),
            })

        if len(daily_points) < 2:
            return {
                "period": f"{days} days",
                "total_return": 0.0,
                "daily_returns": [],
                "volatility": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "win_rate": 0.0,
                "message": "Insufficient daily samples for analytics"
            }

        values = [p['value'] for p in daily_points]

        # Calculate daily returns (percentage change between consecutive daily closes)
        daily_returns = []
        for i in range(1, len(values)):
            if values[i-1] > 0:
                daily_return = ((values[i] - values[i-1]) / values[i-1]) * 100
                daily_returns.append(daily_return)
            else:
                daily_returns.append(0.0)
        
        if not daily_returns:
            return {
                "period": f"{days} days",
                "total_return": 0.0,
                "daily_returns": [],
                "volatility": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "win_rate": 0.0
            }
        
        # Calculate total return (first to last)
        total_return = ((values[-1] - values[0]) / values[0] * 100) if values[0] > 0 else 0.0
        
        # Calculate volatility (annualized standard deviation)
        import statistics
        if len(daily_returns) > 1:
            daily_return_std = statistics.stdev(daily_returns)
            volatility = daily_return_std * (252 ** 0.5)  # Annualized (in percentage)
        else:
            volatility = 0.0
            daily_return_std = 0.0
        
        # Calculate Sharpe ratio (assuming 0% risk-free rate)
        # Sharpe = (Annualized Return - Risk Free Rate) / Annualized Volatility
        # Since returns are in percentages, we work with percentages
        avg_daily_return = statistics.mean(daily_returns) if daily_returns else 0.0
        annualized_return = avg_daily_return * 252  # Annualized return in percentage
        
        if volatility > 0:
            sharpe_ratio = annualized_return / volatility
        else:
            sharpe_ratio = 0.0
        
        # Calculate max drawdown
        # Max drawdown = maximum percentage decline from peak
        max_drawdown = 0.0
        peak = values[0]
        for value in values:
            if value > peak:
                peak = value  # Update peak when new high reached
            # Calculate drawdown as positive percentage: (peak - value) / peak
            drawdown = ((peak - value) / peak * 100) if peak > 0 else 0.0
            if drawdown > max_drawdown:  # Track maximum drawdown (largest decline)
                max_drawdown = drawdown
        
        # Calculate win rate (% of positive days)
        positive_days = sum(1 for r in daily_returns if r > 0)
        win_rate = (positive_days / len(daily_returns) * 100) if daily_returns else 0.0
        
        return {
            "period": f"{days} days",
            "total_return": round(total_return, 2),
            "daily_returns": [round(r, 2) for r in daily_returns[-30:]],  # Last 30 days
            "volatility": round(volatility, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "max_drawdown": round(max_drawdown, 2),
            "win_rate": round(win_rate, 1),
            "data_points": len(values)
        }
    except (Timeout, ConnectionError) as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service temporarily unavailable: Unable to connect to exchange APIs. Error: {str(e)}"
        )
    except RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Bad gateway: Exchange API request failed. Error: {str(e)}"
        )
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/analytics/risk")
async def get_risk_analytics(
    days: int = 180,
    confidence: float = 0.95,
    sharpe_window: int = 30,
    current_user: Dict = Depends(get_current_user)
):
    """Compute VaR, CVaR and rolling Sharpe based on portfolio history (USD values)."""
    try:
        # Get portfolio history
        user_id = current_user.get("username")
        history_points = portfolio_history.get_chart_data(days, user_id=user_id)
        # Transform for service
        values = [{
            "timestamp": p["timestamp"],
            "value_usd": p.get("value_usd") or p.get("value", 0)
        } for p in history_points]

        # Compute daily returns (%)
        returns = risk_analytics_service.compute_daily_returns(values)

        var_cvar = risk_analytics_service.calculate_var_cvar(returns, confidence)
        sharpe = risk_analytics_service.calculate_rolling_sharpe(returns, window=sharpe_window)

        return {
            "days": days,
            "confidence": confidence,
            "var": var_cvar["var"],
            "cvar": var_cvar["cvar"],
            "sharpe_window": sharpe_window,
            "rolling_sharpe_latest": sharpe["latest"],
            "rolling_sharpe_series": sharpe["series"],
            "samples": var_cvar["sample"]
        }
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/analytics/correlation-matrix")
async def get_correlation_matrix(current_user: Dict = Depends(get_current_user)):
    """Calculate correlation matrix between assets based on portfolio history"""
    try:
        import statistics
        import math
        
        # Get portfolio history for last 90 days
        user_id = current_user.get("username")
        history_points = portfolio_history.get_chart_data(days=90, user_id=user_id)
        if len(history_points) < 10:
            return {}
        
        # Get all assets
        portfolios = portfolio_tracker.get_all_portfolios(current_user["username"], use_transactions_only=True)
        asset_symbols = set()
        for portfolio in portfolios:
            for balance in portfolio.get('balances', []):
                symbol = balance.get('asset', '')
                if symbol:
                    asset_symbols.add(symbol)
        
        if len(asset_symbols) < 2:
            return {}
        
        # Build price history for each asset using market_data_service
        # Cache correlation matrix for 1 hour to avoid excessive API calls
        cache_key = f"correlation_matrix_{len(asset_symbols)}"
        correlation_cache_ttl = 3600  # 1 hour
        
        # Check cache first
        if hasattr(market_data_service, '_price_cache'):
            if cache_key in market_data_service._price_cache:
                cached = market_data_service._price_cache[cache_key]
                if isinstance(cached, dict) and 'timestamp' in cached:
                    if time.time() - cached['timestamp'] < correlation_cache_ttl:
                        app_logger.debug(f"Returning cached correlation matrix")
                        return cached['data']
        
        asset_histories: Dict[str, List[float]] = {}
        asset_dates: Dict[str, List[str]] = {}
        
        # Fetch real price history for each asset
        for symbol in asset_symbols:
            try:
                # Get 90 days of history for correlation calculation
                history = market_data_service.get_symbol_history(symbol, days=90)
                if history and len(history) >= 10:
                    # Extract dates and close prices
                    dates = [h.get('date') for h in history if h.get('date')]
                    prices = [h.get('close') for h in history if h.get('close')]
                    if len(dates) == len(prices) and len(prices) >= 10:
                        asset_dates[symbol] = dates
                        asset_histories[symbol] = prices
                    else:
                        app_logger.debug(f"Insufficient data for {symbol}: {len(prices)} prices, {len(dates)} dates")
                else:
                    app_logger.debug(f"No history data for {symbol}")
            except Exception as e:
                app_logger.warning(f"Error fetching history for {symbol}: {e}")
                # Fallback: skip this symbol or use mock
                continue
        
        # If we have less than 2 assets with real data, return empty or use fallback
        valid_symbols = [s for s in asset_symbols if s in asset_histories and len(asset_histories[s]) >= 10]
        if len(valid_symbols) < 2:
            app_logger.warning(f"Only {len(valid_symbols)} assets with valid data, returning empty correlation matrix")
            return {}
        
        # Align dates across all assets (find common date range)
        if len(valid_symbols) >= 2:
            # Find common dates
            common_dates = set(asset_dates[valid_symbols[0]])
            for symbol in valid_symbols[1:]:
                common_dates = common_dates.intersection(set(asset_dates[symbol]))
            
            if len(common_dates) < 10:
                app_logger.warning(f"Only {len(common_dates)} common dates, returning empty correlation matrix")
                return {}
            
            # Sort dates and filter histories to common dates only
            sorted_dates = sorted(list(common_dates))
            aligned_histories: Dict[str, List[float]] = {}
            
            for symbol in valid_symbols:
                symbol_dates = asset_dates[symbol]
                symbol_prices = asset_histories[symbol]
                # Create date->price mapping
                date_price_map = {date: price for date, price in zip(symbol_dates, symbol_prices)}
                # Extract prices for common dates in order
                aligned_histories[symbol] = [date_price_map[date] for date in sorted_dates if date in date_price_map]
            
            # Update asset_histories to use aligned data
            asset_histories = aligned_histories
            asset_symbols = valid_symbols
        
        # Calculate daily returns for each asset
        asset_returns: Dict[str, List[float]] = {}
        for symbol in asset_symbols:
            returns = []
            prices = asset_histories[symbol]
            for i in range(1, len(prices)):
                if prices[i-1] > 0:
                    daily_return = (prices[i] - prices[i-1]) / prices[i-1]
                    returns.append(daily_return)
            asset_returns[symbol] = returns
        
        # Calculate correlation matrix
        correlation_matrix: Dict[str, Dict[str, float]] = {}
        symbols_list = sorted(list(asset_symbols))
        
        for symbol1 in symbols_list:
            correlation_matrix[symbol1] = {}
            returns1 = asset_returns.get(symbol1, [])
            
            if len(returns1) < 2:
                for symbol2 in symbols_list:
                    correlation_matrix[symbol1][symbol2] = 0.0
                continue
            
            for symbol2 in symbols_list:
                if symbol1 == symbol2:
                    correlation_matrix[symbol1][symbol2] = 1.0
                else:
                    returns2 = asset_returns.get(symbol2, [])
                    if len(returns2) < 2:
                        correlation_matrix[symbol1][symbol2] = 0.0
                        continue
                    
                    # Calculate Pearson correlation
                    min_len = min(len(returns1), len(returns2))
                    if min_len < 2:
                        correlation_matrix[symbol1][symbol2] = 0.0
                        continue
                    
                    r1 = returns1[:min_len]
                    r2 = returns2[:min_len]
                    
                    mean1 = statistics.mean(r1)
                    mean2 = statistics.mean(r2)
                    
                    numerator = sum((r1[i] - mean1) * (r2[i] - mean2) for i in range(min_len))
                    variance1 = sum((r1[i] - mean1) ** 2 for i in range(min_len))
                    variance2 = sum((r2[i] - mean2) ** 2 for i in range(min_len))
                    
                    denominator = math.sqrt(variance1 * variance2)
                    
                    if denominator == 0:
                        correlation = 0.0
                    else:
                        correlation = numerator / denominator
                        # Clamp to [-1, 1]
                        correlation = max(-1.0, min(1.0, correlation))
                    
                    correlation_matrix[symbol1][symbol2] = round(correlation, 4)
        
        # Cache the result
        if hasattr(market_data_service, '_price_cache'):
            market_data_service._price_cache[cache_key] = {
                'data': correlation_matrix,
                'timestamp': time.time()
            }
        
        return correlation_matrix
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/analytics/portfolio-optimizer", tags=["Analytics"])
async def get_portfolio_optimizer(
    method: str = "mpt",  # "mpt" or "risk_parity"
    risk_free_rate: float = 0.02,  # 2% annual risk-free rate
    target_return: Optional[float] = None,
    max_weight: float = 0.4,  # Maximum 40% per asset
    current_user: Dict = Depends(get_current_user)
):
    """Get optimized portfolio weights using Modern Portfolio Theory or Risk Parity"""
    try:
        # Get user's assets
        portfolios = portfolio_tracker.get_all_portfolios(current_user["username"], use_transactions_only=True)
        assets = []
        asset_symbols = set()
        
        for portfolio in portfolios:
            for balance in portfolio.get('balances', []):
                symbol = balance.get('asset', '')
                value_usd = balance.get('value_usdt', 0) or balance.get('value_usd', 0)
                if symbol and value_usd > 0:
                    asset_symbols.add(symbol)
                    assets.append({
                        'symbol': symbol,
                        'value_usd': value_usd,
                        'asset_type': 'crypto' if portfolio.get('exchange') in ['Binance', 'Bybit'] else 'stock'
                    })
        
        if len(assets) < 2:
            return {
                'optimized_weights': {},
                'current_weights': {},
                'method': method,
                'message': 'Need at least 2 assets for optimization'
            }
        
        # Get current weights
        total_value = sum(a['value_usd'] for a in assets)
        current_weights = {a['symbol']: (a['value_usd'] / total_value * 100) for a in assets}
        
        # Get historical returns for optimization
        asset_returns_data: Dict[str, List[float]] = {}
        for asset in assets:
            symbol = asset['symbol']
            try:
                if market_data_service:
                    history = market_data_service.get_symbol_history(symbol, days=90)
                    if history and len(history) >= 30:
                        if isinstance(history, tuple):
                            history = history[0]
                        prices = [point.get('close', 0) for point in history if point.get('close')]
                        if len(prices) >= 30:
                            returns = []
                            for i in range(1, len(prices)):
                                if prices[i-1] > 0:
                                    ret = (prices[i] - prices[i-1]) / prices[i-1]
                                    returns.append(ret)
                            if len(returns) >= 20:
                                asset_returns_data[symbol] = returns
            except Exception:
                continue
        
        if len(asset_returns_data) < 2:
            return {
                'optimized_weights': current_weights,
                'current_weights': current_weights,
                'method': method,
                'message': 'Insufficient historical data for optimization'
            }
        
        # Calculate optimized weights
        optimized_weights = {}
        
        if method == "mpt":
            # Modern Portfolio Theory - maximize Sharpe ratio
            try:
                import numpy as np
                symbols = list(asset_returns_data.keys())
                n = len(symbols)
                
                # Calculate expected returns and covariance matrix
                expected_returns = np.array([np.mean(asset_returns_data[s]) for s in symbols])
                min_len = min(len(asset_returns_data[s]) for s in symbols)
                returns_matrix = np.array([asset_returns_data[s][:min_len] for s in symbols])
                cov_matrix = np.cov(returns_matrix)
                
                # Annualize (assuming daily returns)
                expected_returns = expected_returns * 252
                cov_matrix = cov_matrix * 252
                
                # Simple optimization: equal risk contribution (simplified MPT)
                # In production, would use scipy.optimize for proper optimization
                inv_cov = np.linalg.pinv(cov_matrix)
                ones = np.ones(n)
                
                # Minimum variance portfolio weights
                w = inv_cov @ ones / (ones.T @ inv_cov @ ones)
                w = np.maximum(w, 0)  # No short selling
                w = w / np.sum(w)  # Normalize
                
                # Apply max_weight constraint
                w = np.minimum(w, max_weight / 100)
                w = w / np.sum(w)  # Renormalize
                
                for i, symbol in enumerate(symbols):
                    optimized_weights[symbol] = round(float(w[i]) * 100, 2)
            except Exception as e:
                app_logger.warning(f"MPT optimization failed: {e}, using equal weights")
                # Fallback to equal weights
                equal_weight = 100 / len(asset_returns_data)
                for symbol in asset_returns_data.keys():
                    optimized_weights[symbol] = round(equal_weight, 2)
        
        elif method == "risk_parity":
            # Risk Parity - equal risk contribution from each asset
            try:
                import numpy as np
                symbols = list(asset_returns_data.keys())
                n = len(symbols)
                
                # Calculate volatilities
                volatilities = np.array([np.std(asset_returns_data[s]) * np.sqrt(252) for s in symbols])
                
                # Risk parity: weights inversely proportional to volatility
                inv_vol = 1.0 / (volatilities + 1e-6)  # Add small epsilon to avoid division by zero
                w = inv_vol / np.sum(inv_vol)
                
                # Apply max_weight constraint
                w = np.minimum(w, max_weight / 100)
                w = w / np.sum(w)  # Renormalize
                
                for i, symbol in enumerate(symbols):
                    optimized_weights[symbol] = round(float(w[i]) * 100, 2)
            except Exception as e:
                app_logger.warning(f"Risk parity optimization failed: {e}, using equal weights")
                # Fallback to equal weights
                equal_weight = 100 / len(asset_returns_data)
                for symbol in asset_returns_data.keys():
                    optimized_weights[symbol] = round(equal_weight, 2)
        
        # Calculate expected metrics
        expected_return = 0
        expected_volatility = 0
        sharpe_ratio = 0
        
        try:
            import numpy as np
            symbols = list(asset_returns_data.keys())
            min_len = min(len(asset_returns_data[s]) for s in symbols)
            returns_matrix = np.array([asset_returns_data[s][:min_len] for s in symbols])
            
            # Portfolio expected return
            weights_array = np.array([optimized_weights.get(s, 0) / 100 for s in symbols])
            portfolio_returns = returns_matrix.T @ weights_array
            expected_return = np.mean(portfolio_returns) * 252 * 100  # Annualized in %
            expected_volatility = np.std(portfolio_returns) * np.sqrt(252) * 100  # Annualized in %
            
            if expected_volatility > 0:
                sharpe_ratio = (expected_return - risk_free_rate * 100) / expected_volatility
        except Exception:
            pass
        
        return {
            'optimized_weights': optimized_weights,
            'current_weights': current_weights,
            'method': method,
            'expected_return': round(expected_return, 2),
            'expected_volatility': round(expected_volatility, 2),
            'sharpe_ratio': round(sharpe_ratio, 3),
            'rebalancing_needed': any(
                abs(optimized_weights.get(s, 0) - current_weights.get(s, 0)) > 5
                for s in set(list(optimized_weights.keys()) + list(current_weights.keys()))
            )
        }
    except HTTPException:
        raise
    except Exception as e:
        error_type = type(e).__name__
        app_logger.error(f"Error optimizing portfolio: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/analytics/advanced", tags=["Analytics"])
async def get_advanced_analytics(
    days: int = 90,
    benchmark: str = "SPY",
    current_user: Dict = Depends(get_current_user)
):
    """Get comprehensive advanced analytics including correlation, risk-return, efficient frontier, and beta analysis."""
    try:
        import asyncio
        
        # Get user's assets
        portfolios = portfolio_tracker.get_all_portfolios(current_user["username"], use_transactions_only=True)
        assets = []
        for portfolio in portfolios:
            for balance in portfolio.get('balances', []):
                symbol = balance.get('asset', '')
                value_usd = balance.get('value_usdt', 0) or balance.get('value_usd', 0)
                if symbol and value_usd > 0:
                    assets.append({'symbol': symbol, 'value_usd': value_usd})

        if not assets:
            return {
                "correlation_matrix": {},
                "risk_return_scatter": [],
                "efficient_frontier": [],
                "beta_analysis": {},
                "message": "No assets found for advanced analytics."
            }

        # Limit days to prevent excessive computation
        days = min(days, 90)
        
        # Limit number of assets to prevent timeout
        if len(assets) > 20:
            # Sort by value and take top 20
            assets = sorted(assets, key=lambda x: x['value_usd'], reverse=True)[:20]
            app_logger.warning(f"Advanced analytics limited to top 20 assets by value")

        asset_symbols = [a['symbol'] for a in assets]

        # Run calculations in parallel to reduce total time
        # Use asyncio to run CPU-bound tasks concurrently
        import concurrent.futures
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        
        # Submit all tasks to thread pool
        correlation_matrix_future = executor.submit(
            advanced_analytics_service.calculate_correlation_matrix, 
            asset_symbols, days
        )
        risk_return_scatter_future = executor.submit(
            advanced_analytics_service.calculate_risk_return_scatter,
            assets, days
        )
        efficient_frontier_future = executor.submit(
            advanced_analytics_service.calculate_efficient_frontier,
            assets, 30, days  # Reduced num_portfolios from 50 to 30 for speed
        )
        beta_analysis_future = executor.submit(
            advanced_analytics_service.calculate_beta_analysis,
            assets, benchmark, days
        )
        
        # Wait for all tasks with timeout
        try:
            correlation_matrix, risk_return_scatter, efficient_frontier, beta_analysis = await asyncio.wait_for(
                asyncio.gather(
                    asyncio.wrap_future(correlation_matrix_future),
                    asyncio.wrap_future(risk_return_scatter_future),
                    asyncio.wrap_future(efficient_frontier_future),
                    asyncio.wrap_future(beta_analysis_future)
                ),
                timeout=25.0  # 25 second timeout per request
            )
        except asyncio.TimeoutError:
            app_logger.warning("Advanced analytics timeout, returning partial results")
            # Return partial results if timeout
            correlation_matrix = {}
            risk_return_scatter = []
            efficient_frontier = []
            beta_analysis = {}
        finally:
            executor.shutdown(wait=False)

        return {
            "correlation_matrix": correlation_matrix,
            "risk_return_scatter": risk_return_scatter,
            "efficient_frontier": efficient_frontier,
            "beta_analysis": beta_analysis
        }
    except HTTPException:
        raise
    except Exception as e:
        error_type = type(e).__name__
        app_logger.error(f"Error getting advanced analytics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/analytics/portfolio-projection")
async def get_portfolio_projection(
    days: int = 30,
    current_user: Dict = Depends(get_current_user)
):
    """Get portfolio value projection using AI price forecasting"""
    try:
        # Get user's assets
        portfolios = portfolio_tracker.get_all_portfolios(current_user["username"], use_transactions_only=True)
        assets = []
        
        for portfolio in portfolios:
            for balance in portfolio.get('balances', []):
                symbol = balance.get('asset', '')
                # Support both live-exchange balances (amount) and manual/aggregated portfolios (total/free)
                amount = (
                    balance.get('amount')
                    or balance.get('total')
                    or balance.get('free')
                    or 0
                )
                value_usd = balance.get('value_usdt', 0) or balance.get('value_usd', 0)
                if symbol and amount > 0:
                    assets.append({
                        'symbol': symbol,
                        'amount': float(amount),
                        'value_usd': float(value_usd),
                        'asset_type': 'crypto' if portfolio.get('exchange') in ['Binance', 'Bybit'] else 'stock'
                    })
        
        if not assets:
            return {
                'projections': [],
                'total_current_value': 0,
                'total_projected_value': 0,
                'projected_change': 0,
                'message': 'No assets found'
            }
        
        # Get current portfolio value
        total_current_value = sum(a['value_usd'] for a in assets)
        
        # Get price predictions for each asset
        projections = []
        total_projected_value = 0
        
        for asset in assets:
            symbol = asset['symbol']
            amount = asset['amount']
            asset_type = asset['asset_type']
            
            try:
                prediction = ai_service.predict_price(symbol, asset_type, days)
                if prediction and prediction.get('predictions'):
                    # Use the last prediction (furthest day)
                    last_pred = prediction['predictions'][-1]
                    predicted_price = last_pred.get('predicted_price', 0)
                    
                    if predicted_price > 0:
                        projected_value = amount * predicted_price
                        current_price = asset['value_usd'] / amount if amount > 0 else 0
                        change_percent = ((predicted_price - current_price) / current_price * 100) if current_price > 0 else 0
                        
                        projections.append({
                            'symbol': symbol,
                            'current_price': current_price,
                            'predicted_price': predicted_price,
                            'current_value': asset['value_usd'],
                            'projected_value': projected_value,
                            'change_percent': change_percent,
                            'amount': amount,
                            'confidence': last_pred.get('confidence', 0.5)
                        })
                        total_projected_value += projected_value
            except Exception as e:
                app_logger.warning(f"Failed to get prediction for {symbol}: {e}")
                # Use current value as fallback
                projections.append({
                    'symbol': symbol,
                    'current_price': asset['value_usd'] / amount if amount > 0 else 0,
                    'predicted_price': asset['value_usd'] / amount if amount > 0 else 0,
                    'current_value': asset['value_usd'],
                    'projected_value': asset['value_usd'],
                    'change_percent': 0,
                    'amount': amount,
                    'confidence': 0
                })
                total_projected_value += asset['value_usd']
        
        projected_change = ((total_projected_value - total_current_value) / total_current_value * 100) if total_current_value > 0 else 0
        
        return {
            'projections': projections,
            'total_current_value': total_current_value,
            'total_projected_value': total_projected_value,
            'projected_change': projected_change,
            'days': days
        }
    except HTTPException:
        raise
    except Exception as e:
        error_type = type(e).__name__
        app_logger.error(f"Error calculating portfolio projection: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/analytics/portfolio-flow")
async def get_portfolio_flow(current_user: Dict = Depends(get_current_user)):
    """Get portfolio flow data for Sankey diagram (exchange -> asset)"""
    try:
        portfolios = portfolio_tracker.get_all_portfolios(current_user["username"], use_transactions_only=True)
        
        # Build exchange and asset data
        exchanges = []
        assets = []
        exchange_map = {}
        
        for portfolio in portfolios:
            exchange = portfolio.get('exchange', '')
            total_value = portfolio.get('total_value_usdt', 0)
            
            if exchange and total_value > 0:
                if exchange not in exchange_map:
                    exchange_map[exchange] = {
                        'name': exchange,
                        'total_value': 0
                    }
                exchange_map[exchange]['total_value'] += total_value
            
            for balance in portfolio.get('balances', []):
                asset_symbol = balance.get('asset', '')
                value = balance.get('value_usdt', 0)
                
                if asset_symbol and value > 0:
                    assets.append({
                        'symbol': asset_symbol,
                        'value_usd': value,
                        'exchange': exchange,
                        'amount': balance.get('free', 0)
                    })
        
        exchanges = list(exchange_map.values())
        
        return {
            'exchanges': exchanges,
            'assets': assets
        }
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/insights")
async def get_smart_insights(current_user: Dict = Depends(get_current_user)):
    """Get smart portfolio insights, alerts, and recommendations"""
    try:
        start_ts = time.time()
        max_seconds = float(os.getenv("SMART_INSIGHTS_MAX_SECONDS", "10.0"))
        
        # Helper to check budget and return minimal data if exceeded
        def check_budget_and_return_minimal(portfolios=None) -> Optional[Dict]:
            elapsed = time.time() - start_ts
            if elapsed > max_seconds:
                app_logger.warning(f"Smart insights exceeded budget ({max_seconds}s) after {elapsed:.2f}s, returning minimal data")
                total_value = sum(p.get('total_value_usdt', 0) for p in portfolios) if portfolios else 0
                return {
                    "insights": [],
                    "alerts": [],
                    "recommendations": [],
                    "health_score": 50,
                    "risk_level": "Unknown",
                    "total_value": total_value,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            return None
        
        # Check budget BEFORE expensive operations
        minimal = check_budget_and_return_minimal()
        if minimal:
            return minimal
        
        # Get portfolio data
        portfolios = portfolio_tracker.get_all_portfolios(current_user["username"], use_transactions_only=True)
        
        # Check budget after get_all_portfolios
        minimal = check_budget_and_return_minimal(portfolios)
        if minimal:
            return minimal
        
        # Get transaction history
        user_id = current_user.get("username")
        all_transactions = transaction_history.get_all_transactions(user_id=user_id)
        
        # Check budget again before expensive analysis
        minimal = check_budget_and_return_minimal(portfolios)
        if minimal:
            return minimal
        
        # Generate smart insights
        insights_data = smart_insights_service.analyze_portfolio(
            portfolios=portfolios,
            transaction_history=all_transactions
        )
        
        return insights_data
    except (Timeout, ConnectionError) as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service temporarily unavailable: Unable to connect to exchange APIs. Error: {str(e)}"
        )
    except RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Bad gateway: Exchange API request failed. Error: {str(e)}"
        )
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )


@app.get("/api/insights/health-score", tags=["Insights"])
async def get_portfolio_health_score(current_user: Dict = Depends(get_current_user)):
    """
    Get portfolio health score (0-100) and risk level.
    Thin wrapper around SmartInsightsService.analyze_portfolio.
    """
    try:
        start_ts = time.time()
        max_seconds = float(os.getenv("HEALTH_SCORE_MAX_SECONDS", "8.0"))
        
        # Helper to check budget and return default if exceeded
        def check_budget_and_return_default(portfolios=None) -> Optional[Dict]:
            elapsed = time.time() - start_ts
            if elapsed > max_seconds:
                app_logger.warning(f"Health score exceeded budget ({max_seconds}s) after {elapsed:.2f}s, returning default")
                return {
                    "health_score": 50,
                    "risk_level": "Unknown",
                    "total_value": sum(p.get('total_value_usdt', 0) for p in portfolios) if portfolios else 0,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            return None
        
        # Check budget BEFORE expensive operations
        default = check_budget_and_return_default()
        if default:
            return default
        
        portfolios = portfolio_tracker.get_all_portfolios(current_user["username"], use_transactions_only=True)
        
        # Check budget after get_all_portfolios
        default = check_budget_and_return_default(portfolios)
        if default:
            return default
        
        user_id = current_user.get("username")
        all_transactions = transaction_history.get_all_transactions(user_id=user_id)

        # Check budget again before expensive analysis
        default = check_budget_and_return_default(portfolios)
        if default:
            return default

        insights_data = smart_insights_service.analyze_portfolio(
            portfolios=portfolios,
            transaction_history=all_transactions,
        )

        return {
            "health_score": insights_data.get("health_score", 0),
            "risk_level": insights_data.get("risk_level", "Unknown"),
            "total_value": insights_data.get("total_value", 0),
            "timestamp": insights_data.get("timestamp"),
        }
    except HTTPException:
        raise
    except Exception as e:
        error_type = type(e).__name__
        app_logger.error(f"Error getting portfolio health score: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/insights/risk-alerts", tags=["Insights"])
async def get_risk_alerts(
    days: int = 90,
    current_user: Dict = Depends(get_current_user)
):
    """Get real-time risk alerts for portfolio (concentration, correlation, volatility, drawdown)"""
    try:
        start_ts = time.time()
        max_seconds = float(os.getenv("RISK_ALERTS_MAX_SECONDS", "10.0"))
        
        # Helper to check budget and return empty if exceeded
        def check_budget_and_return_empty() -> Optional[Dict]:
            elapsed = time.time() - start_ts
            if elapsed > max_seconds:
                app_logger.warning(f"Risk alerts exceeded budget ({max_seconds}s) after {elapsed:.2f}s, returning empty")
                return {
                    "concentration": [],
                    "correlation": [],
                    "volatility": [],
                    "drawdown": [],
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            return None
        
        # Check budget BEFORE expensive operations
        if check_budget_and_return_empty():
            return check_budget_and_return_empty()
        
        # Get portfolio data
        portfolios = portfolio_tracker.get_all_portfolios(current_user["username"], use_transactions_only=True)
        
        # Check budget after get_all_portfolios
        empty = check_budget_and_return_empty()
        if empty:
            return empty
        
        # Detect risk alerts
        risk_alerts = smart_insights_service.detect_risk_alerts(portfolios, days)
        
        return risk_alerts
    except HTTPException:
        raise
    except Exception as e:
        error_type = type(e).__name__
        app_logger.error(f"Error detecting risk alerts: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )


@app.get("/api/insights/rebalancing-suggestions", tags=["Insights"])
async def get_rebalancing_suggestions(
    threshold: float = 5.0,
    max_suggestions: int = 5,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get automatic rebalancing suggestions based on allocation drift.

    - threshold: minimum drift in percentage points to trigger a suggestion (default 5%)
    - max_suggestions: maximum number of suggestions to return (default 5)
    """
    try:
        start_ts = time.time()
        max_seconds = float(os.getenv("REBALANCING_SUGGESTIONS_MAX_SECONDS", "8.0"))
        
        # Helper to check budget and return empty if exceeded
        def check_budget_and_return_empty() -> Optional[Dict]:
            elapsed = time.time() - start_ts
            if elapsed > max_seconds:
                app_logger.warning(f"Rebalancing suggestions exceeded budget ({max_seconds}s) after {elapsed:.2f}s, returning empty")
                return {
                    "current_allocation": {},
                    "target_allocation": {},
                    "suggestions": [],
                    "total_value": 0,
                    "threshold": threshold
                }
            return None
        
        # Check budget BEFORE expensive operations
        if check_budget_and_return_empty():
            return check_budget_and_return_empty()
        
        portfolios = portfolio_tracker.get_all_portfolios(current_user["username"], use_transactions_only=True)
        
        # Check budget after get_all_portfolios
        empty = check_budget_and_return_empty()
        if empty:
            return empty

        result = smart_insights_service.generate_rebalancing_suggestions(
            portfolios=portfolios,
            threshold=threshold,
            max_suggestions=max_suggestions,
        )

        return result
    except HTTPException:
        raise
    except Exception as e:
        error_type = type(e).__name__
        app_logger.error(f"Error generating rebalancing suggestions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/analytics/allocation")
async def get_allocation_analytics(current_user: Dict = Depends(get_current_user)):
    """Get portfolio allocation analytics"""
    try:
        portfolios = portfolio_tracker.get_all_portfolios(current_user["username"], use_transactions_only=True)
        
        # Calculate allocation by exchange
        by_exchange = {}
        by_asset = {}
        
        for portfolio in portfolios:
            exchange = portfolio.get('exchange', '')
            total_value = portfolio.get('total_value_usdt', 0)
            
            if total_value > 0:
                by_exchange[exchange] = total_value
                
                for balance in portfolio.get('balances', []):
                    asset = balance.get('asset', '')
                    value = balance.get('value_usdt', 0)
                    if value > 0:
                        by_asset[asset] = by_asset.get(asset, 0) + value
        
        # Calculate allocation by type (crypto vs stocks)
        by_type = {"Crypto": 0.0, "Stocks": 0.0}
        for portfolio in portfolios:
            exchange = portfolio.get('exchange', '')
            total_value = portfolio.get('total_value_usdt', 0)
            
            if total_value > 0:
                # Classify by exchange name
                if exchange.lower() in ['binance', 'bybit', 'coinbase', 'kraken']:
                    by_type["Crypto"] += total_value
                elif exchange.lower() in ['xtb', 'interactive brokers', 'robinhood']:
                    by_type["Stocks"] += total_value
        
        # Convert to percentages
        total_value = sum(by_exchange.values())
        if total_value > 0:
            by_exchange = {k: (v / total_value) * 100 for k, v in by_exchange.items()}
            by_asset = {k: (v / total_value) * 100 for k, v in by_asset.items()}
            by_type = {k: (v / total_value) * 100 for k, v in by_type.items()}
        
        return {
            "by_asset": by_asset,
            "by_exchange": by_exchange,
            "by_type": by_type
        }
    except (Timeout, ConnectionError) as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service temporarily unavailable: Unable to connect to exchange APIs. Error: {str(e)}"
        )
    except RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Bad gateway: Exchange API request failed. Error: {str(e)}"
        )
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/portfolio/history")
async def get_portfolio_history(
    days: int = 30,
    lite: bool = False,
    current_user: Dict = Depends(get_current_user)
):
    """Get portfolio performance history"""
    start_ts = time.time()
    max_seconds = float(os.getenv("PORTFOLIO_HISTORY_MAX_SECONDS", "10.0"))  # Increased from 5s to 10s
    user_id = current_user.get("username")
    
    try:
        # Get historical data from portfolio_history with error handling
        try:
            app_logger.debug(f"Fetching portfolio history for user: {user_id}, days: {days}")
            history_data = portfolio_history.get_chart_data(days=days, user_id=user_id)
            app_logger.debug(f"Got {len(history_data)} history entries for user: {user_id}")
        except Exception as e:
            app_logger.error(f"Error fetching portfolio history for user {user_id}: {e}", exc_info=True)
            # Return empty list instead of crashing
            return []
        
        # Enforce time budget early
        if time.time() - start_ts > max_seconds:
            app_logger.warning(f"Portfolio history exceeded budget ({max_seconds}s) for user {user_id}, returning empty")
            return []
        
        # Convert to API format with error handling
        history_points = []
        for entry in history_data:
            try:
                history_points.append({
                    "date": entry.get('timestamp', ''),
                    "value_usd": entry.get('value_usd', 0),
                    "value_pln": entry.get('value_pln', 0),
                    "total_assets": 0,  # Not available in portfolio_history
                    "active_exchanges": 0  # Not available in portfolio_history
                })
            except Exception as e:
                app_logger.warning(f"Error converting history entry for user {user_id}: {e}")
                continue  # Skip this entry but continue with others
        
        # Lite mode for mobile: return every 5th point to reduce payload
        if lite and len(history_points) > 10:
            history_points = history_points[::5]
        
        app_logger.debug(f"Returning {len(history_points)} history points for user: {user_id}")
        return history_points
    except (Timeout, ConnectionError) as e:
        app_logger.error(f"Network error in get_portfolio_history for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"Service temporarily unavailable: Unable to connect to exchange APIs. Error: {str(e)}"
        )
    except RequestException as e:
        app_logger.error(f"Request error in get_portfolio_history for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=502,
            detail=f"Bad gateway: Exchange API request failed. Error: {str(e)}"
        )
    except Exception as e:
        error_type = type(e).__name__
        app_logger.error(f"Unexpected error in get_portfolio_history for user {user_id}: {e}", exc_info=True)
        # Return empty list instead of crashing
        return []

@app.get("/api/reports/tax-pdf")
async def generate_tax_report_pdf(year: int = None, current_user: Dict = Depends(get_current_user)):
    """Generate tax report PDF for specified year"""
    try:
        # Get current year if not specified
        if year is None:
            from datetime import datetime
            year = datetime.now().year
        
        # Get all transactions
        user_id = current_user.get("username")
        all_transactions = transaction_history.get_all_transactions(user_id=user_id)
        
        # Filter transactions for the specified year
        transactions_for_year = [
            t for t in all_transactions 
            if t.get('date', '')[:4] == str(year)
        ]
        
        # Get realized PNL for the year using transaction_history
        # For now, we'll use total realized PNL (can be enhanced to filter by year)
        realized_pnl = transaction_history.get_total_realized_pnl(user_id=user_id)
        
        # Generate PDF with realized PNL
        pdf_bytes = pdf_generator.generate_tax_report_pdf(year, transactions_for_year, realized_pnl)
        
        return StreamingResponse(
            pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="tax_report_{year}.pdf"'
            }
        )
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/reports/portfolio-pdf")
async def generate_portfolio_summary_pdf(current_user: Dict = Depends(get_current_user)):
    """Generate portfolio summary PDF"""
    try:
        portfolios = portfolio_tracker.get_all_portfolios(current_user["username"], use_transactions_only=True)
        
        # Calculate portfolio summary
        total_value_usd = sum(p.get('total_value_usdt', 0) for p in portfolios)
        
        # Calculate exchange allocation
        exchange_data = {}
        for portfolio in portfolios:
            exchange = portfolio.get('exchange', 'Unknown')
            value = portfolio.get('total_value_usdt', 0)
            if exchange not in exchange_data:
                exchange_data[exchange] = {'value': 0, 'percentage': 0}
            exchange_data[exchange]['value'] += value
        
        # Calculate percentages
        if total_value_usd > 0:
            for exchange in exchange_data:
                exchange_data[exchange]['percentage'] = (exchange_data[exchange]['value'] / total_value_usd) * 100
        
        portfolio_data = {
            'total_value_usd': total_value_usd,
            'exchanges': exchange_data
        }
        
        # Generate PDF
        pdf_bytes = pdf_generator.generate_portfolio_summary_pdf(portfolio_data)
        
        from datetime import datetime
        date_str = datetime.now().strftime('%Y%m%d')
        
        return StreamingResponse(
            pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="portfolio_summary_{date_str}.pdf"'
            }
        )
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

# Settings API endpoints
class ApiKeysUpdate(BaseModel):
    api_key: Optional[str] = None
    secret_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None

class AppSettingsUpdate(BaseModel):
    cache_enabled: Optional[bool] = None
    auto_refresh_enabled: Optional[bool] = None
    refresh_interval: Optional[int] = None
    theme: Optional[str] = None
    currency: Optional[str] = None

@app.get("/api/settings/api-keys")
async def get_api_keys_status(current_user: Dict = Depends(get_current_user)):
    """Get status of API keys (masked)"""
    try:
        status = settings_manager.get_api_keys_status(current_user["username"])
        return status
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.put("/api/settings/api-keys/{exchange}")
async def update_api_keys(exchange: str, keys: ApiKeysUpdate, current_user: Dict = Depends(get_current_user)):
    """Update API keys for a specific exchange"""
    try:
        success = settings_manager.update_api_keys(
            username=current_user["username"],
            exchange=exchange,
            api_key=keys.api_key,
            secret_key=keys.secret_key,
            username_field=keys.username,
            password=keys.password
        )
        if success:
            return {"success": True, "message": f"{exchange} API keys updated successfully"}
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to update API keys"
            )
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.post("/api/settings/test-connection/{exchange}")
async def test_exchange_connection(exchange: str, current_user: Dict = Depends(get_current_user)):
    """Test connection to exchange API"""
    try:
        result = settings_manager.test_connection(current_user["username"], exchange)
        if result.get("success"):
            return result
        return {
            "success": False,
            "error": result.get("error", "Connection test failed"),
        }
    except HTTPException:
        raise
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/settings/app")
async def get_app_settings(current_user: Dict = Depends(get_current_user)):
    """Get application settings"""
    try:
        settings = settings_manager.get_app_settings()
        return settings
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.put("/api/settings/app")
async def update_app_settings(settings: AppSettingsUpdate, current_user: Dict = Depends(get_current_user)):
    """Update application settings"""
    try:
        settings_dict = settings.dict(exclude_unset=True)
        success = settings_manager.update_app_settings(settings_dict)
        if success:
            return {"success": True, "message": "Settings updated successfully"}
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to update settings"
            )
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.post("/api/settings/clear-cache")
async def clear_cache(current_user: Dict = Depends(get_current_user)):
    """Clear application cache"""
    try:
        # Clear cache in portfolio service (frontend will handle this via portfolioService)
        return {"success": True, "message": "Cache cleared successfully"}
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

# Authentication endpoints
class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

@app.post("/api/auth/register", response_model=Dict[str, Any])
@limiter.limit("5/minute")  # Max 5 registrations per minute per IP
async def register(request: Request, user_data: UserRegister):
    """Register a new user"""
    try:
        # Validate input
        if len(user_data.username) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username must be at least 3 characters long"
            )
        if len(user_data.password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters long"
            )
        
        user = auth_manager.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password
        )
        
        return {
            "success": True,
            "message": "User registered successfully",
            "user": user
        }
    except HTTPException:
        raise
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.post("/api/auth/login", response_model=TokenResponse)
@limiter.limit("10/minute")  # Max 10 login attempts per minute per IP (brute force protection)
async def login(request: Request, user_data: UserLogin):
    """Login user and return JWT token"""
    try:
        user = auth_manager.authenticate_user(
            username=user_data.username,
            password=user_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = auth_manager.create_access_token(username=user["username"])
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=user
        )
    except HTTPException:
        raise
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/auth/me")
async def get_current_user_info(current_user: Dict = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@app.post("/api/auth/logout")
async def logout():
    """Logout user (client-side token removal)"""
    return {"success": True, "message": "Logged out successfully"}

# Goals API Endpoints
@app.get("/api/goals")
async def get_goals(current_user: Dict = Depends(get_current_user)):
    """Get all goals for current user"""
    start_ts = time.time()
    max_seconds = float(os.getenv("GOALS_MAX_SECONDS", "10.0"))
    
    try:
        user_id = current_user.get("username", "default")
        goals = goal_tracking_service.get_user_goals(user_id)
        
        # Check budget before expensive operation
        if time.time() - start_ts > max_seconds:
            app_logger.warning(f"Goals exceeded budget ({max_seconds}s), returning goals without progress update")
            return goals
        
        # Update progress for each goal
        portfolio_summary = await get_portfolio_summary(current_user)
        current_value = portfolio_summary.total_value_usd
        
        # Check budget again after portfolio summary
        if time.time() - start_ts > max_seconds:
            app_logger.warning(f"Goals exceeded budget ({max_seconds}s) after portfolio summary, returning goals without progress update")
            return goals
        
        updated_goals = []
        for goal in goals:
            # Check budget during loop
            if time.time() - start_ts > max_seconds:
                app_logger.warning(f"Goals exceeded budget ({max_seconds}s) during progress update, returning partial results")
                break
                
            updated_goal = goal_tracking_service.update_goal_progress(
                goal["id"], user_id, current_value
            )
            if updated_goal:
                updated_goals.append(updated_goal)
        
        return updated_goals if updated_goals else goals
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.post("/api/goals")
async def create_goal(goal_data: CreateGoal, current_user: Dict = Depends(get_current_user)):
    """Create a new goal"""
    try:
        user_id = current_user.get("username", "default")
        
        # Get current portfolio value
        portfolio_summary = await get_portfolio_summary(current_user)
        start_value = portfolio_summary.total_value_usd
        
        goal_dict = goal_data.dict()
        goal_dict["start_value"] = start_value
        
        goal = goal_tracking_service.create_goal(user_id, goal_dict)
        return goal
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.put("/api/goals/{goal_id}")
async def update_goal(goal_id: int, goal_data: UpdateGoal, current_user: Dict = Depends(get_current_user)):
    """Update a goal"""
    try:
        user_id = current_user.get("username", "default")
        updates = {k: v for k, v in goal_data.dict().items() if v is not None}
        
        goal = goal_tracking_service.update_goal(goal_id, user_id, updates)
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        return goal
    except HTTPException:
        raise
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.delete("/api/goals/{goal_id}")
async def delete_goal(goal_id: int, current_user: Dict = Depends(get_current_user)):
    """Delete (cancel) a goal"""
    try:
        user_id = current_user.get("username", "default")
        success = goal_tracking_service.delete_goal(goal_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        return {"success": True, "message": "Goal deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/goals/{goal_id}/projections")
async def get_goal_projections(goal_id: int, current_user: Dict = Depends(get_current_user)):
    """Get projections for goal completion"""
    try:
        user_id = current_user.get("username", "default")
        goal = goal_tracking_service.get_goal(goal_id, user_id)
        
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        portfolio_summary = await get_portfolio_summary(current_user)
        current_value = portfolio_summary.total_value_usd
        
        projections = goal_tracking_service.get_projections(goal, current_value)
        return projections
    except HTTPException:
        raise
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

# Tax Optimization API Endpoints
@app.get("/api/tax/calculation")
async def get_tax_calculation(year: int = None, current_user: Dict = Depends(get_current_user)):
    """Calculate tax for specified year"""
    try:
        if year is None:
            year = datetime.now().year
        
        # Get transactions for the year
        user_id = current_user.get("username")
        all_transactions = transaction_history.get_all_transactions(user_id=user_id)
        year_transactions = [
            t for t in all_transactions
            if t.get('date', '')[:4] == str(year)
        ]
        
        # Calculate realized gains/losses
        realized_pnl = transaction_history.get_total_realized_pnl(user_id=user_id)
        
        # Get current exchange rate
        exchange_rate = exchange_rate_service.get_current_rate()
        
        # Calculate tax
        tax_calculation = tax_optimization_service.calculate_tax(
            realized_gains=max(0, realized_pnl) if realized_pnl > 0 else 0,
            realized_losses=abs(min(0, realized_pnl)) if realized_pnl < 0 else 0,
            exchange_rate=exchange_rate
        )
        
        return tax_calculation
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/tax/suggestions")
async def get_tax_loss_harvesting_suggestions(current_user: Dict = Depends(get_current_user)):
    """Get tax-loss harvesting suggestions"""
    try:
        user_id = current_user.get("username")
        all_transactions = transaction_history.get_all_transactions(user_id=user_id)
        realized_pnl = transaction_history.get_total_realized_pnl(user_id=user_id)
        current_gains = max(0, realized_pnl) if realized_pnl > 0 else 0
        
        exchange_rate = exchange_rate_service.get_current_rate()
        
        suggestions = tax_optimization_service.suggest_tax_loss_harvesting(
            all_transactions,
            current_gains,
            exchange_rate
        )
        
        return {"suggestions": suggestions}
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/tax/deadline")
async def get_tax_deadline_info(current_user: Dict = Depends(get_current_user)):
    """Get tax deadline information"""
    try:
        deadline_info = tax_optimization_service.get_tax_deadline_info()
        return deadline_info
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.post("/api/tax/scenario")
async def calculate_tax_scenario(
    request: Request,
    current_user: Dict = Depends(get_current_user)
):
    """Calculate tax scenario with additional losses"""
    try:
        from fastapi import Query
        
        # Get additional_losses from query parameter
        additional_losses = float(request.query_params.get('additional_losses', 0))
        
        user_id = current_user.get("username")
        realized_pnl = transaction_history.get_total_realized_pnl(user_id=user_id)
        current_gains = max(0, realized_pnl) if realized_pnl > 0 else 0
        current_losses = abs(min(0, realized_pnl)) if realized_pnl < 0 else 0
        
        exchange_rate = exchange_rate_service.get_current_rate()
        
        scenario = tax_optimization_service.calculate_scenario(
            current_gains,
            current_losses,
            additional_losses,
            exchange_rate
        )
        
        return scenario
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

# Price Alerts API
class CreatePriceAlert(BaseModel):
    symbol: str
    condition: str  # 'above', 'below', 'rsi_above', 'rsi_below', 'volume_spike', 'dd_score_below'
    price: Optional[float] = None  # Required for price conditions
    name: Optional[str] = None
    # Advanced conditions
    rsi_threshold: Optional[float] = None  # For RSI conditions (0-100)
    volume_spike_percent: Optional[float] = None  # For volume spike (e.g., 200 = 200% of 7d average)
    dd_score_threshold: Optional[float] = None  # For DD score conditions (0-100)

class UpdatePriceAlert(BaseModel):
    condition: Optional[str] = None
    price: Optional[float] = None
    active: Optional[bool] = None

@app.get("/api/price-alerts")
async def get_price_alerts(current_user: Dict = Depends(get_current_user)):
    """Get all price alerts for current user"""
    try:
        user_id = current_user.get("username", "default")
        alerts = price_alert_service.get_alerts(user_id)
        return alerts
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.post("/api/price-alerts")
async def create_price_alert(
    alert_data: CreatePriceAlert,
    current_user: Dict = Depends(get_current_user)
):
    """Create a new price alert"""
    try:
        user_id = current_user.get("username", "default")
        alert = price_alert_service.create_alert(
            user_id=user_id,
            symbol=alert_data.symbol,
            condition=alert_data.condition,
            price=alert_data.price,
            name=alert_data.name,
            rsi_threshold=alert_data.rsi_threshold,
            volume_spike_percent=alert_data.volume_spike_percent,
            dd_score_threshold=alert_data.dd_score_threshold
        )
        return alert
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.put("/api/price-alerts/{alert_id}")
async def update_price_alert(
    alert_id: int,
    alert_data: UpdatePriceAlert,
    current_user: Dict = Depends(get_current_user)
):
    """Update a price alert"""
    try:
        user_id = current_user.get("username", "default")
        alert = price_alert_service.update_alert(
            user_id=user_id,
            alert_id=alert_id,
            condition=alert_data.condition,
            price=alert_data.price,
            active=alert_data.active
        )
        return alert
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.delete("/api/price-alerts/{alert_id}")
async def delete_price_alert(
    alert_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Delete a price alert"""
    try:
        user_id = current_user.get("username", "default")
        success = price_alert_service.delete_alert(user_id, alert_id)
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        return {"success": True, "message": "Alert deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

# Alert Templates
ALERT_TEMPLATES = {
    "breakout_above": {
        "name": "Breakout Above",
        "description": "Alert when price breaks above a resistance level",
        "condition": "above",
        "default_price_offset_percent": 5.0
    },
    "breakout_below": {
        "name": "Breakout Below",
        "description": "Alert when price breaks below a support level",
        "condition": "below",
        "default_price_offset_percent": -5.0
    },
    "rsi_overbought": {
        "name": "RSI Overbought",
        "description": "Alert when RSI exceeds 70 (overbought condition)",
        "condition": "rsi_above",
        "default_rsi_threshold": 70.0
    },
    "rsi_oversold": {
        "name": "RSI Oversold",
        "description": "Alert when RSI falls below 30 (oversold condition)",
        "condition": "rsi_below",
        "default_rsi_threshold": 30.0
    },
    "volume_spike": {
        "name": "Volume Spike",
        "description": "Alert when 24h volume exceeds 200% of 7-day average",
        "condition": "volume_spike",
        "default_volume_spike_percent": 200.0
    },
    "dd_score_drop": {
        "name": "DD Score Drop",
        "description": "Alert when Due Diligence score drops below 50",
        "condition": "dd_score_below",
        "default_dd_score_threshold": 50.0
    },
    "reversal_up": {
        "name": "Reversal Up",
        "description": "Alert when RSI oversold and price starts recovering",
        "condition": "rsi_below",
        "default_rsi_threshold": 30.0,
        "note": "Combined with price recovery pattern"
    },
    "reversal_down": {
        "name": "Reversal Down",
        "description": "Alert when RSI overbought and price starts declining",
        "condition": "rsi_above",
        "default_rsi_threshold": 70.0,
        "note": "Combined with price decline pattern"
    }
}

@app.get("/api/alerts/templates")
async def get_alert_templates(current_user: Dict = Depends(get_current_user)):
    """Get available alert templates"""
    return {"templates": ALERT_TEMPLATES}

class CreateAlertFromTemplate(BaseModel):
    symbol: str
    template_id: str
    price: Optional[float] = None  # Base price for price-based templates
    customizations: Optional[Dict[str, Any]] = None  # Override template defaults

@app.post("/api/alerts/from-template")
async def create_alert_from_template(
    request: CreateAlertFromTemplate,
    current_user: Dict = Depends(get_current_user)
):
    """Create an alert from a template"""
    try:
        template = ALERT_TEMPLATES.get(request.template_id)
        if not template:
            raise HTTPException(status_code=400, detail=f"Template {request.template_id} not found")
        
        user_id = current_user.get("username", "default")
        
        # Build alert data from template
        alert_data = {
            "symbol": request.symbol,
            "condition": template["condition"],
            "name": f"{request.symbol} {template['name']}"
        }
        
        # Apply template defaults and customizations
        if template["condition"] in ["above", "below"]:
            if request.price is None:
                # Get current price
                price_data = market_data_service.get_price(request.symbol, priority='normal')
                if not price_data:
                    raise HTTPException(status_code=400, detail=f"Could not fetch price for {request.symbol}")
                base_price = price_data.get("price", 0)
            else:
                base_price = request.price
            
            offset_percent = request.customizations.get("price_offset_percent", template.get("default_price_offset_percent", 0)) if request.customizations else template.get("default_price_offset_percent", 0)
            alert_data["price"] = base_price * (1 + offset_percent / 100)
        
        if template["condition"] in ["rsi_above", "rsi_below"]:
            alert_data["rsi_threshold"] = request.customizations.get("rsi_threshold", template.get("default_rsi_threshold")) if request.customizations else template.get("default_rsi_threshold")
        
        if template["condition"] == "volume_spike":
            alert_data["volume_spike_percent"] = request.customizations.get("volume_spike_percent", template.get("default_volume_spike_percent")) if request.customizations else template.get("default_volume_spike_percent")
        
        if template["condition"] == "dd_score_below":
            alert_data["dd_score_threshold"] = request.customizations.get("dd_score_threshold", template.get("default_dd_score_threshold")) if request.customizations else template.get("default_dd_score_threshold")
        
        # Create alert
        alert = price_alert_service.create_alert(
            user_id=user_id,
            symbol=alert_data["symbol"],
            condition=alert_data["condition"],
            price=alert_data.get("price"),
            name=alert_data.get("name"),
            rsi_threshold=alert_data.get("rsi_threshold"),
            volume_spike_percent=alert_data.get("volume_spike_percent"),
            dd_score_threshold=alert_data.get("dd_score_threshold")
        )
        
        return alert
    except HTTPException:
        raise
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/price-alerts/check")
async def check_price_alerts(current_user: Dict = Depends(get_current_user)):
    """Check if any price alerts should be triggered"""
    try:
        user_id = current_user.get("username", "default")
        alerts = price_alert_service.get_alerts(user_id)
        
        # Get symbols from alerts
        symbols = list(set([a['symbol'] for a in alerts if a['active'] and not a['triggered']]))
        
        if not symbols:
            return {"triggered": []}
        
        # Get current prices
        current_prices = {}
        for symbol in symbols:
            price_data = market_data_service.get_price(symbol, priority='normal')
            if price_data:
                current_prices[symbol] = price_data['price']
        
        # Check alerts
        triggered = price_alert_service.check_alerts(user_id, current_prices)
        return {"triggered": triggered}
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

# Market Data API
@app.get("/api/market/watchlist")
async def get_watchlist_prices(
    symbols: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Get prices for watchlist symbols (legacy endpoint, max 4 symbols for SSE compatibility)"""
    try:
        market_watchlist_requests.inc()
        default_stock_symbols = ["AAPL", "MSFT", "TSLA", "GOOGL"]
        if symbols:
            symbol_list = [s.strip().upper() for s in symbols.split(',')]
        else:
            # Default to user's saved watchlist
            username = current_user.get("username", "default")
            user_symbols = watchlist_service.get_watchlist(username)
            symbol_list = user_symbols[:10] if user_symbols else default_stock_symbols
        
        # Dedup and cap to 4 symbols to respect provider limits
        symbol_list = list(dict.fromkeys([s.upper() for s in symbol_list]))[:4]
        prices = market_data_service.get_watchlist_prices(symbol_list)
        # If no prices returned (e.g., rate limit or unknown symbols), try default stocks
        if not prices:
            prices = market_data_service.get_watchlist_prices(default_stock_symbols)
        return {"prices": prices, "count": len(prices)}
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/market/watchlist/batch")
async def get_watchlist_prices_batch(
    symbols: Optional[str] = None,
    limit: int = 50,
    include_dd_scores: bool = False,
    current_user: Dict = Depends(get_current_user)
):
    """Get prices for watchlist symbols in batch (supports up to 50 symbols for large watchlists).
    Set include_dd_scores=true to include Due Diligence 360° scores."""
    try:
        market_watchlist_requests.inc()
        default_stock_symbols = ["AAPL", "MSFT", "TSLA", "GOOGL"]
        if symbols:
            symbol_list = [s.strip().upper() for s in symbols.split(',')]
        else:
            # Default to user's saved watchlist
            username = current_user.get("username", "default")
            user_symbols = watchlist_service.get_watchlist(username)
            symbol_list = user_symbols if user_symbols else default_stock_symbols
        
        # Dedup and cap to limit
        symbol_list = list(dict.fromkeys([s.upper() for s in symbol_list]))[:min(limit, 50)]
        prices = market_data_service.get_watchlist_prices(symbol_list)
        # If no prices returned (e.g., rate limit or unknown symbols), try default stocks
        if not prices:
            prices = market_data_service.get_watchlist_prices(default_stock_symbols)
        
        # Optionally fetch DD scores
        dd_scores = {}
        if include_dd_scores:
            for price_item in prices:
                symbol = price_item.get('symbol', '').upper()
                if symbol:
                    try:
                        dd_result = due_diligence_service.evaluate(symbol, force_refresh=False)
                        if dd_result and dd_result.normalized_score is not None:
                            dd_scores[symbol] = {
                                "score": dd_result.normalized_score,
                                "verdict": dd_result.verdict,
                                "confidence": dd_result.confidence,
                                "cached_at": dd_result.cached_at.isoformat() if dd_result.cached_at else None
                            }
                    except Exception as e:
                        logger.warning(f"Failed to fetch DD score for {symbol}: {e}")
                        # Continue with other symbols
        
        result = {"prices": prices, "count": len(prices), "requested": len(symbol_list)}
        if include_dd_scores:
            result["dd_scores"] = dd_scores
        return result
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get('/metrics')
async def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

# Lightweight telemetry endpoint for UI interactions
class TrackEvent(BaseModel):
    event: str

@app.post('/api/metrics/track')
async def track_ui_event(payload: TrackEvent, current_user: Dict = Depends(get_current_user)):
    try:
        event_name = (payload.event or '').strip().lower()
        if not event_name:
            raise HTTPException(status_code=400, detail='Missing event')
        # Optionally, restrict to known events
        ui_interactions.labels(event=event_name).inc()
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# AI/ML Endpoints
@app.get("/api/ai/predictions", tags=["AI/ML"])
async def get_ai_predictions(
    symbol: str,
    asset_type: str = "crypto",
    days_ahead: int = 7,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get AI-powered price predictions for an asset using Prophet time series forecasting.
    
    Uses Facebook Prophet for accurate price forecasting with confidence intervals.
    Falls back to statistical models if insufficient historical data is available.
    
    **Authentication Required:** Yes
    
    **Parameters:**
    - `symbol`: Asset symbol (e.g., 'BTC', 'ETH', 'AAPL')
    - `asset_type`: Type of asset ('crypto' or 'stock')
    - `days_ahead`: Number of days to predict ahead (default: 7, max: 30)
    
    **Returns:**
    - Predicted prices with confidence intervals
    - Model used (Prophet or mock)
    - Historical data period used for training
    """
    try:
        predictions = ai_service.predict_price(symbol, asset_type, days_ahead)
        return predictions
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/ai/recommendations/enhanced", tags=["AI/ML"])
async def get_enhanced_recommendations(
    risk_tolerance: str = "moderate",
    time_horizon: str = "long_term",
    include_rebalancing: bool = True,
    include_tax_loss: bool = True,
    current_user: Dict = Depends(get_current_user)
):
    """Get enhanced AI recommendations with rebalancing calculator and tax-loss harvesting"""
    try:
        # Get user's current portfolio
        portfolios = portfolio_tracker.get_all_portfolios(current_user["username"], use_transactions_only=True)
        
        # Calculate current allocation
        total_value = 0
        current_allocation = {}
        asset_details = {}
        
        for portfolio in portfolios:
            for balance in portfolio.get('balances', []):
                symbol = balance.get('asset', '')
                value_usd = balance.get('value_usdt', 0) or balance.get('value_usd', 0)
                amount = balance.get('amount', 0)
                if symbol and value_usd > 0:
                    total_value += value_usd
                    current_allocation[symbol] = current_allocation.get(symbol, 0) + value_usd
                    if symbol not in asset_details:
                        asset_details[symbol] = {
                            'amount': 0,
                            'average_price': 0,
                            'current_price': 0
                        }
                    asset_details[symbol]['amount'] += amount
                    asset_details[symbol]['current_price'] = value_usd / amount if amount > 0 else 0
        
        # Normalize allocation to percentages
        if total_value > 0:
            current_allocation = {k: (v / total_value * 100) for k, v in current_allocation.items()}
        
        # Get base AI recommendations
        base_recommendations = ai_service.recommend_rebalance(
            current_allocation,
            current_allocation,  # Use current as target for now
            0.05  # 5% threshold
        )
        
        recommendations = {
            'base_recommendations': base_recommendations,
            'current_allocation': current_allocation,
            'total_value': total_value,
            'rebalancing_suggestions': [],
            'tax_loss_opportunities': []
        }
        
        # Add rebalancing calculator suggestions
        if include_rebalancing and base_recommendations:
            rebalancing_suggestions = []
            for rec in base_recommendations.get('recommendations', []):
                symbol = rec.get('symbol', '')
                action = rec.get('action', '')
                signal_strength = rec.get('signal_strength', 0)
                
                if symbol in asset_details:
                    current_pct = current_allocation.get(symbol, 0)
                    current_value = current_allocation.get(symbol, 0) * total_value / 100
                    
                    # Calculate suggested adjustment
                    if action == 'buy' and signal_strength > 30:
                        # Suggest increasing allocation by 2-5% based on signal strength
                        target_pct = min(100, current_pct + (signal_strength / 100 * 5))
                        adjustment_pct = target_pct - current_pct
                        adjustment_value = adjustment_pct * total_value / 100
                        
                        rebalancing_suggestions.append({
                            'symbol': symbol,
                            'action': 'increase',
                            'current_allocation': round(current_pct, 2),
                            'target_allocation': round(target_pct, 2),
                            'adjustment_value': round(adjustment_value, 2),
                            'adjustment_percent': round(adjustment_pct, 2),
                            'reason': f'Strong buy signal (strength: {signal_strength})',
                            'confidence': rec.get('confidence', 0.5)
                        })
                    elif action == 'sell' and signal_strength < -30:
                        # Suggest decreasing allocation by 2-5% based on signal strength
                        target_pct = max(0, current_pct + (signal_strength / 100 * 5))
                        adjustment_pct = target_pct - current_pct
                        adjustment_value = adjustment_pct * total_value / 100
                        
                        rebalancing_suggestions.append({
                            'symbol': symbol,
                            'action': 'decrease',
                            'current_allocation': round(current_pct, 2),
                            'target_allocation': round(target_pct, 2),
                            'adjustment_value': round(adjustment_value, 2),
                            'adjustment_percent': round(adjustment_pct, 2),
                            'reason': f'Strong sell signal (strength: {signal_strength})',
                            'confidence': rec.get('confidence', 0.5)
                        })
            
            recommendations['rebalancing_suggestions'] = rebalancing_suggestions
        
        # Add tax-loss harvesting opportunities
        if include_tax_loss:
            tax_loss_opportunities = []
            for symbol, details in asset_details.items():
                current_price = details.get('current_price', 0)
                average_price = details.get('average_price', 0)
                
                if average_price > 0 and current_price < average_price:
                    # Asset is at a loss
                    loss_percent = ((current_price - average_price) / average_price) * 100
                    loss_value = (average_price - current_price) * details.get('amount', 0)
                    
                    if loss_percent < -5:  # At least 5% loss
                        tax_loss_opportunities.append({
                            'symbol': symbol,
                            'current_price': round(current_price, 2),
                            'average_price': round(average_price, 2),
                            'loss_percent': round(loss_percent, 2),
                            'loss_value': round(loss_value, 2),
                            'amount': details.get('amount', 0),
                            'potential_tax_savings': round(loss_value * 0.20, 2),  # Assume 20% tax rate
                            'recommendation': 'Consider selling to realize tax loss, then repurchase after 30 days (wash sale rule)'
                        })
            
            recommendations['tax_loss_opportunities'] = tax_loss_opportunities
        
        return recommendations
    except HTTPException:
        raise
    except Exception as e:
        error_type = type(e).__name__
        app_logger.error(f"Error getting enhanced recommendations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/ai/recommendations", tags=["AI/ML"])
async def get_ai_recommendations(
    risk_tolerance: str = "moderate",
    time_horizon: str = "long_term",
    current_user: Dict = Depends(get_current_user)
):
    """
    Get AI-powered portfolio rebalancing recommendations using technical indicators.
    
    Analyzes portfolio holdings using RSI, MACD, and allocation drift to suggest
    buy/sell actions for optimal rebalancing.
    
    **Authentication Required:** Yes
    
    **Parameters:**
    - `risk_tolerance`: Risk tolerance level ('conservative', 'moderate', 'aggressive')
    - `time_horizon`: Investment horizon ('short_term', 'medium_term', 'long_term')
    
    **Returns:**
    - Rebalancing recommendations with action priorities
    - Technical indicators (RSI, MACD) for each asset
    - Total rebalancing amount suggested
    """
    logger = get_logger(__name__)
    try:
        # Get current portfolio holdings
        portfolios = portfolio_tracker.get_all_portfolios(current_user["username"], use_transactions_only=True)
        total_value_usd = sum(p.get('total_value_usdt', 0) or p.get('total_value_usd', 0) for p in portfolios)
        
        # Calculate current holdings allocation
        current_holdings = {}
        for portfolio in portfolios:
            # Use 'balances' field (standard for all exchanges)
            for balance in portfolio.get('balances', []):
                symbol = balance.get('asset', '')
                if symbol:
                    value = balance.get('value_usdt', 0) or balance.get('value_usd', 0)
                    if value > 0:
                        current_holdings[symbol] = current_holdings.get(symbol, 0) + value
        
        # Normalize to percentages
        if total_value_usd > 0:
            current_holdings = {k: v / total_value_usd for k, v in current_holdings.items()}
        else:
            # If no holdings, return empty recommendations with helpful message
            logger.info("AI Recommendations: No portfolio data available")
            return {
                "recommendations": [],
                "total_rebalance_amount": 0,
                "model_used": "none",
                "status": "no_portfolio_data",
                "message": "No portfolio data available. Please add assets to your portfolio first."
            }
        
        # Get target allocation based on risk tolerance
        target_allocations = {
            "conservative": {
                "BTC": 0.10, "ETH": 0.10, "SOL": 0.05, "USDT": 0.50,
                "AAPL": 0.10, "GOOGL": 0.10, "TSLA": 0.05
            },
            "moderate": {
                "BTC": 0.20, "ETH": 0.20, "SOL": 0.10, "USDT": 0.20,
                "AAPL": 0.10, "GOOGL": 0.10, "TSLA": 0.10
            },
            "aggressive": {
                "BTC": 0.35, "ETH": 0.25, "SOL": 0.15, "USDT": 0.10,
                "AAPL": 0.05, "GOOGL": 0.05, "TSLA": 0.05
            }
        }
        target_allocation = target_allocations.get(risk_tolerance, target_allocations["moderate"])
        
        # Generate rebalancing recommendations with error handling
        try:
            # Check if market data service is available
            if not ai_service.market_data_service:
                logger.warning("AI Recommendations: Market data service not available")
                return {
                    "recommendations": [],
                    "total_rebalance_amount": 0,
                    "model_used": "none",
                    "status": "service_unavailable",
                    "message": "Market data service is not available. Please try again later."
                }
            
            logger.info(f"AI Recommendations: Generating recommendations for {len(current_holdings)} assets")
            recommendations = ai_service.recommend_rebalance(
                portfolio_holdings=current_holdings,
                target_allocation=target_allocation,
                rebalance_threshold=0.05
            )
            
            logger.info(f"AI Recommendations: Generated {len(recommendations.get('recommendations', []))} recommendations")
            return recommendations
        except Exception as rec_error:
            error_type = type(rec_error).__name__
            logger.error(f"Error in recommend_rebalance: {error_type}: {str(rec_error)}", exc_info=True)
            # Return structured error response instead of raising HTTPException
            return {
                "recommendations": [],
                "total_rebalance_amount": 0,
                "model_used": "error",
                "status": "error",
                "error": f"Failed to generate recommendations: {str(rec_error)}",
                "error_type": error_type
            }
    except Exception as e:
        error_type = type(e).__name__
        import traceback
        logger.error(f"Error in get_ai_recommendations: {error_type}: {str(e)}\n{traceback.format_exc()}")
        # Return error response instead of raising HTTPException to allow frontend to handle gracefully
        return {
            "recommendations": [],
            "total_rebalance_amount": 0,
            "model_used": "error",
            "status": "error",
            "error": f"Internal server error: {str(e)}",
            "error_type": error_type
        }

@app.post("/api/ai/recommendations/verify", tags=["AI/ML"])
async def verify_recommendation(
    recommendation_id: int,
    price_after_7d: Optional[float] = None,
    price_after_30d: Optional[float] = None,
    price_after_90d: Optional[float] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Update a recommendation with actual results after specified periods.
    
    **Authentication Required:** Yes
    
    **Parameters:**
    - `recommendation_id`: ID of the recommendation to update
    - `price_after_7d`: Price 7 days after recommendation (optional)
    - `price_after_30d`: Price 30 days after recommendation (optional)
    - `price_after_90d`: Price 90 days after recommendation (optional)
    
    **Returns:**
    - Success status and updated recommendation data
    """
    try:
        if not hasattr(ai_service, 'recommendations_history') or not ai_service.recommendations_history:
            raise HTTPException(status_code=503, detail="Recommendations history tracking not available")
        
        updated = ai_service.recommendations_history.update_result(
            recommendation_id=recommendation_id,
            price_after_7d=price_after_7d,
            price_after_30d=price_after_30d,
            price_after_90d=price_after_90d
        )
        
        if not updated:
            raise HTTPException(status_code=404, detail=f"Recommendation {recommendation_id} not found")
        
        return {
            "status": "success",
            "message": f"Recommendation {recommendation_id} updated successfully",
            "recommendation_id": recommendation_id
        }
    except HTTPException:
        raise
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/ai/recommendations/performance", tags=["AI/ML"])
async def get_recommendations_performance(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get performance statistics for all AI recommendations.
    
    **Authentication Required:** Yes
    
    **Returns:**
    - Win rate (7d, 30d, 90d)
    - Average returns
    - Signal strength vs accuracy correlation
    - Per-timeframe analysis
    - Per-indicator accuracy (if available)
    """
    try:
        if not hasattr(ai_service, 'recommendations_history') or not ai_service.recommendations_history:
            raise HTTPException(status_code=503, detail="Recommendations history tracking not available")
        
        stats = ai_service.recommendations_history.get_performance_stats()
        return stats
    except HTTPException:
        raise
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/ai/recommendations/history", tags=["AI/ML"])
async def get_recommendations_history(
    symbol: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get all historical recommendations, optionally filtered by symbol.
    
    **Authentication Required:** Yes
    
    **Parameters:**
    - `symbol`: Optional symbol to filter by (e.g., 'BTC')
    
    **Returns:**
    - List of all recommendations with their verification status
    """
    try:
        if not hasattr(ai_service, 'recommendations_history') or not ai_service.recommendations_history:
            raise HTTPException(status_code=503, detail="Recommendations history tracking not available")
        
        if symbol:
            recommendations = ai_service.recommendations_history.get_recommendations_for_symbol(symbol)
        else:
            recommendations = ai_service.recommendations_history.get_all_recommendations()
        
        return {
            "total": len(recommendations),
            "recommendations": recommendations
        }
    except HTTPException:
        raise
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

class AIBacktestRequest(BaseModel):
    """Request model for AI recommendations backtesting"""
    start_date: str
    end_date: str
    initial_capital: float
    symbols: List[str]
    strategy: str = "follow_ai"  # 'follow_ai', 'high_confidence', 'weighted_allocation', 'buy_and_hold'
    signal_threshold: float = 20.0  # For 'follow_ai' strategy

@app.post("/api/ai/backtest-recommendations", tags=["AI/ML"])
async def backtest_ai_recommendations(
    request: AIBacktestRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Backtest AI recommendations strategies on historical data.
    
    **Authentication Required:** Yes
    
    **Strategies:**
    - `follow_ai`: Buy when signal_strength > threshold, sell when < -threshold
    - `high_confidence`: Only trade when signal_strength > 50 or < -50
    - `weighted_allocation`: Allocate proportionally to signal_strength
    - `buy_and_hold`: Baseline strategy for comparison
    
    **Returns:**
    - Total return, CAGR, Sharpe ratio
    - Max drawdown, win rate
    - Equity curve (time series)
    - Trade history
    - Comparison with Buy & Hold
    """
    try:
        result = ai_service.backtest_recommendations(
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
            symbols=request.symbols,
            strategy=request.strategy,
            signal_threshold=request.signal_threshold
        )
        
        # Also run Buy & Hold for comparison if strategy is not already buy_and_hold
        if request.strategy != 'buy_and_hold':
            buy_hold_result = ai_service.backtest_recommendations(
                start_date=request.start_date,
                end_date=request.end_date,
                initial_capital=request.initial_capital,
                symbols=request.symbols,
                strategy='buy_and_hold',
                signal_threshold=0.0
            )
            
            result['buy_and_hold_comparison'] = buy_hold_result
        
        return result
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

# ========== CONFLUENCE STRATEGY ENDPOINTS ==========

class ConfluenceEntryRequest(BaseModel):
    symbol: str
    interval: str = '4h'  # '1h', '4h', '1d'
    timeframe: str = '4h'

class ConfluenceExitRequest(BaseModel):
    symbol: str
    entry_price: float
    entry_date: str
    current_price: float
    current_date: str
    interval: str = '4h'
    portfolio_value: float = 10000.0
    risk_per_trade: float = 0.02

class ConfluenceBacktestRequest(BaseModel):
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float
    interval: str = '4h'
    risk_per_trade: float = 0.02
    min_confluence_score: int = 4
    min_confidence: float = 0.7


@app.get("/api/analysis/due-diligence/{symbol}", tags=["Analysis"])
async def get_due_diligence_assessment(
    symbol: str,
    refresh: bool = False,
    current_user: Dict = Depends(get_current_user),
):
    """
    Retrieve the Due Diligence 360° assessment for the requested asset.

    Set `refresh=true` to bypass the cache and recompute the score from upstream data providers.
    """
    try:
        result = due_diligence_service.evaluate(symbol, force_refresh=refresh)
        return {"symbol": symbol.upper(), "result": result.dict()}
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}",
        )

@app.post("/api/strategy/confluence/analyze-entry", tags=["Strategy/Confluence"])
async def analyze_confluence_entry(
    request: ConfluenceEntryRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Analyze entry signals based on confluence of multiple indicators.
    
    **Authentication Required:** Yes
    
    **Returns:**
    - Entry signal (buy/sell/hold)
    - Confidence score (0-1)
    - Confluence score (0-6)
    - Entry price
    - List of confluence conditions met
    - All calculated indicators and patterns
    """
    try:
        result = confluence_strategy_service.analyze_entry_signals(
            symbol=request.symbol,
            interval=request.interval,
            timeframe=request.timeframe
        )
        return result
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.post("/api/strategy/confluence/analyze-exit", tags=["Strategy/Confluence"])
async def analyze_confluence_exit(
    request: ConfluenceExitRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Analyze exit signals with position management (SL/TP/Trailing Stop).
    
    **Authentication Required:** Yes
    
    **Returns:**
    - Exit signal (hold/sell_50%/sell_100%)
    - Exit reason
    - Stop Loss, Take Profit levels
    - Trailing Stop
    - Current return percentage
    - Risk/Reward ratio
    - Position size recommendations
    """
    try:
        result = confluence_strategy_service.analyze_exit_signals(
            symbol=request.symbol,
            entry_price=request.entry_price,
            entry_date=request.entry_date,
            current_price=request.current_price,
            current_date=request.current_date,
            interval=request.interval,
            portfolio_value=request.portfolio_value,
            risk_per_trade=request.risk_per_trade
        )
        return result
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.post("/api/strategy/confluence/backtest", tags=["Strategy/Confluence"])
async def backtest_confluence_strategy(
    request: ConfluenceBacktestRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Backtest the confluence strategy on historical data.
    
    **Authentication Required:** Yes
    
    **Returns:**
    - Total return, CAGR, Sharpe ratio
    - Max drawdown, win rate, profit factor
    - Equity curve (time series)
    - Trade history with full details
    """
    try:
        result = confluence_strategy_service.backtest_confluence_strategy(
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
            interval=request.interval,
            risk_per_trade=request.risk_per_trade,
            min_confluence_score=request.min_confluence_score,
            min_confidence=request.min_confidence
        )
        return result
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/strategy/confluence/history/{symbol}", tags=["Strategy/Confluence"])
async def get_confluence_history(
    symbol: str,
    interval: str = '4h',
    limit: int = 100,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get historical confluence signals for a symbol.
    
    **Authentication Required:** Yes
    
    **Query Parameters:**
    - interval: Data interval ('1h', '4h', '1d')
    - limit: Maximum number of signals to return
    
    **Returns:**
    - List of historical entry/exit signals
    """
    try:
        # For now, return a placeholder response
        # In the future, this could store and retrieve historical signals
        return {
            'symbol': symbol,
            'interval': interval,
            'limit': limit,
            'signals': [],
            'message': 'Historical signals not yet implemented. Use analyze-entry endpoint for current signals.'
        }
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

# ============================================================================
# Benchmark Analytics API
# ============================================================================

class BenchmarkRequest(BaseModel):
    days: Optional[int] = 365
    equity_curve: Optional[List[Dict[str, float]]] = None

@app.post("/api/benchmarks/summary", tags=["Analytics"])
async def get_benchmark_summary(
    request: BenchmarkRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Retrieve benchmark performance metrics and optional relative comparison against
    a provided equity curve.
    """
    try:
        summary = benchmark_service.get_benchmark_summary(
            days=request.days or 365,
            equity_curve=request.equity_curve
        )
        if not summary:
            raise HTTPException(status_code=404, detail="Unable to fetch benchmark data")
        return {"benchmarks": summary}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching benchmark summary: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching benchmark summary: {str(e)}")


# ============================================================================
# Fundamental Screening API Endpoints
# ============================================================================

class FundamentalAnalysisRequest(BaseModel):
    symbol: str
    exchange: Optional[str] = 'US'

class ScreeningRequest(BaseModel):
    symbols: Optional[List[str]] = None
    min_f_score: Optional[int] = 7
    max_z_score: Optional[float] = 3.0  # We want > 3.0, so this is a min threshold
    max_accrual_ratio: Optional[float] = 5.0
    auto_universe: Optional[bool] = False
    universe_index: Optional[str] = 'SP500'
    value_percentile: Optional[float] = 0.2

class UniverseRankingRequest(BaseModel):
    exchange: Optional[str] = 'US'
    index: Optional[str] = 'SP500'
    percentile: Optional[float] = 0.2

class CapitalAllocationRequest(BaseModel):
    screened_stocks: List[Dict]
    total_capital: float
    method: Optional[str] = 'equal_weights'

class RebalanceScenarioRequest(BaseModel):
    screened_stocks: List[Dict]
    total_capital: float
    max_positions_options: Optional[List[int]] = [5, 10, 20]
    strategies: Optional[List[str]] = ['equal_weight', 'momentum', 'quality']
    transaction_cost: Optional[float] = 0.001
    current_holdings: Optional[Dict[str, float]] = None

class RebalanceRequest(BaseModel):
    current_holdings: Dict[str, float]  # {symbol: current_value}
    target_allocations: List[Dict]
    rebalance_date: str
    transaction_cost_percent: Optional[float] = 0.001

@app.get("/api/fundamental/data/{symbol}", tags=["Fundamental Screening"])
async def get_fundamental_data(
    symbol: str,
    exchange: str = 'US',
    current_user: Dict = Depends(get_current_user)
):
    """
    Get fundamental financial data for a symbol.
    
    **Authentication Required:** Yes
    
    **Returns:**
    - Company name, market cap, financial metrics
    - Total assets, liabilities, net income
    - Operating cash flow, revenue, EBIT
    - Current assets, current liabilities, long-term debt
    - Book value, shares outstanding
    """
    try:
        data = fundamental_screening_service.get_fundamental_data(symbol, exchange)
        if not data:
            raise HTTPException(status_code=404, detail=f"No fundamental data available for {symbol}")
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching fundamental data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching fundamental data: {str(e)}")

@app.post("/api/fundamental/f-score", tags=["Fundamental Screening"])
async def calculate_f_score(
    request: FundamentalAnalysisRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Calculate Piotroski F-Score for a symbol.
    
    **Authentication Required:** Yes
    
    **Returns:**
    - F-Score (0-9 points)
    - Breakdown by category (Profitability, Leverage, Operating Efficiency)
    - Detailed explanation for each criterion
    - Interpretation
    """
    try:
        result = fundamental_screening_service.calculate_piotroski_f_score(
            request.symbol,
            current_data=None,  # Will fetch automatically
            previous_data=None  # Will estimate
        )
        return result
    except Exception as e:
        logger.error(f"Error calculating F-Score for {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating F-Score: {str(e)}")

@app.post("/api/fundamental/z-score", tags=["Fundamental Screening"])
async def calculate_z_score(
    request: FundamentalAnalysisRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Calculate Altman Z-Score for bankruptcy risk assessment.
    
    **Authentication Required:** Yes
    
    **Returns:**
    - Z-Score value
    - Component breakdown (A, B, C, D, E)
    - Risk level (safe/moderate/high)
    - Interpretation and recommendation
    """
    try:
        result = fundamental_screening_service.calculate_altman_z_score(
            request.symbol,
            financial_data=None  # Will fetch automatically
        )
        return result
    except Exception as e:
        logger.error(f"Error calculating Z-Score for {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating Z-Score: {str(e)}")

@app.post("/api/fundamental/magic-formula", tags=["Fundamental Screening"])
async def calculate_magic_formula(
    request: FundamentalAnalysisRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Calculate Magic Formula metrics (ROIC and EBIT/EV).
    
    **Authentication Required:** Yes
    
    **Returns:**
    - Return on Invested Capital (ROIC)
    - Earnings Yield (EBIT/EV)
    - Combined score
    - Current price, enterprise value, invested capital
    """
    try:
        result = fundamental_screening_service.calculate_magic_formula_metrics(
            request.symbol,
            current_price=None,  # Will fetch automatically
            financial_data=None  # Will fetch automatically
        )
        return result
    except Exception as e:
        logger.error(f"Error calculating Magic Formula for {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating Magic Formula: {str(e)}")

@app.post("/api/fundamental/accrual-ratio", tags=["Fundamental Screening"])
async def calculate_accrual_ratio(
    request: FundamentalAnalysisRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Calculate Accrual Ratio to detect earnings quality issues.
    
    **Authentication Required:** Yes
    
    **Returns:**
    - Accrual Ratio percentage
    - Accrual amount
    - Net income vs Operating cash flow
    - Quality flag (excellent/good/acceptable/warning/danger)
    - Interpretation and recommendation
    """
    try:
        result = fundamental_screening_service.calculate_accrual_ratio(
            request.symbol,
            financial_data=None  # Will fetch automatically
        )
        return result
    except Exception as e:
        logger.error(f"Error calculating Accrual Ratio for {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating Accrual Ratio: {str(e)}")

@app.post("/api/fundamental/screen/vq-plus", tags=["Fundamental Screening"])
async def screen_vq_plus(
    request: ScreeningRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Screen stocks using VQ+ Strategy (Value + Quality with protective filters).
    
    **Authentication Required:** Yes
    
    **Strategy Steps:**
    1. Screen for Value (low valuation - using EBIT/EV)
    2. Filter by Quality (high F-Score)
    3. Apply protective filters (Z-Score > 3.0, Accrual Ratio < threshold)
    4. Rank by combined score
    
    **Returns:**
    - List of screened stocks (ranked by combined score)
    - F-Score, Z-Score, ROIC, EBIT/EV, Accrual Ratio for each
    - Combined score and ranking
    - Market cap and current price
    - Detailed breakdown for each stock
    """
    try:
        screen_payload = fundamental_screening_service.screen_vq_plus_strategy(
            symbols=request.symbols,
            min_f_score=request.min_f_score,
            max_z_score=request.max_z_score,  # Actually min threshold (we want > 3.0)
            max_accrual_ratio=request.max_accrual_ratio,
            auto_universe=request.auto_universe,
            universe_index=request.universe_index,
            value_percentile=request.value_percentile
        )
        results = screen_payload.get('results', []) if isinstance(screen_payload, dict) else screen_payload
        return {
            'total_screened': len(results),
            'symbols_analyzed': len(request.symbols) if request.symbols else 0,
            'results': results,
            'skipped': screen_payload.get('skipped', []) if isinstance(screen_payload, dict) else [],
            'data_issues': screen_payload.get('data_issues', []) if isinstance(screen_payload, dict) else [],
            'errors': screen_payload.get('errors', []) if isinstance(screen_payload, dict) else [],
            'filters_applied': {
                'min_f_score': request.min_f_score,
                'min_z_score': request.max_z_score,  # Note: This is actually min threshold
                'max_accrual_ratio': request.max_accrual_ratio
            }
        }
    except Exception as e:
        error_type = type(e).__name__
        logger.error(f"Error screening VQ+ strategy: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

class VQPlusBacktestRequest(BaseModel):
    symbols: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    initial_capital: Optional[float] = 100000.0
    rebalance_frequency: Optional[str] = 'quarterly'  # 'quarterly' or 'yearly'
    max_positions: Optional[int] = 20
    min_f_score: Optional[int] = 7
    max_z_score: Optional[float] = 3.0
    max_accrual_ratio: Optional[float] = 5.0
    auto_universe: Optional[bool] = False
    universe_index: Optional[str] = 'SP500'
    value_percentile: Optional[float] = 0.2

@app.post("/api/fundamental/backtest/vq-plus", tags=["Fundamental Screening"])
async def backtest_vq_plus_strategy(
    request: VQPlusBacktestRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Backtest the VQ+ Strategy on historical data.
    
    **Authentication Required:** Yes
    
    **Strategy:**
    - Screens stocks using VQ+ filters (F-Score, Z-Score, Accrual Ratio)
    - Selects top N stocks by combined_score
    - Allocates equal weights to each position
    - Rebalances quarterly or yearly
    - Closes positions that fail filters
    
    **Returns:**
    - Total return, CAGR, Sharpe ratio
    - Max drawdown, win rate, profit factor
    - Equity curve (time series)
    - Trade history with full details
    - Portfolio compositions at each rebalance
    """
    try:
        result = fundamental_screening_service.backtest_vq_plus_strategy(
            symbols=request.symbols,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
            rebalance_frequency=request.rebalance_frequency,
            max_positions=request.max_positions,
            min_f_score=request.min_f_score,
            max_z_score=request.max_z_score,
            max_accrual_ratio=request.max_accrual_ratio,
            auto_universe=request.auto_universe,
            universe_index=request.universe_index,
            value_percentile=request.value_percentile
        )
        return result
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.post("/api/fundamental/full-analysis/{symbol}", tags=["Fundamental Screening"])
async def get_full_fundamental_analysis(
    symbol: str,
    exchange: str = 'US',
    current_user: Dict = Depends(get_current_user)
):
    """
    Get complete fundamental analysis for a symbol (all metrics).
    
    **Authentication Required:** Yes
    
    **Returns:**
    - Fundamental data
    - F-Score with breakdown
    - Z-Score with risk assessment
    - Magic Formula metrics
    - Accrual Ratio with quality assessment
    - Overall recommendation
    """
    try:
        # Get all metrics
        fundamental_data = fundamental_screening_service.get_fundamental_data(symbol, exchange)
        f_score = fundamental_screening_service.calculate_piotroski_f_score(symbol, fundamental_data)
        z_score = fundamental_screening_service.calculate_altman_z_score(symbol, fundamental_data)
        magic_formula = fundamental_screening_service.calculate_magic_formula_metrics(symbol, financial_data=fundamental_data)
        accrual = fundamental_screening_service.calculate_accrual_ratio(symbol, fundamental_data)
        
        # Determine overall recommendation
        passes_filters = (
            f_score.get('score', 0) >= 7 and
            z_score.get('z_score', 0) > 3.0 and
            accrual.get('accrual_ratio', 999) < 5.0
        )
        
        return {
            'symbol': symbol,
            'fundamental_data': fundamental_data,
            'f_score': f_score,
            'z_score': z_score,
            'magic_formula': magic_formula,
            'accrual_ratio': accrual,
            'overall_recommendation': 'STRONG BUY' if passes_filters else 'REVIEW',
            'passes_vq_plus_filters': passes_filters,
            'summary': {
                'f_score_value': f_score.get('score', 0),
                'z_score_value': z_score.get('z_score', 0),
                'z_score_risk': z_score.get('risk_level', 'unknown'),
                'roic': magic_formula.get('roic', 0),
                'ebit_ev': magic_formula.get('ebit_ev', 0),
                'accrual_ratio_value': accrual.get('accrual_ratio', 0),
                'accrual_quality': accrual.get('quality_flag', 'unknown')
            }
        }
    except Exception as e:
        logger.error(f"Error performing full fundamental analysis for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Error performing analysis: {str(e)}")

@app.post("/api/fundamental/rank-universe", tags=["Fundamental Screening"])
async def rank_universe_by_value(
    request: UniverseRankingRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Rank universe of stocks by EBIT/EV (Value screening).
    
    **Authentication Required:** Yes
    
    According to the report: "Szeroki Skrining Value: Algorytmiczna selekcja uniwersum spółek,
    które są historycznie nisko wyceniane (np. te znajdujące się w dolnym kwintylu wyceny według wskaźnika EBIT/EV)"
    
    **Returns:**
    - Ranked list of stocks by EBIT/EV (highest EBIT/EV = lowest valuation)
    - Bottom percentile (e.g., bottom 20% = highest EBIT/EV)
    """
    try:
        # Get universe symbols
        universe_symbols = fundamental_screening_service.get_universe_symbols(
            exchange=request.exchange,
            index=request.index
        )
        
        # Rank by EBIT/EV
        ranked_stocks = fundamental_screening_service.rank_universe_by_ebit_ev(
            symbols=universe_symbols,
            percentile=request.percentile
        )
        
        return {
            'universe_size': len(universe_symbols),
            'ranked_count': len(ranked_stocks),
            'percentile': request.percentile,
            'ranked_stocks': ranked_stocks
        }
    except Exception as e:
        logger.error(f"Error ranking universe: {e}")
        raise HTTPException(status_code=500, detail=f"Error ranking universe: {str(e)}")

@app.post("/api/fundamental/allocate-capital", tags=["Fundamental Screening"])
async def allocate_capital(
    request: CapitalAllocationRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Allocate capital among screened stocks using equal weights.
    
    **Authentication Required:** Yes
    
    According to the report: "Budowa Portfela i Rebalansowanie: Mechaniczna alokacja kapitału
    (np. równe wagi) i rebalansowanie w regularnych, z góry określonych odstępach czasowych"
    
    **Returns:**
    - List of stocks with allocation_amount, allocation_percent, shares_to_buy
    """
    try:
        if request.method != 'equal_weights':
            raise HTTPException(status_code=400, detail="Only 'equal_weights' method is currently supported")
        
        allocated_stocks = fundamental_screening_service.allocate_capital_equal_weights(
            screened_stocks=request.screened_stocks,
            total_capital=request.total_capital
        )
        
        return {
            'method': request.method,
            'total_capital': request.total_capital,
            'stocks_count': len(allocated_stocks),
            'allocation_per_stock': request.total_capital / len(allocated_stocks) if allocated_stocks else 0,
            'allocated_stocks': allocated_stocks
        }
    except Exception as e:
        logger.error(f"Error allocating capital: {e}")
        raise HTTPException(status_code=500, detail=f"Error allocating capital: {str(e)}")

@app.post("/api/fundamental/rebalance/simulate", tags=["Fundamental Screening"])
async def simulate_rebalance_scenarios(
    request: RebalanceScenarioRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Simulate multiple rebalancing scenarios (equal weight, momentum, quality) for various
    position counts and estimate transaction costs.
    """
    try:
        scenarios = fundamental_screening_service.simulate_rebalance_scenarios(
            screened_stocks=request.screened_stocks,
            total_capital=request.total_capital,
            max_positions_options=request.max_positions_options or [5, 10, 20],
            strategies=request.strategies or ['equal_weight', 'momentum', 'quality'],
            transaction_cost=request.transaction_cost or 0.001,
            current_holdings=request.current_holdings or {}
        )
        return {
            'total_capital': request.total_capital,
            'scenario_count': len(scenarios),
            'scenarios': scenarios
        }
    except Exception as e:
        logger.error(f"Error simulating rebalance scenarios: {e}")
        raise HTTPException(status_code=500, detail=f"Error simulating rebalance scenarios: {str(e)}")

@app.post("/api/fundamental/rebalance", tags=["Fundamental Screening"])
async def rebalance_portfolio(
    request: RebalanceRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Generate rebalancing recommendations for portfolio.
    
    **Authentication Required:** Yes
    
    According to the report: "Rebalansowanie w regularnych, z góry określonych odstępach czasowych
    (np. rocznych), w celu zminimalizowania kosztów transakcyjnych i utrzymania regułowości systemu"
    
    **Returns:**
    - List of rebalance actions (buy/sell for each stock)
    - Total rebalance amount and transaction costs
    - Number of transactions
    """
    try:
        rebalance_result = fundamental_screening_service.rebalance_portfolio(
            current_holdings=request.current_holdings,
            target_allocations=request.target_allocations,
            rebalance_date=request.rebalance_date,
            transaction_cost_percent=request.transaction_cost_percent
        )
        
        return rebalance_result
    except Exception as e:
        logger.error(f"Error rebalancing portfolio: {e}")
        raise HTTPException(status_code=500, detail=f"Error rebalancing portfolio: {str(e)}")

@app.get("/api/fundamental/should-rebalance/{last_rebalance_date}", tags=["Fundamental Screening"])
async def check_rebalance_status(
    last_rebalance_date: str,
    rebalance_frequency: str = 'annual',
    current_user: Dict = Depends(get_current_user)
):
    """
    Check if portfolio should be rebalanced based on frequency.
    
    **Authentication Required:** Yes
    
    **Returns:**
    - Boolean indicating if rebalancing is due
    - Days since last rebalance
    - Required days for frequency
    """
    try:
        should_rebalance = fundamental_screening_service.should_rebalance(
            last_rebalance_date=last_rebalance_date,
            rebalance_frequency=rebalance_frequency
        )
        
        return {
            'should_rebalance': should_rebalance,
            'last_rebalance_date': last_rebalance_date,
            'rebalance_frequency': rebalance_frequency
        }
    except Exception as e:
        logger.error(f"Error checking rebalance status: {e}")
        raise HTTPException(status_code=500, detail=f"Error checking rebalance status: {str(e)}")

@app.post("/api/backtesting/run", tags=["Backtesting"])
async def run_backtest(
    request: BacktestRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Run an investment strategy backtest on historical data.
    
    Simulates investment strategies using real historical price data and calculates
    comprehensive performance metrics including CAGR, Sharpe ratio, and max drawdown.
    
    **Authentication Required:** Yes
    
    **Supported Strategies:**
    - `buy_and_hold`: Simple buy and hold strategy
    - `dca`: Dollar Cost Averaging (mock implementation)
    - `momentum`: Momentum-based strategy (mock implementation)
    - `mean_reversion`: Mean reversion strategy (mock implementation)
    
    **Returns:**
    - Total return, CAGR, Sharpe ratio
    - Volatility and max drawdown
    - Equity curve data
    - Win rate and trade history
    """
    try:
        results = backtest_engine.run_backtest(
            strategy=request.strategy,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
            asset_symbol=request.asset_symbol,
            asset_type=request.asset_type,
            strategy_params=request.strategy_params
        )
        return results
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get('/api/market/stream')
async def stream_market_prices(symbols: str, interval: int = 10, token: Optional[str] = None, current_user: Dict = Depends(get_current_user)):
    """Server-Sent Events: stream watchlist prices every N seconds"""
    # Support token via query param for SSE clients that cannot set headers
    if token:
        try:
            username = auth_manager.verify_token(token)
            if not username:
                return JSONResponse(status_code=401, content={"detail": "Invalid token"})
        except Exception:
            return JSONResponse(status_code=401, content={"detail": "Invalid token"})

    symbol_list = [s.strip().upper() for s in (symbols or '').split(',') if s.strip()]
    if not symbol_list:
        username = current_user.get("username", "default")
        user_symbols = watchlist_service.get_watchlist(username)
        symbol_list = user_symbols[:4] if user_symbols else ["AAPL", "MSFT", "TSLA", "GOOGL"]

    async def event_generator():
        while True:
            try:
                data = market_data_service.get_watchlist_prices(symbol_list[:4])
                payload = {"prices": data, "ts": datetime.utcnow().isoformat() + 'Z'}
                yield f"data: {payload}\n\n"
            except Exception as e:
                yield f"event: error\ndata: {str(e)}\n\n"
            await asyncio.sleep(max(5, min(60, int(interval))))

    return StreamingResponse(event_generator(), media_type='text/event-stream')

@app.get("/api/market/news")
async def get_market_news(
    symbols: Optional[str] = None,
    limit: int = 5,
    current_user: Dict = Depends(get_current_user)
):
    """Fetch market news headlines for the provided symbols (or general market headlines)."""
    try:
        symbol_list = [s.strip().upper() for s in (symbols or "").split(",") if s.strip()] if symbols else None
        items = market_data_service.get_news(symbol_list, limit)
        return items
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/market/price/{symbol}")
async def get_asset_price(
    symbol: str,
    asset_type: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Get current price for a specific asset"""
    try:
        data = market_data_service.get_price(symbol.upper(), asset_type or 'auto', priority='normal')
        if not data:
            raise HTTPException(status_code=404, detail=f"Price data not available for {symbol}")
        return data
    except HTTPException:
        raise
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/market/history/{symbol}")
async def get_symbol_history(symbol: str, days: int = 7, current_user: Dict = Depends(get_current_user)):
    try:
        series = market_data_service.get_symbol_history(symbol.upper(), days, priority='high')
        if not series:
            raise HTTPException(status_code=404, detail=f"History not available for {symbol}")
        return {"symbol": symbol.upper(), "days": days, "series": series}
    except HTTPException:
        raise
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(status_code=500, detail=f"Internal server error ({error_type}): {str(e)}")

@app.get("/api/market/history/batch")
async def get_symbol_history_batch(
    symbols: str,
    days: int = 7,
    current_user: Dict = Depends(get_current_user)
):
    """Get history for multiple symbols in a single request"""
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(',') if s.strip()]
        # Limit to 10 symbols per batch to avoid timeout
        symbol_list = symbol_list[:10]
        
        results = {}
        for symbol in symbol_list:
            try:
                series = market_data_service.get_symbol_history(symbol, days, priority='normal')
                if series:
                    results[symbol] = series
            except Exception as e:
                logger.warning(f"Failed to get history for {symbol}: {e}")
                # Continue with other symbols
                continue
        
        return {
            "days": days,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )


@app.get("/api/market-data/quality-report")
async def get_market_data_quality_report(current_user: Dict = Depends(get_current_user)):
    """
    Data quality report for market data:
    - Cache staleness (price/history)
    - Provider cooldown and failure statistics
    - Simple anomaly detection in recent history
    """
    try:
        report = market_data_service.get_quality_report()
        return report
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/market/search")
async def search_symbols(q: str, limit: int = 10, current_user: Dict = Depends(get_current_user)):
    try:
        items = market_data_service.search_symbols(q, limit)
        return {"query": q, "results": items}
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(status_code=500, detail=f"Internal server error ({error_type}): {str(e)}")

@app.get("/api/market/symbol/validate/{symbol}")
async def validate_symbol(symbol: str, current_user: Dict = Depends(get_current_user)):
    """Validate if a symbol exists and is tradeable"""
    try:
        result = market_data_service.validate_symbol(symbol)
        return result
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(status_code=500, detail=f"Internal server error ({error_type}): {str(e)}")

@app.get("/api/market/symbol/preview/{symbol}")
async def get_symbol_preview(symbol: str, current_user: Dict = Depends(get_current_user)):
    """Get preview data for a symbol before adding to watchlist"""
    try:
        preview = market_data_service.get_symbol_preview(symbol)
        if not preview:
            raise HTTPException(status_code=404, detail="Symbol not found or no data available")
        return preview
    except HTTPException:
        raise
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(status_code=500, detail=f"Internal server error ({error_type}): {str(e)}")

@app.get("/api/benchmark/{symbol}")
async def get_benchmark_history(symbol: str, days: int = 30, current_user: Dict = Depends(get_current_user)):
    """Get historical benchmark data (S&P500, BTC, etc.) for comparison"""
    try:
        history = market_data_service.get_symbol_history(symbol.upper(), days, priority='normal')
        if not history:
            return []
        
        # Calculate normalized returns (starting from 100% = base)
        if not history:
            return []
        
        base_value = history[0].get('close', 1) if history else 1
        normalized = []
        for point in history:
            normalized.append({
                'date': point.get('date'),
                'value': point.get('close', 0),
                'normalized_value': (point.get('close', 0) / base_value) * 100 if base_value > 0 else 0
            })
        
        return normalized
    except Exception as e:
        error_type = type(e).__name__
        logger.error(f"Error fetching benchmark history for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error ({error_type}): {str(e)}")

# Risk Management API
@app.get("/api/risk/analysis")
async def get_risk_analysis(current_user: Dict = Depends(get_current_user)):
    """Get comprehensive risk analysis for portfolio"""
    try:
        start_ts = time.time()
        # Hard budget for this endpoint to avoid excessive waiting on external providers
        max_seconds = float(os.getenv("RISK_ANALYSIS_MAX_SECONDS", "8.0"))

        # Get portfolio data
        portfolios = portfolio_tracker.get_all_portfolios(current_user["username"], use_transactions_only=True)
        summary = portfolio_tracker.calculate_total_portfolio(current_user["username"])
        total_value = summary.get('total_value_usd', 0)

        volatility_cache: Dict[str, Optional[float]] = {}
        volatility_threshold = 0.5  # minimum allocation % to trigger external volatility fetch
        max_symbols_for_volatility = int(os.getenv("RISK_VOLATILITY_MAX_ASSETS", "25"))

        def compute_asset_volatility(symbol: str) -> Optional[float]:
            key = (symbol or '').upper()
            if not key:
                return None
            if key in volatility_cache:
                return volatility_cache[key]

            # Enforce global time budget per request
            if time.time() - start_ts > max_seconds:
                volatility_cache[key] = None
                return None

            try:
                history = market_data_service.get_symbol_history(key, days=90, priority='low') or []
            except Exception as exc:  # pragma: no cover - diagnostic only
                app_logger.debug(f"Heatmap volatility fetch failed for {key}: {exc}")
                volatility_cache[key] = None
                return None

            closes: List[float] = []
            for point in history:
                close_val = point.get('close')
                if close_val is None:
                    continue
                try:
                    close_float = float(close_val)
                except (TypeError, ValueError):
                    continue
                if close_float > 0:
                    closes.append(close_float)

            if len(closes) < 2:
                volatility_cache[key] = None
                return None

            returns: List[float] = []
            for i in range(1, len(closes)):
                prev = closes[i - 1]
                if prev <= 0:
                    continue
                returns.append((closes[i] - prev) / prev)

            if len(returns) < 2:
                volatility_cache[key] = None
                return None

            import statistics

            try:
                std_dev = statistics.stdev(returns)
            except statistics.StatisticsError:
                volatility_cache[key] = None
                return None

            volatility = std_dev * (252 ** 0.5) * 100  # annualized volatility in %
            volatility_cache[key] = volatility
            return volatility
        
        usd_to_pln_rate = exchange_rate_service.get_current_rate()
        user_id = current_user.get("username")
        aggregated_assets, _ = _build_assets_with_validation(portfolios, usd_to_pln_rate, user_id=user_id)

        # Format assets for risk analysis using aggregated positions
        # Sort by value to process most important assets first (budget-friendly)
        sorted_aggregated = sorted(
            aggregated_assets,
            key=lambda a: (a.value_usd or 0.0),
            reverse=True,
        )

        assets = []
        processed_for_volatility = 0
        for aggregated in sorted_aggregated:
            symbol = (aggregated.symbol or '').upper()
            value_usd = aggregated.value_usd or 0.0
            amount_held = aggregated.amount or 0.0
            if not symbol or value_usd <= 0 or amount_held <= 0:
                continue

            allocation_percent = (value_usd / total_value * 100) if total_value > 0 else 0.0
            pnl_percent = aggregated.pnl_percent or 0.0
            asset_type = (aggregated.asset_type or '').lower()
            if asset_type not in ('crypto', 'stock'):
                # Infer type from sources when possible
                source_types: List[str] = []
                for src in aggregated.sources or []:
                    exchange_lower = (src.exchange or '').lower()
                    if any(name in exchange_lower for name in ['binance', 'bybit', 'coinbase', 'kraken', 'crypto']):
                        source_types.append('crypto')
                    elif any(name in exchange_lower for name in ['xtb', 'nyse', 'nasdaq', 'lse', 'amex']):
                        source_types.append('stock')
                if source_types:
                    asset_type = source_types[0]
                else:
                    asset_type = 'crypto'

            # Only fetch expensive volatility data for sufficiently important assets
            should_fetch_volatility = (
                allocation_percent >= volatility_threshold
                and processed_for_volatility < max_symbols_for_volatility
            )
            volatility_percent = compute_asset_volatility(symbol) if should_fetch_volatility else None
            if should_fetch_volatility:
                processed_for_volatility += 1
            if volatility_percent is None:
                volatility_percent = 60.0 if asset_type == 'crypto' else 25.0
            volatility_percent = max(5.0, min(120.0, float(volatility_percent)))

            assets.append({
                'symbol': symbol,
                'name': symbol,
                'type': asset_type,
                'allocation_percent': allocation_percent,
                'volatility': volatility_percent,
                'pnl_percent': pnl_percent,
            })
        
        # Calculate risk score
        risk_analysis = risk_management_service.calculate_portfolio_risk_score(assets, total_value)
        
        # Generate heatmap
        heatmap = risk_management_service.generate_portfolio_heatmap(assets)
        response_payload = {
            'risk_analysis': risk_analysis,
            'heatmap': heatmap,
            'assets_count': len(assets),
            'processing_time_sec': round(time.time() - start_ts, 3),
            'volatility_samples': processed_for_volatility,
        }
        app_logger.info(
            "risk_analysis completed in %.3fs (assets=%d, vol_samples=%d)",
            response_payload['processing_time_sec'],
            response_payload['assets_count'],
            response_payload['volatility_samples'],
        )
        return response_payload
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/risk/stop-loss/{symbol}")
async def get_stop_loss_suggestion(
    symbol: str,
    entry_price: float,
    current_price: float,
    asset_type: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Get stop-loss suggestion for an asset"""
    try:
        suggestion = risk_management_service.suggest_stop_loss(
            entry_price=entry_price,
            current_price=current_price,
            asset_type=asset_type or 'crypto'
        )
        return suggestion
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/risk/take-profit/{symbol}")
async def get_take_profit_suggestion(
    symbol: str,
    entry_price: float,
    current_price: float,
    asset_type: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Get take-profit suggestion for an asset"""
    try:
        suggestion = risk_management_service.suggest_take_profit(
            entry_price=entry_price,
            current_price=current_price,
            asset_type=asset_type or 'crypto'
        )
        return suggestion
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

@app.get("/api/risk/position-size")
async def calculate_position_size(
    portfolio_value: float,
    risk_per_trade: float = 2.0,
    entry_price: float = 0,
    stop_loss_price: float = 0,
    current_user: Dict = Depends(get_current_user)
):
    """Calculate optimal position size based on risk"""
    try:
        if entry_price == 0 or stop_loss_price == 0:
            raise HTTPException(status_code=400, detail="Entry price and stop-loss price are required")
        
        suggestion = risk_management_service.calculate_position_size(
            portfolio_value=portfolio_value,
            risk_per_trade=risk_per_trade,
            entry_price=entry_price,
            stop_loss_price=stop_loss_price
        )
        return suggestion
    except HTTPException:
        raise
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error ({error_type}): {str(e)}"
        )

# Startup/shutdown handled via lifespan; avoid double worker initialization

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        timeout_keep_alive=75,  # Keep connections alive longer
        timeout_graceful_shutdown=30  # Graceful shutdown timeout
    )
