from django.apps import AppConfig


class V2Config(AppConfig):
    name = "v2"

    def ready(self):
        from apps.connector import register_connectors

        register_connectors()
