"""
Interfaz de administración para Socket.IO.
Implementa el namespace /admin compatible con Socket.IO Admin UI.

En python-socketio, los decoradores deben estar en el nivel del módulo.
Basado en: https://socket.io/docs/v4/admin-ui/
"""
import socketio
import logging
import os
import platform
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

# Almacenamiento de estadísticas
stats = {
	'servers': {},
	'namespaces': defaultdict(dict),
	'rooms': defaultdict(dict),
	'sockets': {},
	'events': [],
}

# Namespace de administración
ADMIN_NAMESPACE = '/admin'

# Variable global para el servidor (se establecerá en setup_admin_namespace)
_sio_instance = None


def setup_admin_namespace(sio):
	"""
	Configurar el namespace /admin para la interfaz de administración.
	
	En python-socketio, los decoradores se registran cuando se importa el módulo,
	pero necesitamos acceso al servidor. Usamos una variable global.
	
	Args:
		sio: Instancia de AsyncServer de Socket.IO
	"""
	global _sio_instance
	_sio_instance = sio
	logger.info("✅ Socket.IO Admin UI configurado (namespace /admin)")


# Eventos del namespace /admin
# Nota: Estos decoradores se registran cuando se importa el módulo
# pero solo funcionan si _sio_instance está configurado

def get_sio():
	"""Obtener la instancia del servidor"""
	if _sio_instance is None:
		raise RuntimeError("Admin namespace no está configurado. Llama a setup_admin_namespace() primero.")
	return _sio_instance


# Los eventos se registrarán dinámicamente cuando se llame a setup_admin_namespace
# Para evitar problemas, usamos una función que registra los eventos

