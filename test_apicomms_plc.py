#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python
'''
Script que testea la apicomms simulando ser un PLC


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

Se usa para mandar datos a la API como si fuesemos un PLC.

REF: https://stackoverflow.com/questions/14365027/python-post-binary-data

REF: https://stackoverflow.com/questions/9029287/how-to-extract-http-response-body-from-a-python-requests-call

'''

import requests
from collections import namedtuple
from struct import unpack_from, pack
from pymodbus.utilities import computeCRC
import argparse
import random
import sys

APICOMMS_HOST='127.0.0.1'
APICOMMS_PORT='5000'

APIREDIS_HOST='127.0.0.1'
APIREDIS_PORT='5100'

APICONF_HOST = '127.0.0.1'
APICONF_PORT = '5200'
               

class Plc:

    def __init__(self):
        self.plcid = ''
        self.plc_conf_mbk = None

    def set_plcid(self,plcid):
        self.plcid = plcid

    def __process_mbk__( self, l_mbk:list ):
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
        for ( name, tipo, *others) in l_mbk:
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

    def write_configuration(self, plcid):
        '''
        Pido a apiconf el template de la ultima version de PLC
        '''
        params = {'ver':'latest', 'type':'PLC'}
        url = f'http://{APICONF_HOST}:{APICONF_PORT}/apiconf/template'
        rsp = requests.get(url=url, params=params, timeout=10 )
        if rsp.status_code != 200:
            print('ERROR: No puedo leer template. Exit')
            return False
        d_template = rsp.json()['template']
        #
        params = {'unit':plcid}
        url = f'http://{APICONF_HOST}:{APICONF_PORT}/apiconf/config'
        rsp = requests.post(url=url, params=params, json=d_template, timeout=10 )
        if rsp.status_code != 200:
            print('ERROR: No puedo grabar configuracion. Exit')
            return False
        return True
    
    def read_configuration(self, plcid):
        '''
        Pido a apiconf la configuracion del PLC
        '''
        params = {'unit':plcid}
        url = f'http://{APICONF_HOST}:{APICONF_PORT}/apiconf/config'
        rsp = requests.get(url=url, params=params, timeout=10 )
        if rsp.status_code == 200:
            d_conf = rsp.json()['MEMBLOCK']
            self.plc_conf_mbk = d_conf
            return True
        return False

    def get_configuration(self):
        return self.plc_conf_mbk
    
    def generar_frame_ping(self):
        '''
        Emula a un PLC enviando un PING al servidor
        '''
        url = f'http://{APICOMMS_HOST}:{APICOMMS_PORT}/apiplc'
        params = { 'ID':self.plcid,'VER':'1.1.0','TYPE':'PLC'}
        data_ping = b'P\xbf|'
        headers={'Content-Type': 'application/octet-stream'}
        res = requests.post( url=url, params=params, data=data_ping, headers=headers)
        print(f'PING response_code={res.status_code}')
        print(f'PING response_content={res.content}')

    def generar_frame_configuracion(self):
        '''
        Emula a un PLC enviando un frame de CONFIGURACION al servidor
        Luego el servidor manda un bytestream que debo descomponer en un dict.
        - Leo el formato del mbk (sformat)
        - Genero la lista de nombres de las variables (var_names)
        - Desempaco el rx_bytes con formato sformat en la tupla t_vals
        - Genero una namedtuple con t_vals y la lista de nombres var_names
        - La convierto a un diccionario
        '''
        url = f'http://{APICOMMS_HOST}:{APICOMMS_PORT}/apiplc'
        params = { 'ID':self.plcid,'VER':'1.1.0','TYPE':'PLC'}
        data_configuracion = b'C\xe6\xcd'
        headers={'Content-Type': 'application/octet-stream'}
        res = requests.post( url=url, params=params, data=data_configuracion, headers=headers)
        print(f'CONF response_code={res.status_code}')
        print(f'CONF response_content={res.content}')
        #
        # DESCOMPONGO el bytestream recibido para obtener un diccionario con las variables
        rx_bytes = res.content
        print(f'CONF rx_bytes={rx_bytes}')
        #
        # En el payload util debo eliminar el primer byte que indica el tipo de frame
        rx_bytes = rx_bytes[1:]
        #
        mbk_conf = self.plc_conf_mbk['CONFIGURACION']
        print(f'CONF mbk={mbk_conf}')
        #
        sformat, _ , var_names = self.__process_mbk__(mbk_conf)
        print(f'CONF sformat={sformat}')
        print(f'CONF var_names={var_names}')
        #
        t_vals = unpack_from(sformat, rx_bytes)
        t_names = namedtuple('t_foo', var_names)
        rx_tuple = t_names._make(t_vals)
        rx_payload = rx_tuple._asdict()
        print(f'CONF rx_d={rx_payload}')

    def generar_datalines_en_server(self):
        '''
        Si en el mbk_srv indica que deben haber datos de equipos remotos
        inserta los correspondientes datalines.
        '''   
        mbk = self.plc_conf_mbk['DATOS_SRV']
        print(f'mbk_datos_srv={mbk}')
        for item in mbk:
            (name,tipo,default_value,origen,rem_name) = item
            if origen in ['SYS','ATVISE']:
                continue
            #
            if tipo == 'float':
                val = random.uniform(0,10.0)
            else:
                val = random.randrange(0,100)
            # Inserto la linea datalinne
            dataline = { "DATE": "230519","TIME": "144412", rem_name:val }
            params = {'unit':origen,'type':'DLG'}
            url = f'http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/dataline'
            rsp = requests.put(url=url, params=params, json=dataline, timeout=10 )
            #print(f'Dataline: {dataline}')
            #print(f'DEBUG: {rsp.status_code}, {rsp.text}')
            if rsp.status_code == 200:
                print(f'Dataline OK: {dataline}')
            else:
                print('Dataline FAIL')
        #
        return True

    def generar_orden_atvise(self):
        '''
        Genera un d_ordenes con todas las entradas del mbk_srv que indican
        que provienen del ATVISE.
        '''
        mbk = self.plc_conf_mbk['DATOS_SRV']
        print(f'mbk_datos_srv={mbk}')
        d_ordenes = {}
        for item in mbk:
            (name,tipo,default_value,origen,rem_name_) = item
            if origen == 'ATVISE':
                if tipo == 'float':
                    val = random.uniform(0,10.0)
                else:
                    val = random.randrange(0,100)
                d_ordenes[name] = val
        #
        json = { "ordenes_atvise": d_ordenes }
        params = {'unit':'PLCTESTV2'}
        url = f'http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/ordenesatvise'
        rsp = requests.put(url=url, params=params, json=json, timeout=10 )
        if rsp.status_code == 200:
            print(f'Orden Atvise: {d_ordenes}')
            return True
        #
        print('Ordenes Atvise FAIL.')
        return False

    def generar_frame_datos(self):
        '''
        Basado en el mbk DATOS_PLC, genero valores aleatorios y armo el bytestring que envio.
        - Calculo el sformat.
        - Genero una lista de valores aleatorios de las variables (list_values)
        - serializo (pack) la lista_values de acuerdo al sformat
        - Envio los datos ( agrego el header 'D' y el CRC)
        - Decodifico la respuesta ( datos/ordenes al PLC)
        '''
        # Genero los datos para enviar al server
        mbk_datos_plc = self.plc_conf_mbk['DATOS_PLC']
        print(f'DATOS_PLC mbk={mbk_datos_plc}')
        sformat, *others = self.__process_mbk__(mbk_datos_plc)
        list_values = []
        for item in mbk_datos_plc:
            (_,tipo,_) = item
            if tipo == 'float':
                val = random.uniform(0,10.0)
            else:
                val = random.randrange(0,100)
            list_values.append(val)
        print(f'DATOS_PLC sformat={sformat}')
        print(f'DATOS_PLC list_values={list_values}')
        tx_bytestream = pack( sformat, *list_values)
        tx_bytestream = b'D' + tx_bytestream
        crc = computeCRC(tx_bytestream)
        tx_bytestream += crc.to_bytes(2,'big')
        print(f'DATOS_PLC sresp={tx_bytestream}')
        #
        # Transmito los datos al server
        url = f'http://{APICOMMS_HOST}:{APICOMMS_PORT}/apiplc'
        params = { 'ID':self.plcid,'VER':'1.1.0','TYPE':'PLC'}
        headers={'Content-Type': 'application/octet-stream'}
        try:
            res = requests.post( url=url, params=params, data=tx_bytestream, headers=headers)
        except:
            print('ERROR request. Exit')
            return
        
        print(f'DATOS_PLC response_code={res.status_code}')
        if res.status_code != 200:
            print('ERROR request. Exit')
            return
        
        print(f'DATOS_PLC response_content={res.content}')
        #
        # Proceso la respuesta (datos/ordenes)
        rx_bytes = res.content
        rx_bytes = rx_bytes[1:]
        #
        mbk_datos_srv = self.plc_conf_mbk['DATOS_SRV']
        print(f'DATOS_SRV mbk={mbk_datos_srv}')
        sformat, _ , var_names = self.__process_mbk__(mbk_datos_srv)
        t_vals = unpack_from(sformat, rx_bytes)
        t_names = namedtuple('t_foo', var_names)
        rx_tuple = t_names._make(t_vals)
        d_rx_datos_srv = rx_tuple._asdict()
        print(f'DATOS_SRV={d_rx_datos_srv}')

