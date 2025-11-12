from django.contrib import admin
from django.urls import path, include, re_path
from django.http import JsonResponse
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

def blocked_swagger_view(request, *args, **kwargs):
    """Vista que SIEMPRE retorna 403 para Swagger - Swagger deshabilitado"""
    return JsonResponse(
        {
            'error': '403 Forbidden',
            'detail': 'La documentación de la API está deshabilitada por seguridad.',
            'message': 'Swagger no está disponible.'
        },
        status=403
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
    
    return JsonResponse(response_data)

urlpatterns = [
    path('', root_view, name='root'),
    path('admin/', admin.site.urls),
    path('api/', include('apps.api.urls')),
    path('api-auth/', include('rest_framework.urls')),
    
    # URLs de JWT
    path('api/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify', TokenVerifyView.as_view(), name='token_verify'),
    
    # URLs de Swagger - BLOQUEADAS COMPLETAMENTE
    # Todas las URLs de Swagger retornan 403
    re_path(r'^swagger', blocked_swagger_view, name='swagger-blocked'),
    re_path(r'^redoc', blocked_swagger_view, name='redoc-blocked'),
]
