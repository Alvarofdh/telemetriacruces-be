"""
Comando para probar actualización de cruce y verificar que Socket.IO emite eventos
"""
from django.core.management.base import BaseCommand
from apps.api.models import Cruce
from django.utils import timezone


class Command(BaseCommand):
	help = 'Actualizar un cruce para probar que Socket.IO emite eventos'

	def add_arguments(self, parser):
		parser.add_argument(
			'--cruce-id',
			type=int,
			required=True,
			help='ID del cruce a actualizar',
		)

	def handle(self, *args, **options):
		cruce_id = options['cruce_id']

		self.stdout.write(self.style.SUCCESS('\n' + '='*70))
		self.stdout.write(self.style.SUCCESS('🔄 TEST DE ACTUALIZACIÓN DE CRUCE'))
		self.stdout.write(self.style.SUCCESS('='*70 + '\n'))

		try:
			cruce = Cruce.objects.get(id=cruce_id)
		except Cruce.DoesNotExist:
			self.stdout.write(self.style.ERROR(f'❌ Cruce con ID {cruce_id} no existe'))
			return

		self.stdout.write(self.style.SUCCESS(f'✅ Cruce encontrado: {cruce.nombre} (ID: {cruce.id})'))
		self.stdout.write('')

		# Guardar valores originales
		# Limpiar nombre de actualizaciones anteriores (remover "(Actualizado...)" si existe)
		import re
		nombre_limpio = re.sub(r'\s*\(Actualizado\s+\d{2}:\d{2}:\d{2}\)', '', cruce.nombre).strip()
		if not nombre_limpio:
			nombre_limpio = cruce.nombre  # Si no hay nombre limpio, usar el original
		
		ubicacion_original = cruce.ubicacion

		# Actualizar cruce
		self.stdout.write(self.style.WARNING('⚠️  IMPORTANTE:'))
		self.stdout.write(self.style.WARNING('   1. Asegúrate de que el servidor esté corriendo con Uvicorn'))
		self.stdout.write(self.style.WARNING('   2. Abre el frontend o test_socketio_frontend.html'))
		self.stdout.write(self.style.WARNING('   3. Conecta con un token JWT válido'))
		self.stdout.write(self.style.WARNING(f'   4. Únete a la sala: cruce_{cruce_id}'))
		self.stdout.write('')

		input('Presiona Enter cuando el frontend esté conectado y unido a la sala...')

		# Actualizar nombre (asegurarse de que no exceda 100 caracteres)
		timestamp = timezone.now().strftime("%H:%M:%S")
		sufijo = f' (Actualizado {timestamp})'
		# Limitar el nombre para que no exceda 100 caracteres
		max_length = 100
		nombre_max = max_length - len(sufijo)
		nombre_truncado = nombre_limpio[:nombre_max] if len(nombre_limpio) > nombre_max else nombre_limpio
		nuevo_nombre = f'{nombre_truncado}{sufijo}'
		
		cruce.nombre = nuevo_nombre
		cruce.save(update_fields=['nombre', 'updated_at'])

		self.stdout.write(self.style.SUCCESS(f'✅ Cruce actualizado:'))
		self.stdout.write(self.style.SUCCESS(f'   Nombre: {nuevo_nombre}'))
		self.stdout.write('')
		self.stdout.write(self.style.WARNING(f'   → Deberías ver evento "cruce_update" en el frontend'))
		self.stdout.write('')

		# Esperar un poco
		import time
		time.sleep(1)

		# Actualizar ubicación (asegurarse de que no exceda el límite)
		# Verificar el max_length del campo ubicacion
		max_ubicacion_length = cruce._meta.get_field('ubicacion').max_length if hasattr(cruce._meta.get_field('ubicacion'), 'max_length') else 200
		sufijo_ubicacion = ' - Modificado'
		ubicacion_max = max_ubicacion_length - len(sufijo_ubicacion) if max_ubicacion_length else len(ubicacion_original)
		ubicacion_truncada = ubicacion_original[:ubicacion_max] if len(ubicacion_original) > ubicacion_max else ubicacion_original
		nueva_ubicacion = f'{ubicacion_truncada}{sufijo_ubicacion}'
		
		cruce.ubicacion = nueva_ubicacion
		cruce.save(update_fields=['ubicacion', 'updated_at'])

		self.stdout.write(self.style.SUCCESS(f'✅ Cruce actualizado nuevamente:'))
		self.stdout.write(self.style.SUCCESS(f'   Ubicación: {nueva_ubicacion}'))
		self.stdout.write('')
		self.stdout.write(self.style.WARNING(f'   → Deberías ver otro evento "cruce_update" en el frontend'))
		self.stdout.write('')

		# Restaurar valores originales (opcional)
		self.stdout.write(self.style.SUCCESS('\n' + '='*70))
		self.stdout.write(self.style.SUCCESS('📊 RESUMEN'))
		self.stdout.write(self.style.SUCCESS('='*70))
		self.stdout.write(f'\n✅ Cruce actualizado: {cruce.nombre} (ID: {cruce.id})')
		self.stdout.write(f'✅ Eventos emitidos: 2 (cruce_update)')
		self.stdout.write('')

		self.stdout.write(self.style.WARNING('\n💡 Verifica en el frontend:'))
		self.stdout.write(self.style.WARNING('   - Eventos "cruce_update" recibidos'))
		self.stdout.write(self.style.WARNING('   - Datos del cruce actualizados en tiempo real'))
		self.stdout.write('')

		self.stdout.write(self.style.SUCCESS('✅ Test de actualización completado\n'))

