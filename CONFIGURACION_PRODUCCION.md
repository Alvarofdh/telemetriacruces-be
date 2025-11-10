# 🔒 Configuración de Seguridad para Producción

## ✅ Cambios Realizados

### 1. **DEBUG = False por defecto** ✅
- **Antes:** `DEBUG = os.getenv('DEBUG', 'True')` → Por defecto True (riesgo de seguridad)
- **Ahora:** `DEBUG = os.getenv('DEBUG', 'False')` → Por defecto False (seguro)

**¿Qué significa?**
- En producción, Django NO mostrará información de debug
- Los errores mostrarán páginas genéricas sin exponer detalles del sistema
- Solo se activará DEBUG si explícitamente defines `DEBUG=True` en variables de entorno

### 2. **BrowsableAPIRenderer deshabilitado en producción** ✅
- **Antes:** Siempre habilitado (interfaz web de DRF visible)
- **Ahora:** Solo habilitado cuando `DEBUG=True`

**¿Qué significa?**
- En producción, la API solo devuelve JSON (más seguro)
- No se puede navegar la API desde el navegador
- Solo se puede acceder mediante requests HTTP con autenticación

### 3. **Vista raíz `/` agregada** ✅
- **Antes:** Error 404 al acceder a la raíz
- **Ahora:** Respuesta JSON simple con información básica

**Respuesta de la raíz:**
```json
{
  "service": "API de Monitoreo de Cruces Ferroviarios",
  "version": "1.0.0",
  "endpoints": {
    "api": "/api/",
    "documentation": "/swagger/",
    "admin": "/admin/"
  },
  "message": "Esta es una API REST. Accede a /api/ para ver los endpoints disponibles."
}
```

---

## 🔧 Configuración en CapRover

### Variables de Entorno Necesarias

En tu configuración de CapRover, asegúrate de tener:

```bash
# Producción (seguro)
DEBUG=False

# O simplemente NO definas DEBUG (por defecto será False)
```

**⚠️ IMPORTANTE:** Si defines `DEBUG=True` en CapRover, se activará el modo debug (no recomendado en producción).

---

## 🧪 Verificación

### 1. Verificar que DEBUG está desactivado:

Accede a: `https://viametrica-be.psicosiodev.me/`

**Deberías ver:**
```json
{
  "service": "API de Monitoreo de Cruces Ferroviarios",
  "version": "1.0.0",
  ...
}
```

**NO deberías ver:**
- ❌ Páginas de error con información de debug
- ❌ Stack traces
- ❌ Información de rutas disponibles en errores 404
- ❌ Interfaz BrowsableAPI de DRF

### 2. Verificar que la API funciona:

```bash
# Health check
curl https://viametrica-be.psicosiodev.me/api/health

# Debería devolver:
{
  "status": "ok",
  "message": "API funcionando correctamente",
  ...
}
```

### 3. Verificar que los errores no exponen información:

Accede a una ruta inexistente: `https://viametrica-be.psicosiodev.me/ruta-inexistente`

**Deberías ver:**
- Una página 404 genérica (sin información de debug)
- O un JSON con error simple

**NO deberías ver:**
- ❌ Lista de todas las rutas disponibles
- ❌ Stack traces
- ❌ Información del sistema

---

## 📋 Checklist de Seguridad

- ✅ `DEBUG=False` en producción
- ✅ `BrowsableAPIRenderer` deshabilitado
- ✅ Vista raíz sin información sensible
- ✅ Errores no exponen información del sistema
- ✅ `ALLOWED_HOSTS` configurado correctamente
- ✅ `SECRET_KEY` en variables de entorno (no en código)
- ✅ HTTPS habilitado (`USE_HTTPS=True`)
- ✅ Cookies seguras configuradas

---

## 🚀 Despliegue

Después de estos cambios:

1. **Hacer commit:**
```bash
git add config/settings.py config/urls.py
git commit -m "Configurar seguridad para producción: DEBUG=False, vista raíz, deshabilitar BrowsableAPI"
git push origin main
```

2. **Desplegar en CapRover:**
```bash
caprover deploy
```

3. **Verificar en producción:**
- Acceder a `https://viametrica-be.psicosiodev.me/`
- Verificar que no se muestre información de debug
- Probar endpoints de la API

---

## 🔍 Troubleshooting

### Si aún ves información de debug:

1. **Verificar variable de entorno en CapRover:**
   - Ve a tu app en CapRover
   - Verifica que `DEBUG` NO esté definido o esté en `False`

2. **Reiniciar la aplicación:**
   - En CapRover, reinicia el contenedor

3. **Verificar logs:**
   - Revisa los logs de CapRover para ver si hay errores

### Si la vista raíz no funciona:

1. **Verificar que el código se desplegó correctamente**
2. **Revisar logs de CapRover**
3. **Verificar que `config/urls.py` tiene la ruta raíz**

---

## 📝 Notas

- **Desarrollo local:** Si quieres DEBUG=True localmente, define `DEBUG=True` en tu `.env`
- **Producción:** Nunca uses `DEBUG=True` en producción
- **BrowsableAPI:** Solo disponible en desarrollo (cuando DEBUG=True)

