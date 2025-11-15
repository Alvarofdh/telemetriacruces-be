"""
Señales para crear automáticamente el perfil de usuario
y emitir eventos Socket.IO cuando ocurren cambios en el sistema
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, Telemetria, BarrierEvent, Alerta, Cruce
from .socketio_utils import (
	emit_telemetria,
	emit_barrier_event,
	emit_alerta,
	emit_alerta_resuelta,
	emit_cruce_update,
)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
	"""
	Crear automáticamente el perfil de usuario cuando se crea un usuario
	"""
	if created:
		UserProfile.objects.get_or_create(
			user=instance,
			defaults={'role': 'OBSERVER'}  # Rol por defecto
		)


@receiver(post_save, sender=Telemetria)
def telemetria_created(sender, instance, created, **kwargs):
	"""
	Emitir evento Socket.IO cuando se crea nueva telemetría
	"""
	if created:
		try:
			emit_telemetria(instance)
		except Exception as e:
			import logging
			logger = logging.getLogger(__name__)
			logger.error(f"Error al emitir telemetría: {str(e)}")


@receiver(post_save, sender=BarrierEvent)
def barrier_event_created(sender, instance, created, **kwargs):
	"""
	Emitir evento Socket.IO cuando se crea un evento de barrera
	"""
	if created:
		try:
			emit_barrier_event(instance)
		except Exception as e:
			import logging
			logger = logging.getLogger(__name__)
			logger.error(f"Error al emitir evento de barrera: {str(e)}")


@receiver(post_save, sender=Alerta)
def alerta_created_or_updated(sender, instance, created, **kwargs):
	"""
	Emitir evento Socket.IO cuando se crea o resuelve una alerta
	Y enviar email si está configurado
	"""
	import logging
	logger = logging.getLogger(__name__)
	
	if created:
		try:
			emit_alerta(instance)
			
			# Enviar email si es crítica o warning
			if instance.severity in ['CRITICAL', 'WARNING']:
				try:
					from .email_service import enviar_email_alerta
					enviar_email_alerta(instance)
				except Exception as e:
					logger.warning(f"Error al enviar email de alerta: {str(e)}")
		except Exception as e:
			logger.error(f"Error al emitir alerta: {str(e)}")
	else:
		# Si se actualizó y se resolvió
		if instance.resolved and 'resolved' in kwargs.get('update_fields', []):
			try:
				emit_alerta_resuelta(instance)
			except Exception as e:
				logger.error(f"Error al emitir alerta resuelta: {str(e)}")


@receiver(post_save, sender=Cruce)
def cruce_created_or_updated(sender, instance, created, **kwargs):
	"""
	Emitir evento Socket.IO cuando se crea o actualiza un cruce
	"""
	import logging
	logger = logging.getLogger(__name__)
	
	try:
		action = "creado" if created else "actualizado"
		logger.info(f"📡 Signal post_save recibido: Cruce {instance.id} {action} (Nombre: {instance.nombre})")
		
		# Emitir actualización (tanto para creación como actualización)
		emit_cruce_update(instance)
		
		if created:
			logger.info(f"✅ Signal procesado: Cruce {instance.id} creado - evento emitido")
		else:
			logger.info(f"✅ Signal procesado: Cruce {instance.id} actualizado - evento emitido")
	except Exception as e:
		logger.error(f"❌ Error en signal de cruce {instance.id}: {str(e)}", exc_info=True)

