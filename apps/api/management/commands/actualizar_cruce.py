"""
Comando para actualizar un cruce usando el ORM de Django.
Esto asegura que los signals se ejecuten y se emitan eventos Socket.IO.
"""
from django.core.management.base import BaseCommand
from apps.api.models import Cruce
from django.core.exceptions import ValidationError


class Command(BaseCommand):
	help = 'Actualizar un cruce usando el ORM (dispara signals y eventos Socket.IO)'

	def add_arguments(self, parser):
		parser.add_argument(
			'--cruce-id',
			type=int,
			required=True,
			help='ID del cruce a actualizar'
		)
		parser.add_argument(
			'--nombre',
			type=str,
			help='Nuevo nombre del cruce'
		)
		parser.add_argument(
			'--ubicacion',
			type=str,
			help='Nueva ubicación del cruce'
		)
		parser.add_argument(
			'--estado',
			type=str,
			choices=['ACTIVO', 'INACTIVO', 'MANTENIMIENTO'],
			help='Nuevo estado del cruce'
		)
		parser.add_argument(
			'--lat',
			type=float,
			help='Nueva latitud'
		)
		parser.add_argument(
			'--lng',
			type=float,
			help='Nueva longitud'
		)

	def handle(self, *args, **options):
		cruce_id = options['cruce_id']
		
		try:
			cruce = Cruce.objects.get(id=cruce_id)
		except Cruce.DoesNotExist:
			self.stdout.write(self.style.ERROR(f'❌ Cruce con ID {cruce_id} no existe'))
			return
		
		# Mostrar valores actuales
		self.stdout.write(f'\n📋 Valores actuales del Cruce {cruce_id}:')
		self.stdout.write(f'   Nombre: {cruce.nombre}')
		self.stdout.write(f'   Ubicación: {cruce.ubicacion}')
		self.stdout.write(f'   Estado: {cruce.estado}')
		self.stdout.write(f'   Latitud: {cruce.coordenadas_lat}')
		self.stdout.write(f'   Longitud: {cruce.coordenadas_lng}')
		self.stdout.write('')
		
		# Actualizar campos si se proporcionaron
		cambios = []
		
		if options.get('nombre'):
			cambios.append(f'nombre: "{cruce.nombre}" → "{options["nombre"]}"')
			cruce.nombre = options['nombre']
		
		if options.get('ubicacion'):
			cambios.append(f'ubicacion: "{cruce.ubicacion}" → "{options["ubicacion"]}"')
			cruce.ubicacion = options['ubicacion']
		
		if options.get('estado'):
			cambios.append(f'estado: "{cruce.estado}" → "{options["estado"]}"')
			cruce.estado = options['estado']
		
		if options.get('lat') is not None:
			cambios.append(f'latitud: {cruce.coordenadas_lat} → {options["lat"]}')
			cruce.coordenadas_lat = options['lat']
		
		if options.get('lng') is not None:
			cambios.append(f'longitud: {cruce.coordenadas_lng} → {options["lng"]}')
			cruce.coordenadas_lng = options['lng']
		
		if not cambios:
			self.stdout.write(self.style.WARNING('⚠️  No se proporcionaron campos para actualizar'))
			self.stdout.write('\nUso:')
			self.stdout.write('  python manage.py actualizar_cruce --cruce-id 21 --nombre "Nuevo Nombre"')
			self.stdout.write('  python manage.py actualizar_cruce --cruce-id 21 --estado ACTIVO')
			self.stdout.write('  python manage.py actualizar_cruce --cruce-id 21 --nombre "Nombre" --ubicacion "Ubicación"')
			return
		
		# Mostrar cambios
		self.stdout.write('📝 Cambios a realizar:')
		for cambio in cambios:
			self.stdout.write(f'   • {cambio}')
		self.stdout.write('')
		
		# Guardar usando ORM (esto disparará los signals)
		try:
			self.stdout.write('💾 Guardando cambios (esto disparará signals y eventos Socket.IO)...')
			cruce.save()
			
			self.stdout.write(self.style.SUCCESS('✅ Cruce actualizado exitosamente'))
			self.stdout.write('')
			self.stdout.write('📡 Deberías ver en los logs del servidor:')
			self.stdout.write('   - 📡 Signal post_save recibido')
			self.stdout.write('   - 🚀 Signal detectado')
			self.stdout.write('   - 📤 Emitiendo evento cruce_update')
			self.stdout.write('   - ✅ Evento emitido exitosamente')
			self.stdout.write('')
			self.stdout.write('🎯 El frontend debería recibir el evento automáticamente')
			
		except ValidationError as e:
			self.stdout.write(self.style.ERROR(f'❌ Error de validación: {str(e)}'))
		except Exception as e:
			self.stdout.write(self.style.ERROR(f'❌ Error al guardar: {str(e)}'))

