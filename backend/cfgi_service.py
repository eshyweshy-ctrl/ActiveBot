"""
CFGI.io Sentiment Data Service - Using Web Scraping for Real Data
"""
import os
import logging
import httpx
import re
from typing import Optional, Dict
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class CFGIService:
    """Service to fetch Crypto Fear & Greed Index data from CFGI.io"""
    
    # Map asset symbols to CFGI.io page URLs
    ASSET_URLS = {
        "BTC": "https://cfgi.io/bitcoin-fear-greed-index/",
        "ETH": "https://cfgi.io/ethereum-fear-greed-index/",
        "SOL": "https://cfgi.io/solana-fear-greed-index/"
    }
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("CFGI_API_KEY", "")
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        self._cache = {}
        self._cache_time = {}
        self._cache_ttl = 60  # Cache for 60 seconds
    
    async def get_sentiment(self, asset: str = "BTC") -> Dict:
        """
        Fetch current sentiment for an asset from CFGI.io
        
        Returns:
            Dict with score, signal, and timestamp
        """
        # Check cache
        cache_key = f"{asset}_sentiment"
        if cache_key in self._cache:
            cache_age = (datetime.now(timezone.utc) - self._cache_time[cache_key]).total_seconds()
            if cache_age < self._cache_ttl:
                return self._cache[cache_key]
        
        try:
            # Try to scrape CFGI.io page for the asset
            if asset in self.ASSET_URLS:
                score = await self._scrape_cfgi_page(asset)
                if score is not None:
                    result = {
                        "score": score,
                        "asset": asset,
                        "timestamp": datetime.now(timezone.utc),
                        "signal": self._determine_signal(score),
                        "source": "CFGI.io"
                    }
                    self._cache[cache_key] = result
                    self._cache_time[cache_key] = datetime.now(timezone.utc)
                    return result
            
            # Fallback to Alternative.me
            logger.warning(f"Could not scrape CFGI.io for {asset}, using fallback")
            return await self._get_alternative_sentiment(asset)
                
        except Exception as e:
            logger.error(f"Error fetching CFGI data: {e}")
            return await self._get_alternative_sentiment(asset)
    
    async def _scrape_cfgi_page(self, asset: str) -> Optional[int]:
        """
        Scrape the CFGI.io page to get the current fear & greed score
        """
        try:
            url = self.ASSET_URLS.get(asset)
            if not url:
                return None
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }
            
            response = await self.client.get(url, headers=headers)
            
            if response.status_code == 200:
                html = response.text
                
                # Primary pattern: Look for value__score class with the actual score number
                # Example: value__score cfgi-color cfgi-color-bg">37
                primary_patterns = [
                    r'value__score[^>]*>(\d+)',
                    r'cfgi-color-bg">(\d+)',
                    r'class="[^"]*score[^"]*"[^>]*>(\d+)',
                ]
                
                for pattern in primary_patterns:
                    match = re.search(pattern, html, re.IGNORECASE)
                    if match:
                        score = int(match.group(1))
                        if 0 <= score <= 100:
                            logger.info(f"CFGI.io scraped score for {asset}: {score} (1D timeframe)")
                            return score
                
                # Fallback patterns
                fallback_patterns = [
                    r'Now\s*(?:Extreme Fear|Fear|Neutral|Greed|Extreme Greed)\s*(\d+)',
                    r'Now[^0-9]*(\d{1,2})',
                ]
                
                for pattern in fallback_patterns:
                    match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
                    if match:
                        score = int(match.group(1))
                        if 0 <= score <= 100:
                            logger.info(f"CFGI.io fallback score for {asset}: {score}")
                            return score
                
                logger.warning(f"Could not find score on CFGI.io page for {asset}")
                return None
            else:
                logger.warning(f"CFGI.io returned status {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error scraping CFGI.io: {e}")
            return None
    
    async def _get_alternative_sentiment(self, asset: str) -> Dict:
        """
        Fallback to Alternative.me Fear & Greed Index API (free, no key needed)
        Note: This only provides overall crypto sentiment, not per-asset
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
                    "signal": self._determine_signal(score),
                    "source": "Alternative.me (fallback)"
                }
        except Exception as e:
            logger.error(f"Alternative API also failed: {e}")
        
        # Return neutral if all fails
        return {
            "score": 50,
            "asset": asset,
            "timestamp": datetime.now(timezone.utc),
            "signal": "HOLD",
            "source": "default"
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
            "signal": signal,
            "source": "simulated"
        }
    
    async def close(self):
        pass
