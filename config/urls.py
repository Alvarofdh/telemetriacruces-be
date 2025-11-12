from django.contrib import admin
from django.urls import path, include, re_path
from django.http import JsonResponse, HttpResponseForbidden
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from django.conf import settings

# Configuración de Swagger base (sin protección aquí, la haremos en las vistas)
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

# Vistas protegidas para Swagger usando APIView de DRF
class ProtectedSwaggerUIView(APIView):
    """Vista protegida para Swagger UI - requiere autenticación"""
    authentication_classes = [JWTAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    
    def dispatch(self, request, *args, **kwargs):
        """Verificar autenticación ANTES de cualquier renderizado"""
        # Autenticar explícitamente
        for auth_class in self.authentication_classes:
            try:
                auth_instance = auth_class()
                auth_result = auth_instance.authenticate(request)
                if auth_result:
                    user, token = auth_result
                    request.user = user
                    break
            except:
                pass
        
        # Verificar permisos explícitamente
        if not request.user or not request.user.is_authenticated:
            from rest_framework.exceptions import AuthenticationFailed
            from rest_framework.response import Response
            from rest_framework import status
            return Response(
                {
                    'detail': 'Las credenciales de autenticación no se proveyeron.',
                    'message': 'Se requiere autenticación para acceder a la documentación de la API.'
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Si está autenticado, continuar con el método normal
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        # El request de DRF funciona directamente con drf-yasg
        return schema_view.with_ui('swagger', cache_timeout=0)(request, *args, **kwargs)

class ProtectedRedocUIView(APIView):
    """Vista protegida para ReDoc UI - requiere autenticación"""
    authentication_classes = [JWTAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    
    def dispatch(self, request, *args, **kwargs):
        """Verificar autenticación ANTES de cualquier renderizado"""
        for auth_class in self.authentication_classes:
            try:
                auth_instance = auth_class()
                auth_result = auth_instance.authenticate(request)
                if auth_result:
                    user, token = auth_result
                    request.user = user
                    break
            except:
                pass
        
        if not request.user or not request.user.is_authenticated:
            from rest_framework.response import Response
            from rest_framework import status
            return Response(
                {
                    'detail': 'Las credenciales de autenticación no se proveyeron.',
                    'message': 'Se requiere autenticación para acceder a la documentación de la API.'
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        return schema_view.with_ui('redoc', cache_timeout=0)(request, *args, **kwargs)

class ProtectedSchemaView(APIView):
    """Vista protegida para schema JSON/YAML - requiere autenticación"""
    authentication_classes = [JWTAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    
    def dispatch(self, request, *args, **kwargs):
        """Verificar autenticación ANTES de cualquier renderizado"""
        for auth_class in self.authentication_classes:
            try:
                auth_instance = auth_class()
                auth_result = auth_instance.authenticate(request)
                if auth_result:
                    user, token = auth_result
                    request.user = user
                    break
            except:
                pass
        
        if not request.user or not request.user.is_authenticated:
            from rest_framework.response import Response
            from rest_framework import status
            return Response(
                {
                    'detail': 'Las credenciales de autenticación no se proveyeron.',
                    'message': 'Se requiere autenticación para acceder a la documentación de la API.'
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        return schema_view.without_ui(cache_timeout=0)(request, *args, **kwargs)

# Crear instancias de las vistas protegidas
protected_swagger_view = ProtectedSwaggerUIView.as_view()
protected_redoc_view = ProtectedRedocUIView.as_view()
protected_schema_view = ProtectedSchemaView.as_view()

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
    
    # URLs de Swagger - PROTEGIDAS con middleware (el middleware bloquea antes de llegar aquí)
    # Si el middleware permite el acceso, estas vistas se ejecutarán
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', protected_schema_view, name='schema-json'),
    re_path(r'^swagger/$', protected_swagger_view, name='schema-swagger-ui'),
    re_path(r'^redoc/$', protected_redoc_view, name='schema-redoc'),
]
