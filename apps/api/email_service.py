"""
Servicio de envío de emails para notificaciones
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


def enviar_email_alerta(alerta_instance, usuarios=None):
	"""
	Enviar email de alerta a usuarios configurados
	
	Args:
		alerta_instance: Instancia de Alerta
		usuarios: Lista de usuarios a notificar (opcional, si None usa configuración)
	"""
	if not getattr(settings, 'EMAIL_ENABLED', False):
		logger.debug('Emails deshabilitados, no se enviará notificación')
		return False
	
	try:
		# Obtener usuarios a notificar
		if usuarios is None:
			from .models import UserNotificationSettings
			usuarios = UserNotificationSettings.objects.filter(
				enable_email_notifications=True,
				enable_notifications=True
			)
			
			# Filtrar por tipo de alerta
			if alerta_instance.severity == 'CRITICAL':
				usuarios = usuarios.filter(notify_critical_alerts=True)
			elif alerta_instance.severity == 'WARNING':
				usuarios = usuarios.filter(notify_warning_alerts=True)
			else:
				usuarios = usuarios.filter(notify_info_alerts=True)
		
		if not usuarios.exists():
			return False
		
		# Preparar email
		subject = f'🚨 Alerta {alerta_instance.get_severity_display()} - {alerta_instance.cruce.nombre}'
		
		# Crear contenido HTML
		context = {
			'alerta': alerta_instance,
			'cruce': alerta_instance.cruce,
			'severity': alerta_instance.get_severity_display(),
			'type': alerta_instance.get_type_display(),
		}
		
		html_message = f"""
		<!DOCTYPE html>
		<html>
		<head>
			<style>
				body {{ font-family: Arial, sans-serif; }}
				.container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
				.header {{ background-color: {'#dc3545' if alerta_instance.severity == 'CRITICAL' else '#ffc107' if alerta_instance.severity == 'WARNING' else '#17a2b8'}; color: white; padding: 15px; border-radius: 5px; }}
				.content {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-top: 10px; }}
				.detail {{ margin: 10px 0; }}
				.label {{ font-weight: bold; }}
			</style>
		</head>
		<body>
			<div class="container">
				<div class="header">
					<h2>🚨 Alerta {alerta_instance.get_severity_display()}</h2>
				</div>
				<div class="content">
					<div class="detail">
						<span class="label">Cruce:</span> {alerta_instance.cruce.nombre}
					</div>
					<div class="detail">
						<span class="label">Tipo:</span> {alerta_instance.get_type_display()}
					</div>
					<div class="detail">
						<span class="label">Severidad:</span> {alerta_instance.get_severity_display()}
					</div>
					<div class="detail">
						<span class="label">Descripción:</span> {alerta_instance.description}
					</div>
					<div class="detail">
						<span class="label">Fecha:</span> {alerta_instance.created_at.strftime('%Y-%m-%d %H:%M:%S')}
					</div>
				</div>
			</div>
		</body>
		</html>
		"""
		
		plain_message = strip_tags(html_message)
		
		# Enviar a cada usuario
		emails_enviados = 0
		for user_settings in usuarios:
			try:
				user = user_settings.user
				if not user.email:
					continue
				
				email = EmailMultiAlternatives(
					subject=subject,
					body=plain_message,
					from_email=settings.DEFAULT_FROM_EMAIL,
					to=[user.email]
				)
				email.attach_alternative(html_message, "text/html")
				email.send()
				
				emails_enviados += 1
				logger.info(f'Email de alerta enviado a {user.email}')
			except Exception as e:
				logger.error(f'Error al enviar email a {user.email}: {str(e)}')
		
		return emails_enviados > 0
		
	except Exception as e:
		logger.error(f'Error al enviar email de alerta: {str(e)}')
		return False


def enviar_email_mantenimiento(mantenimiento_instance, usuarios=None):
	"""
	Enviar email de mantenimiento programado
	
	Args:
		mantenimiento_instance: Instancia de HistorialMantenimiento
		usuarios: Lista de usuarios a notificar
	"""
	if not getattr(settings, 'EMAIL_ENABLED', False):
		return False
	
	try:
		if usuarios is None:
			from .models import UserNotificationSettings
			usuarios = UserNotificationSettings.objects.filter(
				enable_email_notifications=True,
				enable_notifications=True
			).select_related('user')
		
		if not usuarios.exists():
			return False
		
		subject = f'🔧 Mantenimiento Programado - {mantenimiento_instance.cruce.nombre}'
		
		html_message = f"""
		<!DOCTYPE html>
		<html>
		<head>
			<style>
				body {{ font-family: Arial, sans-serif; }}
				.container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
				.header {{ background-color: #007bff; color: white; padding: 15px; border-radius: 5px; }}
				.content {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-top: 10px; }}
				.detail {{ margin: 10px 0; }}
				.label {{ font-weight: bold; }}
			</style>
		</head>
		<body>
			<div class="container">
				<div class="header">
					<h2>🔧 Mantenimiento Programado</h2>
				</div>
				<div class="content">
					<div class="detail">
						<span class="label">Cruce:</span> {mantenimiento_instance.cruce.nombre}
					</div>
					<div class="detail">
						<span class="label">Tipo:</span> {mantenimiento_instance.get_tipo_mantenimiento_display()}
					</div>
					<div class="detail">
						<span class="label">Prioridad:</span> {mantenimiento_instance.get_prioridad_display()}
					</div>
					<div class="detail">
						<span class="label">Fecha Programada:</span> {mantenimiento_instance.fecha_programada.strftime('%Y-%m-%d %H:%M:%S')}
					</div>
					<div class="detail">
						<span class="label">Descripción:</span> {mantenimiento_instance.descripcion}
					</div>
				</div>
			</div>
		</body>
		</html>
		"""
		
		plain_message = strip_tags(html_message)
		
		emails_enviados = 0
		for user_settings in usuarios:
			try:
				user = user_settings.user
				if not user.email:
					continue
				
				email = EmailMultiAlternatives(
					subject=subject,
					body=plain_message,
					from_email=settings.DEFAULT_FROM_EMAIL,
					to=[user.email]
				)
				email.attach_alternative(html_message, "text/html")
				email.send()
				
				emails_enviados += 1
			except Exception as e:
				logger.error(f'Error al enviar email a {user.email}: {str(e)}')
		
		return emails_enviados > 0
		
	except Exception as e:
		logger.error(f'Error al enviar email de mantenimiento: {str(e)}')
		return False

