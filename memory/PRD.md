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
- [x] Polymarket market discovery (15-min crypto markets)
- [x] Automated trading based on extreme sentiment
- [x] Visual dashboard with P&L tracking
- [x] Trade history with win/loss stats
- [x] Bet amount slider control ($1-$1000)
- [x] Dry-run mode for testing
- [x] Telegram notification support

## What's Been Implemented (2026-02-23)
### Backend
- FastAPI server with CORS support
- MongoDB integration for trades and config storage
- CFGI sentiment service (with fallback to Alternative.me API)
- Polymarket service (simulated for dry-run, ready for live integration)
- Telegram notification service
- Bot control endpoints (start/stop/status)
- Trade history and statistics APIs
- Configuration management APIs

### Frontend
- Dashboard page with sentiment analysis, bot status, quick stats, P&L chart, recent trades
- Settings page with trade size slider, asset toggles, dry-run mode, Telegram config
- Trade History page with filters, search, and CSV export
- Dark mode trading terminal aesthetic (JetBrains Mono + Inter fonts)
- Responsive Bento Grid layout

## Prioritized Backlog

### P0 - Critical (Completed)
- [x] Core trading loop
- [x] Sentiment-based decision engine
- [x] Visual dashboard
- [x] Bet amount control

### P1 - High Priority (For Live Trading)
- [ ] Connect to real Polymarket API (py-clob-client SDK integration)
- [ ] Connect to real CFGI.io API with paid tier
- [ ] Telegram bot token configuration (user needs to create bot via @BotFather)
- [ ] Wallet balance display
- [ ] Token approval handling for USDC/CTF

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

## Next Tasks
1. Create Telegram bot via @BotFather and configure bot token
2. Test with real CFGI.io API key
3. Set up token approvals for live trading
4. Add wallet balance monitoring
5. Railway/Render deployment configuration

## Environment Configuration
- Backend: FastAPI on port 8001
- Frontend: React on port 3000
- Database: MongoDB (activebot_db)
- Mode: DRY RUN (simulated trades)

## API Keys Stored
- CFGI_API_KEY: Configured
- POLYMARKET_PRIVATE_KEY: Configured (rotate before live deployment)
