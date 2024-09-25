web: gunicorn climbers_eye_backend.wsgi
release: python3 manage.py makemigrations --noinput && python3 manage.py migrate --noinput && python3 manage.py collectstatic --noinput
