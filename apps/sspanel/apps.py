from django.apps import AppConfig


class SspanelConfig(AppConfig):
    name = "apps.sspanel"

    def ready(self):
        from apps.connector import register_connectors

        register_connectors()
