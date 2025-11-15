#!/bin/bash

# Esperar a que PostgreSQL esté listo (si usas DB_HOST)
if [ -n "$DB_HOST" ]; then
    echo "Esperando PostgreSQL en $DB_HOST:$DB_PORT..."
    while ! nc -z $DB_HOST ${DB_PORT:-5432}; do
        sleep 0.1
    done
    echo "PostgreSQL está listo"
fi

# Ejecutar migraciones
echo "Ejecutando migraciones..."
python manage.py migrate --noinput

# Recolectar archivos estáticos
echo "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear

# Iniciar Gunicorn con Uvicorn workers (para ASGI + Socket.IO)
echo "Iniciando Gunicorn con Uvicorn workers (ASGI + Socket.IO)..."
exec gunicorn config.asgi:application \
    --bind 0.0.0.0:8500 \
    --workers 3 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info