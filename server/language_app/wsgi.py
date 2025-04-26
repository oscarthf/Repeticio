"""
WSGI config for language_app project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

cwd = os.getcwd()
print(f"Current working directory: {cwd}")
list_of_files = os.listdir(cwd)
print(f"List of files in the current directory: {list_of_files}")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'language_app.settings')

application = get_wsgi_application()
