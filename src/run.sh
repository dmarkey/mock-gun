#!/bin/sh
if [ -f /data/fixtures.json ] ;
then
    python manage.py loaddata /data/fixtures.json
fi

exec python manage.py runserver 0.0.0.0:8000 --noreload
