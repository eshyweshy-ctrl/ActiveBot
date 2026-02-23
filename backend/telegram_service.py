"""
Telegram Notification Service - Enhanced for ACTIVEBOT
"""
import os
import logging
import httpx
from typing import Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class TelegramService:
    """Service for sending Telegram notifications"""
    
    def __init__(self, bot_token: Optional[str] = None):
        self.bot_token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def send_message(self, chat_id: str, message: str, parse_mode: str = "HTML") -> bool:
        """Send a message to a Telegram chat"""
        if not self.bot_token:
            logger.warning("No Telegram bot token configured")
            return False
        
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            
            response = await self.client.post(url, json=payload)
            
            if response.status_code == 200:
                logger.info(f"Telegram message sent to {chat_id}")
                return True
            else:
                logger.error(f"Telegram API error: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
    
    async def send_trade_alert(
        self, 
        chat_id: str,
        asset: str,
        direction: str,
        amount: float,
        cfgi_score: int,
        signal: str,
        entry_price: float = 0,
        market_id: str = ""
    ) -> bool:
        """Send a formatted trade alert when entering a position"""
        
        direction_emoji = "📈" if direction == "UP" else "📉"
        
        # Determine sentiment description
        if cfgi_score <= 19:
            sentiment = "🔴 EXTREME FEAR"
        elif cfgi_score >= 80:
            sentiment = "🟢 EXTREME GREED"
        else:
            sentiment = "⚪ NEUTRAL"
        
        timestamp = datetime.now(timezone.utc).strftime("%H:%M UTC")
        
        message = f"""
{direction_emoji} <b>NEW TRADE OPENED</b> {direction_emoji}

<b>Asset:</b> {asset}
<b>Direction:</b> {"UP (YES)" if direction == "UP" else "DOWN (NO)"}
<b>Amount:</b> ${amount:.2f} USDC
<b>Entry Price:</b> {entry_price:.4f}

<b>CFGI Score:</b> {cfgi_score}/100
<b>Sentiment:</b> {sentiment}

<b>Time:</b> {timestamp}
<code>Market: {market_id[:20]}...</code>

<i>15-min market - Result in ~15 minutes</i>
"""
        return await self.send_message(chat_id, message)
    
    async def send_trade_result(
        self,
        chat_id: str,
        asset: str,
        direction: str,
        amount: float,
        entry_price: float,
        exit_price: float,
        pnl: float,
        is_win: bool,
        cfgi_score: int,
        total_pnl: float = 0,
        win_rate: float = 0,
        total_trades: int = 0
    ) -> bool:
        """Send detailed trade result with summary stats"""
        
        result_emoji = "✅" if is_win else "❌"
        result_text = "WIN" if is_win else "LOSS"
        pnl_emoji = "💰" if pnl >= 0 else "💸"
        pnl_text = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
        total_pnl_text = f"+${total_pnl:.2f}" if total_pnl >= 0 else f"-${abs(total_pnl):.2f}"
        
        timestamp = datetime.now(timezone.utc).strftime("%H:%M UTC")
        
        message = f"""
{result_emoji} <b>TRADE RESULT: {result_text}</b> {result_emoji}

<b>Asset:</b> {asset}
<b>Direction:</b> {"UP (YES)" if direction == "UP" else "DOWN (NO)"}
<b>Amount:</b> ${amount:.2f} USDC
<b>CFGI at Entry:</b> {cfgi_score}/100

<b>Entry:</b> {entry_price:.4f}
<b>Exit:</b> {exit_price:.4f}
{pnl_emoji} <b>P&L:</b> {pnl_text}

━━━━━━━━━━━━━━━━━━
📊 <b>SESSION SUMMARY</b>
━━━━━━━━━━━━━━━━━━
<b>Total Trades:</b> {total_trades}
<b>Win Rate:</b> {win_rate:.1f}%
<b>Total P&L:</b> {total_pnl_text}
<b>Time:</b> {timestamp}
"""
        return await self.send_message(chat_id, message)
    
    async def send_cycle_update(
        self,
        chat_id: str,
        sentiments: dict,
        next_cycle_mins: int = 15
    ) -> bool:
        """Send a cycle update with current sentiment readings"""
        
        timestamp = datetime.now(timezone.utc).strftime("%H:%M UTC")
        
        lines = []
        for asset, data in sentiments.items():
            score = data.get('score', 50)
            signal = data.get('signal', 'HOLD')
            
            if signal == "BUY_YES":
                emoji = "🟢"
                action = "BUY YES"
            elif signal == "BUY_NO":
                emoji = "🔴"
                action = "BUY NO"
            else:
                emoji = "⚪"
                action = "HOLD"
            
            lines.append(f"{emoji} <b>{asset}:</b> {score}/100 → {action}")
        
        sentiment_text = "\n".join(lines)
        
        message = f"""
🔄 <b>SENTIMENT CHECK</b> - {timestamp}

{sentiment_text}

<i>Next check in {next_cycle_mins} minutes</i>
"""
        return await self.send_message(chat_id, message)
    
    async def send_bot_started(self, chat_id: str, config: dict) -> bool:
        """Send notification when bot starts"""
        
        assets = ", ".join(config.get('assets_enabled', ['BTC', 'ETH', 'SOL']))
        trade_size = config.get('trade_size_usdc', 1)
        mode = "🔴 LIVE" if not config.get('dry_run_mode', True) else "🟡 DRY RUN"
        
        message = f"""
🤖 <b>ACTIVEBOT STARTED</b>

<b>Mode:</b> {mode}
<b>Trade Size:</b> ${trade_size} USDC
<b>Assets:</b> {assets}
<b>Timeframe:</b> 15 minutes

<b>Trading Rules:</b>
• CFGI 0-19 (Extreme Fear) → BUY YES
• CFGI 80-100 (Extreme Greed) → BUY NO
• CFGI 20-79 → HOLD

<i>Monitoring started. You'll receive alerts on trades.</i>
"""
        return await self.send_message(chat_id, message)
    
    async def send_bot_stopped(self, chat_id: str) -> bool:
        """Send notification when bot stops"""
        message = "🛑 <b>ACTIVEBOT STOPPED</b>\n\n<i>Trading paused. No new positions will be opened.</i>"
        return await self.send_message(chat_id, message)
    
    async def test_connection(self, chat_id: str) -> bool:
        """Test Telegram connection by sending a test message"""
        message = """
🤖 <b>ACTIVEBOT Connected!</b>

✅ Telegram alerts configured successfully.

You will receive:
• Trade entry alerts
• Win/Loss results with P&L
• Session summaries

<i>Ready to trade!</i>
"""
        return await self.send_message(chat_id, message)
    
    async def close(self):
        await self.client.aclose()
