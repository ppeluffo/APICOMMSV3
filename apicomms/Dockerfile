FROM ubuntu:20.04
RUN apt-get update && apt-get install -y --no-install-recommends python3.8 python3-pip systemctl && apt-get clean && rm -rf /var/lib/apt/lists/*
COPY Requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r Requirements.txt

WORKDIR /apicomms
COPY apicomms.py .
COPY apicomms_utils_dlg.py .
COPY apicomms_utils_plc.py .
COPY gunicorn.conf.py .
COPY wsgi.py .

RUN mkdir /var/log/gunicorn
RUN touch /var/log/gunicorn/apicomms.log && chmod 777 /var/log/gunicorn/apicomms.log

COPY entrypoint.sh .
RUN chmod 777 /apicomms/*
ENTRYPOINT ["sh", "entrypoint.sh"]

#ENV APICOMMS_HOST $APICOMMS_HOST
#ENV APICOMMS_PORT $APICOMMS_PORT
#ENV APIREDIS_HOST $APIREDIS_HOST
#ENV APIREDIS_PORT $APIREDIS_PORT
#ENV APISQL_HOST $APISQL_HOST
#ENV APISQL_PORT $APISQL_PORT

EXPOSE 5000
