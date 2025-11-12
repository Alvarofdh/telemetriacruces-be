"""
Comando para sincronizar un cruce desde la BD y emitir evento Socket.IO.
Útil cuando se han hecho cambios directos en la BD y quieres notificar al frontend.
"""
from django.core.management.base import BaseCommand
from apps.api.models import Cruce
from apps.api.socketio_utils import emit_cruce_update
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
	help = 'Sincronizar cruce desde BD y emitir evento Socket.IO (útil después de cambios directos en BD)'

	def add_arguments(self, parser):
		parser.add_argument(
			'--cruce-id',
			type=int,
			required=True,
			help='ID del cruce a sincronizar'
		)

	def handle(self, *args, **options):
		cruce_id = options['cruce_id']
		
		try:
			# Recargar desde BD (por si hubo cambios directos)
			cruce = Cruce.objects.get(id=cruce_id)
			
			# Forzar actualización de updated_at para que se vea como cambio reciente
			from django.utils import timezone
			cruce.updated_at = timezone.now()
			cruce.save(update_fields=['updated_at'])
			
			self.stdout.write(self.style.SUCCESS(f'\n✅ Cruce {cruce_id} sincronizado desde BD'))
			self.stdout.write(f'   Nombre: {cruce.nombre}')
			self.stdout.write(f'   Ubicación: {cruce.ubicacion}')
			self.stdout.write(f'   Estado: {cruce.estado}')
			self.stdout.write('')
			
			# Emitir evento manualmente
			self.stdout.write('📤 Emitiendo evento Socket.IO...')
			emit_cruce_update(cruce)
			
			self.stdout.write(self.style.SUCCESS('✅ Evento emitido'))
			self.stdout.write('')
			self.stdout.write('📡 Deberías ver en los logs del servidor:')
			self.stdout.write('   - 🚀 Signal detectado')
			self.stdout.write('   - 📤 Emitiendo evento cruce_update')
			self.stdout.write('   - ✅ Evento emitido exitosamente')
			self.stdout.write('')
			self.stdout.write('🎯 El frontend debería recibir el evento automáticamente')
			
		except Cruce.DoesNotExist:
			self.stdout.write(self.style.ERROR(f'❌ Cruce con ID {cruce_id} no existe'))
		except Exception as e:
			self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
			logger.error(f"Error al sincronizar cruce {cruce_id}: {str(e)}", exc_info=True)

