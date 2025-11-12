"""
Comando para verificar el estado de las salas Socket.IO en tiempo real.
"""
from django.core.management.base import BaseCommand
from apps.api.socketio_app import sio
import asyncio


class Command(BaseCommand):
	help = 'Verificar qué clientes están en las salas Socket.IO'

	def add_arguments(self, parser):
		parser.add_argument(
			'--sala',
			type=str,
			default='cruce_21',
			help='Nombre de la sala a verificar (default: cruce_21)'
		)

	def handle(self, *args, **options):
		sala = options['sala']
		
		self.stdout.write(self.style.SUCCESS('\n' + '='*70))
		self.stdout.write(self.style.SUCCESS('🔍 VERIFICACIÓN DE SALAS SOCKET.IO'))
		self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
		
		async def verificar_sala():
			try:
				# Obtener participantes de la sala
				participants = list(sio.manager.get_participants('/', sala))
				num_clients = len(participants)
				
				self.stdout.write(f"📊 Sala: {sala}")
				self.stdout.write(f"👥 Clientes en sala: {num_clients}")
				
				if num_clients > 0:
					self.stdout.write(self.style.SUCCESS(f"✅ Hay {num_clients} cliente(s) en la sala:"))
					for sid in participants[:10]:  # Mostrar primeros 10
						self.stdout.write(f"   • {sid}")
					if num_clients > 10:
						self.stdout.write(f"   ... y {num_clients - 10} más")
				else:
					self.stdout.write(self.style.WARNING("⚠️ No hay clientes en la sala"))
					self.stdout.write(self.style.WARNING("   Los eventos emitidos a esta sala no llegarán a nadie"))
				
				# Verificar todas las salas activas
				self.stdout.write("\n📋 Todas las salas activas:")
				# Nota: No hay método directo para listar todas las salas en python-socketio
				# Pero podemos verificar salas conocidas
				salas_conocidas = ['telemetria', 'barrier_events', 'alertas', 'notifications', 'cruce_21']
				for sala_conocida in salas_conocidas:
					participants_sala = list(sio.manager.get_participants('/', sala_conocida))
					if participants_sala:
						self.stdout.write(f"   • {sala_conocida}: {len(participants_sala)} cliente(s)")
				
			except Exception as e:
				self.stdout.write(self.style.ERROR(f"❌ Error: {str(e)}"))
				import traceback
				traceback.print_exc()
		
		# Ejecutar verificación
		asyncio.run(verificar_sala())
		
		self.stdout.write(self.style.SUCCESS('\n' + '='*70 + '\n'))

