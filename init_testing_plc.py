#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python
'''
Script que inicializa la BD Redis local con los datos necesarios para 
probar la parte de los PLC
'''
import redis
import pickle
import json

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

    pk_d_conf = pickle.dumps(json.dumps(d_conf))
    rh = redis.Redis()
    rh.hset('PLCTEST','PKCONFIG',pk_d_conf)
    #
    d_line1={'DATE':'230519', 'TIME':'1200', 'HTQ1':1.23, 'HTQ2': 4.56 }
    pk_d_line1 = pickle.dumps(json.dumps(d_line1))
    rh.hset('KIYU001', 'PKLINE', pk_d_line1)
    #
    d_line2={'DATE':'230519', 'TIME':'1300', 'PA':3.4, 'PB':7.8}
    pk_d_line2 = pickle.dumps(json.dumps(d_line2))
    rh.hset('SJOSE001', 'PKLINE', pk_d_line2)

    order_atvise = { 'UPA1_ORDER_1':101, 'UPA1_CONSIGNA_6': 102, 'ESP_ORDER_8': 103 }
    pk_order_atvise = pickle.dumps(json.dumps(order_atvise))
    rh.hset('PLCTEST', 'PKATVISE', pk_order_atvise)

if __name__ == '__main__':
    crear_configuracion_test()
