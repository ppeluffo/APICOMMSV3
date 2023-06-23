#!/bin/bash

exec gunicorn -c gunicorn.conf.py --bind 0.0.0.0:5500 wsgi:app "$@"

