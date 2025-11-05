# Create your models here.
from django.db import models
from django.utils import timezone


class ApiAlerta(models.Model):
    sensor = models.ForeignKey('Sensor', models.DO_NOTHING, blank=True, null=True)
    telemetria = models.ForeignKey('Telemetria', models.DO_NOTHING, blank=True, null=True)
    type = models.CharField(max_length=20)
    description = models.TextField()
    created_at = models.DateTimeField()
    resolved = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'api_alerta'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class BarrierEvent(models.Model):
    """Eventos de cambio de estado de barrera"""
    STATE_CHOICES = [
        ('DOWN', 'Barrera Abajo'),
        ('UP', 'Barrera Arriba'),
    ]
    
    telemetria = models.ForeignKey('Telemetria', on_delete=models.CASCADE, related_name='barrier_events')
    cruce = models.ForeignKey('Cruce', on_delete=models.CASCADE, related_name='barrier_events')
    state = models.CharField(max_length=4, choices=STATE_CHOICES)
    event_time = models.DateTimeField()
    voltage_at_event = models.FloatField()  # Voltaje en el momento del evento
    
    def __str__(self):
        return f"Evento {self.cruce.nombre} - {self.state} - {self.event_time}"

    class Meta:
        verbose_name = "Evento de Barrera"
        verbose_name_plural = "Eventos de Barrera"
        ordering = ['-event_time']
        indexes = [
            models.Index(fields=['-event_time', 'cruce'], name='barrier_event_time_cruce_idx'),
            models.Index(fields=['cruce', 'event_time'], name='barrier_cruce_event_time_idx'),
            models.Index(fields=['state'], name='barrier_state_idx'),
        ]


class Cruce(models.Model):
    """Modelo para los cruces ferroviarios"""
    nombre = models.CharField(max_length=100)
    ubicacion = models.CharField(max_length=200)
    coordenadas_lat = models.FloatField(null=True, blank=True)
    coordenadas_lng = models.FloatField(null=True, blank=True)
    estado = models.CharField(max_length=20, default='ACTIVO')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} - {self.ubicacion}"

    class Meta:
        verbose_name = "Cruce"
        verbose_name_plural = "Cruces"
        ordering = ['nombre']  # Ordenar por nombre por defecto
        indexes = [
            models.Index(fields=['estado'], name='cruce_estado_idx'),
        ]


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class Sensor(models.Model):
    """Modelo para los sensores del sistema"""
    SENSOR_TYPES = [
        ('BARRERA', 'Sensor de Barrera'),
        ('GABINETE', 'Sensor de Gabinete'),
        ('BATERIA', 'Sensor de Batería'),
        ('PLC', 'Sensor PLC'),
        ('TEMPERATURA', 'Sensor de Temperatura'),
    ]
    
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=SENSOR_TYPES)
    cruce = models.ForeignKey(Cruce, on_delete=models.CASCADE, related_name='sensores')
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} - {self.get_tipo_display()} - {self.cruce.nombre}"

    class Meta:
        verbose_name = "Sensor"
        verbose_name_plural = "Sensores"
        ordering = ['nombre']  # Ordenar por nombre por defecto


class Telemetria(models.Model):
    """Modelo principal para las lecturas del ESP32"""
    cruce = models.ForeignKey(Cruce, on_delete=models.CASCADE, related_name='telemetrias')
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Voltajes principales
    barrier_voltage = models.FloatField()  # Voltaje de barrera del PLC (0-24V)
    battery_voltage = models.FloatField()  # Voltaje de batería (10-15V)
    
    # Sensores adicionales
    sensor_1 = models.IntegerField(null=True, blank=True)  # Sensores adicionales
    sensor_2 = models.IntegerField(null=True, blank=True)
    sensor_3 = models.IntegerField(null=True, blank=True)
    sensor_4 = models.IntegerField(null=True, blank=True)
    
    # Estado de la barrera (calculado automáticamente)
    barrier_status = models.CharField(max_length=4, choices=[
        ('UP', 'Barrera Arriba'),
        ('DOWN', 'Barrera Abajo'),
    ], null=True, blank=True)
    
    # Información adicional del ESP32
    signal_strength = models.IntegerField(null=True, blank=True)  # RSSI
    temperature = models.FloatField(null=True, blank=True)
    
    def __str__(self):
        return f"Telemetría {self.cruce.nombre} - {self.timestamp}"

    class Meta:
        verbose_name = "Telemetría"
        verbose_name_plural = "Telemetrías"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp', 'cruce'], name='telemetria_timestamp_cruce_idx'),
            models.Index(fields=['cruce', 'timestamp'], name='telemetria_cruce_timestamp_idx'),
            models.Index(fields=['barrier_status'], name='telemetria_barrier_status_idx'),
        ]


