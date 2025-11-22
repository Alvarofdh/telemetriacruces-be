from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
# Swagger habilitado
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.db import transaction, IntegrityError
from django.db.models import Q, ProtectedError
from django.conf import settings
import logging
from .serializers import (
    LoginSerializer, RegisterSerializer, UserSerializer, TokenSerializer,
    TelemetriaSerializer, CruceSerializer, SensorSerializer, 
    BarrierEventSerializer, AlertaSerializer, ESP32TelemetriaSerializer,
    UserNotificationSettingsSerializer,
    MantenimientoPreventivoSerializer, HistorialMantenimientoSerializer,
    MetricasDesempenoSerializer
)
from .user_serializer import UserManagementSerializer, UserUpdateSerializer
from .models import (
    Telemetria, Cruce, Sensor, BarrierEvent, Alerta, UserNotificationSettings, UserProfile,
    MantenimientoPreventivo, HistorialMantenimiento, MetricasDesempeno
)
from .permissions import IsAdmin, IsAdminOrMaintenance, IsObserverOrAbove, CanModifyCruces, CanModifyAlertas
from django.contrib.auth.models import User
from .security import log_security_event

# Configurar logging
logger = logging.getLogger(__name__)

# Create your views here.

@swagger_auto_schema(
    method='get',
    operation_description="Endpoint raíz de la API que muestra los endpoints disponibles",
    responses={
        200: openapi.Response(
            description="Lista de endpoints disponibles",
            examples={
                "application/json": {
                    "api_root": "/api",
                    "health_check": "/api/health",
                    "login": "/api/login",
                    "telemetria": "/api/telemetria",
                    "cruces": "/api/cruces",
                    "alertas": "/api/alertas",
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
        'telemetria': reverse('api:telemetria-list', request=request, format=format),
        'cruces': reverse('api:cruce-list', request=request, format=format),
        'alertas': reverse('api:alerta-list', request=request, format=format),
        'esp32_telemetria': reverse('api:esp32-telemetria', request=request, format=format),
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
    
    URL: GET /api/health
    """
    from django.db import connection
    
    health_status = {
        'status': 'ok',
        'message': 'API funcionando correctamente',
        'timestamp': timezone.now().isoformat(),
        'service': 'Monitoreo de Cruces Ferroviarios API',
        'checks': {}
    }
    
    # Verificar conexión a base de datos
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            health_status['checks']['database'] = {
                'status': 'ok',
                'message': 'Conexión a base de datos exitosa'
            }
    except Exception as e:
        health_status['checks']['database'] = {
            'status': 'error',
            'message': f'Error de conexión: {str(e)}'
        }
        health_status['status'] = 'error'
    
    # Verificar espacio en disco (opcional, requiere psutil)
    try:
        import psutil
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        health_status['checks']['disk'] = {
            'status': 'ok' if disk_percent < 90 else 'warning',
            'message': f'Espacio en disco: {disk_percent:.1f}% usado',
            'free_gb': round(disk.free / (1024**3), 2),
            'total_gb': round(disk.total / (1024**3), 2)
        }
        if disk_percent >= 95:
            health_status['status'] = 'error'
        elif disk_percent >= 90:
            health_status['status'] = 'warning'
    except ImportError:
        health_status['checks']['disk'] = {
            'status': 'unknown',
            'message': 'psutil no instalado'
        }
    except Exception as e:
        health_status['checks']['disk'] = {
            'status': 'unknown',
            'message': f'Error: {str(e)}'
        }
    
    # Verificar memoria (opcional, requiere psutil)
    try:
        import psutil
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        health_status['checks']['memory'] = {
            'status': 'ok' if memory_percent < 90 else 'warning',
            'message': f'Memoria: {memory_percent:.1f}% usada',
            'available_gb': round(memory.available / (1024**3), 2),
            'total_gb': round(memory.total / (1024**3), 2)
        }
        if memory_percent >= 95:
            health_status['status'] = 'error'
        elif memory_percent >= 90:
            health_status['status'] = 'warning'
    except ImportError:
        health_status['checks']['memory'] = {
            'status': 'unknown',
            'message': 'psutil no instalado'
        }
    except Exception as e:
        health_status['checks']['memory'] = {
            'status': 'unknown',
            'message': f'Error: {str(e)}'
        }
    
    # Determinar código HTTP
    http_status = status.HTTP_200_OK
    if health_status['status'] == 'error':
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE
    
    return Response(health_status, status=http_status)


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
    
    URL: POST /api/login
    """
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']  # type: ignore
        refresh = RefreshToken.for_user(user)
        
        # Obtener rol del usuario
        user_data = UserSerializer(user).data
        try:
            profile = user.profile
            user_data['role'] = profile.role
            user_data['role_display'] = profile.get_role_display()
        except:
            user_data['role'] = 'OBSERVER'
            user_data['role_display'] = 'Observador'
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': user_data,
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
    
    URL: POST /api/logout
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
    operation_description="Registrar nuevo usuario con email (username se genera automáticamente)",
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
@permission_classes([IsAuthenticated])
def register_view(request):
    """
    Endpoint para registrar nuevos usuarios.
    
    Solo administradores pueden crear usuarios.
    Crea un nuevo usuario en el sistema usando email.
    El username se genera automáticamente desde el email.
    
    URL: POST /api/register
    
    Campos requeridos:
    - email: Email del usuario
    - password: Contraseña (mínimo 8 caracteres)
    - password_confirm: Confirmación de contraseña
    
    Campos opcionales:
    - first_name: Nombre del usuario
    - last_name: Apellido del usuario
    - role: Rol del usuario (ADMIN, MAINTENANCE, OBSERVER) - Solo admin puede crear otros admin
    """
    # Verificar que el usuario es administrador
    try:
        if not request.user.profile.is_admin():
            return Response({
                'error': 'Solo administradores pueden crear usuarios'
            }, status=status.HTTP_403_FORBIDDEN)
    except:
        return Response({
            'error': 'Usuario no válido'
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = RegisterSerializer(data=request.data, context={'request': request})
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
@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    """
    Endpoint para obtener y actualizar el perfil del usuario autenticado.
    
    Requiere autenticación con token JWT.
    
    URL: GET /api/profile - Obtener perfil
    URL: PUT /api/profile - Actualizar perfil
    """
    if request.method == 'GET':
        return Response({
            'user': UserSerializer(request.user).data,
            'message': 'Perfil obtenido exitosamente'
        }, status=status.HTTP_200_OK)
    
    elif request.method == 'PUT':
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'user': serializer.data,
                'message': 'Perfil actualizado exitosamente'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'error': 'Datos inválidos',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='post',
    operation_description="Cambiar contraseña del usuario autenticado",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'current_password': openapi.Schema(type=openapi.TYPE_STRING, description='Contraseña actual'),
            'new_password': openapi.Schema(type=openapi.TYPE_STRING, description='Nueva contraseña'),
            'confirm_password': openapi.Schema(type=openapi.TYPE_STRING, description='Confirmar nueva contraseña'),
        },
        required=['current_password', 'new_password', 'confirm_password']
    ),
    responses={
        200: openapi.Response(
            description="Contraseña cambiada exitosamente",
            examples={
                "application/json": {
                    "message": "Contraseña cambiada exitosamente"
                }
            }
        ),
        400: openapi.Response(
            description="Datos inválidos",
            examples={
                "application/json": {
                    "error": "Contraseña actual incorrecta"
                }
            }
        )
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    """
    Endpoint para cambiar la contraseña del usuario autenticado.
    
    Requiere autenticación con token JWT.
    
    URL: POST /api/change-password
    
    Campos requeridos:
    - current_password: Contraseña actual
    - new_password: Nueva contraseña (mínimo 8 caracteres)
    - confirm_password: Confirmación de nueva contraseña
    """
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')
    
    # Validar campos requeridos
    if not all([current_password, new_password, confirm_password]):
        return Response({
            'error': 'Todos los campos son requeridos'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validar que las contraseñas coincidan
    if new_password != confirm_password:
        return Response({
            'error': 'Las contraseñas nuevas no coinciden'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validar longitud mínima
    if len(new_password) < 8:
        return Response({
            'error': 'La nueva contraseña debe tener al menos 8 caracteres'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Verificar contraseña actual
    if not request.user.check_password(current_password):
        return Response({
            'error': 'Contraseña actual incorrecta'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Cambiar contraseña
    request.user.set_password(new_password)
    request.user.save()
    
    return Response({
        'message': 'Contraseña cambiada exitosamente'
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='get',
    operation_description="Obtener configuración de notificaciones del usuario",
    responses={
        200: openapi.Response(
            description="Configuración de notificaciones",
            schema=UserNotificationSettingsSerializer
        ),
        404: openapi.Response(
            description="Configuración no encontrada",
            examples={
                "application/json": {
                    "error": "Configuración de notificaciones no encontrada"
                }
            }
        )
    }
)
@swagger_auto_schema(
    method='put',
    request_body=UserNotificationSettingsSerializer,
    operation_description="Actualizar configuración de notificaciones del usuario",
    responses={
        200: openapi.Response(
            description="Configuración actualizada exitosamente",
            schema=UserNotificationSettingsSerializer
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
@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def notification_settings_view(request):
    """
    Endpoint para obtener y actualizar configuración de notificaciones del usuario.
    
    Requiere autenticación con token JWT.
    
    URL: GET /api/notification-settings - Obtener configuración
    URL: PUT /api/notification-settings - Actualizar configuración
    """
    try:
        # Obtener o crear configuración de notificaciones
        settings_obj, created = UserNotificationSettings.objects.get_or_create(
            user=request.user,
            defaults={
                'enable_notifications': True,
                'enable_push_notifications': True,
                'enable_email_notifications': False,
                'notify_critical_alerts': True,
                'notify_warning_alerts': True,
                'notify_info_alerts': False,
                'notify_barrier_events': True,
                'notify_battery_low': True,
                'notify_communication_lost': True,
                'notify_gabinete_open': True,
                'notification_frequency': 'IMMEDIATE'
            }
        )
        
        if request.method == 'GET':
            serializer = UserNotificationSettingsSerializer(settings_obj)
            return Response({
                'settings': serializer.data,
                'message': 'Configuración obtenida exitosamente'
            }, status=status.HTTP_200_OK)
        
        elif request.method == 'PUT':
            serializer = UserNotificationSettingsSerializer(settings_obj, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'settings': serializer.data,
                    'message': 'Configuración actualizada exitosamente'
                }, status=status.HTTP_200_OK)
            
            return Response({
                'error': 'Datos inválidos',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error en configuración de notificaciones: {str(e)}")
        return Response({
            'error': 'Error interno del servidor',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Endpoint público para ESP32 (sin autenticación JWT)

@swagger_auto_schema(
    method='post',
    request_body=ESP32TelemetriaSerializer,
    operation_description="Endpoint público para ESP32 - Enviar datos de telemetría sin autenticación JWT",
    responses={
        201: openapi.Response(
            description="Telemetría recibida exitosamente",
            examples={
                "application/json": {
                    "status": "success",
                    "message": "Datos recibidos correctamente",
                    "telemetria_id": 123,
                    "events_created": 1,
                    "alerts_created": 0
                }
            }
        ),
        400: openapi.Response(
            description="Datos inválidos o token incorrecto",
            examples={
                "application/json": {
                    "status": "error",
                    "message": "Token de ESP32 inválido",
                    "details": ["Token de ESP32 inválido"]
                }
            }
        )
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def esp32_telemetria(request):
    """
    Endpoint público para ESP32 - Enviar datos de telemetría.
    
    Este endpoint NO requiere autenticación JWT, solo un token fijo del ESP32.
    
    URL: POST /api/esp32/telemetria
    
    Campos requeridos:
    - esp32_token: Token de autenticación del ESP32
    - cruce_id: ID del cruce ferroviario
    - barrier_voltage: Voltaje de barrera (0-24V)
    - battery_voltage: Voltaje de batería (10-15V)
    
    Campos opcionales:
    - sensor_1/2/3/4: Sensores adicionales (0-1023)
    - signal_strength: Fuerza de señal WiFi (RSSI)
    - temperature: Temperatura del gabinete
    """
    try:
        # Validar datos con serializer específico para ESP32
        serializer = ESP32TelemetriaSerializer(data=request.data)
        
        if not serializer.is_valid():
            logger.warning(f"ESP32 - Datos inválidos: {serializer.errors}")
            return Response({
                'status': 'error',
                'message': 'Datos inválidos',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener el cruce y validar que existe y está activo
        try:
            cruce = Cruce.objects.get(id=serializer.validated_data['cruce_id'])
            if cruce.estado != 'ACTIVO':
                logger.warning(f"ESP32 - Intento de enviar datos a cruce inactivo: {cruce.id}")
                return Response({
                    'status': 'error',
                    'message': f'El cruce {cruce.nombre} no está activo',
                    'details': {'cruce_id': cruce.id, 'estado': cruce.estado}
                }, status=status.HTTP_400_BAD_REQUEST)
        except Cruce.DoesNotExist:
            logger.error(f"ESP32 - Cruce no encontrado: {serializer.validated_data['cruce_id']}")
            return Response({
                'status': 'error',
                'message': 'Cruce no encontrado',
                'details': {'cruce_id': serializer.validated_data['cruce_id']}
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Crear telemetría
        telemetria_data = {
            'cruce': cruce,
            'barrier_voltage': serializer.validated_data['barrier_voltage'],
            'battery_voltage': serializer.validated_data['battery_voltage'],
            'sensor_1': serializer.validated_data.get('sensor_1'),
            'sensor_2': serializer.validated_data.get('sensor_2'),
            'sensor_3': serializer.validated_data.get('sensor_3'),
            'sensor_4': serializer.validated_data.get('sensor_4'),
            'signal_strength': serializer.validated_data.get('signal_strength'),
            'temperature': serializer.validated_data.get('temperature'),
        }
        
        telemetria = Telemetria.objects.create(**telemetria_data)
        
        # Ejecutar lógica de negocio
        events_created = 0
        alerts_created = 0
        
        # Detectar eventos de barrera
        try:
            detect_barrier_event(telemetria)
            # Contar eventos creados en los últimos segundos
            events_created = BarrierEvent.objects.filter(
                cruce=cruce,
                event_time__gte=timezone.now() - timezone.timedelta(seconds=5)
            ).count()
        except Exception as e:
            logger.error(f"ESP32 - Error en detección de eventos: {str(e)}")
        
        # Verificar alertas
        try:
            check_alerts(telemetria)
            # Contar alertas creadas en los últimos segundos
            alerts_created = Alerta.objects.filter(
                cruce=cruce,
                created_at__gte=timezone.now() - timezone.timedelta(seconds=5)
            ).count()
        except Exception as e:
            logger.error(f"ESP32 - Error en verificación de alertas: {str(e)}")
        
        # Log de éxito
        logger.info(f"ESP32 - Telemetría recibida: Cruce {cruce.nombre}, ID {telemetria.id}, "
                   f"Barrier: {telemetria.barrier_voltage}V, Battery: {telemetria.battery_voltage}V")
        
        return Response({
            'status': 'success',
            'message': 'Datos recibidos correctamente',
            'telemetria_id': telemetria.id,
            'cruce': cruce.nombre,
            'timestamp': telemetria.timestamp.isoformat(),
            'events_created': events_created,
            'alerts_created': alerts_created
        }, status=status.HTTP_201_CREATED)
        
    except Cruce.DoesNotExist:
        logger.error(f"ESP32 - Cruce no encontrado: {request.data.get('cruce_id')}")
        return Response({
            'status': 'error',
            'message': 'Cruce no encontrado o inactivo'
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"ESP32 - Error interno: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Error interno del servidor',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Lógica de negocio para detección de eventos y alertas

def detect_barrier_event(telemetria_instance):
    """
    Detecta cambios de estado de barrera basado en voltaje
    barrier_voltage > 2.0V = DOWN, < 2.0V = UP
    """
    # Determinar estado actual basado en voltaje
    current_status = 'DOWN' if telemetria_instance.barrier_voltage > 2.0 else 'UP'
    
    # Actualizar el estado en la telemetría
    telemetria_instance.barrier_status = current_status
    telemetria_instance.save()
    
    # Obtener el último evento de barrera para este cruce
    last_event = BarrierEvent.objects.filter(
        cruce=telemetria_instance.cruce
    ).order_by('-event_time').first()
    
    # Si no hay eventos previos o el estado cambió, crear nuevo evento
    if not last_event or last_event.state != current_status:
        # Verificar que no haya eventos duplicados en menos de 2 segundos
        recent_events = BarrierEvent.objects.filter(
            cruce=telemetria_instance.cruce,
            event_time__gte=timezone.now() - timezone.timedelta(seconds=2)
        )
        
        if not recent_events.exists():
            BarrierEvent.objects.create(
                telemetria=telemetria_instance,
                cruce=telemetria_instance.cruce,
                state=current_status,
                event_time=telemetria_instance.timestamp,
                voltage_at_event=telemetria_instance.barrier_voltage
            )


def check_alerts(telemetria_instance):
    """
    Verifica y crea alertas automáticas basadas en la telemetría
    """
    # Alerta por batería baja - CRÍTICA
    if telemetria_instance.battery_voltage < 11.0:
        Alerta.objects.get_or_create(
            type='LOW_BATTERY',
            cruce=telemetria_instance.cruce,
            telemetria=telemetria_instance,
            defaults={
                'severity': 'CRITICAL',
                'description': f'Batería baja en cruce {telemetria_instance.cruce.nombre}. '
                              f'Voltaje actual: {telemetria_instance.battery_voltage}V',
                'resolved': False
            }
        )
    
    # Alerta por voltaje crítico del PLC - CRÍTICA
    if telemetria_instance.barrier_voltage < 20.0:
        Alerta.objects.get_or_create(
            type='VOLTAGE_CRITICAL',
            cruce=telemetria_instance.cruce,
            telemetria=telemetria_instance,
            defaults={
                'severity': 'CRITICAL',
                'description': f'Voltaje crítico del PLC en cruce {telemetria_instance.cruce.nombre}. '
                              f'Voltaje actual: {telemetria_instance.barrier_voltage}V',
                'resolved': False
            }
        )
    
    # Alerta por gabinete abierto (sensor_1 > 500) - ADVERTENCIA
    if telemetria_instance.sensor_1 and telemetria_instance.sensor_1 > 500:
        Alerta.objects.get_or_create(
            type='GABINETE_ABIERTO',
            cruce=telemetria_instance.cruce,
            telemetria=telemetria_instance,
            defaults={
                'severity': 'WARNING',
                'description': f'Gabinete abierto en cruce {telemetria_instance.cruce.nombre}',
                'resolved': False
            }
        )
    
    # Alerta por comunicación perdida - CRÍTICA
    # (Se puede implementar si no hay telemetría en X tiempo)
    # if ultima_telemetria > 1 hora:
    #     Alerta.objects.get_or_create(
    #         type='COMMUNICATION_LOST',
    #         cruce=telemetria_instance.cruce,
    #         defaults={
    #             'severity': 'CRITICAL',
    #             'description': f'Comunicación perdida con cruce {telemetria_instance.cruce.nombre}',
    #             'resolved': False
    #         }
    #     )


# ViewSets para los modelos principales

class CruceViewSet(ModelViewSet):
    """ViewSet para gestión de cruces ferroviarios"""
    queryset = Cruce.objects.all()
    serializer_class = CruceSerializer
    permission_classes = [IsAuthenticated, CanModifyCruces]

    def get_queryset(self):
        queryset = Cruce.objects.all().order_by('nombre')  # Ordenar por nombre para evitar advertencia de paginación
        estado = self.request.query_params.get('estado', None)
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset

    def destroy(self, request, *args, **kwargs):
        """
        Eliminar un cruce junto con todas sus dependencias directas
        para evitar errores de integridad referencial en la base de datos.
        """
        instance = self.get_object()
        cruce_id = instance.id
        cruce_nombre = instance.nombre
        
        dependencias = {
            'sensores': instance.sensores.count(),
            'telemetrias': instance.telemetrias.count(),
            'alertas': instance.alertas.count(),
            'eventos_barrera': instance.barrier_events.count(),
            'metricas': instance.metricas.count(),
            'historial_mantenimientos': instance.historial_mantenimientos.count(),
            'reglas_mantenimiento': instance.reglas_mantenimiento.count(),
        }
        
        try:
            with transaction.atomic():
                # Eliminar dependencias en orden para evitar restricciones
                instance.historial_mantenimientos.all().delete()
                instance.metricas.all().delete()
                instance.reglas_mantenimiento.all().delete()
                instance.barrier_events.all().delete()
                instance.alertas.all().delete()
                instance.telemetrias.all().delete()
                instance.sensores.all().delete()
                
                instance.delete()
        except ProtectedError as exc:
            logger.error("No se pudo eliminar el cruce %s por dependencias protegidas: %s", cruce_id, str(exc))
            return Response({
                'error': 'No se puede eliminar el cruce porque tiene dependencias protegidas',
                'detalles': str(exc)
            }, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as exc:
            logger.error("Error de integridad al eliminar cruce %s: %s", cruce_id, str(exc))
            return Response({
                'error': 'Ocurrió un error de integridad al eliminar el cruce',
                'detalles': str(exc)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as exc:
            logger.exception("Error inesperado al eliminar cruce %s", cruce_id)
            return Response({
                'error': 'Ocurrió un error inesperado al eliminar el cruce',
                'detalles': str(exc)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        log_security_event(
            'CRUCE_DELETED',
            f'Cruce eliminado: {cruce_nombre} (ID: {cruce_id})',
            request=request,
            user=request.user,
            severity='WARNING',
            cruce_id=cruce_id,
            extra={'dependencias_eliminadas': dependencias}
        )
        
        return Response({
            'message': f'Cruce {cruce_nombre} eliminado correctamente',
            'cruce_id': cruce_id,
            'dependencias_eliminadas': dependencias
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """
        Obtener detalles completos de un cruce incluyendo telemetría
        """
        instance = self.get_object()
        
        # Optimización: Usar select_related y prefetch_related para evitar N+1 queries
        # Obtener telemetría más reciente
        telemetria_actual = Telemetria.objects.filter(
            cruce=instance
        ).select_related('cruce').order_by('-timestamp').first()
        
        # Obtener últimas 10 telemetrías para historial
        telemetrias_recientes = Telemetria.objects.filter(
            cruce=instance
        ).select_related('cruce').order_by('-timestamp')[:10]
        
        # Obtener alertas activas con prefetch de cruce
        alertas_activas = Alerta.objects.filter(
            cruce=instance,
            resolved=False
        ).select_related('cruce', 'telemetria').order_by('-created_at')
        
        # Obtener últimos eventos de barrera con prefetch de cruce
        eventos_recientes = BarrierEvent.objects.filter(
            cruce=instance
        ).select_related('cruce', 'telemetria').order_by('-event_time')[:5]
        
        # Obtener sensores del cruce con prefetch de cruce
        sensores = Sensor.objects.filter(
            cruce=instance,
            activo=True
        ).select_related('cruce')
        
        # Construir respuesta completa
        cruce_data = {
            'id': instance.id,
            'nombre': instance.nombre,
            'ubicacion': instance.ubicacion,
            'coordenadas_lat': instance.coordenadas_lat,
            'coordenadas_lng': instance.coordenadas_lng,
            'estado': instance.estado,
            'responsable': {
                'nombre': instance.responsable_nombre,
                'telefono': instance.responsable_telefono,
                'email': instance.responsable_email,
                'empresa': instance.responsable_empresa,
                'horario': instance.responsable_horario,
            },
            'created_at': instance.created_at.isoformat(),
            'updated_at': instance.updated_at.isoformat(),
            
            # Telemetría actual
            'telemetria_actual': None,
            
            # Historial de telemetría
            'telemetrias_recientes': [],
            
            # Alertas activas
            'alertas_activas': [],
            
            # Eventos recientes
            'eventos_recientes': [],
            
            # Sensores
            'sensores': [],
            
            # Estadísticas
            'estadisticas': {
                'total_telemetrias': Telemetria.objects.filter(cruce=instance).count(),
                'total_alertas_activas': alertas_activas.count(),
                'total_eventos': BarrierEvent.objects.filter(cruce=instance).count(),
                'ultima_actualizacion': telemetria_actual.timestamp.isoformat() if telemetria_actual else None
            }
        }
        
        # Agregar telemetría actual si existe
        if telemetria_actual:
            cruce_data['telemetria_actual'] = {
                'id': telemetria_actual.id,
                'timestamp': telemetria_actual.timestamp.isoformat(),
                'barrier_voltage': telemetria_actual.barrier_voltage,
                'battery_voltage': telemetria_actual.battery_voltage,
                'barrier_status': telemetria_actual.barrier_status,
                'sensor_1': telemetria_actual.sensor_1,
                'sensor_2': telemetria_actual.sensor_2,
                'sensor_3': telemetria_actual.sensor_3,
                'sensor_4': telemetria_actual.sensor_4,
                'signal_strength': telemetria_actual.signal_strength,
                'temperature': telemetria_actual.temperature
            }
        
        # Agregar telemetrías recientes
        for telemetria in telemetrias_recientes:
            cruce_data['telemetrias_recientes'].append({
                'id': telemetria.id,
                'timestamp': telemetria.timestamp.isoformat(),
                'barrier_voltage': telemetria.barrier_voltage,
                'battery_voltage': telemetria.battery_voltage,
                'barrier_status': telemetria.barrier_status,
                'sensor_1': telemetria.sensor_1,
                'sensor_2': telemetria.sensor_2
            })
        
        # Agregar alertas activas
        for alerta in alertas_activas:
            cruce_data['alertas_activas'].append({
                'id': alerta.id,
                'type': alerta.type,
                'description': alerta.description,
                'created_at': alerta.created_at.isoformat(),
                'resolved': alerta.resolved
            })
        
        # Agregar eventos recientes
        for evento in eventos_recientes:
            cruce_data['eventos_recientes'].append({
                'id': evento.id,
                'state': evento.state,
                'event_time': evento.event_time.isoformat(),
                'voltage_at_event': evento.voltage_at_event
            })
        
        # Agregar sensores
        for sensor in sensores:
            cruce_data['sensores'].append({
                'id': sensor.id,
                'nombre': sensor.nombre,
                'tipo': sensor.tipo,
                'descripcion': sensor.descripcion,
                'activo': sensor.activo
            })
        
        return Response(cruce_data)

    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        """
        Endpoint para dashboard que muestra resumen de todos los cruces
        con su telemetría actual y alertas activas
        """
        # Optimización: Prefetch telemetría y alertas para evitar N+1 queries
        from django.db.models import Prefetch, OuterRef, Subquery
        
        # Subquery para obtener la telemetría más reciente de cada cruce
        latest_telemetria = Telemetria.objects.filter(
            cruce=OuterRef('pk')
        ).order_by('-timestamp')[:1]
        
        # Prefetch alertas activas
        alertas_prefetch = Prefetch(
            'alertas',
            queryset=Alerta.objects.filter(resolved=False).order_by('-created_at'),
            to_attr='alertas_activas_list'
        )
        
        # Prefetch eventos recientes
        eventos_prefetch = Prefetch(
            'barrier_events',
            queryset=BarrierEvent.objects.order_by('-event_time')[:1],
            to_attr='ultimo_evento_list'
        )
        
        cruces = Cruce.objects.prefetch_related(
            alertas_prefetch,
            eventos_prefetch
        ).annotate(
            latest_telemetria_id=Subquery(latest_telemetria.values('id')[:1])
        )
        
        # Obtener todas las telemetrías más recientes en una sola query
        telemetria_ids = [c.latest_telemetria_id for c in cruces if c.latest_telemetria_id]
        telemetrias_dict = {
            t.id: t for t in Telemetria.objects.filter(id__in=telemetria_ids).select_related('cruce')
        }
        
        dashboard_data = []
        
        for cruce in cruces:
            # Obtener telemetría más reciente del diccionario
            telemetria_actual = telemetrias_dict.get(cruce.latest_telemetria_id) if cruce.latest_telemetria_id else None
            
            # Contar alertas activas (ya prefetched)
            alertas_activas = len(cruce.alertas_activas_list) if hasattr(cruce, 'alertas_activas_list') else 0
            
            # Obtener último evento (ya prefetched)
            ultimo_evento = cruce.ultimo_evento_list[0] if hasattr(cruce, 'ultimo_evento_list') and cruce.ultimo_evento_list else None
            
            cruce_data = {
                'id': cruce.id,
                'nombre': cruce.nombre,
                'ubicacion': cruce.ubicacion,
                'estado': cruce.estado,
                'telemetria_actual': None,
                'alertas_activas': alertas_activas,
                'ultimo_evento': ultimo_evento.event_time.isoformat() if ultimo_evento else None
            }
            
            # Agregar telemetría actual si existe
            if telemetria_actual:
                cruce_data['telemetria_actual'] = {
                    'barrier_voltage': telemetria_actual.barrier_voltage,
                    'battery_voltage': telemetria_actual.battery_voltage,
                    'barrier_status': telemetria_actual.barrier_status,
                    'sensor_1': telemetria_actual.sensor_1,
                    'sensor_2': telemetria_actual.sensor_2,
                    'timestamp': telemetria_actual.timestamp.isoformat()
                }
            
            dashboard_data.append(cruce_data)
        
        return Response({
            'cruces': dashboard_data,
            'total_cruces': len(dashboard_data),
            'cruces_activos': len([c for c in dashboard_data if c['estado'] == 'ACTIVO']),
            'total_alertas_activas': sum(c['alertas_activas'] for c in dashboard_data)
        })

    @action(detail=False, methods=['get'], url_path='mapa')
    def mapa(self, request):
        """
        Endpoint para obtener coordenadas de todos los cruces para el mapa
        """
        cruces = Cruce.objects.filter(
            coordenadas_lat__isnull=False,
            coordenadas_lng__isnull=False
        ).values('id', 'nombre', 'ubicacion', 'estado', 'coordenadas_lat', 'coordenadas_lng')
        
        mapa_data = []
        for cruce in cruces:
            # Obtener telemetría más reciente para mostrar estado
            telemetria_actual = Telemetria.objects.filter(
                cruce_id=cruce['id']
            ).order_by('-timestamp').first()
            
            # Contar alertas activas
            alertas_activas = Alerta.objects.filter(
                cruce_id=cruce['id'],
                resolved=False
            ).count()
            
            mapa_data.append({
                'id': cruce['id'],
                'nombre': cruce['nombre'],
                'ubicacion': cruce['ubicacion'],
                'estado': cruce['estado'],
                'coordenadas': {
                    'lat': float(cruce['coordenadas_lat']),
                    'lng': float(cruce['coordenadas_lng'])
                },
                'telemetria_actual': {
                    'battery_voltage': telemetria_actual.battery_voltage if telemetria_actual else None,
                    'barrier_status': telemetria_actual.barrier_status if telemetria_actual else None,
                    'timestamp': telemetria_actual.timestamp.isoformat() if telemetria_actual else None
                } if telemetria_actual else None,
                'alertas_activas': alertas_activas
            })
        
        return Response({
            'cruces': mapa_data,
            'total_cruces': len(mapa_data)
        })


class SensorViewSet(ModelViewSet):
    """ViewSet para gestión de sensores"""
    queryset = Sensor.objects.all()
    serializer_class = SensorSerializer
    permission_classes = [IsAuthenticated, IsObserverOrAbove]
    
    def get_permissions(self):
        """
        Los observadores solo pueden leer.
        Solo admin puede crear/modificar sensores.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated(), IsObserverOrAbove()]

    def get_queryset(self):
        queryset = Sensor.objects.all()
        cruce_id = self.request.query_params.get('cruce_id', None)
        tipo = self.request.query_params.get('tipo', None)
        
        if cruce_id:
            queryset = queryset.filter(cruce_id=cruce_id)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        return queryset


class TelemetriaViewSet(ModelViewSet):
    """ViewSet para gestión de telemetría con lógica de negocio"""
    queryset = Telemetria.objects.all()
    serializer_class = TelemetriaSerializer
    permission_classes = [IsAuthenticated, IsObserverOrAbove]
    
    def get_permissions(self):
        """
        Los observadores solo pueden leer.
        Solo admin puede crear/modificar telemetría manualmente.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated(), IsObserverOrAbove()]

    def get_queryset(self):
        queryset = Telemetria.objects.all()
        cruce_id = self.request.query_params.get('cruce_id', None)
        fecha_desde = self.request.query_params.get('fecha_desde', None)
        fecha_hasta = self.request.query_params.get('fecha_hasta', None)
        
        if cruce_id:
            queryset = queryset.filter(cruce_id=cruce_id)
        if fecha_desde:
            queryset = queryset.filter(timestamp__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(timestamp__lte=fecha_hasta)
        return queryset

    def create(self, request, *args, **kwargs):
        """Crear telemetría con detección automática de eventos y alertas"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        telemetria = serializer.save()
        
        # Ejecutar lógica de negocio
        detect_barrier_event(telemetria)
        check_alerts(telemetria)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def exportar(self, request):
        """Exportar telemetría a CSV"""
        from django.http import HttpResponse
        import csv
        
        queryset = self.get_queryset()
        
        # Limitar a 10000 registros para evitar problemas de memoria
        if queryset.count() > 10000:
            queryset = queryset[:10000]
        
        # Crear respuesta CSV
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="telemetria_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Cruce', 'Fecha', 'Voltaje Barrera (V)', 'Voltaje Batería (V)',
            'Sensor 1', 'Sensor 2', 'Sensor 3', 'Sensor 4',
            'Estado Barrera', 'Señal WiFi (dBm)', 'Temperatura (°C)'
        ])
        
        for telemetria in queryset:
            writer.writerow([
                telemetria.id,
                telemetria.cruce.nombre,
                telemetria.timestamp.isoformat(),
                telemetria.barrier_voltage,
                telemetria.battery_voltage,
                telemetria.sensor_1 or '',
                telemetria.sensor_2 or '',
                telemetria.sensor_3 or '',
                telemetria.sensor_4 or '',
                telemetria.barrier_status or '',
                telemetria.signal_strength or '',
                telemetria.temperature or ''
            ])
        
        return response


class BarrierEventViewSet(ModelViewSet):
    """ViewSet para gestión de eventos de barrera"""
    queryset = BarrierEvent.objects.all()
    serializer_class = BarrierEventSerializer
    permission_classes = [IsAuthenticated, IsObserverOrAbove]
    
    def get_permissions(self):
        """
        Los observadores solo pueden leer.
        Solo admin puede crear/modificar eventos manualmente.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated(), IsObserverOrAbove()]

    def get_queryset(self):
        queryset = BarrierEvent.objects.all()
        cruce_id = self.request.query_params.get('cruce_id', None)
        estado = self.request.query_params.get('estado', None)
        fecha_desde = self.request.query_params.get('fecha_desde', None)
        
        if cruce_id:
            queryset = queryset.filter(cruce_id=cruce_id)
        if estado:
            queryset = queryset.filter(state=estado)
        if fecha_desde:
            queryset = queryset.filter(event_time__gte=fecha_desde)
        return queryset


class AlertaViewSet(ModelViewSet):
    """ViewSet para gestión de alertas"""
    queryset = Alerta.objects.all()
    serializer_class = AlertaSerializer
    permission_classes = [IsAuthenticated, CanModifyAlertas]
    
    @action(detail=False, methods=['get'])
    def exportar(self, request):
        """Exportar alertas a CSV"""
        from django.http import HttpResponse
        import csv
        
        queryset = self.get_queryset()
        
        # Crear respuesta CSV
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="alertas_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Tipo', 'Severidad', 'Cruce', 'Descripción',
            'Resuelta', 'Fecha Creación', 'Fecha Resolución'
        ])
        
        for alerta in queryset:
            writer.writerow([
                alerta.id,
                alerta.get_type_display(),
                alerta.get_severity_display(),
                alerta.cruce.nombre,
                alerta.description,
                'Sí' if alerta.resolved else 'No',
                alerta.created_at.isoformat(),
                alerta.resolved_at.isoformat() if alerta.resolved_at else ''
            ])
        
        return response

    def get_queryset(self):
        queryset = Alerta.objects.all()
        cruce_id = self.request.query_params.get('cruce_id', None)
        tipo = self.request.query_params.get('tipo', None)
        resuelta = self.request.query_params.get('resuelta', None)
        severidad = self.request.query_params.get('severidad', None)
        
        if cruce_id:
            queryset = queryset.filter(cruce_id=cruce_id)
        if tipo:
            queryset = queryset.filter(type=tipo)
        if resuelta is not None:
            resuelta_bool = resuelta.lower() == 'true'
            queryset = queryset.filter(resolved=resuelta_bool)
        if severidad:
            queryset = queryset.filter(severity=severidad)
        return queryset

    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        """
        Endpoint para dashboard que muestra resumen de alertas activas por cruce
        """
        # Obtener todas las alertas activas
        alertas_activas = Alerta.objects.filter(resolved=False).select_related('cruce')
        
        # Agrupar por cruce
        alertas_por_cruce = {}
        for alerta in alertas_activas:
            cruce_id = alerta.cruce.id
            if cruce_id not in alertas_por_cruce:
                alertas_por_cruce[cruce_id] = {
                    'cruce_id': cruce_id,
                    'cruce_nombre': alerta.cruce.nombre,
                    'total_alertas': 0,
                    'tipos_alertas': {},
                    'ultima_alerta': None
                }
            
            alertas_por_cruce[cruce_id]['total_alertas'] += 1
            
            # Contar por tipo
            tipo = alerta.type
            if tipo not in alertas_por_cruce[cruce_id]['tipos_alertas']:
                alertas_por_cruce[cruce_id]['tipos_alertas'][tipo] = 0
            alertas_por_cruce[cruce_id]['tipos_alertas'][tipo] += 1
            
            # Actualizar última alerta
            if (alertas_por_cruce[cruce_id]['ultima_alerta'] is None or 
                alerta.created_at > alertas_por_cruce[cruce_id]['ultima_alerta']):
                alertas_por_cruce[cruce_id]['ultima_alerta'] = alerta.created_at.isoformat()
        
        # Convertir a lista y ordenar por total de alertas
        alertas_list = list(alertas_por_cruce.values())
        alertas_list.sort(key=lambda x: x['total_alertas'], reverse=True)
        
        return Response({
            'alertas_por_cruce': alertas_list,
            'total_alertas_activas': len(alertas_activas),
            'cruces_con_alertas': len(alertas_list)
        })

    def update(self, request, *args, **kwargs):
        """Actualizar alerta con manejo especial para resolver"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Si se está resolviendo la alerta, agregar timestamp
        if 'resolved' in request.data and request.data['resolved'] and not instance.resolved:
            serializer.validated_data['resolved_at'] = timezone.now()
        
        serializer.save()
        return Response(serializer.data)



# ViewSets para Gestión de Usuarios

class UserViewSet(ModelViewSet):
	"""ViewSet para gestión completa de usuarios (solo administradores)"""
	queryset = User.objects.all().select_related('profile')
	serializer_class = UserManagementSerializer
	permission_classes = [IsAuthenticated, IsAdmin]

	def get_queryset(self):
		"""Obtener lista de usuarios con filtros opcionales"""
		queryset = User.objects.all().select_related('profile').order_by('-date_joined')

		# Filtro por rol
		role = self.request.query_params.get('role', None)
		if role:
			queryset = queryset.filter(profile__role=role)

		# Filtro por estado activo
		is_active = self.request.query_params.get('is_active', None)
		if is_active is not None:
			is_active_bool = is_active.lower() == 'true'
			queryset = queryset.filter(is_active=is_active_bool)

		# Filtro por búsqueda (email, username, nombre)
		search = self.request.query_params.get('search', None)
		if search:
			queryset = queryset.filter(
				Q(email__icontains=search) |
				Q(username__icontains=search) |
				Q(first_name__icontains=search) |
				Q(last_name__icontains=search)
			)

		return queryset

	def get_serializer_class(self):
		"""Usar serializer diferente para update parcial"""
		if self.action == 'partial_update':
			return UserUpdateSerializer
		return UserManagementSerializer

	def retrieve(self, request, *args, **kwargs):
		"""Obtener detalles de un usuario"""
		instance = self.get_object()
		serializer = self.get_serializer(instance)
		return Response({
			'user': serializer.data,
			'message': 'Usuario obtenido exitosamente'
		})

	def update(self, request, *args, **kwargs):
		"""Actualizar usuario completo"""
		partial = kwargs.pop('partial', False)
		instance = self.get_object()
		serializer = self.get_serializer(instance, data=request.data, partial=partial)

		if serializer.is_valid():
			user = serializer.save()

			# Log de actualización
			log_security_event(
				'USER_UPDATED',
				f'Usuario actualizado: {user.username} (ID: {user.id})',
				request=request,
				user=request.user,
				updated_user_id=user.id,
				severity='INFO'
			)

			return Response({
				'user': UserManagementSerializer(user).data,
				'message': 'Usuario actualizado exitosamente'
			})

		return Response({
			'error': 'Datos inválidos',
			'details': serializer.errors
		}, status=status.HTTP_400_BAD_REQUEST)

	def destroy(self, request, *args, **kwargs):
		"""Eliminar usuario (soft delete - desactivar)"""
		instance = self.get_object()

		# No permitir auto-eliminación
		if instance.id == request.user.id:
			return Response({
				'error': 'No puedes eliminar tu propio usuario'
			}, status=status.HTTP_400_BAD_REQUEST)

		# Soft delete: desactivar en lugar de eliminar
		username = instance.username
		user_id = instance.id
		instance.is_active = False
		instance.save()

		# Log de desactivación
		log_security_event(
			'USER_DEACTIVATED',
			f'Usuario desactivado: {username} (ID: {user_id})',
			request=request,
			user=request.user,
			deactivated_user_id=user_id,
			severity='WARNING'
		)

		return Response({
			'message': f'Usuario {username} desactivado exitosamente',
			'user_id': user_id
		}, status=status.HTTP_200_OK)

	@action(detail=True, methods=['post'])
	def activate(self, request, pk=None):
		"""Activar usuario desactivado"""
		user = self.get_object()

		if user.is_active:
			return Response({
				'error': 'El usuario ya está activo'
			}, status=status.HTTP_400_BAD_REQUEST)

		user.is_active = True
		user.save()

		log_security_event(
			'USER_ACTIVATED',
			f'Usuario activado: {user.username} (ID: {user.id})',
			request=request,
			user=request.user,
			activated_user_id=user.id,
			severity='INFO'
		)

		return Response({
			'message': f'Usuario {user.username} activado exitosamente',
			'user': UserManagementSerializer(user).data
		})

	@action(detail=True, methods=['post'])
	def change_role(self, request, pk=None):
		"""Cambiar rol de usuario"""
		user = self.get_object()
		new_role = request.data.get('role')

		if not new_role:
			return Response({
				'error': 'El campo "role" es requerido'
			}, status=status.HTTP_400_BAD_REQUEST)

		# Validar que el rol sea válido
		valid_roles = [choice[0] for choice in UserProfile.ROLE_CHOICES]
		if new_role not in valid_roles:
			return Response({
				'error': f'Rol inválido. Roles válidos: {", ".join(valid_roles)}'
			}, status=status.HTTP_400_BAD_REQUEST)

		# Validar que solo admin puede crear otros admin
		if new_role == 'ADMIN' and not request.user.profile.is_admin():
			return Response({
				'error': 'Solo administradores pueden asignar rol de administrador'
			}, status=status.HTTP_403_FORBIDDEN)

		# Actualizar rol
		try:
			profile = user.profile
			old_role = profile.role
			profile.role = new_role
			profile.save()
		except UserProfile.DoesNotExist:
			UserProfile.objects.create(user=user, role=new_role)
			old_role = None

		log_security_event(
			'USER_ROLE_CHANGED',
			f'Rol de usuario cambiado: {user.username} de {old_role} a {new_role}',
			request=request,
			user=request.user,
			target_user_id=user.id,
			old_role=old_role,
			new_role=new_role,
			severity='INFO'
		)

		return Response({
			'message': f'Rol de {user.username} cambiado de {old_role} a {new_role}',
			'user': UserManagementSerializer(user).data
		})

	@action(detail=False, methods=['get'])
	def roles(self, request):
		"""Obtener lista de roles disponibles"""
		roles = [
			{
				'value': choice[0],
				'label': choice[1]
			}
			for choice in UserProfile.ROLE_CHOICES
		]
		return Response({
			'roles': roles,
			'message': 'Roles disponibles obtenidos exitosamente'
		})


# ViewSets para Mantenimiento Preventivo

class MantenimientoPreventivoViewSet(ModelViewSet):
	"""ViewSet para gestión de reglas de mantenimiento preventivo"""
	queryset = MantenimientoPreventivo.objects.all()
	serializer_class = MantenimientoPreventivoSerializer
	permission_classes = [IsAuthenticated, IsAdmin]
	
	def get_queryset(self):
		"""Filtrar reglas por cruce o estado activo"""
		queryset = MantenimientoPreventivo.objects.all()
		
		cruce_id = self.request.query_params.get('cruce', None)
		if cruce_id:
			queryset = queryset.filter(Q(cruce_id=cruce_id) | Q(cruce__isnull=True))
		
		activo = self.request.query_params.get('activo', None)
		if activo is not None:
			activo_bool = activo.lower() == 'true'
			queryset = queryset.filter(activo=activo_bool)
		
		return queryset.order_by('-prioridad', 'nombre')


class HistorialMantenimientoViewSet(ModelViewSet):
	"""ViewSet para gestión de historial de mantenimientos"""
	queryset = HistorialMantenimiento.objects.all()
	serializer_class = HistorialMantenimientoSerializer
	permission_classes = [IsAuthenticated, IsObserverOrAbove]
	
	def get_queryset(self):
		"""Filtrar mantenimientos por cruce, estado o fecha"""
		queryset = HistorialMantenimiento.objects.all()
		
		cruce_id = self.request.query_params.get('cruce', None)
		if cruce_id:
			queryset = queryset.filter(cruce_id=cruce_id)
		
		estado = self.request.query_params.get('estado', None)
		if estado:
			queryset = queryset.filter(estado=estado)
		
		fecha_desde = self.request.query_params.get('fecha_desde', None)
		if fecha_desde:
			queryset = queryset.filter(fecha_programada__gte=fecha_desde)
		
		fecha_hasta = self.request.query_params.get('fecha_hasta', None)
		if fecha_hasta:
			queryset = queryset.filter(fecha_programada__lte=fecha_hasta)
		
		return queryset.order_by('-fecha_programada')
	
	def get_permissions(self):
		"""Solo admin puede crear/modificar/eliminar mantenimientos"""
		if self.action in ['create', 'update', 'partial_update', 'destroy']:
			return [IsAuthenticated(), IsAdmin()]
		return [IsAuthenticated(), IsObserverOrAbove()]
	
	@action(detail=True, methods=['post'])
	def iniciar(self, request, pk=None):
		"""Iniciar un mantenimiento programado"""
		mantenimiento = self.get_object()
		
		if mantenimiento.estado != 'PENDIENTE':
			return Response({
				'error': f'El mantenimiento ya está {mantenimiento.get_estado_display()}'
			}, status=status.HTTP_400_BAD_REQUEST)
		
		mantenimiento.estado = 'EN_PROCESO'
		mantenimiento.fecha_inicio = timezone.now()
		mantenimiento.responsable = request.data.get('responsable', mantenimiento.responsable)
		mantenimiento.save()
		
		return Response({
			'message': 'Mantenimiento iniciado',
			'mantenimiento': HistorialMantenimientoSerializer(mantenimiento).data
		})
	
	@action(detail=True, methods=['post'])
	def completar(self, request, pk=None):
		"""Completar un mantenimiento"""
		mantenimiento = self.get_object()
		
		if mantenimiento.estado not in ['EN_PROCESO', 'PENDIENTE']:
			return Response({
				'error': f'No se puede completar un mantenimiento {mantenimiento.get_estado_display()}'
			}, status=status.HTTP_400_BAD_REQUEST)
		
		# Obtener métricas después del mantenimiento
		ultima_telemetria = Telemetria.objects.filter(
			cruce=mantenimiento.cruce
		).order_by('-timestamp').first()
		
		metricas_despues = {}
		if ultima_telemetria:
			metricas_despues = {
				'battery_voltage': ultima_telemetria.battery_voltage,
				'barrier_voltage': ultima_telemetria.barrier_voltage,
				'barrier_status': ultima_telemetria.barrier_status,
				'signal_strength': ultima_telemetria.signal_strength,
				'temperature': ultima_telemetria.temperature,
				'timestamp': ultima_telemetria.timestamp.isoformat(),
			}
		
		mantenimiento.estado = 'COMPLETADO'
		mantenimiento.fecha_fin = timezone.now()
		mantenimiento.observaciones = request.data.get('observaciones', mantenimiento.observaciones)
		mantenimiento.metricas_despues = metricas_despues
		mantenimiento.save()
		
		return Response({
			'message': 'Mantenimiento completado',
			'mantenimiento': HistorialMantenimientoSerializer(mantenimiento).data
		})


class MetricasDesempenoViewSet(ModelViewSet):
	"""ViewSet para métricas de desempeño"""
	queryset = MetricasDesempeno.objects.all()
	serializer_class = MetricasDesempenoSerializer
	permission_classes = [IsAuthenticated, IsObserverOrAbove]
	
	def get_queryset(self):
		"""Filtrar métricas por cruce o fecha"""
		queryset = MetricasDesempeno.objects.all()
		
		cruce_id = self.request.query_params.get('cruce', None)
		if cruce_id:
			queryset = queryset.filter(cruce_id=cruce_id)
		
		fecha_desde = self.request.query_params.get('fecha_desde', None)
		if fecha_desde:
			queryset = queryset.filter(fecha__gte=fecha_desde)
		
		fecha_hasta = self.request.query_params.get('fecha_hasta', None)
		if fecha_hasta:
			queryset = queryset.filter(fecha__lte=fecha_hasta)
		
		return queryset.order_by('-fecha', 'cruce')
	
	def get_permissions(self):
		"""Solo admin puede crear/modificar métricas"""
		if self.action in ['create', 'update', 'partial_update', 'destroy']:
			return [IsAuthenticated(), IsAdmin()]
		return [IsAuthenticated(), IsObserverOrAbove()]
	
	@action(detail=False, methods=['get'])
	def resumen(self, request):
		"""Obtener resumen de métricas"""
		cruce_id = request.query_params.get('cruce', None)
		fecha_desde = request.query_params.get('fecha_desde', None)
		fecha_hasta = request.query_params.get('fecha_hasta', None)
		
		queryset = self.get_queryset()
		
		if fecha_desde:
			queryset = queryset.filter(fecha__gte=fecha_desde)
		if fecha_hasta:
			queryset = queryset.filter(fecha__lte=fecha_hasta)
		
		# Calcular promedios
		from django.db.models import Avg, Sum, Count
		
		resumen = queryset.aggregate(
			disponibilidad_promedio=Avg('disponibilidad_porcentaje'),
			total_mantenimientos=Sum('mantenimientos_realizados'),
			total_alertas=Sum('total_alertas'),
			total_eventos=Sum('total_eventos_barrera'),
			horas_bateria_baja_total=Sum('horas_bateria_baja'),
		)
		
		return Response({
			'resumen': resumen,
			'periodo': {
				'fecha_desde': fecha_desde,
				'fecha_hasta': fecha_hasta,
			}
		})
