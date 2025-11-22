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
    ESTADO_CHOICES = [
        ('ACTIVO', 'Activo'),
        ('MANTENIMIENTO', 'En mantenimiento'),
        ('INACTIVO', 'Inactivo'),
    ]
    
    nombre = models.CharField(max_length=100)
    ubicacion = models.CharField(max_length=200)
    coordenadas_lat = models.FloatField(null=True, blank=True)
    coordenadas_lng = models.FloatField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='ACTIVO')
    responsable_nombre = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Nombre del Responsable"
    )
    responsable_telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Teléfono del Responsable"
    )
    responsable_email = models.EmailField(
        max_length=254,
        blank=True,
        null=True,
        verbose_name="Email del Responsable"
    )
    responsable_empresa = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Empresa de Mantenimiento"
    )
    responsable_horario = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Horario de Atención",
        help_text="Ej: Lunes a Viernes 8:00-18:00"
    )
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


class MantenimientoPreventivo(models.Model):
	"""Reglas de mantenimiento preventivo configurables"""
	PRIORIDAD_CHOICES = [
		('BAJA', 'Baja'),
		('MEDIA', 'Media'),
		('ALTA', 'Alta'),
		('CRITICA', 'Crítica'),
	]
	
	TIPO_MANTENIMIENTO_CHOICES = [
		('BATERIA', 'Cambio de Batería'),
		('SENSOR', 'Revisión de Sensor'),
		('BARRERA', 'Mantenimiento de Barrera'),
		('ENERGIA', 'Revisión de Sistema Energético'),
		('GENERAL', 'Mantenimiento General'),
		('LIMPIEZA', 'Limpieza y Revisión'),
	]
	
	nombre = models.CharField(max_length=100, verbose_name="Nombre de la Regla")
	descripcion = models.TextField(blank=True, verbose_name="Descripción")
	tipo_mantenimiento = models.CharField(max_length=20, choices=TIPO_MANTENIMIENTO_CHOICES, verbose_name="Tipo de Mantenimiento")
	prioridad = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='MEDIA', verbose_name="Prioridad")
	
	# Condiciones de activación (JSON configurable)
	condiciones = models.JSONField(default=dict, verbose_name="Condiciones de Activación", help_text="JSON con las condiciones que deben cumplirse")
	
	# Acciones a realizar
	acciones = models.JSONField(default=dict, verbose_name="Acciones", help_text="JSON con las acciones a realizar cuando se active")
	
	# Configuración de alertas
	generar_alerta = models.BooleanField(default=True, verbose_name="Generar Alerta Automática")
	tipo_alerta = models.CharField(max_length=20, choices=Alerta.ALERT_TYPES, default='LOW_BATTERY', verbose_name="Tipo de Alerta")
	severidad_alerta = models.CharField(max_length=10, choices=Alerta.SEVERITY_CHOICES, default='WARNING', verbose_name="Severidad de Alerta")
	
	# Configuración de fechas (para mantenimiento programado)
	fecha_inicio = models.DateField(null=True, blank=True, verbose_name="Fecha de Inicio")
	fecha_fin = models.DateField(null=True, blank=True, verbose_name="Fecha de Fin")
	dias_semana = models.JSONField(default=list, blank=True, verbose_name="Días de la Semana", help_text="[0=Domingo, 1=Lunes, ..., 6=Sábado]")
	
	# Estado
	activo = models.BooleanField(default=True, verbose_name="Regla Activa")
	
	# Relaciones
	cruce = models.ForeignKey('Cruce', on_delete=models.CASCADE, null=True, blank=True, related_name='reglas_mantenimiento', verbose_name="Cruce Específico")
	
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	def __str__(self):
		return f"{self.nombre} - {self.get_tipo_mantenimiento_display()}"
	
	class Meta:
		verbose_name = "Regla de Mantenimiento Preventivo"
		verbose_name_plural = "Reglas de Mantenimiento Preventivo"
		ordering = ['-prioridad', 'nombre']


