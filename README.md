# 🚂 Sistema de Monitoreo de Cruces Ferroviarios

Sistema de monitoreo en tiempo real para cruces ferroviarios que combina hardware IoT (ESP32 + PLC Delta) con backend Django y frontend React.

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Arquitectura](#-arquitectura)
- [Tecnologías](#-tecnologías)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [API Endpoints](#-api-endpoints)
- [Uso del ESP32](#-uso-del-esp32)
- [Ejemplos de Uso](#-ejemplos-de-uso)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Contribución](#-contribución)

## 🚀 Características

- **Monitoreo en tiempo real** de cruces ferroviarios
- **Detección automática** de eventos de barrera (UP/DOWN)
- **Sistema de alertas** automáticas (batería baja, gabinete abierto, etc.)
- **API REST** completa con autenticación JWT
- **Endpoint específico** para ESP32 (sin JWT)
- **Validaciones específicas** del hardware ferroviario
- **Logging detallado** para debugging
- **Documentación automática** con Swagger

## 🏗️ Arquitectura

```
┌─────────────┐    HTTP     ┌─────────────┐    HTTP     ┌─────────────┐
│    ESP32    │ ──────────► │   Django    │ ◄────────── │    React    │
│             │            │   Backend   │             │   Frontend  │
│  + PLC      │            │             │             │             │
│  Delta      │            │  PostgreSQL │             │             │
└─────────────┘            └─────────────┘             └─────────────┘
```

### Componentes:

- **ESP32-WROOM**: Microcontrolador que lee datos del PLC
- **PLC Delta DVP28SV11R2**: Controlador lógico programable
- **Django Backend**: API REST con lógica de negocio
- **PostgreSQL**: Base de datos para almacenar telemetría
- **React Frontend**: Dashboard web para visualización

## 🛠️ Tecnologías

### Backend
- **Django 5.2** - Framework web
- **Django REST Framework** - API REST
- **PostgreSQL** - Base de datos
- **JWT** - Autenticación
- **Swagger** - Documentación API

### Frontend
- **React** - Framework frontend
- **Axios** - Cliente HTTP

### Hardware
- **ESP32-WROOM** - Microcontrolador
- **PLC Delta DVP28SV11R2** - Controlador lógico

## 📦 Instalación

### Prerrequisitos
- Python 3.8+
- PostgreSQL 12+
- Node.js 16+ (para React)

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/telemetriacruces-be.git
cd telemetriacruces-be
```

### 2. Crear entorno virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar base de datos
```bash
# Crear base de datos PostgreSQL
createdb cruces_ferroviarios

# Ejecutar migraciones
python manage.py migrate
```

### 5. Crear superusuario
```bash
python manage.py createsuperuser
```

### 6. Ejecutar servidor
```bash
python manage.py runserver
```

## ⚙️ Configuración

### Variables de Entorno
Crear archivo `.env` en la raíz del proyecto:

```env
# Base de datos
DB_NAME=cruces_ferroviarios
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432

# Django
SECRET_KEY=tu_secret_key_segura
DEBUG=True

# ESP32
ESP32_TOKEN=esp32_default_token_123
```

### Configuración del ESP32
```python
# Token de autenticación para ESP32
ESP32_TOKEN = "esp32_default_token_123"

# URL del servidor
API_URL = "http://tu-servidor:8000/api/esp32/telemetria"
```

## 📡 API Endpoints

### Endpoints Públicos (Sin Autenticación)

| Método | Endpoint | Descripción | Usuario |
|--------|----------|-------------|---------|
| GET | `/api/` | Lista de endpoints disponibles | Todos |
| GET | `/api/health` | Estado de salud de la API | Todos |
| POST | `/api/login` | Iniciar sesión | React/Admin |
| POST | `/api/register` | Registrar usuario | React/Admin |
| POST | `/api/esp32/telemetria` | Enviar datos del ESP32 | ESP32 |

### Endpoints Protegidos (Con JWT)

| Método | Endpoint | Descripción | Usuario |
|--------|----------|-------------|---------|
| GET | `/api/telemetria/` | Consultar telemetría | React/Admin |
| GET | `/api/cruces/` | Lista de cruces | React/Admin |
| GET | `/api/cruces/{id}/` | Detalles de cruce | React/Admin |
| GET | `/api/cruces/dashboard/` | Dashboard general | React/Admin |
| GET | `/api/alertas/` | Consultar alertas | React/Admin |
| GET | `/api/alertas/dashboard/` | Dashboard de alertas | React/Admin |
| GET | `/api/barrier-events/` | Eventos de barrera | React/Admin |

## 🔌 Uso del ESP32

### Estructura de Datos
El ESP32 debe enviar datos en formato JSON:

```json
{
  "esp32_token": "esp32_default_token_123",
  "cruce_id": 1,
  "barrier_voltage": 3.3,
  "battery_voltage": 12.5,
  "sensor_1": 1023,
  "sensor_2": 350,
  "sensor_3": null,
  "sensor_4": null,
  "signal_strength": -45,
  "temperature": 25.5
}
```

### Validaciones
- **barrier_voltage**: 0-24V (PLC Delta)
- **battery_voltage**: 10-15V (batería 12V)
- **sensor_1/2/3/4**: 0-1023 (ADC 10-bit)
- **esp32_token**: Token de autenticación

### Ejemplo de Código ESP32 (Arduino)
```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

const char* ssid = "tu_wifi";
const char* password = "tu_password";
const char* serverURL = "http://tu-servidor:8000/api/esp32/telemetria";
const char* esp32Token = "esp32_default_token_123";

void enviarTelemetria() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverURL);
    http.addHeader("Content-Type", "application/json");
    
    // Crear JSON
    DynamicJsonDocument doc(1024);
    doc["esp32_token"] = esp32Token;
    doc["cruce_id"] = 1;
    doc["barrier_voltage"] = leerVoltajeBarrera();
    doc["battery_voltage"] = leerVoltajeBateria();
    doc["sensor_1"] = leerSensor1();
    doc["sensor_2"] = leerSensor2();
    doc["signal_strength"] = WiFi.RSSI();
    doc["temperature"] = leerTemperatura();
    
    String jsonString;
    serializeJson(doc, jsonString);
    
    int httpCode = http.POST(jsonString);
    
    if (httpCode > 0) {
      String response = http.getString();
      Serial.println("Respuesta: " + response);
    }
    
    http.end();
  }
}
```

## 📊 Ejemplos de Uso

### 1. Login y Obtener Token
```bash
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@ejemplo.com",
    "password": "mi_password"
  }'
