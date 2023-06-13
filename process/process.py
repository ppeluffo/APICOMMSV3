#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python
'''
Proceso en forma lineal la cola de datos RXDATA_QUEUE.
En esta, cada elemento es un pickle de un dict con el formato:
 {'PROTO':protocol, 'DLGID':dlgid, 'D_LINE':d_line}.
El proceso master lee y saca todos los elementos de la cola y
arma 2 listas: uno para SPX y otro para PLC
Pone los elementos correspondientes en c/lista e invoca a un
subproceso para c/u.
Luego duerme 60s.
'''

import time
import signal
from multiprocessing import Process
import sys
import datetime as dt 
import requests
import json
from sqlalchemy import create_engine, exc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

#APIREDIS_HOST = 'apiredis'
APIREDIS_HOST = '127.0.0.1'
APIREDIS_PORT = '5100'

#PGSQL_HOST = 'pgsql'
PGSQL_HOST = '127.0.0.1'
PGSQL_PORT = '5432'
PGSQL_USER = 'admin'
PGSQL_PASSWD = 'pexco599'
PGSQL_BD = 'bd_spcomms'

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
            self.engine = create_engine(url=self.url, echo=False)
        except SQLAlchemyError as err:
            print( f'PROCESS_ERR001: Pgsql engine error, HOST:{PGSQL_HOST} Err={err}')
            self.connected = False
            return False 
        # Connection
        try:
            self.conn = self.engine.connect()
        except SQLAlchemyError as err:
            print( f'CONFSQL_ERR002: Pgsql connection error, HOST:{PGSQL_HOST} Err={err}')
            self.connected = False
            return False
        #
        self.connected = True
        return True
        #

    def exec_sql(self, sql):
        # Ejecuta la orden sql.
        # Retorna un resultProxy o None
        if not self.connected:
            if not self.connect():
                print({ 'PROCESS: exec_sql: ERROR: No hay conexion a BD. Exit !!'})
                return False
        #
        try:
            query = text(sql)
        except Exception as err_var:
            print( f"PROCESS: query_sql, MSG: ERROR SQLQUERY: {sql}")
            print( f"PROCESS: query_sql, MSG: EXCEPTION: {err_var}")
            return False
        #
        try:
            print(sql)
            _ = self.conn.execute(query)
        except Exception as err_var:
            print( f"PROCESS: exec_sql, MSG: EXCEPTION: {err_var}")
            return False
        return True

    def insert_raw(self, unit_id, key, value, datetime):
        '''
        Ejecuta la iserción raw en la bd
        Retorna un resultProxy o None
        '''
        dnow = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not datetime: 
            datetime = dnow
        else: 
            # paso del fromato yymmdd hhmmss a yyyy-mm-dd hh:mm:ss utilizado por la bd
            # utilizo la funcion strptime
            datetime = dt.datetime.strptime(datetime, "%y%m%d %H%M%S")

            ## FALTA VALIDAR LA FECHA ##
            # if datetime > dt.datetime.now():
            #     datetime = datetime - dt.timedelta(days=1)
            # .strftime("%Y-%m-%d %H:%M:%S")

        # TABLA HISTORICA
        sql = f"INSERT INTO historica ( fechadata,fechasys,equipo,tag,valor) VALUES ('{datetime}', '{dnow}','{unit_id}','{key}','{value}')  ON CONFLICT DO NOTHING" 
        if self.exec_sql(sql):
            print(f"INSERT bdsql historica OK !! (unit={unit_id})")
        else:
            print(f"INSERT bdsql historica FAIL !! (unit={unit_id})")
        #
        # TABLA ONLINE
        sql = f"INSERT INTO online ( fechadata,fechasys,equipo,tag,valor) VALUES ('{datetime}', '{dnow}','{unit_id}','{key}','{value}')  ON CONFLICT DO NOTHING" 
        if self.exec_sql(sql):
            print(f"INSERT bdsql online OK !! (unit={unit_id})")
        else:
            print(f"INSERT bdsql online FAIL !! (unit={unit_id})")
        #

def clt_C_handler(signum, frame):
    sys.exit(0)

def process_frames( protocolo, boundle_list ):
    '''
    Esta funcion recibe una lista con diccionarios de datos a insertar y
    hace las inserciones.
    '''
    nro_items = len(boundle_list)
    print(f"PROCESS: process_frames, PROTO:{protocolo}, ITEMS_LENGTH={nro_items}")
    #
    bdsql = BD_SQL_BASE()
    if not bdsql.connect():
        print('PROCESS: rocess_frames ERROR, bd_connect !!!')
        return
    
    # Leo c/dict del bundle y lo proceso
    for d_data in boundle_list:
        unit_id = d_data.get('id','0000')
        jd_line = d_data.get('d_line',{})
        d_line = json.loads(jd_line)
        ddate = d_line.pop('DATE',None)
        dtime = d_line.pop('TIME',None)

        datetime = None        
        if ddate and dtime:
            datetime = f'{ddate} {dtime}'

        print(f"PROCESS: process_frames, PROTO{protocolo}, D_LINE={d_line}")
        for key in d_line:
            value = d_line[key]
            msg = f'{protocolo},{unit_id},{datetime},{key}=>{value}'
            #print( f"PROCESS: process_frames, MSG:{msg}")
            #
            bdsql.insert_raw( unit_id, key, value, datetime)
        #
    #
    print(f"PROCESS: process_frames {protocolo} EXIT")
    sys.stdout.flush()

def read_data_queue_length():
    try:
        r_conf = requests.get(f"http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/queuelength", params={'qname':'RXDATA_QUEUE'}, timeout=10 )
    except requests.exceptions.RequestException as err: 
        print(f"ERROR XC001: request exception, Err={err}")
        return -1
    
    if r_conf.status_code == 200:
        d = json.loads(r_conf.json())
        queue_length = d.get('length',-1)
        return queue_length
    
def read_data_queue(count):

    try:
        params = {'qname':'RXDATA_QUEUE', 'count':count }
        r_conf = requests.get(f"http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/queueitems", params=params, timeout=10 )
    except requests.exceptions.RequestException as err: 
        print(f"ERROR XC001: request exception, Err={err}")
        return []
    
    if r_conf.status_code != 200:
        return []
    
    # Cada elemento es del tipo: {'TYPE':args['type'], 'ID':args['unit'], 'D_LINE':d_params}
    l_datos = json.loads(r_conf.json())
    return l_datos
          
if __name__ == '__main__':

    signal.signal(signal.SIGINT, clt_C_handler)

    # Espero para siempre
    while True:
        # Leo el tamaño de la cola de RXDATA_QUEUE.
        if read_data_queue_length() > 0:
            # Si hay datos leo la cola, los leo
            l_datos = read_data_queue(3)
            dlg_list = []
            plc_list = []
            # Separo los datos de c/tipo en una lista distinta
            for element in l_datos:
                tipo = element.get('TYPE','UNKNOWN')
                id = element.get('ID','UNKNOWN')
                d_line = element.get('D_LINE',{})
                #
                if 'DLG' in tipo:
                    dlg_list.append({'id':id, 'd_line':d_line})
                elif 'PLC' in tipo:
                    plc_list.append({'id':id, 'd_line':d_line})
            #
            # Proceso las listas
            if len(dlg_list) > 0:
                p1 = Process(target = process_frames, args = ('DLG', dlg_list))
                p1.start()
            #
            if len(plc_list) > 0:
                p2 = Process(target = process_frames, args = ('PLC', plc_list))
                p2.start()
        #
        #
        time.sleep(60)
    #