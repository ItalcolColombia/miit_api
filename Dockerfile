
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

# Actualización de CA trust store
RUN update-ca-trust extract

#Configuración zona horaria (America/Bogota)
RUN ln -sf /usr/share/zoneinfo/America/Bogota /etc/localtime && \
    echo "America/Bogota" > /etc/localtime

# Download and install Python 3.13.3
RUN cd /usr/src \  
  && wget https://www.python.org/ftp/python/3.13.3/Python-3.13.3.tgz \ 
  && tar -xzf Python-3.13.3.tgz \     
  && cd Python-3.13.3 \     
  && ./configure --enable-optimizations \     
  && make altinstall \
  && ln -s /usr/local/bin/python3.13.3 /usr/bin/python3.13.3 \
  && ln -s /usr/local/bin/pip3.13.3 /usr/bin/pip3.13.3
	
# Verify Python installation
RUN python3.13 --version

#Instalar o actualizar gestor de paquetes pip, setuptools y wheel
RUN python3.13 -m pip install --upgrade pip setuptools wheel

# Establece el directorio de trabajo
WORKDIR /var/www/metalsoft/miit_api

#Clonar y obtener proyecto
RUN cd /var/www/metalsoft/work_dir
RUN git clone https://oauth2:${ghp_TOKEN}@github.com/jadapache/miit.git . && \
    rm -rf .git

#Definir las variables de entorno
ENV API_NAME=MIIT_API \
    API_HOST=0.0.0.0 \
    API_PORT=8443
    API_VERSION=0.0.1

#Copia los archivos de la api al contenedor
COPY . /var/www/metalsoft/miit_api

# Instalar dependencias de Python
COPY requirements.txt .
RUN python3.13 -m pip install --no-cache-dir -r requirements.txt

# Crea el directorio de log
RUN mkdir -p /var/www/metalsoft/log/miit_api && chmod -R 777 /var/www/metalsoft/log/miit_api

#Comando para iniciar servicio
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8443"]

