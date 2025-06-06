# 🚢 Servicio Interconsulta MIIT - Puerto Antioquia

API Rest desarrollada en FastAPI para la intercomunicación entre los interesados y el repositorio central de MIIT en **Puerto Antioquia**,
construida con principios de arquitectura limpia y prácticas modernas. Este proyecto fue desarrollado como respuesta a las interrogantes
detectadas en el flujo de información ahondado en la propuesta de un sistema integrador de información para el puerto.

---

## 🌟 Características

### Principales Funcionalidades
- 🧱 **Desarrollo**: Principios de arquitectura limpia, patrón de repositorio y capa de servicios.
- 🔐 **Encriptación**: Claves de seguridad hasheadas mediante algoritmo SHA-256.
- 🔑 **Seguridad Integrada**: Autenticación y autorización de peticiones con **OAuth2** y **JWT**.
- 🧪 **Testeo**: Pruebas unitarias realizadas con Pytest.
- 📄 **Documentación Automática**: Disponible mediante **Swagger UI** y **ReDoc**.
- 🐳 **Contenerización**: Incluye archivos para realizar despliegue con **Docker Compose**.

### Herramientas y librerias
- ⚡ **[FastAPI](https://fastapi.tiangolo.com)**: Construcción ágil de APIs con alto rendimiento y listas para producción.
- 🧰 **[SQLModel](https://sqlmodel.tiangolo.com)**: Manejo de las interacciónes con la base de datos (ORM).
- 🔍 **[Pydantic](https://docs.pydantic.dev)**: Permite establecer el modelo de entrada y de respuesta (Schema).  
- 💾 **[PostgreSQL](https://www.postgresql.org)**: Sistema de base de datos relacional robusta y escalable.
---

## 🚀 Requisitos

- Python 3.13 o superior
- (Opcional) Docker y Docker Compose

---

## ⚙️ Configuración del proyecto

### 1. Clonar o descargar el repositorio

```bash
git clone https://github.com/jadapache/miit_api.git
cd miit_api
```

### 2. Definir las variables de entorno
- Copiar `.env.dist` y renombrar como `.env`
- Remplazar texto de variables con valores por defecto

### 3. Crear y activar un entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## ▶️ Ejecución del Proyecto

### 🖥️ 1. Ejecutar localmente con Uvicorn

```bash
uvicorn main:app --reload
```

La API estará disponible en: http://localhost:8443/

### 🌐 2. Ejecutar en un contenedor

```bash
docker-compose up --build
```

Esto desplegará la api junto con los servicios definidos en `docker-compose.yml`.

---

## 📚 Documentación de la API

La documentación automática generada de la API puede ser encontrada en:

- **Swagger UI**: [http://host:8443/docs](http://host:8443/docs)
- **ReDoc**: [http://host:8443/redoc](http://host:8443/redoc)

---

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Abrir un issue para reportar un bug
  o seguir estos pasos antes de enviar una Pull Request:

1. Realizar **fork** del repositorio.
2. Crear una nueva rama:  
   `git checkout -b feature/nueva-funcionalidad`
3. Efectuar los cambios y hacer commit:  
   `git commit -am 'Agrega nueva funcionalidad'`
4. Hacer push a tu rama:  
   `git push origin feature/nueva-funcionalidad`
5. Enviar **Pull Request**.

---

## 📝 Licencia

Este proyecto está licenciado bajo la [Licencia MIT](LICENSE).

---

## 📬 Contacto

Para mayor información o consultas, contactar a:  
**[@jadapache](https://github.com/jadapache)**
