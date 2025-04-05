from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class TicketsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tickets'
    verbose_name = _('Tickets')

    def ready(self):
        # Import signals to register them
        import tickets.signals
        import tickets.translation  # This ensures translation.py is loaded