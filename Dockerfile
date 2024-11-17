#Usa una imagen oficial ligera de Python
FROM python:3.9-slim

#Establece variables de entorno para optimizar Python en producción
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

#Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

#Copia el archivo de dependencias al contenedor
COPY requirements.txt .

#Instala las dependencias necesarias
RUN pip install --no-cache-dir -r requirements.txt

#Crea un usuario no root por seguridad
RUN useradd -m appuser
RUN chown -R appuser:appuser /app

#Cambia al usuario no root
USER appuser

#Copia el resto del código al directorio de trabajo
COPY . .

#Expone el puerto 8000 para la aplicación
EXPOSE 8000

#Comando por defecto para iniciar la aplicación
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]