"""
Telegram Notification Service
"""
import os
import logging
import httpx
from typing import Optional

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
        signal: str
    ) -> bool:
        """Send a formatted trade alert"""
        
        direction_emoji = "📈" if direction == "UP" else "📉"
        signal_emoji = "🟢" if signal == "BUY_YES" else "🔴" if signal == "BUY_NO" else "⚪"
        
        message = f"""
{direction_emoji} <b>ACTIVEBOT TRADE ALERT</b> {direction_emoji}

<b>Asset:</b> {asset}
<b>Direction:</b> {direction}
<b>Amount:</b> ${amount:.2f} USDC
<b>CFGI Score:</b> {cfgi_score} {signal_emoji}
<b>Signal:</b> {signal}

<i>Trade executed automatically based on extreme sentiment.</i>
"""
        return await self.send_message(chat_id, message)
    
    async def send_win_loss_alert(
        self,
        chat_id: str,
        asset: str,
        direction: str,
        pnl: float,
        is_win: bool
    ) -> bool:
        """Send win/loss notification"""
        
        result_emoji = "🎉" if is_win else "😔"
        result_text = "WIN" if is_win else "LOSS"
        pnl_text = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
        
        message = f"""
{result_emoji} <b>TRADE RESULT: {result_text}</b> {result_emoji}

<b>Asset:</b> {asset}
<b>Direction:</b> {direction}
<b>P&L:</b> {pnl_text}
"""
        return await self.send_message(chat_id, message)
    
    async def test_connection(self, chat_id: str) -> bool:
        """Test Telegram connection by sending a test message"""
        message = "🤖 <b>ACTIVEBOT</b>\n\nConnection test successful! You will receive trade alerts here."
        return await self.send_message(chat_id, message)
    
    async def close(self):
        await self.client.aclose()
