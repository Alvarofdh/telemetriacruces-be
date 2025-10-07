from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.db.models import Q
from django.conf import settings
import logging
from .serializers import (
    LoginSerializer, RegisterSerializer, UserSerializer, TokenSerializer,
    TelemetriaSerializer, CruceSerializer, SensorSerializer, 
    BarrierEventSerializer, AlertaSerializer, ESP32TelemetriaSerializer,
    UserNotificationSettingsSerializer
)
from .models import Telemetria, Cruce, Sensor, BarrierEvent, Alerta, UserNotificationSettings

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
    
    URL: POST /api/login
    """
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']  # type: ignore
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
@permission_classes([AllowAny])
def register_view(request):
    """
    Endpoint para registrar nuevos usuarios.
    
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
        
        # Obtener el cruce
        cruce = Cruce.objects.get(id=serializer.validated_data['cruce_id'])
        
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
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Cruce.objects.all()
        estado = self.request.query_params.get('estado', None)
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset

    def retrieve(self, request, *args, **kwargs):
        """
        Obtener detalles completos de un cruce incluyendo telemetría
        """
        instance = self.get_object()
        
        # Obtener telemetría más reciente
        telemetria_actual = Telemetria.objects.filter(
            cruce=instance
        ).order_by('-timestamp').first()
        
        # Obtener últimas 10 telemetrías para historial
        telemetrias_recientes = Telemetria.objects.filter(
            cruce=instance
        ).order_by('-timestamp')[:10]
        
        # Obtener alertas activas
        alertas_activas = Alerta.objects.filter(
            cruce=instance,
            resolved=False
        ).order_by('-created_at')
        
        # Obtener últimos eventos de barrera
        eventos_recientes = BarrierEvent.objects.filter(
            cruce=instance
        ).order_by('-event_time')[:5]
        
        # Obtener sensores del cruce
        sensores = Sensor.objects.filter(
            cruce=instance,
            activo=True
        )
        
        # Construir respuesta completa
        cruce_data = {
            'id': instance.id,
            'nombre': instance.nombre,
            'ubicacion': instance.ubicacion,
            'coordenadas_lat': instance.coordenadas_lat,
            'coordenadas_lng': instance.coordenadas_lng,
            'estado': instance.estado,
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
        cruces = Cruce.objects.all()
        dashboard_data = []
        
        for cruce in cruces:
            # Obtener telemetría más reciente
            telemetria_actual = Telemetria.objects.filter(
                cruce=cruce
            ).order_by('-timestamp').first()
            
            # Contar alertas activas
            alertas_activas = Alerta.objects.filter(
                cruce=cruce,
                resolved=False
            ).count()
            
            # Obtener último evento de barrera
            ultimo_evento = BarrierEvent.objects.filter(
                cruce=cruce
            ).order_by('-event_time').first()
            
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
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

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


class BarrierEventViewSet(ModelViewSet):
    """ViewSet para gestión de eventos de barrera"""
    queryset = BarrierEvent.objects.all()
    serializer_class = BarrierEventSerializer
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

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
