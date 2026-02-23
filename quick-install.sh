#!/bin/bash
# ACTIVEBOT Quick Installer for DigitalOcean
# Usage: bash <(curl -s URL_TO_THIS_SCRIPT)

set -e
DROPLET_IP="64.227.170.252"

echo "🤖 ACTIVEBOT Installer"
echo "======================"

# Install dependencies
apt update
apt install -y docker.io docker-compose git curl

# Start Docker
systemctl start docker
systemctl enable docker

# Create directories
mkdir -p /opt/activebot/{backend,frontend/src/{components/ui,pages,hooks,lib},frontend/public}
cd /opt/activebot

# Create .env
cat > .env << 'ENVEOF'
CFGI_API_KEY=28418_b2ba_ebf6bface1
POLYMARKET_PRIVATE_KEY=0x90b866fe220739cf836be67fdab7143b762a3a356721d96d262246ea69ae2735
RPC_URL=https://polygon-rpc.com
TRADE_SIZE_USDC=1
NETWORK=polygon
TELEGRAM_BOT_TOKEN=8577956930:AAH8QJNbyKeCKVtUeMkZDsl9exp_TBL0gUU
TELEGRAM_CHAT_ID=875284528
REACT_APP_BACKEND_URL=http://64.227.170.252:8001
ENVEOF

echo "✅ Environment configured"
echo ""
echo "📋 Now you need to copy the source files."
echo "The easiest way is to use 'Save to GitHub' in Emergent,"
echo "then run: git clone YOUR_REPO_URL ."
echo ""
echo "Or download the ZIP from Emergent and upload via:"
echo "scp activebot-deploy.zip root@64.227.170.252:/opt/activebot/"
