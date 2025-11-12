"""
Comando para probar Socket.IO desde el backend
"""
from django.core.management.base import BaseCommand
import socketio
import time
from django.conf import settings
try:
	import requests
except ImportError:
	requests = None


class Command(BaseCommand):
	help = 'Probar conexión Socket.IO al servidor'

	def add_arguments(self, parser):
		parser.add_argument(
			'--url',
			type=str,
			default='http://localhost:8000',
			help='URL del servidor Socket.IO',
		)
		parser.add_argument(
			'--token',
			type=str,
			help='Token JWT para autenticación',
		)

	def handle(self, *args, **options):
		url = options['url']
		token = options['token']
		
		self.stdout.write(self.style.SUCCESS('\n' + '='*70))
		self.stdout.write(self.style.SUCCESS('🧪 TEST DE CONEXIÓN SOCKET.IO'))
		self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
		
		if not token:
			self.stdout.write(self.style.ERROR('❌ Error: Se requiere un token JWT'))
			self.stdout.write(self.style.WARNING('   Uso: python manage.py test_socketio --token TU_TOKEN_JWT'))
			self.stdout.write(self.style.WARNING('\n   Obtener token:'))
			self.stdout.write(self.style.WARNING('   curl -X POST http://localhost:8000/api/login \\'))
			self.stdout.write(self.style.WARNING('     -H "Content-Type: application/json" \\'))
			self.stdout.write(self.style.WARNING('     -d \'{"email": "tu@email.com", "password": "tu_password"}\''))
			return
		
		# Verificar que el servidor esté corriendo (opcional, solo si requests está disponible)
		if requests:
			self.stdout.write(self.style.WARNING('🔍 Verificando que el servidor esté corriendo...'))
			try:
				response = requests.get(f'{url}/api/health', timeout=3)
				if response.status_code == 200:
					self.stdout.write(self.style.SUCCESS('✅ Servidor está corriendo'))
				else:
					self.stdout.write(self.style.WARNING(f'⚠️  Servidor responde con código: {response.status_code}'))
			except requests.exceptions.ConnectionError:
				self.stdout.write(self.style.ERROR('❌ El servidor NO está corriendo'))
				self.stdout.write(self.style.WARNING('\n💡 Inicia el servidor con:'))
				self.stdout.write(self.style.WARNING('   python manage.py runserver'))
				return
			except Exception as e:
				self.stdout.write(self.style.WARNING(f'⚠️  No se pudo verificar el servidor: {str(e)}'))
		else:
			self.stdout.write(self.style.WARNING('⚠️  No se puede verificar el servidor (requests no instalado)'))
			self.stdout.write(self.style.WARNING('   Asegúrate de que el servidor esté corriendo'))
		
		# Verificar que websocket-client esté instalado
		try:
			import websocket
		except ImportError:
			self.stdout.write(self.style.WARNING('\n⚠️  websocket-client no está instalado'))
			self.stdout.write(self.style.WARNING('   Instalando...'))
			import subprocess
			try:
				subprocess.run(['pip', 'install', 'websocket-client==1.7.0'], check=True, capture_output=True)
				self.stdout.write(self.style.SUCCESS('✅ websocket-client instalado'))
			except Exception as e:
				self.stdout.write(self.style.ERROR(f'❌ Error al instalar websocket-client: {str(e)}'))
				self.stdout.write(self.style.WARNING('   Instala manualmente: pip install websocket-client'))
				return
		
		# Crear cliente Socket.IO
		sio_client = socketio.Client()
		
		# Eventos de conexión
		connected = False
		authenticated = False
		events_received = []
		
		@sio_client.event
		def connect():
			nonlocal connected
			connected = True
			self.stdout.write(self.style.SUCCESS('✅ Conectado al servidor Socket.IO'))
		
		@sio_client.event
		def connected(data):
			nonlocal authenticated
			authenticated = True
			self.stdout.write(self.style.SUCCESS(f'✅ Autenticado: {data.get("user", {}).get("username", "N/A")}'))
		
		@sio_client.event
		def disconnect():
			self.stdout.write(self.style.WARNING('❌ Desconectado del servidor'))
		
		@sio_client.event
		def connect_error(data):
			self.stdout.write(self.style.ERROR(f'❌ Error de conexión: {data}'))
		
		@sio_client.on('new_telemetria')
		def on_telemetria(data):
			events_received.append(('new_telemetria', data))
			self.stdout.write(self.style.SUCCESS('📊 Evento recibido: new_telemetria'))
		
		@sio_client.on('telemetria')
		def on_telemetria_old(data):
			events_received.append(('telemetria', data))
			self.stdout.write(self.style.SUCCESS('📊 Evento recibido: telemetria'))
		
		@sio_client.on('new_alerta')
		def on_alerta(data):
			events_received.append(('new_alerta', data))
			self.stdout.write(self.style.SUCCESS('🚨 Evento recibido: new_alerta'))
		
		@sio_client.on('barrier_event')
		def on_barrier_event(data):
			events_received.append(('barrier_event', data))
			self.stdout.write(self.style.SUCCESS('🚧 Evento recibido: barrier_event'))
		
		@sio_client.on('notification')
		def on_notification(data):
			events_received.append(('notification', data))
			self.stdout.write(self.style.SUCCESS('🔔 Notificación recibida'))
		
		@sio_client.on('pong')
		def on_pong(data):
			events_received.append(('pong', data))
			self.stdout.write(self.style.SUCCESS('🏓 Pong recibido'))
		
		@sio_client.on('subscribed')
		def on_subscribed(data):
			self.stdout.write(self.style.SUCCESS(f'✅ Suscrito a eventos: {data.get("events", [])}'))
		
		@sio_client.on('joined_room')
		def on_joined_room(data):
			self.stdout.write(self.style.SUCCESS(f'✅ Unido a sala: {data.get("room", "N/A")}'))
		
		@sio_client.on('error')
		def on_error(data):
			self.stdout.write(self.style.ERROR(f'❌ Error: {data.get("message", "Error desconocido")}'))
		
		try:
			# Conectar
			self.stdout.write(self.style.WARNING(f'\n🔌 Conectando a {url}...'))
			
			try:
				sio_client.connect(
					url,
					socketio_path='/socket.io',
					transports=['websocket', 'polling'],
					auth={'token': token},
					wait_timeout=15
				)
			except socketio.exceptions.ConnectionError as e:
				self.stdout.write(self.style.ERROR(f'❌ Error de conexión: {str(e)}'))
				self.stdout.write(self.style.WARNING('💡 Verifica que el servidor esté corriendo: python manage.py runserver'))
				return
			except Exception as e:
				self.stdout.write(self.style.ERROR(f'❌ Error inesperado: {str(e)}'))
				return
			
			# Esperar conexión
			time.sleep(3)
			
			if not connected:
				self.stdout.write(self.style.ERROR('❌ No se pudo conectar al servidor'))
				return
			
			if not authenticated:
				self.stdout.write(self.style.ERROR('❌ No se pudo autenticar (token inválido o expirado)'))
				sio_client.disconnect()
				return
			
			# Probar suscripción
			self.stdout.write(self.style.WARNING('\n📡 Suscribiéndose a eventos...'))
			sio_client.emit('subscribe', {'events': ['telemetria', 'alertas', 'barrier_events']})
			time.sleep(1)
			
			# Probar unirse a sala
			self.stdout.write(self.style.WARNING('📡 Uniéndose a sala de notificaciones...'))
			sio_client.emit('join_room', {'room': 'notifications'})
			time.sleep(1)
			
			# Probar ping
			self.stdout.write(self.style.WARNING('📡 Enviando ping...'))
			sio_client.emit('ping')
			time.sleep(1)
			
			# Esperar eventos
			self.stdout.write(self.style.WARNING('\n⏳ Esperando eventos (10 segundos)...'))
			self.stdout.write(self.style.WARNING('   (Puedes crear telemetría/alertas en otra terminal para ver eventos)'))
			time.sleep(10)
			
			# Resumen
			self.stdout.write(self.style.SUCCESS('\n' + '='*70))
			self.stdout.write(self.style.SUCCESS('📊 RESUMEN'))
			self.stdout.write(self.style.SUCCESS('='*70))
			self.stdout.write(f'\n✅ Conexión: {"OK" if connected else "FAIL"}')
			self.stdout.write(f'✅ Autenticación: {"OK" if authenticated else "FAIL"}')
			self.stdout.write(f'✅ Eventos recibidos: {len(events_received)}')
			
			if events_received:
				self.stdout.write('\n📋 Eventos recibidos:')
				for event_name, data in events_received:
					self.stdout.write(f'   • {event_name}')
			
			# Desconectar
			sio_client.disconnect()
			self.stdout.write(self.style.SUCCESS('\n✅ Test completado\n'))
			
		except socketio.exceptions.ConnectionError as e:
			self.stdout.write(self.style.ERROR(f'\n❌ Error de conexión: {str(e)}'))
			self.stdout.write(self.style.WARNING('\n💡 Posibles causas:'))
			self.stdout.write(self.style.WARNING('   1. El servidor no está corriendo'))
			self.stdout.write(self.style.WARNING('   2. La URL es incorrecta'))
			self.stdout.write(self.style.WARNING('   3. El token JWT es inválido o expirado'))
			self.stdout.write(self.style.WARNING('\n   Solución: Inicia el servidor con: python manage.py runserver'))
		except Exception as e:
			self.stdout.write(self.style.ERROR(f'\n❌ Error durante el test: {str(e)}'))
			import traceback
			self.stdout.write(self.style.ERROR(f'\nTraceback:\n{traceback.format_exc()}'))
		finally:
			if sio_client.connected:
				sio_client.disconnect()

