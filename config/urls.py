from django.contrib import admin
from django.urls import path, include, re_path
from django.http import JsonResponse
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

# Importar URLs de la API para incluirlas en Swagger
from apps.api.urls import urlpatterns as api_urlpatterns

# Configuración de Swagger
schema_view = get_schema_view(
	openapi.Info(
		title="API de Monitoreo de Cruces Ferroviarios",
		default_version='v1',
		description="""
		API REST para el sistema de monitoreo en tiempo real de cruces ferroviarios.
		
		## Autenticación
		Para usar esta API, necesitas autenticarte usando JWT. 
		1. Obtén un token haciendo POST a `/api/login` con tus credenciales
		2. Usa el token en el header: `Authorization: Bearer <tu_token>`
		
		## Endpoints Principales
		- `/api/telemetria/` - Gestión de telemetría
		- `/api/cruces/` - Gestión de cruces ferroviarios
		- `/api/alertas/` - Gestión de alertas
		- `/api/esp32/telemetria/` - Endpoint público para ESP32
		""",
		terms_of_service="https://www.example.com/terms/",
		contact=openapi.Contact(email="contacto@example.com"),
		license=openapi.License(name="BSD License"),
	),
	public=True,
	permission_classes=[permissions.AllowAny],  # Permitir acceso a Swagger sin autenticación
	patterns=[
		path('api/', include('apps.api.urls')),
		path('api/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
		path('api/token/verify', TokenVerifyView.as_view(), name='token_verify'),
	],
)

def root_view(request):
	"""
	Vista raíz de la API. Devuelve información básica sin exponer detalles del sistema.
	"""
	response_data = {
		'service': 'API de Monitoreo de Cruces Ferroviarios',
		'version': '1.0.0',
		'endpoints': {
			'api': '/api/',
			'admin': '/admin/',
			'swagger': '/swagger/',
			'redoc': '/redoc/'
		},
		'message': 'Esta es una API REST. Accede a /api/ para ver los endpoints disponibles.'
	}
	
	return JsonResponse(response_data)

urlpatterns = [
	path('', root_view, name='root'),
	path('admin/', admin.site.urls),
	path('api/', include('apps.api.urls')),
	path('api-auth/', include('rest_framework.urls')),
	
	# URLs de JWT
	path('api/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
	path('api/token/verify', TokenVerifyView.as_view(), name='token_verify'),
	
	# URLs de Swagger - Habilitadas con protección de autenticación
	re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
	path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
	path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
