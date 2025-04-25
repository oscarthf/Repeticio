from django.apps import AppConfig

from language_app_backend.util.db import setup_globals

class PlayerAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'player_app'
    
    def ready(self):
        # put your startup code here

        setup_globals()