"""
Middleware para proteger Swagger en producción
"""
from django.http import HttpResponseForbidden, JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication
from django.conf import settings


class SwaggerProtectionMiddleware:
    """
    Middleware que bloquea el acceso a Swagger si el usuario no está autenticado.
    Se ejecuta ANTES de que cualquier vista procese la solicitud.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Verificar si la URL es de Swagger
        if request.path.startswith('/swagger') or request.path.startswith('/redoc'):
            # Intentar autenticar con JWT
            jwt_auth = JWTAuthentication()
            user = None
            
            try:
                auth_result = jwt_auth.authenticate(request)
                if auth_result:
                    user, token = auth_result
            except:
                pass
            
            # Si no hay usuario con JWT, intentar con sesión
            if not user:
                session_auth = SessionAuthentication()
                try:
                    auth_result = session_auth.authenticate(request)
                    if auth_result:
                        user, token = auth_result
                except:
                    pass
            
            # Si aún no hay usuario, verificar sesión de Django
            if not user and hasattr(request, 'user') and request.user.is_authenticated:
                user = request.user
            
            # Si no hay usuario autenticado, BLOQUEAR el acceso
            if not user or not user.is_authenticated:
                # Retornar 403 Forbidden inmediatamente
                return JsonResponse(
                    {
                        'error': '403 Forbidden',
                        'detail': 'Se requiere autenticación para acceder a la documentación de la API.',
                        'message': 'Por favor, haz login primero en /api/login o incluye tu token JWT en el header: Authorization: Bearer TU_TOKEN'
                    },
                    status=403
                )
            
            # Si está autenticado, asignar el usuario al request y continuar
            request.user = user

        # Continuar con el procesamiento normal
        response = self.get_response(request)
        return response

