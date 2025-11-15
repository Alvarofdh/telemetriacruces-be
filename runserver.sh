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

# Iniciar Uvicorn (para ASGI + Socket.IO)
echo "Iniciando Uvicorn (ASGI + Socket.IO) en puerto 8500..."
exec uvicorn config.asgi:application \
    --host 0.0.0.0 \
    --port 8500 \
    --log-level info \
    --access-log