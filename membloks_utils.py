#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python
'''
Script que testea el funcionamiento de los memblocs.
Las entradas son el PLCID y el rx_payload.
Simula todo el proceso que dicho frame correría en el servidor APICOMMS
El PLCID debe estar definido en la BD para poder leer su configuración.


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

Se usa para mandar datos a la API como si fuesemos un PLC.

REF: https://stackoverflow.com/questions/14365027/python-post-binary-data

REF: https://stackoverflow.com/questions/9029287/how-to-extract-http-response-body-from-a-python-requests-call

'''

import requests
import argparse
import sys
import pprint
from pymodbus.utilities import computeCRC
from collections import namedtuple
from struct import unpack_from, pack
import numpy as np

APICONF_HOST = '192.168.0.8'
APICONF_PORT = '5200'
               
class DebugMemblocks:

    def __init__(self):
        self.plcid = None
        self.plc_conf_mbk = None
        self.rxpayload = None

    def set_plcid(self, plcid=None):
        self.plcid = plcid

    def get_plcid(self):
        return self.plcid
    
    def read_configuration(self):
        '''
        Pido a apiconf la configuracion del PLC.
        Solo me quedo con el memblock
        '''
        params = {'unit':self.plcid}
        url = f'http://{APICONF_HOST}:{APICONF_PORT}/apiconf/config'
        rsp = requests.get(url=url, params=params, timeout=10 )
        if rsp.status_code == 200:
            d_conf = rsp.json()['MEMBLOCK']
            self.plc_conf_mbk = d_conf
            return True
        return False
    
    def get_memblock(self):
        return self.plc_conf_mbk
    
    def set_rxpayload(self, rxpayload=None):
        self.rxpayload = rxpayload

    def get_rxpayload(self):
        return self.rxpayload
    
    def convert_mbk2bytes(self, plcid, l_mbk:list):
        '''
        Recibo una lista de memblock y serializo sus valores de acuerdo al formato y orden en la lista.
        l_mbk = [['ALT_MAX_TQ1', 'float', 10],['ALT_MIN_TQ1', 'float', 2],['PRES_ALM_1', 'short', 101],['TIMER_B2', 'short', 200]]
        Siempre retorna un bytestream.
        '''
        # Proceso la lista del mbk para obtener sus elementos
        # Obtengo algo del tipo  ('<ffhh', 12, 'ALT_MAX_TQ1 ALT_MIN_TQ1 PRES_ALM_1 TIMER_B2 ')

        tx_bytestream = b''
        if not isinstance(l_mbk,list):
            print('ERROR: l_mbk no es lista. ID={plcid}' )
            return tx_bytestream

        sformat, *others = self.__process_mbk__(l_mbk)
        #
        # Genero una lista con los valores
        # Obtengo [10, 2, 101, 200]
        list_values = [ k for (i,j,k) in l_mbk ]
        #
        ### AJUSTE: 2023-07-12:
        ### Ajusto el valor al tipo que espero en sformat.
        for i,(fmt,value) in enumerate(zip( sformat[1:], list_values)):
            new_val = self.__convert_val2format__(fmt,value)
            list_values[i] = new_val
        #
        print(f'sformat={sformat},list_values={list_values}' )
        # Serializo la lista de valores con el formato sformat
        # Convierto la ntuple a un bytearray serializado 
        # b'\x00\x00 A\x00\x00\x00@e\x00\xc8\x00'
        try:  
            tx_bytestream = pack( sformat, *list_values)      
        except Exception as ex:
            print(f'ERROR: No puedo serializar lista. ID={plcid},lista={list_values},Err={ex}' )
        #
        return tx_bytestream
        #

    def convert_bytes2dict(self, plcid, rx_bytes, l_mbk):
        
        '''
        Toma el payload ( bytes )
        Chequea si el crc es correcto.
        Lo decodifica de acuerdo a la struct definida en l_mbk
        y retorna un dict con las variables y sus valores.
        La defincion de la struct no deberia tener menos bytes que el bloque !!!. Por las dudas uso 'unpack_from'
        
        l_mbk = 
        [
            ['UPA1_CAUDALIMETRO', 'float', 32.15],['UPA1_STATE1', 'uchar', 100],['UPA1_POS_ACTUAL_6', 'short', 24],
            ['UPA2_CAUDALIMETRO', 'float', 11.5],['BMB_STATE18', 'uchar', 201]
        ]

        rx_bytes = b'\x9a\x99\x00Bd\x18\x00\x00\x008A\xc9\xaa\xb7'

        '''
        # Calculo los componentes del memblock de recepcion (formato,largo, lista de nombres)
        sformat, _ , var_names = self.__process_mbk__(l_mbk)
        # sformat = '<fBhfB'
        # var_names = 'UPA1_CAUDALIMETRO UPA1_STATE1 UPA1_POS_ACTUAL_6 UPA2_CAUDALIMETRO BMB_STATE18 '
        if self.debug:
            self.app.logger.info( f'553) ApiPLCR2_INFO: ID={plcid}, convert_rxbytes2dict IN: RXVD_MBK_DEF={l_mbk}, sformat={sformat}, var_names={var_names}')
        #
        # Desempaco los datos recibidos del PLC de acuerdo al formato dado (sformat del l_mbk)
        # l_mbk es una lista porque importa el orden de las variables !!!
        # El resultado es una tupla de valores
        # sformat = '<fBhfB'
        # rx_bytes = b'\x9a\x99\x00Bd\x18\x00\x00\x008A\xc9\xaa\xb7'
        try:
            t_vals = unpack_from(sformat, rx_bytes)
        except Exception as err:
            self.app.logger.error( f'(554) ApiPLCR2_ERR011: No puedo UNPACK, ID={plcid},sformat={sformat},rx_payload=[{rx_bytes}],Err={err}' )
            return None
        #
        # Genero una namedtuple con los valores anteriores y los nombres de las variables
        # Creo una namedtuple con la lista de nombres del rx_mbk
        # var_names = 'UPA1_CAUDALIMETRO UPA1_STATE1 UPA1_POS_ACTUAL_6 UPA2_CAUDALIMETRO BMB_STATE18 '
        t_names = namedtuple('t_foo', var_names)
        try:
            rx_tuple = t_names._make(t_vals)
        except Exception as err:
            self.app.logger.error( f'(555) ApiPLCR2_ERR012: No puedo generar tupla de valores, ID={plcid},Err={err}' )
            return None
        #
        # La convierto a diccionario
        # d_rx_payload = {  'UPA1_CAUDALIMETRO': 32.150001525878906,
        #                   'UPA1_STATE1': 100, 'UPA1_POS_ACTUAL_6': 24, 
        #                   'UPA2_CAUDALIMETRO': 11.5,'BMB_STATE18': 201
        #                 }
        d_rx_payload = rx_tuple._asdict()
        if self.debug:
            self.app.logger.info(  f'(556) ApiCOMMS_INFO: ID={self.plcid}, convert_bytes2dict OUT ,d_rx_payload={d_rx_payload}' )
        return d_rx_payload
 
    def check_payload_crc_valid(self, rx_bytes):
        '''
        Calcula el CRC del payload y lo compara el que trae.
        El payload trae el CRC que envia el PLC en los 2 ultimos bytes
        El payload es un bytestring
        '''
        crc = int.from_bytes(rx_bytes[-2:],'big')
        calc_crc = computeCRC(rx_bytes[:-2])
        if crc == calc_crc:
            return True
        else:
            return False

    def __process_mbk__( self, l_mbk_def:list ):
        '''
        Toma una lista de definicion de un memblok de recepcion y genera 3 elementos:
        -un iterable con los nombres en orden
        -el formato a usar en la conversion de struct
        -el largo total definido por las variables
        '''
        #
        sformat = '<'
        largo = 0
        var_names = ''
        for ( name, tipo, *others ) in l_mbk_def:
            var_names += f'{name} '
            if tipo.lower() == 'char':
                sformat += 'c'
                largo += 1
            elif tipo.lower() == 'schar':
                sformat += 'b'
                largo += 1
            elif tipo.lower() == 'uchar':
                sformat += 'B'
                largo += 1
            elif tipo.lower() == 'short':
                sformat += 'h'
                largo += 2
            elif tipo.lower() == 'int':
                sformat += 'i'
                largo += 4
            elif tipo.lower() == 'float':
                sformat += 'f'
                largo += 4
            elif tipo.lower() == 'unsigned':
                sformat += 'H'
                largo += 2
            else:
                sformat += '?'
        #
        return sformat, largo, var_names

    def __convert_val2format__(self,fmt,val):
        '''
        Me aseguro que el valor corresponda con el formato
        '''
        if fmt == 'h':
            return np.int16(val)
        if fmt == 'i':
            return np.int32(val)
        if fmt == 'f':
            return np.float32(val)
        return val

    def __process_ping__(self):
        '''
        El frame de ping responde igual que lo que recibió.
        '''
        print('PING frame')
        #sresp = b'\r\n' + rx_payload
        #sresp = b'P\xe6\xcd'
        sresp = self.rxpayload
        return sresp

    def __process_configuration__(self):
        '''
        Frame de configuracion. Ya tengo cargado el memblock con los datos a enviar
        '''

        print("CONFIGURATION frame")
        sresp = self.convert_mbk2bytes( self.plcid, self.plc_conf_mbk['CONFIGURACION'] )
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
    
    def process_frame(self):
        '''
        Procesa el rxpayload
        '''
        id_frame = self.rxpayload[0]
        if id_frame == 80:
            sresp = self.__process_ping__()
        elif id_frame == 67:
            sresp = self.__process_configuration__()
        elif id_frame == 68:
            sresp = self.__process_data__()
        else:
            sresp = None
            print(f'ERROR: No se reconoce el frame ID, fid={id_frame}')
        return sresp

