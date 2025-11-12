"""
Socket.IO Application para el sistema de monitoreo de cruces ferroviarios.

Este módulo maneja las conexiones WebSocket en tiempo real para:
- Telemetría en tiempo real
- Eventos de barrera
- Alertas del sistema
- Notificaciones a usuarios

Seguridad implementada:
- Autenticación JWT
- Validación de origen (CORS)
- Rate limiting
- Validación de datos
"""
import socketio
import logging
from django.conf import settings
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
from django.core.cache import cache
from asgiref.sync import sync_to_async
from datetime import timedelta
import time

logger = logging.getLogger(__name__)
User = get_user_model()

# Configuración de CORS para Socket.IO
# Permitir localhost y orígenes configurados, además de None/null para clientes sin origen
socketio_cors_origins = getattr(settings, 'SOCKETIO_CORS_ALLOWED_ORIGINS', [])
if not socketio_cors_origins and hasattr(settings, 'CORS_ALLOWED_ORIGINS'):
	socketio_cors_origins = settings.CORS_ALLOWED_ORIGINS

# Agregar localhost para desarrollo si no está presente
if settings.DEBUG:
	localhost_origins = [
		'http://localhost:8000', 
		'http://127.0.0.1:8000', 
		'http://localhost:3000', 
		'http://127.0.0.1:3000',
		'http://localhost:8080',  # Para servidor HTTP local del HTML
		'http://127.0.0.1:8080',
		'http://localhost:5173',  # Vite
		'http://127.0.0.1:5173',
		'null',  # Para file:// (aunque no es ideal, permite polling)
	]
	for origin in localhost_origins:
		if origin not in socketio_cors_origins:
			socketio_cors_origins.append(origin)

# Configuración de Socket.IO con seguridad desde settings
sio = socketio.AsyncServer(
	async_mode='asgi',
	cors_allowed_origins=socketio_cors_origins if socketio_cors_origins else '*',  # Permitir todos en desarrollo si está vacío
	cors_credentials=getattr(settings, 'SOCKETIO_CORS_CREDENTIALS', True),
	ping_timeout=getattr(settings, 'SOCKETIO_PING_TIMEOUT', 60),
	ping_interval=getattr(settings, 'SOCKETIO_PING_INTERVAL', 25),
	max_http_buffer_size=getattr(settings, 'SOCKETIO_MAX_HTTP_BUFFER_SIZE', 1e6),
	allow_upgrades=getattr(settings, 'SOCKETIO_ALLOW_UPGRADES', True),
	transports=getattr(settings, 'SOCKETIO_TRANSPORTS', ['websocket', 'polling']),
	logger=True,
	engineio_logger=True if settings.DEBUG else False,  # Habilitar en desarrollo para debugging detallado
)

# Aplicación ASGI
socketio_app = socketio.ASGIApp(sio, socketio_path='socket.io')


# Rate limiting: máximo de conexiones por IP (desde settings)
MAX_CONNECTIONS_PER_IP = getattr(settings, 'SOCKETIO_MAX_CONNECTIONS_PER_IP', 5)
RATE_LIMIT_WINDOW = getattr(settings, 'SOCKETIO_RATE_LIMIT_WINDOW', 60)  # segundos
MAX_EVENTS_PER_MINUTE = getattr(settings, 'SOCKETIO_MAX_EVENTS_PER_MINUTE', 60)


def get_client_ip(environ):
	"""Obtener IP del cliente desde el entorno"""
	# Intentar obtener IP real (útil con proxies)
	x_forwarded_for = environ.get('HTTP_X_FORWARDED_FOR')
	if x_forwarded_for:
		ip = x_forwarded_for.split(',')[0].strip()
	else:
		ip = environ.get('REMOTE_ADDR', 'unknown')
	return ip


# Función síncrona para rate limiting (usada con sync_to_async)
def _check_rate_limit_sync(client_ip):
	"""Verificar rate limiting por IP (versión síncrona)"""
	# Verificar conexiones simultáneas por IP
	connections_key = f'socketio_connections_{client_ip}'
	current_connections = cache.get(connections_key, 0)
	
	if current_connections >= MAX_CONNECTIONS_PER_IP:
		logger.warning(f"Rate limit excedido para IP {client_ip}: {current_connections} conexiones")
		return False
	
	# Incrementar contador de conexiones
	cache.set(connections_key, current_connections + 1, timeout=RATE_LIMIT_WINDOW)
	
	# Verificar eventos por minuto
	events_key = f'socketio_events_{client_ip}'
	event_count = cache.get(events_key, 0)
	
	if event_count >= MAX_EVENTS_PER_MINUTE:
		logger.warning(f"Rate limit de eventos excedido para IP {client_ip}")
		return False
	
	return True


# Versión asíncrona usando sync_to_async
check_rate_limit_async = sync_to_async(_check_rate_limit_sync)


