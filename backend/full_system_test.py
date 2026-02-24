#!/usr/bin/env python3
"""
ACTIVEBOT - Full System Test
============================
Tests all components:
1. CFGI sentiment data fetching (BTC, ETH, SOL)
2. Polymarket 15-min market discovery
3. Wallet balance and connection
4. Order placement (real trade)
"""

import os
import json
import asyncio
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# Colors
G = '\033[92m'  # Green
R = '\033[91m'  # Red
Y = '\033[93m'  # Yellow
B = '\033[94m'  # Blue
W = '\033[0m'   # Reset
BOLD = '\033[1m'

def ok(msg): print(f"{G}✓ {msg}{W}")
def fail(msg): print(f"{R}✗ {msg}{W}")
def warn(msg): print(f"{Y}⚠ {msg}{W}")
def info(msg): print(f"  {msg}")
def header(msg): print(f"\n{B}{BOLD}[{msg}]{W}\n" + "="*50)

async def main():
    print(f"\n{BOLD}{'='*60}")
    print("ACTIVEBOT - FULL SYSTEM TEST")
    print(f"{'='*60}{W}")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}\n")
    
    results = {
        "cfgi": {"status": "UNTESTED", "details": {}},
        "polymarket_markets": {"status": "UNTESTED", "details": {}},
        "polymarket_wallet": {"status": "UNTESTED", "details": {}},
        "polymarket_trade": {"status": "UNTESTED", "details": {}}
    }
    
    # ========================================
    # TEST 1: CFGI Sentiment Data
    # ========================================
    header("TEST 1: CFGI Sentiment Data")
    
    try:
        from cfgi_service import CFGIService
        cfgi = CFGIService()
        
        for asset in ["BTC", "ETH", "SOL"]:
            sentiment = await cfgi.get_sentiment(asset)
            score = sentiment.get('score', 0)
            signal = sentiment.get('signal', 'UNKNOWN')
            source = sentiment.get('source', 'unknown')
            
            if 0 <= score <= 100:
                ok(f"{asset}: Score={score}, Signal={signal}, Source={source}")
                results["cfgi"]["details"][asset] = {"score": score, "signal": signal}
            else:
                fail(f"{asset}: Invalid score {score}")
        
        await cfgi.close()
        results["cfgi"]["status"] = "PASS"
        ok("CFGI sentiment service working!")
        
    except Exception as e:
        fail(f"CFGI test failed: {e}")
        results["cfgi"]["status"] = "FAIL"
    
    # ========================================
    # TEST 2: Polymarket Market Discovery
    # ========================================
    header("TEST 2: Polymarket 15-min Markets")
    
    try:
        from polymarket_service import PolymarketService
        poly = PolymarketService()
        
        markets_found = []
        for asset in ["BTC", "ETH", "SOL"]:
            market = await poly.get_market_for_asset(asset)
            if market:
                ok(f"{asset}: {market.question[:50]}...")
                info(f"   Slug: {market.slug}")
                info(f"   Up: {market.yes_price:.2f}, Down: {market.no_price:.2f}")
                info(f"   Accepting Orders: {market.accepting_orders}")
                markets_found.append(asset)
                results["polymarket_markets"]["details"][asset] = {
                    "slug": market.slug,
                    "yes_price": market.yes_price,
                    "no_price": market.no_price
                }
            else:
                warn(f"{asset}: No market found")
        
        if len(markets_found) >= 2:
            results["polymarket_markets"]["status"] = "PASS"
            ok(f"Found {len(markets_found)}/3 markets")
        else:
            results["polymarket_markets"]["status"] = "PARTIAL"
            warn(f"Only found {len(markets_found)}/3 markets")
        
    except Exception as e:
        fail(f"Market discovery failed: {e}")
        results["polymarket_markets"]["status"] = "FAIL"
    
    # ========================================
    # TEST 3: Wallet Connection & Balance
    # ========================================
    header("TEST 3: Wallet Connection & Balance")
    
    try:
        proxy = os.environ.get("POLYMARKET_PROXY_ADDRESS", "")
        pk = os.environ.get("POLYMARKET_PRIVATE_KEY", "")
        
        if not pk:
            fail("POLYMARKET_PRIVATE_KEY not set!")
            results["polymarket_wallet"]["status"] = "FAIL"
        else:
            from eth_account import Account
            wallet = Account.from_key(pk).address
            ok(f"EOA Wallet: {wallet}")
            
            if proxy:
                ok(f"Proxy Wallet: {proxy}")
            else:
                warn("POLYMARKET_PROXY_ADDRESS not set - using wallet address")
                proxy = wallet
            
            # Check balance
            from py_clob_client.client import ClobClient
            from py_clob_client.clob_types import BalanceAllowanceParams, AssetType
            
            clob = ClobClient(
                "https://clob.polymarket.com",
                key=pk,
                chain_id=137,
                signature_type=2,
                funder=proxy
            )
            creds = clob.derive_api_key()
            clob.set_api_creds(creds)
            
            params = BalanceAllowanceParams(asset_type=AssetType.COLLATERAL, signature_type=2)
            bal_info = clob.get_balance_allowance(params)
            balance = int(bal_info.get('balance', 0)) / 1e6
            allowance = bal_info.get('allowance', 0)
            
            ok(f"Balance: ${balance:.2f} USDC")
            info(f"Allowance: {allowance}")
            
            results["polymarket_wallet"]["details"] = {
                "wallet": wallet,
                "proxy": proxy,
                "balance": balance
            }
            
            if balance >= 5:
                results["polymarket_wallet"]["status"] = "PASS"
                ok("Sufficient balance for trading (min $5)")
            else:
                results["polymarket_wallet"]["status"] = "LOW_BALANCE"
                warn(f"Balance ${balance:.2f} may be too low (need ~$5 for min order)")
                
    except Exception as e:
        fail(f"Wallet test failed: {e}")
        results["polymarket_wallet"]["status"] = "FAIL"
    
    # ========================================
    # TEST 4: Order Placement (Real Trade)
    # ========================================
    header("TEST 4: Order Placement (Real Trade)")
    
    try:
        if results["polymarket_wallet"]["status"] in ["PASS", "LOW_BALANCE"]:
            balance = results["polymarket_wallet"]["details"].get("balance", 0)
            
            if balance < 5:
                warn(f"Skipping trade test - balance ${balance:.2f} too low")
                results["polymarket_trade"]["status"] = "SKIPPED"
            else:
                # Get a market
                market = await poly.get_market_for_asset("BTC")
                if not market:
                    market = await poly.get_market_for_asset("ETH")
                
                if market:
                    info(f"Testing trade on: {market.slug}")
                    
                    from py_clob_client.clob_types import OrderArgs, OrderType
                    from py_clob_client.order_builder.constants import BUY
                    
                    # Place order with minimum size
                    order_args = OrderArgs(
                        token_id=market.yes_token_id,
                        price=0.99,
                        size=5.1,  # Minimum required size
                        side=BUY
                    )
                    
                    signed = clob.create_order(order_args)
                    ok("Order signed successfully")
                    
                    response = clob.post_order(signed, OrderType.GTC)
                    
                    if response and response.get('success'):
                        ok(f"ORDER PLACED SUCCESSFULLY!")
                        ok(f"Order ID: {response.get('orderID', 'N/A')}")
                        ok(f"Status: {response.get('status', 'N/A')}")
                        if response.get('transactionsHashes'):
                            ok(f"Tx: {response['transactionsHashes'][0]}")
                        results["polymarket_trade"]["status"] = "PASS"
                        results["polymarket_trade"]["details"] = {
                            "order_id": response.get('orderID'),
                            "status": response.get('status')
                        }
                    else:
                        error = response.get('errorMsg', 'Unknown') if response else 'No response'
                        fail(f"Order failed: {error}")
                        results["polymarket_trade"]["status"] = "FAIL"
                        results["polymarket_trade"]["details"] = {"error": error}
                else:
                    fail("No market available for testing")
                    results["polymarket_trade"]["status"] = "NO_MARKET"
        else:
            warn("Skipping trade test - wallet not connected")
            results["polymarket_trade"]["status"] = "SKIPPED"
            
    except Exception as e:
        fail(f"Trade test failed: {e}")
        results["polymarket_trade"]["status"] = "FAIL"
        results["polymarket_trade"]["details"] = {"error": str(e)}
    
    # ========================================
    # SUMMARY
    # ========================================
    print(f"\n{BOLD}{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}{W}\n")
    
    all_pass = True
    for test_name, result in results.items():
        status = result["status"]
        if status == "PASS":
            print(f"  {G}✓{W} {test_name}: {status}")
        elif status in ["PARTIAL", "LOW_BALANCE", "SKIPPED"]:
            print(f"  {Y}⚠{W} {test_name}: {status}")
        else:
            print(f"  {R}✗{W} {test_name}: {status}")
            all_pass = False
    
    print()
    if all_pass:
        print(f"{G}{BOLD}ALL SYSTEMS OPERATIONAL!{W}")
        print("The bot is ready for automated trading.")
    else:
        print(f"{R}{BOLD}SOME TESTS FAILED{W}")
        print("Please fix issues before enabling automated trading.")
    
    # Cleanup
    try:
        await poly.close()
    except:
        pass
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
