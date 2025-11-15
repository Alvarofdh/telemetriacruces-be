from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.exceptions import ObjectDoesNotExist
from rest_framework_simplejwt.tokens import RefreshToken
from .models import (
	Telemetria, Cruce, Sensor, BarrierEvent, Alerta, UserNotificationSettings, UserProfile,
	MantenimientoPreventivo, HistorialMantenimiento, MetricasDesempeno
)

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer para el perfil de usuario"""
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ('role', 'role_display', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')

class UserSerializer(serializers.ModelSerializer):
    """Serializer para el modelo User de Django"""
    profile = UserProfileSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'full_name', 'date_joined', 'profile')
        read_only_fields = ('id', 'date_joined')
    
    def get_full_name(self, obj):
        """Obtener nombre completo del usuario"""
        if obj.first_name or obj.last_name:
            return f"{obj.first_name} {obj.last_name}".strip()
        return obj.username

class LoginSerializer(serializers.Serializer):
    """Serializer para el login con email"""
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(max_length=128, write_only=True)

    def validate_email(self, value):
        """Validar formato y longitud de email"""
        if not value:
            raise serializers.ValidationError('El email es requerido')
        
        # Validar longitud máxima
        if len(value) > 255:
            raise serializers.ValidationError('El email es demasiado largo')
        
        # Validar formato básico
        if '@' not in value or '.' not in value.split('@')[1]:
            raise serializers.ValidationError('Formato de email inválido')
        
        # Sanitizar email
        value = value.strip().lower()
        
        return value

    def validate_password(self, value):
        """Validar contraseña"""
        if not value:
            raise serializers.ValidationError('La contraseña es requerida')
        
        # Validar longitud mínima
        if len(value) < 8:
            raise serializers.ValidationError('La contraseña debe tener al menos 8 caracteres')
        
        # Validar longitud máxima
        if len(value) > 128:
            raise serializers.ValidationError('La contraseña es demasiado larga')
        
        return value

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            # Buscar usuario por email
            try:
                user = User.objects.get(email=email)
                # Autenticar con username (Django usa username para authenticate)
                user = authenticate(username=user.username, password=password)
                if not user:
                    raise serializers.ValidationError('Credenciales inválidas')
                if not user.is_active:
                    raise serializers.ValidationError('Usuario inactivo')
            except ObjectDoesNotExist:
                # No exponer si el usuario existe o no (prevenir enumeración)
                raise serializers.ValidationError('Credenciales inválidas')
        else:
            raise serializers.ValidationError('Debe proporcionar email y password')

        attrs['user'] = user
        return attrs

class RegisterSerializer(serializers.ModelSerializer):
    """Serializer para registro de usuarios con email"""
    email = serializers.EmailField(required=True, max_length=255)
    password = serializers.CharField(write_only=True, min_length=12, max_length=128)  # Aumentado a 12
    password_confirm = serializers.CharField(write_only=True, max_length=128)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, default='OBSERVER', write_only=True)

    class Meta:
        model = User
        fields = ('email', 'password', 'password_confirm', 'first_name', 'last_name', 'role')

    def validate_email(self, value):
        """Validar email"""
        if not value:
            raise serializers.ValidationError('El email es requerido')
        
        # Sanitizar email
        value = value.strip().lower()
        
        # Validar longitud
        if len(value) > 255:
            raise serializers.ValidationError('El email es demasiado largo')
        
        # Verificar que el email no esté en uso
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este email ya está registrado")
        
        return value

    def validate_password(self, value):
        """Validar contraseña"""
        if len(value) < 12:
            raise serializers.ValidationError("La contraseña debe tener al menos 12 caracteres")
        
        if len(value) > 128:
            raise serializers.ValidationError("La contraseña es demasiado larga")
        
        # Verificar que no sea solo números
        if value.isdigit():
            raise serializers.ValidationError("La contraseña no puede ser solo números")
        
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        
        # Solo administradores pueden crear otros administradores
        request = self.context.get('request')
        if attrs.get('role') == 'ADMIN':
            if request and request.user.is_authenticated:
                try:
                    if not request.user.profile.is_admin():
                        raise serializers.ValidationError("Solo administradores pueden crear otros administradores")
                except:
                    raise serializers.ValidationError("Solo administradores pueden crear otros administradores")
            else:
                raise serializers.ValidationError("Solo administradores pueden crear otros administradores")
        
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        role = validated_data.pop('role', 'OBSERVER')
        
        # Generar username desde el email
        email = validated_data['email']
        username = email.split('@')[0]  # Tomar la parte antes del @
        
        # Si el username ya existe, agregar números
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Crear usuario con username generado
        user = User.objects.create_user(
            username=username,
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        
        # Crear perfil con el rol especificado
        UserProfile.objects.create(user=user, role=role)
        
        return user

class TokenSerializer(serializers.Serializer):
    """Serializer para tokens JWT"""
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()

# Serializers para el sistema de cruces ferroviarios

class CruceSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Cruce"""
    # Campos calculados
    total_sensores = serializers.SerializerMethodField()
    sensores_activos = serializers.SerializerMethodField()
    ultima_telemetria = serializers.SerializerMethodField()
    alertas_activas = serializers.SerializerMethodField()
    
    class Meta:
        model = Cruce
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
    
    def get_total_sensores(self, obj):
        """Obtener total de sensores del cruce"""
        return obj.sensores.count()
    
    def get_sensores_activos(self, obj):
        """Obtener cantidad de sensores activos"""
        return obj.sensores.filter(activo=True).count()
    
    def get_ultima_telemetria(self, obj):
        """Obtener última telemetría del cruce"""
        ultima = obj.telemetrias.order_by('-timestamp').first()
        if ultima:
            return {
                'id': ultima.id,
                'timestamp': ultima.timestamp,
                'barrier_voltage': ultima.barrier_voltage,
                'battery_voltage': ultima.battery_voltage,
                'barrier_status': ultima.barrier_status,
                'signal_strength': ultima.signal_strength,
                'temperature': ultima.temperature,
            }
        return None
    
    def get_alertas_activas(self, obj):
        """Obtener cantidad de alertas activas"""
        return obj.alertas.filter(resolved=False).count()

class SensorSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Sensor"""
    cruce_nombre = serializers.CharField(source='cruce.nombre', read_only=True)
    
    class Meta:
        model = Sensor
        fields = '__all__'
        read_only_fields = ('created_at',)

class TelemetriaSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Telemetria con validaciones específicas"""
    cruce_nombre = serializers.CharField(source='cruce.nombre', read_only=True)
    
    class Meta:
        model = Telemetria
        fields = '__all__'
        read_only_fields = ('timestamp', 'barrier_status')

    def validate_barrier_voltage(self, value):
        """Validar rango de voltaje de barrera (0-24V)"""
        if value < 0 or value > 24:
            raise serializers.ValidationError("El voltaje de barrera debe estar entre 0V y 24V")
        return value

    def validate_battery_voltage(self, value):
        """Validar rango de voltaje de batería (10-15V)"""
        if value < 10 or value > 15:
            raise serializers.ValidationError("El voltaje de batería debe estar entre 10V y 15V")
        return value

    def validate_sensor_1(self, value):
        """Validar rango de sensor ADC (0-1023)"""
        if value is not None and (value < 0 or value > 1023):
            raise serializers.ValidationError("El valor del sensor debe estar entre 0 y 1023")
        return value

    def validate_sensor_2(self, value):
        """Validar rango de sensor ADC (0-1023)"""
        if value is not None and (value < 0 or value > 1023):
            raise serializers.ValidationError("El valor del sensor debe estar entre 0 y 1023")
        return value

    def validate_sensor_3(self, value):
        """Validar rango de sensor ADC (0-1023)"""
        if value is not None and (value < 0 or value > 1023):
            raise serializers.ValidationError("El valor del sensor debe estar entre 0 y 1023")
        return value

    def validate_sensor_4(self, value):
        """Validar rango de sensor ADC (0-1023)"""
        if value is not None and (value < 0 or value > 1023):
            raise serializers.ValidationError("El valor del sensor debe estar entre 0 y 1023")
        return value

class BarrierEventSerializer(serializers.ModelSerializer):
    """Serializer para el modelo BarrierEvent"""
    cruce_nombre = serializers.CharField(source='cruce.nombre', read_only=True)
    
    class Meta:
        model = BarrierEvent
        fields = '__all__'

    def validate_event_time(self, value):
        """Validar que el evento no sea en el futuro"""
        from django.utils import timezone
        if value > timezone.now():
            raise serializers.ValidationError("El evento no puede ser en el futuro")
        return value

class AlertaSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Alerta"""
    cruce_nombre = serializers.CharField(source='cruce.nombre', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    
    class Meta:
        model = Alerta
        fields = '__all__'
        read_only_fields = ('created_at', 'resolved_at')

    def validate_description(self, value):
        """Validar que la descripción no esté vacía"""
        if not value.strip():
            raise serializers.ValidationError("La descripción no puede estar vacía")
        return value


class ESP32TelemetriaSerializer(serializers.Serializer):
    """Serializer específico para ESP32 - Sin autenticación JWT"""
    esp32_token = serializers.CharField(max_length=200, write_only=True, min_length=10)
    cruce_id = serializers.IntegerField(min_value=1)
    
    # Voltajes principales
    barrier_voltage = serializers.FloatField(min_value=0.0, max_value=24.0)
    battery_voltage = serializers.FloatField(min_value=10.0, max_value=15.0)
    
    # Sensores adicionales (opcionales)
    sensor_1 = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=1023)
    sensor_2 = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=1023)
    sensor_3 = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=1023)
    sensor_4 = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=1023)
    
    # Información adicional del ESP32 (opcionales)
    signal_strength = serializers.IntegerField(required=False, allow_null=True, min_value=-120, max_value=0)
    temperature = serializers.FloatField(required=False, allow_null=True, min_value=-40.0, max_value=85.0)

    def validate_esp32_token(self, value):
        """Validar token del ESP32"""
        from django.conf import settings
        expected_token = getattr(settings, 'ESP32_TOKEN', 'esp32_default_token_123')
        if value != expected_token:
            raise serializers.ValidationError("Token de ESP32 inválido")
        return value

    def validate_cruce_id(self, value):
        """Validar que el cruce existe"""
        try:
            Cruce.objects.get(id=value, estado='ACTIVO')
        except Cruce.DoesNotExist:
            raise serializers.ValidationError("Cruce no encontrado o inactivo")
        return value

    def validate_barrier_voltage(self, value):
        """Validar rango de voltaje de barrera (0-24V)"""
        if value < 0 or value > 24:
            raise serializers.ValidationError("El voltaje de barrera debe estar entre 0V y 24V")
        return value

    def validate_battery_voltage(self, value):
        """Validar rango de voltaje de batería (10-15V)"""
        if value < 10 or value > 15:
            raise serializers.ValidationError("El voltaje de batería debe estar entre 10V y 15V")
        return value

    def validate_sensor_1(self, value):
        """Validar rango de sensor ADC (0-1023)"""
        if value is not None and (value < 0 or value > 1023):
            raise serializers.ValidationError("El valor del sensor debe estar entre 0 y 1023")
        return value

    def validate_sensor_2(self, value):
        """Validar rango de sensor ADC (0-1023)"""
        if value is not None and (value < 0 or value > 1023):
            raise serializers.ValidationError("El valor del sensor debe estar entre 0 y 1023")
        return value

    def validate_sensor_3(self, value):
        """Validar rango de sensor ADC (0-1023)"""
        if value is not None and (value < 0 or value > 1023):
            raise serializers.ValidationError("El valor del sensor debe estar entre 0 y 1023")
        return value

    def validate_sensor_4(self, value):
        """Validar rango de sensor ADC (0-1023)"""
        if value is not None and (value < 0 or value > 1023):
            raise serializers.ValidationError("El valor del sensor debe estar entre 0 y 1023")
        return value


class UserNotificationSettingsSerializer(serializers.ModelSerializer):
    """Serializer para configuración de notificaciones del usuario"""
    frequency_display = serializers.CharField(source='get_notification_frequency_display', read_only=True)
    
    class Meta:
        model = UserNotificationSettings
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')


# Serializers para Mantenimiento Preventivo

class MantenimientoPreventivoSerializer(serializers.ModelSerializer):
	"""Serializer para reglas de mantenimiento preventivo"""
	cruce_nombre = serializers.CharField(source='cruce.nombre', read_only=True)
	tipo_mantenimiento_display = serializers.CharField(source='get_tipo_mantenimiento_display', read_only=True)
	prioridad_display = serializers.CharField(source='get_prioridad_display', read_only=True)
	
	class Meta:
		model = MantenimientoPreventivo
		fields = '__all__'
		read_only_fields = ('created_at', 'updated_at')


class HistorialMantenimientoSerializer(serializers.ModelSerializer):
	"""Serializer para historial de mantenimientos"""
	cruce_nombre = serializers.CharField(source='cruce.nombre', read_only=True)
	regla_nombre = serializers.CharField(source='regla.nombre', read_only=True)
	tipo_mantenimiento_display = serializers.CharField(source='get_tipo_mantenimiento_display', read_only=True)
	prioridad_display = serializers.CharField(source='get_prioridad_display', read_only=True)
	estado_display = serializers.CharField(source='get_estado_display', read_only=True)
	
	class Meta:
		model = HistorialMantenimiento
		fields = '__all__'
		read_only_fields = ('created_at', 'updated_at')


class MetricasDesempenoSerializer(serializers.ModelSerializer):
	"""Serializer para métricas de desempeño"""
	cruce_nombre = serializers.CharField(source='cruce.nombre', read_only=True)
	
	class Meta:
		model = MetricasDesempeno
		fields = '__all__'
		read_only_fields = ('created_at', 'updated_at')