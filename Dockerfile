
#Definir imagen de SO
FROM registry.access.redhat.com/ubi9/python-312

# Argumentos de build para ambiente y configuración
ARG GIT_BRANCH=main
ARG ghp_TOKEN
ARG KEEP_VERSIONED_CERTS=false

USER root

##Instalar dependencias del sistema
RUN yum update -y && \
    yum install -y \
        procps-ng \
        dnf \
        gcc \
        openssl-devel \
        bzip2-devel \
        libffi-devel \
        zlib-devel \
        wget \
        tzdata \
        unzip \
        git \
        ca-certificates \
        make \
        curl-minimal && \
        rm -rf /var/cache/yum/*

# Actualización de CA trust store
RUN update-ca-trust extract

#Configuración zona horaria (America/Bogota)
ENV TZ=America/Bogota
ENV TG_API_VERIFY_SSL=True
RUN ln -sf /usr/share/zoneinfo/America/Bogota /etc/localtime && \
    echo "America/Bogota" > /etc/timezone

#Instalar o actualizar gestor de paquetes pip, setuptools, wheel, supervisor
RUN pip install --upgrade pip "setuptools<81" wheel supervisor

# Establece el directorio de trabajo
WORKDIR /var/www/metalsoft/miit_api

#Clonar y obtener proyecto de la rama especificada
RUN git clone --branch ${GIT_BRANCH} https://oauth2:${ghp_TOKEN}@github.com/ItalcolColombia/miit_api .

# Si no se requieren certificados versionados dentro de la imagen, se eliminan.
# El contenedor seguirá usando el trust store del sistema (ca-certificates).
RUN if [ "${KEEP_VERSIONED_CERTS}" != "true" ]; then rm -rf certs; fi


# #Copia los archivos de la api al contenedor
# COPY . /var/www/metalsoft/miit_api

# Instalar dependencias y Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#Copiar configuración supervisord
COPY supervisord.conf /etc/supervisord.conf

#Copiar y dar permisos al script de inicio
COPY start.sh /var/www/metalsoft/miit_api/start.sh
RUN sed -i 's/\r$//' /var/www/metalsoft/miit_api/start.sh && \
    chmod +x /var/www/metalsoft/miit_api/start.sh

# Crea el directorio de log de la API
RUN mkdir -p /var/www/metalsoft/log/miit_api && chmod -R 777 /var/www/metalsoft/log/miit_api

# Crea el directorio de log de supervisord
RUN mkdir -p /var/www/metalsoft/log/supervisord && chmod -R 777 /var/www/metalsoft/log/supervisord


# Se expone el puerto
EXPOSE 8443

#Comando para iniciar servicio con supervisor
CMD ["supervisord", "-c", "/etc/supervisord.conf"]
