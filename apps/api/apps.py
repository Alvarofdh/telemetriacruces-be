from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'  # type: ignore
    name = 'apps.api'
    verbose_name = 'API de Monitoreo de Cruces Ferroviarios'