def process_arguments():
    '''
    Proceso la linea de comandos.
    d_vp es un diccionario donde guardamos todas las variables del programa
    Corrijo los parametros que sean necesarios
    '''

    parser = argparse.ArgumentParser(description='Testing del MEMBLOCKS')
    parser.add_argument('-p', '--plcid', dest='plcid', action='store', default='',
                        help='Id del PLC a usar')
    parser.add_argument('-r', '--rxpayload', dest='rxpayload', action='store', default='',
                        help='RX payload(bytes)')
    
    args = parser.parse_args()
    d_args = vars(args)
    return d_args

if __name__ == '__main__':

    d_args = process_arguments()
    plc_id = d_args['plcid']
    rxpayload = bytes(d_args['rxpayload'],'utf-8')
    if plc_id == '':
        print('ERROR: Debe ingresar un plcid. Exit...')
        sys.exit(0)

    mbc = DebugMemblocks()
    mbc.set_plcid(plc_id)
    mbc.set_rxpayload(rxpayload)
    # Leo configuracion
    if mbc.read_configuration() is False:
        print(f'No hay configuracion de {plc_id}. EXIT...')
        sys.exit(0)
    #
    memblock = mbc.get_memblock()
    print(f'PLC {plc_id} MEMBLOCK:')
    pprint.pprint(memblock)
    #
    sresp = mbc.process_frame()
    print(f'RESPONSE={sresp}')




