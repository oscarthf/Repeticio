from dotenv import load_dotenv

from django.apps import AppConfig

from language_app_backend.util.db import setup_globals

class PlayerAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'player_app'
    
    def ready(self):
        load_dotenv()
        setup_globals()