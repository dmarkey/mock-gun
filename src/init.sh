#!/bin/sh
rm db.sqlite3 || true
python3 manage.py migrate

