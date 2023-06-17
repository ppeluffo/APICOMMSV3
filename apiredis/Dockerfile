#ROM ubuntu:20.04
#RUN apt-get update && apt-get install -y --no-install-recommends python3.8 python3-pip tzdata && apt-get clean && rm -rf /var/lib/apt/lists/*
#COPY Requirements.txt .
#RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r Requirements.txt

#RUN cp /usr/share/zoneinfo/America/Montevideo /etc/localtime
#RUN echo "America/Montevideo" >  /etc/timezone
#RUN date 

FROM spymovil/commsv3_imagen_base:latest

WORKDIR /apiredis
COPY apiredis.py .
COPY gunicorn.conf.py .
COPY wsgi.py .

COPY entrypoint.sh .
RUN chmod 777 /apiredis/*

ENTRYPOINT ["sh", "entrypoint.sh"]

EXPOSE 5100
