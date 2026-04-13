# Guía de Mantenimiento

## Servicio Interconsulta MIIT — Backend API

**Versión:** 1.0.9
**Fecha:** 26 de marzo de 2026
**Proyecto:** Puerto Antioquia — Urabá
**Desarrollado por:** Metalteco S.A.S

---

## Tabla de Contenido

1. [Introducción](#1-introducción)
2. [Requisitos del Entorno](#2-requisitos-del-entorno)
3. [Configuración del Entorno Local](#3-configuración-del-entorno-local)
4. [Gestión de la Base de Datos](#4-gestión-de-la-base-de-datos)
5. [Sistema de Logging y Monitoreo](#5-sistema-de-logging-y-monitoreo)
6. [Gestión del Contenedor Docker](#6-gestión-del-contenedor-docker)
7. [Despliegue en Producción (AWS ECS Fargate)](#7-despliegue-en-producción-aws-ecs-fargate)
8. [Mantenimiento de la Integración Externa (TurboGraneles)](#8-mantenimiento-de-la-integración-externa-turbograneles)
9. [Mantenimiento del Sistema de Reportería](#9-mantenimiento-del-sistema-de-reportería)
10. [Gestión de Usuarios y Seguridad](#10-gestión-de-usuarios-y-seguridad)
11. [Mantenimiento del Código](#11-mantenimiento-del-código)
12. [Procedimientos de Respaldo](#12-procedimientos-de-respaldo)
13. [Solución de Problemas Comunes](#13-solución-de-problemas-comunes)
14. [Checklist de Mantenimiento Periódico](#14-checklist-de-mantenimiento-periódico)

---

## 1. Introducción

Esta guía está dirigida al equipo técnico responsable del mantenimiento del **Servicio Interconsulta MIIT**, la API backend que actúa como puente operacional entre el Integrador (PBCU), el Automatizador (SCADA) y el sistema de reportería web.

### Alcance

- Configuración y puesta en marcha del entorno de desarrollo
- Administración de la base de datos PostgreSQL
- Monitoreo y diagnóstico mediante logs
- Gestión de contenedores Docker y despliegue en AWS ECS
- Mantenimiento de integraciones externas
- Procedimientos de respaldo y recuperación
- Resolución de problemas frecuentes

### Audiencia

- Desarrolladores backend (Python/FastAPI)
- Administradores de sistemas / DevOps
- Personal de soporte técnico nivel 2+

---

## 2. Requisitos del Entorno

### 2.1 Software Requerido

| Software | Versión Mínima | Uso |
|----------|---------------|-----|
| Python | 3.12 | Runtime de la aplicación |
| PostgreSQL | 17 | Base de datos |
| Docker | 24+ | Contenedorización |
| Docker Compose | 2.x | Orquestación local |
| Git | 2.x | Control de versiones |
| AWS CLI | 2.x | Despliegue en producción |

### 2.2 Puertos Utilizados

| Puerto | Servicio | Entorno |
|--------|----------|---------|
| 8443 | API (Uvicorn) | Producción / Docker |
| 8000 | API (Uvicorn) | Desarrollo local |
| 5432 | PostgreSQL | Estándar |
| 5517 | PostgreSQL | Docker Compose |
| 5050 | pgAdmin | Docker Compose |

### 2.3 Accesos Requeridos

- Repositorio GitHub: `ItalcolColombia/miit_api`
- AWS Console: ECS, ECR, CloudWatch
- Servidor de base de datos PostgreSQL
- API TurboGraneles (credenciales en `.env`)

---

## 3. Configuración del Entorno Local

### 3.1 Clonar el Repositorio

```bash
git clone https://github.com/ItalcolColombia/miit_api.git
cd miit_api
```

### 3.2 Crear Entorno Virtual

```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3.3 Instalar Dependencias

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 3.4 Configurar Variables de Entorno

Crear un archivo `.env` en la raíz del proyecto con las siguientes variables obligatorias:

```env
# === API ===
API_NAME=MIIT_API
API_HOST=0.0.0.0
API_PORT=8000
API_V1_STR=v1
API_VERSION=1.0.9
API_LOG_LEVEL=DEBUG

# === Base de Datos ===
DB_TYPE=PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nombre_base_datos
DB_USER=usuario_db
DB_PASSWORD=password_db

# === Super Administrador ===
API_USER_ADMINISTRATOR=admin_user
API_PASSWORD_ADMINISTRATOR=admin_password_seguro

# === JWT ===
JWT_SECRET_KEY=clave_secreta_jwt_segura
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=40
JWT_REFRESH_TOKEN_EXPIRE_DAYS=1
JWT_ISSUER=MIIT-API-Authentication
JWT_AUDIENCE=MIIT-API

# === Cifrado ===
ENCRYPTION_KEY=clave_cifrado_segura

# === Timezone ===
APP_TIMEZONE=America/Bogota

# === TurboGraneles (opcional en desarrollo) ===
TG_API_AUTH=
TG_API_URL=
TG_API_USER=
TG_API_PASS=
TG_API_VERIFY_SSL=True
```

> **IMPORTANTE:** El archivo `.env` contiene credenciales sensibles. Nunca debe ser versionado en Git. Verificar que está incluido en `.gitignore`.

### 3.5 Iniciar la Aplicación

```bash
# Desarrollo local directo
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Con Docker Compose
docker compose up -d
```

### 3.6 Verificar el Funcionamiento

```bash
# Health check
curl http://localhost:8000/

# Respuesta esperada:
# {"service": "MIIT_API", "version": "v1", "env": "DEBUG"}

# Documentación interactiva
# Swagger UI: http://localhost:8000/docs
# ReDoc:      http://localhost:8000/redoc
```

---

## 4. Gestión de la Base de Datos

### 4.1 Conexión y Verificación

La API verifica la conexión a la base de datos al iniciar mediante `DatabaseUtil.check_connection()`. Este proceso incluye:

- **Reintentos automáticos:** 12 intentos con 2 segundos de espera entre cada uno
- **Variables de control:** `DB_CHECK_RETRIES` y `DB_CHECK_DELAY` (env vars opcionales)
- **Logging:** Cada intento fallido se registra como WARNING

**Verificar conexión manualmente:**

```bash
# Desde el host
psql -h localhost -p 5432 -U $DB_USER -d $DB_NAME -c "SELECT 1;"

# Desde Docker Compose
docker exec -it bdc psql -U $DB_USER -d $DB_NAME -c "SELECT 1;"
```

### 4.2 Vistas Materializadas

Las vistas materializadas alimentan el sistema de reportería. Deben refrescarse periódicamente para mantener datos actualizados.

**Vistas existentes:**

| Vista | Descripción |
|-------|-------------|
| `v_viajes` | Viajes consolidados con flota y material |
| `v_pesadas_acumulado` | Pesadas acumuladas por transacción |
| `v_usuarios_roles` | Usuarios con rol asignado |
| `v_roles_permisos` | Roles con permisos |
| `v_alm_materiales` | Almacenamientos con materiales y saldos |

**Refrescar vistas desde la API (requiere rol ADMINISTRADOR):**

```bash
# Todas las vistas
curl -X POST http://localhost:8000/api/v1/reportes/refresh \
  -H "Authorization: Bearer $TOKEN"

# Vista específica
curl -X POST http://localhost:8000/api/v1/reportes/RPT_VIAJES/refresh \
  -H "Authorization: Bearer $TOKEN"
```

**Refrescar directamente en PostgreSQL:**

```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY v_viajes;
REFRESH MATERIALIZED VIEW CONCURRENTLY v_pesadas_acumulado;
REFRESH MATERIALIZED VIEW CONCURRENTLY v_usuarios_roles;
REFRESH MATERIALIZED VIEW CONCURRENTLY v_roles_permisos;
REFRESH MATERIALIZED VIEW CONCURRENTLY v_alm_materiales;
```

> **Nota:** Usar `CONCURRENTLY` permite refrescar sin bloquear lecturas, pero requiere un índice único en la vista.

### 4.3 Auditoría (logs_auditoria)

La tabla `logs_auditoria` crece continuamente con cada operación CRUD. Se recomienda:

- **Monitorear tamaño:** Revisar periódicamente el tamaño de la tabla
- **Archivado:** Considerar mover registros antiguos (>90 días) a una tabla de archivo
- **No eliminar:** Los registros de auditoría son evidencia de trazabilidad operacional

```sql
-- Verificar tamaño de la tabla
SELECT pg_size_pretty(pg_total_relation_size('logs_auditoria'));

-- Contar registros por mes
SELECT DATE_TRUNC('month', fecha_hora) AS mes, COUNT(*)
FROM logs_auditoria
GROUP BY mes ORDER BY mes DESC;
```

### 4.4 Tabla de Saldos (almacenamientos_materiales)

Esta tabla mantiene el saldo actual de cada material en cada almacenamiento. Es crítica para la operación.

```sql
-- Verificar saldos actuales
SELECT a.nombre AS almacenamiento, m.nombre AS material, am.saldo
FROM almacenamientos_materiales am
JOIN almacenamientos a ON a.id = am.almacenamiento_id
JOIN materiales m ON m.id = am.material_id
ORDER BY a.nombre, m.nombre;

-- Verificar consistencia: saldo vs suma de movimientos
SELECT am.almacenamiento_id, am.material_id, am.saldo,
       COALESCE(SUM(CASE WHEN mov.accion = 'ENTRADA' THEN mov.peso ELSE -mov.peso END), 0) AS saldo_calculado
FROM almacenamientos_materiales am
LEFT JOIN movimientos mov ON mov.almacenamiento_id = am.almacenamiento_id
  AND mov.material_id = am.material_id
GROUP BY am.almacenamiento_id, am.material_id, am.saldo
HAVING am.saldo != COALESCE(SUM(CASE WHEN mov.accion = 'ENTRADA' THEN mov.peso ELSE -mov.peso END), 0);
```

### 4.5 Ajustes de Saldo

Los ajustes (`ajustes`) permiten corregir discrepancias de inventario. Cada ajuste:

- Registra `saldo_anterior`, `saldo_nuevo` y `delta`
- Requiere un `motivo` descriptivo
- Se vincula al `usuario_id` que lo realizó
- Opcionalmente se vincula a un `movimiento_id`

```sql
-- Últimos ajustes realizados
SELECT a.id, alm.nombre, mat.nombre, a.saldo_anterior, a.saldo_nuevo,
       a.delta, a.motivo, a.fecha_hora
FROM ajustes a
JOIN almacenamientos alm ON alm.id = a.almacenamiento_id
JOIN materiales mat ON mat.id = a.material_id
ORDER BY a.fecha_hora DESC LIMIT 20;
```

---

## 5. Sistema de Logging y Monitoreo

### 5.1 Arquitectura de Logs

El sistema de logging tiene dos capas:

| Capa | Destino | Contenido |
|------|---------|-----------|
| Aplicativo (`LoggerUtil`) | Archivos + Consola | Logs de negocio, errores, debug |
| Supervisord | Archivos | stdout/stderr del proceso Uvicorn |

### 5.2 Ubicación de Archivos de Log

**En producción (Docker):**

```
/var/www/metalsoft/log/
├── miit_api/
│   ├── MIIT_API.log              # Log actual
│   ├── MIIT_API.log.2026-03-25   # Rotación diaria
│   ├── MIIT_API.log.2026-03-24
│   └── ...                       # Últimos 30 días
└── supervisord/
    ├── supervisord.log           # Log del gestor de procesos
    ├── uvicorn_out.log           # stdout de Uvicorn
    └── uvicorn_err.log           # stderr de Uvicorn
```

**En desarrollo local:**

```
miit_api/
└── logs/
    └── miit_api/
        ├── MIIT_API.log
        └── MIIT_API.log.YYYY-MM-DD
```

### 5.3 Formato del Log

```
DD-MM-YYYY | HH:MM:SS - LEVEL - [filename.py:lineno] - mensaje
```

**Ejemplo:**
```
26-03-2026 | 14:30:15 - INFO - [viajes_service.py:142] - Buque MV ATLANTIC registrado exitosamente
26-03-2026 | 14:30:16 - ERROR - [ext_api_service.py:89] - Error al notificar TurboGraneles: timeout
```

### 5.4 Rotación de Logs

- **Mecanismo:** `TimedRotatingFileHandler` con rotación a medianoche
- **Sufijo:** `YYYY-MM-DD`
- **Retención:** 30 días (`backupCount=30`)
- **Encoding:** UTF-8

### 5.5 Niveles de Log

| Nivel | Variable `API_LOG_LEVEL` | Uso |
|-------|-------------------------|-----|
| `DEBUG` | Desarrollo | Incluye logs de Uvicorn, máximo detalle |
| `INFO` | Staging | Operaciones normales, sin debug de framework |
| `WARNING` | — | Situaciones anómalas no críticas |
| `ERROR` | Producción | Solo errores y fallos |
| `CRITICAL` | — | Fallos del sistema |

> **Nota:** Cuando el nivel es distinto de `DEBUG`, se deshabilitan los logs internos de Uvicorn y APScheduler para reducir ruido.

### 5.6 Monitoreo Recomendado

**Indicadores clave a monitorear:**

| Indicador | Dónde buscar | Alerta sugerida |
|-----------|-------------|-----------------|
| Errores 5xx | Logs `ERROR` | >5 errores/minuto |
| Tiempo de respuesta | `TimeMiddleware` en logs | >5 segundos promedio |
| Conexión DB fallida | Logs `WARNING` con "DB not ready" | Cualquier ocurrencia |
| Fallos API TurboGraneles | Logs `ERROR` con "ext_api" | >3 fallos consecutivos |
| Tamaño de logs | Directorio de logs | >1 GB |

**Comandos útiles para análisis:**

```bash
# Buscar errores en el log actual
grep "ERROR" /var/www/metalsoft/log/miit_api/MIIT_API.log

# Errores de las últimas 24 horas
grep "ERROR" /var/www/metalsoft/log/miit_api/MIIT_API.log.$(date +%Y-%m-%d)

# Contar errores por tipo
grep "ERROR" /var/www/metalsoft/log/miit_api/MIIT_API.log | awk -F'- ' '{print $NF}' | sort | uniq -c | sort -rn

# Buscar errores de conexión a DB
grep -i "database\|connection\|DB not ready" /var/www/metalsoft/log/miit_api/MIIT_API.log

# Buscar fallos de API externa
grep -i "turbograneles\|ext_api\|httpx" /var/www/metalsoft/log/miit_api/MIIT_API.log
```

---

## 6. Gestión del Contenedor Docker

### 6.1 Estructura del Contenedor

```
Imagen base: Red Hat UBI 9 (Python 3.12)
    │
    ├── Supervisord (PID 1) ─── gestiona el proceso
    │       │
    │       └── Uvicorn (worker) ─── sirve la API FastAPI
    │
    ├── /var/www/metalsoft/miit_api/    → Código fuente
    ├── /var/www/metalsoft/log/         → Logs (API + Supervisord)
    └── /etc/supervisord.conf           → Configuración de Supervisord
```

### 6.2 Comandos Docker Compose (Desarrollo)

```bash
# Levantar todos los servicios
docker compose up -d

# Ver estado de los servicios
docker compose ps

# Ver logs en tiempo real
docker compose logs -f api
docker compose logs -f bdc

# Reiniciar solo la API
docker compose restart api

# Reconstruir la imagen (después de cambios)
docker compose up -d --build api

# Detener todos los servicios
docker compose down

# Detener y eliminar volúmenes (¡CUIDADO! Borra datos de DB)
docker compose down -v
```

### 6.3 Inspección del Contenedor

```bash
# Entrar al contenedor de la API
docker exec -it api bash

# Verificar el proceso Uvicorn dentro del contenedor
docker exec -it api supervisorctl status

# Ver logs de Supervisord
docker exec -it api cat /var/www/metalsoft/log/supervisord/supervisord.log

# Reiniciar Uvicorn sin reiniciar el contenedor
docker exec -it api supervisorctl restart uvicorn

# Verificar variables de entorno
docker exec -it api env | grep -E "^(API_|DB_|JWT_|TG_)"
```

### 6.4 Healthcheck de la Base de Datos

El servicio `bdc` (PostgreSQL) tiene un healthcheck configurado:

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U postgres"]
  interval: 5s
  timeout: 5s
  retries: 5
```

La API depende de este healthcheck antes de iniciar. Si la API no arranca, verificar primero que PostgreSQL esté healthy:

```bash
docker compose ps  # Verificar columna STATUS
docker exec -it bdc pg_isready -U postgres
```

### 6.5 Volúmenes

| Volumen | Mapeo | Contenido |
|---------|-------|-----------|
| `./logs` → `/var/www/metalsoft/log/miit_api` | Logs de la API (persisten en host) |
| `bdc_data` → `/var/lib/postgresql/data` | Datos de PostgreSQL |
| `pgadmin_data` → `/var/lib/pgadmin` | Configuración de pgAdmin |

---

## 7. Despliegue en Producción (AWS ECS Fargate)

### 7.1 Arquitectura de Producción

```
                   ┌─────────────┐
                   │  AWS ECR    │ ◄── Docker image push
                   │ (Registry)  │
                   └──────┬──────┘
                          │
                   ┌──────▼──────┐
                   │  AWS ECS    │
                   │  Fargate    │
                   │  ┌────────┐ │
                   │  │  Task  │ │ ◄── Contenedor API (puerto 8443)
                   │  └────────┘ │
                   └──────┬──────┘
                          │
                   ┌──────▼──────┐
                   │ PostgreSQL  │ (RDS o instancia dedicada)
                   └─────────────┘
```

### 7.2 Proceso de Despliegue

**Paso 1: Build de la imagen**

```bash
docker build -t miit-api:latest .
```

**Paso 2: Tag para ECR**

```bash
docker tag miit-api:latest <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/miit-api:latest
docker tag miit-api:latest <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/miit-api:v1.0.9
```

**Paso 3: Login y Push a ECR**

```bash
aws ecr get-login-password --region <REGION> | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com

docker push <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/miit-api:latest
docker push <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/miit-api:v1.0.9
```

**Paso 4: Actualizar servicio ECS**

```bash
aws ecs update-service --cluster <CLUSTER_NAME> --service <SERVICE_NAME> --force-new-deployment
```

### 7.3 Variables de Entorno en ECS

Las variables sensibles deben configurarse como **secretos** en la definición de tarea ECS, usando AWS Secrets Manager o SSM Parameter Store:

- `DB_PASSWORD`
- `JWT_SECRET_KEY`
- `ENCRYPTION_KEY`
- `API_PASSWORD_ADMINISTRATOR`
- `TG_API_PASS`

Las variables no sensibles pueden ir directamente en la definición de tarea como variables de entorno.

### 7.4 Verificación Post-Despliegue

```bash
# Verificar el health check
curl https://<DOMAIN>/

# Verificar la versión desplegada
curl https://<DOMAIN>/ | jq .version

# Verificar que la documentación esté accesible
curl -s -o /dev/null -w "%{http_code}" https://<DOMAIN>/docs
```

### 7.5 Rollback

Si la nueva versión presenta problemas:

```bash
# Opción 1: Actualizar tarea ECS con la imagen anterior
aws ecs update-service --cluster <CLUSTER_NAME> --service <SERVICE_NAME> \
  --task-definition <TASK_DEFINITION_ANTERIOR>

# Opción 2: Re-tag de la imagen anterior como latest
docker pull <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/miit-api:v1.0.8
docker tag <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/miit-api:v1.0.8 \
           <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/miit-api:latest
docker push <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/miit-api:latest
aws ecs update-service --cluster <CLUSTER_NAME> --service <SERVICE_NAME> --force-new-deployment
```

---

## 8. Mantenimiento de la Integración Externa (TurboGraneles)

### 8.1 Visión General

La integración con TurboGraneles se realiza mediante `ExtApiService`, un cliente HTTP asíncrono que envía notificaciones REST en tres momentos clave:

| Notificación | Disparador | Endpoint API |
|-------------|-----------|--------------|
| **FinalizaBuque** | Operador finaliza buque | `PUT /integrador/buque-finalizar/{puerto_id}` |
| **CamionCargue** | SCADA finaliza transacción de despacho | `PUT /scada/transaccion-finalizar/{tran_id}` |
| **EnvioFinal** | SCADA ejecuta envío final | `POST /scada/envio-final/{viaje_id}/notify` |

### 8.2 Mecanismo de Reintentos

El `ExtApiService` implementa reintentos automáticos para errores de servidor:

- **Máximo de reintentos:** 3
- **Backoff exponencial:** entre intentos
- **Solo para errores 5xx:** Los errores 4xx no se reintentan
- **Timeout:** 15 segundos por solicitud

### 8.3 Diagnóstico de Fallos

**Verificar conectividad:**

```bash
# Desde el contenedor
docker exec -it api curl -v $TG_API_AUTH

# Verificar certificados SSL
docker exec -it api openssl s_client -connect <TG_HOST>:443 -showcerts
```

**Buscar errores en logs:**

```bash
grep -i "ext_api\|turbograneles\|httpx\|notify" /var/www/metalsoft/log/miit_api/MIIT_API.log
```

**Errores comunes:**

| Error | Causa | Solución |
|-------|-------|----------|
| `ConnectTimeout` | TG API no responde | Verificar red/firewall, contactar TG |
| `SSL: CERTIFICATE_VERIFY_FAILED` | Certificado inválido o expirado | Actualizar `TG_API_SSL_CERT_BASE64` o `ca-certificates` |
| `401 Unauthorized` | Credenciales TG expiradas | Renovar `TG_API_USER` y `TG_API_PASS` en `.env` |
| `422 Unprocessable Entity` | Payload con formato incorrecto | Revisar schemas de envío en `ext_api_schema.py` |

### 8.4 Configuración SSL

Si TurboGraneles usa un certificado personalizado:

1. Obtener el certificado en formato PEM
2. Codificarlo en Base64: `base64 -w 0 cert.pem`
3. Asignar a `TG_API_SSL_CERT_BASE64` en `.env`
4. Verificar que `TG_API_VERIFY_SSL=True`

Para deshabilitar verificación SSL en desarrollo (no recomendado en producción):
```env
TG_API_VERIFY_SSL=False
```

### 8.5 Reenvío Manual de Notificaciones

Si una notificación falló y necesita reenviarse:

```bash
# CamionCargue manual
curl -X POST http://localhost:8000/api/v1/scada/camion-cargue/{viaje_id} \
  -H "Authorization: Bearer $TOKEN"

# EnvioFinal manual (modos: auto, list, single, last)
curl -X POST http://localhost:8000/api/v1/scada/envio-final/{viaje_id}/notify \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"mode": "auto", "items": []}'
```

---

## 9. Mantenimiento del Sistema de Reportería

### 9.1 Arquitectura de Reportes

Los reportes son **metadata-driven**: se definen en las tablas `reportes` y `reportes_columnas` de PostgreSQL, y se alimentan de vistas materializadas.

```
Tabla reportes          → Define el reporte (código, nombre, vista, filtros)
Tabla reportes_columnas → Define las columnas (campo, tipo, formato, totalización)
Tabla permisos_reportes → Define acceso por rol (puede_ver, puede_exportar)
Vista materializada     → Datos del reporte (se refresca periódicamente)
```

### 9.2 Crear un Nuevo Reporte

**Paso 1:** Crear la vista materializada en PostgreSQL:

```sql
CREATE MATERIALIZED VIEW v_mi_nuevo_reporte AS
SELECT
    t.id AS transaccion_id,
    m.nombre AS material,
    t.peso_real,
    t.fecha_inicio
FROM transacciones t
JOIN materiales m ON m.id = t.material_id
WHERE t.estado = 'Finalizado';

-- Crear índice único (requerido para REFRESH CONCURRENTLY)
CREATE UNIQUE INDEX idx_v_mi_nuevo_reporte_id ON v_mi_nuevo_reporte(transaccion_id);
```

**Paso 2:** Registrar el reporte en la tabla `reportes`:

```sql
INSERT INTO reportes (codigo, nombre, descripcion, vista_nombre, campo_fecha,
                      permite_exportar_pdf, permite_exportar_csv, permite_exportar_excel,
                      requiere_rango_fechas, permite_filtrar_material, activo, orden)
VALUES ('RPT_NUEVO', 'Mi Nuevo Reporte', 'Descripción del reporte',
        'v_mi_nuevo_reporte', 'fecha_inicio',
        true, true, false,
        true, true, true, 10);
```

**Paso 3:** Definir las columnas en `reportes_columnas`:

```sql
INSERT INTO reportes_columnas (reporte_id, campo, nombre_mostrar, tipo_dato, visible, orden,
                                ordenable, filtrable, es_totalizable, tipo_totalizacion)
VALUES
  ((SELECT id FROM reportes WHERE codigo = 'RPT_NUEVO'), 'transaccion_id', 'ID Transacción', 'number', true, 1, true, false, false, null),
  ((SELECT id FROM reportes WHERE codigo = 'RPT_NUEVO'), 'material', 'Material', 'string', true, 2, true, true, false, null),
  ((SELECT id FROM reportes WHERE codigo = 'RPT_NUEVO'), 'peso_real', 'Peso Real', 'number', true, 3, true, false, true, 'sum'),
  ((SELECT id FROM reportes WHERE codigo = 'RPT_NUEVO'), 'fecha_inicio', 'Fecha', 'datetime', true, 4, true, false, false, null);
```

**Paso 4:** Asignar permisos por rol:

```sql
INSERT INTO permisos_reportes (rol_id, codigo_reporte, reporte_id, puede_ver, puede_exportar)
SELECT r.id, 'RPT_NUEVO', (SELECT id FROM reportes WHERE codigo = 'RPT_NUEVO'), true, true
FROM roles r WHERE r.nombre IN ('ADMINISTRADOR', 'SUPERVISOR');
```

### 9.3 Modificar un Reporte Existente

**Agregar una columna:**

```sql
INSERT INTO reportes_columnas (reporte_id, campo, nombre_mostrar, tipo_dato, visible, orden,
                                ordenable, es_totalizable, tipo_totalizacion)
VALUES ((SELECT id FROM reportes WHERE codigo = 'RPT_VIAJES'),
        'nuevo_campo', 'Nuevo Campo', 'string', true, 99, true, false, null);
```

**Modificar visibilidad u orden:**

```sql
UPDATE reportes_columnas
SET visible = false
WHERE reporte_id = (SELECT id FROM reportes WHERE codigo = 'RPT_VIAJES')
  AND campo = 'campo_a_ocultar';
```

**Cambiar totalización:**

```sql
UPDATE reportes_columnas
SET es_totalizable = true, tipo_totalizacion = 'avg'
WHERE reporte_id = (SELECT id FROM reportes WHERE codigo = 'RPT_VIAJES')
  AND campo = 'peso_real';
```

### 9.4 Refrescar Vistas Materializadas

**Refresco manual desde la API:**

```bash
# Todas las vistas
curl -X POST https://<DOMAIN>/api/v1/reportes/refresh \
  -H "Authorization: Bearer $TOKEN"

# Vista específica
curl -X POST https://<DOMAIN>/api/v1/reportes/RPT_VIAJES/refresh \
  -H "Authorization: Bearer $TOKEN"
```

**Refresco programado (recomendado en producción):**

Configurar un cron job o tarea programada para refrescar las vistas:

```bash
# Crontab ejemplo: refrescar cada hora
0 * * * * curl -s -X POST https://<DOMAIN>/api/v1/reportes/refresh -H "Authorization: Bearer $TOKEN"
```

### 9.5 Exportación

| Formato | Estado | Servicio |
|---------|--------|----------|
| PDF | Activo | `exportacion_service.exportar_pdf()` — ReportLab |
| CSV | Activo | `exportacion_service.exportar_csv()` — pandas |
| Excel | Temporalmente deshabilitado | `exportacion_service.exportar_excel()` — openpyxl |

**Nota sobre PDF:** La generación adapta automáticamente la orientación (portrait ≤5 columnas, landscape >5), el tamaño de fuente y los anchos de columna según la cantidad de datos.

---

## 10. Gestión de Usuarios y Seguridad

### 10.1 Roles del Sistema

| Rol | Acceso |
|-----|--------|
| `COLABORADOR` | Consulta de reportes asignados |
| `SUPERVISOR` | Reportes con permisos extendidos |
| `INTEGRADOR` | Endpoints `/integrador/*` + reportes |
| `AUTOMATIZADOR` | Endpoints `/scada/*` + reportes |
| `ADMINISTRADOR` | Todos los endpoints operacionales + admin |
| `SUPER_ADMINISTRATOR` | Acceso total al sistema |

### 10.2 Gestión de Usuarios vía API

```bash
# Crear usuario
curl -X POST https://<DOMAIN>/api/v1/admin/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nick_name": "nuevo_usuario",
    "full_name": "Nombre Completo",
    "cedula": "123456789",
    "email": "usuario@ejemplo.com",
    "clave": "Password1!",
    "rol_id": 3
  }'

# Listar usuarios
curl https://<DOMAIN>/api/v1/admin/ \
  -H "Authorization: Bearer $TOKEN"

# Cambiar contraseña
curl -X PATCH https://<DOMAIN>/api/v1/admin/{user_id}/change-password \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"clave_actual": "OldPass1!", "clave_nueva": "NewPass1!"}'
```

### 10.3 Política de Contraseñas

Las contraseñas deben cumplir (validado en `core/validators/password.py`):

- Al menos **1 dígito** (`0-9`)
- Al menos **1 letra mayúscula** (`A-Z`)
- Al menos **1 carácter especial** (`!¡/@#$%^&*(),.¿?":{}|<>`)

### 10.4 Tokens JWT

**Ciclo de vida del token:**

1. Login → Se genera access token (40 min) + refresh token (1 día)
2. Cada request envía el access token en `Authorization: Bearer <token>`
3. Antes de que expire, el frontend usa `/auth/token/refresh` para renovar
4. Si ambos tokens expiran, el usuario debe re-autenticarse

**Seguridad del JWT:**

- Firmado con `HS256` usando `JWT_SECRET_KEY`
- Incluye `issuer` y `audience` para validación adicional
- No almacena información sensible en el payload

> **IMPORTANTE:** Si se sospecha que `JWT_SECRET_KEY` fue comprometida, cambiarla inmediatamente en `.env` y reiniciar la API. Esto invalidará TODOS los tokens activos.

### 10.5 Cifrado de Datos

La `ENCRYPTION_KEY` se utiliza para cifrar datos sensibles en la base de datos (via `encryption_service.py`). Si se pierde esta clave, los datos cifrados no podrán recuperarse.

**Recomendaciones:**
- Respaldar `ENCRYPTION_KEY` en un gestor de secretos (AWS Secrets Manager)
- Nunca rotar esta clave sin un plan de migración de datos cifrados
- Documentar qué campos están cifrados

---

## 11. Mantenimiento del Código

### 11.1 Estructura de Capas

Al agregar nueva funcionalidad, respetar la arquitectura en capas:

```
1. Endpoint (api/v1/endpoints/)     → Recibe request, valida, retorna response
2. Schema (schemas/)                → Define DTOs de entrada/salida (Pydantic)
3. Service (services/)              → Lógica de negocio
4. Repository (repositories/)       → Acceso a datos (hereda de IRepository)
5. Model (database/models.py)       → Definición ORM (SQLAlchemy)
```

### 11.2 Agregar un Nuevo Endpoint

**Ejemplo: agregar `GET /scada/nuevo-endpoint`**

**1. Definir el schema** en `schemas/nuevo_schema.py`:

```python
from schemas.base_schema import BaseSchema

class NuevoResponse(BaseSchema):
    id: int
    nombre: str
```

**2. Agregar al servicio** existente o crear uno nuevo en `services/`:

```python
class NuevoService:
    def __init__(self, repository):
        self.repository = repository

    async def obtener_datos(self):
        return await self.repository.get_all()
```

**3. Registrar inyección de dependencias** en `core/di/service_injection.py`:

```python
def get_nuevo_service(repo=Depends(get_nuevo_repository)):
    return NuevoService(repository=repo)
```

**4. Crear el endpoint** en el archivo correspondiente (e.g., `etl.py`):

```python
@router.get("/nuevo-endpoint", response_model=list[NuevoResponse])
async def get_nuevo_endpoint(service=Depends(get_nuevo_service)):
    return await service.obtener_datos()
```

### 11.3 Agregar un Nuevo Modelo

```python
# En database/models.py
class NuevaEntidad(Base):
    __tablename__ = "nueva_entidad"
    id = Column(BigInteger, Identity(), primary_key=True)
    nombre = Column(String, nullable=False)
    fecha_hora = Column(DateTime(timezone=True), default=func.now())
    usuario_id = Column(BigInteger, nullable=True)
```

> **Nota:** No se utiliza Alembic para migraciones. Los cambios de esquema se aplican directamente en PostgreSQL con scripts SQL.

### 11.4 Convenciones del Proyecto

| Aspecto | Convención |
|---------|-----------|
| Nombres de tablas | snake_case, plural (`viajes`, `transacciones`) |
| Nombres de columnas | snake_case (`peso_real`, `fecha_hora`) |
| Nombres de clases (modelos) | PascalCase, singular (`Viaje`, `Transaccion`) |
| Nombres de schemas | PascalCase + sufijo (`ViajeCreate`, `ViajeResponse`) |
| Nombres de servicios | PascalCase + Service (`ViajesService`) |
| Nombres de repositorios | PascalCase + Repository (`ViajesRepository`) |
| Endpoints | kebab-case (`/buque-registro`, `/camion-ingreso`) |
| Timezone | Siempre `America/Bogota` |
| IDs | `BigInteger` con `Identity()` |
| Audit fields | `fecha_hora` + `usuario_id` en todas las tablas |

### 11.5 Actualizar Dependencias

```bash
# Ver dependencias desactualizadas
pip list --outdated

# Actualizar una dependencia específica
pip install --upgrade fastapi

# Regenerar requirements.txt (si se usa pip freeze)
pip freeze > requirements.txt
```

> **Precaución:** Antes de actualizar dependencias en producción, probar exhaustivamente en desarrollo. Especialmente cuidado con actualizaciones mayores de FastAPI, SQLAlchemy y Pydantic.

---

## 12. Procedimientos de Respaldo

### 12.1 Base de Datos PostgreSQL

**Respaldo completo (pg_dump):**

```bash
# Desde el host (Docker Compose)
docker exec -t bdc pg_dump -U $DB_USER -d $DB_NAME -F c -f /tmp/backup.dump
docker cp bdc:/tmp/backup.dump ./backups/miit_db_$(date +%Y%m%d_%H%M%S).dump

# Desde un host con acceso directo
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -F c -f backup.dump
```

**Respaldo solo de datos críticos:**

```sql
-- Exportar tabla específica
\COPY (SELECT * FROM viajes WHERE fecha_hora > NOW() - INTERVAL '30 days') TO '/tmp/viajes_recientes.csv' CSV HEADER;

-- Exportar ajustes
\COPY (SELECT * FROM ajustes) TO '/tmp/ajustes_full.csv' CSV HEADER;
```

**Restauración:**

```bash
# Restaurar desde dump
pg_restore -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c backup.dump

# Restaurar en una base de datos nueva
createdb -h $DB_HOST -p $DB_PORT -U $DB_USER miit_db_restored
pg_restore -h $DB_HOST -p $DB_PORT -U $DB_USER -d miit_db_restored backup.dump
```

### 12.2 Variables de Entorno

Respaldar el archivo `.env` de forma segura:

```bash
# Cifrar con GPG antes de respaldar
gpg --symmetric --cipher-algo AES256 .env
# Genera .env.gpg

# Para restaurar
gpg --decrypt .env.gpg > .env
```

> **Recomendación:** Almacenar las credenciales en AWS Secrets Manager como fuente de verdad. El `.env` es solo para uso local.

### 12.3 Imágenes Docker

```bash
# Exportar imagen como archivo tar
docker save miit-api:v1.0.9 | gzip > miit-api-v1.0.9.tar.gz

# Restaurar imagen desde archivo
docker load < miit-api-v1.0.9.tar.gz
```

### 12.4 Frecuencia Recomendada de Respaldos

| Componente | Frecuencia | Retención | Método |
|-----------|-----------|-----------|--------|
| Base de datos completa | Diario | 30 días | pg_dump + almacenamiento externo |
| Base de datos incremental | Cada 6 horas | 7 días | WAL archiving (si configurado) |
| Variables de entorno | Por cada cambio | Indefinida | AWS Secrets Manager |
| Imágenes Docker | Por cada release | 5 versiones | AWS ECR (tags versionados) |
| Logs de aplicación | Automático | 30 días | Rotación de LoggerUtil |

---

## 13. Solución de Problemas Comunes

### 13.1 La API no Inicia

| Síntoma | Causa Probable | Solución |
|---------|---------------|----------|
| `Error en database_util` | DB no accesible | Verificar que PostgreSQL esté corriendo y las credenciales en `.env` |
| `ValidationError` al startup | Variable `.env` faltante | Revisar que todas las variables requeridas estén en `.env` |
| `Address already in use` | Puerto ocupado | Verificar que no haya otra instancia: `lsof -i :8443` o `netstat -tlnp | grep 8443` |
| Container reinicia en loop | Error en startup | `docker compose logs api` para ver el error |

### 13.2 Errores de Autenticación

| Síntoma | Causa | Solución |
|---------|-------|----------|
| `401 - No se pudieron validar las credenciales del token` | Token expirado o inválido | Renovar con `/auth/token/refresh` o re-login |
| `403 - Forbidden` | Rol sin permisos para el endpoint | Verificar rol del usuario vs roles requeridos del endpoint |
| `401` en todos los endpoints | `JWT_SECRET_KEY` cambiada | Todos los tokens quedan inválidos, los usuarios deben re-login |

### 13.3 Errores de Base de Datos

| Síntoma | Causa | Solución |
|---------|-------|----------|
| `DatabaseConnectionException (502)` | PostgreSQL caído o inalcanzable | Verificar servicio PostgreSQL, red, firewall |
| `DatabaseSQLAlchemyException (500)` | Error en query/ORM | Revisar logs para el SQL fallido, verificar esquema |
| `DatabaseTypeMismatchException (422)` | Tipo incompatible en filtro | Verificar los tipos de datos enviados en la query |
| Datos desactualizados en reportes | Vista materializada no refrescada | `POST /reportes/refresh` |

### 13.4 Errores de Integración TurboGraneles

| Síntoma | Causa | Solución |
|---------|-------|----------|
| `ConnectTimeout` | Red/Firewall | Verificar conectividad desde el contenedor |
| `SSL: CERTIFICATE_VERIFY_FAILED` | Cert expirado | Actualizar certificado en `TG_API_SSL_CERT_BASE64` |
| `401` de TG | Credenciales expiradas | Actualizar `TG_API_USER`/`TG_API_PASS` |
| Notificación no enviada | Error silencioso | Buscar en logs: `grep "ext_api\|notify" MIIT_API.log` |

### 13.5 Problemas de Rendimiento

| Síntoma | Causa | Solución |
|---------|-------|----------|
| Reportes lentos | Vista no refrescada o sin índices | Refrescar vista + verificar índices |
| Alta latencia general | Pool de conexiones DB agotado | Verificar conexiones activas en PostgreSQL |
| Memoria alta del contenedor | Exportación de reportes grandes | Verificar tamaño de datos exportados, considerar paginación |
| Logs ocupan mucho disco | Acumulación >30 días | Verificar rotación, limpiar logs antiguos manualmente |

### 13.6 Problemas de Timezone

| Síntoma | Causa | Solución |
|---------|-------|----------|
| Fechas con desfase de 5 horas | Timezone no configurado | Verificar `APP_TIMEZONE=America/Bogota` y `TZ=America/Bogota` |
| Filtros de fecha no coinciden | Naive vs aware datetime | Los filtros deben usar formato ISO con zona |
| Hora incorrecta en logs | Contenedor con TZ diferente | Verificar `TZ` en docker-compose y Dockerfile |

---

## 14. Checklist de Mantenimiento Periódico

### 14.1 Diario

- [ ] Verificar que la API responde correctamente (`GET /`)
- [ ] Revisar logs de ERROR del día actual
- [ ] Verificar que las notificaciones a TurboGraneles se enviaron correctamente
- [ ] Confirmar que no hay alertas en CloudWatch / monitoreo

### 14.2 Semanal

- [ ] Revisar crecimiento de la tabla `logs_auditoria`
- [ ] Verificar espacio en disco de logs
- [ ] Revisar saldos de `almacenamientos_materiales` para inconsistencias
- [ ] Verificar que las vistas materializadas se están refrescando
- [ ] Revisar intentos de acceso no autorizados en logs

### 14.3 Mensual

- [ ] Revisar y rotar logs antiguos si la rotación automática no aplica
- [ ] Verificar respaldos de base de datos y hacer prueba de restauración
- [ ] Revisar dependencias por vulnerabilidades de seguridad (`pip audit`)
- [ ] Verificar expiración de certificados SSL (TurboGraneles y propios)
- [ ] Revisar usuarios inactivos o con roles innecesarios
- [ ] Verificar tamaño total de la base de datos

### 14.4 Trimestral

- [ ] Evaluar rendimiento general de queries y reportes
- [ ] Revisar y actualizar dependencias Python (en entorno de staging)
- [ ] Verificar que los respaldos de AWS Secrets Manager estén actualizados
- [ ] Analizar registros de auditoría para detectar patrones anómalos
- [ ] Considerar archivado de registros históricos (auditoría, logs)
- [ ] Revisar configuración de ECS (CPU, memoria, escalado)

### 14.5 Por Release / Despliegue

- [ ] Actualizar `API_VERSION_NUM` en `settings.py`
- [ ] Ejecutar tests locales
- [ ] Verificar que `.env` de producción tiene las variables necesarias
- [ ] Build y push de imagen Docker a ECR
- [ ] Desplegar en ECS y verificar health check
- [ ] Verificar `/docs` para confirmar que los nuevos endpoints aparecen
- [ ] Probar endpoints nuevos/modificados
- [ ] Monitorear logs por 30 minutos post-despliegue
- [ ] Documentar cambios en el changelog

---

*Guía de Mantenimiento generada el 26 de marzo de 2026 — Servicio Interconsulta MIIT v1.0.9*
