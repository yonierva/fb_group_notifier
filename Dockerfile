# Imagen oficial con Python y Playwright preinstalados
FROM mcr.microsoft.com/playwright/python:v1.63.0-jammy

ENV PYTHONUNBUFFERED=1

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos del proyecto
COPY . /app

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements

# Comando para iniciar el proceso continuo
CMD ["python", "main.py"]