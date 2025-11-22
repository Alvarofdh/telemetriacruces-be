from django.contrib import admin
from .models import (
    Cruce, Sensor, Telemetria, BarrierEvent, Alerta,
    UserProfile, UserNotificationSettings,
    MantenimientoPreventivo, HistorialMantenimiento, MetricasDesempeno
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin para perfiles de usuario"""
    list_display = ('user', 'role', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Cruce)
class CruceAdmin(admin.ModelAdmin):
    """Admin para cruces"""
    list_display = ('nombre', 'ubicacion', 'estado', 'responsable_nombre', 'responsable_telefono', 'created_at')
    list_filter = ('estado', 'created_at')
    search_fields = ('nombre', 'ubicacion', 'responsable_nombre', 'responsable_empresa')
    fieldsets = (
        ('Información del Cruce', {
            'fields': ('nombre', 'ubicacion', 'estado')
        }),
        ('Coordenadas', {
            'fields': ('coordenadas_lat', 'coordenadas_lng')
        }),
        ('Contacto del Responsable', {
            'fields': (
                'responsable_nombre',
                'responsable_telefono',
                'responsable_email',
                'responsable_empresa',
                'responsable_horario',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    """Admin para sensores"""
    list_display = ('nombre', 'tipo', 'cruce', 'activo', 'created_at')
    list_filter = ('tipo', 'activo', 'created_at')
    search_fields = ('nombre', 'cruce__nombre')


@admin.register(Telemetria)
class TelemetriaAdmin(admin.ModelAdmin):
    """Admin para telemetría"""
    list_display = ('cruce', 'timestamp', 'barrier_voltage', 'battery_voltage', 'barrier_status')
    list_filter = ('timestamp', 'barrier_status', 'cruce')
    search_fields = ('cruce__nombre',)
    readonly_fields = ('timestamp',)


@admin.register(BarrierEvent)
class BarrierEventAdmin(admin.ModelAdmin):
    """Admin para eventos de barrera"""
    list_display = ('cruce', 'state', 'event_time', 'voltage_at_event')
    list_filter = ('state', 'event_time', 'cruce')
    search_fields = ('cruce__nombre',)
    readonly_fields = ('event_time',)


@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    """Admin para alertas"""
    list_display = ('type', 'severity', 'cruce', 'resolved', 'created_at')
    list_filter = ('type', 'severity', 'resolved', 'created_at')
    search_fields = ('description', 'cruce__nombre')
    readonly_fields = ('created_at', 'resolved_at')


@admin.register(UserNotificationSettings)
class UserNotificationSettingsAdmin(admin.ModelAdmin):
    """Admin para configuración de notificaciones"""
    list_display = ('user', 'enable_notifications', 'notification_frequency', 'created_at')
    list_filter = ('enable_notifications', 'notification_frequency', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(MantenimientoPreventivo)
class MantenimientoPreventivoAdmin(admin.ModelAdmin):
    """Admin para reglas de mantenimiento preventivo"""
    list_display = ('nombre', 'tipo_mantenimiento', 'prioridad', 'activo', 'cruce', 'created_at')
    list_filter = ('tipo_mantenimiento', 'prioridad', 'activo', 'created_at')
    search_fields = ('nombre', 'descripcion', 'cruce__nombre')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'descripcion', 'tipo_mantenimiento', 'prioridad', 'activo', 'cruce')
        }),
        ('Condiciones', {
            'fields': ('condiciones',),
            'description': 'JSON con las condiciones que deben cumplirse'
        }),
        ('Acciones', {
            'fields': ('acciones',),
            'description': 'JSON con las acciones a realizar cuando se active'
        }),
        ('Configuración de Alertas', {
            'fields': ('generar_alerta', 'tipo_alerta', 'severidad_alerta')
        }),
        ('Configuración de Fechas', {
            'fields': ('fecha_inicio', 'fecha_fin', 'dias_semana')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(HistorialMantenimiento)
class HistorialMantenimientoAdmin(admin.ModelAdmin):
    """Admin para historial de mantenimientos"""
    list_display = ('cruce', 'tipo_mantenimiento', 'prioridad', 'estado', 'fecha_programada', 'responsable', 'created_at')
    list_filter = ('tipo_mantenimiento', 'prioridad', 'estado', 'fecha_programada', 'created_at')
    search_fields = ('cruce__nombre', 'descripcion', 'responsable')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'fecha_programada'
    fieldsets = (
        ('Información Básica', {
            'fields': ('cruce', 'regla', 'tipo_mantenimiento', 'prioridad', 'estado')
        }),
        ('Descripción', {
            'fields': ('descripcion', 'observaciones')
        }),
        ('Fechas', {
            'fields': ('fecha_programada', 'fecha_inicio', 'fecha_fin')
        }),
        ('Responsable', {
            'fields': ('responsable',)
        }),
        ('Métricas', {
            'fields': ('metricas_antes', 'metricas_despues')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(MetricasDesempeno)
class MetricasDesempenoAdmin(admin.ModelAdmin):
    """Admin para métricas de desempeño"""
    list_display = ('cruce', 'fecha', 'disponibilidad_porcentaje', 'voltaje_promedio', 'total_alertas', 'created_at')
    list_filter = ('fecha', 'created_at')
    search_fields = ('cruce__nombre',)
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'fecha'
    fieldsets = (
        ('Información Básica', {
            'fields': ('cruce', 'fecha')
        }),
        ('Disponibilidad', {
            'fields': ('tiempo_activo', 'tiempo_inactivo', 'disponibilidad_porcentaje')
        }),
        ('Energía', {
            'fields': ('voltaje_promedio', 'voltaje_minimo', 'voltaje_maximo', 'horas_bateria_baja')
        }),
        ('Eventos', {
            'fields': ('total_eventos_barrera', 'total_alertas', 'alertas_criticas', 'alertas_resueltas')
        }),
        ('Comunicación', {
            'fields': ('total_telemetrias', 'tiempo_sin_comunicacion')
        }),
        ('Mantenimiento', {
            'fields': ('mantenimientos_realizados', 'mantenimientos_preventivos', 'mantenimientos_correctivos')
        }),
        ('Métricas Adicionales', {
            'fields': ('metricas_adicionales',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
