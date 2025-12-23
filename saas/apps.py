from django.apps import AppConfig


class SaasConfig(AppConfig):
    name = 'saas'

    def ready(self):
        import saas.signals 
