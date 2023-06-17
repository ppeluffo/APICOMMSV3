#FROM ubuntu:20.04
#RUN apt-get update && apt-get install -y --no-install-recommends python3.8 python3-pip tzdata && apt-get clean && rm -rf /var/lib/apt/lists/*
#COPY Requirements.txt .
#RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r Requirements.txt

#RUN apt-get update && apt-get install -y tzdata
#RUN cp /usr/share/zoneinfo/America/Montevideo /etc/localtime
#RUN echo "America/Montevideo" >  /etc/timezone
#RUN date 

FROM spymovil/commsv3_imagen_base:latest

WORKDIR /apicomms
COPY apicomms.py .
COPY apicomms_utils_dlg.py .
COPY apicomms_utils_plc.py .
COPY gunicorn.conf.py .
COPY wsgi.py .

#RUN mkdir /var/log/gunicorn
#RUN touch /var/log/gunicorn/apicomms.log && chmod 777 /var/log/gunicorn/apicomms.log

COPY entrypoint.sh .
RUN chmod 777 /apicomms/*
ENTRYPOINT ["sh", "entrypoint.sh"]

EXPOSE 5000

