from django.contrib import admin
from django.urls import path, include, re_path
from django.http import JsonResponse
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

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
    public=True,
    permission_classes=(permissions.AllowAny,),
)

def root_view(request):
    """
    Vista raíz de la API. Devuelve información básica sin exponer detalles del sistema.
    """
    return JsonResponse({
        'service': 'API de Monitoreo de Cruces Ferroviarios',
        'version': '1.0.0',
        'endpoints': {
            'api': '/api/',
            'documentation': '/swagger/',
            'admin': '/admin/'
        },
        'message': 'Esta es una API REST. Accede a /api/ para ver los endpoints disponibles.'
    })

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
