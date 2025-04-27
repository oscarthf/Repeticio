web: bash -c "python manage.py collectstatic --noinput && gunicorn --config gunicorn_config.py language_app.wsgi:application --bind 0.0.0.0:8000"
