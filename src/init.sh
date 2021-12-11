#!/bin/sh
rm db.sqlite3 || true
python manage.py migrate

