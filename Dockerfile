FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# deps de sistema para postgres
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# instala requirements primero
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# copia todo el proyecto
COPY . /app/

# copiamos el script de arranque
COPY runserver.sh /app/runserver.sh
RUN chmod +x /app/runserver.sh

EXPOSE 8500

CMD ["/app/runserver.sh"]
