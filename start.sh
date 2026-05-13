#!/bin/bash

# Ejecutar la aplicación
exec uvicorn main:app --host 0.0.0.0 --port 8443

