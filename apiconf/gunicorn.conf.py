#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python

#import multiprocessing

import multiprocessing

max_requests = 1000
max_requests_jitter = 50
# Si queremos el log en stdout
log_file = "-"
#workers = multiprocessing.cpu_count() * 2 + 1
workers = 5
bind = '0.0.0.0:5200'
#worker_class = 'sync'
loglevel = 'info'
#accesslog = '/var/log/gunicorn/apiredis.log'
#acceslogformat ="%(h)s %(l)s %(u)s %(t)s %(r)s %(s)s %(b)s %(f)s %(a)s"
acceslogformat =""
#errorlog =  '/var/log/gunicorn/apiredis.log'