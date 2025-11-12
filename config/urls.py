from django.contrib import admin
from django.urls import path, include, re_path
from django.http import JsonResponse, HttpResponseForbidden
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from django.conf import settings

# Configuración de Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="API de Monitoreo de Cruces Ferroviarios",
        default_version='v1',
        description="API para el sistema de monitoreo de cruces ferroviarios",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@crucesferroviarios.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,  # Permitir acceso al schema, pero protegeremos las vistas manualmente
    permission_classes=(permissions.AllowAny,),
)

# Wrapper para proteger Swagger - requiere autenticación
from functools import wraps
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication

def require_auth(view_func):
    """Decorador que requiere autenticación para acceder a Swagger"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Verificar autenticación usando DRF
        jwt_auth = JWTAuthentication()
        session_auth = SessionAuthentication()
        user = None
        
        # Intentar autenticar con JWT
        try:
            auth_result = jwt_auth.authenticate(request)
            if auth_result:
                user, token = auth_result
        except:
            pass
        
        # Si no hay usuario con JWT, intentar con sesión
        if not user:
            try:
                auth_result = session_auth.authenticate(request)
                if auth_result:
                    user, token = auth_result
            except:
                pass
        
        # Si aún no hay usuario, verificar si hay sesión activa
        if not user and hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user
        
        # Si no hay usuario autenticado, retornar 403
        if not user or not user.is_authenticated:
            return HttpResponseForbidden(
                '<h1>403 Forbidden</h1>'
                '<p>Se requiere autenticación para acceder a la documentación de la API.</p>'
                '<p>Por favor, haz login primero en <a href="/api/login">/api/login</a></p>'
                '<p>O incluye tu token JWT en el header: <code>Authorization: Bearer TU_TOKEN</code></p>'
            )
        
        # Asignar usuario al request
        request.user = user
        
        # Si está autenticado, mostrar Swagger
        return view_func(request, *args, **kwargs)
    return wrapper

# Crear vistas protegidas
protected_swagger_ui = require_auth(schema_view.with_ui('swagger', cache_timeout=0))
protected_redoc_ui = require_auth(schema_view.with_ui('redoc', cache_timeout=0))
protected_schema_json = require_auth(schema_view.without_ui(cache_timeout=0))

def root_view(request):
    """
    Vista raíz de la API. Devuelve información básica sin exponer detalles del sistema.
    """
    response_data = {
        'service': 'API de Monitoreo de Cruces Ferroviarios',
        'version': '1.0.0',
        'endpoints': {
            'api': '/api/',
            'admin': '/admin/'
        },
        'message': 'Esta es una API REST. Accede a /api/ para ver los endpoints disponibles.'
    }
    
    # Solo mostrar Swagger si el usuario está autenticado (seguridad)
    if request.user.is_authenticated:
        response_data['endpoints']['documentation'] = '/swagger/'
    
    return JsonResponse(response_data)

urlpatterns = [
    path('', root_view, name='root'),
    path('admin/', admin.site.urls),
    path('api/', include('apps.api.urls')),
    path('api-auth/', include('rest_framework.urls')),
    
    # URLs de JWT
    path('api/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify', TokenVerifyView.as_view(), name='token_verify'),
    
    # URLs de Swagger - PROTEGIDAS con autenticación
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', protected_schema_json, name='schema-json'),
    re_path(r'^swagger/$', protected_swagger_ui, name='schema-swagger-ui'),
    re_path(r'^redoc/$', protected_redoc_ui, name='schema-redoc'),
]
