#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python
'''
API de comunicaciones SPCOMMS para los dataloggers y plc.

Testing:
Para probar los dataloggers, se generan los frames con POSTMAN

Para los PLC
1- Crear en redis una unidad de prueba PLCTEST y usar la configuracion
d_conf = {'MEMBLOCK': {'RCVD_MBK_DEF': [['UPA1_CAUDALIMETRO', 'float', 0],
   ['UPA1_STATE1', 'uchar', 1],
   ['UPA1_POS_ACTUAL_6', 'short', 8],
   ['UPA2_CAUDALIMETRO', 'float', 0],
   ['BMB_STATE18', 'uchar', 1],
   ['BMB_STATE19', 'uchar', 1]],
  'SEND_MBK_DEF': [['UPA1_ORDER_1', 'short', 1],
   ['UPA1_CONSIGNA_6', 'short', 2560],
   ['ESP_ORDER_8', 'short', 200],
   ['NIVEL_TQ_KIYU', 'float', 2560]],
  'RCVD_MBK_LENGTH': 15,
  'SEND_MBK_LENGTH': 10}}

Desde una consola python hacemos:
r_conf=requests.put('http://127.0.0.1:5100/apiredis/configuracion',params={'unit':'PLCTEST'}, json=json.dumps(d_conf))

Supongamos que el PLC tiene los siguientes datos para enviar:
d={'UPA1_CAUDALIMETRO': 123.45,
 'UPA1_STATE1': 100,
 'UPA1_POS_ACTUAL_6': 120,
 'UPA2_CAUDALIMETRO': 32.45,
 'BMB_STATE18': 20,
 'BMB_STATE19': 40
 }

EL bytestring que debemos transmitir al servidor para que procese es:
( los detalles verlos en plcmemblocks.py )

data = b'f\xe6\xf6Bdx\x00\xcd\xcc\x01B\x14(\x8dU'
r_conf=requests.post('http://127.0.0.1:500/apicomms',params={'ID':'PLCTEST','TYPE':'PLCR2','VER':'1.0.0'}, data=data, headers={'Content-Type': 'application/octet-stream'})

En el log de la apicomms vamos a ver que se decodifica correctamente.
'''

import os
import json
import datetime as dt
import requests
from flask import Flask, request, make_response
from flask_restful import Resource, Api, reqparse
import dlgSPXR3
import plcmemblocks

app = Flask(__name__)
api = Api(app)

APIREDIS_HOST = os.environ.get('APIREDIS_HOST','127.0.0.1')
APIREDIS_PORT = os.environ.get('APIREDIS_PORT','5100' )
APISQL_HOST = os.environ.get('APISQL_HOST','192.168.0.6')
APISQL_PORT = os.environ.get('APISQL_PORT','8086')

print(f'APIREDIS: host={APIREDIS_HOST}, port={APIREDIS_PORT}')
print(f'APISQL: host={APISQL_HOST}, port={APISQL_PORT}')


