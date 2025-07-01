#!/home/pablo/Spymovil/python/proyectos/APICOMMS/venv/bin/python
'''
API de comunicaciones SPCOMMS para las estaciones ambientales OCEANUS.

-----------------------------------------------------------------------------
R001 @ 2023-09-25:

'''

import datetime as dt
from flask import Flask, request, make_response
from flask_restful import Resource, reqparse
from apicomms_common import Utils
import re
import requests

API_VERSION = 'R001 @ 2023-09-25'

NEEDLES_LIST = ['HUM:[0-9.]+', 'TEMPER:[0-9.]+', 'PM10:[0-9.]+', 'PM2.5:[0-9.]+', 'TSP:[0-9.]+', 'AIRPRE:[0-9.]+']

class ApiOceanus(Resource):
    ''' 
    Clase especializada en atender los dataloggers y PLCs
    '''
    def __init__(self, **kwargs):
        self.app = kwargs['app']
        self.servers = kwargs['servers']
        self.debug_unit_id = None
        self.args = None
        self.d_conf = None
        self.ID = None
        self.VER = None
        self.TYPE = None
        self.payload = None
        self.d_mags = None
        self.url_redis = f"http://{self.servers['APIREDIS_HOST']}:{self.servers['APIREDIS_PORT']}/apiredis/"

    def filter_payload(self, rx_payload):
        '''
        Filtra el contenido recibido en POST y solo se queda con los bytes imprimibles.
        Convierto el rx_payload para solo quedarme con los ascii.
        rx_payload=b'\x00\x00\x18\x00\x0c\x00\x0c\x00\x01\n\x01\x02\x00\x00\x00\x00\x01\x01\x01\x00\x17\x02\x11\x00\x00\x00\\FO000HUM:47.0%RH\xcc
             \xffZ\xa5\xa5\xa5\xa5\xa5\xa5\xa5\xa5\x01\x00\x00\x80\x00\x00\x00\x00\x00\x00\xfe\x02:\x00\xa3\x06\x02\x00\x00\x00\x011\x00\x00
             \x00\x00$\x00\x0c\x00\x0c\x00\x02\n\x01\x02\x00\x00\x00\x00\x01\x01\x01\x00\x17\x02\x16\x00\x00\x00\\FO000AIRPRE:1016.0hPaJrZ'

        payload = 7.\FO000TEMPER:24.3HZ5
        payload = \FO000PM10:29.0ug/m3KZ7.$\FO000TSP:78.0ug/m3nZ

        HUM:47.0%
        AIRPRE:1016.0hPa            
        TEMPER:24.1
        '''
        self.payload = ''
        for i in rx_payload:
            if 33 <= i <= 127:
                self.payload += chr(i)
        if self.ID == self.debug_unit_id:        
            self.app.logger.info(f"(103) ApiOCEANUS_INFO: ID={self.ID}, payload={self.payload}")

    def extract_mags_values_from_payload(self):
        '''
        Revisa el string self.payload ( solo caracteres imprimibles ) y extra los nombres y valores de las magnitudes
        que las devuelve en self.d_mags.
        payload = 7.\FO000TEMPER:24.3HZ5
        { TEMPER = 24.3 }
        '''
        self.d_mags = {}
        for needle in NEEDLES_LIST:
            subs = re.search(needle,self.payload)
            if subs:
                s = subs.group()
                name,value = s.split(':')
                self.d_mags[name] = value
                if self.ID == self.debug_unit_id:
                    self.app.logger.info(f"(104) ApiOCEANUS_INFO: ID={self.ID}, MAG={name}:{value}")
            #
        #
        if self.ID == self.debug_unit_id:
            self.app.logger.info(f"(105) ApiOCEANUS_INFO: ID={self.ID}, d_mags={self.d_mags}")

    def save_data_in_bd(self):
        '''
        Guarda el diccionario con los datos en la Redis.
        Le agrega el timestamp.
        '''
        now = dt.datetime.now()
        self.d_mags['DATE'] = now.strftime('%y%m%d')
        self.d_mags['TIME'] = now.strftime('%H%M%S')
        #
        # Guardo los datos en Redis a traves de la api.
        try:
            r_datos = requests.put(self.url_redis + 'dataline', params={'unit':self.ID,'type':'OCEANUS'}, json=self.d_mags, timeout=10 )
        except Exception as err:
            self.app.logger.info(f"(107) ApiOCEANUS_ERR001: Redis request exception,ID={self.ID},Err={err}")
            return False
        
        if r_datos.status_code != 200:
            # Si da error genero un mensaje pero continuo para no trancar al datalogger.
            self.app.logger.info(f"(107) ApiOCEANUS_ERR002: Redis request exception,ID={self.ID},Err={r_datos.text}")
            return False
        #
        return True
    
    def post(self):
        '''
        Procesa los POST que vienen de las estaciones OCEANUS
        Del URL leo los parámetro ID,VER,TYPE
        Los datos vienen en el cuerpo del POST.
        '''
        # Leo los argumentos que vinen en el URL.
        parser = reqparse.RequestParser()
        parser.add_argument('ID',type=str,location='args',required=True)
        parser.add_argument('VER',type=str,location='args',required=True)
        parser.add_argument('TYPE',type=str,location='args',required=True)
        self.args=parser.parse_args()
        self.ID = self.args['ID']
        self.VER = self.args['VER']
        self.TYPE = self.args['TYPE']
    
        utils=Utils( {'id':self.ID, 'app':self.app, 'servers':self.servers} )

        # Leo el debugdlgid
        self.debug_unit_id = utils.read_debug_id()

        # Logs general.
        if self.ID == self.debug_unit_id:
            self.app.logger.info("(100) ApiOCEANUS_INFO: QS=%(a)s", {'a': request.query_string })
            self.app.logger.info(f"(101) ApiOCEANUS_INFO: ID={self.ID},VER={self.VER},TYPE={self.TYPE}")
        #
        # Las estaciones no necesitan respuesta.!!!. Solo transmiten.
        # Leo el cuerpo del post
        rx_payload = request.get_data()
        if self.ID == self.debug_unit_id:
            self.app.logger.info(f"(102) ApiOCEANUS_INFO: ID={self.ID}, rx_payload={rx_payload}")
        #
        self.filter_payload(rx_payload)
        #
        self.extract_mags_values_from_payload()
        #
        _ = self.save_data_in_bd()
        #if self.ID == self.debug_unit_id:
        self.app.logger.info(f"(106) ApiOCEANUS_INFO: ID={self.ID}, d_mags={self.d_mags}")
        