# Función síncrona para autenticar (usada con sync_to_async)
def _authenticate_socket_sync(token):
	"""
	Autenticar socket usando JWT token (versión síncrona).
	
	Args:
		token: Token JWT como string
		
	Returns:
		User object si es válido, None si no
	"""
	try:
		# Validar token
		untyped_token = UntypedToken(token)
		user_id = untyped_token['user_id']
		
		# Obtener usuario
		try:
			user = User.objects.get(id=user_id)
			if not user.is_active:
				logger.warning(f"Usuario inactivo intentando conectar: {user_id}")
				return None
			return user
		except User.DoesNotExist:
			logger.warning(f"Usuario no encontrado: {user_id}")
			return None
			
	except (InvalidToken, TokenError, KeyError) as e:
		logger.warning(f"Token inválido en Socket.IO: {str(e)}")
		return None
	except Exception as e:
		logger.error(f"Error en autenticación Socket.IO: {str(e)}")
		return None


# Versión asíncrona usando sync_to_async
authenticate_socket = sync_to_async(_authenticate_socket_sync)


@sio.event
async def connect(sid, environ, auth):
	"""
	Manejar conexión de cliente.
	
	Requiere autenticación JWT en el campo 'token' de auth.
	"""
	try:
		# Obtener información del cliente
		client_ip = get_client_ip(environ)
		
		# Logging detallado de nueva conexión
		logger.info(f"🔌 Nueva conexión: SID={sid}, IP={client_ip}")
		if settings.DEBUG:
			logger.debug(f"   User-Agent: {environ.get('HTTP_USER_AGENT', 'unknown')}")
			logger.debug(f"   Transport: {environ.get('HTTP_UPGRADE', 'polling')}")
			logger.debug(f"   Origin: {environ.get('HTTP_ORIGIN', 'unknown')}")
		
		# Verificar rate limiting (ahora es async)
		if not await check_rate_limit_async(client_ip):
			logger.warning(f"❌ Conexión rechazada por rate limit: {sid} (IP: {client_ip})")
			await sio.disconnect(sid)
			return False
		
		# Obtener token de autenticación
		if not auth or 'token' not in auth:
			logger.warning(f"❌ Intento de conexión sin token: {sid}")
			await sio.disconnect(sid)
			return False
		
		token = auth['token']
		
		# Autenticar usuario (ahora es async)
		user = await authenticate_socket(token)
		if not user:
			logger.warning(f"❌ Autenticación fallida para socket: {sid}")
			await sio.disconnect(sid)
			return False
		
		# Guardar información del usuario en la sesión
		await sio.save_session(sid, {
			'user_id': user.id,
			'username': user.username,
			'email': user.email,
			'ip': get_client_ip(environ),
			'connected_at': time.time(),
		})
		
		# Unir al usuario a una sala personalizada
		await sio.enter_room(sid, f'user_{user.id}')
		
		# Unir a sala general para notificaciones globales
		await sio.enter_room(sid, 'notifications')
		
		logger.info(f"✅ Conexión exitosa: {user.username} (ID: {user.id}, Socket: {sid})")
		
		# Enviar confirmación de conexión
		await sio.emit('connected', {
			'status': 'success',
			'message': 'Conectado exitosamente',
			'user': {
				'id': user.id,
				'username': user.username,
				'email': user.email,
			}
		}, room=sid)
		
		return True
		
	except Exception as e:
		logger.error(f"❌ Error en conexión Socket.IO {sid}: {str(e)}", exc_info=True)
		await sio.disconnect(sid)
		return False


@sio.event
async def disconnect(sid, reason=None):
	"""Manejar desconexión de cliente"""
	try:
		session = await sio.get_session(sid)
		user_id = session.get('user_id')
		username = session.get('username', 'unknown')
		
		# Decrementar contador de conexiones
		ip = session.get('ip', 'unknown')
		if ip != 'unknown':
			connections_key = f'socketio_connections_{ip}'
			current_connections = cache.get(connections_key, 0)
			if current_connections > 0:
				cache.set(connections_key, current_connections - 1, timeout=RATE_LIMIT_WINDOW)
		
		reason_msg = f" - Razón: {reason}" if reason else ""
		logger.info(f"Cliente desconectado: {username} (ID: {user_id}, Socket: {sid}){reason_msg}")
		
	except Exception as e:
		logger.error(f"Error en desconexión Socket.IO: {str(e)}")


