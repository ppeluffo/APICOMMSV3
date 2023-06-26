FROM spymovil/commsv3_imagen_base:latest

WORKDIR /apicomms
COPY *.py ./
COPY entrypoint.sh .
RUN chmod 777 /apicomms/*
ENTRYPOINT ["sh", "entrypoint.sh"]

EXPOSE 5000

