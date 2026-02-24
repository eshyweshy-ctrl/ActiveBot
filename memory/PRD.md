# ACTIVEBOT - Product Requirements Document

## Original Problem Statement
Build ACTIVEBOT - a cloud-hosted automated trading bot that reads crypto sentiment from CFGI.io and places trades in 15-minute direction markets on Polymarket. The bot must run continuously and trade automatically based on extreme sentiment only.

### Trading Rules
- **0-19 (EXTREME FEAR)**: Buy YES tokens (expecting price to go UP)
- **80-100 (EXTREME GREED)**: Buy NO tokens (expecting price to go DOWN)
- **20-79 (NEUTRAL)**: No trade - wait for extreme sentiment

### Supported Assets
- BTC (Bitcoin)
- ETH (Ethereum)
- SOL (Solana)

## User Personas
1. **Crypto Trader**: Wants automated sentiment-based trading without manual intervention
2. **Risk-Averse User**: Prefers dry-run mode to test strategies before live trading
3. **Active Monitor**: Wants real-time dashboard and Telegram alerts for trade notifications

## Core Requirements (Static)
- [x] CFGI sentiment data polling
- [x] Polymarket 15-minute market discovery (FIXED 2026-02-23)
- [x] Automated trading based on extreme sentiment
- [x] Visual dashboard with P&L tracking
- [x] Trade history with win/loss stats
- [x] Bet amount slider control ($1-$1000)
- [x] Dry-run mode for testing
- [x] Telegram notification support (VERIFIED WORKING 2026-02-23)

## What's Been Implemented

### 2026-02-23 (Latest Session)
**🔧 CRITICAL FIX: Polymarket 15-Minute Market Integration**
- Fixed market discovery using correct dynamic slug pattern: `{asset}-updown-15m-{unix_timestamp}`
- Markets are now correctly discovered via: `https://gamma-api.polymarket.com/events?slug={slug}`
- Verified working for BTC, ETH, and SOL 15-minute markets
- Added `/api/markets/test` endpoint for debugging market discovery

**✅ VERIFIED: Telegram Notifications Working**
- Confirmed Telegram messages are being sent and received
- Bot start/stop notifications working
- Scanning status updates working
- Trade alerts configured (will trigger on extreme sentiment)

**✨ NEW: Wallet Info & Enhanced Trade Display**
- Added wallet balance display (USDC, MATIC, Positions Value)
- Shows connected wallet address with copy-to-clipboard and Polygonscan link
- Added Wallet status to System Status bar
- Enhanced Recent Trades table with:
  - CFGI score column (shows sentiment at time of trade)
  - Improved time display with separate date
  - Trade duration column
- Added `/api/wallet/info` and `/api/wallet/positions` endpoints

### Backend
- FastAPI server with CORS support
- MongoDB integration for trades and config storage
- CFGI sentiment service (web scraping from cfgi.io with fallback)
- **Polymarket service with correct 15-minute market discovery**
- Telegram notification service (verified working)
- Bot control endpoints (start/stop/status)
- Trade history and statistics APIs
- Configuration management APIs

### Frontend
- Dashboard page with sentiment analysis, bot status, quick stats, P&L chart, recent trades
- Settings page with trade size slider, asset toggles, dry-run mode, Telegram config
- Trade History page with filters, search, and CSV export
- Dark mode trading terminal aesthetic (JetBrains Mono + Inter fonts)
- Responsive Bento Grid layout

## Technical Implementation Details

### Polymarket 15-Minute Market Slug Pattern
```
Format: {asset}-updown-15m-{unix_timestamp}
Examples:
- btc-updown-15m-1771859700
- eth-updown-15m-1771859700
- sol-updown-15m-1771859700
```

The timestamp represents the START of the 15-minute trading window, rounded down to the nearest 15-minute boundary.

### API Endpoints
- `GET /api/markets` - Lists all discovered 15-minute crypto markets
- `GET /api/markets/test` - Tests Polymarket API connection and market discovery
- `GET /api/wallet/info` - Gets wallet address and balances (USDC, MATIC, positions)
- `GET /api/wallet/positions` - Gets current open positions for the wallet
- `POST /api/bot/start` - Starts the trading bot
- `POST /api/bot/stop` - Stops the trading bot
- `GET /api/sentiment/current` - Gets current CFGI sentiment for all assets
- `POST /api/telegram/test` - Tests Telegram connection

