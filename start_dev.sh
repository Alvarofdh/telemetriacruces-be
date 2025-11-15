#!/bin/bash
# Script para iniciar el servidor en DESARROLLO
# Uso: ./start_dev.sh

set -e

echo "🚀 Iniciando servidor de DESARROLLO..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Directorio del proyecto (usar directorio del script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

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

# Limpiar caché de Python
echo "🧹 Limpiando caché de Python..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Verificar variables de entorno
if [ ! -f .env ]; then
	echo "❌ ERROR: Archivo .env no encontrado"
	exit 1
fi

echo "✅ Variables de entorno cargadas"

# Iniciar Uvicorn en modo desarrollo
echo ""
echo "🌟 Iniciando Uvicorn (DESARROLLO)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📍 URL: http://localhost:8000"
echo "📍 Socket.IO: ws://localhost:8000/socket.io/"
echo "📍 Admin: http://localhost:8000/admin/"
echo "📍 API Docs: http://localhost:8000/swagger/"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Iniciar con reload automático
uvicorn config.asgi:application \
	--host 0.0.0.0 \
	--port 8000 \
	--reload \
	--log-level info \
	--access-log \
	--use-colors

