"""
ACTIVEBOT - FastAPI Backend Server
Automated trading bot dashboard API
"""
from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
import asyncio

from models import Trade, BotConfig, SentimentData, BotStats, TelegramConfig
from trading_bot import ActiveBot
from cfgi_service import CFGIService, SimulatedCFGIService
from telegram_service import TelegramService

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Bot password
BOT_PASSWORD = os.environ.get('BOT_PASSWORD', '62411')

# Create the main app
app = FastAPI(
    title="ACTIVEBOT API",
    description="Automated crypto trading bot powered by CFGI sentiment analysis",
    version="1.0.0"
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global bot instance
trading_bot: Optional[ActiveBot] = None

# Request/Response Models
class ConfigUpdate(BaseModel):
    trade_size_usdc: Optional[float] = Field(None, ge=1.0, le=1000.0)
    assets_enabled: Optional[List[str]] = None
    dry_run_mode: Optional[bool] = None
    telegram_enabled: Optional[bool] = None
    telegram_chat_id: Optional[str] = None

class TelegramTestRequest(BaseModel):
    chat_id: str

class SimulateSentimentRequest(BaseModel):
    score: int = Field(..., ge=0, le=100)
    asset: str = "BTC"

class TradeResponse(BaseModel):
    id: str
    asset: str
    direction: str
    market_id: str
    amount_usdc: float
    entry_price: float
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    status: str
    cfgi_score: int
    timestamp: str
    closed_at: Optional[str] = None

class LoginRequest(BaseModel):
    password: str

class SystemStatus(BaseModel):
    cfgi_api: str
    polymarket_api: str
    mongodb: str
    telegram: str

# Auth
@api_router.post("/auth/login")
async def login(request: LoginRequest):
    if request.password == BOT_PASSWORD:
        return {"authenticated": True, "message": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid password")

@api_router.get("/auth/verify")
async def verify_password(password: str):
    return {"authenticated": password == BOT_PASSWORD}

# System Status
@api_router.get("/system/status")
async def get_system_status():
    """Check status of all external services"""
    import httpx
    
    status = {
        "cfgi_api": "unknown",
        "polymarket_api": "unknown", 
        "mongodb": "unknown",
        "telegram": "unknown"
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Check CFGI.io
        try:
            resp = await client.get("https://cfgi.io/bitcoin-fear-greed-index/15m")
            status["cfgi_api"] = "online" if resp.status_code == 200 else "error"
        except:
            status["cfgi_api"] = "offline"
        
        # Check Polymarket
        try:
            resp = await client.get("https://gamma-api.polymarket.com/markets?limit=1")
            status["polymarket_api"] = "online" if resp.status_code == 200 else "error"
        except:
            status["polymarket_api"] = "offline"
        
        # Check Telegram
        try:
            bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
            if bot_token:
                resp = await client.get(f"https://api.telegram.org/bot{bot_token}/getMe")
                status["telegram"] = "online" if resp.status_code == 200 else "error"
            else:
                status["telegram"] = "not_configured"
        except:
            status["telegram"] = "offline"
    
    # Check MongoDB
    try:
        await db.command("ping")
        status["mongodb"] = "online"
    except:
        status["mongodb"] = "offline"
    
    return status

# Health & Root
@api_router.get("/")
async def root():
    return {"message": "ACTIVEBOT API", "status": "online"}

@api_router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "bot_running": trading_bot.is_running if trading_bot else False
    }

# Bot Control
@api_router.post("/bot/start")
async def start_bot():
    global trading_bot
    
    if trading_bot is None:
        trading_bot = ActiveBot(db, dry_run=True)
    
    if trading_bot.is_running:
        return {"status": "already_running", "message": "Bot is already running"}
    
    await trading_bot.start()
    return {"status": "started", "message": "Bot started successfully"}

@api_router.post("/bot/stop")
async def stop_bot():
    global trading_bot
    
    if trading_bot is None or not trading_bot.is_running:
        return {"status": "not_running", "message": "Bot is not running"}
    
    await trading_bot.stop()
    return {"status": "stopped", "message": "Bot stopped successfully"}

@api_router.get("/bot/status")
async def get_bot_status():
    global trading_bot
    
    is_running = trading_bot.is_running if trading_bot else False
    config = None
    
    if trading_bot and trading_bot.config:
        config = {
            "trade_size_usdc": trading_bot.config.trade_size_usdc,
            "assets_enabled": trading_bot.config.assets_enabled,
            "dry_run_mode": trading_bot.config.dry_run_mode,
            "telegram_enabled": trading_bot.config.telegram_enabled
        }
    else:
        # Load from DB
        config_doc = await db.bot_config.find_one({"id": "main_config"}, {"_id": 0})
        if config_doc:
            config = {
                "trade_size_usdc": config_doc.get("trade_size_usdc", 10.0),
                "assets_enabled": config_doc.get("assets_enabled", ["BTC", "ETH", "SOL"]),
                "dry_run_mode": config_doc.get("dry_run_mode", True),
                "telegram_enabled": config_doc.get("telegram_enabled", False)
            }
        else:
            config = {
                "trade_size_usdc": 10.0,
                "assets_enabled": ["BTC", "ETH", "SOL"],
                "dry_run_mode": True,
                "telegram_enabled": False
            }
    
    return {
        "is_running": is_running,
        "config": config
    }

# Configuration
@api_router.get("/config")
async def get_config():
    config_doc = await db.bot_config.find_one({"id": "main_config"}, {"_id": 0})
    if config_doc:
        return config_doc
    return BotConfig().model_dump()

@api_router.put("/config")
async def update_config(update: ConfigUpdate):
    global trading_bot
    
    config_doc = await db.bot_config.find_one({"id": "main_config"}, {"_id": 0})
    if config_doc:
        config = BotConfig(**config_doc)
    else:
        config = BotConfig()
    
    # Update fields
    if update.trade_size_usdc is not None:
        config.trade_size_usdc = update.trade_size_usdc
    if update.assets_enabled is not None:
        config.assets_enabled = update.assets_enabled
    if update.dry_run_mode is not None:
        config.dry_run_mode = update.dry_run_mode
    if update.telegram_enabled is not None:
        config.telegram_enabled = update.telegram_enabled
    if update.telegram_chat_id is not None:
        config.telegram_chat_id = update.telegram_chat_id
    
    config.last_updated = datetime.now(timezone.utc)
    
    # Save to DB
    doc = config.model_dump()
    doc['last_updated'] = doc['last_updated'].isoformat()
    await db.bot_config.update_one(
        {"id": "main_config"},
        {"$set": doc},
        upsert=True
    )
    
    # Update bot instance if running
    if trading_bot:
        trading_bot.config = config
    
    return {"status": "updated", "config": doc}

# Sentiment
@api_router.get("/sentiment/current")
async def get_current_sentiment():
    """Get current sentiment for all assets - ALWAYS uses real CFGI data"""
    global trading_bot
    
    # Always use real CFGI service for sentiment
    cfgi_service = CFGIService()
    
    try:
        sentiments = {}
        for asset in ["BTC", "ETH", "SOL"]:
            sentiment = await cfgi_service.get_sentiment(asset)
            sentiments[asset] = {
                "score": sentiment['score'],
                "signal": sentiment['signal'],
                "timestamp": sentiment['timestamp'].isoformat()
            }
        return sentiments
    finally:
        await cfgi_service.close()

@api_router.get("/sentiment/history")
async def get_sentiment_history(asset: Optional[str] = None, limit: int = 100):
    """Get sentiment history"""
    query = {}
    if asset:
        query["asset"] = asset
    
    history = await db.sentiment_history.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)
    return history

@api_router.post("/sentiment/simulate")
async def simulate_sentiment(request: SimulateSentimentRequest):
    """Set simulated sentiment score (for testing)"""
    global trading_bot
    
    if trading_bot and isinstance(trading_bot.cfgi_service, SimulatedCFGIService):
        trading_bot.cfgi_service.set_simulated_score(request.score)
        sentiment = await trading_bot.cfgi_service.get_sentiment(request.asset)
        return {
            "status": "simulated",
            "score": sentiment['score'],
            "signal": sentiment['signal']
        }
    
    return {"status": "not_available", "message": "Simulation only available in dry-run mode"}

# Trades
@api_router.get("/trades", response_model=List[TradeResponse])
async def get_trades(
    asset: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Get trade history"""
    query = {}
    if asset:
        query["asset"] = asset
    if status:
        query["status"] = status
    
    trades = await db.trades.find(query, {"_id": 0}).sort("timestamp", -1).skip(offset).limit(limit).to_list(limit)
    return trades

@api_router.get("/trades/{trade_id}")
async def get_trade(trade_id: str):
    """Get specific trade details"""
    trade = await db.trades.find_one({"id": trade_id}, {"_id": 0})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade

# Statistics
@api_router.get("/stats")
async def get_stats():
    """Get bot statistics"""
    global trading_bot
    
    if trading_bot:
        return await trading_bot.get_stats()
    
    # Calculate from DB
    trades = await db.trades.find({}, {"_id": 0}).to_list(1000)
    
    total_trades = len(trades)
    winning_trades = len([t for t in trades if t.get('status') == 'WON'])
    losing_trades = len([t for t in trades if t.get('status') == 'LOST'])
    open_trades = len([t for t in trades if t.get('status') == 'OPEN'])
    
    pnls = [t.get('pnl', 0) or 0 for t in trades if t.get('pnl') is not None]
    total_pnl = sum(pnls)
    
    win_rate = (winning_trades / (winning_trades + losing_trades) * 100) if (winning_trades + losing_trades) > 0 else 0
    
    return {
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "open_trades": open_trades,
        "total_pnl": round(total_pnl, 2),
        "win_rate": round(win_rate, 1),
        "best_trade": round(max(pnls) if pnls else 0, 2),
        "worst_trade": round(min(pnls) if pnls else 0, 2)
    }

@api_router.get("/stats/pnl-history")
async def get_pnl_history(days: int = 7):
    """Get P&L history for charts"""
    trades = await db.trades.find(
        {"status": {"$in": ["WON", "LOST"]}},
        {"_id": 0, "timestamp": 1, "pnl": 1, "asset": 1}
    ).sort("timestamp", 1).to_list(1000)
    
    # Group by day and calculate cumulative P&L
    pnl_history = []
    cumulative_pnl = 0
    
    for trade in trades:
        pnl = trade.get('pnl', 0) or 0
        cumulative_pnl += pnl
        pnl_history.append({
            "timestamp": trade['timestamp'],
            "pnl": pnl,
            "cumulative_pnl": round(cumulative_pnl, 2),
            "asset": trade.get('asset', 'BTC')
        })
    
    return pnl_history

# Telegram
@api_router.post("/telegram/test")
async def test_telegram(request: TelegramTestRequest):
    """Test Telegram connection"""
    global trading_bot
    
    if trading_bot:
        success = await trading_bot.telegram_service.test_connection(request.chat_id)
    else:
        from telegram_service import TelegramService
        service = TelegramService()
        success = await service.test_connection(request.chat_id)
        await service.close()
    
    if success:
        return {"status": "success", "message": "Test message sent successfully"}
    else:
        raise HTTPException(status_code=400, detail="Failed to send test message. Check bot token and chat ID.")

# Markets (from Polymarket)
@api_router.get("/markets")
async def get_markets():
    """Get available 15-min crypto markets using the correct Polymarket API
    
    Markets are discovered using the dynamic slug pattern:
    {asset}-updown-15m-{unix_timestamp}
    """
    global trading_bot
    
    if trading_bot and trading_bot.polymarket_service:
        markets = await trading_bot.polymarket_service.fetch_15min_crypto_markets()
        return [
            {
                "condition_id": m.condition_id,
                "question": m.question,
                "asset": m.asset,
                "slug": m.slug,
                "yes_token_id": m.yes_token_id[:30] + "..." if len(m.yes_token_id) > 30 else m.yes_token_id,
                "no_token_id": m.no_token_id[:30] + "..." if len(m.no_token_id) > 30 else m.no_token_id,
                "yes_price": m.yes_price,
                "no_price": m.no_price,
                "volume_24h": m.volume_24h,
                "is_active": m.is_active,
                "accepting_orders": m.accepting_orders
            }
            for m in markets
        ]
    
    # Use SimulatedPolymarketService which still fetches real market data
    from polymarket_service import SimulatedPolymarketService
    sim = SimulatedPolymarketService()
    try:
        markets = await sim.fetch_15min_crypto_markets()
        return [
            {
                "condition_id": m.condition_id,
                "question": m.question,
                "asset": m.asset,
                "slug": m.slug,
                "yes_token_id": m.yes_token_id[:30] + "..." if len(m.yes_token_id) > 30 else m.yes_token_id,
                "no_token_id": m.no_token_id[:30] + "..." if len(m.no_token_id) > 30 else m.no_token_id,
                "yes_price": m.yes_price,
                "no_price": m.no_price,
                "volume_24h": m.volume_24h,
                "is_active": m.is_active,
                "accepting_orders": m.accepting_orders
            }
            for m in markets
        ]
    finally:
        await sim.close()

@api_router.get("/markets/test")
async def test_polymarket_connection():
    """Test the Polymarket API connection and market discovery
    
    This endpoint verifies:
    1. Connection to Gamma API
    2. Connection to CLOB API
    3. Ability to discover 15-minute markets
    4. Wallet configuration status
    """
    from polymarket_service import PolymarketService
    
    service = PolymarketService()
    try:
        # Check connection
        connection_status = await service.check_connection()
        
        # Try to fetch current markets
        markets_found = []
        for asset in ["BTC", "ETH", "SOL"]:
            market = await service.get_market_for_asset(asset)
            if market:
                markets_found.append({
                    "asset": asset,
                    "slug": market.slug,
                    "question": market.question,
                    "condition_id": market.condition_id[:20] + "...",
                    "prices": {
                        "up": market.yes_price,
                        "down": market.no_price
                    },
                    "accepting_orders": market.accepting_orders
                })
        
        return {
            "connection": connection_status,
            "markets_found": len(markets_found),
            "markets": markets_found,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    finally:
        await service.close()

# Include the router
app.include_router(api_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup/Shutdown
@app.on_event("startup")
async def startup_event():
    global trading_bot
    logger.info("ACTIVEBOT API starting up...")
    
    # Load config first to check dry_run mode
    config_doc = await db.bot_config.find_one({"id": "main_config"}, {"_id": 0})
    dry_run = True
    if config_doc:
        dry_run = config_doc.get("dry_run_mode", True)
    
    # Initialize bot with correct mode
    trading_bot = ActiveBot(db, dry_run=dry_run)
    await trading_bot.load_config()
    
    # Set defaults from environment if config not set
    if trading_bot.config:
        # Update Telegram settings from env if not already set
        telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        if telegram_chat_id and not trading_bot.config.telegram_chat_id:
            trading_bot.config.telegram_chat_id = telegram_chat_id
            trading_bot.config.telegram_enabled = True
            await trading_bot.save_config()
    
    # Auto-start if was running before
    if trading_bot.config and trading_bot.config.is_running:
        await trading_bot.start()
        logger.info("Bot auto-started from previous state")

@app.on_event("shutdown")
async def shutdown_event():
    global trading_bot
    logger.info("ACTIVEBOT API shutting down...")
    
    if trading_bot:
        await trading_bot.stop()
        await trading_bot.cleanup()
    
    client.close()
