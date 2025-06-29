FROM python:3.11.9-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requisitos
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Exponer puerto dinámico para Render - ACTUALIZACIÓN 6
EXPOSE $PORT

# Comando con PORT variable para Render - ACTUALIZACIÓN 6
CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port $PORT"]
