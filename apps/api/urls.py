from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    # Endpoints básicos
    path('', views.api_root, name='api-root'),
    path('health', views.health_check, name='health-check'),
    
    # Endpoints de autenticación
    path('login', views.login_view, name='login'),
    path('logout', views.logout_view, name='logout'),
    path('register', views.register_view, name='register'),
    path('profile', views.profile_view, name='profile'),
] 