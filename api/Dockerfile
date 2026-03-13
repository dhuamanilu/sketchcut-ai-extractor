# Usar una imagen oficial de Python ligera
FROM python:3.9-slim

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el archivo de requerimientos primero para aprovechar la cache de capas de Docker
COPY requirements.txt .

# Instalar las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código de la aplicación (excluyendo lo que esté en .dockerignore)
COPY . .

# Exponer el puerto 8000 para acceso web
EXPOSE 8000

# Comando para ejecutar la aplicación con Uvicorn de forma optimizada
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
