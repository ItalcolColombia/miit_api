# Manual de Usuario

## Servicio Interconsulta MIIT — Backend API

**Versión:** 1.0.9
**Fecha:** 26 de marzo de 2026
**Proyecto:** Puerto Antioquia — Urabá
**Desarrollado por:** Metalteco S.A.S

---

## Tabla de Contenido

1. [Introducción](#1-introducción)
2. [Acceso al Sistema](#2-acceso-al-sistema)
3. [Roles y Permisos](#3-roles-y-permisos)
4. [Documentación Interactiva (Swagger)](#4-documentación-interactiva-swagger)
5. [Operaciones del Integrador (Operador Portuario)](#5-operaciones-del-integrador-operador-portuario)
6. [Operaciones del Automatizador (SCADA)](#6-operaciones-del-automatizador-scada)
7. [Flujo Completo: Recibo de Buque](#7-flujo-completo-recibo-de-buque)
8. [Flujo Completo: Despacho de Camión](#8-flujo-completo-despacho-de-camión)
9. [Flujo Completo: Despacho Directo](#9-flujo-completo-despacho-directo)
10. [Sistema de Reportería](#10-sistema-de-reportería)
11. [Administración de Usuarios](#11-administración-de-usuarios)
12. [Gestión de Perfil](#12-gestión-de-perfil)
13. [Notificaciones a API Externa (TurboGraneles)](#13-notificaciones-a-api-externa-turbograneles)
14. [Códigos de Respuesta y Errores](#14-códigos-de-respuesta-y-errores)
15. [Preguntas Frecuentes](#15-preguntas-frecuentes)

---

## 1. Introducción

### 1.1 ¿Qué es el Servicio Interconsulta MIIT?

El Servicio Interconsulta MIIT es la **API REST central** de la operación portuaria de Puerto Antioquia. Funciona como un puente de datos entre:

- **Integrador (PBCU):** El sistema del operador portuario que gestiona buques, BLs y camiones.
- **Automatizador (SCADA):** El sistema de automatización que controla pesajes, transacciones y movimientos de materiales.
- **MIIT Reportes Web:** La aplicación de reportería que permite consultar y exportar datos operacionales.
- **TurboGraneles:** Sistema externo que recibe notificaciones de eventos operacionales.

### 1.2 ¿Cómo se usa esta API?

La API se consume mediante solicitudes HTTP (REST). Cada sistema externo se comunica con la API usando:

1. **Autenticación JWT:** Se obtiene un token mediante login y se incluye en cada solicitud.
2. **Endpoints específicos:** Cada rol tiene un conjunto de operaciones disponibles.
3. **Formato JSON:** Todas las solicitudes y respuestas usan JSON.

### 1.3 URL Base

| Entorno | URL |
|---------|-----|
| Producción | `https://<DOMINIO_PRODUCCION>/api/v1/` |
| Desarrollo | `http://localhost:8000/api/v1/` |

---

## 2. Acceso al Sistema

### 2.1 Autenticación (Login)

Para acceder a cualquier endpoint protegido, primero se debe obtener un token JWT.

**Solicitud:**

```http
POST /api/v1/auth
Content-Type: application/json

{
  "nick_name": "mi_usuario",
  "clave": "MiPassword1!"
}
```

**Respuesta exitosa (200):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer"
}
```

**Respuesta con error (401):**

```json
{
  "status_code": "401",
  "status_name": "Unauthorized",
  "message": "Credenciales inválidas."
}
```

### 2.2 Usar el Token

Una vez obtenido el `access_token`, incluirlo en el header `Authorization` de cada solicitud:

```http
GET /api/v1/integrador/pesadas-parciales/1001
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### 2.3 Renovar el Token

El access token expira en **40 minutos**. Antes de que expire, puede renovarse sin necesidad de re-login:

```http
POST /api/v1/auth/token/refresh
Authorization: Bearer <refresh_token>
```

**Respuesta (200):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...(nuevo)...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...(nuevo)...",
  "token_type": "Bearer"
}
```

> **Nota:** El refresh token expira en **1 día**. Si ambos tokens expiran, el usuario debe autenticarse nuevamente con `POST /auth`.

### 2.4 Política de Contraseñas

Las contraseñas deben cumplir los siguientes requisitos:

- Al menos **1 dígito** (0-9)
- Al menos **1 letra mayúscula** (A-Z)
- Al menos **1 carácter especial** (!¡/@#$%^&*(),.¿?":{}|<>)

---

## 3. Roles y Permisos

### 3.1 Roles Disponibles

| Rol | Descripción | Endpoints Disponibles |
|-----|-------------|----------------------|
| `COLABORADOR` | Personal operativo básico | Reportes asignados, perfil propio |
| `SUPERVISOR` | Supervisión de operaciones | Reportes extendidos, perfil propio |
| `INTEGRADOR` | Operador portuario (PBCU) | `/integrador/*`, reportes asignados |
| `AUTOMATIZADOR` | Sistema SCADA | `/scada/*`, reportes asignados |
| `ADMINISTRADOR` | Administrador del sistema | Todos los operacionales + admin |
| `SUPER_ADMINISTRATOR` | Super administrador | Acceso total sin restricciones |

### 3.2 Matriz de Acceso por Endpoint

| Módulo | COLABORADOR | SUPERVISOR | INTEGRADOR | AUTOMATIZADOR | ADMINISTRADOR | SUPER_ADMIN |
|--------|:-----------:|:----------:|:----------:|:-------------:|:-------------:|:-----------:|
| `/auth` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `/profile` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `/integrador/*` | ❌ | ❌ | ✅ | ❌ | ✅ | ✅ |
| `/scada/*` | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| `/reportes` | ✅* | ✅* | ✅* | ✅* | ✅ | ✅ |
| `/admin/*` | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |

*\* Acceso controlado individualmente por reporte (tabla `permisos_reportes`)*

---

## 4. Documentación Interactiva (Swagger)

La API incluye documentación interactiva generada automáticamente:

| Herramienta | URL | Descripción |
|------------|-----|-------------|
| **Swagger UI** | `/docs` | Interfaz interactiva para probar endpoints |
| **ReDoc** | `/redoc` | Documentación de referencia detallada |
| **OpenAPI JSON** | `/openapi/v1.json` | Especificación OpenAPI en formato JSON |

### 4.1 Cómo Usar Swagger UI

1. Abrir `https://<DOMINIO>/docs` en el navegador
2. Hacer clic en **"Authorize"** (botón con candado)
3. En el campo **Value**, ingresar: `Bearer <access_token>`
4. Hacer clic en **"Authorize"** y cerrar el diálogo
5. Ahora se pueden probar todos los endpoints directamente

### 4.2 Filtrar Endpoints

Swagger UI incluye un campo de búsqueda en la parte superior para filtrar endpoints por nombre. Los endpoints están organizados por tags:

- **Autenticación** — Login y refresh de tokens
- **Integrador** — Operaciones del operador portuario
- **Automatizador** — Operaciones del SCADA
- **Reportes** — Consulta y exportación de reportes
- **Admin - Reportes** — Administración de reportes
- **Admin - Roles** — Administración de roles
- **Administrador** — Gestión de usuarios
- **Perfil** — Gestión del perfil propio

---

## 5. Operaciones del Integrador (Operador Portuario)

Todos los endpoints del Integrador están bajo el prefijo `/api/v1/integrador/` y requieren rol **INTEGRADOR** o **ADMINISTRADOR**.

### 5.1 Registro de Buque

Registra un nuevo buque en el sistema con su flota y viaje asociado.

```http
POST /api/v1/integrador/buque-registro
Authorization: Bearer <token>
Content-Type: application/json

{
  "tipo": "buque",
  "referencia": "MV ATLANTIC PIONEER",
  "puntos": 3,
  "puerto_id": 1001,
  "material_id": 5,
  "peso_meta": 45000.00
}
```

**Respuesta (201):**

```json
{
  "status_code": "201",
  "status_name": "Created",
  "message": "registro exitoso"
}
```

### 5.2 Registro de Carga (BLs)

Registra los Bills of Lading asociados a un buque.

```http
POST /api/v1/integrador/buque-carga
Authorization: Bearer <token>
Content-Type: application/json

{
  "viaje_id": 100,
  "bls": [
    {
      "no_bl": "BL-2026-001",
      "material_id": 5,
      "cliente_id": 12,
      "peso_bl": 15000.00
    },
    {
      "no_bl": "BL-2026-002",
      "material_id": 5,
      "cliente_id": 8,
      "peso_bl": 30000.00
    }
  ]
}
```

### 5.3 Arribo de Buque

Marca la fecha de llegada del buque al puerto.

```http
PUT /api/v1/integrador/buque-arribo/1001
Authorization: Bearer <token>
Content-Type: application/json

{
  "fecha_llegada": "2026-03-26T08:30:00"
}
```

### 5.4 Registro de Camión

Registra una cita de camión para despacho.

```http
POST /api/v1/integrador/camion-registro
Authorization: Bearer <token>
Content-Type: application/json

{
  "tipo": "camion",
  "referencia": "ABC-123",
  "puerto_id": 2001,
  "material_id": 5,
  "bl_id": 50
}
```

### 5.5 Ingreso de Camión

Marca el ingreso del camión al puerto con sus pesos.

```http
PUT /api/v1/integrador/camion-ingreso/2001
Authorization: Bearer <token>
Content-Type: application/json

{
  "peso_vacio": 12500.00,
  "peso_maximo": 35000.00
}
```

### 5.6 Egreso de Camión

Marca la salida del camión con el peso real registrado.

```http
PUT /api/v1/integrador/camion-egreso/2001
Authorization: Bearer <token>
Content-Type: application/json

{
  "peso_real": 33200.00
}
```

### 5.7 Consultar Pesadas Parciales

Obtiene los pesos acumulados de un viaje en curso.

```http
GET /api/v1/integrador/pesadas-parciales/2001
Authorization: Bearer <token>
```

**Respuesta (200):**

```json
{
  "puerto_id": 2001,
  "pesadas": [
    {
      "consecutivo": 1,
      "peso": 5200.50,
      "pit": "PIT-A",
      "material": "Carbón"
    },
    {
      "consecutivo": 2,
      "peso": 4800.30,
      "pit": "PIT-A",
      "material": "Carbón"
    }
  ],
  "total_acumulado": 10000.80
}
```

### 5.8 Levante de Carga

Actualiza el estado de un BL. Existen dos variantes según quién actualiza:

**Levante por el puerto:**

```http
PUT /api/v1/integrador/levante-carga-puerto/BL-2026-001
Authorization: Bearer <token>
Content-Type: application/json

{
  "estado_puerto": "Liberado"
}
```

**Levante por el operador:**

```http
PUT /api/v1/integrador/levante-carga-operador/BL-2026-001
Authorization: Bearer <token>
Content-Type: application/json

{
  "estado_operador": "Aprobado"
}
```

### 5.9 Finalizar Buque

Finaliza el buque desde el lado del operador. **Esta operación envía una notificación FinalizaBuque a TurboGraneles.**

```http
PUT /api/v1/integrador/buque-finalizar/1001
Authorization: Bearer <token>
```

> **Importante:** Esta operación es irreversible. Una vez finalizado, el buque no puede reactivarse.

### 5.10 Entrada Parcial de Buque (Despacho Directo)

Obtiene los pesos delta prorrateados por BL para viajes de despacho directo.

```http
GET /api/v1/integrador/entrada-parcial-buque/1001
Authorization: Bearer <token>
```

**Respuesta (200):**

```json
[
  {
    "bl_id": 50,
    "no_bl": "BL-2026-001",
    "peso_bl": 15000.00,
    "peso_prorrateado_acumulado": 8500.00,
    "delta_peso": 1200.00
  }
]
```

---

## 6. Operaciones del Automatizador (SCADA)

Todos los endpoints del Automatizador están bajo el prefijo `/api/v1/scada/` y requieren rol **AUTOMATIZADOR** o **ADMINISTRADOR**.

### 6.1 Consultar Viajes Activos

Obtiene los viajes que están actualmente en proceso, filtrados por tipo de material.

```http
GET /api/v1/scada/viajes-activos?material=buque
Authorization: Bearer <token>
```

**Respuesta (200):**

```json
[
  {
    "id": 100,
    "puerto_id": 1001,
    "flota": "MV ATLANTIC PIONEER",
    "material": "Carbón",
    "peso_meta": 45000.00,
    "estado": "En Proceso"
  }
]
```

### 6.2 Consultar Almacenamientos

Lista el inventario actual de los almacenamientos con paginación.

```http
GET /api/v1/scada/almacenamientos-listado?page=1&size=20
Authorization: Bearer <token>
```

### 6.3 Consultar Materiales

```http
GET /api/v1/scada/materiales-listado
Authorization: Bearer <token>
```

### 6.4 Registrar Transacción

Crea una nueva transacción de movimiento de material. El sistema **calcula automáticamente el `peso_meta`** a partir de los BLs asociados.

```http
POST /api/v1/scada/transaccion-registro
Authorization: Bearer <token>
Content-Type: application/json

{
  "material_id": 5,
  "tipo": "descargue",
  "viaje_id": 100,
  "pit": "PIT-A",
  "origen_id": 10,
  "destino_id": 20,
  "bl_id": 50
}
```

**Respuesta (201):**

```json
{
  "id": 500,
  "material_id": 5,
  "tipo": "descargue",
  "viaje_id": 100,
  "peso_meta": 15000.00,
  "estado": "Proceso"
}
```

### 6.5 Registrar Pesada

Registra un pesaje individual en la báscula.

```http
POST /api/v1/scada/pesada-registro
Authorization: Bearer <token>
Content-Type: application/json

{
  "transaccion_id": 500,
  "consecutivo": 1,
  "bascula_id": 1,
  "peso_meta": 5000.00,
  "peso_real": 5150.30
}
```

### 6.6 Finalizar Transacción

Finaliza o cancela una transacción. Al finalizar una transacción de tipo **despacho**, se envía automáticamente una notificación **CamionCargue** a TurboGraneles.

```http
PUT /api/v1/scada/transaccion-finalizar/500
Authorization: Bearer <token>
Content-Type: application/json

{
  "estado": "Finalizado"
}
```

**Estados posibles:**
- `Finalizado` — Cierra la transacción y genera movimientos de inventario
- `Cancelado` — Cancela la transacción sin afectar inventario

### 6.7 Consultar Transacciones

```http
GET /api/v1/scada/transacciones-listado?page=1&size=20
Authorization: Bearer <token>
```

### 6.8 Consultar Pesadas

```http
GET /api/v1/scada/pesadas-listado?page=1&size=20
Authorization: Bearer <token>
```

### 6.9 Consultar Movimientos

```http
GET /api/v1/scada/movimientos-listado?page=1&size=20
Authorization: Bearer <token>
```

### 6.10 Ajustar Camión

Permite modificar los puntos de entrega (pit) de un camión en proceso.

```http
PUT /api/v1/scada/camion-ajuste
Authorization: Bearer <token>
Content-Type: application/json

{
  "viaje_id": 200,
  "pit": "PIT-B"
}
```

### 6.11 Crear Ajuste de Saldo

Crea un ajuste manual para corregir discrepancias en el inventario de un almacenamiento.

```http
POST /api/v1/scada/ajustes
Authorization: Bearer <token>
Content-Type: application/json

{
  "almacenamiento_id": 10,
  "material_id": 5,
  "saldo_nuevo": 25000.00,
  "motivo": "Corrección por inventario físico"
}
```

El sistema calcula automáticamente `saldo_anterior` y `delta`.

### 6.12 Finalizar Buque (desde SCADA)

Finaliza el buque desde el lado de la automatización.

```http
PUT /api/v1/scada/buque-finalizar/1001
Authorization: Bearer <token>
```

> **Nota:** La finalización del buque requiere tanto la confirmación del Integrador como del Automatizador.

### 6.13 Preview de Envío Final

Consulta los datos que se enviarán como envío final, sin ejecutar la notificación.

```http
GET /api/v1/scada/envio-final/200
Authorization: Bearer <token>
```

**Respuesta (200):**

```json
{
  "viaje_id": 200,
  "items": [
    {
      "consecutivo": 1,
      "peso": 5150.30,
      "material": "Carbón",
      "referencia": "TX500-F"
    }
  ]
}
```

### 6.14 Ejecutar Envío Final

Envía la notificación **EnvioFinal** a TurboGraneles.

```http
POST /api/v1/scada/envio-final/200/notify
Authorization: Bearer <token>
Content-Type: application/json

{
  "mode": "auto",
  "items": []
}
```

**Modos disponibles:**

| Modo | Comportamiento |
|------|---------------|
| `auto` | Envía automáticamente según configuración del sistema |
| `list` | Envía una lista específica de items proporcionados |
| `single` | Envía un solo item específico |
| `last` | Envía solo el último item registrado |

### 6.15 Enviar CamionCargue Manual

Envía manualmente la notificación CamionCargue para un viaje específico.

```http
POST /api/v1/scada/camion-cargue/200
Authorization: Bearer <token>
```

---

## 7. Flujo Completo: Recibo de Buque

Este flujo describe paso a paso la operación de recibo de un buque, desde su registro hasta su finalización.

### 7.1 Diagrama del Flujo

```
 INTEGRADOR                           API                              SCADA
     │                                 │                                 │
 ①   │── POST buque-registro ─────────►│                                 │
     │◄── 201 Created ────────────────│                                 │
     │                                 │                                 │
 ②   │── POST buque-carga ───────────►│                                 │
     │◄── 201 Created ────────────────│                                 │
     │                                 │                                 │
 ③   │── PUT buque-arribo ───────────►│                                 │
     │◄── 200 OK ─────────────────────│                                 │
     │                                 │                                 │
     │                                 │◄── GET viajes-activos ──────── ④│
     │                                 │── 200 OK ────────────────────►│
     │                                 │                                 │
     │                                 │◄── POST transaccion-registro ─ ⑤│
     │                                 │── 201 Created ───────────────►│
     │                                 │                                 │
     │                                 │◄── POST pesada-registro ────── ⑥│
     │                                 │── 201 Created ───────────────►│
     │                                 │    (repetir por cada pesaje)    │
     │                                 │                                 │
     │                                 │◄── PUT transaccion-finalizar ─ ⑦│
     │                                 │── 200 OK ────────────────────►│
     │                                 │                                 │
 ⑧   │── PUT levante-carga-puerto ───►│                                 │
     │◄── 200 OK ─────────────────────│                                 │
     │                                 │                                 │
 ⑨   │── PUT levante-carga-operador ─►│                                 │
     │◄── 200 OK ─────────────────────│                                 │
     │                                 │                                 │
 ⑩   │── PUT buque-finalizar ────────►│── Notifica FinalizaBuque ──►TG  │
     │◄── 200 OK ─────────────────────│                                 │
     │                                 │                                 │
     │                                 │◄── PUT buque-finalizar ─────── ⑪│
     │                                 │── 200 OK ────────────────────►│
```

### 7.2 Descripción de Cada Paso

| Paso | Actor | Endpoint | Acción |
|------|-------|----------|--------|
| ① | Integrador | `POST /integrador/buque-registro` | Registra el buque con datos de flota y viaje |
| ② | Integrador | `POST /integrador/buque-carga` | Registra los BLs con pesos y clientes |
| ③ | Integrador | `PUT /integrador/buque-arribo/{puerto_id}` | Marca la fecha de llegada al puerto |
| ④ | SCADA | `GET /scada/viajes-activos` | Consulta viajes disponibles para operar |
| ⑤ | SCADA | `POST /scada/transaccion-registro` | Crea transacción de descargue |
| ⑥ | SCADA | `POST /scada/pesada-registro` | Registra cada pesaje en báscula (puede repetirse) |
| ⑦ | SCADA | `PUT /scada/transaccion-finalizar/{id}` | Cierra la transacción y genera movimientos |
| ⑧ | Integrador | `PUT /integrador/levante-carga-puerto/{no_bl}` | Actualiza estado del BL por parte del puerto |
| ⑨ | Integrador | `PUT /integrador/levante-carga-operador/{no_bl}` | Actualiza estado del BL por parte del operador |
| ⑩ | Integrador | `PUT /integrador/buque-finalizar/{puerto_id}` | Finaliza el buque → Notifica TurboGraneles |
| ⑪ | SCADA | `PUT /scada/buque-finalizar/{puerto_id}` | Confirma finalización desde automatización |

> **Nota:** Los pasos ⑤-⑦ se repiten por cada transacción necesaria (múltiples materiales, múltiples bodegas, etc.). Los pasos ⑧-⑨ se ejecutan por cada BL.

---

## 8. Flujo Completo: Despacho de Camión

Este flujo describe el ciclo completo de despacho de material a un camión.

### 8.1 Diagrama del Flujo

```
 INTEGRADOR                           API                              SCADA
     │                                 │                                 │
 ①   │── POST camion-registro ────────►│                                 │
     │◄── 201 Created ────────────────│                                 │
     │                                 │                                 │
 ②   │── PUT camion-ingreso ─────────►│                                 │
     │◄── 200 OK ─────────────────────│                                 │
     │                                 │                                 │
     │                                 │◄── GET viajes-activos ──────── ③│
     │                                 │── 200 OK ────────────────────►│
     │                                 │                                 │
     │                                 │◄── POST transaccion-registro ─ ④│
     │                                 │── 201 Created ───────────────►│
     │                                 │                                 │
     │                                 │◄── POST pesada-registro ────── ⑤│
     │                                 │── 201 Created ───────────────►│
     │                                 │                                 │
     │                                 │◄── PUT transaccion-finalizar ─ ⑥│
     │                                 │── 200 OK ────────────────────►│
     │                                 │── Notifica CamionCargue ──►TG  │
     │                                 │                                 │
 ⑦   │── GET pesadas-parciales ──────►│                                 │
     │◄── 200 OK ─────────────────────│                                 │
     │                                 │                                 │
 ⑧   │── PUT camion-egreso ─────────►│                                 │
     │◄── 200 OK ─────────────────────│                                 │
     │                                 │                                 │
     │                                 │◄── POST envio-final/.../notify ⑨│
     │                                 │── 200 OK ────────────────────►│
     │                                 │── Notifica EnvioFinal ────►TG  │
```

### 8.2 Descripción de Cada Paso

| Paso | Actor | Endpoint | Acción |
|------|-------|----------|--------|
| ① | Integrador | `POST /integrador/camion-registro` | Registra el camión con placa y BL asignado |
| ② | Integrador | `PUT /integrador/camion-ingreso/{puerto_id}` | Marca ingreso con peso_vacio y peso_maximo |
| ③ | SCADA | `GET /scada/viajes-activos` | Consulta camiones disponibles para cargar |
| ④ | SCADA | `POST /scada/transaccion-registro` | Crea transacción de cargue |
| ⑤ | SCADA | `POST /scada/pesada-registro` | Registra pesaje(s) en báscula |
| ⑥ | SCADA | `PUT /scada/transaccion-finalizar/{id}` | Finaliza transacción → Notifica CamionCargue a TG |
| ⑦ | Integrador | `GET /integrador/pesadas-parciales/{puerto_id}` | Consulta peso acumulado del viaje |
| ⑧ | Integrador | `PUT /integrador/camion-egreso/{puerto_id}` | Marca salida con peso_real en báscula de salida |
| ⑨ | SCADA | `POST /scada/envio-final/{viaje_id}/notify` | Envía datos finales a TurboGraneles |

> **Nota:** Si el camión requiere múltiples cargas (múltiples pits), los pasos ④-⑥ se repiten por cada transacción.

---

## 9. Flujo Completo: Despacho Directo

El despacho directo permite cargar camiones **directamente desde el buque** sin almacenamiento intermedio. Se usa un almacenamiento virtual configurado en el sistema.

### 9.1 Diagrama del Flujo

```
 INTEGRADOR                           API                              SCADA
     │                                 │                                 │
     │   (Buque ya registrado con BLs, pasos ①-③ del flujo Recibo)      │
     │                                 │                                 │
 ①   │── POST camion-registro ────────►│  (vinculado al BL del buque)   │
     │◄── 201 Created ────────────────│                                 │
     │                                 │                                 │
 ②   │── PUT camion-ingreso ─────────►│                                 │
     │◄── 200 OK ─────────────────────│                                 │
     │                                 │                                 │
 ③   │── GET entrada-parcial-buque ──►│                                 │
     │◄── 200 (deltas prorrateados) ──│                                 │
     │                                 │                                 │
     │                                 │◄── POST transaccion-registro ─ ④│
     │                                 │── 201 (usa almacen virtual) ──►│
     │                                 │                                 │
     │                                 │◄── POST pesada-registro ────── ⑤│
     │                                 │── 201 Created ───────────────►│
     │                                 │                                 │
     │                                 │◄── PUT transaccion-finalizar ─ ⑥│
     │                                 │── 200 OK ────────────────────►│
     │                                 │                                 │
 ⑦   │── PUT camion-egreso ─────────►│                                 │
     │◄── 200 OK ─────────────────────│                                 │
     │                                 │                                 │
     │                                 │◄── POST envio-final/.../notify ⑧│
     │                                 │── Notifica EnvioFinal ────►TG  │
```

### 9.2 Descripción de Cada Paso

| Paso | Actor | Endpoint | Acción |
|------|-------|----------|--------|
| ① | Integrador | `POST /integrador/camion-registro` | Registra camión vinculado a un BL del buque |
| ② | Integrador | `PUT /integrador/camion-ingreso/{puerto_id}` | Marca ingreso del camión |
| ③ | Integrador | `GET /integrador/entrada-parcial-buque/{puerto_id}` | Obtiene deltas de peso prorrateados por BL |
| ④ | SCADA | `POST /scada/transaccion-registro` | Crea transacción usando almacenamiento virtual |
| ⑤ | SCADA | `POST /scada/pesada-registro` | Registra pesaje |
| ⑥ | SCADA | `PUT /scada/transaccion-finalizar/{id}` | Finaliza transacción |
| ⑦ | Integrador | `PUT /integrador/camion-egreso/{puerto_id}` | Marca salida del camión |
| ⑧ | SCADA | `POST /scada/envio-final/{viaje_id}/notify` | Envía datos finales a TurboGraneles |

### 9.3 Particularidades del Despacho Directo

| Concepto | Descripción |
|----------|-------------|
| **Almacenamiento Virtual** | Las transacciones usan un almacenamiento virtual (ID configurado en `ALMACENAMIENTO_DESPACHO_DIRECTO_ID`) |
| **Prorrateo de Pesos** | El peso se distribuye proporcionalmente entre los BLs según su peso declarado |
| **ConsumosEntradaParcial** | La tabla `consumos_entrada_parcial` rastrea cuánto se ha consumido de cada BL |
| **Delta de Peso** | El endpoint `entrada-parcial-buque` calcula la diferencia entre lo ya consumido y lo disponible |
| **Vinculación BL-Camión** | Cada camión de despacho directo se vincula a un BL específico del buque |

---

## 10. Sistema de Reportería

### 10.1 Consultar Reportes Disponibles

Lista los reportes a los que el usuario tiene acceso según su rol.

```http
GET /api/v1/reportes?solo_con_acceso=true
Authorization: Bearer <token>
```

**Respuesta (200):**

```json
{
  "reportes": [
    {
      "codigo": "RPT_PERMANENCIA",
      "nombre": "Informe de Tiempos de Permanencia en Puerto",
      "descripcion": "Tiempos de permanencia de camiones en el puerto. Incluye tiempo total, tiempo de espera antes del cargue y tiempo de cargue.",
      "icono": "schedule",
      "categoria": "operacional",
      "puede_ver": true,
      "puede_exportar": true
    },
    {
      "codigo": "RPT_RECIBIDO_DESPACHADO",
      "nombre": "Recibido vs Despachado",
      "descripcion": "Comparativo de carga recibida (buques) vs carga despachada (camiones) agrupado por buque y material.",
      "icono": "compare_arrows",
      "categoria": "operacional",
      "puede_ver": true,
      "puede_exportar": true
    }
  ]
}
```

### 10.2 Consultar Metadata de un Reporte

Obtiene la estructura del reporte: columnas disponibles, filtros y campos totalizables.

```http
GET /api/v1/reportes/RPT_PERMANENCIA/metadata
Authorization: Bearer <token>
```

**Respuesta (200):**

```json
{
  "columnas": [
    {
      "campo": "placa",
      "nombre_mostrar": "Placa",
      "tipo_dato": "string",
      "visible": true,
      "ordenable": true,
      "filtrable": true,
      "es_totalizable": false
    },
    {
      "campo": "peso_meta",
      "nombre_mostrar": "Peso Meta",
      "tipo_dato": "number",
      "visible": true,
      "ordenable": true,
      "filtrable": false,
      "es_totalizable": true,
      "tipo_totalizacion": "sum",
      "decimales": 2,
      "sufijo": "kg"
    },
    {
      "campo": "tiempo_permanencia_min",
      "nombre_mostrar": "Tiempo Permanencia",
      "tipo_dato": "number",
      "visible": true,
      "ordenable": true,
      "filtrable": false,
      "es_totalizable": true,
      "tipo_totalizacion": "avg",
      "decimales": 1,
      "sufijo": "min"
    },
    {
      "campo": "cita_estado",
      "nombre_mostrar": "Estado Cita",
      "tipo_dato": "string",
      "visible": true,
      "ordenable": true,
      "filtrable": true,
      "es_totalizable": false
    }
  ],
  "filtros_disponibles": {
    "materiales": true,
    "rango_fechas": true
  },
  "totalizables": ["peso_meta", "tiempo_permanencia_min"],
  "filtros_columnas": [
    {
      "campo": "cita_estado",
      "tipo": "select",
      "opciones": ["Programada", "Activa", "Finalizada", "Cancelada"]
    }
  ]
}
```

### 10.3 Consultar Datos del Reporte

```http
GET /api/v1/reportes/RPT_PERMANENCIA?material_id=5&fecha_inicio=2026-03-01&fecha_fin=2026-03-26&page=1&page_size=50&orden_campo=fecha_entrada_puerto&orden_direccion=desc
Authorization: Bearer <token>
```

**Respuesta (200):**

```json
{
  "columnas": [...],
  "datos": [
    {
      "viaje_id": 1001,
      "placa": "XVZ479",
      "trucktransaction": "24128",
      "material": "MAIZ USA",
      "peso_meta": 30000.50,
      "fecha_entrada_puerto": "2026-03-20T14:30:00-05:00",
      "fecha_salida_puerto": "2026-03-20T16:45:00-05:00",
      "tiempo_permanencia_min": 135.0,
      "cita_estado": "Finalizada"
    }
  ],
  "totales": {
    "peso_meta": 145000.00,
    "tiempo_permanencia_min": 128.4
  },
  "paginacion": {
    "page": 1,
    "page_size": 50,
    "total_items": 120,
    "total_pages": 3
  }
}
```

### 10.4 Exportar Reporte

**Exportar a PDF:**

```http
GET /api/v1/reportes/RPT_PERMANENCIA/exportar?formato=PDF&material_id=5&fecha_inicio=2026-03-01&fecha_fin=2026-03-26
Authorization: Bearer <token>
```

Respuesta: Archivo binario PDF con header `Content-Type: application/pdf`.

**Exportar a CSV:**

```http
GET /api/v1/reportes/RPT_PERMANENCIA/exportar?formato=CSV&material_id=5
Authorization: Bearer <token>
```

Respuesta: Archivo CSV con header `Content-Type: text/csv`.

**Formatos disponibles:**

| Formato | Estado | Content-Type |
|---------|--------|-------------|
| `PDF` | Activo | `application/pdf` |
| `CSV` | Activo | `text/csv` |
| `EXCEL` | Temporalmente deshabilitado | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |

### 10.5 Refrescar Vistas (Solo Administradores)

Los datos de los reportes provienen de vistas materializadas que deben refrescarse para mostrar información actualizada.

```http
# Refrescar todas las vistas
POST /api/v1/reportes/refresh
Authorization: Bearer <token_admin>

# Refrescar una vista específica
POST /api/v1/reportes/RPT_PERMANENCIA/refresh
Authorization: Bearer <token_admin>
```

---

## 11. Administración de Usuarios

Requiere rol **ADMINISTRADOR** o **SUPER_ADMINISTRATOR**.

### 11.1 Crear Usuario

```http
POST /api/v1/admin/create
Authorization: Bearer <token>
Content-Type: application/json

{
  "nick_name": "jperez",
  "full_name": "Juan Pérez",
  "cedula": "1234567890",
  "email": "jperez@ejemplo.com",
  "clave": "Password1!",
  "rol_id": 3
}
```

**Respuesta (201):**

```json
{
  "id": 15,
  "nick_name": "jperez",
  "full_name": "Juan Pérez",
  "email": "jperez@ejemplo.com",
  "rol_id": 3
}
```

### 11.2 Listar Usuarios

```http
GET /api/v1/admin/
Authorization: Bearer <token>
```

### 11.3 Obtener Usuario por ID

```http
GET /api/v1/admin/15
Authorization: Bearer <token>
```

### 11.4 Actualizar Usuario

```http
PUT /api/v1/admin/15
Authorization: Bearer <token>
Content-Type: application/json

{
  "full_name": "Juan Carlos Pérez",
  "email": "jcperez@ejemplo.com",
  "rol_id": 4
}
```

### 11.5 Cambiar Contraseña de Usuario

```http
PATCH /api/v1/admin/15/change-password
Authorization: Bearer <token>
Content-Type: application/json

{
  "clave_actual": "Password1!",
  "clave_nueva": "NewPassword2@"
}
```

### 11.6 Eliminar Usuario

```http
DELETE /api/v1/admin/15
Authorization: Bearer <token>
```

**Respuesta:** `204 No Content`

---

## 12. Gestión de Perfil

Cualquier usuario autenticado puede gestionar su propio perfil mediante los endpoints `/api/v1/profile/`.

### 12.1 Ver Mi Perfil

```http
GET /api/v1/profile/
Authorization: Bearer <token>
```

**Respuesta (200):**

```json
{
  "id": 15,
  "nick_name": "jperez",
  "full_name": "Juan Pérez",
  "email": "jperez@ejemplo.com",
  "rol": "INTEGRADOR"
}
```

### 12.2 Actualizar Mi Perfil

```http
PUT /api/v1/profile/
Authorization: Bearer <token>
Content-Type: application/json

{
  "full_name": "Juan Carlos Pérez",
  "email": "jcperez@ejemplo.com"
}
```

### 12.3 Cambiar Mi Contraseña

```http
PATCH /api/v1/profile/change-password
Authorization: Bearer <token>
Content-Type: application/json

{
  "clave_actual": "MiPasswordActual1!",
  "clave_nueva": "MiNuevaPassword2@"
}
```

---

## 13. Notificaciones a API Externa (TurboGraneles)

La API envía notificaciones automáticas y manuales al sistema TurboGraneles en momentos clave de la operación.

### 13.1 Resumen de Notificaciones

| Notificación | Cuándo se Envía | Disparador | Tipo |
|-------------|----------------|-----------|------|
| **FinalizaBuque** | Al finalizar un buque desde el Integrador | `PUT /integrador/buque-finalizar/{puerto_id}` | Automática |
| **CamionCargue** | Al finalizar una transacción de despacho | `PUT /scada/transaccion-finalizar/{id}` | Automática |
| **CamionCargue** | Reenvío manual | `POST /scada/camion-cargue/{viaje_id}` | Manual |
| **EnvioFinal** | Al ejecutar envío final | `POST /scada/envio-final/{viaje_id}/notify` | Manual/SCADA |

### 13.2 FinalizaBuque

**Se envía cuando:** El Integrador finaliza un buque mediante `PUT /integrador/buque-finalizar/{puerto_id}`.

**Datos enviados:** Información consolidada del buque incluyendo:
- Identificación del viaje y puerto
- Material descargado
- Pesos totales (meta y real)
- Fecha de llegada y finalización
- BLs asociados

**Reintentos:** 3 intentos con backoff exponencial si TurboGraneles responde con error 5xx.

### 13.3 CamionCargue

**Se envía automáticamente cuando:** El SCADA finaliza una transacción de tipo despacho mediante `PUT /scada/transaccion-finalizar/{id}`.

**Se puede reenviar manualmente:** `POST /scada/camion-cargue/{viaje_id}`

**Datos enviados:** Información compilada del cargue del camión incluyendo:
- Identificación del viaje
- Material cargado
- Pesos por transacción
- Pit/punto de carga
- Timestamp de finalización

### 13.4 EnvioFinal

**Se ejecuta manualmente por el SCADA:** `POST /scada/envio-final/{viaje_id}/notify`

**Preview disponible:** Antes de enviar, se puede consultar qué datos se enviarán con `GET /scada/envio-final/{viaje_id}`.

**Modos de envío:**

| Modo | Uso |
|------|-----|
| `auto` | El sistema decide qué enviar según la configuración y el estado actual |
| `list` | Se envía una lista de items proporcionados en el body |
| `single` | Se envía un solo item |
| `last` | Se envía solo el último registro |

### 13.5 Comportamiento ante Fallos

- Las notificaciones se envían de forma **asíncrona** durante la ejecución del endpoint.
- Si la notificación falla, **la operación principal (finalizar transacción, finalizar buque) NO se revierte**.
- Los errores se registran en los logs de la aplicación.
- Para reenviar notificaciones fallidas, usar los endpoints manuales (`camion-cargue`, `envio-final/notify`).

---

## 14. Códigos de Respuesta y Errores

### 14.1 Códigos de Éxito

| Código | Nombre | Uso |
|--------|--------|-----|
| `200` | OK | Consulta o actualización exitosa |
| `201` | Created | Registro creado exitosamente |
| `204` | No Content | Eliminación exitosa |

### 14.2 Códigos de Error del Cliente

| Código | Nombre | Causa Común |
|--------|--------|------------|
| `400` | Bad Request | Datos de entrada inválidos o error de validación de token |
| `401` | Unauthorized | Token expirado, inválido o credenciales incorrectas |
| `403` | Forbidden | Rol del usuario no tiene permiso para este endpoint |
| `404` | Not Found | Recurso no encontrado (viaje, transacción, usuario, etc.) |
| `409` | Conflict | Entidad ya registrada (duplicado) |
| `422` | Unprocessable Entity | Error de validación de datos o tipo incompatible |

### 14.3 Códigos de Error del Servidor

| Código | Nombre | Causa Común |
|--------|--------|------------|
| `500` | Internal Server Error | Error inesperado en la aplicación o base de datos |
| `502` | Bad Gateway | No se puede conectar a la base de datos |

### 14.4 Formato de Error Estándar

Todas las respuestas de error siguen el mismo formato JSON:

```json
{
  "status_code": "404",
  "status_name": "Not Found",
  "message": "Viaje no encontrado en la base de datos."
}
```

### 14.5 Errores de Validación (422)

Cuando los datos de entrada no cumplen las validaciones de Pydantic:

```json
{
  "status_code": "422",
  "status_name": "Unprocessable request",
  "message": "Validation error",
  "detail": [
    {
      "field": "peso_real",
      "error": "Field required"
    },
    {
      "field": "puerto_id",
      "error": "Input should be a valid integer"
    }
  ]
}
```

### 14.6 Errores de Autenticación

**Token expirado o inválido:**

```json
{
  "status_code": "401",
  "status_name": "Unauthorized",
  "message": "No se pudieron validar las credenciales del token."
}
```

El header de respuesta incluirá: `WWW-Authenticate: Bearer`

**Credenciales de login incorrectas:**

```json
{
  "status_code": "401",
  "status_name": "Unauthorized",
  "message": "Credenciales inválidas."
}
```

---

## 15. Preguntas Frecuentes

### 15.1 Autenticación y Acceso

**P: ¿Cuánto dura mi token?**
R: El access token dura **40 minutos**. El refresh token dura **1 día**. Usa `POST /auth/token/refresh` antes de que expire el access token.

**P: ¿Qué hago si mi token expiró?**
R: Si el access token expiró pero el refresh token sigue vigente, usa `POST /auth/token/refresh`. Si ambos expiraron, vuelve a autenticarte con `POST /auth`.

**P: Recibo error 403 Forbidden, ¿por qué?**
R: Tu rol no tiene permiso para ese endpoint. Verifica tu rol en la [sección 3](#3-roles-y-permisos). Contacta al administrador si necesitas acceso adicional.

### 15.2 Operaciones

**P: ¿Puedo revertir la finalización de un buque?**
R: No. La finalización es una operación irreversible. Asegúrese de que todos los BLs y transacciones estén correctos antes de finalizar.

**P: ¿Qué pasa si la notificación a TurboGraneles falla?**
R: La operación principal se completa normalmente. La notificación puede reenviarse manualmente usando `POST /scada/camion-cargue/{viaje_id}` o `POST /scada/envio-final/{viaje_id}/notify`.

**P: ¿Cómo corrijo un saldo incorrecto en un almacenamiento?**
R: Usa el endpoint `POST /scada/ajustes` proporcionando el almacenamiento, material, nuevo saldo y un motivo descriptivo. El sistema registra automáticamente el delta y la auditoría.

**P: ¿Puedo registrar múltiples pesadas para una misma transacción?**
R: Sí. El endpoint `POST /scada/pesada-registro` puede llamarse múltiples veces con consecutivos incrementales para la misma transacción.

### 15.3 Reportes

**P: Los datos del reporte no están actualizados, ¿qué hago?**
R: Los reportes usan vistas materializadas que deben refrescarse. Si eres administrador, usa `POST /reportes/refresh`. Si no, contacta al administrador.

**P: ¿Puedo exportar a Excel?**
R: La exportación a Excel está temporalmente deshabilitada. Usa PDF o CSV como alternativa.

**P: ¿Por qué no veo ciertos reportes?**
R: Los reportes son visibles según los permisos de tu rol. Solo verás los reportes donde tu rol tenga `puede_ver = true` en la tabla de permisos de reportes.

### 15.4 Despacho Directo

**P: ¿Qué diferencia hay entre despacho normal y despacho directo?**
R: En el despacho normal, el material se descarga del buque a un almacenamiento y luego se despacha al camión. En el despacho directo, el camión se carga directamente desde el buque usando un almacenamiento virtual, sin pasar por bodega intermedia.

**P: ¿Cómo se calcula el peso prorrateado en despacho directo?**
R: El endpoint `GET /integrador/entrada-parcial-buque/{puerto_id}` calcula el delta de peso distribuyendo proporcionalmente entre los BLs según su peso declarado, descontando lo ya consumido registrado en `consumos_entrada_parcial`.

### 15.5 Integración

**P: ¿Cómo sé si una notificación a TurboGraneles se envió correctamente?**
R: Si el endpoint retorna `200 OK`, la notificación fue aceptada. Si hubo error, se registra en los logs de la aplicación. En caso de duda, contacta al equipo de soporte para revisar los logs.

**P: ¿Se pueden enviar notificaciones de prueba?**
R: En el entorno de desarrollo, las notificaciones se envían a la URL configurada en `TG_API_URL`. Si esta variable está vacía, las notificaciones no se envían.

---

*Manual de Usuario generado el 26 de marzo de 2026 — Servicio Interconsulta MIIT v1.0.9*
