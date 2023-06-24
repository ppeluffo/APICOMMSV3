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
import datetime as dt
from flask import Flask, request, make_response
from flask_restful import Resource, reqparse
from pymodbus.utilities import computeCRC
from struct import pack
import requests
import apiplc_utils
from apicomms_common import Utils

API_VERSION = 'R001 @ 2023-06-15'

class ApiPlc(Resource):
    ''' 
    Clase especializada en atender los dataloggers y PLCs
    '''
    def __init__(self, **kwargs):
        self.app = kwargs['app']
        self.servers = kwargs['servers']
        self.debug_unit_id = None
        self.args = None
        self.d_conf = None
        self.mbk = None
        self.ID = None
        self.VER = None
        self.TYPE = None
        self.d_ordenes_atvise = None
        self.url_redis = f"http://{self.servers['APIREDIS_HOST']}:{self.servers['APIREDIS_PORT']}/apiredis/"
        self.url_conf = f"http://{self.servers['APICONF_HOST']}:{self.servers['APICONF_PORT']}/apiconf/"

    def __process_ping__(self, rx_payload):
        '''
        El frame de ping responde igual que lo que recibió.
        '''
        if self.ID == self.debug_unit_id:
            self.app.logger.info(f"(600) ApiPLC_INFO: ID={self.ID}, PING frame")
        #sresp = b'\r\n' + rx_payload
        #sresp = b'P\xe6\xcd'
        sresp = rx_payload
        return sresp

    def __process_configuration__(self):
        '''
        Frame de configuracion. Ya tengo cargado el memblock con los datos a enviar
        '''
        if self.ID == self.debug_unit_id:
            self.app.logger.info(f"(610) ApiPLC_INFO: ID={self.ID}, CONFIGURATION frame")

        sresp = self.mbk.convert_mbk2bytes( self.ID, self.mbk.configuracion_mbk )
        #
        if self.ID == self.debug_unit_id:
            self.app.logger.info(f'(611) ApiPLC_INFO: ID={self.ID}, sresp={sresp}')
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
            self.app.logger.info(f'(620) ApiPLC_INFO: ID={self.ID}, DATA frame (reception)')
        
        # 1) El CRC debe ser correcto. Lo debo calcular con todos los bytes (inclusive el 'D')
        if not self.mbk.check_payload_crc_valid(rx_payload):
            self.app.logger.error(f'(621) ApiPLC_ERR007: rx_payload CRC Error, ID={self.ID} ' )
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
            self.app.logger.info(f'(622) ApiPLC_INFO: ID={self.ID}, Save dataline: d_payload={d_payload}')
        # Guardo los datos en Redis a traves de la api.
        r_datos = requests.put(self.url_redis + 'dataline', params={'unit':self.ID,'type':'PLC'}, json=d_payload, timeout=10 )
        if r_datos.status_code != 200:
            # Si da error genero un mensaje pero continuo para no trancar al datalogger.
            self.app.logger.info(f"(622) ApiPLC_ERR001: Redis request exception,ID={self.ID},Err={r_datos.text}")
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
        #
        return 0

    def __aux_generate_atvise_val__(self, nombre, def_val):
        '''
        Si self.ordenes_atvise es None, leo las ordenes atvise (dict)
        Si no hay ordenes o no puedo leerlas, pongo un dict vacio.
        '''
        if self.d_ordenes_atvise is None:
            try:
                r_data = requests.get(self.url_redis + 'ordenesatvise', params={'unit':self.ID}, timeout=10 )
            except requests.exceptions.RequestException as err: 
                self.app.logger.info( f'(630) ApiPLC_ERR001: Read_ordenes_atvise request exception, Err:{err}')
                self.d_ordenes_atvise = {}
            #
            if r_data.status_code == 200:
                d_rsp = r_data.json()
                self.d_ordenes_atvise = d_rsp.get('ordenes_atvise',{})
                if self.ID == self.debug_unit_id:
                    self.app.logger.info(f"(631) ApiPLC_INFO: ID={self.ID}, D_ORDENES_ATVISE={self.d_ordenes_atvise}")
            else:
                self.app.logger.info(f"(632) ApiPLC_WARN005: No hay ordenes_atvise,ID={self.ID}, Err=({r_data.status_code}){r_data.text}")
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
            r_data = requests.get(self.url_redis + 'dataline', params={'unit':origen}, timeout=10 )
        except requests.exceptions.RequestException as err:
            self.app.logger.info(f"(640) ApiPLC_ERR001: Redis request exception, Err={err}")
            return def_val
        #
        if r_data.status_code == 200:
            d_dataline = r_data.json()
            if self.ID == self.debug_unit_id:
                self.app.logger.info(f'(641) ApiPLC INFO: ID={self.ID}, d_dataline={d_dataline}')
        else:
            self.app.logger.info(f'(642) ApiPLC_WARN006: No dataline from {origen} , Err=({r_data.status_code}){r_data.text}')
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
            self.app.logger.info(f'(650) ApiPLC_INFO: ID={self.ID}, DATA frame (response)')
        
        # Obtengo el mbk de los datos del servidor 'DATOS_SRV'
        if self.ID == self.debug_unit_id:
            self.app.logger.info(f'(651) ApiPLC_INFO: ID={self.ID}, respuestas_mbk={self.mbk.respuestas_mbk}')
        #
        # Genero el formato para codificar los datos de la respuesta
        sformat,*others = self.mbk.__process_mbk__(self.mbk.respuestas_mbk)
        if self.ID == self.debug_unit_id:
            self.app.logger.info(f'(652) ApiPLC_INFO: ID={self.ID}, sformat= {sformat}')
        
        # Recorro la lista de respuestas y calculo los valores de c/variable.
        list_values = []
        list_nombres = []
        borrar_orden_atvise = False
        for item in self.mbk.respuestas_mbk:
            (nombre,tipo,def_val,origen,rem_name) = item
            if origen == 'SYS':
                val = self.__aux_generate_sys_val__(nombre)
            elif origen == 'ATVISE':
                val = self.__aux_generate_atvise_val__(nombre, def_val)
                borrar_orden_atvise = True
            else:
                val = self.__aux_generate_remote_val__(def_val, origen, rem_name )
            list_values.append(val)
            list_nombres.append(nombre)

        if borrar_orden_atvise:
            #app.logger.info(f'(534) ApiPLCR2 INFO: ID={self.ID}, Borrar Orden Atvise')
            try:
                r_data = requests.delete(self.url_redis + 'ordenesatvise', params={'unit':self.ID}, timeout=10 )
            except requests.exceptions.RequestException as err: 
                self.app.logger.info( f'(653) ApiPLC_ERR001: Read_ordenes_atvise request exception, Err:{err}')


        if self.ID == self.debug_unit_id:
            self.app.logger.info(f'(654) ApiPLC INFO: ID={self.ID}, list_values= {list_values}')
        #
        d_response = { i:j for i,j in zip( list_nombres, list_values)}
        if self.ID == self.debug_unit_id:
            self.app.logger.info(f'(655) ApiPLC INFO: ID={self.ID}, d_response= {d_response}')
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
        self.mbk = apiplc_utils.Memblock(self.app)
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
        if self.ID == self.debug_unit_id:
            self.mbk.set_debug()

        # Logs general.
        self.app.logger.info("(660) ApiPLC_INFO: PLC_QS=%(a)s", {'a': request.query_string })
    
        # Leo la configuracion de la unidad ( globalmente )
        self.d_conf = utils.read_configuration((self.ID == self.debug_unit_id)) 
        if self.d_conf is None :
            return {}, 204

        # Filtro de la configuracion la definicion del memblock y la cargo en el objeto mbk
        # Esto ya separa c/u de los memblocks (conf,data,response)
        d_mbk = self.d_conf.get('MEMBLOCK',{})
        self.mbk.load_configuration(self.ID, d_mbk)
        if self.ID == self.debug_unit_id:
            self.app.logger.info(f"(661) ApiPLC_INFO: ID={self.args['ID']}, MBK={d_mbk}")
        
        # Proceso el frame de acuerdo a su tipo: ('P':0x50:80:Ping, 'C':0x43:67:Config, 'D':0x44:68:Data )
        rx_payload = request.get_data()
        if self.ID == self.debug_unit_id:
            self.app.logger.info(f"(662) ApiPLC_INFO: ID={self.args['ID']}, rx_payload={rx_payload}")
        #
        id_frame = rx_payload[0]
        if id_frame == 80:
            sresp = self.__process_ping__(rx_payload)
        elif id_frame == 67:
            sresp = self.__process_configuration__()
        elif id_frame == 68:
            sresp = self.__process_data__(rx_payload)
        else:
            self.app.logger.error(f"(663) ApiPLC_ERR008: No se reconoce el frame ID, ID={self.ID}, fid={id_frame}")
            return {}, 204
        #
        # Armo el frame de respuesta POST
        # La funcion make_response es de FLASK !!!
        response = make_response(sresp)
        response.headers['Content-type'] = 'application/binary'
        #if self.ID == self.debug_unit_id:
        self.app.logger.info(f"(664) ApiPLC_INFO: ID={self.ID}, RSP={sresp}")
        return response