def process_arguments():
    '''
    Proceso la linea de comandos.
    d_vp es un diccionario donde guardamos todas las variables del programa
    Corrijo los parametros que sean necesarios
    '''

    parser = argparse.ArgumentParser(description='Testing del sistema APICOMMSV3')
    parser.add_argument('-o', '--ordenes', dest='ordenes', action='store', default='',
                        help='Genera ordenes para el PLC (atvise/datalines)')
    parser.add_argument('-p', '--plcid', dest='plcid', action='store', default='',
                        help='Id del PLC a usar')
    parser.add_argument('-f', '--frame', dest='frame', action='store', default='',
                        help='Frame a enviar (ping,conf,data)')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store', default='False',
                        help='Verbosidad')
    
    args = parser.parse_args()
    d_args = vars(args)
    return d_args

if __name__ == '__main__':

    d_args = process_arguments()
    frame_type = d_args['frame']
    tipo_ordenes = d_args['ordenes']
    plc_id = d_args['plcid']
    verbose = d_args['verbose']

    if plc_id == '':
        print('ERROR: Debe ingresar un plcid. Exit...')
        sys.exit(0)

    print('Arguments:')
    print(f'    Frame={frame_type}')
    print(f'    Ordenes={tipo_ordenes}')
    print(f'    Plcid={plc_id}')
    print(f'    Verbose={verbose}')

    debug = bool ( verbose in ['true','TRUE','True'])
    plc=Plc()
    plc.set_plcid(plc_id)
    if not plc.read_configuration(plc_id):
        print('Genero nueva configuracion desde template...')
        plc.write_configuration(plc_id)
    if debug:
        print(f'PLC_CONF={plc.get_configuration()}')

    # FRAMES
    if frame_type.upper() == 'PING':
        plc.generar_frame_ping()
    elif frame_type.upper() == 'CONF':
        plc.generar_frame_configuracion()    
    elif frame_type.upper() == 'DATOS':
        plc.generar_frame_datos()

    if tipo_ordenes.upper() == 'ATVISE':
        plc.generar_orden_atvise()
    elif tipo_ordenes.upper() == 'DATALINES':
        plc.generar_datalines_en_server()


        




   



