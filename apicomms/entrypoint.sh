#!/bin/bash

# Prepare log files and start outputting logs to stdout
#mkdir -p /var/log/gunicorn
#touch /var/log/gunicorn/apicomms.log
#tail -n 0 -f /var/log/gunicorn/apicomms.log &

exec gunicorn -c gunicorn.conf.py --bind 0.0.0.0:5000 wsgi:app "$@"

