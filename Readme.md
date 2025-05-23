# Servicio Interconsulta MIIT - Pto Antioquia

API para la intercomunicación entre los stackholder y el repositorio central en **Puerto Antiquia, Urabá**.

## Uso

Para hacer uso de este repositorio realice los siguientes pasos:

* Clonar el repositorio remoto:

```bash
git clone https://github.com/jadapache/miit_api
```

Características
Desarrollada con FastAPI, un framework moderno y de alto rendimiento para construir APIs con Python.

Estructura modular que incluye componentes como api/v1, core, database, repositories, schemas, services, utils y tests.

Implementación de autenticación y autorización utilizando estándares como OAuth2 y JWT.

Documentación automática de la API mediante Swagger UI y ReDoc.

Preparada para despliegue en contenedores Docker, facilitando su implementación en diferentes entornos.
GitHub
+1
fastapi.tiangolo.com
+1
fastapi.tiangolo.com
Codecademy
+1
fastapi.tiangolo.com
+1

Requisitos
Python 3.8 o superior.

Docker y Docker Compose (opcional, para despliegue en contenedores).

Instalación
Clonar el repositorio
bash
Copiar
Editar
git clone https://github.com/jadapache/miit_api.git
cd miit_api
Crear y activar un entorno virtual
bash
Copiar
Editar
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
Instalar las dependencias
bash
Copiar
Editar
pip install -r requirements.txt
Ejecución del proyecto
Usando Uvicorn
bash
Copiar
Editar
uvicorn main:app --reload
La aplicación estará disponible en http://127.0.0.1:8000/.
fastapi.tiangolo.com

Usando Docker
bash
Copiar
Editar
docker-compose up --build
Esto levantará la aplicación junto con sus servicios dependientes definidos en docker-compose.yml.

Documentación de la API
Swagger UI: http://127.0.0.1:8000/docs

ReDoc: http://127.0.0.1:8000/redoc
fastapi.tiangolo.com

Estas interfaces proporcionan una documentación interactiva de los endpoints disponibles en la API.

Contribuciones
Las contribuciones son bienvenidas. Si deseas colaborar, por favor sigue los siguientes pasos:

Haz un fork del repositorio.

Crea una nueva rama (git checkout -b feature/nueva-funcionalidad).

Realiza tus cambios y haz commit de los mismos (git commit -am 'Agrega nueva funcionalidad').

Haz push a la rama (git push origin feature/nueva-funcionalidad).

Abre un Pull Request.
fastapi.tiangolo.com
+8
testdriven.io
+8
fastapi.tiangolo.com
+8

Licencia
Este proyecto está licenciado bajo la Licencia MIT. Consulta el archivo LICENSE para más detalles.

Contacto
Para más información o consultas, por favor contacta a jadapache.