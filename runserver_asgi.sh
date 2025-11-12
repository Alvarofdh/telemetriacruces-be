#!/bin/bash

# Script para iniciar el servidor Django con ASGI (requerido para Socket.IO)
# Este script usa Uvicorn directamente para soportar Socket.IO

echo "🚀 Iniciando servidor Django con ASGI (Socket.IO habilitado)..."
echo "📡 Socket.IO disponible en: http://localhost:8000/socket.io/"
echo ""

# Activar entorno virtual si existe
if [ -d "venv" ]; then
	source venv/bin/activate
fi

# Verificar que uvicorn esté instalado
if ! python -c "import uvicorn" 2>/dev/null; then
	echo "❌ Error: uvicorn no está instalado"
	echo "   Instala con: pip install uvicorn[standard]"
	exit 1
fi

# Ejecutar migraciones
echo "📦 Ejecutando migraciones..."
python manage.py migrate --noinput

# Iniciar servidor con Uvicorn (ASGI)
echo "✅ Iniciando servidor en http://localhost:8000"
echo "   Presiona Ctrl+C para detener"
echo ""

exec uvicorn config.asgi:application \
	--host 0.0.0.0 \
	--port 8000 \
	--reload \
	--log-level info

