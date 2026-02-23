#!/usr/bin/env python3
"""
ACTIVEBOT - Polymarket Trade Debug Script
==========================================

This standalone script tests Polymarket trade execution step by step.
Run this INSIDE the backend container on your DigitalOcean server:

    docker exec -it activebot-backend python debug_trade.py

The script will:
1. Load credentials from .env
2. Initialize CLOB client with signature_type=2 (Gnosis Safe proxy)
3. Check balance and allowance
4. Attempt to place a $1 test order

This isolates the py-clob-client interaction from the rest of the application.
"""

import os
import sys
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_step(step_num, title):
    print(f"\n{Colors.BLUE}{Colors.BOLD}[STEP {step_num}] {title}{Colors.RESET}")
    print("=" * 60)

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")

def print_info(msg):
    print(f"  {msg}")

def main():
    print(f"\n{Colors.BOLD}{'='*60}")
    print("ACTIVEBOT - Polymarket Trade Debug Script")
    print(f"{'='*60}{Colors.RESET}")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    
    # =========================================================================
    # STEP 1: Load and validate credentials
    # =========================================================================
    print_step(1, "Loading Credentials")
    
    private_key = os.environ.get("POLYMARKET_PRIVATE_KEY", "")
    wallet_address = os.environ.get("POLYMARKET_WALLET_ADDRESS", "")
    proxy_address = os.environ.get("POLYMARKET_PROXY_ADDRESS", "")
    
    if not private_key:
        print_error("POLYMARKET_PRIVATE_KEY not set in .env")
        sys.exit(1)
    
    print_success(f"Private Key: {private_key[:10]}...{private_key[-6:]}")
    
    # Derive wallet address from private key
    try:
        from eth_account import Account
        derived_address = Account.from_key(private_key).address
        print_success(f"Derived Address (from PK): {derived_address}")
    except Exception as e:
        print_error(f"Failed to derive address from private key: {e}")
        sys.exit(1)
    
    if wallet_address:
        print_info(f"Explicit Wallet Address: {wallet_address}")
        if wallet_address.lower() != derived_address.lower():
            print_warning("Explicit wallet address differs from derived address!")
    else:
        wallet_address = derived_address
        print_info("Using derived address as wallet address")
    
    if proxy_address:
        print_success(f"Proxy Address (Gnosis Safe): {proxy_address}")
    else:
        print_warning("No POLYMARKET_PROXY_ADDRESS set - will use wallet address")
        proxy_address = wallet_address
    
    # =========================================================================
    # STEP 2: Initialize CLOB Client
    # =========================================================================
    print_step(2, "Initializing CLOB Client")
    
    try:
        from py_clob_client.client import ClobClient
        from py_clob_client.clob_types import BalanceAllowanceParams, AssetType
        
        CLOB_HOST = "https://clob.polymarket.com"
        CHAIN_ID = 137  # Polygon mainnet
        
        print_info(f"Host: {CLOB_HOST}")
        print_info(f"Chain ID: {CHAIN_ID}")
        print_info(f"Signature Type: 2 (POLY_GNOSIS_SAFE)")
        print_info(f"Funder (proxy): {proxy_address}")
        
        clob_client = ClobClient(
            CLOB_HOST,
            key=private_key,
            chain_id=CHAIN_ID,
            signature_type=2,  # POLY_GNOSIS_SAFE
            funder=proxy_address
        )
        
        print_success("CLOB client created")
        
        # Derive API credentials
        print_info("Deriving API credentials...")
        api_creds = clob_client.derive_api_key()
        clob_client.set_api_creds(api_creds)
        print_success(f"API Key: {api_creds.api_key}")
        
    except ImportError as e:
        print_error(f"py-clob-client not installed: {e}")
        print_info("Run: pip install py-clob-client")
        sys.exit(1)
    except Exception as e:
        print_error(f"Failed to initialize CLOB client: {e}")
        sys.exit(1)
    
    # =========================================================================
    # STEP 3: Check Balance
    # =========================================================================
    print_step(3, "Checking Balance")
    
    try:
        params = BalanceAllowanceParams(
            asset_type=AssetType.COLLATERAL,
            signature_type=2
        )
        balance_info = clob_client.get_balance_allowance(params)
        
        balance_raw = int(balance_info.get('balance', 0))
        balance_usdc = balance_raw / 1e6
        allowance_raw = int(balance_info.get('allowance', 0))
        
        print_success(f"Raw balance: {balance_raw}")
        print_success(f"Balance: ${balance_usdc:.2f} USDC")
        print_success(f"Allowance: {allowance_raw}")
        
        if balance_usdc < 1.0:
            print_error("Balance is less than $1 - cannot place test trade!")
            print_info("Please deposit USDC to your Polymarket account")
            sys.exit(1)
        
        if allowance_raw == 0:
            print_error("Allowance is 0 - token spending not approved!")
            print_info("You may need to approve USDC spending on Polymarket")
            # Don't exit - let's try the trade anyway to see the actual error
        
    except Exception as e:
        print_error(f"Failed to check balance: {e}")
        print_info("Continuing to try trade anyway...")
    
    # =========================================================================
    # STEP 4: Find a Market
    # =========================================================================
    print_step(4, "Finding an Active Market")
    
    import httpx
    
    def get_current_15min_timestamp():
        now = datetime.now(timezone.utc)
        base_minute = (now.minute // 15) * 15
        current_window = now.replace(minute=base_minute, second=0, microsecond=0)
        return int(current_window.timestamp())
    
    asset = "BTC"
    timestamp = get_current_15min_timestamp()
    slug = f"btc-updown-15m-{timestamp}"
    
    print_info(f"Looking for market: {slug}")
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                "https://gamma-api.polymarket.com/events",
                params={"slug": slug}
            )
            events = response.json()
            
            if not events:
                # Try previous window
                prev_slug = f"btc-updown-15m-{timestamp - 900}"
                print_info(f"Trying previous window: {prev_slug}")
                response = client.get(
                    "https://gamma-api.polymarket.com/events",
                    params={"slug": prev_slug}
                )
                events = response.json()
            
            if not events:
                print_error("No active BTC market found!")
                sys.exit(1)
            
            event = events[0]
            markets = event.get("markets", [])
            
            if not markets:
                print_error("Event found but no markets inside!")
                sys.exit(1)
            
            market = markets[0]
            token_ids = json.loads(market.get("clobTokenIds", "[]"))
            prices = json.loads(market.get("outcomePrices", "[0.5, 0.5]"))
            
            print_success(f"Found market: {market.get('question', 'Unknown')}")
            print_info(f"Condition ID: {market.get('conditionId', '')[:40]}...")
            print_info(f"Yes Token: {token_ids[0][:40]}...")
            print_info(f"No Token: {token_ids[1][:40]}...")
            print_info(f"Prices - Up: {prices[0]}, Down: {prices[1]}")
            print_info(f"Accepting Orders: {market.get('acceptingOrders', False)}")
            
            if not market.get("acceptingOrders", False):
                print_warning("Market is not accepting orders - trying anyway")
            
            yes_token_id = token_ids[0]
            yes_price = float(prices[0])
            
    except Exception as e:
        print_error(f"Failed to find market: {e}")
        sys.exit(1)
    
    # =========================================================================
    # STEP 5: Get Order Book
    # =========================================================================
    print_step(5, "Getting Order Book")
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                f"{CLOB_HOST}/book",
                params={"token_id": yes_token_id}
            )
            
            if response.status_code == 200:
                orderbook = response.json()
                asks = orderbook.get('asks', [])
                bids = orderbook.get('bids', [])
                
                print_success(f"Order book fetched")
                print_info(f"Best Ask: {asks[0] if asks else 'None'}")
                print_info(f"Best Bid: {bids[0] if bids else 'None'}")
                
                # Use best ask price for our buy order
                if asks:
                    trade_price = float(asks[0]['price'])
                else:
                    trade_price = yes_price
            else:
                print_warning(f"Could not fetch orderbook: {response.status_code}")
                trade_price = yes_price
                
    except Exception as e:
        print_warning(f"Order book error: {e}")
        trade_price = yes_price
    
    # =========================================================================
    # STEP 6: Place Test Order
    # =========================================================================
    print_step(6, "Placing Test Order ($1)")
    
    try:
        from py_clob_client.clob_types import OrderArgs, OrderType
        from py_clob_client.order_builder.constants import BUY
        
        # Calculate order parameters
        amount_usdc = 1.10  # Slightly above minimum
        price = round(max(0.01, min(0.99, trade_price)), 2)
        size = round(amount_usdc / price, 2)
        
        # Ensure minimum order value
        if size * price < 1.0:
            size = round(1.1 / price, 2)
        
        print_info(f"Order Parameters:")
        print_info(f"  Token ID: {yes_token_id[:40]}...")
        print_info(f"  Side: BUY")
        print_info(f"  Price: {price}")
        print_info(f"  Size: {size}")
        print_info(f"  Order Value: ${size * price:.2f}")
        
        # Create order args
        order_args = OrderArgs(
            token_id=yes_token_id,
            price=price,
            size=size,
            side=BUY
        )
        
        print_info("Creating signed order...")
        signed_order = clob_client.create_order(order_args)
        print_success("Order signed successfully")
        
        print_info("Submitting order to CLOB...")
        response = clob_client.post_order(signed_order, OrderType.GTC)
        
        print(f"\n{Colors.BOLD}Response:{Colors.RESET}")
        print(json.dumps(response, indent=2))
        
        if response and response.get('success'):
            print_success(f"\n{Colors.GREEN}{Colors.BOLD}ORDER PLACED SUCCESSFULLY!{Colors.RESET}")
            print_success(f"Order ID: {response.get('orderID', 'N/A')}")
        else:
            error_msg = response.get('errorMsg', 'Unknown error') if response else 'No response'
            print_error(f"\n{Colors.RED}{Colors.BOLD}ORDER FAILED: {error_msg}{Colors.RESET}")
            
    except Exception as e:
        print_error(f"\n{Colors.RED}{Colors.BOLD}EXCEPTION: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
    
    # =========================================================================
    # Summary
    # =========================================================================
    print(f"\n{Colors.BOLD}{'='*60}")
    print("Debug Complete")
    print(f"{'='*60}{Colors.RESET}")
    print("\nIf the order failed with 'not enough balance / allowance':")
    print("1. Check if proxy wallet has approved USDC spending on Polygonscan")
    print("2. Verify the proxy address is the one with funds on Polymarket")
    print("3. Try approving USDC via Polymarket's web interface")
    print(f"\nProxy wallet to check: {proxy_address}")
    print(f"Polygonscan: https://polygonscan.com/address/{proxy_address}#tokentxns")

if __name__ == "__main__":
    main()
