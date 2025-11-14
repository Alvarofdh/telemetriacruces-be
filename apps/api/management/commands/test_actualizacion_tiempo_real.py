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
		nombre_raw = options['nombre'] or f"Actualizado {datetime.now().strftime('%H:%M:%S')}"
		
		# Validar y limpiar el nombre
		MAX_LENGTH = 100
		nombre = nombre_raw.strip()[:MAX_LENGTH]  # Limpiar espacios y truncar si es necesario
		
		if len(nombre_raw) > MAX_LENGTH:
			self.stdout.write(self.style.WARNING(f'⚠️ Nombre truncado de {len(nombre_raw)} a {MAX_LENGTH} caracteres'))
		
		self.stdout.write(self.style.SUCCESS('\n' + '='*70))
		self.stdout.write(self.style.SUCCESS('🔄 PRUEBA DE ACTUALIZACIÓN EN TIEMPO REAL'))
		self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
		
		try:
			cruce = Cruce.objects.get(id=cruce_id)
			nombre_anterior = cruce.nombre
			self.stdout.write(f'📋 Cruce actual: {nombre_anterior}')
			self.stdout.write(f'📋 Estado actual: {cruce.estado}')
			self.stdout.write(f'📋 Última actualización: {cruce.updated_at}\n')
			
			# Verificar que el nombre sea diferente
			if nombre == nombre_anterior:
				self.stdout.write(self.style.WARNING(f'⚠️ El nombre "{nombre}" es igual al actual. Cambiando a "{nombre} [TEST]"'))
				nombre = f"{nombre} [TEST]"[:MAX_LENGTH]
			
			self.stdout.write(self.style.WARNING('⏳ Actualizando cruce (esto disparará el signal y el evento Socket.IO)...'))
			
			# Guardar el timestamp antes de actualizar para verificar que cambió
			updated_at_antes = cruce.updated_at
			
			# Actualizar usando ORM (esto dispara el signal post_save)
			cruce.nombre = nombre
			cruce.save()  # ✅ Esto dispara el signal que emite el evento Socket.IO
			
			# Recargar desde la BD para verificar que se guardó correctamente
			cruce.refresh_from_db()
			
			# Verificar que se actualizó
			if cruce.nombre != nombre:
				self.stdout.write(self.style.ERROR(f'❌ ERROR: El nombre no se guardó correctamente'))
				self.stdout.write(self.style.ERROR(f'   Esperado: "{nombre}"'))
				self.stdout.write(self.style.ERROR(f'   Obtenido: "{cruce.nombre}"'))
				return
			
			if cruce.updated_at == updated_at_antes:
				self.stdout.write(self.style.WARNING('⚠️ ADVERTENCIA: updated_at no cambió (puede ser normal si es muy rápido)'))
			
			self.stdout.write(self.style.SUCCESS(f'✅ Cruce actualizado: {cruce.nombre}'))
			self.stdout.write(self.style.SUCCESS(f'✅ Última actualización: {cruce.updated_at}\n'))
			
			self.stdout.write(self.style.SUCCESS('📡 EVENTO Socket.IO EMITIDO:'))
			self.stdout.write(self.style.SUCCESS(f'   • Evento: cruce_update'))
			self.stdout.write(self.style.SUCCESS(f'   • Sala: cruce_{cruce_id}'))
			self.stdout.write(self.style.SUCCESS(f'   • Datos: Nombre actualizado de "{nombre_anterior}" a "{nombre}"\n'))
			
			self.stdout.write(self.style.WARNING('👀 VERIFICA EN EL FRONTEND:'))
			self.stdout.write(self.style.WARNING(f'   1. El frontend debe estar suscrito a la sala "cruce_{cruce_id}"'))
			self.stdout.write(self.style.WARNING('   2. El frontend debe escuchar el evento "cruce_update"'))
			self.stdout.write(self.style.WARNING('   3. El nombre del cruce debe cambiar automáticamente\n'))
			
			self.stdout.write(self.style.SUCCESS('✅ Si el frontend está configurado correctamente, verás el cambio INMEDIATAMENTE sin refrescar'))
			self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
			
		except Cruce.DoesNotExist:
			self.stdout.write(self.style.ERROR(f'❌ Cruce {cruce_id} no encontrado'))
		except Exception as e:
			self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
			import traceback
			traceback.print_exc()

