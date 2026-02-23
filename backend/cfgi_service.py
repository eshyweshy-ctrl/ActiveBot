"""
CFGI.io Sentiment Data Service
"""
import os
import logging
import httpx
from typing import Optional, Dict
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class CFGIService:
    """Service to fetch Crypto Fear & Greed Index data from CFGI.io"""
    
    BASE_URL = "https://cfgi.io/api"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("CFGI_API_KEY", "")
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_sentiment(self, asset: str = "BTC") -> Dict:
        """
        Fetch current sentiment for an asset
        
        Returns:
            Dict with score, signal, and timestamp
        """
        try:
            # CFGI.io API endpoint structure
            # For now, we'll use a fallback to the main Fear & Greed index
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Try the multi-asset endpoint
            url = f"{self.BASE_URL}/sentiment/{asset.lower()}"
            
            response = await self.client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                score = data.get("value", data.get("score", 50))
                return {
                    "score": int(score),
                    "asset": asset,
                    "timestamp": datetime.now(timezone.utc),
                    "signal": self._determine_signal(int(score))
                }
            else:
                logger.warning(f"CFGI API returned {response.status_code}, using fallback")
                return await self._get_alternative_sentiment(asset)
                
        except Exception as e:
            logger.error(f"Error fetching CFGI data: {e}")
            return await self._get_alternative_sentiment(asset)
    
    async def _get_alternative_sentiment(self, asset: str) -> Dict:
        """
        Fallback to Alternative.me Fear & Greed Index API (free, no key needed)
        """
        try:
            url = "https://api.alternative.me/fng/?limit=1"
            response = await self.client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                fng_data = data.get("data", [{}])[0]
                score = int(fng_data.get("value", 50))
                
                return {
                    "score": score,
                    "asset": asset,
                    "timestamp": datetime.now(timezone.utc),
                    "signal": self._determine_signal(score)
                }
        except Exception as e:
            logger.error(f"Alternative API also failed: {e}")
        
        # Return neutral if all fails
        return {
            "score": 50,
            "asset": asset,
            "timestamp": datetime.now(timezone.utc),
            "signal": "HOLD"
        }
    
    def _determine_signal(self, score: int) -> str:
        """
        Determine trading signal based on CFGI score
        
        0-19: EXTREME FEAR → BUY_YES (price will go UP)
        80-100: EXTREME GREED → BUY_NO (price will go DOWN)
        20-79: No trade
        """
        if score <= 19:
            return "BUY_YES"
        elif score >= 80:
            return "BUY_NO"
        else:
            return "HOLD"
    
    async def close(self):
        await self.client.aclose()


# Simulated sentiment for dry-run testing
class SimulatedCFGIService:
    """Simulated CFGI service for testing"""
    
    def __init__(self):
        self._simulated_score = 50
        self._mode = "neutral"  # neutral, fear, greed
    
    def set_simulated_score(self, score: int):
        self._simulated_score = max(0, min(100, score))
    
    def set_mode(self, mode: str):
        """Set mode: 'fear' (0-19), 'greed' (80-100), 'neutral' (50)"""
        self._mode = mode
        if mode == "fear":
            self._simulated_score = 10
        elif mode == "greed":
            self._simulated_score = 90
        else:
            self._simulated_score = 50
    
    async def get_sentiment(self, asset: str = "BTC") -> Dict:
        score = self._simulated_score
        signal = "HOLD"
        if score <= 19:
            signal = "BUY_YES"
        elif score >= 80:
            signal = "BUY_NO"
            
        return {
            "score": score,
            "asset": asset,
            "timestamp": datetime.now(timezone.utc),
            "signal": signal
        }
    
    async def close(self):
        pass
