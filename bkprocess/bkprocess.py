#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python
'''
Loop infinito en que lee datos a travez de la API datos y los inserta en
la base pgsql local, en la tabla 'historicos'.
De este modo recrea la BD de Spymovil.
Otro proceso, 1 vez por hora lee la tabla de configuraciones y actualiza la local.
Mientras hallan datos, los lee cada 10 segundos, para no apretar al sistema.
'''

import os
import time
import signal
from multiprocessing import Process
import sys
import datetime as dt 
import json
import requests
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

MAX_INSERTS_CHUNK_SIZE = int(os.environ.get('MAX_INSERTS_CHUNK_SIZE',100))
SLEEP_TIME = int(os.environ.get('SLEEP_TIME',15))

APIDATOS_HOST = os.environ.get('APIDATOS_HOST','192.168.0.8')
APIDATOS_PORT = os.environ.get('APIDATOS_PORT','5300')
APIDATOS_USERKEY = "RMNC3O96SJ1DZH700DZ8"

PGSQL_HOST = os.environ.get('PGSQL_HOST','192.168.0.20')
PGSQL_PORT = os.environ.get('PGSQL_PORT', '5432')
PGSQL_USER = os.environ.get('PGSQL_USER', 'admin')
PGSQL_PASSWD = os.environ.get('PGSQL_PASSWD','pexco599')
PGSQL_BD = os.environ.get('PGSQL_BD', 'bd_spcomms')

VERSION = 'R001 @ 2023-08-24'

SECONDS_X_DIA = 86400

