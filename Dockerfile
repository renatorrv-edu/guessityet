# Usar Python 3.11 slim como base
FROM python:3.11-slim

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Crear usuario no-root para seguridad
RUN groupadd -r django && useradd -r -g django django

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    # Dependencias básicas
    build-essential \
    curl \
    # PostgreSQL client y headers
    libpq-dev \
    postgresql-client \
    # Para Pillow (procesamiento de imágenes)
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    # Para moviepy (procesamiento de video)
    ffmpeg \
    # Para compilar algunas dependencias de Python
    gcc \
    g++ \
    # Limpieza
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements primero para aprovechar cache de Docker
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Crear directorios necesarios
RUN mkdir -p /app/static /app/media /app/logs && \
    chown -R django:django /app

# Copiar código fuente
COPY . .

# Instalar dependencias adicionales para producción
RUN pip install --no-cache-dir gunicorn uvicorn[standard]

# Cambiar permisos de archivos importantes
RUN chown -R django:django /app && \
    chmod +x /app/manage.py

# Cambiar a usuario no-root
USER django

# Exponer puerto
EXPOSE 8000

# Comando por defecto (se puede sobrescribir en docker-compose)
CMD ["gunicorn", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "config.asgi:application"]