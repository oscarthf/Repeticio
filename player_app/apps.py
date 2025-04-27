import os
from dotenv import load_dotenv

from django.apps import AppConfig

from language_app_backend.util.db import setup_globals

class PlayerAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'player_app'
    
    def ready(self):
        load_dotenv()
        if os.environ.get('RUN_MAIN'):
            try:
                setup_globals()
            except Exception as e:
                print(f"Error setting up globals: {e}")
                raise e