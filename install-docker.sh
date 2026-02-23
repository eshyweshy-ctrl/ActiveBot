#!/bin/bash
# ACTIVEBOT - One-Command Install for DigitalOcean
# Droplet IP: 64.227.170.252
# 
# Run this on your droplet:
# curl -sSL https://raw.githubusercontent.com/YOUR_REPO/install.sh | bash
# OR copy-paste all commands below

set -e

echo "🤖 Installing ACTIVEBOT on DigitalOcean..."

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Docker Compose
apt install -y docker-compose-plugin

# Create app directory
mkdir -p /opt/activebot
cd /opt/activebot

echo "✅ Docker installed. Now upload your code."
echo ""
echo "From your LOCAL machine, run:"
echo "scp -r /app/* root@64.227.170.252:/opt/activebot/"
echo ""
echo "Then on this droplet, run:"
echo "cd /opt/activebot && docker compose up -d --build"
