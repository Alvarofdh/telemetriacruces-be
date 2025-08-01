# Cursor Rules - Sistema de Monitoreo de Cruces Ferroviarios

## Contexto del Proyecto
Este es un sistema de monitoreo en tiempo real para cruces ferroviarios que utiliza:
- **Hardware**: PLC DVP28SV + ESP32-WROOM
- **Backend**: Django + Django REST Framework
- **Base de Datos**: PostgreSQL
- **Funcionalidad**: Monitoreo de barreras, telemetría de sensores, alertas automáticas

## Arquitectura y Componentes

### 1. Modelos de Datos
Al trabajar con modelos Django, SIEMPRE seguir esta estructura:

**Telemetria** (tabla principal de lecturas):
```python
class Telemetria(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    barrier_voltage = models.FloatField()  # Voltaje de barrera del PLC
    battery_voltage = models.FloatField()  # Voltaje de batería
    sensor_1 = models.IntegerField(null=True, blank=True)  # Sensores adicionales
    sensor_2 = models.IntegerField(null=True, blank=True)
    # Agregar campos según necesidad
```

**BarrierEvent** (eventos de cambio de estado):
```python
class BarrierEvent(models.Model):
    STATE_CHOICES = [
        ('DOWN', 'Barrera Abajo'),
        ('UP', 'Barrera Arriba'),
    ]
    telemetria = models.ForeignKey(Telemetria, on_delete=models.CASCADE)
    state = models.CharField(max_length=4, choices=STATE_CHOICES)
    event_time = models.DateTimeField()
```

**Alerta** (notificaciones del sistema):
```python
class Alerta(models.Model):
    ALERT_TYPES = [
        ('LOW_BATTERY', 'Batería Baja'),
        ('SENSOR_ERROR', 'Error de Sensor'),
        ('BARRIER_STUCK', 'Barrera Bloqueada'),
    ]
    type = models.CharField(max_length=20, choices=ALERT_TYPES)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    telemetria = models.ForeignKey(Telemetria, on_delete=models.SET_NULL, null=True, blank=True)
    resolved = models.BooleanField(default=False)
```

### 2. API Endpoints Requeridos
SIEMPRE implementar estos endpoints con Django REST Framework:

- `POST /api/telemetria/` - Recibir datos del ESP32
- `POST /api/barrier-event/` - Registrar eventos de barrera
- `POST /api/alertas/` - Crear alertas
- `GET /api/telemetria/` - Consultar telemetría
- `GET /api/barrier-event/` - Consultar eventos
- `GET /api/alertas/` - Consultar alertas

### 3. Validaciones Críticas

**En TelemetriaSerializer**:
- `barrier_voltage`: rango 0-24V (típico para PLC)
- `battery_voltage`: rango 10-15V (batería 12V con tolerancia)
- Timestamps coherentes
- Valores de sensores dentro de rangos ADC (0-1023 para 10-bit)

**En BarrierEventSerializer**:
- No permitir eventos duplicados en menos de 2 segundos
- Validar transiciones lógicas (UP → DOWN → UP)
- `event_time` no puede ser futuro

**En AlertaSerializer**:
- Tipos de alerta válidos según ALERT_TYPES
- Descripción no vacía
- Telemetría referenciada debe existir

### 4. Lógica de Negocio Específica

**Detección de Eventos**:
```python
# En la vista de telemetría, después de guardar:
def detect_barrier_event(telemetria_instance):
    # Lógica para detectar cambio de estado
    # barrier_voltage > 2.0V = DOWN, < 2.0V = UP
    # Crear BarrierEvent automáticamente
```

**Generación de Alertas**:
```python
# Reglas de alertas automáticas
def check_alerts(telemetria_instance):
    if telemetria_instance.battery_voltage < 11.0:
        create_alert('LOW_BATTERY', f'Voltaje: {telemetria_instance.battery_voltage}V')
    
    # Verificar si barrera lleva mucho tiempo en un estado
    # Verificar sensores fuera de rango
```

### 5. Convenciones de Código

**Nombres de Variables**:
- `barrier_voltage` (no `barrierVoltage`)
- `event_time` (no `eventTime`)
- `created_at` (timestamp estándar)

**Estructura de Respuestas JSON**:
```json
{
  "id": 123,
  "timestamp": "2025-01-24T10:30:00Z",
  "barrier_voltage": 3.3,
  "battery_voltage": 12.5,
  "sensor_1": 1023,
  "sensor_2": 350
}
```

**Manejo de Errores**:
- Usar códigos HTTP apropiados (400, 404, 500)
- Mensajes de error en español
- Log de errores críticos para debugging

### 6. Testing

**Tests Obligatorios**:
- POST a `/api/telemetria/` con datos válidos e inválidos
- Creación automática de BarrierEvent
- Generación de alertas por reglas de negocio
- Validaciones de rangos de sensores
- Tests de integración ESP32 → API

### 7. Configuración del Proyecto

**Settings.py consideraciones**:
- `TIME_ZONE = 'America/Santiago'` (ajustar según ubicación)
- `LANGUAGE_CODE = 'es-es'`
- Configuración CORS para ESP32
- Rate limiting para endpoints públicos

**Variables de Entorno**:
```
DB_NAME=cruces_ferroviarios
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432
DEBUG=False
SECRET_KEY=tu_secret_key_segura
```

### 8. Documentación API

SIEMPRE usar `drf-yasg` para documentación automática:
- Describir cada endpoint con ejemplos
- Documentar códigos de respuesta
- Incluir ejemplos de payloads ESP32

### 9. Monitoreo y Logging

**Logs Importantes**:
- Cada telemetría recibida (nivel INFO)
- Eventos de barrera (nivel WARNING)
- Alertas generadas (nivel ERROR)
- Errores de comunicación ESP32 (nivel CRITICAL)

### 10. Reglas Específicas del Hardware

**ESP32 Considerations**:
- Timeout de 30 segundos para requests HTTP
- Retry automático en caso de falla de red
- Buffer local para datos críticos
- Validación de JSON antes de envío

**PLC Integration**:
- Señal digital: 24V = DOWN, 0V = UP
- Lectura cada 500ms mínimo
- Debounce de 100ms para evitar falsos positivos

## Comandos Útiles
```bash
# Migraciones
python manage.py makemigrations api
python manage.py migrate

# Tests
python manage.py test apps.api

# Crear superuser
python manage.py createsuperuser

# Ejecutar servidor
python manage.py runserver 0.0.0.0:8000
```

## Notas Finales
- SIEMPRE priorizar la precisión de los eventos de barrera
- Implementar redundancia en alertas críticas
- Mantener logs detallados para debugging
- Considerar backup automático de datos críticos
- Validar TODAS las entradas del ESP32 