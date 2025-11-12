"""
Comando de verificación completa de Socket.IO.
Verifica BD, signals, configuración y flujo completo.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.core.exceptions import ImproperlyConfigured
from apps.api.models import Cruce, Telemetria, Alerta, BarrierEvent
from django.db.models.signals import post_save
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
	help = 'Verificación completa de Socket.IO: BD, signals, configuración y flujo completo'

	def add_arguments(self, parser):
		parser.add_argument(
			'--cruce-id',
			type=int,
			default=21,
			help='ID del cruce para pruebas (default: 21)'
		)

	def handle(self, *args, **options):
		cruce_id = options['cruce_id']
		
		self.stdout.write(self.style.SUCCESS('\n╔══════════════════════════════════════════════════════════════════════════════╗'))
		self.stdout.write(self.style.SUCCESS('║          🔍 VERIFICACIÓN COMPLETA DE SOCKET.IO                                ║'))
		self.stdout.write(self.style.SUCCESS('╚══════════════════════════════════════════════════════════════════════════════╝\n'))
		
		errors = []
		warnings = []
		
		# ========================================================================
		# PASO 1: Verificar Base de Datos
		# ========================================================================
		self.stdout.write('=' * 70)
		self.stdout.write(self.style.WARNING('📝 PASO 1: Verificando Base de Datos...'))
		self.stdout.write('=' * 70)
		
		try:
			# Verificar conexión
			with connection.cursor() as cursor:
				cursor.execute("SELECT 1")
				result = cursor.fetchone()
				if result:
					self.stdout.write(self.style.SUCCESS('✅ Conexión a BD: OK'))
				else:
					errors.append('Conexión a BD falló')
					self.stdout.write(self.style.ERROR('❌ Conexión a BD: FALLO'))
		except Exception as e:
			errors.append(f'Error de BD: {str(e)}')
			self.stdout.write(self.style.ERROR(f'❌ Error de BD: {str(e)}'))
		
		# Verificar que el cruce existe
		try:
			cruce = Cruce.objects.get(id=cruce_id)
			self.stdout.write(self.style.SUCCESS(f'✅ Cruce {cruce_id} existe: {cruce.nombre}'))
		except Cruce.DoesNotExist:
			errors.append(f'Cruce {cruce_id} no existe')
			self.stdout.write(self.style.ERROR(f'❌ Cruce {cruce_id} no existe'))
			return
		except Exception as e:
			errors.append(f'Error al obtener cruce: {str(e)}')
			self.stdout.write(self.style.ERROR(f'❌ Error al obtener cruce: {str(e)}'))
			return
		
		# Verificar modelos relacionados
		try:
			telemetria_count = Telemetria.objects.filter(cruce=cruce).count()
			alerta_count = Alerta.objects.filter(cruce=cruce).count()
			barrier_event_count = BarrierEvent.objects.filter(cruce=cruce).count()
			
			self.stdout.write(f'   📊 Telemetrías: {telemetria_count}')
			self.stdout.write(f'   📊 Alertas: {alerta_count}')
			self.stdout.write(f'   📊 Eventos de barrera: {barrier_event_count}')
			
			if telemetria_count == 0:
				warnings.append(f'Cruce {cruce_id} no tiene telemetrías')
		except Exception as e:
			warnings.append(f'Error al contar registros: {str(e)}')
		
		self.stdout.write('')
		
		# ========================================================================
		# PASO 2: Verificar Signals
		# ========================================================================
		self.stdout.write('=' * 70)
		self.stdout.write(self.style.WARNING('📝 PASO 2: Verificando Signals de Django...'))
		self.stdout.write('=' * 70)
		
		# Verificar signals registrados
		receivers_cruce = post_save._live_receivers(Cruce)
		receivers_telemetria = post_save._live_receivers(Telemetria)
		receivers_alerta = post_save._live_receivers(Alerta)
		receivers_barrier = post_save._live_receivers(BarrierEvent)
		
		self.stdout.write(f'   Receivers para Cruce: {len(receivers_cruce)}')
		if len(receivers_cruce) == 0:
			errors.append('No hay receivers registrados para Cruce')
			self.stdout.write(self.style.ERROR('❌ No hay receivers para Cruce'))
		else:
			self.stdout.write(self.style.SUCCESS('✅ Signals de Cruce registrados'))
			for i, receiver in enumerate(receivers_cruce, 1):
				receiver_name = receiver.__name__ if hasattr(receiver, '__name__') else str(receiver)
				self.stdout.write(f'      Receiver {i}: {receiver_name}')
		
		self.stdout.write(f'   Receivers para Telemetria: {len(receivers_telemetria)}')
		if len(receivers_telemetria) == 0:
			warnings.append('No hay receivers para Telemetria')
		else:
			self.stdout.write(self.style.SUCCESS('✅ Signals de Telemetria registrados'))
		
		self.stdout.write(f'   Receivers para Alerta: {len(receivers_alerta)}')
		if len(receivers_alerta) == 0:
			warnings.append('No hay receivers para Alerta')
		else:
			self.stdout.write(self.style.SUCCESS('✅ Signals de Alerta registrados'))
		
		self.stdout.write(f'   Receivers para BarrierEvent: {len(receivers_barrier)}')
		if len(receivers_barrier) == 0:
			warnings.append('No hay receivers para BarrierEvent')
		else:
			self.stdout.write(self.style.SUCCESS('✅ Signals de BarrierEvent registrados'))
		
		self.stdout.write('')
		
		# ========================================================================
		# PASO 3: Verificar Configuración Socket.IO
		# ========================================================================
		self.stdout.write('=' * 70)
		self.stdout.write(self.style.WARNING('📝 PASO 3: Verificando Configuración Socket.IO...'))
		self.stdout.write('=' * 70)
		
		try:
			from apps.api.socketio_app import sio
			self.stdout.write(self.style.SUCCESS('✅ Socket.IO server importado correctamente'))
			
			# Verificar configuración
			from django.conf import settings
			max_connections = getattr(settings, 'SOCKETIO_MAX_CONNECTIONS_PER_IP', 5)
			max_events = getattr(settings, 'SOCKETIO_MAX_EVENTS_PER_MINUTE', 60)
			
			self.stdout.write(f'   Max conexiones por IP: {max_connections}')
			self.stdout.write(f'   Max eventos por minuto: {max_events}')
			self.stdout.write(f'   DEBUG: {settings.DEBUG}')
			
		except ImportError as e:
			errors.append(f'Error al importar Socket.IO: {str(e)}')
			self.stdout.write(self.style.ERROR(f'❌ Error al importar Socket.IO: {str(e)}'))
		except Exception as e:
			errors.append(f'Error en configuración Socket.IO: {str(e)}')
			self.stdout.write(self.style.ERROR(f'❌ Error en configuración: {str(e)}'))
		
		self.stdout.write('')
		
		# ========================================================================
		# PASO 4: Verificar Funciones de Emisión
		# ========================================================================
		self.stdout.write('=' * 70)
		self.stdout.write(self.style.WARNING('📝 PASO 4: Verificando Funciones de Emisión...'))
		self.stdout.write('=' * 70)
		
		try:
			from apps.api.socketio_utils import (
				emit_telemetria,
				emit_barrier_event,
				emit_alerta,
				emit_alerta_resuelta,
				emit_cruce_update,
				emit_dashboard_update,
				_run_async_in_thread,
			)
			
			self.stdout.write(self.style.SUCCESS('✅ Todas las funciones de emisión importadas'))
			self.stdout.write('   ✅ emit_telemetria')
			self.stdout.write('   ✅ emit_barrier_event')
			self.stdout.write('   ✅ emit_alerta')
			self.stdout.write('   ✅ emit_alerta_resuelta')
			self.stdout.write('   ✅ emit_cruce_update')
			self.stdout.write('   ✅ emit_dashboard_update')
			self.stdout.write('   ✅ _run_async_in_thread (helper común)')
			
		except ImportError as e:
			errors.append(f'Error al importar funciones de emisión: {str(e)}')
			self.stdout.write(self.style.ERROR(f'❌ Error al importar funciones: {str(e)}'))
		
		self.stdout.write('')
		
		# ========================================================================
		# PASO 5: Prueba de Actualización de Cruce
		# ========================================================================
		self.stdout.write('=' * 70)
		self.stdout.write(self.style.WARNING('📝 PASO 5: Prueba de Actualización de Cruce...'))
		self.stdout.write('=' * 70)
		
		self.stdout.write('⚠️  IMPORTANTE: Observa los logs del servidor Uvicorn')
		self.stdout.write('   Deberías ver mensajes como:')
		self.stdout.write('   - 📡 Signal post_save recibido')
		self.stdout.write('   - 🚀 Signal detectado')
		self.stdout.write('   - 📦 Serializando datos')
		self.stdout.write('   - ✅ Datos serializados')
		self.stdout.write('   - 📤 Emitiendo evento')
		self.stdout.write('   - ✅ Evento emitido exitosamente')
		self.stdout.write('')
		
		try:
			# Limpiar nombre de actualizaciones previas
			nombre_original = cruce.nombre
			if ' (Actualizado' in nombre_original:
				nombre_original = nombre_original.split(' (Actualizado')[0]
			
			from django.utils import timezone
			nombre_nuevo = f"{nombre_original} (Verificación {timezone.now().strftime('%H:%M:%S')})"
			
			# Asegurar que no exceda max_length
			if len(nombre_nuevo) > 100:
				nombre_nuevo = nombre_nuevo[:97] + '...'
			
			self.stdout.write(f'   Actualizando nombre: {nombre_original} → {nombre_nuevo}')
			cruce.nombre = nombre_nuevo
			cruce.save()
			
			self.stdout.write(self.style.SUCCESS('✅ Cruce actualizado (signal debería haberse ejecutado)'))
			
		except Exception as e:
			errors.append(f'Error al actualizar cruce: {str(e)}')
			self.stdout.write(self.style.ERROR(f'❌ Error al actualizar cruce: {str(e)}'))
		
		self.stdout.write('')
		
		# ========================================================================
		# RESUMEN
		# ========================================================================
		self.stdout.write('=' * 70)
		self.stdout.write(self.style.WARNING('📊 RESUMEN'))
		self.stdout.write('=' * 70)
		
		if errors:
			self.stdout.write(self.style.ERROR(f'\n❌ ERRORES ENCONTRADOS: {len(errors)}'))
			for error in errors:
				self.stdout.write(self.style.ERROR(f'   • {error}'))
		else:
			self.stdout.write(self.style.SUCCESS('\n✅ SIN ERRORES'))
		
		if warnings:
			self.stdout.write(self.style.WARNING(f'\n⚠️  ADVERTENCIAS: {len(warnings)}'))
			for warning in warnings:
				self.stdout.write(self.style.WARNING(f'   • {warning}'))
		
		self.stdout.write('')
		self.stdout.write('=' * 70)
		self.stdout.write(self.style.SUCCESS('📋 CHECKLIST PARA FRONTEND:'))
		self.stdout.write('=' * 70)
		self.stdout.write('')
		self.stdout.write('1. ✅ Servidor corriendo con Uvicorn (no runserver)')
		self.stdout.write('2. ✅ Frontend conectado y autenticado')
		self.stdout.write('3. ✅ Frontend escuchando evento: socket.on("cruce_update", ...)')
		self.stdout.write(f'4. ✅ Frontend unido a sala: socket.emit("join_room", {{ room: "cruce_{cruce_id}" }})')
		self.stdout.write('5. ✅ Verificar logs del servidor para ver emisión')
		self.stdout.write('6. ✅ Verificar consola del navegador para ver recepción')
		self.stdout.write('')
		
		if errors:
			self.stdout.write(self.style.ERROR('╔══════════════════════════════════════════════════════════════════════════════╗'))
			self.stdout.write(self.style.ERROR('║                    ❌ VERIFICACIÓN FALLIDA                                    ║'))
			self.stdout.write(self.style.ERROR('╚══════════════════════════════════════════════════════════════════════════════╝'))
			return
		else:
			self.stdout.write(self.style.SUCCESS('╔══════════════════════════════════════════════════════════════════════════════╗'))
			self.stdout.write(self.style.SUCCESS('║                    ✅ VERIFICACIÓN COMPLETA                                    ║'))
			self.stdout.write(self.style.SUCCESS('╚══════════════════════════════════════════════════════════════════════════════╝'))
			self.stdout.write('')
			self.stdout.write('🎯 Próximos pasos:')
			self.stdout.write('   1. Verificar logs del servidor Uvicorn')
			self.stdout.write('   2. Probar en el frontend con el HTML de prueba')
			self.stdout.write('   3. Verificar que los eventos se reciban correctamente')

