from pathlib import Path
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
# Por defecto False en producción, solo True si se especifica explícitamente
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# SECURITY WARNING: keep the secret key used in production secret!
# En producción, SECRET_KEY DEBE estar en variables de entorno
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
	if DEBUG:
		# Solo permitir clave insegura en desarrollo
		SECRET_KEY = 'django-insecure-%v)-r%vm$c$6$=1i8e&7dca0m5w3y&jqv!a!7j9!1fa4k*j@ju'
		import warnings
		warnings.warn('SECRET_KEY no configurada. Usando clave insegura solo para desarrollo.')
	else:
		raise ValueError('SECRET_KEY debe estar configurada en variables de entorno para producción')

ALLOWED_HOSTS = ['viametrica-be.psicosiodev.me','fe.psicosiodev.me','localhost','127.0.0.1','admin.socket.io']

# Configuración de URLs
APPEND_SLASH = True  # Agrega automáticamente / al final de URLs


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    # 'drf_yasg',  # Deshabilitado por seguridad
    'corsheaders',
    'apps.api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    # Middleware de seguridad personalizado (orden importante)
    'apps.api.middleware_security.RequestSizeLimitMiddleware',  # Limitar tamaño de requests
    'apps.api.middleware_security.MaliciousPatternDetectionMiddleware',  # Detectar patrones maliciosos
    'apps.api.middleware_security.UserAgentValidationMiddleware',  # Validar User-Agents
    'apps.api.middleware_security.AdvancedRateLimitMiddleware',  # Rate limiting avanzado
    'apps.api.middleware_security.RequestTimeoutMiddleware',  # Detectar requests lentos
    'apps.api.middleware_security.IPWhitelistMiddleware',  # Whitelist de IPs (opcional)
    'apps.api.middleware_security.SecurityHeadersMiddleware',  # Headers de seguridad
    'whitenoise.middleware.WhiteNoiseMiddleware',  
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'config.middleware.SwaggerProtectionMiddleware',  # Middleware para proteger Swagger
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', ''),
        'USER': os.getenv('DB_USER', ''),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', ''),
        'PORT': os.getenv('DB_PORT', ''),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {
            'user_attributes': ('username', 'email', 'first_name', 'last_name'),
            'max_similarity': 0.7,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,  # Aumentado de 8 a 12 para mayor seguridad
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'es-es'

TIME_ZONE = 'America/Santiago'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # Cambiar de 'static' a 'staticfiles'

# WhiteNoise configuration
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        # BasicAuthentication removido por seguridad - no usar en producción
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ] + (['rest_framework.renderers.BrowsableAPIRenderer'] if DEBUG else []),
    # Throttling para rate limiting
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',  # 100 requests por hora para usuarios anónimos
        'user': '1000/hour',  # 1000 requests por hora para usuarios autenticados
        'login': '5/minute',  # 5 intentos de login por minuto
        'register': '3/hour',  # 3 registros por hora
    }
}

# JWT Settings
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',

    'JTI_CLAIM': 'jti',
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
    "https://viametrica-be.psicosiodev.me",
    "https://fe.psicosiodev.me",
    "https://admin.socket.io",
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# CSRF Configuration - Necesario para el admin de Django
CSRF_TRUSTED_ORIGINS = [
    "https://viametrica-be.psicosiodev.me",
    "https://fe.psicosiodev.me",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://admin.socket.io",
]

# Configuración de cookies para funcionar correctamente con HTTPS/HTTP
# En producción (DEBUG=False) usar True, en desarrollo (DEBUG=True) usar False
# Se puede sobrescribir con USE_HTTPS en variables de entorno
USE_HTTPS = os.getenv('USE_HTTPS', str(not DEBUG)).lower() == 'true'
SESSION_COOKIE_SECURE = USE_HTTPS  # Solo enviar cookies por HTTPS en producción
CSRF_COOKIE_SECURE = USE_HTTPS  # Solo enviar cookies CSRF por HTTPS en producción
SESSION_COOKIE_SAMESITE = 'Lax'  # Permitir cookies en requests del mismo sitio
CSRF_COOKIE_SAMESITE = 'Lax'  # Permitir cookies CSRF en requests del mismo sitio
SESSION_COOKIE_HTTPONLY = True  # Prevenir acceso JavaScript a cookies de sesión
CSRF_COOKIE_HTTPONLY = False  # CSRF cookie necesita ser accesible por JavaScript
SESSION_COOKIE_AGE = 86400  # 24 horas en segundos
SESSION_SAVE_EVERY_REQUEST = True  # Renovar sesión en cada request
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Expirar sesión al cerrar navegador

