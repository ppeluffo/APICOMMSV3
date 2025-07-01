FROM spymovil/commsv3_imagen_base:latest

WORKDIR /apicomms
#COPY *.py ./
#COPY baseutils/ baseutils
#COPY prot_dpdavrda/ prot_dpdavrda
#COPY prot_fwdlgx/ prot_fwdlgx
#COPY prot_oceanus/ prot_oceanus
#COPY prot_spqavrda/ prot_spqavrda
#COPY prot_spxavrda/ prot_spxavrda
#COPY prot_spxxmega/ prot_spxxmega
COPY . . 
RUN ls -laR
COPY entrypoint.sh .
RUN chmod 777 /apicomms/*
ENTRYPOINT ["sh", "entrypoint.sh"]

EXPOSE 5000

