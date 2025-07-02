# Sistema de Monitoreo de Cruces Ferroviarios

Backend Django para el sistema de monitoreo en tiempo real de cruces ferroviarios con ESP32 y PostgreSQL.

## 🚀 Características

- **Monitoreo en Tiempo Real**: Telemetría de sensores PLC y ESP32
- **Detección Automática de Eventos**: Cambios de estado de barreras
- **Sistema de Alertas**: Notificaciones automáticas por condiciones críticas
- **API REST**: Documentada con Swagger
- **Autenticación JWT**: Segura y escalable
- **Dashboard**: Resumen de cruces y alertas activas

## 🛠️ Tecnologías

- **Backend**: Django 5.2.3 + Django REST Framework
- **Base de Datos**: PostgreSQL
- **Autenticación**: JWT (djangorestframework-simplejwt)
- **Documentación**: Swagger (drf-yasg)
- **Hardware**: ESP32 + PLC DVP28SV

## 📋 Requisitos

- Python 3.11+
- PostgreSQL 12+
- Microsoft C++ Build Tools (Windows)

## 🔧 Instalación

1. **Clonar el repositorio**
```bash
git clone <url-del-repositorio>
cd telemetriacruces-be-main
```

2. **Crear entorno virtual**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar base de datos**
```sql
CREATE DATABASE cruces_ferroviarios;
```

5. **Configurar variables de entorno**
Crear archivo `.env` en la raíz del proyecto:
```env
DB_NAME=cruces_ferroviarios
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=tu-clave-secreta
DEBUG=True
```

6. **Ejecutar migraciones**
```bash
python manage.py migrate
```

7. **Crear superusuario**
```bash
python manage.py createsuperuser
```

8. **Generar datos de prueba**
```bash
python manage.py create_test_data
```

9. **Ejecutar servidor**
```bash
python manage.py runserver
```

## 📡 Endpoints Principales

### Autenticación
- `POST /api/register` - Registro de usuarios
- `POST /api/login` - Login con JWT
- `POST /api/logout` - Logout
- `GET /api/profile` - Perfil de usuario

### Dashboard
- `GET /api/cruces/dashboard/` - Resumen de cruces
- `GET /api/alertas/dashboard/` - Resumen de alertas

### CRUD
- `GET/POST /api/cruces/` - Gestión de cruces
- `GET/POST /api/telemetria/` - Telemetría
- `GET/POST /api/alertas/` - Alertas
- `GET/POST /api/sensores/` - Sensores

### Utilidad
- `GET /api/health` - Health check
- `GET /swagger/` - Documentación API

## 🔌 Integración ESP32

### Endpoint para telemetría
```
POST /api/telemetria/
Content-Type: application/json

{
  "cruce": 1,
  "barrier_voltage": 3.3,
  "battery_voltage": 12.5,
  "sensor_1": 1023,
  "sensor_2": 350
}
```

## 📊 Estructura de Datos

### Cruce
- Nombre, ubicación, coordenadas
- Estado (ACTIVO/INACTIVO)

### Telemetría
- Voltajes de barrera y batería
- Lecturas de sensores
- Estado calculado de barrera

### Alerta
- Tipos: LOW_BATTERY, VOLTAGE_CRITICAL, etc.
- Estado resuelto/pendiente
- Relación con telemetría y cruce

## 🚨 Alertas Automáticas

- **Batería baja**: < 11.0V
- **Voltaje crítico PLC**: < 20.0V
- **Gabinete abierto**: sensor_1 > 500
- **Comunicación perdida**: Timeout

## 🔒 Seguridad

- Autenticación JWT obligatoria
- Validación de rangos de voltaje
- Prevención de eventos duplicados
- Logs de auditoría

## 📝 Desarrollo

### Comandos útiles
```bash
# Crear migraciones
python manage.py makemigrations api

# Ejecutar tests
python manage.py test apps.api

# Generar datos de prueba
python manage.py create_test_data
```

### Estructura del proyecto
```
telemetriacruces-be-main/
├── apps/
│   └── api/           # Aplicación principal
├── config/            # Configuración Django
├── database/          # Scripts SQL
├── .cursor-rules/     # Reglas del proyecto
└── requirements.txt   # Dependencias
```
