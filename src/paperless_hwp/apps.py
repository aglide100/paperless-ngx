from django.apps import AppConfig
from paperless_hwp.signals import hwp_consumer_declaration

class PaperlessHwpConfig(AppConfig):
    name = "paperless_hwp"

    def ready(self):
        from documents.signals import document_consumer_declaration

        document_consumer_declaration.connect(hwp_consumer_declaration)
        AppConfig.ready(self)
