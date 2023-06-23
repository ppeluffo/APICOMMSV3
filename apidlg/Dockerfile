FROM spymovil/commsv3_imagen_base:latest

WORKDIR /apidlg
COPY apidlg.py .
COPY apidlg_utils.py .
COPY gunicorn.conf.py .
COPY wsgi.py .

COPY entrypoint.sh .
RUN chmod 777 /apidlg/*
ENTRYPOINT ["sh", "entrypoint.sh"]

EXPOSE 5000

