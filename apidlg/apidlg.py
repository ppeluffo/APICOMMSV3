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
import datetime as dt
import logging
import requests
from flask import Flask, request
from flask_restful import Resource, Api, reqparse
import apidlg_utils

app = Flask(__name__)
api = Api(app)

APIREDIS_HOST = os.environ.get('APIREDIS_HOST', 'apiredis')
APIREDIS_PORT = os.environ.get('APIREDIS_PORT', '5100')
APICONF_HOST = os.environ.get('APICONF_HOST', 'apiconf')
APICONF_PORT = os.environ.get('APICONF_PORT', '5200')
            
API_VERSION = 'R001 @ 2023-06-15'

class ApiDlg(Resource):
    ''' 
    Clase especializada en atender los dataloggers y PLCs
    '''
    def __init__(self):
        self.debug_unit_id = None
        self.args = None
        self.dlgutils = apidlg_utils.dlgutils()
        self.d_conf = None
        self.parser = None
        self.GET_response = ''
        self.GET_response_status_code = 0
        self.ID = None
        self.UID = None
        self.VER = None
        self.TYPE = None
        self.CLASS = None

    def __update_uid2id__(self, id, uid):
        '''
        '''
        try:
            r_conf = requests.get(f'http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/uid2id', params={'uid':self.args['UID']}, timeout=10 )
        except requests.exceptions.RequestException as err: 
            app.logger.info(f"(400) ApiDLG_ERR001: Redis request exception', Err:{err}")
            app.logger.info(f"(401) ApiDLG_INFO Recoverid Error: UID={self.args['UID']}: RSP_ERROR=[{self.GET_response}]")
            return
        #
        # Esta en la REDIS...
        if r_conf.status_code == 200:
            d_rsp = r_conf.json()
            nid = d_rsp['id']
            if nid == id:
                # Redis esta actualizada: Salgo.
                return
        # 
        # En todos los otros casos, intento actualizar Redis y Sql
        d_conf = {'id':id,'uid':uid}
        try:
            r_conf = requests.put(f'http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/uid2id', json=d_conf, timeout=10 )
            app.logger.info("(402) ApiDLG INFO uid2id update Redis")
        except requests.exceptions.RequestException as err: 
            app.logger.info(f"(403) ApiDLG_ERR001: Redis request exception', Err:{err}")
        #
        try:
            r_conf = requests.put(f'http://{APICONF_HOST}:{APICONF_PORT}/apiconf/uid2id', json=d_conf, timeout=10 )
            app.logger.info("(404) ApiDLG INFO uid2id update SQL")
        except requests.exceptions.RequestException as err: 
            app.logger.info(f"(405) ApiDLG_ERR001: Redis request exception', Err:{err}")
                
        #

    def __read_debug_id__(self):
        '''
        Consulta el nombre del equipo que debe logearse.
        '''
        try:
            rsp = requests.get(f"http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/debugid", timeout=10 )
        except requests.exceptions.RequestException as err: 
            app.logger.info( f'(406) ApiDLG_ERR003: read_debug_id request exception, Err:{err}')
            self.debug_unit_id = None
            return
        
        if rsp.status_code == 200:
            d = rsp.json()
            self.debug_unit_id = d.get('debugid','UDEBUG')
            #app.logger.debug(f"DEBUG_DLGID={self.debug_unit_id}")
        else:
            app.logger.info(f"(407) ApiDLG_WARN001: No debug unit, Err=({rsp.status_code}){rsp.text}")
            # Seteo uno por default.
            _=requests.put(f"http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/debugid", json={'debugid':'UDEBUG'}, timeout=10 )
   
    def __read_configuration__(self):
        '''
        Lee la configuracion de la unidad y la deja en self.d_conf. Retorna True/False.
        '''
        # Intento leer desde REDIS.
        try:
            r_conf = requests.get(f"http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/config", params={'unit':self.args['ID']}, timeout=10 )
        except requests.exceptions.RequestException as err: 
            app.logger.info( f'(408) ApiDLG_ERR004: read_configuration request exception, Err:{err}')
            return False
        #
        if r_conf.status_code == 200:
            self.d_conf = r_conf.json()
            if self.ID == self.debug_unit_id:
                app.logger.info(f"(409) ApiDLG: ID={self.args['ID']}, REDIS D_CONF={self.d_conf}")
            return True
        else:
            app.logger.info(f"(410) ApiDLG_WARN002: No Rcd en Redis,ID={self.args['ID']}, Err=({r_conf.status_code}){r_conf.text}")
        #
        # Intento leer desde SQL
        try:
            r_conf = requests.get(f"http://{APICONF_HOST}:{APICONF_PORT}/apiconf/config", params={'unit':self.args['ID']}, timeout=10 )
        except requests.exceptions.RequestException as err: 
            app.logger.info( f'(411) ApiDLG_ERR002: Sql request exception, HOST:{APICONF_HOST}:{APICONF_PORT}, Err:{err}')
            return False
        #
        if r_conf.status_code == 200:
            if r_conf.json() == {}:
                app.logger.info(f"(412) ApiDLG_WARN003: Rcd en Sql empty,ID={self.args['ID']}, Err=({r_conf.status_code}){r_conf.text}")
                self.GET_response = 'CONFIG=ERROR;NO HAY REGISTRO EN BD' 
                self.GET_response_status_code = 200
                return False
         #
        elif r_conf.status_code == 204:
            # No hay datos en la SQL tampoco: Debo salir
            app.logger.info(f"(413) ApiDLG_WARN004: No Rcd en Sql,ID={self.args['ID']}, Err=({r_conf.status_code}){r_conf.text}")
            self.GET_response = 'CONFIG=ERROR;NO HAY REGISTRO EN BD' 
            self.GET_response_status_code = 200
            return False
        #
        else:
            app.logger.info(f"(414) ApiDLG_ERR005: No puedo leer SQL,ID={self.args['ID']}, Err=({r_conf.status_code}){r_conf.text}")
            self.GET_response = 'CONFIG=ERROR' 
            self.GET_response_status_code = 200
            return False
        #
        # La api sql me devuelve un json
        d_conf = r_conf.json()
        self.d_conf = d_conf
        app.logger.info(f"(415) ApiDLG INFO ID={self.args['ID']}: SQL D_CONF={self.d_conf}")
        # Actualizo la redis.
        try:
            r_conf = requests.put(f"http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/config", params={'unit':self.args['ID']}, json=d_conf, timeout=10 )
        except requests.exceptions.RequestException as err: 
            app.logger.info(f"(416) ApiDLG_ERR001: Redis request exception', Err:{err}")
            return False

        if r_conf.status_code != 200:
            app.logger.info(f"(417) ApiDLG_ERR006: No puedo actualizar SQL config en REDIS, ID={self.args['ID']}, Err=({r_conf.status_code}){r_conf.text}")
            self.GET_response = 'CONFIG=ERROR' 
            self.GET_response_status_code = 200
            app.logger.info(f"(418) ApiDLG INFO ID={self.args['ID']}: RSP_ERROR=[{self.GET_response}]")
            return False
        #
        app.logger.info(f"(419) ApiDLG INFO ID={self.args['ID']}, Config de SQL updated en Redis")
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
        app.logger.info(f"(420) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
        return self.GET_response, self.GET_response_status_code

    def __process_conf_recover__(self):
        '''
        '''
        self.parser.add_argument('UID', type=str ,location='args', required=True)
        self.args = self.parser.parse_args()
        #
        # Vemos si la redis tiene los datos uid->id
        try:
            r_conf = requests.get(f'http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/uid2id', params={'uid':self.args['UID']}, timeout=10 )
        except requests.exceptions.RequestException as err: 
            app.logger.info(f"(421) ApiDLG_ERR001: Redis request exception', Err:{err}")
            self.GET_response = 'CONFIG=ERROR' 
            self.GET_response_status_code = 200
            self.__format_response__()
            app.logger.info(f"(422) ApiDLG_INFO Recoverid Error: UID={self.args['UID']}: RSP_ERROR=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code
        #
        # Esta en la REDIS...
        if r_conf.status_code == 200:
            d_rsp = r_conf.json()
            new_id = d_rsp['id']
            app.logger.info(f"(423) ApiDLG INFO Recoverid (uid,id) in REDIS: NEW_ID={new_id}")
            self.GET_response = f"CLASS=RECOVER&ID={new_id}"
            self.GET_response_status_code = 200
            self.__format_response__()
            app.logger.info(f"(424) ApiDLG_INFO CLASS={self.args['CLASS']},ID={new_id},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code
        #

        # No esta en REDIS: buscamos en SQL
        try:
            r_conf = requests.get(f'http://{APICONF_HOST}:{APICONF_PORT}/apiconf/uid2id', params={'uid':self.args['UID']}, timeout=10 )
        except requests.exceptions.RequestException as err: 
            app.logger.info(f"(425) ApiDLG_ERR001: Redis request exception', Err:{err}")
            self.GET_response = 'CONFIG=ERROR' 
            self.GET_response_status_code = 200
            self.__format_response__()
            app.logger.info(f"(426) ApiDLG_INFO UID={self.args['UID']}: RSP_ERROR=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code
        #
        # Esta en SQL
        if r_conf.status_code == 200:
            d_rsp = r_conf.json()
            new_id = d_rsp['id']
            app.logger.info(f"(427) ApiDLG INFO Recoverid (uid,id) in SQL: NEW_ID={new_id}")
            self.GET_response = f"CLASS=RECOVER&ID={new_id}"
            self.GET_response_status_code = 200
            self.__format_response__()
            app.logger.info(f"(428) ApiDLG_INFO CLASS={self.args['CLASS']},ID={new_id},RSP=[{self.GET_response}]")
            #
            # Actualizo la redis y mando la respuesta al equipo
            d_conf = {'id':new_id,'uid':self.args['UID']}
            try:
                r_conf = requests.put(f'http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/uid2id', json=d_conf, timeout=10 )
            except requests.exceptions.RequestException as err: 
                app.logger.info(f"(429) ApiDLG_ERR001: Redis request exception', Err:{err}")
            #
            app.logger.info(f"(430) ApiDLG INFO Recoverid SQL update Redis: ID={new_id}")
            return self.GET_response, self.GET_response_status_code
        #
        # No estaba en Redis ni SQL
        elif r_conf.status_code == 204:
            # No hay datos en la SQL tampoco: Debo salir
            app.logger.info(f"(431) ApiDLG_INFO UID2DLGID_ERROR: UID={self.args['UID']}, Err:No Rcd en SQL. Err=({r_conf.status_code}){r_conf.text}")
            self.GET_response = 'CONFIG=ERROR;NO HAY REGISTRO EN BD' 
            self.GET_response_status_code = 200
            self.__format_response__()
            return self.GET_response, self.GET_response_status_code
        #
        # Error general
        self.GET_response = 'CONFIG=ERROR' 
        self.GET_response_status_code = 200
        self.__format_response__()
        app.logger.info(f"(432) ApiDLG INFO UID={self.args['UID']}: RSP_ERROR=[{self.GET_response}]")
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
            app.logger.info(f"(433) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code

        # Actualizo RECOVER UID2ID
        self.UID = self.args['UID']
        self.__update_uid2id__(self.ID, self.UID)

        # Calculo el hash de la configuracion de la BD.
        bd_hash = self.dlgutils.get_hash_config_base(self.d_conf, self.VER )
        if self.ID == self.debug_unit_id:
            app.logger.info(f"(434) ApiDLG_INFO ID={self.args['ID']}, BD_hash={bd_hash}, UI_hash={int(self.args['HASH'],16)}")
        #print(f"DEBUG::__get_conf_base__: bd_hash={bd_hash}, dlg_hash={self.args['HASH']}")
        if bd_hash == int(self.args['HASH'],16):
            self.GET_response = 'CLASS=CONF_BASE&CONFIG=OK'
            self.GET_response_status_code = 200
            self.__format_response__()
            app.logger.info(f"(435) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code
            
        # No coinciden: mando la nueva configuracion
        self.GET_response = self.dlgutils.get_response_base(self.d_conf, self.VER )
        self.GET_response_status_code = 200
        self.__format_response__()
        app.logger.info(f"(436) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
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
            app.logger.info(f"(437) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code

        # Calculo el hash de la configuracion de la BD.
        bd_hash = self.dlgutils.get_hash_config_ainputs(self.d_conf,self.VER )
        if self.ID == self.debug_unit_id:
            app.logger.info(f"(438) ApiDLG_INFO ID={self.args['ID']}, BD_hash={bd_hash}, UI_hash={int(self.args['HASH'],16)}")
        #print(f"DEBUG::__get_conf_ainputs__: bd_hash={bd_hash}, dlg_hash={self.args['HASH']}")
        if bd_hash == int(self.args['HASH'],16):
            self.GET_response = 'CLASS=CONF_AINPUTS&CONFIG=OK'
            self.GET_response_status_code = 200
            self.__format_response__()
            app.logger.info(f"(319) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code
            
        # No coinciden: mando la nueva configuracion
        self.GET_response = self.dlgutils.get_response_ainputs(self.d_conf,self.VER )
        self.GET_response_status_code = 200
        self.__format_response__()
        app.logger.info(f"(440) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
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
            app.logger.info(f"(441) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code

        # Calculo el hash de la configuracion de la BD.
        bd_hash = self.dlgutils.get_hash_config_counters(self.d_conf,self.VER )
        if self.ID == self.debug_unit_id:
            app.logger.info(f"(442) ApiDLG_INFO ID={self.args['ID']}, BD_hash={bd_hash}, UI_hash={int(self.args['HASH'],16)}")
        if bd_hash == int(self.args['HASH'],16):
            self.GET_response = 'CLASS=CONF_COUNTERS&CONFIG=OK'
            self.GET_response_status_code = 200
            self.__format_response__()
            app.logger.info(f"(443) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code
            
        # No coinciden: mando la nueva configuracion
        self.GET_response = self.dlgutils.get_response_counters(self.d_conf,self.VER )
        self.GET_response_status_code = 200
        self.__format_response__()
        app.logger.info(f"(424) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
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
            app.logger.info(f"(444) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code

        # Calculo el hash de la configuracion de la BD.
        bd_hash = self.dlgutils.get_hash_config_modbus(self.d_conf,self.VER )
        if self.ID == self.debug_unit_id:
            app.logger.info(f"(445) ApiDLG_INFO ID={self.args['ID']}, BD_hash={bd_hash}, UI_hash={int(self.args['HASH'],16)}")
        if bd_hash == int(self.args['HASH'],16):
            self.GET_response = 'CLASS=CONF_MODBUS&CONFIG=OK'
            self.GET_response_status_code = 200
            self.__format_response__()
            app.logger.info(f"(446) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code
            
        # No coinciden: mando la nueva configuracion
        self.GET_response = self.dlgutils.get_response_modbus(self.d_conf,self.VER)
        self.GET_response_status_code = 200
        self.__format_response__()
        app.logger.info(f"(447) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
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
            app.logger.error(f"(448) ApiDLG_INFO CLASS={self.CLASS},ID={self.ID},ERROR AL GUARDAR DATA EN REDIS. Err=({r_datos.status_code}){r_datos.text}")
        #
        # 3) Leo las ordenes
        r_ordenes = requests.get(f"http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/ordenes", params={'unit':self.ID }, timeout=10 )
        d_ordenes = None
        if r_ordenes.status_code == 200:
            d_ordenes = r_ordenes.json()
            ordenes = d_ordenes.get('ordenes','')
            if self.ID == self.debug_unit_id:
                app.logger.info(f"(449) ApiDLG INFO CLASS={self.CLASS},ID={self.ID}, D_ORDENES={d_ordenes}")
        elif r_ordenes.status_code == 204:
            # Si da error genero un mensaje pero continuo para no trancar al datalogger.
            if self.ID == self.debug_unit_id:
                app.logger.info(f"(450) ApiDLG INFO CLASS={self.CLASS},ID={self.ID},NO HAY RCD ORDENES")
            ordenes = ''
        else:
            app.logger.error(f"(451) ApiDLG INFO CLASS={self.CLASS},ID={self.ID},ERROR AL LEER ORDENES. Err=({r_ordenes.status_code}){r_ordenes.text}")
            ordenes = ''
        #
        # 3.1) Si RESET entonces borro la configuracion
        if 'RESET' in ordenes:
            _ = requests.delete(f"http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/delete", params={'unit':self.ID}, timeout=10 )
            app.logger.info(f"(452) ApiDLG INFO CLASS={self.CLASS},ID={self.ID}, DELETE REDIS RCD.")
        #
        # 3.2) Borro las ordenes
        _ = requests.delete(f"http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/ordenes", params={'unit':self.ID}, timeout=10 )

        # 4) Respondo
        now=dt.datetime.now().strftime('%y%m%d%H%M')
        self.GET_response = f'CLASS=DATA&CLOCK={now};{ordenes}'
        self.GET_response_status_code = 200
        self.__format_response__()
        app.logger.info(f"(453) ApiDLG INFO CLASS={self.CLASS},ID={self.ID},RSP=[{self.GET_response}]")
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
        app.logger.info("(435) ApiDLG INFO DLG_QS=%(a)s", {'a': request.query_string })
        if self.ID == self.debug_unit_id:
            app.logger.debug("CLASS=%(a)s", {'a': self.args['CLASS'] })
        
        # Los PING siempre se responden !!
        if self.CLASS == 'PING':
            return self.__process_ping__()

        if self.CLASS == 'DATA':
            return self.__process_data__()
        
        if self.CLASS == 'RECOVER':
            return self.__process_conf_recover__() 
        
        # Leo la configuracion porque lo requieren las otras clases
        if not self.__read_configuration__():
            self.GET_response = 'CONFIG=ERROR'
            self.GET_response_status_code = 200
            self.__format_response__()
            app.logger.info(f"(454) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code
        
        # Analizo los tipos de frames
        # No acepto frames con ID DEFAULT.
        if self.ID == 'DEFAULT':
            self.GET_response = 'CONFIG=ERROR'
            self.GET_response_status_code = 200
            self.__format_response__()
            app.logger.info(f"(455) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code
        
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
        app.logger.info(f"(456) ApiDLG INFO CLASS={self.CLASS},ID={self.ID},RSP=[{self.GET_response}]")
        return self.GET_response, self.GET_response_status_code
    
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
            app.logger.info( f'(457) ApiDLG_ERR001: Redis request exception, HOST:{APIREDIS_HOST}:{APIREDIS_PORT}, Err:{err}')
        #
        # Pruebo la conexion a SQL
        sql_status = 'ERR'
        try:
            r_conf = requests.get(f"http://{APICONF_HOST}:{APICONF_PORT}/apiconf/ping",timeout=10 )
            if r_conf.status_code == 200:
                sql_status = 'OK'
        except requests.exceptions.RequestException as err: 
            app.logger.info( f'(458) ApiDLG_ERR002: Sql request exception, HOST:{APICONF_HOST}:{APICONF_PORT}, Err:{err}')
        #
        #
        if redis_status == 'OK' and sql_status == 'OK':
            ping_status = 'OK'
        else:
            ping_status = 'FAIL'
            
        return {'rsp':f'{ping_status}','redis_status':redis_status, 'sql_status':sql_status, 'version':API_VERSION, 'API_REDIS':f'{APIREDIS_HOST}:{APIREDIS_PORT}','API_CONF':f'{APICONF_HOST}:{APICONF_PORT}' }, 200

class Help(Resource):
    '''
    Devuelve el estado de la conexion a la BD Redis.
    '''
    def get(self):
        '''
        '''
        return {}, 200

api.add_resource( ApiDlg, '/apidlg')
api.add_resource( Help, '/apidlg/help')
api.add_resource( Ping, '/apidlg/ping')

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

    app.logger.info( f'Starting ApiDLG: REDIS_HOST={APIREDIS_HOST}, REDIS_PORT={APIREDIS_PORT}' )
    app.logger.info( f'         ApiDLG: CONF_HOST={APICONF_HOST}, CONF_PORT={APICONF_PORT}' )

if __name__ == '__main__':
    APIREDIS_HOST = '127.0.0.1'
    APICONF_HOST = '127.0.0.1'
    app.run(host='0.0.0.0', port=5000, debug=True)
