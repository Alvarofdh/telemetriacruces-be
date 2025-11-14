"""
Utilidades para emitir eventos Socket.IO desde Django.

Este módulo proporciona funciones para emitir eventos en tiempo real
cuando ocurren cambios en el sistema (telemetría, alertas, eventos de barrera).

Nota: Estas funciones deben ejecutarse en un contexto asíncrono.
Para uso desde código síncrono (como signals de Django), usar threading + asyncio.run().
"""
import logging
import asyncio
import threading
from .socketio_app import sio

logger = logging.getLogger(__name__)


def _run_async_in_thread(async_func, *args, **kwargs):
	"""
	Helper común para ejecutar funciones asíncronas en un thread separado.
	
	Esto evita conflictos con el event loop principal cuando se llama desde
	código síncrono (como signals de Django).
	
	Args:
		async_func: Función asíncrona a ejecutar
		*args, **kwargs: Argumentos para la función asíncrona
	"""
	try:
		def run_async():
			asyncio.run(async_func(*args, **kwargs))
		
		thread = threading.Thread(target=run_async, daemon=True)
		thread.start()
	except Exception as e:
		logger.error(f"Error al ejecutar función asíncrona en thread: {str(e)}", exc_info=True)


async def _emit_telemetria_async(telemetria_instance):
	"""Función asíncrona interna para emitir telemetría"""
	try:
		from .serializers import TelemetriaSerializer
		
		serializer = TelemetriaSerializer(telemetria_instance)
		data = serializer.data
		
		event_data = {
			'type': 'telemetria',
			'data': data,
			'timestamp': telemetria_instance.timestamp.isoformat(),
		}
		
		# Emitir a sala general de telemetría
		await sio.emit('new_telemetria', event_data, room='telemetria')
		await sio.emit('telemetria', event_data, room='telemetria')  # Compatibilidad
		
		# Emitir a sala específica del cruce
		cruce_room = f'cruce_{telemetria_instance.cruce.id}'
		await sio.emit('new_telemetria', event_data, room=cruce_room)
		await sio.emit('telemetria', event_data, room=cruce_room)  # Compatibilidad
		
		logger.debug(f"Telemetría emitida: Cruce {telemetria_instance.cruce.id}, ID {telemetria_instance.id}")
		
	except Exception as e:
		logger.error(f"Error al emitir telemetría: {str(e)}")


def emit_telemetria(telemetria_instance):
	"""
	Emitir evento de telemetría nueva.
	
	Args:
		telemetria_instance: Instancia de Telemetria
	"""
	_run_async_in_thread(_emit_telemetria_async, telemetria_instance)


async def _emit_barrier_event_async(barrier_event_instance):
	"""Función asíncrona interna para emitir evento de barrera"""
	try:
		from .serializers import BarrierEventSerializer
		
		serializer = BarrierEventSerializer(barrier_event_instance)
		data = serializer.data
		
		event_data = {
			'type': 'barrier_event',
			'data': data,
			'timestamp': barrier_event_instance.event_time.isoformat(),
		}
		
		# Emitir a sala general de eventos de barrera
		await sio.emit('barrier_event', event_data, room='barrier_events')
		
		# Emitir a sala específica del cruce
		cruce_room = f'cruce_{barrier_event_instance.cruce.id}'
		await sio.emit('barrier_event', event_data, room=cruce_room)
		
		# Emitir notificación a usuarios suscritos
		await sio.emit('notification', {
			'type': 'barrier_event',
			'title': f'Evento de Barrera - {barrier_event_instance.cruce.nombre}',
			'message': f'Barrera {barrier_event_instance.get_state_display()}',
			'data': data,
			'severity': 'info',
			'timestamp': barrier_event_instance.event_time.isoformat(),
		}, room='notifications')
		
		logger.info(f"Evento de barrera emitido: Cruce {barrier_event_instance.cruce.id}, Estado {barrier_event_instance.state}")
		
	except Exception as e:
		logger.error(f"Error al emitir evento de barrera: {str(e)}")


