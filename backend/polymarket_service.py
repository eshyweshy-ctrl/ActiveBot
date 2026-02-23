"""
Polymarket Trading Service
Handles market discovery and order execution for 15-minute crypto direction markets
"""
import os
import logging
import httpx
from typing import Optional, Dict, List
from datetime import datetime, timezone
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CryptoMarket:
    """Represents a Polymarket 15-min crypto direction market"""
    condition_id: str
    question: str
    yes_token_id: str
    no_token_id: str
    yes_price: float
    no_price: float
    volume_24h: float
    is_active: bool
    asset: str  # BTC, ETH, SOL

class PolymarketService:
    """Service for interacting with Polymarket"""
    
    GAMMA_HOST = "https://gamma-api.polymarket.com"
    CLOB_HOST = "https://clob.polymarket.com"
    
    def __init__(self, private_key: Optional[str] = None):
        self.private_key = private_key or os.environ.get("POLYMARKET_PRIVATE_KEY", "")
        self.client = httpx.AsyncClient(timeout=30.0)
        self._api_creds = None
    
    async def fetch_15min_crypto_markets(self) -> List[CryptoMarket]:
        """Fetch active 15-minute crypto direction markets"""
        try:
            url = f"{self.GAMMA_HOST}/markets"
            params = {
                "active": "true",
                "closed": "false",
                "limit": 500
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            all_markets = response.json()
            crypto_markets = []
            
            for market in all_markets:
                question = market.get("question", "").lower()
                
                # Identify 15-minute crypto markets
                is_15min = "15" in question and ("minute" in question or "min" in question)
                
                # Check for specific assets
                asset = None
                if any(term in question for term in ["bitcoin", "btc"]):
                    asset = "BTC"
                elif any(term in question for term in ["ethereum", "eth"]):
                    asset = "ETH"
                elif any(term in question for term in ["solana", "sol"]):
                    asset = "SOL"
                
                if is_15min and asset and market.get("enableOrderBook"):
                    token_ids = market.get("clobTokenIds", [])
                    if len(token_ids) >= 2:
                        outcomes = market.get("outcomePrices", [0.5, 0.5])
                        crypto_markets.append(CryptoMarket(
                            condition_id=market.get("conditionId", ""),
                            question=market.get("question", ""),
                            yes_token_id=token_ids[0],
                            no_token_id=token_ids[1],
                            yes_price=float(outcomes[0]) if outcomes else 0.5,
                            no_price=float(outcomes[1]) if len(outcomes) > 1 else 0.5,
                            volume_24h=float(market.get("volume24h", 0)),
                            is_active=market.get("active", False),
                            asset=asset
                        ))
            
            logger.info(f"Found {len(crypto_markets)} 15-minute crypto markets")
            return crypto_markets
            
        except Exception as e:
            logger.error(f"Failed to fetch markets: {e}")
            return []
    
    async def get_market_for_asset(self, asset: str) -> Optional[CryptoMarket]:
        """Get the current active 15-min market for a specific asset"""
        markets = await self.fetch_15min_crypto_markets()
        for market in markets:
            if market.asset == asset and market.is_active:
                return market
        return None
    
    async def place_order(
        self, 
        token_id: str, 
        amount_usdc: float, 
        is_buy: bool = True
    ) -> Dict:
        """
        Place a market order on Polymarket
        
        In production, this would use the py-clob-client SDK
        For now, returns simulated result
        """
        logger.info(f"Placing order: {'BUY' if is_buy else 'SELL'} {amount_usdc} USDC on token {token_id[:20]}...")
        
        # In production, this would execute via:
        # from py_clob_client.client import ClobClient
        # client = ClobClient(self.CLOB_HOST, 137, key=self.private_key)
        # market_order = client.createMarketOrder(...)
        # response = client.postOrder(market_order, OrderType.FOK)
        
        # Simulated response for dry-run
        return {
            "success": True,
            "order_id": f"sim_{datetime.now(timezone.utc).timestamp()}",
            "status": "matched",
            "executed_price": 0.5,
            "tx_hash": None,
            "simulated": True
        }
    
    async def get_order_book(self, token_id: str) -> Dict:
        """Get current order book for a token"""
        try:
            url = f"{self.CLOB_HOST}/book"
            params = {"token_id": token_id}
            
            response = await self.client.get(url, params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to fetch orderbook: {response.status_code}")
                return {"bids": [], "asks": []}
                
        except Exception as e:
            logger.error(f"Error fetching orderbook: {e}")
            return {"bids": [], "asks": []}
    
    async def close(self):
        await self.client.aclose()


class SimulatedPolymarketService:
    """Simulated Polymarket service for dry-run testing"""
    
    def __init__(self):
        self._markets = self._generate_fake_markets()
        self._trade_counter = 0
    
    def _generate_fake_markets(self) -> List[CryptoMarket]:
        """Generate simulated markets for testing"""
        assets = ["BTC", "ETH", "SOL"]
        markets = []
        
        for asset in assets:
            markets.append(CryptoMarket(
                condition_id=f"sim_cond_{asset.lower()}",
                question=f"Will {asset} price go up in the next 15 minutes?",
                yes_token_id=f"sim_yes_{asset.lower()}",
                no_token_id=f"sim_no_{asset.lower()}",
                yes_price=0.52,
                no_price=0.48,
                volume_24h=100000,
                is_active=True,
                asset=asset
            ))
        
        return markets
    
    async def fetch_15min_crypto_markets(self) -> List[CryptoMarket]:
        return self._markets
    
    async def get_market_for_asset(self, asset: str) -> Optional[CryptoMarket]:
        for market in self._markets:
            if market.asset == asset:
                return market
        return None
    
    async def place_order(
        self, 
        token_id: str, 
        amount_usdc: float, 
        is_buy: bool = True
    ) -> Dict:
        """Simulate order placement"""
        self._trade_counter += 1
        
        # Simulate random success (90% success rate)
        import random
        success = random.random() < 0.9
        
        # Simulate price slightly different from midpoint
        executed_price = 0.5 + random.uniform(-0.05, 0.05)
        
        return {
            "success": success,
            "order_id": f"sim_order_{self._trade_counter}",
            "status": "matched" if success else "failed",
            "executed_price": round(executed_price, 4),
            "tx_hash": f"0xsim_{self._trade_counter:08x}" if success else None,
            "simulated": True,
            "error_message": None if success else "Simulated failure"
        }
    
    async def get_order_book(self, token_id: str) -> Dict:
        """Return simulated orderbook"""
        return {
            "bids": [{"price": "0.49", "size": "1000"}, {"price": "0.48", "size": "2000"}],
            "asks": [{"price": "0.51", "size": "1500"}, {"price": "0.52", "size": "2500"}]
        }
    
    async def close(self):
        pass
