from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'api'

# Configurar router para ViewSets
router = DefaultRouter()
router.register(r'cruces', views.CruceViewSet, basename='cruce')
router.register(r'sensores', views.SensorViewSet, basename='sensor')
router.register(r'telemetria', views.TelemetriaViewSet, basename='telemetria')
router.register(r'barrier-events', views.BarrierEventViewSet, basename='barrier-event')
router.register(r'alertas', views.AlertaViewSet, basename='alerta')

urlpatterns = [
    # Endpoints básicos
    path('', views.api_root, name='api-root'),
    path('health', views.health_check, name='health-check'),
    
    # Endpoints de autenticación
    path('login', views.login_view, name='login'),
    path('logout', views.logout_view, name='logout'),
    path('register', views.register_view, name='register'),
    path('profile', views.profile_view, name='profile'),
    
    # Endpoint público para ESP32 (sin autenticación JWT)
    path('esp32/telemetria', views.esp32_telemetria, name='esp32-telemetria'),
    
    # Incluir URLs de ViewSets (incluye automáticamente las rutas @action)
    path('', include(router.urls)),
] 