# Configuración específica para ESP32
# En producción, ESP32_TOKEN DEBE estar en variables de entorno
ESP32_TOKEN = os.getenv('ESP32_TOKEN')
if not ESP32_TOKEN:
	if DEBUG:
		ESP32_TOKEN = 'esp32_default_token_123'
		import warnings
		warnings.warn('ESP32_TOKEN no configurada. Usando token por defecto solo para desarrollo.')
	else:
		raise ValueError('ESP32_TOKEN debe estar configurada en variables de entorno para producción')

# Configuración de Socket.IO
SOCKETIO_CORS_ALLOWED_ORIGINS = CORS_ALLOWED_ORIGINS
SOCKETIO_CORS_CREDENTIALS = True
SOCKETIO_PING_TIMEOUT = 60
SOCKETIO_PING_INTERVAL = 25
SOCKETIO_MAX_HTTP_BUFFER_SIZE = 1e6  # 1MB
SOCKETIO_ALLOW_UPGRADES = True
SOCKETIO_TRANSPORTS = ['websocket', 'polling']

# Rate limiting para Socket.IO
# En desarrollo: límites más altos para pruebas
# En producción: usar variables de entorno con límites más restrictivos
if DEBUG:
	SOCKETIO_MAX_CONNECTIONS_PER_IP = int(os.getenv('SOCKETIO_MAX_CONNECTIONS_PER_IP', '20'))  # 20 en desarrollo
	SOCKETIO_RATE_LIMIT_WINDOW = int(os.getenv('SOCKETIO_RATE_LIMIT_WINDOW', '60'))  # segundos
	SOCKETIO_MAX_EVENTS_PER_MINUTE = int(os.getenv('SOCKETIO_MAX_EVENTS_PER_MINUTE', '120'))  # 120 en desarrollo
else:
	SOCKETIO_MAX_CONNECTIONS_PER_IP = int(os.getenv('SOCKETIO_MAX_CONNECTIONS_PER_IP', '5'))  # 5 en producción
	SOCKETIO_RATE_LIMIT_WINDOW = int(os.getenv('SOCKETIO_RATE_LIMIT_WINDOW', '60'))  # segundos
	SOCKETIO_MAX_EVENTS_PER_MINUTE = int(os.getenv('SOCKETIO_MAX_EVENTS_PER_MINUTE', '60'))  # 60 en producción

# ============================================
# CONFIGURACIÓN DE EMAIL
# ============================================
EMAIL_ENABLED = os.getenv('EMAIL_ENABLED', 'False').lower() == 'true'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend' if EMAIL_ENABLED else 'django.core.mail.backends.console.EmailBackend'

# Configuración SMTP
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER or 'noreply@viametrica.com')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# ============================================
# CONFIGURACIÓN DE LOGGING
# ============================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/telemetria.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'apps.api': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# ============================================================================
# CONFIGURACIÓN DE SEGURIDAD HTTP HEADERS
# ============================================================================

# Security Headers - Protección contra ataques comunes
SECURE_BROWSER_XSS_FILTER = True  # Habilitar filtro XSS del navegador
SECURE_CONTENT_TYPE_NOSNIFF = True  # Prevenir MIME type sniffing
X_FRAME_OPTIONS = 'DENY'  # Prevenir clickjacking (DENY es más estricto que SAMEORIGIN)
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0  # HSTS solo en producción (1 año)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True if not DEBUG else False
SECURE_HSTS_PRELOAD = True if not DEBUG else False
SECURE_SSL_REDIRECT = False  # Manejar en Nginx/Apache, no en Django
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https') if not DEBUG else None

# Content Security Policy (CSP) - Configuración básica
# Nota: Ajustar según necesidades del frontend
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'") if DEBUG else ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'") if DEBUG else ("'self'",)
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'", "https:")
CSP_CONNECT_SRC = ("'self'",)

