# gunicorn.conf.py

bind = "0.0.0.0:5100"

# Concurrency
worker_class = "gthread"
workers = 8                 # empieza con 2 x núcleos y ajusta con métricas
threads = 6                 # 4–8 va bien para I/O a Redis

# Si usas REDIS_MAX_CONN, apúntalo a >= workers*threads*1.5
# p.ej., con 8*6=48 -> REDIS_MAX_CONN=80..100

# Cola de conexiones en ráfaga
backlog = 4096

# Timeouts / keep-alive
timeout = 30
graceful_timeout = 30       # tiempo para finalizar requests al hacer reload/stop
keepalive = 2

# Ciclo de vida para mitigar leaks
max_requests = 2000
max_requests_jitter = 200

# Carga previa (ahorra memoria por COW; OK porque Redis se inicializa lazy)
preload_app = False

# Logging
errorlog = "-"              # stderr
accesslog = "-"             # stdout
loglevel = "info"

# Formato de access log con status/latencia y XFF si estás detrás de proxy
# %({X-Forwarded-For}i)s = IP real cuando hay proxy
access_log_format = '%({X-Forwarded-For}i)s %(a)s "%(r)s" %(s)s %(b)s %(D)sµs "%({user-agent}i)s"'

# Si hay proxy inverso (Nginx/ALB) y querés honrar X-Forwarded-For:
# forwarded_allow_ips = "*"

# Seguridad y límites defensivos
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190
