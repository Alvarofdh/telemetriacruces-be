"""
Middleware de seguridad adicional para proteger el servidor contra ataques externos.

Protecciones implementadas:
- Límite de tamaño de request body
- Timeout de requests largos
- Validación de headers maliciosos
- Protección contra path traversal
- Rate limiting avanzado
- Detección de patrones de ataque
"""
import logging
import time
import re
from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('apps.api.security')


class SecurityHeadersMiddleware(MiddlewareMixin):
	"""
	Middleware para agregar headers de seguridad adicionales
	"""
	def process_response(self, request, response):
		# Solo procesar respuestas que tienen headers modificables
		# Algunas respuestas como redirecciones pueden no tener headers modificables
		if not hasattr(response, 'headers'):
			return response
		
		try:
			# Headers de seguridad adicionales
			response['X-Content-Type-Options'] = 'nosniff'
			response['X-Frame-Options'] = 'DENY'
			response['X-XSS-Protection'] = '1; mode=block'
			response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
			
			# HSTS solo en producción con HTTPS
			if not settings.DEBUG and getattr(settings, 'USE_HTTPS', False):
				response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
			
			# Remover headers que pueden exponer información
			# Usar del en lugar de pop para evitar errores
			if 'Server' in response:
				del response['Server']
			if 'X-Powered-By' in response:
				del response['X-Powered-By']
		except (AttributeError, TypeError, KeyError):
			# Si hay algún error al modificar headers, continuar sin modificar
			# Esto previene errores con tipos de respuesta especiales
			pass
		
		return response


class RequestSizeLimitMiddleware(MiddlewareMixin):
	"""
	Middleware para limitar el tamaño de los requests y prevenir DoS
	"""
	MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB máximo
	MAX_JSON_SIZE = 5 * 1024 * 1024  # 5MB máximo para JSON
	
	def process_request(self, request):
		# Verificar Content-Length
		content_length = request.META.get('CONTENT_LENGTH', 0)
		if content_length:
			try:
				content_length = int(content_length)
				if content_length > self.MAX_REQUEST_SIZE:
					logger.warning(
						f"Request demasiado grande rechazado: {content_length} bytes desde {request.META.get('REMOTE_ADDR')}"
					)
					return JsonResponse({
						'error': 'Request demasiado grande',
						'message': f'El tamaño máximo permitido es {self.MAX_REQUEST_SIZE / 1024 / 1024}MB'
					}, status=413)
			except (ValueError, TypeError):
				pass
		
		# Verificar Content-Type para JSON
		content_type = request.META.get('CONTENT_TYPE', '')
		if 'application/json' in content_type:
			# Para JSON, limitar más estrictamente
			if content_length and content_length > self.MAX_JSON_SIZE:
				logger.warning(
					f"JSON demasiado grande rechazado: {content_length} bytes desde {request.META.get('REMOTE_ADDR')}"
				)
				return JsonResponse({
					'error': 'Payload JSON demasiado grande',
					'message': f'El tamaño máximo permitido para JSON es {self.MAX_JSON_SIZE / 1024 / 1024}MB'
				}, status=413)
		
		return None


class RequestTimeoutMiddleware(MiddlewareMixin):
	"""
	Middleware para detectar y limitar requests que tardan demasiado
	"""
	MAX_REQUEST_TIME = 30  # 30 segundos máximo
	
	def process_request(self, request):
		# Marcar tiempo de inicio
		request._start_time = time.time()
		return None
	
	def process_response(self, request, response):
		if hasattr(request, '_start_time'):
			elapsed = time.time() - request._start_time
			if elapsed > self.MAX_REQUEST_TIME:
				logger.warning(
					f"Request lento detectado: {elapsed:.2f}s en {request.path} desde {request.META.get('REMOTE_ADDR')}"
				)
		
		return response


class MaliciousPatternDetectionMiddleware(MiddlewareMixin):
	"""
	Middleware para detectar patrones maliciosos en requests
	"""
	# Patrones de ataque comunes
	MALICIOUS_PATTERNS = [
		# SQL Injection
		(r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|SCRIPT)\b)", 'SQL_INJECTION'),
		(r"(--|#|/\*|\*/|;|'|'|`|\"|\"|\\|%)", 'SQL_INJECTION'),
		(r"(\b(OR|AND)\s+\d+\s*=\s*\d+)", 'SQL_INJECTION'),
		
		# Path Traversal
		(r"(\.\./|\.\.\\|\.\.%2F|\.\.%5C)", 'PATH_TRAVERSAL'),
		
		# Command Injection
		(r"(\||;|&|`|\$\(|%3B|%7C)", 'COMMAND_INJECTION'),
		
		# XSS
		(r"(<script|javascript:|onerror=|onload=)", 'XSS'),
		
		# LDAP Injection
		(r"(\*|\(|\)|&|\|)", 'LDAP_INJECTION'),
	]
	
	def process_request(self, request):
		# Excluir rutas administrativas internas para evitar falsos positivos
		admin_paths = ['/admin/', '/django-admin/']
		if any(request.path.startswith(path) for path in admin_paths):
			return None
		
		# Verificar URL
		path = request.path
		query_string = request.META.get('QUERY_STRING', '')
		
		# Verificar parámetros GET
		for key, value in request.GET.items():
			if self._check_malicious_pattern(str(value)):
				logger.warning(
					f"Patrón malicioso detectado en GET: {key}={value[:50]} desde {request.META.get('REMOTE_ADDR')}"
				)
				return JsonResponse({
					'error': 'Request inválido',
					'message': 'Se detectó un patrón sospechoso en la solicitud'
				}, status=400)
		
		# Verificar path
		if self._check_malicious_pattern(path):
			logger.warning(
				f"Patrón malicioso detectado en path: {path} desde {request.META.get('REMOTE_ADDR')}"
			)
			return JsonResponse({
				'error': 'Request inválido',
				'message': 'Se detectó un patrón sospechoso en la URL'
			}, status=400)
		
		return None
	
	def _check_malicious_pattern(self, value):
		"""Verificar si un valor contiene patrones maliciosos"""
		if not isinstance(value, str):
			return False
		
		value_upper = value.upper()
		for pattern, attack_type in self.MALICIOUS_PATTERNS:
			if re.search(pattern, value_upper, re.IGNORECASE):
				return True
		return False


