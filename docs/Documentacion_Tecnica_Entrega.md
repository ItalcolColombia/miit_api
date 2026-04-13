# Documentación Técnica de Entrega

## Servicio Interconsulta MIIT — Backend API

**Versión:** 1.1.2
**Fecha de entrega:** 26 de marzo de 2026
**Proyecto:** Puerto Antioquia — Urabá
**Desarrollado por:** Metalteco S.A.S

---

## Tabla de Contenido

1. [Descripción General](#1-descripción-general)
2. [Arquitectura del Sistema](#2-arquitectura-del-sistema)
3. [Estructura del Proyecto](#3-estructura-del-proyecto)
4. [Stack Tecnológico](#4-stack-tecnológico)
5. [Configuración y Variables de Entorno](#5-configuración-y-variables-de-entorno)
6. [Base de Datos](#6-base-de-datos)
7. [Flujos Operacionales](#7-flujos-operacionales)
8. [Endpoints de la API](#8-endpoints-de-la-api)
9. [Sistema de Autenticación y Autorización](#9-sistema-de-autenticación-y-autorización)
10. [Integración con API Externa (TurboGraneles)](#10-integración-con-api-externa-turbograneles)
11. [Sistema de Reportería](#11-sistema-de-reportería)
12. [Middleware y Manejo de Errores](#12-middleware-y-manejo-de-errores)
13. [Auditoría y Trazabilidad](#13-auditoría-y-trazabilidad)
14. [Despliegue](#14-despliegue)
15. [Dependencias](#15-dependencias)

---

## 1. Descripción General

El **Servicio Interconsulta MIIT** es una API REST desarrollada en **FastAPI** que actúa como el puente operacional central entre los dos sistemas principales de la operación portuaria de Puerto Antioquia:

- **Integrador (PBCU):** Sistema del operador portuario que gestiona la llegada de buques, registro de BLs (Bills of Lading), ingreso/egreso de camiones y levantes de carga.
- **Automatizador (SCADA):** Sistema de automatización que controla las transacciones de movimiento de materiales, pesajes en báscula, almacenamiento y despacho.

Además de este rol como puente operacional, la API soporta:

- **Sistema de reportería** para la aplicación web MIIT Reportes Web (frontend).
- **Notificaciones externas** al sistema de TurboGraneles mediante integración REST.
- **Administración de usuarios** con control de acceso basado en roles (RBAC).
- **Auditoría completa** de todas las operaciones CRUD con snapshots JSON.

### Diagrama de Contexto

```
┌──────────────┐         ┌─────────────────────────┐         ┌──────────────────┐
│  Integrador  │◄───────►│                         │◄───────►│  Automatizador   │
│   (PBCU)     │  REST   │   Servicio Interconsulta│  REST   │    (SCADA)       │
│              │         │        MIIT API         │         │                  │
└──────────────┘         │       v1.1.2            │         └──────────────────┘
                         │                         │
                         │   ┌─────────────────┐   │         ┌──────────────────┐
                         │   │   PostgreSQL 17  │   │────────►│  TurboGraneles   │
                         │   │   BD Central     │   │  REST   │   (API Externa)  │
                         │   └─────────────────┘   │         └──────────────────┘
                         │                         │
                         └────────────┬────────────┘
                                      │ REST
                              ┌───────┴───────┐
                              │ MIIT Reportes │
                              │   Web (Front) │
                              └───────────────┘
```

---

## 2. Arquitectura del Sistema

### 2.1 Patrón Arquitectónico

La API implementa una **arquitectura en capas** con el patrón Repository, separando responsabilidades de forma clara:

```
Endpoints (Controllers)
    │
    ▼
Services (Business Logic)
    │
    ▼
Repositories (Data Access)
    │
    ▼
Database (PostgreSQL + SQLAlchemy ORM)
```

### 2.2 Inyección de Dependencias

Se utiliza el sistema de **Dependency Injection** nativo de FastAPI, organizado en tres módulos dentro de `core/di/`:

| Módulo | Responsabilidad |
|--------|----------------|
| `database_injection.py` | Provee sesiones de base de datos (`get_db`) |
| `repository_injection.py` | Instancia repositorios con su `Auditor` |
| `service_injection.py` | Instancia servicios con sus repositorios |

### 2.3 Stack de Middleware

Los middlewares se ejecutan en **orden inverso** al que se registran. El orden de ejecución para una solicitud entrante es:

```
Solicitud → CORS → Time → Logger → Error → Auth → GZip → Session → Endpoint
Respuesta ← CORS ← Time ← Logger ← Error ← Auth ← GZip ← Session ← Endpoint
```

| Middleware | Función |
|-----------|---------|
| `CORSMiddleware` | Maneja solicitudes preflight y headers CORS |
| `TimeMiddleware` | Registra tiempo de procesamiento de cada request |
| `LoggerMiddleware` | Logging estructurado de request/response |
| `ErrorMiddleware` | Captura excepciones no controladas |
| `AuthMiddleware` | Validación JWT y contexto de usuario |
| `GZipMiddleware` | Compresión de respuestas (>1000 bytes) |
| `SessionMiddleware` | Manejo de sesiones con clave secreta JWT |

---

## 3. Estructura del Proyecto

```
miit_api/
├── main.py                          # Punto de entrada FastAPI
├── Dockerfile                       # Imagen Docker (Red Hat UBI 9)
├── docker-compose.yml               # Orquestación local (API + DB + pgAdmin)
├── requirements.txt                 # Dependencias Python
├── supervisord.conf                 # Configuración del gestor de procesos
├── start.sh                         # Script de inicio
├── .env                             # Variables de entorno (no versionado)
│
├── api/
│   └── v1/
│       ├── routes.py                # Agregador de rutas
│       └── endpoints/
│           ├── auth.py              # Autenticación (POST /auth)
│           ├── etl.py               # SCADA/Automatizador (POST/GET /scada/*)
│           ├── operador.py          # Integrador/PBCU (POST/PUT/GET /integrador/*)
│           ├── profile.py           # Perfil de usuario autenticado
│           ├── reportes.py          # Reportería y exportación
│           └── admin/
│               ├── admin.py         # Gestión de usuarios
│               ├── admin_reportes.py# Administración de reportes
│               └── admin_roles.py   # Administración de roles
│
├── core/
│   ├── config/
│   │   └── settings.py              # Configuración centralizada (pydantic-settings)
│   ├── contracts/                   # Interfaces/contratos (Auditor, etc.)
│   ├── di/                          # Inyección de dependencias
│   │   ├── database_injection.py
│   │   ├── repository_injection.py
│   │   └── service_injection.py
│   ├── enums/                       # Enumeraciones del sistema
│   │   ├── database_enum.py         # DatabaseTypeEnum
│   │   ├── user_permission_enum.py  # UserPermissionEnum (CRUD)
│   │   ├── user_role_enum.py        # UserRoleEnum (6 roles)
│   │   └── user_status_enum.py      # UserStatusEnum
│   ├── exceptions/                  # Excepciones personalizadas
│   │   ├── base_exception.py        # BasedException (raíz)
│   │   ├── auth_exception.py        # Credenciales y tokens
│   │   ├── db_exception.py          # Conexión y queries
│   │   ├── entity_exceptions.py     # Entidad no encontrada / duplicada
│   │   └── jwt_exception.py         # Token no autorizado
│   ├── handlers/
│   │   └── exception_handler.py     # Manejador global de excepciones
│   ├── middleware/
│   │   ├── auth_middleware.py        # Validación JWT por request
│   │   ├── error_middleware.py       # Captura de errores no controlados
│   │   ├── logger_middleware.py      # Logging de requests
│   │   └── time_middleware.py        # Medición de tiempos
│   └── validators/
│       └── password.py              # Complejidad de contraseña
│
├── database/
│   └── models.py                    # Modelos SQLAlchemy ORM (20+ entidades)
│
├── repositories/
│   ├── base_repository.py           # Repositorio genérico (IRepository[M, S])
│   ├── viajes_repository.py
│   ├── pesadas_repository.py
│   ├── transacciones_repository.py
│   ├── movimientos_repository.py
│   ├── bls_repository.py
│   ├── almacenamientos_repository.py
│   ├── almacenamientos_materiales_repository.py
│   ├── clientes_repository.py
│   ├── flotas_repository.py
│   ├── materiales_repository.py
│   ├── usuarios_repository.py
│   ├── roles_repository.py
│   ├── ajustes_repository.py
│   ├── consumos_entrada_parcial_repository.py
│   ├── pesadas_corte_repository.py
│   ├── saldo_snapshot_repository.py
│   └── reportes/                    # Repositorios de reportería
│
├── schemas/
│   ├── base_schema.py               # BaseSchema, respuestas genéricas
│   ├── viajes_schema.py
│   ├── pesadas_schema.py
│   ├── transacciones_schema.py
│   ├── movimientos_schema.py
│   ├── bls_schema.py
│   ├── almacenamientos_schema.py
│   ├── almacenamientos_materiales_schema.py
│   ├── clientes_schema.py
│   ├── flotas_schema.py
│   ├── materiales_schema.py
│   ├── usuarios_schema.py
│   ├── roles_schema.py
│   ├── ajustes_schema.py
│   ├── consumos_entrada_parcial_schema.py
│   ├── pesadas_corte_schema.py
│   ├── saldo_snapshot_schema.py
│   ├── ext_api_schema.py
│   ├── logs_auditoria_schema.py
│   ├── response_models.py
│   └── reportes/                    # Schemas de reportería
│
├── services/
│   ├── auth_service.py              # Autenticación y JWT
│   ├── viajes_service.py            # Lógica de viajes/buques/camiones
│   ├── pesadas_service.py           # Lógica de pesajes
│   ├── transacciones_service.py     # Lógica de transacciones
│   ├── movimientos_service.py       # Lógica de movimientos
│   ├── bls_service.py               # Lógica de Bills of Lading
│   ├── almacenamientos_service.py   # Lógica de almacenamientos
│   ├── almacenamientos_materiales_service.py
│   ├── clientes_service.py
│   ├── flotas_service.py
│   ├── materiales_service.py
│   ├── usuarios_service.py
│   ├── ajustes_service.py           # Ajustes de saldo
│   ├── envio_final_service.py       # Preparación de envíos finales
│   ├── ext_api_service.py           # Cliente HTTP para API externa
│   ├── encryption_service.py        # Cifrado de datos sensibles
│   ├── email_service.py             # Envío de correos
│   ├── logs_auditoria_service.py    # Servicio de auditoría
│   └── reportes/
│       ├── reportes_service.py      # Lógica de consulta de reportes
│       └── exportacion_service.py   # Exportación PDF/Excel/CSV
│
├── utils/
│   ├── database_util.py             # Verificación de conexión DB
│   ├── jwt_util.py                  # Codificación/decodificación JWT
│   ├── logger_util.py               # Logger con colorlog
│   ├── message_util.py              # Mensajes de startup
│   ├── response_util.py             # Utilidades de respuesta HTTP
│   ├── serialize_util.py            # Serialización con orjson
│   ├── time_util.py                 # Timezone y fechas (America/Bogota)
│   ├── any_utils.py                 # Utilidades generales
│   └── dot_env_util.py              # Verificación de .env
│
├── tests/                           # Tests del proyecto
├── scripts/                         # Scripts auxiliares (SQL, Python)
├── certs/                           # Certificados SSL
├── logs/                            # Logs de la aplicación
└── docs/                            # Documentación del proyecto
```

---

## 4. Stack Tecnológico

### 4.1 Lenguaje y Framework

| Componente | Tecnología | Versión |
|-----------|-----------|---------|
| Lenguaje | Python | 3.12 |
| Framework | FastAPI | latest |
| Servidor ASGI | Uvicorn | ≥0.25.0 |
| Validación | Pydantic | ≥2.5.0 |
| Configuración | pydantic-settings | ≥2.1.0 |

### 4.2 Base de Datos

| Componente | Tecnología | Versión |
|-----------|-----------|---------|
| Motor | PostgreSQL | 17 |
| ORM | SQLAlchemy (async) | ≥2.0.23 |
| Driver async | asyncpg | ≥0.29.0 |

### 4.3 Seguridad

| Componente | Tecnología | Versión |
|-----------|-----------|---------|
| JWT | PyJWT | ≥2.8.0 |
| Hashing | bcrypt | ≥4.1.0 |
| Cifrado | cryptography | ≥41.0.0 |

### 4.4 Exportación y Reportería

| Componente | Tecnología | Uso |
|-----------|-----------|-----|
| pandas | ≥2.1.0 | Procesamiento de datos / CSV |
| openpyxl | ≥3.1.0 | Exportación Excel (.xlsx) |
| ReportLab | ≥4.0.0 | Generación PDF |

### 4.5 Comunicación y Serialización

| Componente | Tecnología | Uso |
|-----------|-----------|-----|
| httpx | ≥0.26.0 | Cliente HTTP async (API TurboGraneles) |
| orjson | ≥3.9.0 | Serialización JSON de alto rendimiento |

### 4.6 Infraestructura

| Componente | Tecnología |
|-----------|-----------|
| Contenedor base | Red Hat UBI 9 (Python 3.12) |
| Gestor de procesos | Supervisord |
| Orquestación (prod) | AWS ECS Fargate |
| Orquestación (local) | Docker Compose |

---

## 5. Configuración y Variables de Entorno

La configuración se centraliza en `core/config/settings.py` usando **pydantic-settings** con carga automática desde `.env`.

### 5.1 Variables de la API

| Variable | Tipo | Default | Descripción |
|----------|------|---------|-------------|
| `API_NAME` | str | `MIIT_API` | Nombre del servicio |
| `API_HOST` | str | `0.0.0.0` | Host de escucha |
| `API_PORT` | int | `8000` | Puerto de escucha |
| `API_V1_STR` | str | `v1` | Prefijo de versión |
| `API_VERSION_NUM` | str | `1.1.2` | Versión actual |
| `API_LOG_LEVEL` | str | `DEBUG` | Nivel de logging |
| `APP_LOG_DIR` | str | `/var/www/metalsoft/logs/miit_api/` | Directorio de logs |
| `ALLOWED_HOSTS` | list | (ver settings.py) | Hosts permitidos |
| `CORS_ORIGINS` | list | (ver settings.py) | Orígenes CORS permitidos |

### 5.2 Variables Sensibles (solo en .env)

| Variable | Tipo | Descripción |
|----------|------|-------------|
| `API_USER_ADMINISTRATOR` | str | Usuario super-admin |
| `API_PASSWORD_ADMINISTRATOR` | SecretStr | Contraseña super-admin |
| `DB_USER` | str | Usuario de base de datos |
| `DB_PASSWORD` | SecretStr | Contraseña de base de datos |
| `DB_NAME` | str | Nombre de base de datos |
| `JWT_SECRET_KEY` | SecretStr | Clave secreta para tokens JWT |
| `ENCRYPTION_KEY` | SecretStr | Clave de cifrado |

### 5.3 Variables de Base de Datos

| Variable | Tipo | Default | Descripción |
|----------|------|---------|-------------|
| `DB_TYPE` | str | `PostgreSQL` | Tipo de motor |
| `DB_HOST` | str | `localhost` | Host del servidor |
| `DB_PORT` | str | `5432` | Puerto del servidor |

### 5.4 Variables JWT

| Variable | Tipo | Default | Descripción |
|----------|------|---------|-------------|
| `JWT_ALGORITHM` | str | `HS256` | Algoritmo de firma |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | int | `40` | Expiración del access token |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | int | `1` | Expiración del refresh token |
| `JWT_ISSUER` | str | `MIIT-API-Authentication` | Emisor del token |
| `JWT_AUDIENCE` | str | `MIIT-API` | Audiencia del token |

### 5.5 Variables de API Externa (TurboGraneles)

| Variable | Tipo | Default | Descripción |
|----------|------|---------|-------------|
| `TG_API_AUTH` | str | `""` | URL de autenticación |
| `TG_API_URL` | str | `""` | URL base de la API |
| `TG_API_USER` | str | `None` | Usuario de autenticación |
| `TG_API_PASS` | SecretStr | `None` | Contraseña de autenticación |
| `TG_API_ACCEPTS_LIST` | bool | `False` | Si acepta listas en payload |
| `TG_API_VERIFY_SSL` | str | `True` | Verificación SSL |
| `TG_API_SSL_CERT_BASE64` | str | `None` | Certificado SSL en Base64 |

### 5.6 Variables de Email

| Variable | Tipo | Default | Descripción |
|----------|------|---------|-------------|
| `SMTP_HOST` | str | `smtp.example.com` | Servidor SMTP |
| `SMTP_PORT` | str | `587` | Puerto SMTP |
| `SMTP_USER` | str | `None` | Usuario SMTP |
| `SMTP_PASSWORD` | SecretStr | `None` | Contraseña SMTP |

### 5.7 Feature Flags

| Variable | Tipo | Default | Descripción |
|----------|------|---------|-------------|
| `ALMACENAMIENTO_DESPACHO_DIRECTO_ID` | int | `0` | ID del almacenamiento virtual para despacho directo |

---

## 6. Base de Datos

### 6.1 Motor y Conexión

- **Motor:** PostgreSQL 17
- **Driver:** asyncpg (conexión asíncrona)
- **ORM:** SQLAlchemy 2.0+ con soporte async
- **Timezone:** Todas las columnas `fecha_hora` usan `America/Bogota`

### 6.2 Modelo Entidad-Relación

#### Entidades Operacionales Principales

```
Flotas ──1:M──► Viajes ──1:M──► Transacciones ──1:M──► Movimientos
                  │                    │                      │
                  │                    ├──1:M──► Pesadas      │
                  │                    │                      │
                  ├──1:M──► Bls       ├──M:1──► Materiales ◄─┤
                  │         │         │                      │
                  │         ├──M:1────┘         Almacenamientos
                  │         │                       │
                  │         └──M:1──► Clientes      ├──M:M──► Materiales
                  │                                 │    (AlmacenamientosMateriales
                  └──M:1──► Materiales              │     con campo saldo)
                                                    │
                                              Ajustes
```

#### Entidades de Soporte

```
Usuarios ──M:1──► Roles ──M:M──► Permisos
                    │           (RolesPermisos)
                    │
              PermisoReporte ──M:1──► Reporte ──1:M──► ReporteColumna
```

### 6.3 Catálogo de Tablas

#### Tablas Operacionales

| Tabla | Descripción | Campos Clave |
|-------|-------------|--------------|
| `almacenamientos` | Bodegas/silos de almacenamiento | id, nombre, capacidad, poli_material, es_virtual |
| `almacenamientos_materiales` | Relación M:M con saldo actual | almacenamiento_id, material_id, **saldo** |
| `materiales` | Catálogo de materiales | id, nombre, codigo, tipo, densidad |
| `clientes` | Clientes/consignatarios | id, tipo_identificacion, num_identificacion, razon_social |
| `flotas` | Flotas (buques y camiones) | id, tipo, referencia, puntos, estado_puerto, estado_operador |
| `viajes` | Viajes de buques y camiones | id, flota_id, puerto_id, peso_meta, peso_real, peso_tara, despacho_directo |
| `bls` | Bills of Lading | id, viaje_id, material_id, cliente_id, no_bl, peso_bl, peso_real, peso_enviado_api |
| `transacciones` | Transacciones de movimiento | id, tipo, viaje_id, pit, origen_id, destino_id, peso_meta, peso_real, estado, bl_id |
| `movimientos` | Movimientos de inventario | id, transaccion_id, almacenamiento_id, tipo, accion, peso, saldo_anterior, saldo_nuevo |
| `pesadas` | Registros de pesaje | id, transaccion_id, consecutivo, bascula_id, peso_meta, peso_real |
| `pesadas_corte` | Pesajes de punto de corte | id, puerto_id, transaccion, consecutivo, pit, material, peso, enviado |
| `consumos_entrada_parcial` | Consumos prorrateados por BL | id, puerto_id, bl_id, peso_bl, peso_prorrateado_acumulado, delta_peso |
| `saldo_snapshot_scada` | Snapshots de saldo del SCADA | id, pesada_id, almacenamiento_id, saldo_anterior, saldo_nuevo, tipo_almacenamiento |
| `ajustes` | Ajustes manuales de saldo | id, almacenamiento_id, material_id, saldo_anterior, saldo_nuevo, delta, motivo |

#### Tablas de Autenticación y Administración

| Tabla | Descripción | Campos Clave |
|-------|-------------|--------------|
| `usuarios` | Usuarios del sistema | id, nick_name, full_name, cedula, email, clave, rol_id |
| `roles` | Roles del sistema | id, nombre, estado |
| `permisos` | Permisos CRUD | id, nombre |
| `roles_permisos` | Relación M:M roles-permisos | rol_id, permiso_id |

#### Tablas de Reportería

| Tabla | Descripción | Campos Clave |
|-------|-------------|--------------|
| `reportes` | Catálogo de reportes | codigo, nombre, vista_nombre, campo_fecha, permite_exportar_* |
| `reportes_columnas` | Definición de columnas por reporte | reporte_id, campo, nombre_mostrar, tipo_dato, es_totalizable |
| `permisos_reportes` | Permisos de reporte por rol | rol_id, codigo_reporte, puede_ver, puede_exportar |

#### Tabla de Auditoría

| Tabla | Descripción | Campos Clave |
|-------|-------------|--------------|
| `logs_auditoria` | Log de cambios con JSON | entidad, entidad_id, accion, valor_anterior (JSON), valor_nuevo (JSON) |

### 6.4 Vistas Materializadas

Las vistas se crean directamente en PostgreSQL y se consumen como modelos de solo lectura:

| Vista | Descripción |
|-------|-------------|
| `v_viajes` | Vista consolidada de viajes con datos de flota y material |
| `v_pesadas_acumulado` | Pesadas acumuladas por transacción |
| `v_usuarios_roles` | Usuarios con información de rol |
| `v_roles_permisos` | Roles con sus permisos asignados |
| `v_alm_materiales` | Almacenamientos con sus materiales y saldos |

Las vistas materializadas se refrescan mediante los endpoints administrativos:
- `POST /reportes/refresh` — Refresca todas las vistas
- `POST /reportes/{codigo_reporte}/refresh` — Refresca una vista específica

---

## 7. Flujos Operacionales

La API actúa como la **BD Central Metalteco** en los diagramas de secuencia de la operación. A continuación se describen los tres flujos principales.

### 7.1 Flujo: Recibo de Buque

Este flujo gestiona todo el ciclo de vida de un buque desde su registro hasta la finalización, incluyendo el consumo periodico de parciales por parte del Integrador para reporte al puerto.

```
Integrador (PBCU)                    MIIT API                         Automatizador (SCADA)
      │                                 │                                      │
      │  POST /integrador/buque-registro│                                      │
      │────────────────────────────────►│  Registra flota + viaje              │
      │                                 │                                      │
      │  POST /integrador/buque-carga   │                                      │
      │────────────────────────────────►│  Registra BLs del buque              │
      │                                 │                                      │
      │  PUT /integrador/buque-arribo   │                                      │
      │────────────────────────────────►│  Marca fecha de llegada              │
      │                                 │                                      │
      │                                 │  GET /scada/viajes-activos           │
      │                                 │◄─────────────────────────────────────│
      │                                 │  Retorna viajes activos              │
      │                                 │                                      │
      │                                 │  POST /scada/transaccion-registro    │
      │                                 │◄─────────────────────────────────────│
      │                                 │  Crea transacción + calcula peso_meta│
      │                                 │                                      │
      │                                 │  POST /scada/pesada-registro         │
      │                                 │◄─────────────────────────────────────│
      │                                 │  Registra pesaje en báscula          │
      │                                 │                                      │
      │                                 │  PUT /scada/transaccion-finalizar    │
      │                                 │◄─────────────────────────────────────│
      │                                 │  Finaliza transacción + movimientos  │
      │                                 │                                      │
      │  GET /integrador/pesadas-parciales/{puerto_id}                         │
      │────────────────────────────────►│  Job periodico (~5 min) desde arribo │
      │◄────────────────────────────────│  hasta finalizacion del buque        │
      │                                 │                                      │
      │  PUT /integrador/buque-finalizar/{puerto_id}                           │
      │────────────────────────────────►│  Opcion A: finaliza buque            │
      │                                 │  + notifica FinalizaBuque a TG       │
      │                                 │                                      │
      │                                 │  PUT /scada/buque-finalizar/{puerto_id}
      │                                 │◄─────────────────────────────────────│
      │                                 │  Opcion B: finaliza buque (SCADA)    │
      │                                 │                                      │
      │                                 │  POST /scada/envio-final/{viaje_id}/notify
      │                                 │◄─────────────────────────────────────│
      │                                 │  Envio manual posterior al cierre    │
```

**Endpoints involucrados:**

| Paso | Endpoint | Método | Actor |
|------|----------|--------|-------|
| BuquesRegistro | `/integrador/buque-registro` | POST | Integrador |
| BuquesCarga | `/integrador/buque-carga` | POST | Integrador |
| BuqueArribo | `/integrador/buque-arribo/{puerto_id}` | PUT | Integrador |
| ViajesActivos | `/scada/viajes-activos` | GET | SCADA |
| TransaccionRegistro | `/scada/transaccion-registro` | POST | SCADA |
| PesadaRegistro | `/scada/pesada-registro` | POST | SCADA |
| TransaccionFinalizar | `/scada/transaccion-finalizar/{tran_id}` | PUT | SCADA |
| PesadasParcialesJob | `/integrador/pesadas-parciales/{puerto_id}` | GET | Integrador |
| FinalizaBuqueOP | `/integrador/buque-finalizar/{puerto_id}` | PUT | Integrador |
| FinalizaBuqueMT | `/scada/buque-finalizar/{puerto_id}` | PUT | SCADA |
| EnvioFinalManual | `/scada/envio-final/{viaje_id}/notify` | POST | SCADA |

**Nota de cierre de buque:** `FinalizaBuqueOP` y `FinalizaBuqueMT` se documentan como alternativas de finalizacion del mismo proceso (no pasos acumulativos obligatorios). En la operacion manual posterior al cierre, SCADA puede ejecutar `EnvioFinal` para pesadas pendientes.

### 7.2 Flujo: Despacho de Camión

Este flujo gestiona el ciclo completo de despacho de materiales a camiones.

```
Integrador (PBCU)                    MIIT API                         Automatizador (SCADA)
      │                                 │                                      │
      │  PUT /integrador/levante-carga-puerto/{no_bl}                          │
      │────────────────────────────────►│  Referencia BL habilitado            │
      │                                 │                                      │
      │  PUT /integrador/levante-carga-operador/{no_bl}                        │
      │────────────────────────────────►│  Confirmación de levante operador    │
      │                                 │                                      │
      │  POST /integrador/camion-registro                                      │
      │────────────────────────────────►│  Registra flota + viaje camión       │
      │                                 │                                      │
      │  PUT /integrador/camion-ingreso │                                      │
      │────────────────────────────────►│  Marca ingreso + peso_vacio/máximo   │
      │                                 │                                      │
      │                                 │  GET /scada/viajes-activos           │
      │                                 │◄─────────────────────────────────────│
      │                                 │                                      │
      │                                 │  POST /scada/transaccion-registro    │
      │                                 │◄─────────────────────────────────────│
      │                                 │  Crea transacción de cargue          │
      │                                 │                                      │
      │                                 │  POST /scada/pesada-registro         │
      │                                 │◄─────────────────────────────────────│
      │                                 │                                      │
      │                                 │  PUT /scada/transaccion-finalizar    │
      │                                 │◄─────────────────────────────────────│
      │                                 │  Finaliza + envía CamionCargue a TG  │
      │                                 │                                      │
      │  PUT /integrador/camion-egreso  │                                      │
      │────────────────────────────────►│  Marca salida + peso_real            │
```

**Endpoints involucrados:**

| Paso | Endpoint | Método | Actor |
|------|----------|--------|-------|
| LevanteCargaPuerto | `/integrador/levante-carga-puerto/{no_bl}` | PUT | Integrador |
| LevanteCargaOperador | `/integrador/levante-carga-operador/{no_bl}` | PUT | Integrador |
| CamionRegistro | `/integrador/camion-registro` | POST | Integrador |
| CamionIngreso | `/integrador/camion-ingreso/{puerto_id}` | PUT | Integrador |
| ViajesActivos | `/scada/viajes-activos` | GET | SCADA |
| TransaccionRegistro | `/scada/transaccion-registro` | POST | SCADA |
| PesadaRegistro | `/scada/pesada-registro` | POST | SCADA |
| TransaccionFinalizar | `/scada/transaccion-finalizar/{tran_id}` | PUT | SCADA |
| CamionSalida | `/integrador/camion-egreso/{puerto_id}` | PUT | Integrador |

### 7.3 Flujo: Despacho Directo

El despacho directo permite cargar camiones directamente desde el buque sin pasar por almacenamiento intermedio. Utiliza un **almacenamiento virtual** (configurado por `ALMACENAMIENTO_DESPACHO_DIRECTO_ID`).

```
Integrador (PBCU)                    MIIT API                         Automatizador (SCADA)
      │                                 │                                      │
      │  POST /integrador/buque-registro│                                      │
      │────────────────────────────────►│  Registra buque (despacho_directo)   │
      │                                 │                                      │
      │  POST /integrador/buque-carga   │                                      │
      │────────────────────────────────►│  Registra BLs vinculados             │
      │                                 │                                      │
      │  PUT /integrador/buque-arribo/{puerto_id}                              │
      │────────────────────────────────►│  Arribo explicito de buque           │
      │                                 │                                      │
      │  (Ciclo de recibo/descarga de buque por SCADA, similar a 7.1)          │
      │                                 │◄─────────────────────────────────────│
      │                                 │  Transacciones + pesajes de recibo   │
      │                                 │                                      │
      │  PUT /integrador/levante-carga-puerto/{no_bl}                          │
      │────────────────────────────────►│  BL habilitado para despacho         │
      │                                 │                                      │
      │  PUT /integrador/levante-carga-operador/{no_bl}                        │
      │────────────────────────────────►│  Confirmación del operador           │
      │                                 │                                      │
      │  POST /integrador/camion-registro                                      │
      │────────────────────────────────►│  Registra camión vinculado a BL      │
      │                                 │                                      │
      │  PUT /integrador/camion-ingreso │                                      │
      │────────────────────────────────►│                                      │
      │                                 │                                      │
      │                                 │  POST /scada/transaccion-registro    │
      │                                 │◄─────────────────────────────────────│
      │                                 │  Usa almacenamiento virtual          │
      │                                 │                                      │
      │                                 │  POST /scada/pesada-registro         │
      │                                 │◄─────────────────────────────────────│
      │                                 │                                      │
      │                                 │  PUT /scada/transaccion-finalizar/{tran_id}
      │                                 │◄─────────────────────────────────────│
      │                                 │  Cierra cargue del camión            │
      │                                 │                                      │
      │  GET /integrador/entrada-parcial-buque/{puerto_id}                     │
      │────────────────────────────────►│  Consumo parcial prorrateado por BL  │
      │                                 │  (despues de cada transacción)       │
      │                                 │                                      │
      │  PUT /integrador/camion-egreso  │                                      │
      │────────────────────────────────►│                                      │
      │                                 │                                      │
      │  (Repetir ciclo por cada camión del despacho directo)                  │
      │                                 │                                      │
      │  PUT /integrador/buque-finalizar/{puerto_id} o                         │
      │  [alternativamente] /scada/buque-finalizar/{puerto_id}                 │
      │────────────────────────────────►│  Cierre del flujo consolidado        │
```

**Particularidades del Despacho Directo:**
- El campo `despacho_directo` en `Viajes` indica este modo.
- Se utiliza la tabla `consumos_entrada_parcial` para rastrear los pesos prorrateados por BL.
- El endpoint `GET /integrador/entrada-parcial-buque/{puerto_id}` calcula el delta de peso entre lo ya consumido y lo disponible y se consume despues de cada `transaccion-finalizar` de camión.
- El flujo combina pasos de recibo y despacho en paralelo operativo: mientras existe descargue de buque, se habilita despacho de camiones vinculados a BL.
- Las transacciones se crean contra el almacenamiento virtual definido en configuración.

---

## 8. Endpoints de la API

Todos los endpoints están bajo el prefijo `/api/v1/`.

### 8.1 Autenticación (`/auth`)

| Método | Ruta | Descripción | Acceso |
|--------|------|-------------|--------|
| POST | `/auth` | Iniciar sesión (obtener JWT) | Público |
| POST | `/auth/token/refresh` | Renovar token JWT | Autenticado |

### 8.2 Integrador — Operador Portuario (`/integrador`)

Requiere rol: **ADMINISTRADOR** o **INTEGRADOR**

| Método | Ruta | Descripción | Notificación TG |
|--------|------|-------------|-----------------|
| POST | `/integrador/buque-registro` | Registrar buque (flota + viaje) | — |
| POST | `/integrador/buque-carga` | Registrar BLs del buque | — |
| PUT | `/integrador/buque-arribo/{puerto_id}` | Marcar arribo del buque | — |
| PUT | `/integrador/buque-finalizar/{puerto_id}` | Finalizar buque (operador) | **FinalizaBuque** |
| GET | `/integrador/entrada-parcial-buque/{puerto_id}` | Delta prorrateado para despacho directo | — |
| PUT | `/integrador/levante-carga-puerto/{no_bl}` | Actualizar estado_puerto del BL | — |
| PUT | `/integrador/levante-carga-operador/{no_bl}` | Actualizar estado_operador del BL | — |
| POST | `/integrador/camion-registro` | Registrar cita de camión | — |
| PUT | `/integrador/camion-ingreso/{puerto_id}` | Marcar ingreso (peso_vacio, peso_maximo) | — |
| PUT | `/integrador/camion-egreso/{puerto_id}` | Marcar egreso (peso_real) | — |
| GET | `/integrador/pesadas-parciales/{puerto_id}` | Pesos acumulados del viaje | — |

### 8.3 Automatizador — SCADA (`/scada`)

Requiere rol: **ADMINISTRADOR** o **AUTOMATIZADOR**

| Método | Ruta | Descripción | Notificación TG |
|--------|------|-------------|-----------------|
| GET | `/scada/almacenamientos-listado` | Inventario de almacenamientos (paginado) | — |
| GET | `/scada/viajes-activos` | Viajes activos por material | — |
| PUT | `/scada/buque-finalizar/{puerto_id}` | Finalizar buque (automatización) | — |
| PUT | `/scada/camion-ajuste` | Ajustar puntos de entrega del camión | — |
| GET | `/scada/materiales-listado` | Catálogo de materiales | — |
| GET | `/scada/movimientos-listado` | Movimientos de inventario (paginado) | — |
| POST | `/scada/pesada-registro` | Registrar pesaje en báscula | — |
| GET | `/scada/pesadas-listado` | Pesajes registrados (paginado) | — |
| GET | `/scada/transacciones-listado` | Transacciones (paginado) | — |
| POST | `/scada/transaccion-registro` | Crear transacción (calcula peso_meta) | — |
| PUT | `/scada/transaccion-finalizar/{tran_id}` | Finalizar/cancelar transacción | **CamionCargue** (si despacho) |
| POST | `/scada/ajustes` | Crear ajuste de saldo | — |
| GET | `/scada/envio-final/{viaje_id}` | Preview de datos de envío final | — |
| POST | `/scada/envio-final/{viaje_id}/notify` | Ejecutar envío final a TG | **EnvioFinal** |
| POST | `/scada/camion-cargue/{viaje_id}` | Enviar notificación CamionCargue | **CamionCargue** |

### 8.4 Reportería (`/reportes`)

| Método | Ruta | Descripción | Acceso |
|--------|------|-------------|--------|
| GET | `/reportes` | Listar reportes disponibles | Autenticado |
| GET | `/reportes/{codigo_reporte}` | Consultar datos del reporte | Con permiso `puede_ver` |
| GET | `/reportes/{codigo_reporte}/metadata` | Metadata del reporte (columnas, filtros) | Autenticado |
| GET | `/reportes/{codigo_reporte}/exportar` | Exportar reporte (PDF/CSV/Excel) | Con permiso `puede_exportar` |
| POST | `/reportes/refresh` | Refrescar todas las vistas | ADMINISTRADOR |
| POST | `/reportes/{codigo_reporte}/refresh` | Refrescar vista específica | ADMINISTRADOR |

**Parámetros de consulta de reportes:**
- `material_id` — Filtro por material
- `fecha_inicio` / `fecha_fin` — Rango de fechas
- `orden_campo` / `orden_direccion` — Ordenamiento
- `page` / `page_size` — Paginación
- Filtros dinámicos por columna (definidos en configuración)

**Formatos de exportación:**
- **PDF:** Orientación adaptativa, fuentes responsivas, totales incluidos
- **CSV:** Procesado con pandas, columnas renombradas
- **Excel:** Actualmente deshabilitado temporalmente

### 8.5 Administración de Usuarios (`/admin`)

Requiere rol: **SUPER_ADMINISTRATOR** o **ADMINISTRADOR**

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/admin/create` | Crear usuario |
| GET | `/admin/{user_id}` | Obtener usuario por ID |
| GET | `/admin/` | Listar todos los usuarios |
| PUT | `/admin/{user_id}` | Actualizar usuario |
| PATCH | `/admin/{user_id}/change-password` | Cambiar contraseña |
| DELETE | `/admin/{user_id}` | Eliminar usuario |

### 8.6 Administración de Reportes y Roles (`/admin`)

Estos endpoints están bajo los routers `admin_reportes` y `admin_roles` para la gestión de configuración de reportes y asignación de roles/permisos.

### 8.7 Perfil (`/profile`)

Endpoints para la gestión del perfil del usuario autenticado (datos personales y cambio de contraseña propio).

---

## 9. Sistema de Autenticación y Autorización

### 9.1 Autenticación JWT

- **Algoritmo:** HS256
- **Access Token:** Expira en 40 minutos (configurable)
- **Refresh Token:** Expira en 1 día (configurable)
- **Emisor:** `MIIT-API-Authentication`
- **Audiencia:** `MIIT-API`

**Flujo de autenticación:**

```
1. POST /api/v1/auth  →  { nick_name, clave }
2. Servidor valida credenciales (bcrypt)
3. Retorna { access_token, refresh_token, token_type: "Bearer" }
4. Cliente incluye header: Authorization: Bearer <access_token>
5. AuthMiddleware valida el token en cada request protegido
```

### 9.2 Rutas Públicas (sin autenticación)

- `/` — Health check
- `/api/v1/auth` — Login
- `/docs` — Swagger UI
- `/redoc` — ReDoc
- `/openapi/v1.json` — OpenAPI spec

### 9.3 Control de Acceso Basado en Roles (RBAC)

| Rol | Nivel | Acceso Principal |
|-----|-------|-----------------|
| `COLABORADOR` | Base | Consulta de reportes asignados |
| `SUPERVISOR` | Medio | Reportes con permisos extendidos |
| `INTEGRADOR` | Operacional | Endpoints `/integrador/*` + reportes |
| `AUTOMATIZADOR` | Operacional | Endpoints `/scada/*` + reportes |
| `ADMINISTRADOR` | Admin | Todos los endpoints operacionales + admin |
| `SUPER_ADMINISTRATOR` | Super | Acceso total al sistema |

### 9.4 Permisos Granulares

Los permisos se definen a nivel de rol mediante la tabla `roles_permisos`:

| Permiso | Descripción |
|---------|-------------|
| `CREATE` | Crear registros |
| `READ` | Consultar registros |
| `UPDATE` | Modificar registros |
| `DELETE` | Eliminar registros |

Para reportería, se utiliza un sistema de permisos adicional por reporte:
- `puede_ver` — Permite consultar el reporte
- `puede_exportar` — Permite exportar a PDF/CSV/Excel

### 9.5 Validación de Contraseñas

Las contraseñas deben cumplir:
- Al menos 1 dígito
- Al menos 1 letra mayúscula
- Al menos 1 carácter especial (`!¡/@#$%^&*(),.¿?":{}|<>`)

---

## 10. Integración con API Externa (TurboGraneles)

### 10.1 Arquitectura de Integración

La comunicación con TurboGraneles se realiza mediante el servicio `ExtApiService`, un cliente HTTP asíncrono basado en **httpx**.

```
MIIT API                              TurboGraneles API
   │                                        │
   │  1. POST /auth (JWT)                   │
   │───────────────────────────────────────►│
   │◄───────────────────────────────────────│
   │        { token }                       │
   │                                        │
   │  2. POST /endpoint (con Bearer token)  │
   │───────────────────────────────────────►│
   │◄───────────────────────────────────────│
   │        { response }                    │
```

### 10.2 Características del Cliente HTTP

- **Autenticación:** JWT con obtención automática de token
- **Reintentos:** 3 intentos con backoff exponencial para errores 5xx
- **Timeout:** 15 segundos por solicitud
- **SSL:** Verificación configurable, soporte para certificado en Base64
- **Headers:** `X-Request-Id` para trazabilidad
- **Serialización:** orjson con fallback a json estándar

### 10.3 Notificaciones Específicas

#### FinalizaBuque
- **Disparado por:** `PUT /integrador/buque-finalizar/{puerto_id}`
- **Actor:** Integrador (operador portuario)
- **Datos:** Información consolidada del buque finalizado
- **Destino:** TurboGraneles API

#### CamionCargue
- **Disparado por:** `PUT /scada/transaccion-finalizar/{tran_id}` (tipo despacho)
- **También disponible:** `POST /scada/camion-cargue/{viaje_id}`
- **Actor:** Automatizador (SCADA)
- **Datos:** Información compilada de cargue del camión
- **Destino:** TurboGraneles API

#### EnvioFinal
- **Disparado por:** `POST /scada/envio-final/{viaje_id}/notify`
- **Actor:** Automatizador (SCADA)
- **Modos de envío:**
  - `auto` — Envía automáticamente según configuración
  - `list` — Envía una lista de items
  - `single` — Envía un solo item
  - `last` — Envía el último item
- **Datos:** Pesadas finales con información del viaje y timestamp
- **Destino:** TurboGraneles API

### 10.4 Configuración Requerida

Para habilitar la integración, se deben configurar en `.env`:
```
TG_API_AUTH=https://url-autenticacion-tg
TG_API_URL=https://url-api-tg
TG_API_USER=usuario_tg
TG_API_PASS=password_tg
TG_API_VERIFY_SSL=True
```

---

## 11. Sistema de Reportería

### 11.1 Arquitectura de Reportes

El sistema de reportería es **metadata-driven**: los reportes se definen completamente en base de datos mediante las tablas `reportes` y `reportes_columnas`.

```
Reporte (definición)
  ├── vista_nombre → Vista materializada en PostgreSQL
  ├── campo_fecha → Campo para filtro de fechas
  ├── permite_exportar_pdf/excel/csv
  └── ReporteColumna[] (definición de columnas)
        ├── campo → Nombre del campo en la vista
        ├── nombre_mostrar → Label para el usuario
        ├── tipo_dato → string/number/date/datetime/boolean
        ├── visible/ordenable/filtrable
        ├── formato/prefijo/sufijo/decimales
        └── es_totalizable → sum/avg/count/min/max
```

### 11.2 Flujo de Consulta

1. **Metadata:** El frontend solicita `GET /reportes/{codigo}/metadata` para obtener la estructura del reporte.
2. **Datos:** Se consulta `GET /reportes/{codigo}` con filtros y paginación.
3. **Exportar:** Se solicita `GET /reportes/{codigo}/exportar?formato=PDF`.

### 11.3 Filtros Dinámicos

- **Filtro por material:** Si `permite_filtrar_material = true`
- **Rango de fechas:** Si `requiere_rango_fechas = true`, sobre el campo `campo_fecha`
- **Filtros por columna:** Configurados en `filtros_reportes_config` para cada reporte
- **Ordenamiento:** Cualquier columna marcada como `ordenable`

### 11.4 Totalización

Las columnas marcadas como `es_totalizable` generan totales automáticos según el tipo:
- `sum` — Suma total
- `avg` — Promedio
- `count` — Conteo
- `min` / `max` — Valores extremos

### 11.5 Formatos de Exportación

| Formato | Servicio | Características |
|---------|----------|----------------|
| **PDF** | ReportLab | Orientación adaptativa, fuentes responsivas, alternancia de colores, totales |
| **CSV** | pandas | Columnas renombradas, formato de fechas, enteros formateados |
| **Excel** | openpyxl | Estilos, colores alternados, anchos automáticos (temporalmente deshabilitado) |

---

## 12. Middleware y Manejo de Errores

### 12.1 Jerarquía de Excepciones

```
BasedException (400)
├── InvalidCredentialsException (401)
├── InvalidTokenCredentialsException (401)
├── ErrorTokenException (400)
├── UnauthorizedToken (401)
├── DatabaseConnectionException (502)
├── DatabaseInvalidConfigurationException (500)
├── DatabaseSQLAlchemyException (500)
├── DatabaseTypeMismatchException (422)
├── EntityAlreadyRegisteredException (409)
└── EntityNotFoundException (404)
```

### 12.2 Manejadores Globales

| Manejador | Excepción | Comportamiento |
|-----------|----------|----------------|
| `http_exception_handler` | `BasedException`, `StarletteHTTPException` | Retorna JSON con status_code, status_name, message |
| `json_decode_error_handler` | `RequestValidationError` | Retorna detalle de errores de validación Pydantic |

### 12.3 Formato de Error Estándar

```json
{
  "status_code": "404",
  "status_name": "Not Found",
  "message": "Viaje no encontrado en la base de datos."
}
```

---

## 13. Auditoría y Trazabilidad

### 13.1 Logs de Auditoría

Cada operación CRUD en el repositorio base genera automáticamente un registro en `logs_auditoria`:

| Campo | Contenido |
|-------|-----------|
| `entidad` | Nombre del modelo (e.g., "Viajes") |
| `entidad_id` | ID del registro afectado |
| `accion` | CREATE / UPDATE / DELETE |
| `valor_anterior` | JSON snapshot antes del cambio |
| `valor_nuevo` | JSON snapshot después del cambio |
| `usuario_id` | ID del usuario que realizó la acción |
| `fecha_hora` | Timestamp con zona America/Bogota |

### 13.2 Tracking de Usuario

- El `AuthMiddleware` extrae el `user_id` del JWT y lo almacena en el contexto.
- El `base_repository` inyecta automáticamente `usuario_id` en cada operación.
- El usuario administrador usa `user_id = 999` como convención.

### 13.3 Logging Aplicativo

- **Logger:** `colorlog` con formato estructurado
- **Directorio:** Configurable via `APP_LOG_DIR`
- **Rotación:** Por fecha (archivos diarios)
- **Niveles:** DEBUG, INFO, WARNING, ERROR (configurable via `API_LOG_LEVEL`)
- **Middleware:** `LoggerMiddleware` registra cada request/response con tiempo de procesamiento

---

## 14. Despliegue

### 14.1 Contenedor Docker

**Imagen base:** `registry.access.redhat.com/ubi9/python-312`

**Características del contenedor:**
- Timezone: `America/Bogota`
- Paquetes del sistema: gcc, openssl, git, ca-certificates, supervisor, curl
- Puerto expuesto: **8443**
- Gestor de procesos: **Supervisord**
- Directorio de logs: `/var/www/metalsoft/logs/miit_api/`

### 14.2 Docker Compose (Desarrollo Local)

```yaml
services:
  api:        # Puerto 8443:8443 — Aplicación FastAPI
  bdc:        # Puerto 5517:5432 — PostgreSQL 17 con healthcheck
  pgadmin:    # Puerto 5050:80  — pgAdmin para administración
```

### 14.3 Producción — AWS ECS Fargate

- **Orquestación:** AWS ECS (Elastic Container Service) con Fargate
- **Registro:** AWS ECR (Elastic Container Registry)
- **Configuración:** Variables de entorno inyectadas como secretos en la definición de tarea ECS
- **Red:** VPC con subnets privadas para la base de datos

### 14.4 Proceso de Despliegue

1. Build de la imagen Docker
2. Push a AWS ECR
3. Actualización de la definición de tarea en ECS
4. ECS Fargate despliega la nueva versión con rolling update

---

## 15. Dependencias

### 15.1 Dependencias de Producción

| Paquete | Versión Mínima | Propósito |
|---------|---------------|-----------|
| fastapi | latest | Framework web |
| fastapi-pagination | ≥0.12.0 | Paginación automática |
| starlette | ≥0.49.1 | ASGI toolkit |
| uvicorn[standard] | ≥0.25.0 | Servidor ASGI |
| pydantic | ≥2.5.0 | Validación de datos |
| pydantic-settings | ≥2.1.0 | Gestión de configuración |
| SQLAlchemy[asyncio] | ≥2.0.23 | ORM async |
| asyncpg | ≥0.29.0 | Driver PostgreSQL async |
| PyJWT | ≥2.8.0 | Tokens JWT |
| bcrypt | ≥4.1.0 | Hash de contraseñas |
| cryptography | ≥41.0.0 | Cifrado de datos |
| itsdangerous | ≥2.1.0 | Firma de datos |
| httpx | ≥0.26.0 | Cliente HTTP async |
| orjson | ≥3.9.0 | Serialización JSON rápida |
| pandas | ≥2.1.0 | Procesamiento de datos |
| openpyxl | ≥3.1.0 | Generación Excel |
| reportlab | ≥4.0.0 | Generación PDF |
| python-dotenv | ≥1.0.0 | Carga de .env |
| colorlog | ≥6.8.0 | Logging con colores |

---

*Documento generado el 26 de marzo de 2026 — Servicio Interconsulta MIIT v1.0.9*
