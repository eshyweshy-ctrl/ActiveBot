"""
ACTIVEBOT - Database Models
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Literal
from datetime import datetime, timezone
import uuid

class SentimentData(BaseModel):
    """CFGI Sentiment Data"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    score: int = Field(..., ge=0, le=100)
    asset: str  # BTC, ETH, SOL
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    signal: Literal["BUY_YES", "BUY_NO", "HOLD"]
    
class Trade(BaseModel):
    """Trade Record"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    asset: str  # BTC, ETH, SOL
    direction: Literal["UP", "DOWN"]  # UP = bought YES, DOWN = bought NO
    market_id: str
    token_id: str
    amount_usdc: float
    entry_price: float
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    status: Literal["PENDING", "OPEN", "WON", "LOST", "CANCELLED"] = "PENDING"
    cfgi_score: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    closed_at: Optional[datetime] = None
    tx_hash: Optional[str] = None
    error_message: Optional[str] = None

class BotConfig(BaseModel):
    """Bot Configuration"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = "main_config"
    is_running: bool = False
    trade_size_usdc: float = Field(default=10.0, ge=1.0, le=1000.0)
    assets_enabled: List[str] = Field(default=["BTC", "ETH", "SOL"])
    dry_run_mode: bool = True  # Start with dry run for safety
    min_time_to_close_minutes: int = 2  # Skip if market closes soon
    telegram_enabled: bool = False
    telegram_chat_id: Optional[str] = None
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TelegramConfig(BaseModel):
    """Telegram Notification Settings"""
    enabled: bool = False
    chat_id: Optional[str] = None

class BotStats(BaseModel):
    """Bot Statistics Summary"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    open_trades: int = 0
    total_pnl: float = 0.0
    win_rate: float = 0.0
    best_trade: float = 0.0
    worst_trade: float = 0.0
    
class TradeHistoryFilter(BaseModel):
    """Filter for trade history"""
    asset: Optional[str] = None
    status: Optional[str] = None
    limit: int = 50
    offset: int = 0
