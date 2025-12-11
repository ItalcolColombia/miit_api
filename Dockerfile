#Definir imagen de SO
FROM registry.access.redhat.com/ubi9/python-312

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
RUN ln -sf /usr/share/zoneinfo/America/Bogota /etc/localtime && \
    echo "America/Bogota" > /etc/timezone

#Instalar o actualizar gestor de paquetes pip, setuptools, wheel, supervisor
RUN pip install --upgrade pip "setuptools<81" wheel supervisor

# Establece el directorio de trabajo
WORKDIR /var/www/metalsoft/miit_api

#Clonar y obtener proyecto
RUN git clone https://oauth2:${ghp_TOKEN}@github.com/ItalcolColombia/miit_api .


# #Copia los archivos de la api al contenedor
# COPY . /var/www/metalsoft/miit_api

# Instalar dependencias y Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#Copiar configuración supervisord
COPY supervisord.conf /etc/supervisord.conf

#Copiar y dar permisos al script de inicio
COPY start.sh /var/www/metalsoft/miit_api/start.sh
RUN chmod +x /var/www/metalsoft/miit_api/start.sh

# Crea el directorio de log de la API
RUN mkdir -p /var/www/metalsoft/log/miit_api && chmod -R 777 /var/www/metalsoft/log/miit_api

# Crea el directorio de log de supervisord
RUN mkdir -p /var/www/metalsoft/log/supervisord && chmod -R 777 /var/www/metalsoft/log/supervisord


# Se expone el puerto
EXPOSE 8443

#Comando para iniciar servicio con supervisor
CMD ["supervisord", "-c", "/etc/supervisord.conf"]
