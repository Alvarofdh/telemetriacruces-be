from django.contrib import admin
from .models import (
    Cruce, Sensor, Telemetria, BarrierEvent, Alerta,
    UserProfile, UserNotificationSettings
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
    list_display = ('nombre', 'ubicacion', 'estado', 'created_at')
    list_filter = ('estado', 'created_at')
    search_fields = ('nombre', 'ubicacion')


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
