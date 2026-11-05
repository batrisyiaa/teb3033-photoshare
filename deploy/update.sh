#!/usr/bin/env bash
# Redeploy after pushing new code: cd /opt/photoshare && bash deploy/update.sh
set -euo pipefail
cd /opt/photoshare
git pull
./backend/venv/bin/pip install -q -r backend/requirements.txt
(cd frontend && npm install && npm run build)
sudo systemctl restart photoshare
curl -s http://127.0.0.1/api/health && echo
