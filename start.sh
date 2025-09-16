#!/bin/bash
cd /var/www/metalsoft/miit_api
pip install -r requirements.txt --no-cache-dir
exec uvicorn main:app --host 0.0.0.0 --port 8443