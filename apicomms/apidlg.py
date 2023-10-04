#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python
'''
API de comunicaciones SPCOMMS para los dataloggers y plc.
-----------------------------------------------------------------------------
R002 @ 2023-09-13: (commsv3_apicomms:1.2)
- Agrego a la configuracion las consignas

R001 @ 2023-06-15: (commsv3_apicomms:1.1)
- Se modifica el procesamiento de frames de modo que al procesar uno de DATA sea
  como los PING, no se lee la configuracion ya que no se necesita y genera carga
  innecesaria.
- Se manejan todos los parámetros por variables de entorno
- Se agrega un entrypoint 'ping' que permite ver si la api esta operativa

'''

import datetime as dt
import requests
from flask_restful import Resource, request, reqparse
import apidlg_utils
from apicomms_common import Utils

API_VERSION = 'R001 @ 2023-06-23'

class ApiDlg(Resource):
    ''' 
    Clase especializada en atender los dataloggers
    '''
    def __init__(self, **kwargs):
        self.app = kwargs['app']
        self.servers = kwargs['servers']
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
        self.url_redis = f"http://{self.servers['APIREDIS_HOST']}:{self.servers['APIREDIS_PORT']}/apiredis/"
        self.url_conf = f"http://{self.servers['APICONF_HOST']}:{self.servers['APICONF_PORT']}/apiconf/"

    def __update_uid2id__(self, id, uid):
        '''
        '''
        try:
            r_conf = requests.get(self.url_redis + '/uid2id', params={'uid':self.args['UID']}, timeout=10 )
        except requests.exceptions.RequestException as err: 
            self.app.logger.info(f"(500) ApiDLG_ERR001: Redis request exception', Err:{err}")
            self.app.logger.info(f"(501) ApiDLG_INFO Recoverid Error: UID={self.args['UID']}: RSP_ERROR=[{self.GET_response}]")
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
            r_conf = requests.put(self.url_redis + 'uid2id', json=d_conf, timeout=10 )
            self.app.logger.info("(502) ApiDLG_INFO uid2id update Redis")
        except requests.exceptions.RequestException as err: 
            self.app.logger.info(f"(503) ApiDLG_ERR001: Redis request exception', Err:{err}")
        #
        try:
            r_conf = requests.put(self.url_conf + 'uid2id', json=d_conf, timeout=10 )
            self.app.logger.info("(504) ApiDLG_INFO uid2id update SQL")
        except requests.exceptions.RequestException as err: 
            self.app.logger.info(f"(505) ApiDLG_ERR001: Redis request exception', Err:{err}")        
        #
 
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
        self.app.logger.info(f"(510) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
        return self.GET_response, self.GET_response_status_code

    def __process_conf_recover__(self):
        '''
        '''
        self.parser.add_argument('UID', type=str ,location='args', required=True)
        self.args = self.parser.parse_args()
        #
        # Vemos si la redis tiene los datos uid->id
        try:
            r_conf = requests.get(self.url_redis + 'uid2id', params={'uid':self.args['UID']}, timeout=10 )
        except requests.exceptions.RequestException as err: 
            self.app.logger.info(f"(520) ApiDLG_ERR001: Redis request exception', Err:{err}")
            self.GET_response = 'CONFIG=ERROR' 
            self.GET_response_status_code = 200
            self.__format_response__()
            self.app.logger.info(f"(521) ApiDLG_INFO Recoverid Error: UID={self.args['UID']}: RSP_ERROR=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code
        #
        # Esta en la REDIS...
        if r_conf.status_code == 200:
            d_rsp = r_conf.json()
            new_id = d_rsp['id']
            self.app.logger.info(f"(522) ApiDLG_INFO Recoverid (uid,id) in REDIS: NEW_ID={new_id}")
            self.GET_response = f"CLASS=RECOVER&ID={new_id}"
            self.GET_response_status_code = 200
            self.__format_response__()
            self.app.logger.info(f"(523) ApiDLG_INFO CLASS={self.args['CLASS']},ID={new_id},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code
        #

        # No esta en REDIS: buscamos en SQL
        try:
            r_conf = requests.get(self.url_conf + 'uid2id', params={'uid':self.args['UID']}, timeout=10 )
        except requests.exceptions.RequestException as err: 
            self.app.logger.info(f"(524) ApiDLG_ERR001: Redis request exception', Err:{err}")
            self.GET_response = 'CONFIG=ERROR' 
            self.GET_response_status_code = 200
            self.__format_response__()
            self.app.logger.info(f"(525) ApiDLG_INFO UID={self.args['UID']}: RSP_ERROR=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code
        #
        # Esta en SQL
        if r_conf.status_code == 200:
            d_rsp = r_conf.json()
            new_id = d_rsp['id']
            self.app.logger.info(f"(526) ApiDLG_INFO Recoverid (uid,id) in SQL: NEW_ID={new_id}")
            self.GET_response = f"CLASS=RECOVER&ID={new_id}"
            self.GET_response_status_code = 200
            self.__format_response__()
            self.app.logger.info(f"(527) ApiDLG_INFO CLASS={self.args['CLASS']},ID={new_id},RSP=[{self.GET_response}]")
            #
            # Actualizo la redis y mando la respuesta al equipo
            d_conf = {'id':new_id,'uid':self.args['UID']}
            try:
                r_conf = requests.put(self.url_conf + 'uid2id', json=d_conf, timeout=10 )
            except requests.exceptions.RequestException as err: 
                self.app.logger.info(f"(528) ApiDLG_ERR001: Redis request exception', Err:{err}")
            #
            self.app.logger.info(f"(529) ApiDLG_INFO Recoverid SQL update Redis: ID={new_id}")
            return self.GET_response, self.GET_response_status_code
        #
        # No estaba en Redis ni SQL
        elif r_conf.status_code == 204:
            # No hay datos en la SQL tampoco: Debo salir
            self.app.logger.info(f"(530) ApiDLG_INFO UID2DLGID_ERROR: UID={self.args['UID']}, Err:No Rcd en SQL. Err=({r_conf.status_code}){r_conf.text}")
            self.GET_response = 'CONFIG=ERROR;NO HAY REGISTRO EN BD' 
            self.GET_response_status_code = 200
            self.__format_response__()
            return self.GET_response, self.GET_response_status_code
        #
        # Error general
        self.GET_response = 'CONFIG=ERROR' 
        self.GET_response_status_code = 200
        self.__format_response__()
        self.app.logger.info(f"(531) ApiDLG_INFO UID={self.args['UID']}: RSP_ERROR=[{self.GET_response}]")
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
            self.app.logger.info(f"(540) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code

        # Actualizo RECOVER UID2ID
        self.UID = self.args['UID']
        self.__update_uid2id__(self.ID, self.UID)

        # Calculo el hash de la configuracion de la BD.
        bd_hash = self.dlgutils.get_hash_config_base(self.d_conf, self.VER )
        if self.ID == self.debug_unit_id:
            self.app.logger.info(f"(541) ApiDLG_INFO ID={self.args['ID']}, Base: BD_hash={bd_hash}, UI_hash={int(self.args['HASH'],16)}")
        #print(f"DEBUG::__get_conf_base__: bd_hash={bd_hash}, dlg_hash={self.args['HASH']}")
        if bd_hash == int(self.args['HASH'],16):
            self.GET_response = 'CLASS=CONF_BASE&CONFIG=OK'
            self.GET_response_status_code = 200
            self.__format_response__()
            self.app.logger.info(f"(542) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code
            
        # No coinciden: mando la nueva configuracion
        self.GET_response = self.dlgutils.get_response_base(self.d_conf, self.VER )
        self.GET_response_status_code = 200
        self.__format_response__()
        self.app.logger.info(f"(543) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
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
            self.app.logger.info(f"(550) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code

        # Calculo el hash de la configuracion de la BD.
        bd_hash = self.dlgutils.get_hash_config_ainputs(self.d_conf,self.VER )
        if self.ID == self.debug_unit_id:
            self.app.logger.info(f"(551) ApiDLG_INFO ID={self.args['ID']}, Ainputs: BD_hash={bd_hash}, UI_hash={int(self.args['HASH'],16)}")
        #print(f"DEBUG::__get_conf_ainputs__: bd_hash={bd_hash}, dlg_hash={self.args['HASH']}")
        if bd_hash == int(self.args['HASH'],16):
            self.GET_response = 'CLASS=CONF_AINPUTS&CONFIG=OK'
            self.GET_response_status_code = 200
            self.__format_response__()
            self.app.logger.info(f"(552) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code
            
        # No coinciden: mando la nueva configuracion
        self.GET_response = self.dlgutils.get_response_ainputs(self.d_conf,self.VER )
        self.GET_response_status_code = 200
        self.__format_response__()
        self.app.logger.info(f"(553) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
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
            self.app.logger.info(f"(560) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code

        # Calculo el hash de la configuracion de la BD.
        bd_hash = self.dlgutils.get_hash_config_counters(self.d_conf,self.VER )
        if self.ID == self.debug_unit_id:
            self.app.logger.info(f"(561) ApiDLG_INFO ID={self.args['ID']}, Counters: BD_hash={bd_hash}, UI_hash={int(self.args['HASH'],16)}")
        if bd_hash == int(self.args['HASH'],16):
            self.GET_response = 'CLASS=CONF_COUNTERS&CONFIG=OK'
            self.GET_response_status_code = 200
            self.__format_response__()
            self.app.logger.info(f"(562) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code
            
        # No coinciden: mando la nueva configuracion
        self.GET_response = self.dlgutils.get_response_counters(self.d_conf,self.VER )
        self.GET_response_status_code = 200
        self.__format_response__()
        self.app.logger.info(f"(563) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
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
            self.app.logger.info(f"(570) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code

        # Calculo el hash de la configuracion de la BD.
        bd_hash = self.dlgutils.get_hash_config_modbus(self.d_conf,self.VER )
        if self.ID == self.debug_unit_id:
            self.app.logger.info(f"(571) ApiDLG_INFO ID={self.args['ID']}, Modbus: BD_hash={bd_hash}, UI_hash={int(self.args['HASH'],16)}")
        if bd_hash == int(self.args['HASH'],16):
            self.GET_response = 'CLASS=CONF_MODBUS&CONFIG=OK'
            self.GET_response_status_code = 200
            self.__format_response__()
            self.app.logger.info(f"(572) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code
            
        # No coinciden: mando la nueva configuracion
        self.GET_response = self.dlgutils.get_response_modbus(self.d_conf,self.VER)
        self.GET_response_status_code = 200
        self.__format_response__()
        self.app.logger.info(f"(573) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
        return self.GET_response, self.GET_response_status_code
    
    def __process_conf_piloto__(self):
        '''
        '''
        # ID=PABLO&TYPE=SPXR3&VER=1.0.0&CLASS=CONF_PILOTO&HASH=0x86
        self.parser.add_argument('HASH', type=str ,location='args', required=True)
        self.args = self.parser.parse_args()
        #
        # Chequeo la configuracion
        if self.d_conf is None:
            self.GET_response = 'CLASS=CONF_PILOTO&CONFIG=ERROR' 
            self.GET_response_status_code = 200
            self.__format_response__()
            self.app.logger.info(f"(590) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code

        d_conf_piloto = self.d_conf.get('PILOTO',{})
        # Calculo el hash de la configuracion de la BD.
        bd_hash = self.dlgutils.get_hash_config_piloto( d_conf_piloto,self.VER )
        if self.ID == self.debug_unit_id:
            self.app.logger.info(f"(591) ApiDLG_INFO ID={self.args['ID']}, D_PILOTO={d_conf_piloto}")
            self.app.logger.info(f"(592) ApiDLG_INFO ID={self.args['ID']}, Piloto: BD_hash={bd_hash}, UI_hash={int(self.args['HASH'],16)}")
        if bd_hash == int(self.args['HASH'],16):
            self.GET_response = 'CLASS=CONF_PILOTO&CONFIG=OK'
            self.GET_response_status_code = 200
            self.__format_response__()
            self.app.logger.info(f"(593) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code
            
        # No coinciden: mando la nueva configuracion
        self.GET_response = self.dlgutils.get_response_piloto(d_conf_piloto,self.VER )
        self.GET_response_status_code = 200
        self.__format_response__()
        self.app.logger.info(f"(594) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
        return self.GET_response, self.GET_response_status_code
 
    def __process_conf_consigna__(self):
        '''
        '''
        # ID=PABLO&TYPE=SPXR3&VER=1.0.0&CLASS=CONF_PILOTO&HASH=0x86
        self.parser.add_argument('HASH', type=str ,location='args', required=True)
        self.args = self.parser.parse_args()
        #
        # Chequeo la configuracion
        if self.d_conf is None:
            self.GET_response = 'CLASS=CONF_CONSIGNA&CONFIG=ERROR' 
            self.GET_response_status_code = 200
            self.__format_response__()
            self.app.logger.info(f"(600) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code

        d_conf_consigna = self.d_conf.get('CONSIGNA',{})
        # Calculo el hash de la configuracion de la BD.
        bd_hash = self.dlgutils.get_hash_config_consigna( d_conf_consigna,self.VER )
        if self.ID == self.debug_unit_id:
            self.app.logger.info(f"(601) ApiDLG_INFO ID={self.args['ID']}, D_CONSIGNA={d_conf_consigna}")
            self.app.logger.info(f"(602) ApiDLG_INFO ID={self.args['ID']}, Consigna: BD_hash={bd_hash}, UI_hash={int(self.args['HASH'],16)}")
        if bd_hash == int(self.args['HASH'],16):
            self.GET_response = 'CLASS=CONF_CONSIGNA&CONFIG=OK'
            self.GET_response_status_code = 200
            self.__format_response__()
            self.app.logger.info(f"(603) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code
            
        # No coinciden: mando la nueva configuracion
        self.GET_response = self.dlgutils.get_response_consigna(d_conf_consigna,self.VER )
        self.GET_response_status_code = 200
        self.__format_response__()
        self.app.logger.info(f"(604) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
        return self.GET_response, self.GET_response_status_code

    def __process_data__(self):
        '''
        '''
        # ID=PABLO&TYPE=SPXR3&VER=1.0.0&CLASS=DATA&DATE=230321&TIME=094504&A0=0.00&A1=0.00&A2=0.00&C0=0.000&C1=0.000&bt=12.496
        # request.args es un dict con todos los pares key:value del url.
        d_payload = self.dlgutils.convert_dataline2dict(request.args, self.VER)
        
        if d_payload is None:
            return 'ERROR:UNKNOWN VERSION',200

        # 1) Guardo los datos
        r_datos = requests.put(self.url_redis + 'dataline', params={'unit':self.ID,'type':'DLG'}, json=d_payload, timeout=10 )
        if r_datos.status_code != 200:
            # Si da error genero un mensaje pero continuo para no trancar al datalogger.
            self.app.logger.error(f"(580) ApiDLG_INFO CLASS={self.CLASS},ID={self.ID},ERROR AL GUARDAR DATA EN REDIS. Err=({r_datos.status_code}){r_datos.text}")
        #
        # 3) Leo las ordenes
        r_ordenes = requests.get(self.url_redis + 'ordenes', params={'unit':self.ID }, timeout=10 )
        d_ordenes = None
        if r_ordenes.status_code == 200:
            d_ordenes = r_ordenes.json()
            ordenes = d_ordenes.get('ordenes','')
            if self.ID == self.debug_unit_id:
                self.app.logger.info(f"(581) ApiDLG_INFO CLASS={self.CLASS},ID={self.ID}, D_ORDENES={d_ordenes}")
        elif r_ordenes.status_code == 204:
            # Si da error genero un mensaje pero continuo para no trancar al datalogger.
            if self.ID == self.debug_unit_id:
                self.app.logger.info(f"(582) ApiDLG_INFO CLASS={self.CLASS},ID={self.ID},NO HAY RCD ORDENES")
            ordenes = ''
        else:
            self.app.logger.error(f"(583) ApiDLG_INFO CLASS={self.CLASS},ID={self.ID},ERROR AL LEER ORDENES. Err=({r_ordenes.status_code}){r_ordenes.text}")
            ordenes = ''
        #
        # 3.1) Si RESET entonces borro la configuracion
        if 'RESET' in ordenes:
            _ = requests.delete(self.url_redis + 'delete', params={'unit':self.ID}, timeout=10 )
            self.app.logger.info(f"(584) ApiDLG_INFO CLASS={self.CLASS},ID={self.ID}, DELETE REDIS RCD.")
        #
        # 3.2) Borro las ordenes
        _ = requests.delete(self.url_redis + 'ordenes', params={'unit':self.ID}, timeout=10 )

        # 4) Respondo
        now=dt.datetime.now().strftime('%y%m%d%H%M')
        self.GET_response = f'CLASS=DATA&CLOCK={now};{ordenes}'
        self.GET_response_status_code = 200
        self.__format_response__()
        self.app.logger.info(f"(585) ApiDLG_INFO CLASS={self.CLASS},ID={self.ID},RSP=[{self.GET_response}]")
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
        try:
            self.args = self.parser.parse_args()
        except:
            self.app.logger.info("(590) ERROR ApiDLG_QS=%(a)s", {'a': request.query_string })
            self.GET_response = 'ERROR:FAIL TO PARSE'
            self.GET_response_status_code = 500
            self.__format_response__()
            self.app.logger.info(f"(594) ApiDLG_INFO CLASS={self.CLASS},ID={self.ID},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code

        self.ID = self.args['ID']
        self.VER = self.args['VER']
        self.TYPE = self.args['TYPE']
        self.CLASS = self.args['CLASS']

        utils=Utils( {'id':self.ID, 'app':self.app, 'servers':self.servers} )
        
        # Leo el debugdlgid
        self.debug_unit_id = utils.read_debug_id()
        # Logs generales.
        self.app.logger.info("(590) ApiDLG_INFO DLG_QS=%(a)s", {'a': request.query_string })
        if self.ID == self.debug_unit_id:
            self.app.logger.debug("CLASS=%(a)s", {'a': self.args['CLASS'] })
        
        # Los PING siempre se responden !!
        if self.CLASS == 'PING':
            return self.__process_ping__()

        if self.CLASS == 'DATA':
            return self.__process_data__()
        
        if self.CLASS == 'RECOVER':
            return self.__process_conf_recover__() 
        
        # Leo la configuracion porque lo requieren las otras clases
        self.d_conf = utils.read_configuration((self.ID == self.debug_unit_id)) 
        if self.d_conf is None :
            self.GET_response = 'CONFIG=ERROR'
            self.GET_response_status_code = 200
            self.__format_response__()
            self.app.logger.info(f"(591) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code
        
        # Analizo los tipos de frames
        # No acepto frames con ID DEFAULT.
        if self.ID == 'DEFAULT':
            self.GET_response = 'CONFIG=ERROR'
            self.GET_response_status_code = 200
            self.__format_response__()
            self.app.logger.info(f"(592) ApiDLG_INFO CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return self.GET_response, self.GET_response_status_code
        
        if self.CLASS == 'CONF_BASE':
            return self.__process_conf_base__()
        
        if self.CLASS == 'CONF_AINPUTS':
            return self.__process_conf_ainputs__()

        if self.CLASS == 'CONF_COUNTERS':
            return self.__process_conf_counters__()

        if self.CLASS == 'CONF_MODBUS':
            return self.__process_conf_modbus__()
        
        if self.CLASS == 'CONF_PILOTO':
            return self.__process_conf_piloto__()
        
        if self.CLASS == 'CONF_CONSIGNA':
            return self.__process_conf_consigna__()
        
        self.GET_response = 'ERROR:UNKNOWN FRAME TYPE'
        self.GET_response_status_code = 200
        self.__format_response__()
        self.app.logger.info(f"(593) ApiDLG_INFO CLASS={self.CLASS},ID={self.ID},RSP=[{self.GET_response}]")
        return self.GET_response, self.GET_response_status_code
    
