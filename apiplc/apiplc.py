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
from flask import Flask, request, make_response
from flask_restful import Resource, Api, reqparse
from pymodbus.utilities import computeCRC
from struct import pack
import apiplcR2_utils

app = Flask(__name__)
api = Api(app)

APIREDIS_HOST = os.environ.get('APIREDIS_HOST', 'apiredis')
APIREDIS_PORT = os.environ.get('APIREDIS_PORT', '5100')
APICONF_HOST = os.environ.get('APICONF_HOST', 'apiconf')
APICONF_PORT = os.environ.get('APICONF_PORT', '5200')
            
API_VERSION = 'R001 @ 2023-06-15'

class ApiPlcR2(Resource):
    ''' 
    Clase especializada en atender los dataloggers y PLCs
    '''
    def __init__(self):
        self.debug_unit_id = None
        self.args = None
        self.d_conf = None
        self.mbk = None
        self.ID = None
        self.VER = None
        self.TYPE = None
        self.d_ordenes_atvise = None

    def __read_debug_id__(self):
        '''
        Consulta el nombre del equipo que debe logearse.
        '''
        try:
            rsp = requests.get(f"http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/debugid", timeout=10 )
        except requests.exceptions.RequestException as err: 
            app.logger.info( f'(500) ApiPLCR2_ERR001: (read_debug_id) Redis request exception, Err:{err}')
            self.debug_unit_id = None
            return
        
        if rsp.status_code == 200:
            d = rsp.json()
            self.debug_unit_id = d.get('debugid','UDEBUG')
            #app.logger.debug(f"DEBUG_DLGID={self.debug_unit_id}")
        else:
            app.logger.info(f"(501) ApiPLCR2_WARN001: No debug unit, Err=({rsp.status_code}){rsp.text}")
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
            app.logger.info( f'(502) ApiPLCR2_ERR001: (read_configuration) Redis request exception, Err:{err}')
            return False
        #
        if r_conf.status_code == 200:
            self.d_conf = r_conf.json()
            if self.ID == self.debug_unit_id:
                app.logger.info(f"(503) ApiPLCR2_INFO: ID={self.args['ID']}, (Redis) D_CONF={self.d_conf}")
            return True
        else:
            app.logger.info(f"(504) ApiPLCR2_WARN002: No Rcd en Redis,ID={self.args['ID']}, Err=({r_conf.status_code}){r_conf.text}")
        #
        # Intento leer desde SQL
        try:
            r_conf = requests.get(f"http://{APICONF_HOST}:{APICONF_PORT}/apiconf/config", params={'unit':self.args['ID']}, timeout=10 )
        except requests.exceptions.RequestException as err: 
            app.logger.info( f'(505) ApiPLCR2_ERR002: Sql request exception, HOST:{APICONF_HOST}:{APICONF_PORT}, Err:{err}')
            return False
        #
        if r_conf.status_code == 200:
            if r_conf.json() == {}:
                app.logger.info(f"(506) ApiPLCR2_WARN003: Rcd en Sql empty,ID={self.args['ID']}, Err=({r_conf.status_code}){r_conf.text}")
                return False
         #
        elif r_conf.status_code == 204:
            # No hay datos en la SQL tampoco: Debo salir
            app.logger.info(f"(507) ApiPLCR2_WARN004: No Rcd en Sql,ID={self.args['ID']}, Err=({r_conf.status_code}){r_conf.text}")
            return False
        #
        else:
            app.logger.info(f"(508) ApiPLCR2_ERR003: No puedo leer SQL,ID={self.args['ID']}, Err=({r_conf.status_code}){r_conf.text}")
            return False
        #
        # La api sql me devuelve un json
        d_conf = r_conf.json()
        self.d_conf = d_conf
        app.logger.info(f"(509) ApiPLCR2 INFO ID={self.args['ID']}: (Sql) D_CONF={self.d_conf}")
        # Actualizo la redis.
        try:
            r_conf = requests.put(f"http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/config", params={'unit':self.args['ID']}, json=d_conf, timeout=10 )
        except requests.exceptions.RequestException as err: 
            app.logger.info(f"(510) ApiPLCR2_ERR001: Redis request exception', Err:{err}")
            return False

        if r_conf.status_code != 200:
            app.logger.info(f"(511) ApiPLCR2_ERR006: No puedo actualizar SQL config en REDIS, ID={self.args['ID']}, Err=({r_conf.status_code}){r_conf.text}")
            return False
        #
        app.logger.info(f"(512) ApiPLCR2 INFO ID={self.args['ID']}, Config de SQL updated en Redis")
        return True
      
    def __process_ping__(self):
        '''
        El frame de ping responde igual que lo que recibió.
        '''
        if self.ID == self.debug_unit_id:
            app.logger.info(f"(513) ApiPLCR2 INFO: ID={self.args['ID']}, PING frame")
        sresp = b'P\xe6\xcd'
        return sresp

    def __process_configuration__(self):
        '''
        Frame de configuracion. Ya tengo cargado el memblock con los datos a enviar
        '''
        if self.ID == self.debug_unit_id:
            app.logger.info(f"(514) ApiPLCR2 INFO: ID={self.args['ID']}, CONFIGURATION frame")

        sresp = self.mbk.convert_mbk2bytes( self.ID, self.mbk.configuracion_mbk )
        # 
        if self.ID == self.debug_unit_id:
            app.logger.info(f'(515) ApiPLCR2 INFO: ID={self.ID}, sresp={sresp}')
        #
        # El primer byte debe ser un 'C'
        sresp = b'C' + sresp
        #
        # Calculo el CRC y lo agrego al final. Lo debo convertir a bytes antes.
        crc = computeCRC(sresp)
        sresp += crc.to_bytes(2,'big')

        return sresp

    def __process_data__(self, rx_payload):
        '''
        Proceso los datos en 2 etapas: recepcion y respuesta
        '''
        _=self.__process_data_reception__(rx_payload)
        tx_bytestream = self.__process_data_response__()
        return tx_bytestream

    def __process_data_reception__(self, rx_payload):
        '''
        Proceso la recepcion de datos.
        Debo usar el datos_mbk.
        El primer byte del bytestream es el codigo 'D' que indica el tipo de frame
        Debo convertir el byte stream recibido del PLC a un named dict de acuerdo al formato
        del MEMBLOCK['DATOS_PLC']. 
        [
            ['UPA1_CAUDALIMETRO', 'float', 32.15],['UPA1_STATE1', 'uchar', 100],['UPA1_POS_ACTUAL_6', 'short', 24],
            ['UPA2_CAUDALIMETRO', 'float', 11.5],['BMB_STATE18', 'uchar', 201]
        ]
        '''
        if self.ID == self.debug_unit_id:
            app.logger.info(f'(516) ApiPLCR2 INFO: ID={self.ID}, DATA frame (reception)')
        
        # 1) El CRC debe ser correcto. Lo debo calcular con todos los bytes (inclusive el 'D')
        if not self.mbk.check_payload_crc_valid(rx_payload):
            app.logger.error(f'(517) ApiPLCR2_ERR007: rx_payload CRC Error, ID={self.ID} ' )
            return False
        #
        # En el payload util debo eliminar el primer byte que indica el tipo de frame
        rx_bytes = rx_payload[1:]
        # Convierto el bytestring de datos recibidos de acuerdo a la definicion del memblock en un diccionario.
        d_payload = self.mbk.convert_bytes2dict( self.ID, rx_bytes, self.mbk.datos_mbk)
        if d_payload is None:
            return False
        # Agrego los campos DATE y TIME para normalizarlos a la BD.
        # 'DATE': '230417', 'TIME': '161057'
        now = dt.datetime.now()
        d_payload['DATE'] = now.strftime('%y%m%d')
        d_payload['TIME'] = now.strftime('%H%M%S')
        if self.ID == self.debug_unit_id:
            app.logger.info(f'(518) ApiPLCR2 INFO: ID={self.ID}, Save dataline: d_payload={d_payload}')
        # Guardo los datos en Redis a traves de la api.
        r_datos = requests.put(f"http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/dataline", params={'unit':self.ID,'type':'PLC'}, json=d_payload, timeout=10 )
        if r_datos.status_code != 200:
            # Si da error genero un mensaje pero continuo para no trancar al datalogger.
            app.logger.info(f"(519) ApiPLCR2_ERR001: Redis request exception,ID={self.ID},Err={r_datos.text}")
            return False
        #
        return True
   
    def __aux_generate_sys_val__(self, nombre):
        '''
        Por ahora solo es para el TIMESTAMP
        '''
        if nombre == 'TIMESTAMP':
            now = dt.datetime.now()
            now_str = now.strftime("%H%M")
            return int(now_str)
        else:
            return 0

    def __aux_generate_atvise_val__(self, nombre, def_val):
        '''
        Si self.ordenes_atvise es None, leo las ordenes atvise (dict)
        Si no hay ordenes o no puedo leerlas, pongo un dict vacio.
        '''
        if self.d_ordenes_atvise is None:
            try:
                r_data = requests.get(f"http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/ordenesatvise", params={'unit':self.ID}, timeout=10 )
            except requests.exceptions.RequestException as err: 
                app.logger.info( f'(520) ApiPLCR2_ERR001: Read_ordenes_atvise request exception, Err:{err}')
                self.d_ordenes_atvise = {}
            #
            if r_data.status_code == 200:
                d_rsp = r_data.json()
                self.d_ordenes_atvise = d_rsp.get('ordenes_atvise',{})
                if self.ID == self.debug_unit_id:
                    app.logger.info(f"(521) ApiPLCR2_INFO: ID={self.ID}, D_ORDENES_ATVISE={self.d_ordenes_atvise}")
            else:
                app.logger.info(f"(522) ApiPLCR2_WARN005: No hay ordenes_atvise,ID={self.ID}, Err=({r_data.status_code}){r_data.text}")
                self.d_ordenes_atvise = {}
        #
        val = self.d_ordenes_atvise.get(nombre, def_val)
        return val
    
    def __aux_generate_remote_val__(self, def_val, origen, rem_name ):
        '''
        Leo el dataline del equipo de origen y extraigo el valor de la variable rem_name
        Si no existe, uso el def_val
        '''
        try:
            r_data = requests.get(f"http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/dataline", params={'unit':origen}, timeout=10 )
        except requests.exceptions.RequestException as err:
            app.logger.info(f"(523) ApiPLCR2_ERR001: Redis request exception, Err={err}")
            return def_val
        #
        if r_data.status_code == 200:
            d_dataline = r_data.json()
            if self.ID == self.debug_unit_id:
                app.logger.info(f'(524) ApiPLCR2 INFO: ID={self.ID}, d_dataline={d_dataline}')
        else:
            app.logger.info(f'(525) ApiPLCR2_WARN006: No dataline from {origen} , Err=({r_data.status_code}){r_data.text}')
            return def_val
        #
        val = d_dataline.get(rem_name, def_val)
        return val

    def __process_data_response__(self):
        '''
        Preparo la respuesta a enviar al PLC.
        Primero genero el sformat del respuestas_mbk.
        Luego recorro la lista respuestas_mbk y voy generando una nueva lista con los
        valores de c/entrada. Utilizo funciones axiliares para calcularlos.
        Por último serializo la lista de valores de acuerdo al sformat.
        '''
        if self.ID == self.debug_unit_id:
            app.logger.info(f'(526) ApiPLCR2 INFO: ID={self.ID}, DATA frame (response)')
        
        # Obtengo el mbk de los datos del servidor 'DATOS_SRV'
        if self.ID == self.debug_unit_id:
            app.logger.info(f'(527) ApiPLCR2 INFO: ID={self.ID}, respuestas_mbk={self.mbk.respuestas_mbk}')
        #
        # Genero el formato para codificar los datos de la respuesta
        sformat,*others = self.mbk.__process_mbk__(self.mbk.respuestas_mbk)
        if self.ID == self.debug_unit_id:
            app.logger.info(f'(533) ApiPLCR2 INFO: ID={self.ID}, sformat= {sformat}')
        
        # Recorro la lista de respuestas y calculo los valores de c/variable.
        list_values = []
        list_nombres = []
        for item in self.mbk.respuestas_mbk:
            (nombre,tipo,def_val,origen,rem_name) = item
            if origen == 'SYS':
                val = self.__aux_generate_sys_val__(nombre)
            elif origen == 'ATVISE':
                val = self.__aux_generate_atvise_val__(nombre, def_val)
            else:
                val = self.__aux_generate_remote_val__(def_val, origen, rem_name )
            list_values.append(val)
            list_nombres.append(nombre)

        if self.ID == self.debug_unit_id:
            app.logger.info(f'(534) ApiPLCR2 INFO: ID={self.ID}, list_values= {list_values}')
        #
        d_response = { i:j for i,j in zip( list_nombres, list_values)}
        if self.ID == self.debug_unit_id:
            app.logger.info(f'(534) ApiPLCR2 INFO: ID={self.ID}, d_response= {d_response}')
        #
        tx_bytestream = pack( sformat, *list_values)
        tx_bytestream = b'D' + tx_bytestream
        crc = computeCRC(tx_bytestream)
        tx_bytestream += crc.to_bytes(2,'big')
        return tx_bytestream
        
    def post(self):
        '''
        Procesa los POST que vienen de los PLC
        '''
        self.mbk = apiplcR2_utils.Memblock(app)
        # Leo los argumentos que vinen en el URL.
        parser = reqparse.RequestParser()
        parser.add_argument('ID',type=str,location='args',required=True)
        parser.add_argument('VER',type=str,location='args',required=True)
        parser.add_argument('TYPE',type=str,location='args',required=True)
        self.args=parser.parse_args()
        self.ID = self.args['ID']
        self.VER = self.args['VER']
        self.TYPE = self.args['TYPE']
    
        # Leo el debugdlgid
        self.__read_debug_id__()
        if self.ID == self.debug_unit_id:
            self.mbk.set_debug()

        # Logs general.
        app.logger.info("(528) ApiPLCR2 INFO: PLC_QS=%(a)s", {'a': request.query_string })
    
        # Leo la configuracion de la unidad ( globalmente )
        if not self.__read_configuration__():
            return {}, 204

        # Filtro de la configuracion la definicion del memblock y la cargo en el objeto mbk
        # Esto ya separa c/u de los memblocks (conf,data,response)
        d_mbk = self.d_conf.get('MEMBLOCK',{})
        self.mbk.load_configuration(self.ID, d_mbk)
        if self.ID == self.debug_unit_id:
            app.logger.info(f"(529) ApiPLCR2 INFO: ID={self.args['ID']}, MBK={d_mbk}")
        
        # Proceso el frame de acuerdo a su tipo: ('P':0x50:80:Ping, 'C':0x43:67:Config, 'D':0x44:68:Data )
        rx_payload = request.get_data()
        if self.ID == self.debug_unit_id:
            app.logger.info(f"(530) ApiPLCR2 INFO: ID={self.args['ID']}, rx_payload={rx_payload}")
        #
        id_frame = rx_payload[0]
        if id_frame == 80:
            sresp = self.__process_ping__()
        elif id_frame == 67:
            sresp = self.__process_configuration__()
        elif id_frame == 68:
            sresp = self.__process_data__(rx_payload)
        else:
            app.logger.error(f"(531) ApiPLCR2_ERR008: No se reconoce el frame ID, ID={self.ID}, fid={id_frame}")
            return {}, 204
        #
        # Armo el frame de respuesta POST
        # La funcion make_response es de FLASK !!!
        response = make_response(sresp)
        response.headers['Content-type'] = 'application/binary'
        #if self.ID == self.debug_unit_id:
        app.logger.info(f"(532) ApiPLCR2 INFO: ID={self.ID}, RSP={sresp}")
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
            app.logger.info( f'(457) ApiCOMMS_ERR001: Redis request exception, HOST:{APIREDIS_HOST}:{APIREDIS_PORT}, Err:{err}')
        #
        # Pruebo la conexion a SQL
        sql_status = 'ERR'
        try:
            r_conf = requests.get(f"http://{APICONF_HOST}:{APICONF_PORT}/apiconf/ping",timeout=10 )
            if r_conf.status_code == 200:
                sql_status = 'OK'
        except requests.exceptions.RequestException as err: 
            app.logger.info( f'(458) ApiCOMMS_ERR002: Sql request exception, HOST:{APICONF_HOST}:{APICONF_PORT}, Err:{err}')
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

api.add_resource( ApiPlcR2, '/apiplcR2')
api.add_resource( Help, '/apiplc/help')
api.add_resource( Ping, '/apiplc/ping')

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

    app.logger.info( f'Starting ApiPLC: REDIS_HOST={APIREDIS_HOST}, REDIS_PORT={APIREDIS_PORT}' )
    app.logger.info( f'         ApiPLC: CONF_HOST={APICONF_HOST}, CONF_PORT={APICONF_PORT}' )

if __name__ == '__main__':
    APIREDIS_HOST = '127.0.0.1'
    APICONF_HOST = '127.0.0.1'
    app.run(host='0.0.0.0', port=5500, debug=True)
