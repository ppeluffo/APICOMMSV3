FROM ubuntu:20.04
RUN apt-get update && apt-get install -y --no-install-recommends python3.8 python3-pip systemctl redis-server && apt-get clean && rm -rf /var/lib/apt/lists/*
COPY Requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r Requirements.txt

#RUN apt-get update && apt-get install -y --no-install-recommends supervisor redis-server && apt-get clean && rm -rf /var/lib/apt/lists/*
#ADD supervisord.conf /etc/supervisor/conf.d/supervisord.conf

WORKDIR /apiredis
COPY apiredis.py .
COPY gunicorn.conf.py .
COPY wsgi.py .

RUN mkdir /var/log/gunicorn
RUN touch /var/log/gunicorn/apiredis.log && chmod 777 /var/log/gunicorn/apiredis.log

COPY entrypoint.sh .
RUN chmod 777 /apiredis/*

ENTRYPOINT ["sh", "entrypoint.sh"]

EXPOSE 5100
