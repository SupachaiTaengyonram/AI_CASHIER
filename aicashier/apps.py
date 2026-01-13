from django.apps import AppConfig


class AicashierConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "aicashier"

    def ready(self):
        
        import aicashier.signals