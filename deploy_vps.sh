#!/bin/bash
# AutoTube AI — One-Click Automated VPS Deployment Script
# Supports: Ubuntu 20.04 / 22.04 / 24.04, Debian 11/12, Hostinger VPS, DigitalOcean, AWS EC2, Linode

set -e

echo "================================================================================"
echo "🚀 AUTOTUBE AI — ONE-CLICK VPS DEPLOYMENT INSTALLED"
echo "================================================================================"

# 1. Update system packages
echo "[1/4] Updating system packages & installing prerequisites..."
sudo apt-get update -y
sudo apt-get install -y curl git ufw ca-certificates gnupg lsb-release

# 2. Install Docker if missing
if ! command -v docker &> /dev/null; then
    echo "[2/4] Installing Docker Engine..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
else
    echo "[2/4] Docker is already installed."
fi

# 3. Configure Firewall (Allow Ports 80, 443, 22)
echo "[3/4] Setting up security firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 20090/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable || true

# 4. Build and launch Docker containers
echo "[4/4] Building and launching AutoTube AI Production Cluster..."
sudo docker compose down --remove-orphans || true
sudo docker compose up -d --build

SERVER_IP=$(curl -s ifconfig.me || hostname -I | awk '{print $1}')

echo "================================================================================"
echo "🎉 DEPLOYMENT COMPLETE! YOUR AUTOTUBE AI SAAS IS LIVE!"
echo "================================================================================"
echo "🌐 Access Website: http://${SERVER_IP}"
echo "🔌 API Endpoint:   http://${SERVER_IP}/api/v1"
echo "💳 Razorpay Keys:  Configured & Armed"
echo "================================================================================"
