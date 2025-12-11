#!/bin/bash

set -euo pipefail

echo "Starting start.sh: updating repository if possible"
git pull origin main || echo "git pull failed or no network, continuing..."

echo "Installing/ensuring Python requirements"
pip install -r requirements.txt --no-cache-dir || echo "pip install failed or already satisfied, continuing..."

echo "Launching uvicorn"
exec uvicorn main:app --host 0.0.0.0 --port 8443 --log-level info
