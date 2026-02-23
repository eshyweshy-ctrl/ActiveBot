"""
Polymarket Trading Service
Handles market discovery and order execution for 15-minute crypto direction markets.

Market Discovery Logic:
- 15-minute markets use dynamic slugs: {asset}-updown-15m-{unix_timestamp}
- The timestamp represents the START of the 15-minute trading window
- Markets are discovered via: https://gamma-api.polymarket.com/events?slug={slug}
"""
import os
import logging
import httpx
import json
from typing import Optional, Dict, List
from datetime import datetime, timezone
from dataclasses import dataclass
import random

logger = logging.getLogger(__name__)

@dataclass
class CryptoMarket:
    """Represents a Polymarket 15-min crypto direction market"""
    condition_id: str
    question: str
    yes_token_id: str  # "Up" outcome
    no_token_id: str   # "Down" outcome
    yes_price: float   # Price for "Up" 
    no_price: float    # Price for "Down"
    volume_24h: float
    is_active: bool
    asset: str  # BTC, ETH, SOL
    slug: str
    end_time: Optional[datetime] = None
    accepting_orders: bool = True


class PolymarketService:
    """Service for interacting with Polymarket - LIVE TRADING
    
    Uses the Gamma API to discover 15-minute crypto markets and
    the CLOB API for order execution.
    """
    
    GAMMA_HOST = "https://gamma-api.polymarket.com"
    CLOB_HOST = "https://clob.polymarket.com"
    CHAIN_ID = 137  # Polygon mainnet
    
    # Asset mappings for slug generation
    ASSET_SLUG_MAP = {
        "BTC": "btc",
        "ETH": "eth",
        "SOL": "sol"
    }
    
    def __init__(self, private_key: Optional[str] = None):
        self.private_key = private_key or os.environ.get("POLYMARKET_PRIVATE_KEY", "")
        # Use explicit wallet address if provided (for cases where PK doesn't match trading wallet)
        self.wallet_address = os.environ.get("POLYMARKET_WALLET_ADDRESS", "")
        # API credentials for CLOB
        self.api_key = os.environ.get("POLYMARKET_API_KEY", "")
        self.api_secret = os.environ.get("POLYMARKET_API_SECRET", "")
        self.api_passphrase = os.environ.get("POLYMARKET_API_PASSPHRASE", "")
        self.client = httpx.AsyncClient(timeout=30.0)
        self._clob_client = None
        self._initialized = False
    
    def _get_current_15min_timestamp(self) -> int:
        """Calculate the Unix timestamp for the current 15-minute window start"""
        now = datetime.now(timezone.utc)
        # Round down to nearest 15-minute boundary
        base_minute = (now.minute // 15) * 15
        current_window = now.replace(minute=base_minute, second=0, microsecond=0)
        return int(current_window.timestamp())
    
    def _generate_market_slug(self, asset: str, timestamp: Optional[int] = None) -> str:
        """Generate the market slug for a given asset and timestamp
        
        Slug format: {asset}-updown-15m-{unix_timestamp}
        Example: btc-updown-15m-1771858800
        """
        if timestamp is None:
            timestamp = self._get_current_15min_timestamp()
        
        asset_prefix = self.ASSET_SLUG_MAP.get(asset.upper(), asset.lower())
        return f"{asset_prefix}-updown-15m-{timestamp}"
    
    async def _init_clob_client(self):
        """Initialize the CLOB client for trading"""
        if self._initialized:
            return
        
        try:
            from py_clob_client.client import ClobClient
            
            # Initialize CLOB client
            self._clob_client = ClobClient(
                self.CLOB_HOST,
                key=self.private_key,
                chain_id=self.CHAIN_ID
            )
            
            # Derive API credentials
            self._clob_client.set_api_creds(self._clob_client.derive_api_key())
            
            self._initialized = True
            logger.info("Polymarket CLOB client initialized successfully")
            
        except ImportError as e:
            logger.error(f"py-clob-client not installed: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize CLOB client: {e}")
            raise
    
    async def get_market_for_asset(self, asset: str) -> Optional[CryptoMarket]:
        """Get the current active 15-min market for a specific asset
        
        Uses the dynamic slug pattern to find the market for the current
        15-minute window.
        """
        try:
            # Generate the expected slug for current 15-min window
            slug = self._generate_market_slug(asset)
            logger.info(f"[{asset}] Looking for market with slug: {slug}")
            
            # Query the Gamma API for this specific event
            url = f"{self.GAMMA_HOST}/events"
            params = {"slug": slug}
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            events = response.json()
            
            if not events:
                logger.warning(f"[{asset}] No market found for slug: {slug}")
                # Try previous 15-min window as fallback
                prev_timestamp = self._get_current_15min_timestamp() - 900  # 15 mins ago
                prev_slug = self._generate_market_slug(asset, prev_timestamp)
                logger.info(f"[{asset}] Trying previous window: {prev_slug}")
                
                response = await self.client.get(url, params={"slug": prev_slug})
                events = response.json()
                
                if not events:
                    logger.warning(f"[{asset}] No market found for previous window either")
                    return None
            
            event = events[0]
            markets = event.get("markets", [])
            
            if not markets:
                logger.warning(f"[{asset}] Event found but no markets inside")
                return None
            
            market = markets[0]
            
            # Check if market is accepting orders
            if not market.get("acceptingOrders", False):
                logger.warning(f"[{asset}] Market is not accepting orders")
                return None
            
            # Parse token IDs from the clobTokenIds field (JSON string)
            token_ids_str = market.get("clobTokenIds", "[]")
            try:
                token_ids = json.loads(token_ids_str)
            except json.JSONDecodeError:
                token_ids = []
            
            if len(token_ids) < 2:
                logger.warning(f"[{asset}] Market missing token IDs")
                return None
            
            # Parse outcome prices
            prices_str = market.get("outcomePrices", "[0.5, 0.5]")
            try:
                prices = json.loads(prices_str)
            except json.JSONDecodeError:
                prices = [0.5, 0.5]
            
            # Parse end time
            end_time = None
            if market.get("endDate"):
                try:
                    end_time = datetime.fromisoformat(market["endDate"].replace("Z", "+00:00"))
                except:
                    pass
            
            crypto_market = CryptoMarket(
                condition_id=market.get("conditionId", ""),
                question=market.get("question", ""),
                yes_token_id=token_ids[0],  # "Up" token
                no_token_id=token_ids[1],    # "Down" token
                yes_price=float(prices[0]) if prices else 0.5,
                no_price=float(prices[1]) if len(prices) > 1 else 0.5,
                volume_24h=float(market.get("volume24hr", 0) or market.get("volumeNum", 0)),
                is_active=market.get("active", False),
                asset=asset.upper(),
                slug=market.get("slug", slug),
                end_time=end_time,
                accepting_orders=market.get("acceptingOrders", True)
            )
            
            logger.info(f"[{asset}] Found market: {crypto_market.question}")
            logger.info(f"[{asset}] Up price: {crypto_market.yes_price}, Down price: {crypto_market.no_price}")
            
            return crypto_market
            
        except httpx.HTTPStatusError as e:
            logger.error(f"[{asset}] HTTP error fetching market: {e}")
            return None
        except Exception as e:
            logger.error(f"[{asset}] Error fetching market: {e}", exc_info=True)
            return None
    
    async def fetch_15min_crypto_markets(self) -> List[CryptoMarket]:
        """Fetch all active 15-minute crypto direction markets for supported assets"""
        markets = []
        
        for asset in self.ASSET_SLUG_MAP.keys():
            market = await self.get_market_for_asset(asset)
            if market:
                markets.append(market)
        
        logger.info(f"Found {len(markets)} active 15-minute crypto markets")
        return markets
    
    async def place_order(
        self, 
        token_id: str, 
        amount_usdc: float, 
        is_buy: bool = True
    ) -> Dict:
        """
        Place a market order on Polymarket
        
        Uses py-clob-client for real order execution.
        For 15-min markets:
        - Buying "Up" token = betting price will go UP
        - Buying "Down" token = betting price will go DOWN
        """
        logger.info(f"[LIVE] Placing order: {'BUY' if is_buy else 'SELL'} {amount_usdc} USDC on token {token_id[:30]}...")
        
        try:
            await self._init_clob_client()
            
            from py_clob_client.clob_types import OrderArgs, OrderType
            from py_clob_client.order_builder.constants import BUY, SELL
            
            # Get current price from orderbook
            orderbook = await self.get_order_book(token_id)
            
            # For market buy, use best ask price
            if is_buy and orderbook.get('asks'):
                price = float(orderbook['asks'][0]['price'])
            elif not is_buy and orderbook.get('bids'):
                price = float(orderbook['bids'][0]['price'])
            else:
                price = 0.5  # Default midpoint
            
            # Ensure price is within valid range
            price = max(0.01, min(0.99, price))
            
            # Calculate size based on USDC amount and price
            size = amount_usdc / price
            
            logger.info(f"[LIVE] Order details: price={price}, size={size}")
            
            # Create market order
            order_args = OrderArgs(
                token_id=token_id,
                price=price,
                size=size,
                side=BUY if is_buy else SELL
            )
            
            # Build and sign the order
            signed_order = self._clob_client.create_order(order_args)
            
            # Submit order as FOK (Fill-Or-Kill) for market execution
            response = self._clob_client.post_order(signed_order, OrderType.FOK)
            
            if response and response.get('success'):
                logger.info(f"[LIVE] Order executed successfully: {response}")
                return {
                    "success": True,
                    "order_id": response.get('orderID', ''),
                    "status": "matched",
                    "executed_price": price,
                    "tx_hash": response.get('transactionsHashes', [None])[0],
                    "simulated": False
                }
            else:
                error_msg = response.get('errorMsg', 'Unknown error') if response else 'No response'
                logger.error(f"[LIVE] Order failed: {error_msg}")
                return {
                    "success": False,
                    "order_id": None,
                    "status": "failed",
                    "executed_price": 0,
                    "tx_hash": None,
                    "simulated": False,
                    "error_message": error_msg
                }
                
        except Exception as e:
            logger.error(f"[LIVE] Order execution error: {e}", exc_info=True)
            return {
                "success": False,
                "order_id": None,
                "status": "error",
                "executed_price": 0,
                "tx_hash": None,
                "simulated": False,
                "error_message": str(e)
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
    
    async def check_connection(self) -> Dict:
        """Check connection to Polymarket APIs"""
        result = {
            "gamma_api": False,
            "clob_api": False,
            "wallet_connected": False,
            "error": None
        }
        
        try:
            # Test Gamma API
            response = await self.client.get(f"{self.GAMMA_HOST}/events?limit=1")
            result["gamma_api"] = response.status_code == 200
            
            # Test CLOB API
            response = await self.client.get(f"{self.CLOB_HOST}/time")
            result["clob_api"] = response.status_code == 200
            
            # Check if private key is set
            result["wallet_connected"] = bool(self.private_key and len(self.private_key) > 10)
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def get_wallet_address(self) -> Optional[str]:
        """Get the wallet address - uses explicit address if set, otherwise derives from PK"""
        # Prefer explicit wallet address from env
        if self.wallet_address and len(self.wallet_address) > 10:
            return self.wallet_address
        
        # Fall back to deriving from private key
        if not self.private_key or len(self.private_key) < 10:
            return None
        
        try:
            from eth_account import Account
            account = Account.from_key(self.private_key)
            return account.address
        except Exception as e:
            logger.error(f"Error deriving wallet address: {e}")
            return None
    
    async def get_wallet_info(self) -> Dict:
        """Get wallet information including address and balances"""
        wallet_address = self.get_wallet_address()
        
        result = {
            "address": wallet_address,
            "address_short": f"{wallet_address[:6]}...{wallet_address[-4:]}" if wallet_address else None,
            "usdc_balance": 0.0,
            "matic_balance": 0.0,
            "positions_value": 0.0,
            "total_value": 0.0,
            "error": None
        }
        
        if not wallet_address:
            result["error"] = "No wallet configured"
            return result
        
        try:
            # Get USDC balance from Data API
            data_api = "https://data-api.polymarket.com"
            
            # Try to get positions value
            try:
                response = await self.client.get(
                    f"{data_api}/value",
                    params={"user": wallet_address}
                )
                if response.status_code == 200:
                    data = response.json()
                    result["positions_value"] = float(data.get("value", 0))
            except:
                pass
            
            # Get USDC balance from polygon RPC
            try:
                # Use a reliable public RPC
                rpc_url = "https://polygon-mainnet.g.alchemy.com/v2/demo"
                usdc_contract = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"  # USDC on Polygon
                
                # Simple balance check using eth_call
                # balanceOf(address) selector: 0x70a08231
                call_data = f"0x70a08231000000000000000000000000{wallet_address[2:].lower()}"
                
                payload = {
                    "jsonrpc": "2.0",
                    "method": "eth_call",
                    "params": [{"to": usdc_contract, "data": call_data}, "latest"],
                    "id": 1
                }
                
                response = await self.client.post(rpc_url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    if "result" in data and data["result"] != "0x":
                        balance_wei = int(data["result"], 16)
                        result["usdc_balance"] = balance_wei / 1e6  # USDC has 6 decimals
            except Exception as e:
                logger.warning(f"Could not fetch USDC balance: {e}")
            
            # Get MATIC balance
            try:
                rpc_url = "https://polygon-mainnet.g.alchemy.com/v2/demo"
                payload = {
                    "jsonrpc": "2.0",
                    "method": "eth_getBalance",
                    "params": [wallet_address, "latest"],
                    "id": 1
                }
                
                response = await self.client.post(rpc_url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    if "result" in data:
                        balance_wei = int(data["result"], 16)
                        result["matic_balance"] = balance_wei / 1e18
            except Exception as e:
                logger.warning(f"Could not fetch MATIC balance: {e}")
            
            result["total_value"] = result["usdc_balance"] + result["positions_value"]
            
        except Exception as e:
            logger.error(f"Error getting wallet info: {e}")
            result["error"] = str(e)
        
        return result
    
    async def close(self):
        await self.client.aclose()


class SimulatedPolymarketService:
    """Simulated Polymarket service for dry-run testing
    
    Uses the same market discovery logic but simulates order execution.
    """
    
    GAMMA_HOST = "https://gamma-api.polymarket.com"
    ASSET_SLUG_MAP = {"BTC": "btc", "ETH": "eth", "SOL": "sol"}
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self._trade_counter = 0
    
    def _get_current_15min_timestamp(self) -> int:
        """Calculate the Unix timestamp for the current 15-minute window start"""
        now = datetime.now(timezone.utc)
        base_minute = (now.minute // 15) * 15
        current_window = now.replace(minute=base_minute, second=0, microsecond=0)
        return int(current_window.timestamp())
    
    def _generate_market_slug(self, asset: str, timestamp: Optional[int] = None) -> str:
        if timestamp is None:
            timestamp = self._get_current_15min_timestamp()
        asset_prefix = self.ASSET_SLUG_MAP.get(asset.upper(), asset.lower())
        return f"{asset_prefix}-updown-15m-{timestamp}"
    
    async def get_market_for_asset(self, asset: str) -> Optional[CryptoMarket]:
        """Get real market data but will simulate trades"""
        try:
            slug = self._generate_market_slug(asset)
            logger.info(f"[DRY-RUN] [{asset}] Looking for market: {slug}")
            
            url = f"{self.GAMMA_HOST}/events"
            response = await self.client.get(url, params={"slug": slug})
            
            if response.status_code != 200:
                logger.warning(f"[DRY-RUN] [{asset}] API returned {response.status_code}")
                return self._generate_simulated_market(asset)
            
            events = response.json()
            
            if not events:
                # Try previous window
                prev_ts = self._get_current_15min_timestamp() - 900
                prev_slug = self._generate_market_slug(asset, prev_ts)
                response = await self.client.get(url, params={"slug": prev_slug})
                events = response.json()
            
            if not events:
                logger.info(f"[DRY-RUN] [{asset}] No real market found, using simulated")
                return self._generate_simulated_market(asset)
            
            event = events[0]
            markets = event.get("markets", [])
            
            if not markets:
                return self._generate_simulated_market(asset)
            
            market = markets[0]
            token_ids = json.loads(market.get("clobTokenIds", "[]"))
            prices = json.loads(market.get("outcomePrices", "[0.5, 0.5]"))
            
            if len(token_ids) < 2:
                return self._generate_simulated_market(asset)
            
            return CryptoMarket(
                condition_id=market.get("conditionId", ""),
                question=market.get("question", ""),
                yes_token_id=token_ids[0],
                no_token_id=token_ids[1],
                yes_price=float(prices[0]) if prices else 0.5,
                no_price=float(prices[1]) if len(prices) > 1 else 0.5,
                volume_24h=float(market.get("volumeNum", 0)),
                is_active=market.get("active", True),
                asset=asset.upper(),
                slug=market.get("slug", slug),
                accepting_orders=True
            )
            
        except Exception as e:
            logger.error(f"[DRY-RUN] Error fetching real market: {e}")
            return self._generate_simulated_market(asset)
    
    def _generate_simulated_market(self, asset: str) -> CryptoMarket:
        """Generate a simulated market when real API fails"""
        timestamp = self._get_current_15min_timestamp()
        return CryptoMarket(
            condition_id=f"sim_cond_{asset.lower()}_{timestamp}",
            question=f"Will {asset} price go up in the next 15 minutes? (SIMULATED)",
            yes_token_id=f"sim_yes_{asset.lower()}_{timestamp}",
            no_token_id=f"sim_no_{asset.lower()}_{timestamp}",
            yes_price=0.50 + random.uniform(-0.05, 0.05),
            no_price=0.50 + random.uniform(-0.05, 0.05),
            volume_24h=100000,
            is_active=True,
            asset=asset.upper(),
            slug=f"{asset.lower()}-updown-15m-{timestamp}-simulated",
            accepting_orders=True
        )
    
    async def fetch_15min_crypto_markets(self) -> List[CryptoMarket]:
        """Fetch all active 15-minute crypto markets"""
        markets = []
        for asset in self.ASSET_SLUG_MAP.keys():
            market = await self.get_market_for_asset(asset)
            if market:
                markets.append(market)
        return markets
    
    async def place_order(
        self, 
        token_id: str, 
        amount_usdc: float, 
        is_buy: bool = True
    ) -> Dict:
        """Simulate order placement"""
        self._trade_counter += 1
        
        # Simulate random success (95% success rate)
        success = random.random() < 0.95
        
        # Simulate price slightly different from midpoint
        executed_price = 0.5 + random.uniform(-0.05, 0.05)
        
        logger.info(f"[DRY-RUN] Simulated {'BUY' if is_buy else 'SELL'} order: {amount_usdc} USDC")
        
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
    
    async def check_connection(self) -> Dict:
        """Check connection status"""
        return {
            "gamma_api": True,
            "clob_api": True,
            "wallet_connected": True,
            "simulated": True
        }
    
    async def close(self):
        await self.client.aclose()
