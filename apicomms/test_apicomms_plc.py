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
import redis
import pickle
import json

APICOMMS_HOST='127.0.0.1'
APICOMMS_PORT='5000'
APIREDIS_HOST='127.0.0.1'
APIREDIS_PORT='5100'


def simulatePlc():
    url = f'http://{APICOMMS_HOST}:{APICOMMS_PORT}/apicomms'
    params = { 'ID':'PLCTEST','VER':'1.1.0','TYPE':'PLC'}
    data = b'f\xe6\xf6Bdx\x00\xcd\xcc\x01B\x14(\x8dU'
    headers={'Content-Type': 'application/octet-stream'}
    res = requests.post( url=url, params=params, data=data, headers=headers)
    print(f'response_code={res.status_code}')
    print(f'response_content={res.content}')
 
def crear_configuracion_test():
    '''
    Crea para el PLCTEST el archivo de configuracion que tiene el memblock
    '''
    d_conf = { 'MEMBLOCK':{
        'RCVD_MBK_DEF': [
            ['UPA1_CAUDALIMETRO', 'float', 0],['UPA1_STATE1', 'uchar', 1],['UPA1_POS_ACTUAL_6', 'short', 8],
            ['UPA2_CAUDALIMETRO', 'float', 0],['BMB_STATE18', 'uchar', 1],['BMB_STATE19', 'uchar', 1]
        ],
        'SEND_MBK_DEF': [
            ['UPA1_ORDER_1', 'short', 1],['UPA1_CONSIGNA_6', 'short', 2560],['ESP_ORDER_8', 'short', 200],
            ['ALTURA_TANQUE_KIYU_1', 'float', 2560],['ALTURA_TANQUE_KIYU_2', 'float', 2560],
            ['PRESION_ALTA_SJ1', 'float', 0],['PRESION_BAJA_SQ1', 'float', 0]
        ],
        'RCVD_MBK_LENGTH':15,
        'SEND_MBK_LENGTH':24
        },
        'REMVARS':{
            'KIYU001': [
                ('HTQ1', 'ALTURA_TANQUE_KIYU_1'), 
                ('HTQ2', 'ALTURA_TANQUE_KIYU_2')
            ],
            'SJOSE001': [
                ('PA', 'PRESION_ALTA_SJ1'), 
                ('PB', 'PRESION_BAJA_SQ1')
            ]
        }
    }

    #jd_conf = json.dumps(d_conf)
    #url = f'http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/configuracion'
    #req=requests.put(url=url,params={'unit':id}, json=jd_conf)
    #if req.status_code == 200:
    #    print(f'SET_CONFIG OK.')
    #else:
    #    print(f'SET_CONFIG FAIL. {req.status_code}')

    pk_d_conf = pickle.dumps(d_conf)
    rh = redis.Redis()
    rh.hset('PLCTEST','PKCONFIG',pk_d_conf)
    #
    d_line1={'DATE':'230519', 'TIME':'1200', 'HTQ1':1.23, 'HTQ2': 4.56 }
    pk_d_line1 = pickle.dumps(d_line1)
    rh.hset('KIYU001', 'PKLINE', pk_d_line1)
    #
    d_line2={'DATE':'230519', 'TIME':'1300', 'PA':3.4, 'PB':7.8}
    pk_d_line2 = pickle.dumps(d_line2)
    rh.hset('SJOSE001', 'PKLINE', pk_d_line2)

    order_atvise = { 'UPA1_ORDER_1':101, 'UPA1_CONSIGNA_6': 102, 'ESP_ORDER_8': 103 }
    pk_order_atvise = pickle.dumps(order_atvise)
    rh.hset('PLCTEST', 'PKATVISE', pk_order_atvise)

if __name__ == '__main__':
    #crear_configuracion_test()
    simulatePlc()



   



