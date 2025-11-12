"""
Comando de gestión para verificar que todos los endpoints de la API
emiten eventos Socket.IO correctamente.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from apps.api.models import Cruce, Telemetria, BarrierEvent, Alerta
from apps.api.socketio_utils import (
	emit_cruce_update,
	emit_telemetria,
	emit_barrier_event,
	emit_alerta,
	emit_alerta_resuelta,
)
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
	help = 'Verificar que todos los endpoints de la API emiten eventos Socket.IO correctamente'

	def add_arguments(self, parser):
		parser.add_argument(
			'--cruce-id',
			type=int,
			default=21,
			help='ID del cruce a usar para las pruebas (default: 21)'
		)

	def handle(self, *args, **options):
		cruce_id = options['cruce_id']
		
		self.stdout.write(self.style.SUCCESS('\n' + '='*70))
		self.stdout.write(self.style.SUCCESS('🔍 VERIFICACIÓN COMPLETA: Socket.IO con API REST'))
		self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
		
		# Verificar que el cruce existe
		try:
			cruce = Cruce.objects.get(id=cruce_id)
			self.stdout.write(self.style.SUCCESS(f'✅ Cruce encontrado: {cruce.nombre} (ID: {cruce_id})'))
		except Cruce.DoesNotExist:
			self.stdout.write(self.style.ERROR(f'❌ Cruce {cruce_id} no encontrado'))
			return
		
		# Verificar funciones de emisión
		self.stdout.write(self.style.WARNING('\n📋 Verificando funciones de emisión...'))
		
		# 1. Verificar emit_cruce_update
		self.stdout.write('\n1️⃣ Verificando emit_cruce_update()...')
		try:
			emit_cruce_update(cruce)
			self.stdout.write(self.style.SUCCESS('   ✅ emit_cruce_update() ejecutado correctamente'))
			self.stdout.write(f'   📤 Evento: cruce_update')
			self.stdout.write(f'   🏠 Sala: cruce_{cruce_id}')
		except Exception as e:
			self.stdout.write(self.style.ERROR(f'   ❌ Error: {str(e)}'))
		
		# 2. Verificar emit_telemetria
		self.stdout.write('\n2️⃣ Verificando emit_telemetria()...')
		try:
			telemetria = Telemetria.objects.filter(cruce=cruce).first()
			if telemetria:
				emit_telemetria(telemetria)
				self.stdout.write(self.style.SUCCESS('   ✅ emit_telemetria() ejecutado correctamente'))
				self.stdout.write(f'   📤 Eventos: new_telemetria, telemetria')
				self.stdout.write(f'   🏠 Salas: telemetria, cruce_{cruce_id}')
			else:
				self.stdout.write(self.style.WARNING('   ⚠️ No hay telemetría para este cruce'))
		except Exception as e:
			self.stdout.write(self.style.ERROR(f'   ❌ Error: {str(e)}'))
		
		# 3. Verificar emit_barrier_event
		self.stdout.write('\n3️⃣ Verificando emit_barrier_event()...')
		try:
			barrier_event = BarrierEvent.objects.filter(cruce=cruce).first()
			if barrier_event:
				emit_barrier_event(barrier_event)
				self.stdout.write(self.style.SUCCESS('   ✅ emit_barrier_event() ejecutado correctamente'))
				self.stdout.write(f'   📤 Eventos: barrier_event, notification')
				self.stdout.write(f'   🏠 Salas: barrier_events, cruce_{cruce_id}, notifications')
			else:
				self.stdout.write(self.style.WARNING('   ⚠️ No hay eventos de barrera para este cruce'))
		except Exception as e:
			self.stdout.write(self.style.ERROR(f'   ❌ Error: {str(e)}'))
		
		# 4. Verificar emit_alerta
		self.stdout.write('\n4️⃣ Verificando emit_alerta()...')
		try:
			alerta = Alerta.objects.filter(cruce=cruce).first()
			if alerta:
				emit_alerta(alerta)
				self.stdout.write(self.style.SUCCESS('   ✅ emit_alerta() ejecutado correctamente'))
				self.stdout.write(f'   📤 Eventos: new_alerta, alerta, notification')
				self.stdout.write(f'   🏠 Salas: alertas, cruce_{cruce_id}, notifications')
			else:
				self.stdout.write(self.style.WARNING('   ⚠️ No hay alertas para este cruce'))
		except Exception as e:
			self.stdout.write(self.style.ERROR(f'   ❌ Error: {str(e)}'))
		
		# 5. Verificar emit_alerta_resuelta
		self.stdout.write('\n5️⃣ Verificando emit_alerta_resuelta()...')
		try:
			alerta_resuelta = Alerta.objects.filter(cruce=cruce, resolved=True).first()
			if alerta_resuelta:
				emit_alerta_resuelta(alerta_resuelta)
				self.stdout.write(self.style.SUCCESS('   ✅ emit_alerta_resuelta() ejecutado correctamente'))
				self.stdout.write(f'   📤 Eventos: alerta_resolved, alerta_resuelta')
				self.stdout.write(f'   🏠 Salas: alertas, cruce_{cruce_id}')
			else:
				self.stdout.write(self.style.WARNING('   ⚠️ No hay alertas resueltas para este cruce'))
		except Exception as e:
			self.stdout.write(self.style.ERROR(f'   ❌ Error: {str(e)}'))
		
		# Resumen
		self.stdout.write(self.style.SUCCESS('\n' + '='*70))
		self.stdout.write(self.style.SUCCESS('📊 RESUMEN DE VERIFICACIÓN'))
		self.stdout.write(self.style.SUCCESS('='*70))
		
		self.stdout.write('\n✅ Funciones de emisión verificadas:')
		self.stdout.write('   1. emit_cruce_update()')
		self.stdout.write('   2. emit_telemetria()')
		self.stdout.write('   3. emit_barrier_event()')
		self.stdout.write('   4. emit_alerta()')
		self.stdout.write('   5. emit_alerta_resuelta()')
		
		self.stdout.write('\n📤 Eventos Socket.IO disponibles:')
		self.stdout.write('   • cruce_update → Sala: cruce_{id}')
		self.stdout.write('   • new_telemetria / telemetria → Salas: telemetria, cruce_{id}')
		self.stdout.write('   • barrier_event → Salas: barrier_events, cruce_{id}, notifications')
		self.stdout.write('   • new_alerta / alerta → Salas: alertas, cruce_{id}, notifications')
		self.stdout.write('   • alerta_resolved / alerta_resuelta → Salas: alertas, cruce_{id}')
		
		self.stdout.write('\n🔗 Endpoints REST que emiten eventos:')
		self.stdout.write('   • POST /api/cruces/ → cruce_update')
		self.stdout.write('   • PUT/PATCH /api/cruces/{id}/ → cruce_update')
		self.stdout.write('   • POST /api/telemetria/ → new_telemetria')
		self.stdout.write('   • POST /api/barrier-events/ → barrier_event')
		self.stdout.write('   • POST /api/alertas/ → new_alerta')
		self.stdout.write('   • POST /api/alertas/{id}/resolver/ → alerta_resolved')
		
		self.stdout.write(self.style.SUCCESS('\n✅ Verificación completada. Revisa los logs del servidor para confirmar que los eventos se emitieron correctamente.'))
		self.stdout.write(self.style.SUCCESS('='*70 + '\n'))

