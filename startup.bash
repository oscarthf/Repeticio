python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runserver --insecure 0.0.0.0:8000