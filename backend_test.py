#!/usr/bin/env python3
"""
Backend API Tests for ACTIVEBOT
Tests all REST endpoints and validates responses
"""
import requests
import json
import time
from datetime import datetime

class ActiveBotAPITester:
    def __init__(self, base_url="https://activebot-trading-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
    def log(self, message, success=None):
        """Log test results with colored output"""
        if success is True:
            print(f"✅ {message}")
            self.tests_passed += 1
        elif success is False:
            print(f"❌ {message}")
            self.failed_tests.append(message)
        else:
            print(f"📋 {message}")
        self.tests_run += 1
    
    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make HTTP request and validate response"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            
            success = response.status_code == expected_status
            
            if success:
                try:
                    json_response = response.json()
                    return True, json_response
                except:
                    return True, response.text
            else:
                print(f"   Expected: {expected_status}, Got: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False, {}
                
        except requests.exceptions.Timeout:
            print(f"   Timeout error for {url}")
            return False, {}
        except Exception as e:
            print(f"   Request error: {str(e)}")
            return False, {}
    
    def test_health_endpoints(self):
        """Test basic health and connectivity"""
        print("\n🏥 Testing Health Endpoints...")
        
        # Test root endpoint
        success, response = self.make_request('GET', '')
        self.log(f"Root endpoint (/api): {response.get('message', 'No message') if success else 'Failed'}", success)
        
        # Test health check
        success, response = self.make_request('GET', 'health')
        if success and 'status' in response:
            self.log(f"Health check: {response['status']}", success)
            if 'bot_running' in response:
                print(f"   Bot status: {response['bot_running']}")
        else:
            self.log("Health check failed", False)
    
    def test_bot_status_and_control(self):
        """Test bot status and control endpoints"""
        print("\n🤖 Testing Bot Control...")
        
        # Get initial status
        success, status = self.make_request('GET', 'bot/status')
        self.log(f"Bot status: {'Retrieved' if success else 'Failed'}", success)
        
        if success:
            is_running = status.get('is_running', False)
            config = status.get('config', {})
            print(f"   Running: {is_running}")
            print(f"   Config: {config}")
            
            # Test start bot
            success, response = self.make_request('POST', 'bot/start')
            self.log(f"Start bot: {response.get('status', 'Failed') if success else 'Failed'}", success)
            
            # Wait a moment
            time.sleep(1)
            
            # Check status after start
            success, new_status = self.make_request('GET', 'bot/status')
            if success:
                self.log(f"Status after start: Running={new_status.get('is_running', False)}", success)
            
            # Test stop bot  
            success, response = self.make_request('POST', 'bot/stop')
            self.log(f"Stop bot: {response.get('status', 'Failed') if success else 'Failed'}", success)
    
    def test_sentiment_endpoints(self):
        """Test sentiment data endpoints"""
        print("\n📊 Testing Sentiment Endpoints...")
        
        # Get current sentiment
        success, sentiment = self.make_request('GET', 'sentiment/current')
        self.log(f"Current sentiment: {'Retrieved' if success else 'Failed'}", success)
        
        if success:
            for asset in ['BTC', 'ETH', 'SOL']:
                if asset in sentiment:
                    data = sentiment[asset]
                    print(f"   {asset}: Score={data.get('score', 'N/A')}, Signal={data.get('signal', 'N/A')}")
                else:
                    print(f"   {asset}: Missing")
        
        # Test sentiment history
        success, history = self.make_request('GET', 'sentiment/history?limit=5')
        self.log(f"Sentiment history: {'Retrieved {len(history)} records' if success and isinstance(history, list) else 'Failed'}", success)
        
        # Test sentiment simulation
        success, response = self.make_request('POST', 'sentiment/simulate', {'score': 10, 'asset': 'BTC'})
        self.log(f"Simulate sentiment: {response.get('status', 'Failed') if success else 'Failed'}", success)
    
    def test_stats_endpoints(self):
        """Test statistics endpoints"""
        print("\n📈 Testing Statistics Endpoints...")
        
        # Get bot stats
        success, stats = self.make_request('GET', 'stats')
        self.log(f"Bot stats: {'Retrieved' if success else 'Failed'}", success)
        
        if success:
            print(f"   Total Trades: {stats.get('total_trades', 0)}")
            print(f"   Total P&L: ${stats.get('total_pnl', 0)}")
            print(f"   Win Rate: {stats.get('win_rate', 0)}%")
            print(f"   Open Trades: {stats.get('open_trades', 0)}")
        
        # Get P&L history
        success, pnl_history = self.make_request('GET', 'stats/pnl-history')
        self.log(f"P&L history: {'Retrieved {len(pnl_history)} records' if success and isinstance(pnl_history, list) else 'Failed'}", success)
    
    def test_trades_endpoints(self):
        """Test trade-related endpoints"""
        print("\n💰 Testing Trades Endpoints...")
        
        # Get all trades
        success, trades = self.make_request('GET', 'trades?limit=20')
        self.log(f"Get trades: {'Retrieved {len(trades)} trades' if success and isinstance(trades, list) else 'Failed'}", success)
        
        # Test with asset filter
        success, btc_trades = self.make_request('GET', 'trades?asset=BTC&limit=10')
        self.log(f"BTC trades: {'Retrieved {len(btc_trades)} trades' if success and isinstance(btc_trades, list) else 'Failed'}", success)
        
        # Test with status filter
        success, won_trades = self.make_request('GET', 'trades?status=WON&limit=10')
        self.log(f"Won trades: {'Retrieved {len(won_trades)} trades' if success and isinstance(won_trades, list) else 'Failed'}", success)
        
        # If we have trades, test getting specific trade
        if success and isinstance(trades, list) and len(trades) > 0:
            trade_id = trades[0].get('id')
            if trade_id:
                success, trade = self.make_request('GET', f'trades/{trade_id}')
                self.log(f"Get trade {trade_id[:8]}...: {'Retrieved' if success else 'Failed'}", success)
    
    def test_config_endpoints(self):
        """Test configuration endpoints"""
        print("\n⚙️ Testing Configuration Endpoints...")
        
        # Get config
        success, config = self.make_request('GET', 'config')
        self.log(f"Get config: {'Retrieved' if success else 'Failed'}", success)
        
        if success:
            print(f"   Trade Size: ${config.get('trade_size_usdc', 'N/A')}")
            print(f"   Assets: {config.get('assets_enabled', [])}")
            print(f"   Dry Run: {config.get('dry_run_mode', 'N/A')}")
        
        # Test config update
        update_data = {
            "trade_size_usdc": 25.0,
            "dry_run_mode": True
        }
        success, response = self.make_request('PUT', 'config', update_data)
        self.log(f"Update config: {response.get('status', 'Failed') if success else 'Failed'}", success)
    
    def test_markets_endpoint(self):
        """Test markets endpoint"""
        print("\n🏪 Testing Markets Endpoint...")
        
        success, markets = self.make_request('GET', 'markets')
        self.log(f"Get markets: {'Retrieved {len(markets)} markets' if success and isinstance(markets, list) else 'Failed'}", success)
        
        if success and isinstance(markets, list) and len(markets) > 0:
            market = markets[0]
            print(f"   Sample market: {market.get('question', 'No question')[:50]}...")
            print(f"   Asset: {market.get('asset', 'N/A')}")
            print(f"   Active: {market.get('is_active', 'N/A')}")
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting ACTIVEBOT API Tests...")
        print(f"Backend URL: {self.base_url}")
        
        start_time = time.time()
        
        # Run all test categories
        self.test_health_endpoints()
        self.test_bot_status_and_control()
        self.test_sentiment_endpoints()
        self.test_stats_endpoints()
        self.test_trades_endpoints()
        self.test_config_endpoints()
        self.test_markets_endpoint()
        
        # Summary
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n📊 Test Summary:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        print(f"   Duration: {duration:.2f}s")
        
        if self.failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in self.failed_tests:
                print(f"   - {test}")
        
        return self.tests_passed, self.tests_run, self.failed_tests

if __name__ == "__main__":
    tester = ActiveBotAPITester()
    passed, total, failed = tester.run_all_tests()
    
    # Exit with appropriate code
    exit_code = 0 if passed == total else 1
    exit(exit_code)