class BD_SQL_BASE:

    def __init__(self):
        self.engine = None
        self.conn = None
        self.connected = False
        self.response = ''
        self.status_code = 0
        self.url = f'postgresql+psycopg2://{PGSQL_USER}:{PGSQL_PASSWD}@{PGSQL_HOST}:{PGSQL_PORT}/{PGSQL_BD}'

    def connect(self):
        # Engine
        try:
            #self.engine = create_engine(url=self.url, echo=False, isolation_level="AUTOCOMMIT")
            self.engine = create_engine(url=self.url, echo=False )
        except SQLAlchemyError as err:
            print( f'(300) PROCESS_ERR001: Pgsql engine error, HOST:{PGSQL_HOST}:{PGSQL_PORT}, Err:{err}')
            self.connected = False
            return False 
        # Connection
        try:
            self.conn = self.engine.connect()
            self.conn.autocommit = True
        except SQLAlchemyError as err:
            print( f'(301) PROCESS_ERR002: Pgsql connection error, HOST:{PGSQL_HOST}:{PGSQL_PORT}, Err:{err}')
            self.connected = False
            return False
        #
        self.connected = True
        return True
        #

    def close(self):
        print( f'(DEBUG) BKPROCESS_INFO: Sql close and dispose R2. HOST:{PGSQL_HOST}:{PGSQL_PORT}')
        self.conn.invalidate()
        self.conn.close()     
        self.engine.dispose()

    def exec_sql(self, sql):
        # Ejecuta la orden sql.
        # Retorna un resultProxy o None
        if not self.connected:
            if not self.connect():
                print( f'(302) PROCESS_ERR002: Pgsql connection error, HOST:{PGSQL_HOST}:{PGSQL_PORT}, Err:{err}')
                return False
        #
        try:
            query = text(sql)
        except Exception as err:
            print( f'(303) PROCESS_ERR003: Sql query error, HOST:{PGSQL_HOST}:{PGSQL_PORT}, Err:{sql}')
            print( f'(304) PROCESS_ERR004: Sql query exception, HOST:{PGSQL_HOST}:{PGSQL_PORT}, Err:{err}')
            return False
        #
        try:
            #print(sql)
            _ = self.conn.execute(query)
        except Exception as err:
            self.conn.rollback()
            print( f'(305) PROCESS_ERR005: Sql exec error, HOST:{PGSQL_HOST}:{PGSQL_PORT}, Err:{err}')
            return False
        self.conn.commit()
        return True

    def insert_usuarios(self, l_usuarios):
        '''
        Inserta / actuliza los usuarios de la l_usuarios de a uno !!!
        '''
        for usuario in l_usuarios:
            user_id = usuario['user_id']
            fecha_ultimo_acceso = usuario['fecha_ultimo_acceso']
            data_ptr = usuario['data_ptr']
            #
            sql = f"INSERT INTO usuarios (user_id,fecha_ultimo_acceso,data_ptr)  \
                    VALUES ('{user_id}','{fecha_ultimo_acceso}','{data_ptr}') \
                    ON CONFLICT (user_id) DO UPDATE SET data_ptr = '{data_ptr}';"
            if not self.exec_sql(sql):
                print(f"(30x) PROCESS_ERR008: UPSET usuarios FAIL.")
                print(f"(30x) PROCESS_ERR008: SQL={sql}.")

    def insert_configuraciones(self, l_equipos):
        '''
        Inserta / actuliza las configuraciones de equipos de la l_equipos de a uno !!!
        '''
        for equipo in l_equipos:
            unit_id = equipo['unit_id']
            uid = equipo['uid']
            jconfig = json.dumps(equipo['jconfig'])
            #
            sql = f"INSERT INTO configuraciones (unit_id,uid,jconfig)  \
                    VALUES ('{unit_id}','{uid}','{jconfig}') \
                    ON CONFLICT (unit_id) DO UPDATE SET jconfig = '{jconfig}';"
            if not self.exec_sql(sql):
                print(f"(30x) PROCESS_ERR008: UPSET equipos FAIL.")
                print(f"(30x) PROCESS_ERR008: SQL={sql}.")

    def insert_bulk(self, l_datos):
        '''
        No controlo el largo de l_datos !!!.
        PGSQL n forma estándard acepta meter hasta 50 inserts juntos.!!!
        '''
        # Debo hacer chunks de N(50) inserts
        step = MAX_INSERTS_CHUNK_SIZE
        for i in range(0, len(l_datos), step):
            x = i
            chunk = l_datos[x:x+step]
            if len(chunk) == 0:
                return
            
            # TABLA HISTORICA
            sql_historica = f"INSERT INTO historica ( fechadata,fechasys,equipo,tag,valor) VALUES " 
            for element in chunk:
                tp = tuple(element)
                sql_historica += f'{tp},'
            # Remuevo el ultimo ,
            sql_historica = sql_historica[:-1]
            sql_historica += " ON CONFLICT DO NOTHING" 
            #print(sql_historica)
            #print(f'Chunk {i}')
            if not self.exec_sql(sql_historica):
                print(f"(30x) PROCESS_ERR008: BULK INSERT bdsql historica FAIL.")
            self.exec_sql('COMMIT')    
            #
            
def clt_C_handler(signum, frame):
    sys.exit(0)

def read_data_chunk():
    '''
    Lee de la API DATOS un paquete de datos. Obtengo una lista de listas, donde estas ultimas
    son: [fechaData, fechaSys, unit_id, medida, valor]
    [
        ['06/23/2023, 04:47:29', '06/23/2023, 04:49:02', 'ARROZUR01', 'q0', 38.46],
        ['06/23/2023, 04:47:29', '06/23/2023, 04:49:02', 'ARROZUR01', 'bt', 0.36],
        ['06/23/2023, 04:48:11', '06/23/2023, 04:49:02', 'SPY003', 'pA', -2.5],
        ['06/23/2023, 04:48:11', '06/23/2023, 04:49:02', 'SPY003', 'pB', -2.5],
        ['06/23/2023, 04:48:11', '06/23/2023, 04:49:02', 'SPY003', 'bt', 12.168]
    ]

    Esta lista es la que retorno.
    '''
    url = f'http://{APIDATOS_HOST}:{APIDATOS_PORT}/apidatos/datos'
    params={'user':APIDATOS_USERKEY}
    req=requests.get(url=url,params=params,timeout=10)
    if req.status_code != 200:
        print('(30x) BKPROCESS_ERR010: bkprocess_read_data_chunk ERR: !!!')
        return []
    #
    # Retorno la lista de datos recibida. Cada datos es un dict
    jd_rsp = req.json()
    l_datos = jd_rsp['l_datos']
    return l_datos

