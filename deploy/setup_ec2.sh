#!/usr/bin/env bash
# One-time setup on a fresh Ubuntu 24.04 EC2 instance.
# Usage (on the EC2 instance):
#   git clone <your-repo-url> /opt/photoshare   (or upload the project folder there)
#   cd /opt/photoshare && bash deploy/setup_ec2.sh
# Before running: create backend/.env from backend/.env.example with the RDS and S3 values.
set -euo pipefail
APP=/opt/photoshare

if [ ! -f "$APP/backend/.env" ]; then
  echo "ERROR: $APP/backend/.env not found. Copy backend/.env.example and fill it in first."
  exit 1
fi

echo "== Installing system packages"
sudo apt-get update -y
sudo apt-get install -y python3-venv python3-pip nginx nodejs npm postgresql-client

echo "== Backend (Python virtual environment)"
cd "$APP/backend"
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt
sudo mkdir -p /var/log/photoshare && sudo chown ubuntu:ubuntu /var/log/photoshare

echo "== Frontend (React build)"
cd "$APP/frontend"
npm ci || npm install
npm run build

echo "== nginx"
sudo cp "$APP/deploy/nginx.conf" /etc/nginx/sites-available/photoshare
sudo ln -sf /etc/nginx/sites-available/photoshare /etc/nginx/sites-enabled/photoshare
sudo rm -f /etc/nginx/sites-enabled/default
sudo chmod o+x /opt /opt/photoshare /opt/photoshare/frontend
sudo nginx -t && sudo systemctl restart nginx

echo "== Gunicorn service"
sudo cp "$APP/deploy/photoshare.service" /etc/systemd/system/photoshare.service
sudo systemctl daemon-reload
sudo systemctl enable --now photoshare
sleep 3
curl -s http://127.0.0.1/api/health && echo
echo "== Done. Open http://<EC2-public-IP>/ in your browser."
