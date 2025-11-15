#!/bin/bash
# Script para iniciar el servidor en PRODUCCIÓN
# Uso: ./start_prod.sh

set -e

echo "🚀 Iniciando servidor de PRODUCCIÓN..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Directorio del proyecto (usar directorio del script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Verificar que DEBUG=False
if grep -q "DEBUG.*True" .env 2>/dev/null; then
	echo "⚠️  ADVERTENCIA: DEBUG está en True en .env"
	echo "   Para producción, debe ser DEBUG=False"
	read -p "¿Continuar de todos modos? (y/N): " -n 1 -r
	echo
	if [[ ! $REPLY =~ ^[Yy]$ ]]; then
		exit 1
	fi
fi

# Matar procesos anteriores
echo "🔄 Deteniendo servidores anteriores..."
pkill -f "uvicorn|gunicorn|runserver" 2>/dev/null || true
sleep 2

# Verificar que no hay procesos en el puerto 8000
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
	echo "⚠️  Puerto 8000 ocupado, liberando..."
	lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	sleep 1
fi

# Crear directorio de logs si no existe
mkdir -p logs

# Verificar variables de entorno críticas
if [ ! -f .env ]; then
	echo "❌ ERROR: Archivo .env no encontrado"
	exit 1
fi

echo "✅ Variables de entorno cargadas"

# Recolectar archivos estáticos
echo "📦 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear

# Aplicar migraciones
echo "🔄 Aplicando migraciones..."
python manage.py migrate --noinput

# Calcular número de workers
CPU_CORES=$(nproc)
WORKERS=$((2 * CPU_CORES + 1))

echo ""
echo "🌟 Iniciando Gunicorn + Uvicorn Workers (PRODUCCIÓN)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📍 Workers: $WORKERS (CPU cores: $CPU_CORES)"
echo "📍 Bind: 0.0.0.0:8000"
echo "📍 Timeout: 120 segundos"
echo "📍 Logs: logs/access.log, logs/error.log"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Iniciar Gunicorn con Uvicorn workers
gunicorn config.asgi:application \
	-k uvicorn.workers.UvicornWorker \
	--workers $WORKERS \
	--bind 0.0.0.0:8000 \
	--timeout 120 \
	--max-requests 1000 \
	--max-requests-jitter 50 \
	--access-logfile logs/access.log \
	--error-logfile logs/error.log \
	--log-level info \
	--pid /tmp/gunicorn.pid \
	--capture-output \
	--enable-stdio-inheritance

