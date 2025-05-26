
#Definir imagen de SO
FROM registry.access.redhat.com/ubi8/ubi:latest


##Instalar dependencias del sistema
RUN yum update -y && \
    yum install -y \
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
    curl && \
    rm -rf /var/cache/yum/*


## Creación de directorio y copia de certificados SSL
# COPY ./certs/turbograneles_wildcard_cer.crt /etc/pki/ssl/certs/
# COPY ./certs/turbograneles_wildcard.key /etc/pki/ssl/private/


# Actualización de CA trust store
RUN update-ca-trust extract

#Configuración zona horaria (America/Bogota)
RUN ln -sf /usr/share/zoneinfo/America\Bogota  /etc/localtime && \
    echo "America/Bogota" > /etc/localtime \


# Download and install Python 3.13.2
RUN cd /usr/src && \
    wget https://www.python.org/ftp/python/3.13.3/Python-3.13.3.tgz && \
    tar xzf Python-3.13.3.tgz && \
    cd Python-3.13.3 && \
    ./configure --enable-optimizations && \
    make altinstall && \
    ln -s /usr/local/bin/python3.13 /usr/bin/python3.13 && \
    ln -s /usr/local/bin/pip3.13 /usr/bin/pip3.13 && \
    cd /usr/src && \
    rm -rf Python-3.13.3.tgz Python-3.13.3

# Verify Python installation
RUN python3.13 --version

#Instalar o actualizar gestor de paquetes pip, setuptools y wheel
RUN python3.13 -m pip install --upgrade pip setuptools wheel


# RUN chmod -R 600 /etc/pki/ssl/private && \
   # chmod -R 600 /etc/pki/ssl/certs

# Establece el directorio de trabajo
WORKDIR /var/www/metalsoft/work_dir

#Clonar y obtener proyecto
RUN cd /var/www/metalsoft/work_dir
RUN git clone https://oauth2:${ghp_TOKEN}@github.com/jadapache/miit.git . && \
    rm -rf .git

#Definir las variables de entorno
ENV API_NAME=MIIT_API \
    API_HOST=0.0.0.0 \
    API_PORT=8443

#Copia los archivos de la api al contenedor
COPY . /var/www/metalsoft/miit_api

# Instalar dependencias de Python
COPY requirements.txt .
RUN python3.13 -m pip install --no-cache-dir -r requirements.txt

# Crea el directorio de log
RUN mkdir -p /var/www/metalsoft/log/miit_api && chmod -R 777 /var/www/metalsoft/log/miit_api

# Exponer los puertos necesarios
EXPOSE 80 443 8443 5517

#Comando para iniciar servicio
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8443"]
#     "--ssl-keyfile", "/etc/ssl/private/server.key", "--ssl-certfile", "/etc/ssl/certs/server.crt"]

