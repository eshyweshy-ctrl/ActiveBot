#!/bin/bash
# ACTIVEBOT - Quick Deploy Script for DigitalOcean
# Run this on your droplet after uploading the code

set -e

echo "🤖 ACTIVEBOT Deployment Script"
echo "================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (sudo ./deploy.sh)"
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "📝 Creating from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  Please edit .env with your API keys:"
    echo "   nano .env"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Check for required env vars
source .env
if [ -z "$POLYMARKET_PRIVATE_KEY" ] || [ "$POLYMARKET_PRIVATE_KEY" == "your_polymarket_private_key_here" ]; then
    echo "❌ POLYMARKET_PRIVATE_KEY not set in .env"
    exit 1
fi

if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ "$TELEGRAM_BOT_TOKEN" == "your_telegram_bot_token_here" ]; then
    echo "❌ TELEGRAM_BOT_TOKEN not set in .env"
    exit 1
fi

echo "✅ Environment variables configured"

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

# Install Docker Compose if not present
if ! command -v docker compose &> /dev/null; then
    echo "📦 Installing Docker Compose..."
    apt-get update
    apt-get install -y docker-compose-plugin
fi

echo "✅ Docker installed"

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker compose down 2>/dev/null || true

# Build and start
echo "🔨 Building containers..."
docker compose build

echo "🚀 Starting ACTIVEBOT..."
docker compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 10

# Check health
echo ""
echo "🔍 Checking health..."
if curl -s http://localhost:8001/api/health | grep -q "healthy"; then
    echo "✅ Backend is healthy"
else
    echo "⚠️  Backend may still be starting..."
fi

# Get public IP
PUBLIC_IP=$(curl -s ifconfig.me)

echo ""
echo "================================"
echo "🎉 ACTIVEBOT Deployed Successfully!"
echo "================================"
echo ""
echo "📊 Dashboard: http://$PUBLIC_IP"
echo "🔧 API:       http://$PUBLIC_IP:8001/api/health"
echo ""
echo "📱 You should receive a Telegram notification when you start the bot"
echo ""
echo "🔧 Useful commands:"
echo "   docker compose logs -f    # View logs"
echo "   docker compose restart    # Restart services"
echo "   docker compose down       # Stop services"
echo ""
echo "⚠️  IMPORTANT: Make sure to rotate your Polymarket private key!"
echo ""
