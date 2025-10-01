#!/bin/bash

# Instalación de dependencias
pip install -r requirements.txt --no-cache-dir

# Ejecutar la aplicación
exec uvicorn main:app --host 0.0.0.0 --port 8443

