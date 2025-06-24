from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login, logout
from .serializers import LoginSerializer, RegisterSerializer, UserSerializer, TokenSerializer

# Create your views here.

@swagger_auto_schema(
    method='get',
    operation_description="Endpoint raíz de la API que muestra los endpoints disponibles",
    responses={
        200: openapi.Response(
            description="Lista de endpoints disponibles",
            examples={
                "application/json": {
                    "api_root": "/api/",
                    "health_check": "/api/health/",
                    "login": "/api/login/",
                    "swagger": "/swagger/",
                    "admin": "/admin/"
                }
            }
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request, format=None):
    """
    Endpoint raíz de la API de Monitoreo de Cruces Ferroviarios.
    
    Muestra los endpoints principales disponibles en el sistema.
    """
    return Response({
        'api_root': reverse('api:api-root', request=request, format=format),
        'health_check': reverse('api:health-check', request=request, format=format),
        'login': reverse('api:login', request=request, format=format),
        'register': reverse('api:register', request=request, format=format),
        'swagger': '/swagger/',
        'admin': '/admin/',
        'message': 'API de Monitoreo de Cruces Ferroviarios - Backend operativo'
    })


@swagger_auto_schema(
    method='get',
    operation_description="Verificación del estado de salud de la API",
    responses={
        200: openapi.Response(
            description="Estado de salud de la API",
            examples={
                "application/json": {
                    "status": "ok",
                    "message": "API funcionando correctamente",
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            }
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request, format=None):
    """
    Endpoint de verificación de salud de la API.
    
    Permite verificar que la API está funcionando correctamente.
    """
    from django.utils import timezone
    
    return Response({
        'status': 'ok',
        'message': 'API funcionando correctamente',
        'timestamp': timezone.now().isoformat(),
        'service': 'Monitoreo de Cruces Ferroviarios API'
    })


@swagger_auto_schema(
    method='post',
    request_body=LoginSerializer,
    operation_description="Iniciar sesión con email y password para obtener tokens JWT",
    responses={
        200: openapi.Response(
            description="Login exitoso",
            schema=TokenSerializer
        ),
        400: openapi.Response(
            description="Credenciales inválidas",
            examples={
                "application/json": {
                    "error": "Credenciales inválidas"
                }
            }
        )
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Endpoint para iniciar sesión con email.
    
    Recibe email y password, devuelve tokens JWT para autenticación.
    """
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
            'message': 'Login exitoso'
        }, status=status.HTTP_200_OK)
    
    return Response({
        'error': 'Credenciales inválidas',
        'details': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='post',
    operation_description="Cerrar sesión (invalidar token)",
    responses={
        200: openapi.Response(
            description="Logout exitoso",
            examples={
                "application/json": {
                    "message": "Logout exitoso"
                }
            }
        )
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Endpoint para cerrar sesión.
    
    Invalida el token actual del usuario.
    """
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return Response({
            'message': 'Logout exitoso'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': 'Error al hacer logout',
            'details': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='post',
    request_body=RegisterSerializer,
    operation_description="Registrar nuevo usuario",
    responses={
        201: openapi.Response(
            description="Usuario creado exitosamente",
            schema=UserSerializer
        ),
        400: openapi.Response(
            description="Datos inválidos",
            examples={
                "application/json": {
                    "error": "Datos inválidos"
                }
            }
        )
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """
    Endpoint para registrar nuevos usuarios.
    
    Crea un nuevo usuario en el sistema.
    """
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            'message': 'Usuario creado exitosamente',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'error': 'Datos inválidos',
        'details': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='get',
    operation_description="Obtener perfil del usuario autenticado",
    responses={
        200: openapi.Response(
            description="Perfil del usuario",
            schema=UserSerializer
        ),
        401: openapi.Response(
            description="No autenticado",
            examples={
                "application/json": {
                    "detail": "Las credenciales de autenticación no se proveyeron."
                }
            }
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    """
    Endpoint para obtener el perfil del usuario autenticado.
    
    Requiere autenticación con token JWT.
    """
    return Response({
        'user': UserSerializer(request.user).data,
        'message': 'Perfil obtenido exitosamente'
    }, status=status.HTTP_200_OK)
