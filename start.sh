#!/bin/bash
set -e

cd /var/www/metalsoft/miit_api

# Instalación de dependencias
pip install -r requirements.txt --no-cache-dir

# Ejecutar la aplicación
exec uvicorn main:app --host 0.0.0.0 --port 8443