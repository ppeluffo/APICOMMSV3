#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python
'''
API de comunicaciones SPCOMMS para los dataloggers y plc.

-----------------------------------------------------------------------------
R001 @ 2023-06-15: (commsv3_apicomms:1.1)
- Se modifica el procesamiento de frames de modo que al procesar uno de DATA sea
  como los PING, no se lee la configuracion ya que no se necesita y genera carga
  innecesaria.
- Se manejan todos los parámetros por variables de entorno
- Se agrega un entrypoint 'ping' que permite ver si la api esta operativa

'''

import os
import json
import datetime as dt
import logging
import requests
from flask import Flask, request, make_response
from flask_restful import Resource, Api, reqparse
import apicomms_utils_dlg
import apicomms_utils_plc

app = Flask(__name__)
api = Api(app)

APIREDIS_HOST = os.environ.get('APIREDIS_HOST', 'apiredis')
APIREDIS_PORT = os.environ.get('APIREDIS_PORT', '5100')
APICONF_HOST = os.environ.get('APICONF_HOST', 'apiconf')
APICONF_PORT = os.environ.get('APICONF_PORT', '5200')
            
API_VERSION = 'R001 @ 2023-06-15'

class ApiComms(Resource):
    ''' 
    Clase especializada en atender los dataloggers y PLCs
    '''
    def __init__(self):
        self.debug_unit_id = None
        self.args = None
        self.dlgutils = apicomms_utils_dlg.dlgutils()
        self.d_conf = None
        self.mbk = apicomms_utils_plc.Memblock(app)
        self.parser = None
        self.GET_response = ''
        self.GET_response_status_code = 0
        self.POST_response = ''
        self.POST_response_status_code = 0
        self.ID = None
        self.VER = None
        self.TYPE = None
        self.CLASS = None

    def __read_debug_id__(self):
        '''
        Consulta el nombre del equipo que debe logearse.
        '''
        try:
            rsp = requests.get(f"http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/debugid", timeout=10 )
        except requests.exceptions.RequestException as err: 
            app.logger.info(f"ERROR XC001: request exception, Err={err}")
            self.debug_unit_id = None
            return
        
        if rsp.status_code == 200:
            d = rsp.json()
            self.debug_unit_id = d.get('debugid','UDEBUG')
            #app.logger.debug(f"DEBUG_DLGID={self.debug_unit_id}")
        else:
            app.logger.info(f"WARN XC001: No debug unit, Err=({rsp.status_code}){rsp.text}")
            # Seteo uno por default.
            _=requests.put(f"http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/debugid", json={'debugid':'UDEBUG'}, timeout=10 )

    def __format_with_template__(self):
        '''
        Tenemos una configuracion leida de SQL que no necesariamente cumple con el nuevo
        estándard de configuracion de la version del equipo.
        Aqui estandarizo los datos.
        '''
        pass
    
    def __read_configuration__(self):
        '''
        Lee la configuracion de la unidad y la deja en self.d_conf. Retorna True/False.
        '''
        # Intento leer desde REDIS.
        try:
            r_conf = requests.get(f"http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/config", params={'unit':self.args['ID']}, timeout=10 )
        except requests.exceptions.RequestException as err: 
            app.logger.info(f"ERROR XC001: request exception, Err:{err}")
            return False
        #
        if r_conf.status_code == 200:
            self.d_conf = r_conf.json()
            if self.ID == self.debug_unit_id:
                app.logger.info(f"INFO ID={self.args['ID']}, REDIS D_CONF={self.d_conf}")
            return True
        else:
            app.logger.info(f"WARN XC006: No Rcd en Redis, ID={self.args['ID']}, Err=({r_conf.status_code}){r_conf.text}")
        #
        # Intento leer desde SQL
        try:
            r_conf = requests.get(f"http://{APICONF_HOST}:{APICONF_PORT}/apiconf/config", params={'unit':self.args['ID']}, timeout=10 )
        except requests.exceptions.RequestException as err: 
            app.logger.info(f"ERROR XC001: request exception, Err:{err}")
            return False
        #
        if r_conf.status_code == 200:
            if r_conf.json() == {}:
                app.logger.info(f"WARN XC002: No Rcd en SQL, ID={self.args['ID']}, Err=({r_conf.status_code}){r_conf.text}")
                self.GET_response = 'CONFIG=ERROR;NO HAY REGISTRO EN BD' 
                self.GET_response_status_code = 200
                app.logger.info(f"WARN XC002: ID={self.args['ID']}: RSP_ERROR=[{self.GET_response}]")
                return False
         #
        elif r_conf.status_code == 204:
            # No hay datos en la SQL tampoco: Debo salir
            app.logger.info(f"WARN XC002: No Rcd en SQL, ID={self.args['ID']}, Err=({r_conf.status_code}){r_conf.text}")
            self.GET_response = 'CONFIG=ERROR;NO HAY REGISTRO EN BD' 
            self.GET_response_status_code = 200
            app.logger.info(f"WARN XC002: ID={self.args['ID']}: RSP_ERROR=[{self.GET_response}]")
            return False
        #
        else:
            app.logger.info(f"WARN XC003: No puedo leer SQL, ID={self.args['ID']}, Err=({r_conf.status_code}){r_conf.text}")
            self.GET_response = 'CONFIG=ERROR' 
            self.GET_response_status_code = 200
            app.logger.info(f"WARN XC003: ID={self.args['ID']}: RSP_ERROR=[{self.GET_response}]")
            return False
        #
        # La api sql me devuelve un json
        d_conf = r_conf.json()
        self.d_conf = d_conf
        app.logger.info(f"INFO ID={self.args['ID']}: SQL D_CONF={self.d_conf}")
        # Actualizo la redis.
        try:
            r_conf = requests.put(f"http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/config", params={'unit':self.args['ID']}, json=d_conf, timeout=10 )
        except requests.exceptions.RequestException as err: 
            app.logger.info(f"ERROR XC001: request exception, Err:{err}")
            return False

        if r_conf.status_code != 200:
            app.logger.info(f"WARN XC004: No puedo actualizar SQL config en REDIS, ID={self.args['ID']}, Err=({r_conf.status_code}){r_conf.text}")
            self.GET_response = 'CONFIG=ERROR' 
            self.GET_response_status_code = 200
            app.logger.info(f"INFO ID={self.args['ID']}: RSP_ERROR=[{self.GET_response}]")
            return False
        #
        app.logger.info(f"INFO ID={self.args['ID']}, Config de SQL updated en Redis")
        return True
    
    def __format_response__(self):
        '''
        Necesitamos este formateo para que los dlg. puedan parsear la respuesta
        '''
        #return f'<html><body><h1>{response}</h1></body></html>'
        self.GET_response = f'<html>{self.GET_response}</html>'

    def __process_ping__(self):
        '''
        '''
        # ID=PABLO&TYPE=SPXR3&VER=1.0.0&CLASS=PING
        self.GET_response = 'CLASS=PONG'
        self.GET_response_status_code = 200
        self.__format_response__()
        app.logger.info(f"INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
        return self.GET_response, self.GET_response_status_code

    def __process_conf_recover__(self):
        '''
        '''
        self.parser.add_argument('UID', type=str ,location='args', required=True)
        self.args = self.parser.parse_args()
        #
        # Vemos si la redis tiene los datos uid->dlgid
        try:
            r_conf = requests.get(f'http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/configuracion/uid2id', params={'uid':self.args['UID']}, timeout=10 )
        except requests.exceptions.RequestException as err: 
            app.logger.info(f"ERROR XC001: request exception, Err:{err}")
            return '', 500
        #
        if r_conf.status_code == 200:
            d_rsp = json.loads(r_conf.json())
            app.logger.info(f"INFO UID2DLGID in REDIS: NEW_ID={d_rsp['unit']}")
            self.GET_response = f"CLASS=self.args['CLASS']&ID={d_rsp['unit']}"
            self.GET_response_status_code = 200
            self.__format_response__()
            app.logger.info(f"INFO CLASS={self.args['CLASS']},ID={d_rsp['unit']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code
        #
        # No esta en REDIS, buscamos en SQL
        try:
            r_conf = requests.get(f'http://{APICONF_HOST}:{APICONF_PORT}/get/config', params={'dlgid':self.args['ID'], 'uid':self.args['UID']}, timeout=10 )
        except requests.exceptions.RequestException as err: 
            app.logger.info(f"ERROR XC001: request exception, Err:{err}")
            return '', 500
        #
        if r_conf.status_code == 200:
            self.GET_response = f"CLASS=self.args['CLASS']&ID={d_rsp['unit']}"
            self.GET_response_status_code = 200
            self.__format_response__()
            app.logger.info(f"INFO CLASS={self.args['CLASS']},ID={d_rsp['unit']},RSP=[{self.GET_response}]")
            # Actualizo la redis y mando la respuesta al equipo
            jd_conf = json.dumps({'unit':d_rsp['unit'],'uid':self.args['UID']})
            try:
                r_conf = requests.put(f'http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/configuracion/uid2id', json=jd_conf, timeout=10 )
                if r_conf.status_code != 200:
                    app.logger.info(f"INFO UID2DLGID_ERROR: ID={d_rsp['unit']}, Err: no puedo actualizar SQL UID2DLGID en REDIS. Err=({r_conf.status_code}){r_conf.text}")
                    return self.GET_response, self.GET_response_status_code
            except requests.exceptions.RequestException as err: 
                app.logger.info(f"ERROR XC001: request exception, Err:{err}")
            #
        #
        elif r_conf.status_code == 204:
            # No hay datos en la SQL tampoco: Debo salir
            app.logger.info(f"INFO UID2DLGID_ERROR: UID={self.args['UID']}, Err:No Rcd en SQL. Err=({r_conf.status_code}){r_conf.text}")
            self.GET_response = 'CONFIG=ERROR;NO HAY REGISTRO EN BD' 
            self.GET_response_status_code = 200
            self.__format_response__()
            app.logger.info(f"INFO UID={self.args['UID']}: RSP_ERROR=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code
        #
        else:
            # Error general
            app.logger.info(f"INFO UID2DLGID_ERROR: UID={self.args['UID']}, Err: no puedo leer SQL. Err=({r_conf.status_code}){r_conf.text}")
            self.GET_response = 'CONFIG=ERROR' 
            self.GET_response_status_code = 200
            self.__format_response__()
            app.logger.info(f"INFO UID={self.args['UID']}: RSP_ERROR=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code
        #
 
    def __process_conf_base__(self):
        '''
        '''
        # ID=PABLO&TYPE=SPXR3&VER=1.0.0&CLASS=CONF_BASE&UID=42125128300065090117010400000000&HASH=0x11
        self.parser.add_argument('UID', type=str ,location='args', required=True)
        self.parser.add_argument('HASH', type=str ,location='args', required=True)
        self.args = self.parser.parse_args()
        #
        # Chequeo la configuracion
        if self.d_conf is None:
            self.GET_response = 'CLASS=CONF_BASE&CONFIG=ERROR' 
            self.GET_response_status_code = 200
            self.__format_response__()
            app.logger.info(f"INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code

        # Calculo el hash de la configuracion de la BD.
        bd_hash = self.dlgutils.get_hash_config_base(self.d_conf, self.VER )
        if self.ID == self.debug_unit_id:
            app.logger.info(f"INFO ID={self.args['ID']}, BD_hash={bd_hash}, UI_hash={int(self.args['HASH'],16)}")
        #print(f"DEBUG::__get_conf_base__: bd_hash={bd_hash}, dlg_hash={self.args['HASH']}")
        if bd_hash == int(self.args['HASH'],16):
            self.GET_response = 'CLASS=CONF_BASE&CONFIG=OK'
            self.GET_response_status_code = 200
            self.__format_response__()
            app.logger.info(f"INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code
            
        # No coinciden: mando la nueva configuracion
        self.GET_response = self.dlgutils.get_response_base(self.d_conf, self.VER )
        self.GET_response_status_code = 200
        self.__format_response__()
        app.logger.info(f"INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
        return self.GET_response, self.GET_response_status_code

    def __process_conf_ainputs__(self):
        '''
        '''
        # ID=PABLO&TYPE=SPXR3&VER=1.0.0&CLASS=CONF_AINPUTS&HASH=0x01
        self.parser.add_argument('HASH', type=str ,location='args', required=True)
        self.args = self.parser.parse_args()
        #
        # Chequeo la configuracion
        if self.d_conf is None:
            self.GET_response = 'CLASS=CONF_AINPUTS&CONFIG=ERROR'
            self.GET_response_status_code = 200
            self.__format_response__()
            app.logger.info(f"INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code

        # Calculo el hash de la configuracion de la BD.
        bd_hash = self.dlgutils.get_hash_config_ainputs(self.d_conf,self.VER )
        if self.ID == self.debug_unit_id:
            app.logger.info(f"INFO ID={self.args['ID']}, BD_hash={bd_hash}, UI_hash={int(self.args['HASH'],16)}")
        #print(f"DEBUG::__get_conf_ainputs__: bd_hash={bd_hash}, dlg_hash={self.args['HASH']}")
        if bd_hash == int(self.args['HASH'],16):
            self.GET_response = 'CLASS=CONF_AINPUTS&CONFIG=OK'
            self.GET_response_status_code = 200
            self.__format_response__()
            app.logger.info(f"INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code
            
        # No coinciden: mando la nueva configuracion
        self.GET_response = self.dlgutils.get_response_ainputs(self.d_conf,self.VER )
        self.GET_response_status_code = 200
        self.__format_response__()
        app.logger.info(f"INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
        return self.GET_response, self.GET_response_status_code

    def __process_conf_counters__(self):
        '''
        '''
        # ID=PABLO&TYPE=SPXR3&VER=1.0.0&CLASS=CONF_COUNTERS&HASH=0x86
        self.parser.add_argument('HASH', type=str ,location='args', required=True)
        self.args = self.parser.parse_args()
        #
        # Chequeo la configuracion
        if self.d_conf is None:
            self.GET_response = 'CLASS=CONF_COUNTERS&CONFIG=ERROR' 
            self.GET_response_status_code = 200
            self.__format_response__()
            app.logger.info(f"INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code

        # Calculo el hash de la configuracion de la BD.
        bd_hash = self.dlgutils.get_hash_config_counters(self.d_conf,self.VER )
        if self.ID == self.debug_unit_id:
            app.logger.info(f"INFO ID={self.args['ID']}, BD_hash={bd_hash}, UI_hash={int(self.args['HASH'],16)}")
        if bd_hash == int(self.args['HASH'],16):
            self.GET_response = 'CLASS=CONF_COUNTERS&CONFIG=OK'
            self.GET_response_status_code = 200
            self.__format_response__()
            app.logger.info(f"INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code
            
        # No coinciden: mando la nueva configuracion
        self.GET_response = self.dlgutils.get_response_counters(self.d_conf,self.VER )
        self.GET_response_status_code = 200
        self.__format_response__()
        app.logger.info(f"INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
        return self.GET_response, self.GET_response_status_code
    
    def __process_conf_modbus__(self):
        '''
        '''
        # ID=PABLO&TYPE=SPXR3&VER=1.0.0&CLASS=CONF_MODBUS&HASH=0x86
        self.parser.add_argument('HASH', type=str ,location='args', required=True)
        self.args = self.parser.parse_args()
        #
        # Chequeo la configuracion
        if self.d_conf is None:
            self.GET_response = 'CLASS=CONF_MODBUS&CONFIG=ERROR' 
            self.GET_response_status_code = 200
            self.__format_response__()
            app.logger.info(f"INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code

        # Calculo el hash de la configuracion de la BD.
        bd_hash = self.dlgutils.get_hash_config_modbus(self.d_conf,self.VER )
        if self.ID == self.debug_unit_id:
            app.logger.info(f"INFO ID={self.args['ID']}, BD_hash={bd_hash}, UI_hash={int(self.args['HASH'],16)}")
        if bd_hash == int(self.args['HASH'],16):
            self.GET_response = 'CLASS=CONF_MODBUS&CONFIG=OK'
            self.GET_response_status_code = 200
            self.__format_response__()
            app.logger.info(f"INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code
            
        # No coinciden: mando la nueva configuracion
        self.GET_response = self.dlgutils.get_response_modbus(self.d_conf,self.VER)
        self.GET_response_status_code = 200
        self.__format_response__()
        app.logger.info(f"INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
        return self.GET_response, self.GET_response_status_code
    
    def __process_data__(self):
        '''
        '''
        # ID=PABLO&TYPE=SPXR3&VER=1.0.0&CLASS=DATA&DATE=230321&TIME=094504&A0=0.00&A1=0.00&A2=0.00&C0=0.000&C1=0.000&bt=12.496
        d_payload = self.dlgutils.process_data( app, request.args, self.VER )
        
        if d_payload is None:
            return 'ERROR:UNKNOWN VERSION',200

        # 1) Guardo los datos
        r_datos = requests.put(f"http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/dataline", params={'unit':self.ID,'type':'DLG'}, json=d_payload, timeout=10 )
        if r_datos.status_code != 200:
            # Si da error genero un mensaje pero continuo para no trancar al datalogger.
            app.logger.error(f"CLASS={self.CLASS},ID={self.ID},ERROR AL GUARDAR DATA EN REDIS. Err=({r_datos.status_code}){r_datos.text}")
        #
        # 3) Leo las ordenes
        r_ordenes = requests.get(f"http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/ordenes", params={'unit':self.ID }, timeout=10 )
        d_ordenes = None
        if r_ordenes.status_code == 200:
            d_ordenes = r_ordenes.json()
            ordenes = d_ordenes.get('ordenes','')
            if self.ID == self.debug_unit_id:
                app.logger.info(f"CLASS={self.CLASS},ID={self.ID}, D_ORDENES={d_ordenes}")
        elif r_ordenes.status_code == 204:
            # Si da error genero un mensaje pero continuo para no trancar al datalogger.
            if self.ID == self.debug_unit_id:
                app.logger.info(f"CLASS={self.CLASS},ID={self.ID},NO HAY RCD ORDENES")
            ordenes = ''
        else:
            app.logger.error(f"CLASS={self.CLASS},ID={self.ID},ERROR AL LEER ORDENES. Err=({r_ordenes.status_code}){r_ordenes.text}")
            ordenes = ''
        #
        # 3.1) Si RESET entonces borro la configuracion
        if 'RESET' in ordenes:
            _ = requests.delete(f"http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/delete", params={'unit':self.ID}, timeout=10 )
            app.logger.info(f"CLASS={self.CLASS},ID={self.ID}, DELETE REDIS RCD.")
        #
        # 3.2) Borro las ordenes
        _ = requests.delete(f"http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/ordenes", params={'unit':self.ID}, timeout=10 )

        # 4) Respondo
        now=dt.datetime.now().strftime('%y%m%d%H%M')
        self.GET_response = f'CLASS=DATA&CLOCK={now};{ordenes}'
        self.GET_response_status_code = 200
        self.__format_response__()
        app.logger.info(f"INFO CLASS={self.CLASS},ID={self.ID},RSP=[{self.GET_response}]")
        return self.GET_response, self.GET_response_status_code

    def get(self):
        ''' 
        Procesa los GET de los dataloggers: configuracion y datos.
        '''
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('ID', type=str ,location='args', required=True)
        self.parser.add_argument('TYPE', type=str ,location='args', required=True)
        self.parser.add_argument('VER', type=str ,location='args', required=True)
        self.parser.add_argument('CLASS', type=str ,location='args', required=True)
        self.args = self.parser.parse_args()
        self.ID = self.args['ID']
        self.VER = self.args['VER']
        self.TYPE = self.args['TYPE']
        self.CLASS = self.args['CLASS']

        # Leo el debugdlgid
        self.__read_debug_id__()

        # Logs generales.
        app.logger.info("INFO DLG_QS=%(a)s", {'a': request.query_string })
        if self.ID == self.debug_unit_id:
            app.logger.debug("CLASS=%(a)s", {'a': self.args['CLASS'] })
        
        # Los PING siempre se responden !!
        if self.CLASS == 'PING':
            return self.__process_ping__()

        if self.CLASS == 'DATA':
            return self.__process_data__()
        
        # Leo la configuracion porque lo requieren las otras clases
        if not self.__read_configuration__():
            self.GET_response = 'CONFIG_ERROR'
            self.GET_response_status_code = 200
            self.__format_response__()
            return self.GET_response, self.GET_response_status_code
        
        # Analizo los tipos de frames
        if self.CLASS == 'RECOVER':
            return self.__process_conf_recover__() 

        if self.CLASS == 'CONF_BASE':
            return self.__process_conf_base__()
        
        if self.CLASS == 'CONF_AINPUTS':
            return self.__process_conf_ainputs__()

        if self.CLASS == 'CONF_COUNTERS':
            return self.__process_conf_counters__()

        if self.CLASS == 'CONF_MODBUS':
            return self.__process_conf_modbus__()
        
        self.GET_response = 'ERROR:UNKNOWN FRAME TYPE'
        self.GET_response_status_code = 200
        self.__format_response__()
        app.logger.info(f"INFO CLASS={self.CLASS},ID={self.ID},RSP=[{self.GET_response}]")
        return self.GET_response, self.GET_response_status_code
    
    def __POST_reception__(self):
        '''
        Debo convertir el byte stream recibido del PLC a un named dict de acuerdo al formato
        del rcvd_memblock. 
        '''
        if self.ID == self.debug_unit_id:
            app.logger.info(f'INFO PLC_ID={self.ID}, PRCESSING_RECEPTION')
        
        # Cargo los datos (memblock) recibidos del PLC (post) al objeto mbk
        # Los datos los leo con get_data() como bytestring.
        rx_payload = request.get_data()
        self.mbk.load_rx_payload(rx_payload)
        #
        # Convierto el bytestring de datos recibidos de acuerdo a la definicion de RCVD MBK en un dict.
        if not self.mbk.convert_rxbytes2dict():
            self.POST_response = "RECEPTION_ERROR"
            self.POST_response_status_code = 200
            return False
        
        # Guardo los datos en las BD (redis y SQL).
        d_payload = self.mbk.get_d_rx_payload()
        # Agrego los campos DATE y TIME para normalizarlos a la BD.
        # 'DATE': '230417', 'TIME': '161057'
        now = dt.datetime.now()
        d_payload['DATE'] = now.strftime('%y%m%d')
        d_payload['TIME'] = now.strftime('%H%M%S')
        if self.ID == self.debug_unit_id:
            app.logger.info(f'INFO PLC_ID={self.ID}, d_rx_payload={d_payload}')
        # Guardo los datos a traves de la api.
        try:
            r_data = requests.put(f"http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/dataline", params={'unit':self.args['ID'],'type':'PLC'}, json=json.dumps(d_payload), timeout=10 )
        except requests.exceptions.RequestException as err:
            app.logger.info(f"ERROR XC001: request exception, Err={err}")
            return
        if r_data.status_code != 200:
            # Si da error genero un mensaje pero continuo para no trancar al datalogger.
            app.logger.info(f"ERROR XC005: No puede guardarse en Redis, PLC={self.ID}, Err={r_data.text}")
            return False
        #
        return True
   
    def __POST_response__(self):
        '''
        Preparo la respuesta a enviar al PLC.
        Armo un diccionario con todas las variables y valores a enviar que luego lo voy a 
        convertir en un bytestring de acuerdo al memblock SEND_MBK.

        Paso1:
        Leo el diccionario con las variables remotas ( dlgid: [ (var_name_remoto, var_name_local),  ] )
        var_name_remoto es el nombre de la variable en el equipo remoto (pA)
        var_name_local es el nombre definido en el mbk. ( ALTURA_TANQUE_KIYU )
        La configuracion de las variables remotas esta en d_conf con la clave REMVARS
        Ej:
            REMVARS = { 'KIYU001':[('HTQ1', 'ALTURA_TANQUE_KIYU_1'), ('HTQ2', 'ALTURA_TANQUE_KIYU_2')],
                    'SJOSE001' : [ ('PA', 'PRESION_ALTA_SJ1'), ('PB', 'PRESION_BAJA_SQ1')]
                  }
             { dlgid: [(Nombre_en_equipo_remoto, Nombre_en_equipo_destino ),...], }

        Paso2:
        Leo las ordenes de ATVISE y las agrego al diccionario

        Paso3:
        Serializo (memblock) el diccionario de variables a enviar

        '''
        if self.ID == self.debug_unit_id:
            app.logger.info(f'INFO PLC_ID={self.ID}, Processing Response')
        
        # Paso 1) REMVARS
        # Leo de la configuracion las variables remotas que debo enviar al PLC
        d_remvars = self.d_conf.get('REMVARS',{})
        if self.ID == self.debug_unit_id:
            app.logger.info(f'INFO PLC_ID={self.ID}, d_rem_vars={d_remvars}')

        # Leo los valores de los equipos remotos del d_remvars
        d_remote_datalines = {}
        for unit_id in d_remvars:
            try:
                r_data = requests.get(f"http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/dataline", params={'unit':unit_id}, timeout=10 )
            except requests.exceptions.RequestException as err:
                app.logger.info(f"ERROR XC001: request exception, Err={err}")
                return
            #
            if r_data.status_code == 200:
                 d_remote_datalines[unit_id] = json.loads(r_data.json())
            else:
                app.logger.info(f'WARN XC003: No {unit_id} dataline, Err=({r_data.status_code}){r_data.text}')
                d_remote_datalines[unit_id] = {}
        #
        if self.ID == self.debug_unit_id:
            app.logger.info(f'INFO PLC_ID={self.ID}, d_remote_datalines={d_remote_datalines}')

        # Armo el diccionario con las variables y valores de la respuesta al PLC
        d_responses = {}
        for unit_id in d_remvars:
            list_tvars = d_remvars[unit_id]
            for var_name_remoto, var_name_destino in list_tvars:
                # Leo el valor correspondiente al equipo remoto desde d_remote_datalines
                rem_value = d_remote_datalines[unit_id].get(var_name_remoto, -99)
                d_responses[var_name_destino] = rem_value
                if self.ID == self.debug_unit_id:
                    app.logger.info(f'INFO PLC_ID={self.ID}, read_remote_value={var_name_remoto}:{d_responses[var_name_destino]}')
        #
        # Agrego una nueva variable TIMESTAMP que es el timestamp HHMM que sirve para que el PLC pueda tener
        # contol si el enlace cayo y los valores de las variables caducaron.
        now = dt.datetime.now()
        now_str = now.strftime("%H%M")
        d_responses['TIMESTAMP'] = int(now_str)
        if self.ID == self.debug_unit_id:
            app.logger.info(f'INFO PLC_ID={self.ID}, d_responses={d_responses}')
        #
        # Paso 2) ATVISE
        # Leo las variables(ordenes) de  ATVISE y las agrego al diccionario de respuestas
        try:
            r_atvise = requests.get(f"http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/ordenes/atvise", params={'unit':self.ID}, timeout=10 )
        except requests.exceptions.RequestException as err:
            app.logger.info(f"ERROR XC001: request exception, Err={err}")
        #
        if r_atvise.status_code == 200:
            d_atvise_responses = json.loads(r_atvise.json())
            if self.ID == self.debug_unit_id:
                app.logger.info(f'INFO PLC_ID={self.ID}, d_atvise_responses={d_atvise_responses}')
        elif r_atvise.status_code == 204:
            d_atvise_responses = {}
            app.logger.info(f"INFO PLC_ID={self.args['ID']}, NO HAY ORDENES DE ATVISE")
        else:
            d_atvise_responses = {}
            app.logger.info(f"ERROR XC004: No puede leerse ordenes Atvise, PLC_ID={self.args['ID']}, Err=({r_atvise.status_code}){r_atvise.text}")
        #
        # Paso 3)
        # Junto todas las variables de la respuesta en un solo diccionario
        #d_responses.update(d_atvise_responses)
        #print(f"DEBUG: type of d_responses = {type(d_responses)}")
        #print(f"DEBUG: type of d_atvise_responses = {type(d_atvise_responses)}")
        d_responses = { **d_responses, **d_atvise_responses }
        if self.ID == self.debug_unit_id:
            app.logger.info(f'INFO PLC_ID={self.ID}, d_responses={d_responses}')
        #
        # Paso 4)
        # Armo el bloque de respuestas a enviar apareando el d_responses con el mbk dando como resultado un rsp_dict.
        sresp = self.mbk.convert_dict2bytes( self.ID, d_responses)
        if self.ID == self.debug_unit_id:
            app.logger.info(f'INFO PLC_ID={self.ID}, sresp={sresp}')
        #
        return sresp
        
    def post(self):
        '''
        Procesa los POST que vienen de los PLC
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('ID',type=str,location='args',required=True)
        parser.add_argument('VER',type=str,location='args',required=True)
        parser.add_argument('TYPE',type=str,location='args',required=True)
        self.args=parser.parse_args()
        self.ID = self.args['ID']
    
        # Leo el debugdlgid
        self.__read_debug_id__()
        if self.ID == self.debug_unit_id:
            self.mbk.set_debug()

        # Logs generales.
        app.logger.info("PLC_QS=%(a)s", {'a': request.query_string })
    
        # Leo la configuracion
        if not self.__read_configuration__():
            self.POST_response = "CONFIG_ERROR"
            self.POST_response_status_code = 204
            return self.POST_response, self.POST_response_status_code

        # Leo de la configuracion la definicion del memblock y la cargo en el objeto mbk
        d_mbk = self.d_conf.get('MEMBLOCK',{})
        self.mbk.load_configuration(self.ID, d_mbk)
        if self.ID == self.debug_unit_id:
            app.logger.info(f"INFO: PLC_ID={self.args['ID']}, MBK={d_mbk}")
        
        # Recepcion
        if not self.__POST_reception__():
            app.logger.error(f"ERROR XC002: No se puede procesar Rxdata, PLC={self.ID}")
            self.POST_response = "RECEPTION_ERROR"
            self.POST_response_status_code = 204
            return self.POST_response, self.POST_response_status_code
        
        # Respuesta
        sresp = self.__POST_response__()
        #sresp = b'PLC respuesta de Spymovil'
        #sresp = b'\n\x0bf\xe6\xf6Bb\x04W\x02\xecq\xe4C:\x16\x00\x00\x00\x00\x00\x0b\xa3'
        #
        # La funcion make_response es de FLASK !!!

        response = make_response(sresp)
        response.headers['Content-type'] = 'application/binary'

        if self.ID == self.debug_unit_id:
            app.logger.info(f"INFO: RSP2PLC={sresp}")
        return response

class Ping(Resource):
    '''
    Prueba la conexion a la BD Redis
    '''
    def get(self):
        '''
        '''
        # Pruebo la conexion a REDIS
        redis_status = 'ERR'
        try:
            r_conf = requests.get(f"http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/ping",timeout=10 )
            if r_conf.status_code == 200:
                redis_status = 'OK'
        except requests.exceptions.RequestException as err: 
            app.logger.info(f"ERROR XC001: Redis request exception,[{APIREDIS_HOST}:{APIREDIS_PORT}] Err:{err}")
        #
        # Pruebo la conexion a SQL
        sql_status = 'ERR'
        try:
            r_conf = requests.get(f"http://{APICONF_HOST}:{APICONF_PORT}/apiconf/ping",timeout=10 )
            if r_conf.status_code == 200:
                sql_status = 'OK'
        except requests.exceptions.RequestException as err: 
            app.logger.info(f"ERROR XC001: Sql request exception,[{APICONF_HOST}:{APICONF_PORT}] Err:{err}")
        #
        #
        if redis_status == 'OK' and sql_status == 'OK':
            ping_status = 'OK'
        else:
            ping_status = 'FAIL'
            
        return {'Rsp':f'{ping_status}','version':API_VERSION, 'API_REDIS':f'{APIREDIS_HOST}:{APIREDIS_PORT}','API_CONF':f'{APICONF_HOST}:{APICONF_PORT}' }, 200

class Help(Resource):
    '''
    Devuelve el estado de la conexion a la BD Redis.
    '''
    def get(self):
        '''
        '''
        return {}, 200

api.add_resource( ApiComms, '/apicomms')
api.add_resource( Help, '/apicomms/help')
api.add_resource( Ping, '/apicomms/ping')

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

    app.logger.info( f'Starting APICOMMS: REDIS_HOST={APIREDIS_HOST}, REDIS_PORT={APIREDIS_PORT}' )
    app.logger.info( f'         APICOMMS: CONF_HOST={APICONF_HOST}, CONF_PORT={APICONF_PORT}' )

if __name__ == '__main__':
    APIREDIS_HOST = '127.0.0.1'
    APICONF_HOST = '127.0.0.1'
    app.run(host='0.0.0.0', port=5000, debug=True)
