#!/bin/sh
find . -path "*/migrations/*.pyc"  -delete
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
rm db.sqlite3 || true
python manage.py makemigrations main_app
python manage.py migrate

