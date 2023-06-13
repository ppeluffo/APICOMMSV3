#!/bin/bash

exec gunicorn -c gunicorn.conf.py --bind 0.0.0.0:5200 wsgi:app "$@"