# Referrer Policy
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Permissions Policy (anteriormente Feature Policy)
PERMISSIONS_POLICY = {
    'accelerometer': [],
    'ambient-light-sensor': [],
    'autoplay': [],
    'camera': [],
    'display-capture': [],
    'document-domain': [],
    'encrypted-media': [],
    'fullscreen': [],
    'geolocation': [],
    'gyroscope': [],
    'magnetometer': [],
    'microphone': [],
    'midi': [],
    'payment': [],
    'picture-in-picture': [],
    'publickey-credentials-get': [],
    'screen-wake-lock': [],
    'sync-xhr': [],
    'usb': [],
    'web-share': [],
    'xr-spatial-tracking': [],
}

# ============================================================================
# CONFIGURACIÓN DE RATE LIMITING
# ============================================================================

# Rate limiting para endpoints específicos (usando django-ratelimit)
RATELIMIT_ENABLE = not DEBUG  # Deshabilitar en desarrollo para facilitar testing
RATELIMIT_USE_CACHE = 'default'  # Usar cache de Django para rate limiting

# ============================================================================
# CONFIGURACIÓN DE LOGGING DE SEGURIDAD
# ============================================================================

# Agregar handler de seguridad a logging
LOGGING['handlers']['security'] = {
    'level': 'WARNING',
    'class': 'logging.FileHandler',
    'filename': 'logs/security.log',
    'formatter': 'verbose',
}

LOGGING['loggers']['django.security'] = {
    'handlers': ['security', 'console'],
    'level': 'WARNING',
    'propagate': False,
}

LOGGING['loggers']['apps.api.security'] = {
    'handlers': ['security', 'console'],
    'level': 'INFO',
    'propagate': False,
}

# ============================================================================
# CONFIGURACIÓN ADICIONAL DE SEGURIDAD
# ============================================================================

# Prevenir enumeración de usuarios
PREVENT_USER_ENUMERATION = True

# Tiempo de bloqueo después de intentos fallidos de login
LOGIN_FAILURE_LIMIT = 5  # Intentos antes de bloquear
LOGIN_FAILURE_WINDOW = 300  # Ventana de tiempo en segundos (5 minutos)

# Configuración de JWT mejorada
SIMPLE_JWT['ROTATE_REFRESH_TOKENS'] = True  # Rotar tokens en cada refresh
SIMPLE_JWT['BLACKLIST_AFTER_ROTATION'] = True
SIMPLE_JWT['AUTH_TOKEN_CLASSES'] = ('rest_framework_simplejwt.tokens.AccessToken',)
SIMPLE_JWT['TOKEN_OBTAIN_SERIALIZER'] = 'rest_framework_simplejwt.serializers.TokenObtainPairSerializer'

# ============================================================================
# CONFIGURACIÓN DE HARDENING Y PROTECCIÓN CONTRA ATAQUES
# ============================================================================

# Límites de tamaño de request
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB máximo
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB máximo
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000  # Máximo de campos en formulario

# Timeout de requests
REQUEST_TIMEOUT = 30  # 30 segundos máximo

# IP Whitelist (opcional - solo para endpoints críticos)
IP_WHITELIST_ENABLED = os.getenv('IP_WHITELIST_ENABLED', 'False').lower() == 'true'
IP_WHITELIST = os.getenv('IP_WHITELIST', '').split(',') if os.getenv('IP_WHITELIST') else []
IP_WHITELIST_PATHS = ['/api/admin/', '/api/esp32/']  # Paths protegidos por whitelist

# Protección contra enumeración de usuarios
PREVENT_USER_ENUMERATION = True

# Límites de rate limiting global
RATE_LIMIT_GLOBAL_PER_HOUR = int(os.getenv('RATE_LIMIT_GLOBAL_PER_HOUR', '1000'))
RATE_LIMIT_ENDPOINT_PER_MINUTE = int(os.getenv('RATE_LIMIT_ENDPOINT_PER_MINUTE', '100'))

# Protección contra DoS
MAX_REQUESTS_PER_IP_PER_MINUTE = int(os.getenv('MAX_REQUESTS_PER_IP_PER_MINUTE', '60'))