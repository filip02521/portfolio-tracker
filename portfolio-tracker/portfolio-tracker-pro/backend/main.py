from fastapi import FastAPI, HTTPException, Depends, status, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel

# Import backup router
try:
    from routes.backup import router as backup_router
except ImportError:
    backup_router = None
from typing import List, Optional, Dict, Any
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
from fundamental_screening_service import FundamentalScreeningService
from exchange_manager import ExchangeManager
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List
import os
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
portfolio_tracker = PortfolioTracker()
transaction_history = TransactionHistory()
portfolio_history = PortfolioHistory()
pdf_generator = PDFReportGenerator()
settings_manager = SettingsManager()
auth_manager = AuthManager()
exchange_rate_service = get_exchange_rate_service()  # Initialize exchange rate service
smart_insights_service = SmartInsightsService()  # Initialize smart insights service
goal_tracking_service = GoalTrackingService()  # Initialize goal tracking service
tax_optimization_service = TaxOptimizationService()  # Initialize tax optimization service
risk_analytics_service = RiskAnalyticsService()  # Initialize risk analytics service
price_alert_service = PriceAlertService()  # Initialize price alert service
market_data_service = MarketDataService()  # Initialize market data service
risk_management_service = RiskManagementService()  # Initialize risk management service
watchlist_service = WatchlistService()  # Initialize user watchlist service
ai_service = AIService(market_data_service=market_data_service)  # Initialize AI service
backtest_engine = BacktestEngine(market_data_service=market_data_service)  # Initialize backtesting engine
confluence_strategy_service = ConfluenceStrategyService(market_data_service=market_data_service)  # Initialize confluence strategy service
fundamental_screening_service = FundamentalScreeningService(market_data_service=market_data_service)  # Initialize fundamental screening service
exchange_manager = ExchangeManager()  # Initialize exchange manager

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

class Asset(BaseModel):
    symbol: str
    amount: float
    value_usd: float
    value_pln: float
    pnl: float
    pnl_percent: float
    exchange: str

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

class CreateTransaction(BaseModel):
    symbol: str
    type: str  # buy/sell
    amount: float
    price: float
    date: str
    exchange: str
    commission: float = 0.0
    commission_currency: str = 'USD'

class UpdateTransaction(BaseModel):
    symbol: Optional[str] = None
    type: Optional[str] = None
    amount: Optional[float] = None
    price: Optional[float] = None
    date: Optional[str] = None
    exchange: Optional[str] = None
    commission: Optional[float] = None
    commission_currency: Optional[str] = None

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