def read_usuarios():
    '''
    Leo las configuraciones de los usuarios.
    [{'user_id': '3TJWTLKBW4BR6CMI342V', 'fecha_ultimo_acceso': '2023-06-19 11:03:33', 'data_ptr': 0},
     {'user_id': 'A34HNXWUO3SF99FWKWTC', 'fecha_ultimo_acceso': '2023-06-19 11:40:31', 'data_ptr': 20338}
    ]
    '''
    url = f'http://{APIDATOS_HOST}:{APIDATOS_PORT}/apidatos/config/usuarios'
    req=requests.get(url=url,timeout=10)
    if req.status_code != 200:
        print('(30x) BKPROCESS_ERR010: bkprocess_read_usuarios ERR: !!!')
        return []
    #
    # Retorno la lista de datos recibida. Cada datos es un dict
    jd_rsp = req.json()
    l_usuarios = jd_rsp['l_usuarios']
    return l_usuarios

def read_equipos():
    '''
    Leo las configuraciones de los equipos.
    '''
    url = f'http://{APIDATOS_HOST}:{APIDATOS_PORT}/apidatos/config/equipos'
    req=requests.get(url=url,timeout=10)
    if req.status_code != 200:
        print('(30x) BKPROCESS_ERR010: bkprocess_read_equipos ERR: !!!')
        return []
    #
    # Retorno la lista de datos recibida. Cada datos es un dict
    jd_rsp = req.json()
    l_equipos = jd_rsp['l_equipos']
    return l_equipos

def insert_data( boundle_list ):
    '''
    Esta funcion recibe una lista [fechaData, fechaSys, unit_id, medida, valor] con 
    datos a insertar y hace las inserciones en la PGSQL.
    [
        ['06/23/2023, 04:47:29', '06/23/2023, 04:49:02', 'ARROZUR01', 'q0', 38.46],
        ['06/23/2023, 04:47:29', '06/23/2023, 04:49:02', 'ARROZUR01', 'bt', 0.36],
        ['06/23/2023, 04:48:11', '06/23/2023, 04:49:02', 'SPY003', 'pA', -2.5],
        ['06/23/2023, 04:48:11', '06/23/2023, 04:49:02', 'SPY003', 'pB', -2.5],
        ['06/23/2023, 04:48:11', '06/23/2023, 04:49:02', 'SPY003', 'bt', 12.168]
    ]
    '''
    start_time = time.time()
    nro_items = len(boundle_list)
    print(f"BKPROCESS: ITEMS={nro_items}")
    #
    bdsql = BD_SQL_BASE()
    if not bdsql.connect():
        print('(308) PROCESS_ERR010: process_frames ERROR, bd_connect !!!')
        return
    
    # Inserto
    bdsql.insert_bulk( boundle_list )
    elapsed = (time.time() - start_time)
    print(f"(310) BKPROCESS INFO: END. (elapsed={elapsed})")
    sys.stdout.flush()

def upset_usuarios( boundle_list ):
    '''
    Esta funcion recibe una lista con los datos (diccionarios) de los usuarios. 
    Los inserta o actualiza  en la PGSQL.
    [
        {'user_id': 'XPREINIRGBAAFQ11WMY3', 'fecha_ultimo_acceso': '2023-10-02 15:00:51', 'data_ptr': 84612291}
        {'user_id': 'JFW7YGUHXZPMD0LBBX0M', 'fecha_ultimo_acceso': '2023-06-19 11:58:25', 'data_ptr': 0}
        {'user_id': 'D1IYD22J5ABACVT9S4SY', 'fecha_ultimo_acceso': '2023-10-03 09:25:41', 'data_ptr': 85980504}
        {'user_id': 'M25Q5UW3QSA2S9XXMDJ4', 'fecha_ultimo_acceso': '2023-10-03 09:26:01', 'data_ptr': 85980504}
        {'user_id': 'RMNC3O96SJ1DZH700DZ8', 'fecha_ultimo_acceso': '2023-10-03 09:26:12', 'data_ptr': 85981116}
        {'user_id': 'JSEU1VVMDQ8IJM44R4E7', 'fecha_ultimo_acceso': '2023-10-03 09:26:18', 'data_ptr': 85981116}
        {'user_id': '2C3EKUM688ZC36XXZNQF', 'fecha_ultimo_acceso': '2023-10-03 09:26:27', 'data_ptr': 85981116}
    ]
    '''
    start_time = time.time()
    nro_items = len(boundle_list)
    print(f"BKPROCESS USUARIOS: ITEMS={nro_items}")
    #
    bdsql = BD_SQL_BASE()
    if not bdsql.connect():
        print('(308) PROCESS_ERR010: process_frames ERROR, bd_connect !!!')
        return
    
    # Inserto
    bdsql.insert_usuarios( boundle_list )
    elapsed = (time.time() - start_time)
    print(f"(310) BKPROCESS DATOS INFO: END. (elapsed={elapsed})")
    sys.stdout.flush()

