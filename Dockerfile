FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# deps de sistema para postgres
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# copia requirements
COPY requirements.txt /app/

# instala dependencias (fijas django aquí)
RUN pip install --no-cache-dir -r requirements.txt

# copia el resto del proyecto
COPY . /app/

# expone el puerto que usará gunicorn
EXPOSE 8500

# comando de arranque
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8500"]