def emit_barrier_event(barrier_event_instance):
	"""
	Emitir evento de cambio de barrera.
	
	Args:
		barrier_event_instance: Instancia de BarrierEvent
	"""
	_run_async_in_thread(_emit_barrier_event_async, barrier_event_instance)


async def _emit_alerta_async(alerta_instance):
	"""Función asíncrona interna para emitir alerta"""
	try:
		from .serializers import AlertaSerializer
		
		serializer = AlertaSerializer(alerta_instance)
		data = serializer.data
		
		event_data = {
			'type': 'alerta',
			'data': data,
			'timestamp': alerta_instance.created_at.isoformat(),
		}
		
		# Emitir a sala general de alertas
		await sio.emit('new_alerta', event_data, room='alertas')
		await sio.emit('alerta', event_data, room='alertas')  # Compatibilidad
		
		# Emitir a sala específica del cruce
		cruce_room = f'cruce_{alerta_instance.cruce.id}'
		await sio.emit('new_alerta', event_data, room=cruce_room)
		await sio.emit('alerta', event_data, room=cruce_room)  # Compatibilidad
		
		# Emitir notificación según severidad
		severity_map = {
			'CRITICAL': 'error',
			'WARNING': 'warning',
			'INFO': 'info',
		}
		
		notification_severity = severity_map.get(alerta_instance.severity, 'info')
		
		# Emitir notificación a usuarios suscritos
		await sio.emit('notification', {
			'type': 'alerta',
			'title': f'Alerta {alerta_instance.get_severity_display()} - {alerta_instance.cruce.nombre}',
			'message': alerta_instance.description,
			'data': data,
			'severity': notification_severity,
			'timestamp': alerta_instance.created_at.isoformat(),
		}, room='notifications')
		
		logger.info(f"Alerta emitida: Cruce {alerta_instance.cruce.id}, Tipo {alerta_instance.type}, Severidad {alerta_instance.severity}")
		
	except Exception as e:
		logger.error(f"Error al emitir alerta: {str(e)}")


def emit_alerta(alerta_instance):
	"""
	Emitir evento de alerta nueva.
	
	Args:
		alerta_instance: Instancia de Alerta
	"""
	_run_async_in_thread(_emit_alerta_async, alerta_instance)


async def _emit_alerta_resuelta_async(alerta_instance):
	"""Función asíncrona interna para emitir alerta resuelta"""
	try:
		from .serializers import AlertaSerializer
		
		serializer = AlertaSerializer(alerta_instance)
		data = serializer.data
		
		event_data = {
			'type': 'alerta_resuelta',
			'data': data,
			'timestamp': alerta_instance.resolved_at.isoformat() if alerta_instance.resolved_at else None,
		}
		
		# Emitir a sala general de alertas
		await sio.emit('alerta_resolved', event_data, room='alertas')
		await sio.emit('alerta_resuelta', event_data, room='alertas')  # Compatibilidad
		
		# Emitir a sala específica del cruce
		cruce_room = f'cruce_{alerta_instance.cruce.id}'
		await sio.emit('alerta_resolved', event_data, room=cruce_room)
		await sio.emit('alerta_resuelta', event_data, room=cruce_room)  # Compatibilidad
		
		logger.info(f"Alerta resuelta emitida: Alerta {alerta_instance.id}, Cruce {alerta_instance.cruce.id}")
		
	except Exception as e:
		logger.error(f"Error al emitir alerta resuelta: {str(e)}")


def emit_alerta_resuelta(alerta_instance):
	"""
	Emitir evento cuando una alerta es resuelta.
	
	Args:
		alerta_instance: Instancia de Alerta
	"""
	_run_async_in_thread(_emit_alerta_resuelta_async, alerta_instance)