class PlcTest(Resource):
    '''
    Clase de pruebas de PLCs
    '''
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('ID',type=str,location='args',required=True)
        parser.add_argument('VER',type=str,location='args',required=True)
        parser.add_argument('TYPE',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        app.logger.debug('APICOMMS: GET')
        return {'Msg':'SPYMOVIL OK', 'ID':args['ID'], 'VER':args['VER'], 'TYPE':args['TYPE'] } , 200

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('ID',type=str,location='args',required=True)
        parser.add_argument('VER',type=str,location='args',required=True)
        parser.add_argument('TYPE',type=str,location='args',required=True)
        args=parser.parse_args()

        app.logger.debug('APICOMMS: POST')

        rxdata = request.get_data()
        app.logger.debug(f'POST RX DATA = [{rxdata}]')

        sresp = b'respuesta de Spymovil'
        #sresp = b'\n\x0bf\xe6\xf6Bb\x04W\x02\xecq\xe4C:\x16\x00\x00\x00\x00\x00\x0b\xa3'
        response = make_response(sresp)
        response.headers['Content-type'] = 'application/binary'
        return response
    
        #return 'SPYMOVIL POST OK', 200
    
class ApiComms(Resource):
    ''' 
    Clase especializada en atender los dataloggers y PLCs
    '''
    def __init__(self):
        self.debug_unit_id = None
        self.unit_id = None
        self.args = None
        self.dlgutils = dlgSPXR3.dlgutils()
        self.d_conf = None
        self.mbk = plcmemblocks.Memblock(app)
        self.parser = None
        self.GET_response = ''
        self.GET_response_status_code = 0
        self.POST_response = ''
        self.POST_response_status_code = 0

    def __read_debug_id__(self):
        '''
        Consulta el nombre del equipo que debe logearse.
        '''
        r_conf = requests.get(f'http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/configuracion/debugid', timeout=10 )
        if r_conf.status_code == 200:
            self.debug_unit_id = r_conf.json()
            #app.logger.debug(f"DEBUG_DLGID={self.debug_unit_id}")
        else:
            app.logger.debug(f"ERROR: READ DEBUG_DLGID. Err=({r_conf.status_code}){r_conf.text}")

    def __read_configuration__(self):
        '''
        Lee la configuracion de la unidad y la deja en self.d_conf. Retorna True/False.
        '''
        # Intento leer desde REDIS.
        r_conf = requests.get(f'http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/configuracion', params={'unit':self.args['ID']}, timeout=10 )
        if r_conf.status_code == 200:
            self.d_conf = json.loads(r_conf.json())
            if self.unit_id == self.debug_unit_id:
                app.logger.debug(f"ID={self.args['ID']}, REDIS D_CONF={self.d_conf}")
            return True
        else:
            app.logger.debug(f"__read_configuration__. Err=({r_conf.status_code}){r_conf.text}")
        #
        # Intento leer desde SQL
        r_conf = requests.get(f'http://{APISQL_HOST}:{APISQL_PORT}/get/config', params={'dlgid':self.args['ID']}, timeout=10 )
        if r_conf.status_code == 200:
            if r_conf.json() == {}:
                app.logger.error(f"DLG CONFIG_ERROR: ID={self.args['ID']}, Err:No Rcd en SQL. Err=({r_conf.status_code}){r_conf.text}")
                self.GET_response = 'CONFIG=ERROR;NO HAY REGISTRO EN BD' 
                self.GET_response_status_code = 200
                app.logger.error(f"ID={self.args['ID']}: RSP_ERROR=[{self.GET_response}]")
                return False
        #
        elif r_conf.status_code == 204:
            # No hay datos en la SQL tampoco: Debo salir
            app.logger.error(f"DLG CONFIG_ERROR: ID={self.args['ID']}, Err:No Rcd en SQL. Err=({r_conf.status_code}){r_conf.text}")
            self.GET_response = 'CONFIG=ERROR;NO HAY REGISTRO EN BD' 
            self.GET_response_status_code = 200
            app.logger.error(f"ID={self.args['ID']}: RSP_ERROR=[{self.GET_response}]")
            return False
        #
        else:
            app.logger.error(f"DLG CONFIG_ERROR: ID={self.args['ID']}, Err: no puedo leer SQL. Err=({r_conf.status_code}){r_conf.text}")
            self.GET_response = 'CONFIG=ERROR' 
            self.GET_response_status_code = 200
            app.logger.error(f"ID={self.args['ID']}: RSP_ERROR=[{self.GET_response}]")
            return False
        #
        # La api sql me devuelve un dict, no un json !!
        self.d_conf = r_conf.json()
        app.logger.warning(f"ID={self.args['ID']}: SQL D_CONF={self.d_conf}")
        # Actualizo la redis.
        r_conf = requests.put(f'http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/configuracion', params={'unit':self.args['ID']}, json=json.dumps(self.d_conf), timeout=10 )
        if r_conf.status_code != 200:
            app.logger.error(f"DLG CONFIG_ERROR: ID={self.args['ID']}, Err: no puedo actualizar SQL config en REDIS. Err=({r_conf.status_code}){r_conf.text}")
            self.GET_response = 'CONFIG=ERROR' 
            self.GET_response_status_code = 200
            app.logger.error(f"ID={self.args['ID']}: RSP_ERROR=[{self.GET_response}]")
            return False
        #
        app.logger.warning(f"ID={self.args['ID']}, Config de SQL updated en Redis")
        return True
    
    def __GET_format_response__(self):
        '''
        Necesitamos este formateo para que los dlg. puedan parsear la respuesta
        '''
        #return f'<html><body><h1>{response}</h1></body></html>'
        self.GET_response = f'<html>{self.GET_response}</html>'
        app.logger.info(f"xmit_RSP=[{self.GET_response}]")

    def __GET_ping__(self):
        '''
        '''
        # ID=PABLO&TYPE=SPXR3&VER=1.0.0&CLASS=PING
        self.GET_response = 'CLASS=PONG'
        self.GET_response_status_code = 200
        app.logger.info(f"CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
        return

    def __GET_conf_base__(self):
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
            app.logger.error(f"CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return

        # Calculo el hash de la configuracion de la BD.
        bd_hash = self.dlgutils.get_hash_config_base(self.d_conf, self.args['VER'])
        #print(f"DEBUG::__get_conf_base__: bd_hash={bd_hash}, dlg_hash={self.args['HASH']}")
        if bd_hash == int(self.args['HASH'],16):
            self.GET_response = 'CLASS=CONF_BASE&CONFIG=OK'
            self.GET_response_status_code = 200
            app.logger.info(f"CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return
            
        # No coinciden: mando la nueva configuracion
        self.GET_response = self.dlgutils.get_response_base(self.d_conf, self.args['VER'])
        self.GET_response_status_code = 200
        app.logger.info(f"CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
        return

    def __GET_conf_ainputs__(self):
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
            app.logger.error(f"CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return

        # Calculo el hash de la configuracion de la BD.
        bd_hash = self.dlgutils.get_hash_config_ainputs(self.d_conf,self.args['VER'])
        #print(f"DEBUG::__get_conf_ainputs__: bd_hash={bd_hash}, dlg_hash={self.args['HASH']}")
        if bd_hash == int(self.args['HASH'],16):
            self.GET_response = 'CLASS=CONF_AINPUTS&CONFIG=OK'
            self.GET_response_status_code = 200
            app.logger.info(f"CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return
            
        # No coinciden: mando la nueva configuracion
        self.GET_response = self.dlgutils.get_response_ainputs(self.d_conf,self.args['VER'])
        self.GET_response_status_code = 200
        app.logger.info(f"CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
        return

    def __GET_conf_counters__(self):
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
            app.logger.error(f"CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return

        # Calculo el hash de la configuracion de la BD.
        bd_hash = self.dlgutils.get_hash_config_counters(self.d_conf,self.args['VER'])
        if bd_hash == int(self.args['HASH'],16):
            self.GET_response = 'CLASS=CONF_COUNTERS&CONFIG=OK'
            self.GET_response_status_code = 200
            app.logger.info(f"CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return
            
        # No coinciden: mando la nueva configuracion
        self.GET_response = self.dlgutils.get_response_counters(self.d_conf,self.args['VER'])
        self.GET_response_status_code = 200
        app.logger.info(f"CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
        return
    
    def __GET_conf_modbus__(self):
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
            app.logger.error(f"CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return

        # Calculo el hash de la configuracion de la BD.
        bd_hash = self.dlgutils.get_hash_config_modbus(self.d_conf,self.args['VER'])
        if bd_hash == int(self.args['HASH'],16):
            self.GET_response = 'CLASS=CONF_MODBUS&CONFIG=OK'
            self.GET_response_status_code = 200
            app.logger.info(f"CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
            return
            
        # No coinciden: mando la nueva configuracion
        self.GET_response = self.dlgutils.get_response_modbus(self.d_conf,self.args['VER'])
        self.GET_response_status_code = 200
        app.logger.info(f"CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
        return
    
    def __GET_data__(self):
        '''
        '''
        # ID=PABLO&TYPE=SPXR3&VER=1.0.0&CLASS=DATA&DATE=230321&TIME=094504&A0=0.00&A1=0.00&A2=0.00&C0=0.000&C1=0.000&bt=12.496
        # 1) Armo el payload.
        d_payload = {}
        for key in request.args:
            if key not in ('ID','TYPE','CLASS','VER'):
                d_payload[key] = request.args.get(key)
        #
        # 2) Guardo los datos
        r_data = requests.put(f'http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/dataline', params={'unit':self.args['ID'],'type':'DLG'}, json=json.dumps(d_payload), timeout=10 )
        if r_data.status_code != 200:
            # Si da error genero un mensaje pero continuo para no trancar al datalogger.
            app.logger.error(f"CLASS={self.args['CLASS']},ID={self.args['ID']},ERROR AL GUARDAR DATA EN REDIS. Err=({r_data.status_code}){r_data.text}")
        #
        # 3) Leo las ordenes
        r_data = requests.get(f'http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/ordenes', params={'unit':self.args['ID']}, timeout=10 )
        ordenes = ''
        if r_data.status_code == 200:
            ordenes = r_data.json()
            app.logger.info(f"CLASS={self.args['CLASS']},ID={self.args['ID']}, ORDENES=[{ordenes}]")
        elif r_data.status_code == 204:
            # Si da error genero un mensaje pero continuo para no trancar al datalogger.
            app.logger.info(f"CLASS={self.args['CLASS']},ID={self.args['ID']},NO HAY RCD ORDENES")
        else:
            app.logger.error(f"CLASS={self.args['CLASS']},ID={self.args['ID']},ERROR AL LEER ORDENES. Err=({r_data.status_code}){r_data.text}")
        #
        # 3.1) Si RESET entonces borro la configuracion
        if 'RESET' in [ordenes]:
            _ = requests.delete(f'http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/configuracion', params={'unit':self.args['ID']}, timeout=10 )
            app.logger.info(f"CLASS={self.args['CLASS']},ID={self.args['ID']}, DELETE REDIS RCD.")
        #
        # 4) Respondo
        now=dt.datetime.now().strftime('%y%m%d%H%M')
        self.GET_response = f'CLASS=DATA&CLOCK={now};{ordenes}'
        self.GET_response_status_code = 200
        app.logger.info(f"CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")
        return

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
        self.unit_id = self.args['ID']

        # Leo el debugdlgid
        self.__read_debug_id__()

        # Logs generales.
        app.logger.info("DLG_QS=%(a)s", {'a': request.query_string })
        if self.unit_id == self.debug_unit_id:
            app.logger.debug("CLASS=%(a)s", {'a': self.args['CLASS'] })
        
        # Los PING siempre se responden !!
        if self.args['CLASS'] == 'PING':
            self.__GET_ping__()
            self.__GET_format_response__()
            return self.GET_response, self.GET_response_status_code

        # Leo la configuracion
        if not self.__read_configuration__():
            self.__GET_format_response__()
            return self.GET_response, self.GET_response_status_code
        
        # Analizo los tipos de frames
        if self.args['CLASS'] == 'CONF_BASE':
            self.__GET_conf_base__()
        elif self.args['CLASS'] == 'CONF_AINPUTS':
            self.__GET_conf_ainputs__()
        elif self.args['CLASS'] == 'CONF_COUNTERS':
            self.__GET_conf_counters__()
        elif self.args['CLASS'] == 'CONF_MODBUS':
            self.__GET_conf_modbus__()
        elif self.args['CLASS'] == 'DATA':
            self.__GET_data__()
        else:
            self.GET_response = 'ERROR:UNKNOWN FRAME TYPE'
            self.GET_response_status_code = 200
            app.logger.info(f"CLASS={self.args['CLASS']},ID={self.args['ID']},RSP=[{self.GET_response}]")

        self.__GET_format_response__()
        return self.GET_response, self.GET_response_status_code
    
    def __POST_reception__(self):
        '''
        Debo convertir el byte stream recibido del PLC a un named dict de acuerdo al formato
        del rcvd_memblock. 
        '''
        if self.unit_id == self.debug_unit_id:
            app.logger.info(f'PLC={self.unit_id}, PRCESSING_RECEPTION')
        
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
        if self.unit_id == self.debug_unit_id:
            app.logger.info(f'PLC={self.unit_id}, d_rx_payload={d_payload}')
        # Guardo los datos a traves de la api.
        r_data = requests.put(f'http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/dataline', params={'unit':self.args['ID'],'type':'PLC'}, json=json.dumps(d_payload), timeout=10 )
        if r_data.status_code != 200:
            # Si da error genero un mensaje pero continuo para no trancar al datalogger.
            app.logger.error(f"PLC={self.unit_id}, ERROR AL GUARDAR DATA EN REDIS, Err={r_data.text}")
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
        if self.unit_id == self.debug_unit_id:
            app.logger.info(f'PLC={self.unit_id}, PRCESSING_RESPONSE')
        
        # Paso 1) REMVARS
        # Leo de la configuracion las variables remotas que debo enviar al PLC
        d_remvars = self.d_conf.get('REMVARS',{})
        if self.unit_id == self.debug_unit_id:
            app.logger.info(f'PLC={self.unit_id}, d_rem_vars={d_remvars}')

        # Leo los valores de los equipos remotos del d_remvars
        d_remote_datalines = {}
        for unit_id in d_remvars:
            r_data = requests.get(f'http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/dataline', params={'unit':unit_id}, timeout=10 )
            if r_data.status_code != 200:
                d_remote_datalines[unit_id] = {}
                # Si da error genero un mensaje pero continuo para no trancar al datalogger.
                app.logger.error(f"ID={self.args['ID']},ERROR AL LEER DATALINE. Err=({r_data.status_code}){r_data.text}")
            else:
                d_remote_datalines[unit_id] = json.loads(r_data.json())
        #
        if self.unit_id == self.debug_unit_id:
            app.logger.info(f'PLC={self.unit_id}, d_remote_datalines={d_remote_datalines}')

        # Armo el diccionario con las variables y valores de la respuesta al PLC
        d_responses = {}
        for unit_id in d_remvars:
            list_tvars = d_remvars[unit_id]
            for var_name_remoto, var_name_destino in list_tvars:
                # Leo el valor correspondiente al equipo remoto desde d_remote_datalines
                rem_value = d_remote_datalines[unit_id].get(var_name_remoto, -99)
                d_responses[var_name_destino] = rem_value
                if self.unit_id == self.debug_unit_id:
                    app.logger.info(f'PLC={self.unit_id}, read_remote_value={var_name_remoto}:{d_responses[var_name_destino]}')
        #
        # Agrego una nueva variable TIMESTAMP que es el timestamp HHMM que sirve para que el PLC pueda tener
        # contol si el enlace cayo y los valores de las variables caducaron.
        now = dt.datetime.now()
        now_str = now.strftime("%H%M")
        d_responses['TIMESTAMP'] = int(now_str)
        if self.unit_id == self.debug_unit_id:
            app.logger.info(f'PLC={self.unit_id}, d_responses={d_responses}')
        #
        # Paso 2) ATVISE
        # Leo las variables(ordenes) de  ATVISE y las agrego al diccionario de respuestas
        r_atvise = requests.get(f'http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/ordenes/atvise', params={'unit':self.unit_id}, timeout=10 )
        if r_atvise.status_code == 200:
            d_atvise_responses = json.loads(r_atvise.json())
            if self.unit_id == self.debug_unit_id:
                app.logger.info(f'PLC={self.unit_id}, d_atvise_responses={d_atvise_responses}')
        elif r_atvise.status_code == 204:
            d_atvise_responses = {}
            app.logger.info(f"ID={self.args['ID']}, NO HAY ORDENES DE ATVISE")
        else:
            d_atvise_responses = {}
            app.logger.error(f"ID={self.args['ID']}, NO PUEDE LEERSE ORDENES ATVISE, Err=({r_data.status_code}){r_data.text}")
        #
        # Paso 3)
        # Junto todas las variables de la respuesta en un solo diccionario
        #d_responses.update(d_atvise_responses)
        #print(f"DEBUG: type of d_responses = {type(d_responses)}")
        #print(f"DEBUG: type of d_atvise_responses = {type(d_atvise_responses)}")
        d_responses = { **d_responses, **d_atvise_responses }
        if self.unit_id == self.debug_unit_id:
            app.logger.info(f'PLC={self.unit_id}, d_responses={d_responses}')
        #
        # Paso 4)
        # Armo el bloque de respuestas a enviar apareando el d_responses con el mbk dando como resultado un rsp_dict.
        sresp = self.mbk.convert_dict2bytes( self.unit_id, d_responses)
        if self.unit_id == self.debug_unit_id:
            app.logger.info(f'PLC={self.unit_id}, sresp={sresp}')
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
        self.unit_id = self.args['ID']
    
        # Leo el debugdlgid
        self.__read_debug_id__()
        if self.unit_id == self.debug_unit_id:
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
        self.mbk.load_configuration(self.unit_id, d_mbk)
        if self.unit_id == self.debug_unit_id:
            app.logger.info(f"PLC: ID={self.args['ID']}, MBK={d_mbk}")
        
        # Recepcion
        if not self.__POST_reception__():
            app.logger.error(f"PLC={self.unit_id}, ERROR AL PROCESAR RCVDATA")
            self.POST_response = "RECEPTION_ERROR"
            self.POST_response_status_code = 204
            return self.POST_response, self.POST_response_status_code
        
        # Respuesta
        sresp = self.__POST_response__()
        #sresp = b'PLC respuesta de Spymovil'
        #sresp = b'\n\x0bf\xe6\xf6Bb\x04W\x02\xecq\xe4C:\x16\x00\x00\x00\x00\x00\x0b\xa3'
        #
        response = make_response(sresp)
        response.headers['Content-type'] = 'application/binary'
        return response

api.add_resource( PlcTest, '/apicomms/plctest')
api.add_resource( ApiComms, '/apicomms')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