class Alerta(models.Model):
    """Alertas automáticas del sistema"""
    ALERT_TYPES = [
        ('LOW_BATTERY', 'Batería Baja'),
        ('SENSOR_ERROR', 'Error de Sensor'),
        ('BARRIER_STUCK', 'Barrera Bloqueada'),
        ('VOLTAGE_CRITICAL', 'Voltaje Crítico'),
        ('COMMUNICATION_LOST', 'Comunicación Perdida'),
        ('GABINETE_ABIERTO', 'Gabinete Abierto'),
    ]
    
    SEVERITY_CHOICES = [
        ('CRITICAL', 'Crítica'),
        ('WARNING', 'Advertencia'),
        ('INFO', 'Información'),
    ]
    
    type = models.CharField(max_length=20, choices=ALERT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='INFO')
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Relaciones
    telemetria = models.ForeignKey(Telemetria, on_delete=models.SET_NULL, null=True, blank=True, related_name='alertas')
    cruce = models.ForeignKey(Cruce, on_delete=models.CASCADE, related_name='alertas')
    sensor = models.ForeignKey(Sensor, on_delete=models.SET_NULL, null=True, blank=True, related_name='alertas')
    
    def __str__(self):
        return f"Alerta {self.get_type_display()} - {self.cruce.nombre} - {self.created_at}"

    class Meta:
        verbose_name = "Alerta"
        verbose_name_plural = "Alertas"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at', 'cruce'], name='alerta_created_cruce_idx'),
            models.Index(fields=['cruce', 'resolved'], name='alerta_cruce_resolved_idx'),
            models.Index(fields=['severity', 'resolved'], name='alerta_severity_resolved_idx'),
        ]


class UserProfile(models.Model):
    """Perfil extendido del usuario con roles"""
    ROLE_CHOICES = [
        ('ADMIN', 'Administrador'),
        ('MAINTENANCE', 'Personal de Mantenimiento'),
        ('OBSERVER', 'Observador'),
    ]
    
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='OBSERVER', verbose_name="Rol")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    def is_admin(self):
        """Verificar si es administrador"""
        return self.role == 'ADMIN'
    
    def is_maintenance(self):
        """Verificar si es personal de mantenimiento"""
        return self.role == 'MAINTENANCE'
    
    def is_observer(self):
        """Verificar si es observador"""
        return self.role == 'OBSERVER'
    
    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuario"


class UserNotificationSettings(models.Model):
    """Configuración de notificaciones del usuario"""
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='notification_settings')
    
    # Notificaciones generales
    enable_notifications = models.BooleanField(default=True, verbose_name="Activar notificaciones")
    enable_push_notifications = models.BooleanField(default=True, verbose_name="Notificaciones push")
    enable_email_notifications = models.BooleanField(default=False, verbose_name="Notificaciones por email")
    
    # Tipos de alertas específicas
    notify_critical_alerts = models.BooleanField(default=True, verbose_name="Alertas críticas")
    notify_warning_alerts = models.BooleanField(default=True, verbose_name="Alertas de advertencia")
    notify_info_alerts = models.BooleanField(default=False, verbose_name="Alertas informativas")
    
    # Eventos específicos
    notify_barrier_events = models.BooleanField(default=True, verbose_name="Eventos de barrera")
    notify_battery_low = models.BooleanField(default=True, verbose_name="Batería baja")
    notify_communication_lost = models.BooleanField(default=True, verbose_name="Comunicación perdida")
    notify_gabinete_open = models.BooleanField(default=True, verbose_name="Gabinete abierto")
    
    # Configuración de frecuencia
    notification_frequency = models.CharField(
        max_length=20,
        choices=[
            ('IMMEDIATE', 'Inmediato'),
            ('HOURLY', 'Cada hora'),
            ('DAILY', 'Diario'),
            ('WEEKLY', 'Semanal'),
        ],
        default='IMMEDIATE',
        verbose_name="Frecuencia de notificaciones"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Configuración de notificaciones - {self.user.username}"
    
    class Meta:
        verbose_name = "Configuración de Notificaciones"
        verbose_name_plural = "Configuraciones de Notificaciones"
