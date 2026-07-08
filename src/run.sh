#!/bin/sh
python3 manage.py migrate

# The dev server runs threaded (see below) so concurrent requests can hit
# the DB at once. WAL mode lets readers (e.g. the introspection "wait"
# endpoint) proceed without blocking on writers, and keeps writer-vs-writer
# contention from blowing past the busy timeout under concurrent sends.
# journal_mode is persisted in the db file, so this must run every start.
python3 manage.py shell -c "
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('PRAGMA journal_mode=WAL;')
"

if [ -f /data/fixtures.json ] ;
then
    python3 manage.py loaddata /data/fixtures.json
fi

exec python3 manage.py runserver 0.0.0.0:8000 --noreload --insecure