async def _emit_cruce_update_async(serialized_data, timestamp, cruce_id):
	"""Función asíncrona interna para emitir actualización de cruce"""
	try:
		logger.info(f"🔄 Iniciando emisión de actualización de cruce: ID {cruce_id}")
		
		# Asegurar que todos los datos datetime se conviertan a strings ISO
		import json
		from datetime import datetime
		
		def json_serial(obj):
			"""JSON serializer para objetos que no son serializables por defecto"""
			if isinstance(obj, datetime):
				return obj.isoformat()
			raise TypeError(f"Type {type(obj)} not serializable")
		
		# Convertir serialized_data a JSON y de vuelta para asegurar serialización correcta
		# Esto convierte todos los datetime a strings ISO
		serialized_json = json.dumps(serialized_data, default=json_serial)
		serialized_data_clean = json.loads(serialized_json)
		
		event_data = {
			'type': 'cruce_update',
			'data': serialized_data_clean,
			'timestamp': timestamp,
		}
		
		# Emitir a sala específica del cruce
		cruce_room = f'cruce_{cruce_id}'
		
		# Verificar cuántos clientes hay en la sala (para diagnóstico)
		try:
			# Obtener todos los SIDs en la sala
			room_sids = list(sio.manager.get_participants('/', cruce_room))
			num_clients = len(room_sids) if room_sids else 0
			logger.info(f"📊 Clientes en sala '{cruce_room}': {num_clients}")
			if num_clients > 0:
				logger.info(f"   SIDs en sala: {room_sids[:5]}...")  # Mostrar primeros 5
			else:
				logger.warning(f"⚠️ No hay clientes en la sala '{cruce_room}' - el evento no llegará a nadie")
		except Exception as e:
			logger.warning(f"⚠️ No se pudo verificar clientes en sala: {str(e)}")
		
		logger.info(f"📤 Emitiendo evento 'cruce_update' a sala '{cruce_room}' para Cruce {cruce_id}")
		
		await sio.emit('cruce_update', event_data, room=cruce_room)
		
		logger.info(f"✅ Cruce actualizado emitido exitosamente: Cruce {cruce_id} (Sala: {cruce_room})")
		
	except Exception as e:
		logger.error(f"❌ Error al emitir actualización de cruce {cruce_id}: {str(e)}", exc_info=True)


def emit_cruce_update(cruce_instance):
	"""
	Emitir evento cuando un cruce es actualizado.
	
	Args:
		cruce_instance: Instancia de Cruce
	"""
	try:
		logger.info(f"🚀 Signal detectado: Cruce {cruce_instance.id} actualizado. Iniciando emisión Socket.IO...")
		
		# Serializar el objeto ANTES de entrar al contexto asíncrono
		# Esto evita problemas con sync_to_async dentro de asyncio.run()
		from .serializers import CruceSerializer
		
		logger.info(f"📦 Serializando datos del cruce {cruce_instance.id}...")
		serializer = CruceSerializer(cruce_instance)
		serialized_data = serializer.data
		timestamp = cruce_instance.updated_at.isoformat()
		
		logger.info(f"✅ Datos serializados correctamente para Cruce {cruce_instance.id}")
		
		_run_async_in_thread(_emit_cruce_update_async, serialized_data, timestamp, cruce_instance.id)
		logger.info(f"✅ Thread de emisión iniciado para Cruce {cruce_instance.id}")
	except Exception as e:
		logger.error(f"❌ Error al ejecutar emisión de actualización de cruce {cruce_instance.id}: {str(e)}", exc_info=True)


async def _emit_dashboard_update_async():
	"""Función asíncrona interna para emitir actualización de dashboard"""
	try:
		from django.utils import timezone
		
		await sio.emit('dashboard_update', {
			'type': 'dashboard_update',
			'message': 'Dashboard actualizado',
			'timestamp': timezone.now().isoformat(),
		}, room='notifications')
		
		logger.debug("Actualización de dashboard emitida")
		
	except Exception as e:
		logger.error(f"Error al emitir actualización de dashboard: {str(e)}")


def emit_dashboard_update():
	"""
	Emitir evento de actualización del dashboard.
	Útil para notificar cambios generales en el sistema.
	"""
	_run_async_in_thread(_emit_dashboard_update_async)

