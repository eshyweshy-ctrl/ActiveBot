# ACTIVEBOT - DigitalOcean Deployment Guide

## Prerequisites
- DigitalOcean account
- Domain name (optional but recommended)
- Your API keys ready:
  - CFGI.io API key
  - Polymarket wallet private key
  - Telegram bot token & chat ID

---

## Quick Deploy (5 minutes)

### Step 1: Create a Droplet

1. Go to DigitalOcean → Create → Droplets
2. Choose:
   - **Image**: Ubuntu 22.04 LTS
   - **Plan**: Basic → $12/mo (2GB RAM, 1 vCPU) minimum
   - **Region**: Choose closest to you
   - **Authentication**: SSH Key (recommended) or Password

3. Click **Create Droplet**

### Step 2: Connect to Your Droplet

```bash
ssh root@your-droplet-ip
```

### Step 3: Install Docker

```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose-plugin -y

# Verify installation
docker --version
docker compose version
```

### Step 4: Clone & Configure

```bash
# Create app directory
mkdir -p /opt/activebot
cd /opt/activebot

# Clone your code (or upload via SCP)
# Option A: If you have a git repo
git clone your-repo-url .

# Option B: Upload from local machine (run from your local machine)
# scp -r /app/* root@your-droplet-ip:/opt/activebot/
```

### Step 5: Configure Environment

```bash
# Create .env file
nano .env
```

Paste your configuration:
```env
CFGI_API_KEY=28418_b2ba_ebf6bface1
POLYMARKET_PRIVATE_KEY=your_new_rotated_private_key
TELEGRAM_BOT_TOKEN=8577956930:AAH8QJNbyKeCKVtUeMkZDsl9exp_TBL0gUU
TELEGRAM_CHAT_ID=875284528
RPC_URL=https://polygon-rpc.com
TRADE_SIZE_USDC=1
REACT_APP_BACKEND_URL=http://your-droplet-ip:8001
```

Save: `Ctrl+X`, then `Y`, then `Enter`

### Step 6: Deploy

```bash
# Build and start all services
docker compose up -d --build

# Check status
docker compose ps

# View logs
docker compose logs -f
```

### Step 7: Access Your Bot

- **Dashboard**: `http://your-droplet-ip`
- **API Health**: `http://your-droplet-ip:8001/api/health`

---

## Production Setup (Recommended)

### Add SSL with Nginx & Let's Encrypt

```bash
# Install Certbot
apt install certbot python3-certbot-nginx -y

# Install Nginx
apt install nginx -y

# Create Nginx config
nano /etc/nginx/sites-available/activebot
```

Paste:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:80;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable and get SSL:
```bash
ln -s /etc/nginx/sites-available/activebot /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx

# Get SSL certificate
certbot --nginx -d your-domain.com
```

---

## Management Commands

```bash
# View all containers
docker compose ps

# View logs (all services)
docker compose logs -f

# View specific service logs
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f mongodb

# Restart services
docker compose restart

# Stop all services
docker compose down

# Update and redeploy
git pull  # or upload new code
docker compose up -d --build

# Check MongoDB data
docker compose exec mongodb mongosh activebot_db --eval "db.trades.find().pretty()"
```

---

## Backup MongoDB Data

```bash
# Create backup
docker compose exec mongodb mongodump --db activebot_db --out /data/backup

# Copy backup to host
docker cp activebot-mongo:/data/backup ./backup-$(date +%Y%m%d)
```

---

## Monitoring

### Set up monitoring alerts (optional)

```bash
# Install monitoring agent
curl -sSL https://repos.insights.digitalocean.com/install.sh | sudo bash
```

### Health check endpoint
The backend exposes `/api/health` which returns:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-23T10:00:00Z",
  "bot_running": true
}
```

---

## Troubleshooting

### Container not starting
```bash
docker compose logs backend
docker compose logs frontend
```

### MongoDB connection issues
```bash
docker compose exec mongodb mongosh --eval "db.adminCommand('ping')"
```

### Port already in use
```bash
# Find process using port
lsof -i :8001
lsof -i :80

# Kill process
kill -9 PID
```

### Reset everything
```bash
docker compose down -v  # Warning: This deletes all data!
docker compose up -d --build
```

---

## Security Checklist

- [ ] Rotate Polymarket private key (it was shared publicly)
- [ ] Use SSH keys instead of passwords
- [ ] Set up firewall (ufw)
- [ ] Enable automatic security updates
- [ ] Use a domain with SSL

### Basic Firewall Setup
```bash
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8001/tcp
ufw enable
```

---

## Cost Estimate

| Resource | Monthly Cost |
|----------|-------------|
| Droplet (2GB) | $12 |
| Domain (optional) | ~$12/year |
| **Total** | **~$12-15/mo** |

---

## Support

- DigitalOcean Docs: https://docs.digitalocean.com
- Docker Docs: https://docs.docker.com
- MongoDB Docs: https://docs.mongodb.com