def register_admin_events(sio):
	"""
	Registrar todos los eventos del namespace /admin.
	Esta función debe llamarse después de crear el servidor.
	"""
	
	@sio.event(namespace=ADMIN_NAMESPACE)
	async def connect(sid, environ, auth):
		"""Manejar conexión al namespace admin"""
		try:
			logger.info(f"🔧 Admin UI conectado: {sid}")
			await sio.save_session(sid, {
				'connected_at': datetime.now().isoformat(),
				'type': 'admin_ui'
			}, namespace=ADMIN_NAMESPACE)
			
			# Enviar información automáticamente al conectarse (lo que espera Admin UI)
			hostname = platform.node() if hasattr(platform, 'node') else 'unknown'
			
			# Enviar información del servidor automáticamente
			server_info = {
				'id': os.getenv('SERVER_ID', hostname),
				'hostname': hostname,
				'pid': os.getpid(),
				'uptime': get_uptime(),
				'namespaces': ['/', ADMIN_NAMESPACE],
			}
			await sio.emit('servers', [server_info], room=sid, namespace=ADMIN_NAMESPACE)
			
			# Enviar información de namespaces automáticamente
			namespaces_info = [
				{
					'name': '/',
					'socketsCount': len(list(sio.manager.get_participants('/', '/'))),
				},
				{
					'name': ADMIN_NAMESPACE,
					'socketsCount': len(list(sio.manager.get_participants(ADMIN_NAMESPACE, '/'))),
				},
			]
			await sio.emit('namespaces', namespaces_info, room=sid, namespace=ADMIN_NAMESPACE)
			
			logger.info(f"✅ Información enviada a Admin UI: {sid}")
			
		except Exception as e:
			logger.error(f"Error en conexión admin: {str(e)}", exc_info=True)
	
	@sio.event(namespace=ADMIN_NAMESPACE)
	async def disconnect(sid):
		"""Manejar desconexión del namespace admin"""
		logger.info(f"🔧 Admin UI desconectado: {sid}")
	
	@sio.on('get_servers', namespace=ADMIN_NAMESPACE)
	async def get_servers(sid, data):
		"""Obtener lista de servidores"""
		try:
			hostname = platform.node() if hasattr(platform, 'node') else 'unknown'
			server_info = {
				'id': os.getenv('SERVER_ID', hostname),
				'hostname': hostname,
				'pid': os.getpid(),
				'uptime': get_uptime(),
				'namespaces': ['/', ADMIN_NAMESPACE],
			}
			await sio.emit('servers', [server_info], room=sid, namespace=ADMIN_NAMESPACE)
		except Exception as e:
			logger.error(f"Error obteniendo servidores: {str(e)}")
	
	@sio.on('get_namespaces', namespace=ADMIN_NAMESPACE)
	async def get_namespaces(sid, data):
		"""Obtener información de namespaces"""
		try:
			namespaces_info = [
				{
					'name': '/',
					'socketsCount': len(list(sio.manager.get_participants('/', '/'))),
				},
				{
					'name': ADMIN_NAMESPACE,
					'socketsCount': len(list(sio.manager.get_participants(ADMIN_NAMESPACE, '/'))),
				},
			]
			await sio.emit('namespaces', namespaces_info, room=sid, namespace=ADMIN_NAMESPACE)
		except Exception as e:
			logger.error(f"Error obteniendo namespaces: {str(e)}")
			await sio.emit('error', {'message': str(e)}, room=sid, namespace=ADMIN_NAMESPACE)
	
	@sio.on('get_sockets', namespace=ADMIN_NAMESPACE)
	async def get_sockets(sid, data):
		"""Obtener información de sockets"""
		try:
			namespace_name = data.get('namespace', '/')
			
			sockets_info = []
			try:
				all_sockets = list(sio.manager.get_participants(namespace_name, '/'))
				
				for socket_id in all_sockets:
					try:
						socket_session = await sio.get_session(socket_id, namespace=namespace_name)
						sockets_info.append({
							'id': socket_id,
							'data': socket_session or {},
						})
					except Exception as e:
						logger.debug(f"No se pudo obtener sesión de socket {socket_id}: {str(e)}")
			except Exception as e:
				logger.warning(f"Error obteniendo lista de sockets: {str(e)}")
			
			await sio.emit('sockets', sockets_info, room=sid, namespace=ADMIN_NAMESPACE)
		except Exception as e:
			logger.error(f"Error obteniendo sockets: {str(e)}")
			await sio.emit('error', {'message': str(e)}, room=sid, namespace=ADMIN_NAMESPACE)
	
	@sio.on('get_rooms', namespace=ADMIN_NAMESPACE)
	async def get_rooms(sid, data):
		"""Obtener información de salas"""
		try:
			rooms_info = []
			# Nota: python-socketio no expone directamente las salas
			# Por ahora retornamos información básica
			await sio.emit('rooms', rooms_info, room=sid, namespace=ADMIN_NAMESPACE)
		except Exception as e:
			logger.error(f"Error obteniendo salas: {str(e)}")
	
	@sio.on('join_room', namespace=ADMIN_NAMESPACE)
	async def join_room_admin(sid, data):
		"""Unir un socket a una sala (operación administrativa)"""
		try:
			target_socket_id = data.get('socketId')
			room_name = data.get('room')
			namespace_name = data.get('namespace', '/')
			
			await sio.enter_room(target_socket_id, room_name, namespace=namespace_name)
			
			logger.info(f"🔧 Admin: Socket {target_socket_id} unido a sala {room_name}")
			await sio.emit('room_joined', {
				'socketId': target_socket_id,
				'room': room_name
			}, room=sid, namespace=ADMIN_NAMESPACE)
		except Exception as e:
			logger.error(f"Error uniendo socket a sala: {str(e)}")
			await sio.emit('error', {'message': str(e)}, room=sid, namespace=ADMIN_NAMESPACE)
	
	@sio.on('leave_room', namespace=ADMIN_NAMESPACE)
	async def leave_room_admin(sid, data):
		"""Sacar un socket de una sala (operación administrativa)"""
		try:
			target_socket_id = data.get('socketId')
			room_name = data.get('room')
			namespace_name = data.get('namespace', '/')
			
			await sio.leave_room(target_socket_id, room_name, namespace=namespace_name)
			
			logger.info(f"🔧 Admin: Socket {target_socket_id} salió de sala {room_name}")
			await sio.emit('room_left', {
				'socketId': target_socket_id,
				'room': room_name
			}, room=sid, namespace=ADMIN_NAMESPACE)
		except Exception as e:
			logger.error(f"Error sacando socket de sala: {str(e)}")
			await sio.emit('error', {'message': str(e)}, room=sid, namespace=ADMIN_NAMESPACE)
	
	@sio.on('disconnect_socket', namespace=ADMIN_NAMESPACE)
	async def disconnect_socket_admin(sid, data):
		"""Desconectar un socket (operación administrativa)"""
		try:
			target_socket_id = data.get('socketId')
			namespace_name = data.get('namespace', '/')
			
			await sio.disconnect(target_socket_id, namespace=namespace_name)
			
			logger.info(f"🔧 Admin: Socket {target_socket_id} desconectado")
			await sio.emit('socket_disconnected', {
				'socketId': target_socket_id
			}, room=sid, namespace=ADMIN_NAMESPACE)
		except Exception as e:
			logger.error(f"Error desconectando socket: {str(e)}")
			await sio.emit('error', {'message': str(e)}, room=sid, namespace=ADMIN_NAMESPACE)
	
	logger.info("✅ Eventos del namespace /admin registrados")


async def send_server_stats(sio, sid):
	"""Enviar estadísticas del servidor al cliente admin"""
	try:
		hostname = platform.node() if hasattr(platform, 'node') else 'unknown'
		server_info = {
			'id': os.getenv('SERVER_ID', hostname),
			'hostname': hostname,
			'pid': os.getpid(),
			'uptime': get_uptime(),
			'timestamp': datetime.now().isoformat(),
		}
		await sio.emit('server_stats', server_info, room=sid, namespace=ADMIN_NAMESPACE)
	except Exception as e:
		logger.error(f"Error enviando estadísticas: {str(e)}")


def get_uptime():
	"""Obtener tiempo de actividad del servidor (en segundos)"""
	try:
		import psutil
		process = psutil.Process(os.getpid())
		return int((datetime.now() - datetime.fromtimestamp(process.create_time())).total_seconds())
	except:
		return 0
