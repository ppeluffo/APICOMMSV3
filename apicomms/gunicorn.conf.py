# gunicorn.conf.py
bind = "0.0.0.0:5000"

# Concurrency
worker_class = "gthread"
workers = 10               # ajusta con pruebas; regla de pulgar: 2–4 x núcleos
threads = 4                # 4–8 suele ir bien; prueba 4, 6 u 8

# Cola de conexiones en ráfaga
backlog = 4096             # por encima del 2048 default

# Timeouts / keep-alive
timeout = 30               # default; ajusta según tus endpoints lentos
keepalive = 2              # efectivo en gthread; como no reutilizan, 1–2s está bien

# Ciclo de vida para mitigar leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
errorlog = "-"             # stderr
accesslog = "-"            # stdout
access_log_format = "%(f)s %(a)s"
loglevel = "info"