@sio.event
async def subscribe(sid, data):
	"""
	Suscribirse a eventos específicos.
	
	Eventos disponibles:
	- telemetria: Telemetría en tiempo real
	- barrier_events: Eventos de barrera
	- alertas: Alertas del sistema
	- cruce_{id}: Eventos de un cruce específico
	"""
	try:
		session = await sio.get_session(sid)
		user_id = session.get('user_id')
		
		if not data or 'events' not in data:
			await sio.emit('error', {
				'message': 'Formato inválido. Se requiere campo "events"'
			}, room=sid)
			return
		
		events = data['events']
		if not isinstance(events, list):
			events = [events]
		
		# Validar eventos permitidos
		allowed_events = ['telemetria', 'barrier_events', 'alertas', 'notifications']
		
		for event in events:
			if event.startswith('cruce_'):
				# Suscripción a cruce específico
				cruce_id = event.replace('cruce_', '')
				room_name = f'cruce_{cruce_id}'
				await sio.enter_room(sid, room_name)
				logger.info(f"Usuario {user_id} suscrito a cruce {cruce_id}")
			elif event in allowed_events:
				# Suscripción a evento general
				await sio.enter_room(sid, event)
				logger.info(f"Usuario {user_id} suscrito a {event}")
			else:
				logger.warning(f"Intento de suscripción a evento no permitido: {event}")
		
		await sio.emit('subscribed', {
			'status': 'success',
			'events': events,
			'message': 'Suscripción exitosa'
		}, room=sid)
		
	except Exception as e:
		logger.error(f"Error en suscripción: {str(e)}")
		await sio.emit('error', {
			'message': f'Error en suscripción: {str(e)}'
		}, room=sid)


@sio.event
async def join_room(sid, data):
	"""
	Unirse a una sala (compatibilidad con frontend).
	
	Formato: { room: 'nombre_sala' }
	"""
	try:
		session = await sio.get_session(sid)
		user_id = session.get('user_id')
		
		if not data or 'room' not in data:
			await sio.emit('error', {
				'message': 'Formato inválido. Se requiere campo "room"'
			}, room=sid)
			return
		
		room = data['room']
		await sio.enter_room(sid, room)
		logger.info(f"Usuario {user_id} se unió a sala: {room}")
		
		await sio.emit('joined_room', {
			'status': 'success',
			'room': room,
			'message': f'Unido a sala {room}'
		}, room=sid)
		
	except Exception as e:
		logger.error(f"Error al unirse a sala: {str(e)}")
		await sio.emit('error', {
			'message': f'Error al unirse a sala: {str(e)}'
		}, room=sid)


@sio.event
async def leave_room(sid, data):
	"""
	Salir de una sala (compatibilidad con frontend).
	
	Formato: { room: 'nombre_sala' }
	"""
	try:
		session = await sio.get_session(sid)
		user_id = session.get('user_id')
		
		if not data or 'room' not in data:
			await sio.emit('error', {
				'message': 'Formato inválido. Se requiere campo "room"'
			}, room=sid)
			return
		
		room = data['room']
		await sio.leave_room(sid, room)
		logger.info(f"Usuario {user_id} salió de sala: {room}")
		
		await sio.emit('left_room', {
			'status': 'success',
			'room': room,
			'message': f'Salido de sala {room}'
		}, room=sid)
		
	except Exception as e:
		logger.error(f"Error al salir de sala: {str(e)}")


@sio.event
async def unsubscribe(sid, data):
	"""Desuscribirse de eventos"""
	try:
		session = await sio.get_session(sid)
		user_id = session.get('user_id')
		
		if not data or 'events' not in data:
			await sio.emit('error', {
				'message': 'Formato inválido. Se requiere campo "events"'
			}, room=sid)
			return
		
		events = data['events']
		if not isinstance(events, list):
			events = [events]
		
		for event in events:
			if event.startswith('cruce_'):
				room_name = f'cruce_{event.replace("cruce_", "")}'
				await sio.leave_room(sid, room_name)
			else:
				await sio.leave_room(sid, event)
		
		await sio.emit('unsubscribed', {
			'status': 'success',
			'events': events,
			'message': 'Desuscripción exitosa'
		}, room=sid)
		
	except Exception as e:
		logger.error(f"Error en desuscripción: {str(e)}")


@sio.event
async def ping(sid):
	"""Manejar ping del cliente (health check)"""
	try:
		session = await sio.get_session(sid)
		await sio.emit('pong', {
			'timestamp': time.time(),
			'status': 'ok'
		}, room=sid)
	except Exception as e:
		logger.error(f"Error en ping: {str(e)}")


@sio.event
async def catch_all(event, sid, data):
	"""
	Manejar eventos no reconocidos (catch-all handler).
	
	Útil para debugging y detectar eventos del frontend que no están implementados.
	Según documentación: https://python-socketio.readthedocs.io/en/stable/server.html#catch-all-event-handlers
	"""
	try:
		session = await sio.get_session(sid)
		user_id = session.get('user_id', 'unknown')
		
		logger.warning(f"⚠️ Evento no reconocido '{event}' de usuario {user_id} (SID: {sid})")
		if settings.DEBUG:
			logger.debug(f"   Datos recibidos: {data}")
		
		await sio.emit('error', {
			'status': 'error',
			'message': f"Evento '{event}' no está implementado en el servidor",
			'event': event,
			'hint': 'Verifica que el nombre del evento sea correcto'
		}, room=sid)
		
	except Exception as e:
		logger.error(f"Error en catch_all handler: {str(e)}")

