from dotenv import load_dotenv

from django.apps import AppConfig

is_collecting_static = False

try:
    from language_app_backend.util.db import setup_globals
except ImportError:
    print("ImportError: language_app_backend not found. ")
    is_collecting_static = True

class PlayerAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'player_app'
    
    def ready(self):
        if not is_collecting_static:
            load_dotenv()
            setup_globals()