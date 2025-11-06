#!/bin/sh

# aplicar migraciones
python manage.py migrate --noinput

# recolectar estáticos (si usas staticfiles)
python manage.py collectstatic --noinput

# arrancar gunicorn apuntando a tu proyecto django
gunicorn config.wsgi:application --bind 0.0.0.0:8500
