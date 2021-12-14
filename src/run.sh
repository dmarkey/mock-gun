#!/bin/sh
if [ -f /data/fixtures.json ] ;
then
    python3 manage.py loaddata /data/fixtures.json
fi

exec python3 manage.py runserver 0.0.0.0:8000 --noreload --nothreading --insecure
