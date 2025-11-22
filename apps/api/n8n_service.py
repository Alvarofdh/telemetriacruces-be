"""
Servicios de integración con n8n para orquestar notificaciones externas.
"""
from __future__ import annotations

import logging
from typing import Optional

import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def enviar_webhook_estado_cruce(*, cruce, estado_anterior: Optional[str] = None) -> bool:
	"""
	Envia un webhook a n8n cuando cambia el estado del cruce.
	
	Args:
		cruce: Instancia de Cruce actualizada.
		estado_anterior: Estado previo antes de la actualización.
	
	Returns:
		bool: True si el webhook se envió correctamente, False en caso contrario.
	"""
	webhook_url = getattr(settings, 'N8N_WEBHOOK_URL', None)
	if not webhook_url:
		logger.debug('N8N_WEBHOOK_URL no configurada. Se omite el envío del webhook.')
		return False
	
	timeout = getattr(settings, 'N8N_WEBHOOK_TIMEOUT', 5)
	verify_ssl = getattr(settings, 'N8N_WEBHOOK_VERIFY_SSL', True)
	
	payload = {
		'cruce_id': cruce.id,
		'nombre': cruce.nombre,
		'estado': cruce.estado,  # Estado actual del cruce
		'ubicacion': cruce.ubicacion,
		'estado_anterior': estado_anterior,
		'nuevo_estado': cruce.estado,
		'responsable': {
			'nombre': cruce.responsable_nombre,
			'telefono': cruce.responsable_telefono,
			'email': cruce.responsable_email,
		},
		'fecha_evento': timezone.now().isoformat(),
	}
	
	logger.info(
		'Enviando webhook n8n a %s con payload: cruce_id=%s, nombre=%s, estado=%s',
		webhook_url,
		cruce.id,
		cruce.nombre,
		cruce.estado,
	)
	
	try:
		response = requests.post(
			webhook_url,
			json=payload,
			timeout=timeout,
			verify=verify_ssl,
			headers={'Content-Type': 'application/json'}
		)
		response.raise_for_status()
		logger.info(
			'✅ Webhook n8n enviado correctamente para el cruce %s "%s" (%s -> %s)',
			cruce.id,
			cruce.nombre,
			estado_anterior,
			cruce.estado,
		)
		return True
	except requests.RequestException as exc:
		logger.error(
			'❌ Error al enviar webhook n8n para el cruce %s "%s": %s. URL: %s',
			cruce.id,
			cruce.nombre,
			str(exc),
			webhook_url,
		)
		if hasattr(exc, 'response') and exc.response is not None:
			logger.error(
				'Respuesta del servidor n8n: %s - %s',
				exc.response.status_code,
				exc.response.text[:200] if exc.response.text else 'Sin contenido',
			)
		return False

