from django.contrib import admin
from django.urls import path, include, re_path
from django.http import JsonResponse
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from django.conf import settings

# Configuración de Swagger
# SIEMPRE requiere autenticación para acceder a Swagger (seguridad)
# No importa si DEBUG=True o False, Swagger debe estar protegido
swagger_permission_classes = (permissions.IsAuthenticated,)
swagger_public = False
swagger_authentication_classes = (
    JWTAuthentication,
    SessionAuthentication,
    BasicAuthentication,
)

schema_view = get_schema_view(
    openapi.Info(
        title="API de Monitoreo de Cruces Ferroviarios",
        default_version='v1',
        description="API para el sistema de monitoreo de cruces ferroviarios",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@crucesferroviarios.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=swagger_public,
    permission_classes=swagger_permission_classes,
    authentication_classes=swagger_authentication_classes,
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
    
    # URLs de Swagger
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