@app.get("/api/watchlist")
async def get_user_watchlist(current_user: Dict = Depends(get_current_user)):
    try:
        username = current_user.get("username", "default")
        return {"symbols": watchlist_service.get_watchlist(username)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/watchlist")
async def add_user_watchlist(item: WatchlistAdd, current_user: Dict = Depends(get_current_user)):
    try:
        username = current_user.get("username", "default")
        updated = watchlist_service.add_symbol(username, item.symbol)
        return {"symbols": updated}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/watchlist/{symbol}")
async def remove_user_watchlist(symbol: str, current_user: Dict = Depends(get_current_user)):
    try:
        username = current_user.get("username", "default")
        updated = watchlist_service.remove_symbol(username, symbol)
        return {"symbols": updated}
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

@app.get("/api/mobile/dashboard")
async def get_mobile_dashboard(current_user: Dict = Depends(get_current_user)):
    """Get compact mobile dashboard data in a single request"""
    try:
        # Get summary
        portfolios = portfolio_tracker.get_all_portfolios()
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
                realized_pnl = transaction_history.get_total_realized_pnl()
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
        all_transactions = transaction_history.get_all_transactions()
        recent_tx = [{
            "id": t.get('id', ''),
            "symbol": t.get('asset', ''),
            "type": t.get('type', ''),
            "amount": t.get('amount', 0),
            "price": t.get('price_usd', 0),
            "date": t.get('date', '')
        } for t in all_transactions[:5]]
        
        # Get 7-day performance preview (lite mode)
        history_data = portfolio_history.get_chart_data(days=7)
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
    try:
        portfolios = portfolio_tracker.get_all_portfolios()
        
        if not portfolios:
            return PortfolioSummary(
                total_value_usd=0,
                total_value_pln=0,
                total_pnl=0,
                total_pnl_percent=0,
                active_exchanges=0,
                total_assets=0,
                last_updated=datetime.utcnow().isoformat() + "Z"
            )
        
        # Calculate totals
        total_value_usd = sum(p.get('total_value_usdt', 0) for p in portfolios)
        # Get real exchange rate
        usd_to_pln_rate = exchange_rate_service.get_current_rate()
        total_value_pln = total_value_usd * usd_to_pln_rate
        active_exchanges = len([p for p in portfolios if p.get('total_value_usdt', 0) > 0])
        total_assets = sum(len(p.get('balances', [])) for p in portfolios)
        
        # Calculate real PNL from transaction history (realized + unrealized)
        try:
            realized_pnl = transaction_history.get_total_realized_pnl()
            
            # Calculate unrealized PNL for all assets
            unrealized_pnl = 0.0
            for portfolio in portfolios:
                for balance in portfolio.get('balances', []):
                    if balance.get('value_usdt', 0) > 0:
                        asset_symbol = balance.get('asset', '')
                        exchange = portfolio.get('exchange', '')
                        
                        # Get transactions for this asset
                        asset_transactions = transaction_history.get_transactions_for_asset(exchange, asset_symbol)
                        if asset_transactions:
                            # Calculate cost basis using FIFO
                            buy_transactions = [t for t in asset_transactions if t['type'] == 'buy']
                            sell_transactions = [t for t in asset_transactions if t['type'] == 'sell']
                            
                            buy_amount = sum(t['amount'] for t in buy_transactions)
                            sell_amount = sum(t['amount'] for t in sell_transactions)
                            net_amount = buy_amount - sell_amount
                            
                            if net_amount > 0:
                                current_price = balance.get('value_usdt', 0) / balance.get('total', 1)
                                current_value = net_amount * current_price
                                
                                # Calculate cost basis (proportional to remaining holdings)
                                total_invested = sum(t['value_usd'] for t in buy_transactions)
                                cost_basis = total_invested * (net_amount / buy_amount) if buy_amount > 0 else 0
                                
                                # Unrealized PNL for this asset
                                asset_unrealized = current_value - cost_basis
                                unrealized_pnl += asset_unrealized
            
            total_pnl = realized_pnl + unrealized_pnl
            total_pnl_percent = (total_pnl / total_value_usd * 100) if total_value_usd > 0 else 0
        except Exception as e:
            logger.error(f"Error calculating PNL: {e}")
            total_pnl = 0
            total_pnl_percent = 0
        
        # Auto-add portfolio snapshot if enough time has passed (throttled to 1/hour)
        try:
            if portfolio_history.should_add_snapshot(min_interval_hours=1):
                portfolio_history.add_snapshot(total_value_usd, total_value_pln)
        except Exception as e:
            logger.warning(f"Could not add portfolio snapshot: {e}")
        
        return PortfolioSummary(
            total_value_usd=total_value_usd,
            total_value_pln=total_value_pln,
            total_pnl=total_pnl,
            total_pnl_percent=total_pnl_percent,
            active_exchanges=active_exchanges,
            total_assets=total_assets,
            last_updated=datetime.utcnow().isoformat() + "Z"
        )
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

@app.get("/api/portfolio/assets", response_model=List[Asset])
async def get_portfolio_assets(current_user: Dict = Depends(get_current_user)):
    """Get detailed asset breakdown"""
    try:
        portfolios = portfolio_tracker.get_all_portfolios()
        assets = []
        
        for portfolio in portfolios:
            for balance in portfolio.get('balances', []):
                if balance.get('value_usdt', 0) > 0:
                    # Calculate PNL for this asset
                    asset_symbol = balance.get('asset', '')
                    exchange = portfolio.get('exchange', '')
                    try:
                        # Use calculate_pnl which returns realized + unrealized PNL
                        current_price = balance.get('value_usdt', 0) / balance.get('total', 1) if balance.get('total', 0) > 0 else 0
                        pnl_data = transaction_history.calculate_pnl(exchange, asset_symbol, current_price, balance.get('total', 0))
                        
                        if pnl_data:
                            asset_pnl = pnl_data.get('pnl', 0)
                            asset_pnl_percent = pnl_data.get('pnl_percent', 0)
                        else:
                            asset_pnl = 0
                            asset_pnl_percent = 0
                    except Exception as e:
                        logger.error(f"Error calculating PNL for {asset_symbol}: {e}")
                        asset_pnl = 0
                        asset_pnl_percent = 0
                    
                    assets.append(Asset(
                        symbol=asset_symbol,
                        amount=balance.get('free', 0) + balance.get('locked', 0),
                        value_usd=balance.get('value_usdt', 0),
                        value_pln=balance.get('value_usdt', 0) * exchange_rate_service.get_current_rate(),
                        pnl=asset_pnl,
                        pnl_percent=asset_pnl_percent,
                        exchange=exchange
                    ))
        
        return assets
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
        # Get real transaction data
        all_transactions = transaction_history.get_all_transactions()
        
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
        filtered_transactions = sorted(filtered_transactions, key=lambda x: x.get('date', ''), reverse=True)
        
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
                commission_currency=tx.get('commission_currency', 'USD')
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
            commission_currency=transaction_data.commission_currency
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
        all_transactions = transaction_history.get_all_transactions()
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
        
        # Update transaction
        success = transaction_history.update_transaction(transaction_id, **update_dict)
        
        if not success:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Get updated transaction
        updated_transactions = transaction_history.get_all_transactions()
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
            commission_currency=updated_tx['commission_currency']
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
        all_transactions = transaction_history.get_all_transactions()
        tx = next((t for t in all_transactions if t['id'] == transaction_id), None)
        
        if not tx:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        transaction_history.delete_transaction(transaction_id)
        
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
        all_transactions = transaction_history.get_all_transactions()
        
        if format.lower() == "csv":
            # Create CSV in memory
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'ID', 'Date', 'Exchange', 'Asset', 'Type', 
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
        # Get portfolio history
        history_data = portfolio_history.get_chart_data(days=days)
        
        if not history_data or len(history_data) < 2:
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
        
        # Extract values and calculate daily returns
        # portfolio_history returns 'timestamp', not 'date'
        # Filter out entries with zero or missing values
        values = [point.get('value_usd', 0) for point in history_data if point.get('value_usd', 0) > 0]
        
        if len(values) < 2:
            return {
                "period": f"{days} days",
                "total_return": 0.0,
                "daily_returns": [],
                "volatility": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "win_rate": 0.0
            }
        
        # Calculate daily returns (percentage change)
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
        history_points = portfolio_history.get_chart_data(days)
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
        history_points = portfolio_history.get_chart_data(days=90)
        if len(history_points) < 10:
            return {}
        
        # Get all assets
        portfolios = portfolio_tracker.get_all_portfolios()
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

@app.get("/api/analytics/portfolio-flow")
async def get_portfolio_flow(current_user: Dict = Depends(get_current_user)):
    """Get portfolio flow data for Sankey diagram (exchange -> asset)"""
    try:
        portfolios = portfolio_tracker.get_all_portfolios()
        
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
        # Get portfolio data
        portfolios = portfolio_tracker.get_all_portfolios()
        
        # Get transaction history
        all_transactions = transaction_history.get_all_transactions()
        
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

@app.get("/api/analytics/allocation")
async def get_allocation_analytics(current_user: Dict = Depends(get_current_user)):
    """Get portfolio allocation analytics"""
    try:
        portfolios = portfolio_tracker.get_all_portfolios()
        
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
    try:
        # Get historical data from portfolio_history
        history_data = portfolio_history.get_chart_data(days=days)
        
        # Convert to API format
        history_points = []
        for entry in history_data:
            history_points.append({
                "date": entry.get('timestamp', ''),
                "value_usd": entry.get('value_usd', 0),
                "value_pln": entry.get('value_pln', 0),
                "total_assets": 0,  # Not available in portfolio_history
                "active_exchanges": 0  # Not available in portfolio_history
            })
        
        # Lite mode for mobile: return every 5th point to reduce payload
        if lite and len(history_points) > 10:
            history_points = history_points[::5]
        
        return history_points
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

@app.get("/api/reports/tax-pdf")
async def generate_tax_report_pdf(year: int = None, current_user: Dict = Depends(get_current_user)):
    """Generate tax report PDF for specified year"""
    try:
        # Get current year if not specified
        if year is None:
            from datetime import datetime
            year = datetime.now().year
        
        # Get all transactions
        all_transactions = transaction_history.get_all_transactions()
        
        # Filter transactions for the specified year
        transactions_for_year = [
            t for t in all_transactions 
            if t.get('date', '')[:4] == str(year)
        ]
        
        # Get realized PNL for the year using transaction_history
        # For now, we'll use total realized PNL (can be enhanced to filter by year)
        realized_pnl = transaction_history.get_total_realized_pnl()
        
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
        portfolios = portfolio_tracker.get_all_portfolios()
        
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
        status = settings_manager.get_api_keys_status()
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
            exchange=exchange,
            api_key=keys.api_key,
            secret_key=keys.secret_key,
            username=keys.username,
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
        result = settings_manager.test_connection(exchange)
        if result.get("success"):
            return result
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Connection test failed")
            )
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
    try:
        user_id = current_user.get("username", "default")
        goals = goal_tracking_service.get_user_goals(user_id)
        
        # Update progress for each goal
        portfolio_summary = await get_portfolio_summary(current_user)
        current_value = portfolio_summary.total_value_usd
        
        updated_goals = []
        for goal in goals:
            updated_goal = goal_tracking_service.update_goal_progress(
                goal["id"], user_id, current_value
            )
            if updated_goal:
                updated_goals.append(updated_goal)
        
        return updated_goals
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
        all_transactions = transaction_history.get_all_transactions()
        year_transactions = [
            t for t in all_transactions
            if t.get('date', '')[:4] == str(year)
        ]
        
        # Calculate realized gains/losses
        realized_pnl = transaction_history.get_total_realized_pnl()
        
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
        all_transactions = transaction_history.get_all_transactions()
        realized_pnl = transaction_history.get_total_realized_pnl()
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
        
        realized_pnl = transaction_history.get_total_realized_pnl()
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
    condition: str  # 'above' or 'below'
    price: float
    name: Optional[str] = None

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
            name=alert_data.name
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
            price_data = market_data_service.get_price(symbol)
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
    """Get prices for watchlist symbols"""
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
        portfolios = portfolio_tracker.get_all_portfolios()
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
            results = fundamental_screening_service.screen_vq_plus_strategy(
                symbols=request.symbols,
                min_f_score=request.min_f_score,
                max_z_score=request.max_z_score,  # Actually min threshold (we want > 3.0)
                max_accrual_ratio=request.max_accrual_ratio,
                auto_universe=request.auto_universe,
                universe_index=request.universe_index,
                value_percentile=request.value_percentile
            )
        return {
            'total_screened': len(results),
            'symbols_analyzed': len(request.symbols) if request.symbols else 0,
            'results': results,
            'filters_applied': {
                'min_f_score': request.min_f_score,
                'min_z_score': request.max_z_score,  # Note: This is actually min threshold
                'max_accrual_ratio': request.max_accrual_ratio
            }
        }

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

