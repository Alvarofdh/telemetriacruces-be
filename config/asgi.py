"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application

# Inicializar Django antes de importar Socket.IO
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django_asgi_app = get_asgi_application()

# Importar Socket.IO después de inicializar Django
from apps.api.socketio_app import socketio_app, sio


async def asgi_app(scope, receive, send):
	"""
	Aplicación ASGI que enruta peticiones entre Django y Socket.IO.
	
	- Maneja el protocolo 'lifespan' para eventos de inicio/cierre
	- Si la ruta es '/socket.io/', la maneja Socket.IO
	- Si no, la maneja Django
	"""
	# Manejar protocolo lifespan (inicio/cierre de aplicación)
	if scope['type'] == 'lifespan':
		while True:
			message = await receive()
			if message['type'] == 'lifespan.startup':
				# Evento de inicio - inicializar recursos si es necesario
				await send({'type': 'lifespan.startup.complete'})
			elif message['type'] == 'lifespan.shutdown':
				# Evento de cierre - limpiar recursos si es necesario
				await send({'type': 'lifespan.shutdown.complete'})
				break
		return
	
	# Manejar rutas HTTP y WebSocket
	path = scope.get('path', '')
	
	# Si es una ruta de Socket.IO, usar socketio_app
	if path.startswith('/socket.io/'):
		await socketio_app(scope, receive, send)
	else:
		# Para todas las demás rutas, usar Django
		await django_asgi_app(scope, receive, send)


# Aplicación ASGI que maneja tanto HTTP como WebSocket
application = asgi_app
