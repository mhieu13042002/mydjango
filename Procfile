web: python manage.py migrate --noinput && python manage.py seed_categories && python manage.py collectstatic --noinput && gunicorn config.wsgi --bind 0.0.0.0:$PORT --log-file -
