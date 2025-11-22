"""
Utilidades de seguridad para el sistema de monitoreo de cruces ferroviarios.

Incluye:
- Rate limiting para login
- Logging de eventos de seguridad
- Protección contra timing attacks
- Validaciones de seguridad adicionales
"""
import logging
import time
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger('apps.api.security')


def get_client_ip(request):
	"""Obtener IP real del cliente (considerando proxies)"""
	x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
	if x_forwarded_for:
		ip = x_forwarded_for.split(',')[0].strip()
	else:
		ip = request.META.get('REMOTE_ADDR', 'unknown')
	return ip


def check_login_rate_limit(identifier, is_email=True):
	"""
	Verificar rate limiting para intentos de login.
	
	Args:
		identifier: Email o IP del cliente
		is_email: True si es email, False si es IP
		
	Returns:
		tuple: (allowed: bool, remaining_attempts: int, lockout_time: int)
	"""
	# Obtener límites desde settings
	limit = getattr(settings, 'LOGIN_FAILURE_LIMIT', 5)
	window = getattr(settings, 'LOGIN_FAILURE_WINDOW', 300)
	
	# Crear clave de cache
	if is_email:
		cache_key = f'login_attempts_email_{identifier}'
	else:
		cache_key = f'login_attempts_ip_{identifier}'
	
	# Obtener intentos actuales
	attempts_data = cache.get(cache_key, {'count': 0, 'first_attempt': None})
	
	# Verificar si está bloqueado
	if attempts_data['count'] >= limit:
		# Calcular tiempo restante de bloqueo
		if attempts_data['first_attempt']:
			elapsed = time.time() - attempts_data['first_attempt']
			remaining = window - elapsed
			if remaining > 0:
				logger.warning(
					f"Intento de login bloqueado: {identifier} "
					f"(IP: {get_client_ip if not is_email else 'N/A'})"
				)
				return False, 0, int(remaining)
			else:
				# Resetear contador si la ventana expiró
				attempts_data = {'count': 0, 'first_attempt': None}
	
	# Actualizar contador
	if attempts_data['first_attempt'] is None:
		attempts_data['first_attempt'] = time.time()
	
	attempts_data['count'] += 1
	remaining_attempts = max(0, limit - attempts_data['count'])
	
	# Guardar en cache
	cache.set(cache_key, attempts_data, timeout=window)
	
	return True, remaining_attempts, 0


def reset_login_rate_limit(identifier, is_email=True):
	"""Resetear contador de intentos de login después de login exitoso"""
	if is_email:
		cache_key = f'login_attempts_email_{identifier}'
	else:
		cache_key = f'login_attempts_ip_{identifier}'
	cache.delete(cache_key)


def log_security_event(event_type, message, request=None, user=None, severity='INFO', **kwargs):
	"""
	Registrar evento de seguridad en logs.
	
	Args:
		event_type: Tipo de evento (LOGIN_SUCCESS, LOGIN_FAILURE, etc.)
		message: Mensaje descriptivo
		request: Request object (opcional)
		user: User object (opcional)
		severity: Nivel de severidad (INFO, WARNING, ERROR, CRITICAL)
		**kwargs: Datos adicionales para el log
	"""
	log_data = {
		'event_type': event_type,
		'log_message': message,
		'timestamp': timezone.now().isoformat(),
		'severity': severity,
	}
	
	if request:
		log_data['ip'] = get_client_ip(request)
		log_data['user_agent'] = request.META.get('HTTP_USER_AGENT', 'unknown')
		log_data['path'] = request.path
	
	if user:
		log_data['user_id'] = user.id
		log_data['username'] = user.username
	
	reserved_log_keys = {'message'}
	for reserved_key in reserved_log_keys:
		if reserved_key in kwargs:
			log_data[f'extra_{reserved_key}'] = kwargs.pop(reserved_key)
	
	log_data.update(kwargs)
	
	# Log según severidad
	if severity == 'CRITICAL':
		logger.critical(f"[{event_type}] {message}", extra=log_data)
	elif severity == 'ERROR':
		logger.error(f"[{event_type}] {message}", extra=log_data)
	elif severity == 'WARNING':
		logger.warning(f"[{event_type}] {message}", extra=log_data)
	else:
		logger.info(f"[{event_type}] {message}", extra=log_data)


def prevent_timing_attack():
	"""
	Prevenir timing attacks agregando un delay constante.
	Útil en funciones de autenticación.
	"""
	# Delay mínimo para prevenir timing attacks (100ms)
	time.sleep(0.1)


def validate_input_length(field_name, value, min_length=None, max_length=None):
	"""
	Validar longitud de entrada.
	
	Args:
		field_name: Nombre del campo
		value: Valor a validar
		min_length: Longitud mínima
		max_length: Longitud máxima
		
	Returns:
		tuple: (is_valid: bool, error_message: str)
	"""
	if value is None:
		return False, f"{field_name} no puede ser None"
	
	length = len(str(value))
	
	if min_length and length < min_length:
		return False, f"{field_name} debe tener al menos {min_length} caracteres"
	
	if max_length and length > max_length:
		return False, f"{field_name} no puede tener más de {max_length} caracteres"
	
	return True, None


def sanitize_string(value, max_length=1000):
	"""
	Sanitizar string para prevenir inyección.
	
	Args:
		value: String a sanitizar
		max_length: Longitud máxima permitida
		
	Returns:
		str: String sanitizado
	"""
	if not isinstance(value, str):
		return str(value)
	
	# Limitar longitud
	if len(value) > max_length:
		value = value[:max_length]
	
	# Remover caracteres de control (excepto espacios y saltos de línea)
	import re
	value = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', value)
	
	return value.strip()


def check_sql_injection_patterns(value):
	"""
	Detectar patrones comunes de SQL injection.
	
	Args:
		value: Valor a verificar
		
	Returns:
		bool: True si se detecta patrón sospechoso
	"""
	if not isinstance(value, str):
		return False
	
	# Patrones comunes de SQL injection
	sql_patterns = [
		r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|SCRIPT)\b)",
		r"(--|#|/\*|\*/|;|'|'|`|\"|\"|\\|%)",
		r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
		r"(\b(OR|AND)\s+['\"].*['\"]\s*=\s*['\"].*['\"])",
	]
	
	import re
	value_upper = value.upper()
	
	for pattern in sql_patterns:
		if re.search(pattern, value_upper, re.IGNORECASE):
			return True
	
	return False


def validate_email_format(email):
	"""
	Validar formato de email de forma segura.
	
	Args:
		email: Email a validar
		
	Returns:
		tuple: (is_valid: bool, error_message: str)
	"""
	if not email:
		return False, "Email no puede estar vacío"
	
	# Validación básica de formato
	import re
	email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
	
	if not re.match(email_pattern, email):
		return False, "Formato de email inválido"
	
	# Validar longitud
	if len(email) > 254:  # RFC 5321
		return False, "Email demasiado largo"
	
	return True, None

