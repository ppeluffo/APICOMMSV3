FROM ubuntu:20.04

COPY Requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends python3.8 python3-pip libpq-dev gcc python3.8-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade wheel --upgrade pip && pip install --no-cache-dir -r Requirements.txt \
    && apt-get purge -y --auto-remove gcc python3.8-dev

WORKDIR /apiconf
COPY gunicorn.conf.py .
COPY wsgi.py .
COPY entrypoint.sh .

COPY apiconf_templates.py .
COPY apiconf.py .
RUN chmod 777 /apiconf/*

ENTRYPOINT ["sh", "entrypoint.sh"]

EXPOSE 5200