def upset_equipos( boundle_list):
    '''
    Esta funcion recibe una lista con los datos (diccionarios) de los equipos. 
    Los inserta o actualiza  en la PGSQL.
    [
        {'unit_id': 'SJPERF047', 'uid': '0', 'jconfig': {'MEMBLOCK': {'DATOS_PLC': [['CANAL_ANALOG_2', 'FLOAT', 1],.....
        {'unit_id': 'RIVPERF053', 'uid': '0', 'jconfig': {'MEMBLOCK': {'CONFIGURACION': [['DUMMY', 'uchar', 0], .....
        {'unit_id': 'SJTQ014', 'uid': '0', 'jconfig': {'AINPUTS': {'A0': {'IMIN': '4', 'NAME': 'LTQ', 'MMIN': '0', 'MMAX': '5',....
    ]
    '''
    start_time = time.time()
    nro_items = len(boundle_list)
    print(f"BKPROCESS EQUIPOS: ITEMS={nro_items}")
    #
    bdsql = BD_SQL_BASE()
    if not bdsql.connect():
        print('(308) PROCESS_ERR010: process_frames ERROR, bd_connect !!!')
        return
    
    # Inserto
    bdsql.insert_configuraciones( boundle_list[:10] )
    elapsed = (time.time() - start_time)
    print(f"(310) BKPROCESS EQUIPOS INFO: END. (elapsed={elapsed})")
    sys.stdout.flush()

def backup_data():
    '''
    Funcion que lee datos desde la API y los inserta en 
    la tb_historico.
    '''
    l_datos = read_data_chunk()
    if len(l_datos) > 0:
        p1 = Process(target = insert_data, args = (l_datos,))
        p1.start()
    #

def backup_configuraciones():
    '''
    Leo las configuraciones de los equipos y  actualizo la BD.
    '''
    l_equipos = read_equipos()
    if len(l_equipos) > 0:
        p1 = Process(target = upset_equipos, args = (l_equipos,))
        p1.start()

def backup_usuarios():
    '''
    Lee los usuarios desde la API y actualiza la BD local
    '''
    l_usuarios = read_usuarios()
    if len(l_usuarios) > 0:
        p1 = Process(target = upset_usuarios, args = (l_usuarios,))
        p1.start()
    

if __name__ == '__main__':

    signal.signal(signal.SIGINT, clt_C_handler)

    print("BKPROCESS Starting...")
    print(f'-SLEEP_TIME={SLEEP_TIME}')
    print(f'-MAX_NSERTS_CHUNK={MAX_INSERTS_CHUNK_SIZE}')
    print(f'-APIDATOS={APIDATOS_HOST}/{APIDATOS_PORT}')
    print(f'-PGSQL_HOST={PGSQL_HOST}/{PGSQL_PORT}')

    # Espero para siempre
    # Una vez por día actualizo la configuración de equipos y usuarios
    seconds = 0
    while True:
        backup_data()
        #
        print('Running...')
        if seconds == 0:
            backup_usuarios()
            backup_configuraciones()
        #
        time.sleep(SLEEP_TIME)
        seconds += SLEEP_TIME
        if seconds > SECONDS_X_DIA:
            seconds = 0
    #