## Prioritized Backlog

### P0 - Critical (All Completed ✅)
- [x] Core trading loop
- [x] Sentiment-based decision engine
- [x] Visual dashboard
- [x] Bet amount control
- [x] Polymarket 15-minute market discovery
- [x] Telegram notifications

### P1 - High Priority (For Live Trading on User's Server)
- [ ] Verify live trading with real Polymarket orders (requires user to fund wallet)
- [ ] Test with extreme sentiment conditions (wait for CFGI < 20 or > 80)
- [ ] Deploy updated code to user's DigitalOcean droplet

### P2 - Medium Priority
- [ ] Multi-timeframe support (1H, 4H markets)
- [ ] Advanced risk controls (max daily loss, position sizing)
- [ ] Historical sentiment correlation analysis
- [ ] Trade notes/annotations

### P3 - Nice to Have
- [ ] Mobile-responsive PWA
- [ ] Discord webhook notifications
- [ ] API rate limiting dashboard
- [ ] Backtesting with historical data

## Deployment Instructions for User's Server

### Prerequisites
The user has a DigitalOcean droplet at `64.227.170.252` with the code deployed to `/opt/activebot/`.

### Update Procedure
1. SSH into the server: `ssh root@64.227.170.252`
2. Navigate to the project: `cd /opt/activebot`
3. Pull latest changes: `git pull origin main`
4. Rebuild and restart containers:
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```
5. Check logs: `docker logs -f activebot-backend`

### Environment Variables (in /opt/activebot/.env)
```
CFGI_API_KEY=28418_b2ba_ebf6bface1
POLYMARKET_PRIVATE_KEY=0x90b866fe220739cf836be67fdab7143b762a3a356721d96d262246ea69ae2735
RPC_URL=https://polygon-rpc.com
TRADE_SIZE_USDC=1
NETWORK=polygon
TELEGRAM_BOT_TOKEN=8577956930:AAH8QJNbyKeCKVtUeMkZDsl9exp_TBL0gUU
TELEGRAM_CHAT_ID=875284528
REACT_APP_BACKEND_URL=http://64.227.170.252:8001
BOT_PASSWORD=62411
```

## Files Changed (2026-02-23)
- `/app/backend/polymarket_service.py` - Complete rewrite with correct market discovery
- `/app/backend/server.py` - Added `/api/markets/test` endpoint and improved `/api/markets` response

## Current State
- ✅ Polymarket 15-minute markets discoverable
- ✅ Telegram notifications working
- ✅ CFGI sentiment scraping working
- ✅ Dashboard and UI fully functional
- ✅ Bot runs in dry-run mode by default
- ✅ **LIVE TRADING WORKING** (Fixed 2026-02-23)

### 2026-02-23 - CRITICAL FIX: Polymarket Trade Execution
**Problem:** Trades were failing with "not enough balance / allowance" or "invalid signature" errors.

**Root Cause:** The `py-clob-client` was not configured correctly for Gnosis Safe proxy wallets:
1. `signature_type=2` (POLY_GNOSIS_SAFE) is required
2. `funder` parameter MUST be set to the proxy wallet address (not the EOA)
3. **Minimum order SIZE is 5 tokens** (not just $1 value)

**Solution:**
- EOA Signer: `0xD929737cc880A6B019a2666d74860c44b7a38F44` (derived from private key)
- Proxy Wallet: `0x08bc04f888702843ef83370ffcf9c9856bcfa12d` (Gnosis Safe with funds)
- Added `POLYMARKET_PROXY_ADDRESS` to `.env` on server
- Updated minimum order size to 5.1 tokens

**Required .env variables for trading:**
```
POLYMARKET_PRIVATE_KEY=0x598cf1db...  # EOA private key
POLYMARKET_PROXY_ADDRESS=0x08bc04f888702843ef83370ffcf9c9856bcfa12d  # Gnosis Safe proxy
```

## Verified Trade Executions
- Order 0x6428cf7b46e84ceb2bb43bc8c7f6bdceda71295dd115a9b0bb5416a517acbe55 - matched ✅
- Order 0xeaa13edde888ea431dd04ad7f407d06e3560410d35207fe160074b1b834b4fb4 - matched ✅
- Order 0xb579553ce68bfd12db2a1bd476abb379b29bb118e38700460151c8954aff0e33 - matched ✅
