from django.apps import AppConfig


class SspanelConfig(AppConfig):
    name = "apps.sspanel"
    verbose_name = "面板配置"

    def ready(self):
        from apps.connector import register_connectors

        register_connectors()
