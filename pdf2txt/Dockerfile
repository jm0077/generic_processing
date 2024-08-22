# Utilizar una imagen base oficial de Python
FROM python:3.9-slim

# Establecer el directorio de trabajo en /app
WORKDIR /app

# Copiar el archivo requirements.txt en el contenedor en el directorio de trabajo
COPY requirements.txt .

# Instalar las dependencias necesarias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de la aplicación en el contenedor en el directorio de trabajo
COPY . .

# Exponer el puerto en el que correrá la aplicación
EXPOSE 8080

# Definir el comando por defecto para ejecutar la aplicación
CMD ["python", "pdf2txt.py"]