@app.get("/api/market/price/{symbol}")
async def get_asset_price(
    symbol: str,
    asset_type: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Get current price for a specific asset"""
    try:
        data = market_data_service.get_price(symbol.upper(), asset_type or 'auto')
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
        series = market_data_service.get_symbol_history(symbol.upper(), days)
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
                series = market_data_service.get_symbol_history(symbol, days)
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

@app.get("/api/market/search")
async def search_symbols(q: str, limit: int = 10, current_user: Dict = Depends(get_current_user)):
    try:
        items = market_data_service.search_symbols(q, limit)
        return {"query": q, "results": items}
    except Exception as e:
        error_type = type(e).__name__
        raise HTTPException(status_code=500, detail=f"Internal server error ({error_type}): {str(e)}")

@app.get("/api/benchmark/{symbol}")
async def get_benchmark_history(symbol: str, days: int = 30, current_user: Dict = Depends(get_current_user)):
    """Get historical benchmark data (S&P500, BTC, etc.) for comparison"""
    try:
        history = market_data_service.get_symbol_history(symbol.upper(), days)
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
        # Get portfolio data
        portfolios = portfolio_tracker.get_all_portfolios()
        summary = portfolio_tracker.calculate_total_portfolio()
        total_value = summary.get('total_value_usd', 0)
        
        # Format assets for risk analysis
        assets = []
        for portfolio in portfolios.values():
            for asset in portfolio.get('assets', []):
                asset_value = asset.get('current_value_usd', 0)
                allocation_percent = (asset_value / total_value * 100) if total_value > 0 else 0
                pnl_percent = asset.get('pnl_percent', 0)
                
                assets.append({
                    'symbol': asset.get('symbol', ''),
                    'name': asset.get('symbol', ''),
                    'type': 'crypto' if portfolio.get('exchange') in ['binance', 'bybit'] else 'stock',
                    'allocation_percent': allocation_percent,
                    'volatility': 40 if asset.get('symbol') in ['BTC', 'ETH'] else 30,  # Mock volatility
                    'pnl_percent': pnl_percent,
                })
        
        # Calculate risk score
        risk_analysis = risk_management_service.calculate_portfolio_risk_score(assets, total_value)
        
        # Generate heatmap
        heatmap = risk_management_service.generate_portfolio_heatmap(assets)
        
        return {
            'risk_analysis': risk_analysis,
            'heatmap': heatmap,
            'assets_count': len(assets)
        }
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