class IPWhitelistMiddleware(MiddlewareMixin):
	"""
	Middleware para whitelist de IPs (opcional, para endpoints críticos)
	"""
	def process_request(self, request):
		# Solo aplicar a endpoints específicos si está configurado
		whitelist_enabled = getattr(settings, 'IP_WHITELIST_ENABLED', False)
		whitelist_ips = getattr(settings, 'IP_WHITELIST', [])
		protected_paths = getattr(settings, 'IP_WHITELIST_PATHS', [])
		
		if not whitelist_enabled or not whitelist_ips:
			return None
		
		# Verificar si el path está protegido
		if any(request.path.startswith(path) for path in protected_paths):
			client_ip = self._get_client_ip(request)
			
			if client_ip not in whitelist_ips:
				logger.warning(
					f"Acceso denegado desde IP no autorizada: {client_ip} a {request.path}"
				)
				return JsonResponse({
					'error': 'Acceso denegado',
					'message': 'Tu IP no está autorizada para acceder a este recurso'
				}, status=403)
		
		return None
	
	def _get_client_ip(self, request):
		"""Obtener IP real del cliente"""
		x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
		if x_forwarded_for:
			return x_forwarded_for.split(',')[0].strip()
		return request.META.get('REMOTE_ADDR', 'unknown')


class AdvancedRateLimitMiddleware(MiddlewareMixin):
	"""
	Middleware para rate limiting avanzado por endpoint y IP
	"""
	def process_request(self, request):
		# Obtener IP del cliente
		client_ip = self._get_client_ip(request)
		
		# Obtener límites desde settings
		global_limit = getattr(settings, 'RATE_LIMIT_GLOBAL_PER_HOUR', 1000)
		endpoint_limit = getattr(settings, 'RATE_LIMIT_ENDPOINT_PER_MINUTE', 100)
		
		# Rate limiting por IP global
		global_key = f'ratelimit_global_{client_ip}'
		global_count = cache.get(global_key, 0)
		
		# Límite global: configurable desde settings
		if global_count >= global_limit:
			logger.warning(f"Rate limit global excedido para IP: {client_ip} ({global_count}/{global_limit})")
			return JsonResponse({
				'error': 'Demasiadas solicitudes',
				'message': 'Has excedido el límite de solicitudes. Intenta más tarde.',
				'retry_after': 3600
			}, status=429)
		
		# Incrementar contador global
		cache.set(global_key, global_count + 1, timeout=3600)
		
		# Rate limiting específico por endpoint (solo para API)
		if request.path.startswith('/api/'):
			endpoint_key = f'ratelimit_endpoint_{client_ip}_{request.path}'
			endpoint_count = cache.get(endpoint_key, 0)
			
			# Límite por endpoint: configurable desde settings
			if endpoint_count >= endpoint_limit:
				logger.warning(f"Rate limit de endpoint excedido: {request.path} desde IP: {client_ip} ({endpoint_count}/{endpoint_limit})")
				return JsonResponse({
					'error': 'Demasiadas solicitudes a este endpoint',
					'message': 'Has excedido el límite para este endpoint. Intenta más tarde.',
					'retry_after': 60
				}, status=429)
			
			# Incrementar contador de endpoint
			cache.set(endpoint_key, endpoint_count + 1, timeout=60)
		
		return None
	
	def _get_client_ip(self, request):
		"""Obtener IP real del cliente"""
		x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
		if x_forwarded_for:
			return x_forwarded_for.split(',')[0].strip()
		return request.META.get('REMOTE_ADDR', 'unknown')


class UserAgentValidationMiddleware(MiddlewareMixin):
	"""
	Middleware para validar y bloquear User-Agents maliciosos
	"""
	BLOCKED_USER_AGENTS = [
		'sqlmap',
		'nmap',
		'nikto',
		'w3af',
		'havij',
		'acunetix',
		'nessus',
		'openvas',
		'burp',
		'zap',
		'scanner',
		'bot',
		'crawler',
		'spider',
	]
	
	def process_request(self, request):
		user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
		
		# Verificar si el User-Agent está bloqueado
		for blocked in self.BLOCKED_USER_AGENTS:
			if blocked in user_agent:
				logger.warning(
					f"User-Agent bloqueado detectado: {user_agent} desde {request.META.get('REMOTE_ADDR')}"
				)
				return JsonResponse({
					'error': 'Acceso denegado',
					'message': 'User-Agent no permitido'
				}, status=403)
		
		return None

