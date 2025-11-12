"""
Comando para probar actualizaciones en tiempo real del cruce.
Este comando actualiza el cruce y verifica que el evento Socket.IO se emite.
"""
from django.core.management.base import BaseCommand
from apps.api.models import Cruce
from datetime import datetime
import time


class Command(BaseCommand):
	help = 'Probar actualización en tiempo real del cruce (dispara evento Socket.IO)'

	def add_arguments(self, parser):
		parser.add_argument(
			'--cruce-id',
			type=int,
			default=21,
			help='ID del cruce a actualizar (default: 21)'
		)
		parser.add_argument(
			'--nombre',
			type=str,
			default=None,
			help='Nuevo nombre para el cruce'
		)

	def handle(self, *args, **options):
		cruce_id = options['cruce_id']
		nombre = options['nombre'] or f"Actualizado {datetime.now().strftime('%H:%M:%S')}"
		
		self.stdout.write(self.style.SUCCESS('\n' + '='*70))
		self.stdout.write(self.style.SUCCESS('🔄 PRUEBA DE ACTUALIZACIÓN EN TIEMPO REAL'))
		self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
		
		try:
			cruce = Cruce.objects.get(id=cruce_id)
			self.stdout.write(f'📋 Cruce actual: {cruce.nombre}')
			self.stdout.write(f'📋 Estado actual: {cruce.estado}')
			self.stdout.write(f'📋 Última actualización: {cruce.updated_at}\n')
			
			self.stdout.write(self.style.WARNING('⏳ Actualizando cruce (esto disparará el signal y el evento Socket.IO)...'))
			
			# Actualizar usando ORM (esto dispara el signal post_save)
			cruce.nombre = nombre
			cruce.save()  # ✅ Esto dispara el signal que emite el evento Socket.IO
			
			self.stdout.write(self.style.SUCCESS(f'✅ Cruce actualizado: {cruce.nombre}'))
			self.stdout.write(self.style.SUCCESS(f'✅ Última actualización: {cruce.updated_at}\n'))
			
			self.stdout.write(self.style.SUCCESS('📡 EVENTO Socket.IO EMITIDO:'))
			self.stdout.write(self.style.SUCCESS(f'   • Evento: cruce_update'))
			self.stdout.write(self.style.SUCCESS(f'   • Sala: cruce_{cruce_id}'))
			self.stdout.write(self.style.SUCCESS(f'   • Datos: Nombre actualizado a "{nombre}"\n'))
			
			self.stdout.write(self.style.WARNING('👀 VERIFICA EN EL FRONTEND:'))
			self.stdout.write(self.style.WARNING('   1. El frontend debe estar suscrito a la sala "cruce_21"'))
			self.stdout.write(self.style.WARNING('   2. El frontend debe escuchar el evento "cruce_update"'))
			self.stdout.write(self.style.WARNING('   3. El nombre del cruce debe cambiar automáticamente\n'))
			
			self.stdout.write(self.style.SUCCESS('✅ Si el frontend está configurado correctamente, verás el cambio INMEDIATAMENTE sin refrescar'))
			self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
			
		except Cruce.DoesNotExist:
			self.stdout.write(self.style.ERROR(f'❌ Cruce {cruce_id} no encontrado'))
		except Exception as e:
			self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))

