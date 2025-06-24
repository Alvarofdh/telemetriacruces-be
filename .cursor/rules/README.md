# Cursor Rules - Sistema de Monitoreo de Cruces Ferroviarios

Esta carpeta contiene todas las reglas específicas para el proyecto de monitoreo de cruces ferroviarios.

## 📁 Estructura de Archivos

### `cruces-ferroviarios.md`
Reglas principales del sistema de monitoreo que incluyen:
- Modelos de datos (Telemetria, BarrierEvent, Alerta)
- API endpoints requeridos
- Validaciones críticas
- Lógica de negocio específica
- Convenciones de código
- Configuración del proyecto

## 🚀 Cómo usar las reglas

1. **Regla principal activa**: `cruces-ferroviarios.md`
2. **Para agregar nuevas reglas**: Crear archivos `.md` adicionales en esta carpeta
3. **Para reglas específicas**: Crear archivos temáticos (ej: `testing.md`, `hardware.md`, `deployment.md`)

## 📋 Reglas futuras sugeridas

- `testing-rules.md` - Reglas específicas para testing
- `hardware-integration.md` - Reglas para integración ESP32/PLC
- `deployment.md` - Reglas para despliegue y producción
- `security.md` - Reglas de seguridad específicas
- `monitoring.md` - Reglas para monitoreo y alertas

## 🔄 Activación de reglas

Para activar una regla específica, copia el contenido del archivo `.md` al archivo `.cursorrules` en la raíz del proyecto:

```bash
cp .cursor-rules/cruces-ferroviarios.md .cursorrules
```

## 📝 Convenciones

- Todos los archivos en formato Markdown (`.md`)
- Nombres descriptivos en español
- Estructura consistente con headers y ejemplos de código
- Documentación clara y específica para el dominio ferroviario 