class HistorialMantenimiento(models.Model):
	"""Registro histórico de mantenimientos realizados"""
	ESTADO_CHOICES = [
		('PENDIENTE', 'Pendiente'),
		('EN_PROCESO', 'En Proceso'),
		('COMPLETADO', 'Completado'),
		('CANCELADO', 'Cancelado'),
	]
	
	cruce = models.ForeignKey('Cruce', on_delete=models.CASCADE, related_name='historial_mantenimientos')
	regla = models.ForeignKey('MantenimientoPreventivo', on_delete=models.SET_NULL, null=True, blank=True, related_name='ejecuciones')
	tipo_mantenimiento = models.CharField(max_length=20, choices=MantenimientoPreventivo.TIPO_MANTENIMIENTO_CHOICES)
	prioridad = models.CharField(max_length=10, choices=MantenimientoPreventivo.PRIORIDAD_CHOICES)
	
	# Información del mantenimiento
	descripcion = models.TextField(verbose_name="Descripción del Mantenimiento")
	observaciones = models.TextField(blank=True, verbose_name="Observaciones")
	estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='PENDIENTE')
	
	# Fechas
	fecha_programada = models.DateTimeField(verbose_name="Fecha Programada")
	fecha_inicio = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Inicio")
	fecha_fin = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Finalización")
	
	# Responsable
	responsable = models.CharField(max_length=100, blank=True, verbose_name="Responsable del Mantenimiento")
	
	# Métricas antes y después
	metricas_antes = models.JSONField(default=dict, blank=True, verbose_name="Métricas Antes")
	metricas_despues = models.JSONField(default=dict, blank=True, verbose_name="Métricas Después")
	
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	def __str__(self):
		return f"Mantenimiento {self.cruce.nombre} - {self.get_tipo_mantenimiento_display()} - {self.fecha_programada}"
	
	class Meta:
		verbose_name = "Historial de Mantenimiento"
		verbose_name_plural = "Historial de Mantenimientos"
		ordering = ['-fecha_programada']


class MetricasDesempeno(models.Model):
	"""Métricas de desempeño de los cruces"""
	cruce = models.ForeignKey('Cruce', on_delete=models.CASCADE, related_name='metricas')
	fecha = models.DateField(verbose_name="Fecha de la Métrica")
	
	# Métricas de disponibilidad
	tiempo_activo = models.FloatField(default=0, verbose_name="Tiempo Activo (horas)", help_text="Tiempo que el cruce estuvo operativo")
	tiempo_inactivo = models.FloatField(default=0, verbose_name="Tiempo Inactivo (horas)", help_text="Tiempo que el cruce estuvo fuera de servicio")
	disponibilidad_porcentaje = models.FloatField(default=100, verbose_name="Disponibilidad (%)")
	
	# Métricas de energía
	voltaje_promedio = models.FloatField(null=True, blank=True, verbose_name="Voltaje Promedio (V)")
	voltaje_minimo = models.FloatField(null=True, blank=True, verbose_name="Voltaje Mínimo (V)")
	voltaje_maximo = models.FloatField(null=True, blank=True, verbose_name="Voltaje Máximo (V)")
	horas_bateria_baja = models.FloatField(default=0, verbose_name="Horas con Batería Baja", help_text="Tiempo con voltaje < 11.5V")
	
	# Métricas de eventos
	total_eventos_barrera = models.IntegerField(default=0, verbose_name="Total Eventos de Barrera")
	total_alertas = models.IntegerField(default=0, verbose_name="Total Alertas")
	alertas_criticas = models.IntegerField(default=0, verbose_name="Alertas Críticas")
	alertas_resueltas = models.IntegerField(default=0, verbose_name="Alertas Resueltas")
	
	# Métricas de comunicación
	total_telemetrias = models.IntegerField(default=0, verbose_name="Total Telemetrías Recibidas")
	tiempo_sin_comunicacion = models.FloatField(default=0, verbose_name="Tiempo Sin Comunicación (horas)")
	
	# Métricas de mantenimiento
	mantenimientos_realizados = models.IntegerField(default=0, verbose_name="Mantenimientos Realizados")
	mantenimientos_preventivos = models.IntegerField(default=0, verbose_name="Mantenimientos Preventivos")
	mantenimientos_correctivos = models.IntegerField(default=0, verbose_name="Mantenimientos Correctivos")
	
	# Métricas adicionales (JSON para flexibilidad)
	metricas_adicionales = models.JSONField(default=dict, blank=True, verbose_name="Métricas Adicionales")
	
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	def __str__(self):
		return f"Métricas {self.cruce.nombre} - {self.fecha} - {self.disponibilidad_porcentaje}%"
	
	class Meta:
		verbose_name = "Métrica de Desempeño"
		verbose_name_plural = "Métricas de Desempeño"
		ordering = ['-fecha', 'cruce']
		unique_together = [['cruce', 'fecha']]
		indexes = [
			models.Index(fields=['-fecha', 'cruce'], name='metricas_fecha_cruce_idx'),
			models.Index(fields=['cruce', 'disponibilidad_porcentaje'], name='metricas_cruce_disp_idx'),
		]
