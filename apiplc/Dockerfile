FROM spymovil/commsv3_imagen_base:latest

WORKDIR /apiplc
COPY apiplc.py .
COPY apiplcR2_utils.py .
COPY gunicorn.conf.py .
COPY wsgi.py .

COPY entrypoint.sh .
RUN chmod 777 /apiplc/*
ENTRYPOINT ["sh", "entrypoint.sh"]

EXPOSE 5500