```

### 2. Enviar Datos desde ESP32
```bash
curl -X POST http://localhost:8000/api/esp32/telemetria \
  -H "Content-Type: application/json" \
  -d '{
    "esp32_token": "esp32_default_token_123",
    "cruce_id": 1,
    "barrier_voltage": 3.3,
    "battery_voltage": 12.5,
    "sensor_1": 1023
  }'
```

### 3. Consultar Dashboard
```bash
curl http://localhost:8000/api/cruces/dashboard/ \
  -H "Authorization: Bearer tu_token_jwt"
```

### 4. Ver Alertas Activas
```bash
curl "http://localhost:8000/api/alertas/?resuelta=false" \
  -H "Authorization: Bearer tu_token_jwt"
```

## 📁 Estructura del Proyecto

```
telemetriacruces-be/
├── apps/
│   └── api/
│       ├── models.py          # Modelos de datos
│       ├── serializers.py    # Serializers para API
│       ├── views.py          # Vistas y endpoints
│       ├── urls.py           # URLs de la API
│       ├── admin.py          # Configuración admin
│       ├── socketio_app.py   # Socket.IO server
│       └── management/
│           └── commands/     # Comandos de gestión
├── config/
│   ├── settings.py           # Configuración Django
│   ├── urls.py              # URLs principales
│   ├── asgi.py              # ASGI configuration (Socket.IO)
│   └── wsgi.py              # WSGI configuration
├── database/
│   └── setup_basico.sql      # Scripts de base de datos
├── logs/                     # Archivos de log
├── requirements.txt          # Dependencias Python
├── manage.py                # Script de gestión Django
├── start_prod.sh            # Script de inicio producción
├── start_dev.sh             # Script de inicio desarrollo
└── README.md               # Este archivo
```

## 🔧 Lógica de Negocio

### Detección de Eventos
- **Barrera DOWN**: `barrier_voltage > 2.0V`
- **Barrera UP**: `barrier_voltage < 2.0V`
- **Prevención de duplicados**: No eventos en < 2 segundos

### Alertas Automáticas
- **Batería baja**: `battery_voltage < 11.0V`
- **Voltaje crítico PLC**: `barrier_voltage < 20.0V`
- **Gabinete abierto**: `sensor_1 > 500`

## 📝 Logging

El sistema genera logs detallados en `logs/telemetria.log`:

```
INFO 2024-01-24 10:30:00 ESP32 - Telemetría recibida: Cruce Central, ID 123, Barrier: 3.3V, Battery: 12.5V
WARNING 2024-01-24 10:31:00 ESP32 - Datos inválidos: {'esp32_token': ['Token de ESP32 inválido']}
ERROR 2024-01-24 10:32:00 ESP32 - Error en detección de eventos: Cruce no encontrado
```

## 🚀 Despliegue

### Desarrollo
```bash
python manage.py runserver 0.0.0.0:8000
```

### Producción
```bash
# Configurar variables de entorno en archivo .env
# DEBUG=False
# SECRET_KEY=tu_secret_key_produccion
# ESP32_TOKEN=token_super_secreto_produccion

# Ejecutar script de producción
./start_prod.sh
```

**Nota**: El script `start_prod.sh` usa Gunicorn con Uvicorn workers para soportar Socket.IO en producción.

## 📚 Documentación API

La documentación completa está disponible en:
- **Swagger UI**: `http://localhost:8000/swagger/`
- **ReDoc**: `http://localhost:8000/redoc/`

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 👥 Autores

- **Tu Nombre** - *Desarrollo Backend* - [tu-github](https://github.com/tu-usuario)
- **Tu Amigo** - *Desarrollo Frontend* - [amigo-github](https://github.com/amigo-usuario)

## 📞 Contacto

- **Email**: tu-email@ejemplo.com
- **Proyecto**: [https://github.com/tu-usuario/telemetriacruces-be](https://github.com/tu-usuario/telemetriacruces-be)

---

## 🎯 Características Implementadas

- ✅ WebSockets con Socket.IO para tiempo real
- ✅ Sistema de notificaciones en tiempo real
- ✅ Rate limiting implementado
- ✅ Configuración de producción lista
- ✅ Sistema de alertas automáticas
- ✅ Monitoreo 24/7 con actualizaciones en tiempo real

---

**¡Gracias por usar el Sistema de Monitoreo de Cruces Ferroviarios!** 🚂✨
