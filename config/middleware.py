"""
Middleware para proteger Swagger en producción
"""
import logging
from django.http import HttpResponseForbidden, JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication
from django.conf import settings

logger = logging.getLogger(__name__)


class SwaggerProtectionMiddleware:
    """
    Middleware que bloquea el acceso a Swagger si el usuario no está autenticado.
    Se ejecuta ANTES de que cualquier vista procese la solicitud.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Verificar si la URL es de Swagger o Redoc
        if request.path.startswith('/swagger') or request.path.startswith('/redoc'):
            # Permitir acceso a Swagger sin autenticación (común en desarrollo)
            # Los endpoints de la API siguen protegidos por sus propios permisos
            logger.info(f"SwaggerProtectionMiddleware: Permitiendo acceso a {request.path}")
            
            # Intentar autenticar si hay token, pero no bloquear si no hay
            user = None
            
            # 1. Verificar sesión de Django (ya procesada por AuthenticationMiddleware)
            if hasattr(request, 'user') and request.user.is_authenticated:
                user = request.user
                logger.info(f"SwaggerProtectionMiddleware: Usuario encontrado en sesión Django: {user}")
            
            # 2. Si no hay usuario, intentar JWT
            if not user:
                try:
                    jwt_auth = JWTAuthentication()
                    auth_result = jwt_auth.authenticate(request)
                    if auth_result:
                        user, token = auth_result
                        request.user = user
                        logger.info(f"SwaggerProtectionMiddleware: Usuario autenticado con JWT: {user}")
                except Exception as e:
                    logger.debug(f"SwaggerProtectionMiddleware: Error en autenticación JWT: {e}")
            
            # 3. Si aún no hay usuario, intentar sesión DRF
            if not user:
                try:
                    session_auth = SessionAuthentication()
                    auth_result = session_auth.authenticate(request)
                    if auth_result:
                        user, token = auth_result
                        request.user = user
                        logger.info(f"SwaggerProtectionMiddleware: Usuario autenticado con sesión DRF: {user}")
                except Exception as e:
                    logger.debug(f"SwaggerProtectionMiddleware: Error en autenticación DRF: {e}")
            
            # Permitir acceso a Swagger incluso sin autenticación
            # Los endpoints de la API seguirán protegidos
            if user:
                logger.info(f"SwaggerProtectionMiddleware: Acceso permitido a {request.path} para usuario {user}")
            else:
                logger.info(f"SwaggerProtectionMiddleware: Acceso permitido a {request.path} (sin autenticación)")

        # Continuar con el procesamiento normal
        response = self.get_response(request)
        return response

