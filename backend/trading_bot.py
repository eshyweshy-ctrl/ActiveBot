"""
ACTIVEBOT - Main Trading Bot Logic
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Set, Optional
import random

from models import Trade, BotConfig, SentimentData
from cfgi_service import CFGIService, SimulatedCFGIService
from polymarket_service import PolymarketService, SimulatedPolymarketService
from telegram_service import TelegramService

logger = logging.getLogger(__name__)

class ActiveBot:
    """
    ACTIVEBOT - Automated trading bot that reads crypto sentiment
    and places trades on Polymarket 15-minute direction markets
    """
    
    def __init__(self, db, dry_run: bool = True):
        self.db = db
        self.dry_run = dry_run
        
        # Services
        if dry_run:
            self.cfgi_service = SimulatedCFGIService()
            self.polymarket_service = SimulatedPolymarketService()
        else:
            self.cfgi_service = CFGIService()
            self.polymarket_service = PolymarketService()
        
        self.telegram_service = TelegramService()
        
        # State
        self.is_running = False
        self.traded_markets: Set[str] = set()  # Track markets already traded
        self.config: Optional[BotConfig] = None
        self._task: Optional[asyncio.Task] = None
    
    async def load_config(self) -> BotConfig:
        """Load bot configuration from database"""
        config_doc = await self.db.bot_config.find_one({"id": "main_config"}, {"_id": 0})
        if config_doc:
            self.config = BotConfig(**config_doc)
        else:
            self.config = BotConfig()
            await self.save_config()
        return self.config
    
    async def save_config(self):
        """Save bot configuration to database"""
        if self.config:
            self.config.last_updated = datetime.now(timezone.utc)
            doc = self.config.model_dump()
            doc['last_updated'] = doc['last_updated'].isoformat()
            await self.db.bot_config.update_one(
                {"id": "main_config"},
                {"$set": doc},
                upsert=True
            )
    
    async def start(self):
        """Start the trading bot"""
        if self.is_running:
            logger.warning("Bot is already running")
            return
        
        await self.load_config()
        self.is_running = True
        self.config.is_running = True
        await self.save_config()
        
        logger.info(f"Starting ACTIVEBOT (dry_run={self.dry_run})")
        self._task = asyncio.create_task(self._run_loop())
    
    async def stop(self):
        """Stop the trading bot"""
        self.is_running = False
        if self.config:
            self.config.is_running = False
            await self.save_config()
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("ACTIVEBOT stopped")
    
    async def _run_loop(self):
        """Main trading loop - runs every 60 seconds"""
        while self.is_running:
            try:
                await self._execute_cycle()
            except Exception as e:
                logger.error(f"Error in trading cycle: {e}", exc_info=True)
            
            # Wait 60 seconds before next cycle
            await asyncio.sleep(60)
    
    async def _execute_cycle(self):
        """Execute one trading cycle"""
        if not self.config:
            await self.load_config()
        
        logger.info("Starting trading cycle...")
        
        for asset in self.config.assets_enabled:
            try:
                await self._process_asset(asset)
            except Exception as e:
                logger.error(f"Error processing {asset}: {e}")
    
    async def _process_asset(self, asset: str):
        """Process trading decision for a single asset"""
        
        # 1. Get sentiment
        sentiment = await self.cfgi_service.get_sentiment(asset)
        logger.info(f"[{asset}] CFGI Score: {sentiment['score']}, Signal: {sentiment['signal']}")
        
        # Store sentiment data
        sentiment_doc = SentimentData(
            score=sentiment['score'],
            asset=asset,
            signal=sentiment['signal']
        ).model_dump()
        sentiment_doc['timestamp'] = sentiment_doc['timestamp'].isoformat()
        await self.db.sentiment_history.insert_one(sentiment_doc)
        
        # 2. Check if we should trade
        if sentiment['signal'] == "HOLD":
            logger.info(f"[{asset}] Signal is HOLD, skipping trade")
            return
        
        # 3. Get active market
        market = await self.polymarket_service.get_market_for_asset(asset)
        if not market:
            logger.warning(f"[{asset}] No active market found")
            return
        
        # 4. Check if already traded this market
        market_key = f"{market.condition_id}_{asset}"
        if market_key in self.traded_markets:
            logger.info(f"[{asset}] Already traded market {market.condition_id[:20]}...")
            return
        
        # 5. Determine trade direction
        direction = "UP" if sentiment['signal'] == "BUY_YES" else "DOWN"
        token_id = market.yes_token_id if direction == "UP" else market.no_token_id
        
        # 6. Execute trade
        trade = Trade(
            asset=asset,
            direction=direction,
            market_id=market.condition_id,
            token_id=token_id,
            amount_usdc=self.config.trade_size_usdc,
            entry_price=market.yes_price if direction == "UP" else market.no_price,
            cfgi_score=sentiment['score'],
            status="PENDING"
        )
        
        logger.info(f"[{asset}] Executing {direction} trade: ${self.config.trade_size_usdc} USDC")
        
        result = await self.polymarket_service.place_order(
            token_id=token_id,
            amount_usdc=self.config.trade_size_usdc,
            is_buy=True
        )
        
        if result['success']:
            trade.status = "OPEN"
            trade.tx_hash = result.get('tx_hash')
            trade.entry_price = result.get('executed_price', trade.entry_price)
            self.traded_markets.add(market_key)
            logger.info(f"[{asset}] Trade executed successfully: {trade.id}")
            
            # Send Telegram notification
            if self.config.telegram_enabled and self.config.telegram_chat_id:
                await self.telegram_service.send_trade_alert(
                    chat_id=self.config.telegram_chat_id,
                    asset=asset,
                    direction=direction,
                    amount=self.config.trade_size_usdc,
                    cfgi_score=sentiment['score'],
                    signal=sentiment['signal']
                )
        else:
            trade.status = "CANCELLED"
            trade.error_message = result.get('error_message', 'Order failed')
            logger.error(f"[{asset}] Trade failed: {trade.error_message}")
        
        # 7. Save trade to database
        trade_doc = trade.model_dump()
        trade_doc['timestamp'] = trade_doc['timestamp'].isoformat()
        if trade_doc['closed_at']:
            trade_doc['closed_at'] = trade_doc['closed_at'].isoformat()
        await self.db.trades.insert_one(trade_doc)
        
        # 8. Simulate trade resolution for dry-run
        if self.dry_run and trade.status == "OPEN":
            await self._simulate_trade_resolution(trade)
    
    async def _simulate_trade_resolution(self, trade: Trade):
        """Simulate trade outcome for dry-run mode"""
        # Simulate with 50% win rate for extreme sentiment signals
        is_win = random.random() < 0.55  # Slight edge for extreme sentiment
        
        if is_win:
            trade.exit_price = trade.entry_price + random.uniform(0.05, 0.15)
            trade.status = "WON"
            trade.pnl = trade.amount_usdc * (trade.exit_price - trade.entry_price) / trade.entry_price
        else:
            trade.exit_price = trade.entry_price - random.uniform(0.05, 0.15)
            trade.status = "LOST"
            trade.pnl = -trade.amount_usdc * (trade.entry_price - trade.exit_price) / trade.entry_price
        
        trade.closed_at = datetime.now(timezone.utc)
        
        # Update in database
        update_doc = {
            "exit_price": trade.exit_price,
            "status": trade.status,
            "pnl": trade.pnl,
            "closed_at": trade.closed_at.isoformat()
        }
        await self.db.trades.update_one({"id": trade.id}, {"$set": update_doc})
        
        logger.info(f"[{trade.asset}] Trade resolved: {trade.status} P&L: ${trade.pnl:.2f}")
        
        # Send Telegram notification
        if self.config.telegram_enabled and self.config.telegram_chat_id:
            await self.telegram_service.send_win_loss_alert(
                chat_id=self.config.telegram_chat_id,
                asset=trade.asset,
                direction=trade.direction,
                pnl=trade.pnl,
                is_win=trade.status == "WON"
            )
    
    async def get_stats(self) -> Dict:
        """Get bot statistics"""
        trades = await self.db.trades.find({}, {"_id": 0}).to_list(1000)
        
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
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.cfgi_service.close()
        await self.polymarket_service.close()
        await self.telegram_service.close()
