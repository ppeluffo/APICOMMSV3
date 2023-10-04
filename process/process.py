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

-----------------------------------------------------------------------------
R001 @ 2023-09-26 (commsv3_process:1.3)
- Agrego los elementos para procesar los datos de las estaciones OCEANUS
- Modifico exec_sql para que devuelva un cursor.
-----------------------------------------------------------------------------
R001 @ 2023-06-17 (commsv3_process:1.2)
- Hago modificaciones para hacer insert bulk en la pgsql en vez de insertar
  de a 1 fila.
  Modifico 'process_frames' para que genere una lista de tuplas con los valores
  a insertar
  Creo la funcion 'insert_bulk' para que haga los inserts.

-----------------------------------------------------------------------------
R001 @ 2023-06-15 (commsv3_process:1.1)
- Se manejan todos los parámetros por variables de entorno


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
MAX_DEQUEUE_ITEMS = int(os.environ.get('MAX_DEQUEUE_ITEMS',100))
SLEEP_TIME = int(os.environ.get('SLEEP_TIME',60))

APIREDIS_HOST = os.environ.get('APIREDIS_HOST','apiredis')
APIREDIS_PORT = os.environ.get('APIREDIS_PORT','5100')

PGSQL_HOST = os.environ.get('PGSQL_HOST','pgsql')
PGSQL_PORT = os.environ.get('PGSQL_PORT', '5432')
PGSQL_USER = os.environ.get('PGSQL_USER', 'admin')
PGSQL_PASSWD = os.environ.get('PGSQL_PASSWD','pexco599')
PGSQL_BD = os.environ.get('PGSQL_BD', 'bd_spcomms')

VERSION = 'R001 @ 2023-09-26'

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
            #self.conn.autocommit = True
        except SQLAlchemyError as err:
            print( f'(301) PROCESS_ERR002: Pgsql connection error, HOST:{PGSQL_HOST}:{PGSQL_PORT}, Err:{err}')
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
            cursor = self.conn.execute(query)
        except Exception as err:
            print( f'(305) PROCESS_ERR005: Sql exec error, HOST:{PGSQL_HOST}:{PGSQL_PORT}, Err:{err}')
            return False
        return cursor

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
        sql = f"INSERT INTO historica ( fechadata,fechasys,equipo,tag,valor) VALUES ('{datetime}', '{dnow}','{unit_id}','{key}','{value}') ON CONFLICT DO NOTHING" 
        if not self.exec_sql(sql):
            print(f"(306) PROCESS_ERR008: INSERT bdsql historica FAIL !! (unit={unit_id})")
        #
        # TABLA ONLINE
        sql = f"INSERT INTO online ( fechadata,fechasys,equipo,tag,valor) VALUES ('{datetime}', '{dnow}','{unit_id}','{key}','{value}') ON CONFLICT DO NOTHING" 
        if not self.exec_sql(sql):
            print(f"(307) PROCESS_ERR009; INSERT bdsql online FAIL !! (unit={unit_id})")
        #

    def insert_bulk(self, l_tuples):
        '''
        No controlo el largo de l_ntuples !!!.
        Si MAX_DEQUEUE_ITEMS = 100 y c/frame tiene 4 variables, entonces l_tuples es de 400 elementos.
        Hay que sintonizar la pgsq para que acepte esto.
        En forma estándard acepta meter hasta 50 inserts juntos.!!!
        '''
        # Debo hacer chunks de N(50) inserts
        step = MAX_INSERTS_CHUNK_SIZE
        for i in range(0, len(l_tuples), step):
            x = i
            chunk = l_tuples[x:x+step]
            if len(chunk) == 0:
                return
            
            # TABLA HISTORICA
            sql_historica = f"INSERT INTO historica ( fechadata,fechasys,equipo,tag,valor) VALUES " 
            sql_online = f"INSERT INTO online ( fechadata,fechasys,equipo,tag,valor) VALUES " 
            for t in chunk:
                sql_historica += f'{t},'
                sql_online += f'{t},'
            # Remuevo el ultimo ,
            sql_historica = sql_historica[:-1]
            sql_historica += " ON CONFLICT DO NOTHING" 
            sql_online = sql_online[:-1]
            sql_online += " ON CONFLICT DO NOTHING" 

            #print(f'DEBUG: SQL={sql_online}')
            #print(f'Chunk {i}')
            if not self.exec_sql(sql_historica):
                print(f"(30x) PROCESS_ERR008: BULK INSERT bdsql historica FAIL.")
            self.exec_sql('COMMIT')
            #
            if not self.exec_sql(sql_online):
                print(f"(30x) PROCESS_ERR008: BULK INSERT bdsql online FAIL.")
            self.exec_sql('COMMIT')      
            #

    def read_usuarios(self):
        '''
        Retorna todos los datos de la tabla de usuario
        '''
        sql = f"SELECT * FROM usuarios ORDER BY data_ptr ASC" 
        cursor = self.exec_sql(sql)
        if not cursor:
            print(f"(30x) PROCESS_ERR008: SELECT bdsql FAIL !! sql={sql}")
            return False
        return cursor
        
    def update_online(self,idx):
        '''
        Borra los registros de tb_online hasta el idx
        Si idx=-1, borro todos los registros.
        '''
        if idx == -1:
            sql = f"DELETE FROM online" 
        else:    
            sql = f"DELETE FROM online WHERE id < {idx}" 
        _ = self.exec_sql(sql)
        self.conn.commit()

def clt_C_handler(signum, frame):
    sys.exit(0)

def process_frames( protocolo, boundle_list ):
    '''
    Esta funcion recibe una lista con diccionarios de datos a insertar y
    hace las inserciones.
    '''
    start_time = time.time()
    nro_items = len(boundle_list)
    print(f"PROCESS: PROTO:{protocolo}, ITEMS={nro_items}")
    #
    bdsql = BD_SQL_BASE()
    if not bdsql.connect():
        print('(308) PROCESS_ERR010: process_frames ERROR, bd_connect !!!')
        return
    
    # Leo c/dict del bundle y lo proceso
    l_tuples = []
    sfechasys = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for d_data in boundle_list:
        unit_id = d_data.get('id','0000')
        d_line = d_data.get('d_line',{})
        ddate = d_line.pop('DATE',None)
        dtime = d_line.pop('TIME',None)
        sfechadata = None        
        if ddate and dtime:
            sfechadata = f'{ddate} {dtime}'
            try:
                fechadata = dt.datetime.strptime(sfechadata, '%y%m%d %H%M%S')
                sfechadata = fechadata.strftime("%Y-%m-%d %H:%M:%S")
            except Exception as err:
                print(f'ERROR en conversion de fechaData: ddate={ddate},dtime={dtime},ddata={d_data}')
                print(f'ERROR: {err}')
        
        else:
            sfechadata = sfechasys

        #print(f"(309) PROCESS INFO: PROTO:{protocolo},ID={unit_id},D_LINE={d_line}")
        
        for key in d_line:
            value = d_line[key]
            #msg = f'{protocolo},{unit_id},{datetime},{key}=>{value}'
            #print( f"PROCESS: process_frames, MSG:{msg}")
            #
            #bdsql.insert_raw( unit_id, key, value, datetime)
            l_tuples.append( (sfechadata, sfechasys, unit_id, key, value) )
        #
    #
    bdsql.insert_bulk(l_tuples)
    elapsed = (time.time() - start_time)
    print(f"(310) PROCESS INFO: process_frames({len(l_tuples)}) {protocolo} END. (elapsed={elapsed})")
    sys.stdout.flush()

def read_data_queue_length():
    try:
        r_conf = requests.get(f"http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/queuelength", params={'qname':'RXDATA_QUEUE'}, timeout=10 )
    except requests.exceptions.RequestException as err: 
        print(f"(311) PROCESS_ERR006: queuelength request exception, Err={err}")
        return -1
    #
    if r_conf.status_code == 200:
        d = r_conf.json()
        queue_length = d.get('length',-1)
        return queue_length
    #
    return -1
    
def read_data_queue(count):

    try:
        params = {'qname':'RXDATA_QUEUE', 'count':count }
        r_conf = requests.get(f"http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/queueitems", params=params, timeout=10 )
    except requests.exceptions.RequestException as err: 
        print(f"(312) PROCESS_ERR007: queuedata request exception, Err={err}")
        return []
    
    if r_conf.status_code != 200:
        return []
    
    # Cada elemento es del tipo: {'TYPE':args['type'], 'ID':args['unit'], 'D_LINE':d_params}.
    d_resp = r_conf.json()
    l_datos = d_resp.get('ldatos',[])
    return l_datos

def housekeeping_online():
    '''
    Mantiene la tabla online en un minimo
    '''      
    bdsql = BD_SQL_BASE()
    cursor = bdsql.read_usuarios()
    if not cursor:
        print(f"(315) PROCESS_ERR009: No puedo leer tb_usuarios !!")
        return
    #
    l_dates = []
    l_idx = []
    idx = []
    now=dt.datetime.now()
    for t in cursor:
        l_dates.append(t[1])
        l_idx.append(t[2])
    # Solo considero aquellos que hayan tenido actividad en los ultimos 3 dias ( 72 horas)
    for i,date in enumerate(l_dates):
        deltatime = (now - date).total_seconds()/3600
        #print(f"{date},delta={deltatime}")
        if deltatime < 72:
            idx.append(l_idx[i])
    #
    #print(f"DEBUG PROCESS: L_IDX={l_idx},IDX={idx}")
    rcd_id = -1
    if len(idx) > 0:
        rcd_id = min(idx)
        
    bdsql.update_online(rcd_id)
    print(f'PROCESS: housekeeping online delete from:{rcd_id} !!')

if __name__ == '__main__':

    signal.signal(signal.SIGINT, clt_C_handler)

    '''
    APIREDIS_HOST = '127.0.0.1'
    APIREDIS_PORT = '5100'
    PGSQL_HOST = '127.0.0.1'
    PGSQL_PORT = '5432'
    PGSQL_USER = 'admin'
    PGSQL_PASSWD = 'pexco599'
    PGSQL_BD = 'bd_spcomms'
    '''
    print("APICOMMS PROCESS Starting...Waiting 60 secs....")
    print(f'-SLEEP_TIME={SLEEP_TIME}')
    print(f'-MAX_DEQUEUE_ITEMS={MAX_DEQUEUE_ITEMS}')
    print(f'-APIREDIS={APIREDIS_HOST}/{APIREDIS_PORT}')
    print(f'-PGSQL_HOST={PGSQL_HOST}/{PGSQL_PORT}')


    # Espero para siempre
    while True:
        # Leo el tamaño de la cola de RXDATA_QUEUE.
        qlength = read_data_queue_length()
        #print(f'DEBUG QLENGTH={qlength}')
        if  qlength > 0:
            # Si hay datos leo la cola, los leo
            l_datos = read_data_queue( MAX_DEQUEUE_ITEMS )
            #print(f'DEBUG: L_DATOS={l_datos}')
            dlg_list = []
            plc_list = []
            oceanus_list = []
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
                elif 'OCEANUS' in tipo:
                    oceanus_list.append({'id':id, 'd_line':d_line})
            #
            process_list = []
            # Proceso las listas
            if len(dlg_list) > 0:
                p1 = Process(target = process_frames, args = ('DLG', dlg_list))
                p1.start()
                process_list.append(p1)
            #
            if len(plc_list) > 0:
                p2 = Process(target = process_frames, args = ('PLC', plc_list))
                p2.start()
                process_list.append(p2)
            #
            if len(oceanus_list) > 0:
                p3 = Process(target = process_frames, args = ('OCEANUS', oceanus_list))
                p3.start()
                process_list.append(p3)
            #
            # Espero a que terminen los procesos
            for p in process_list:
                p.join()
            #
            # Ajusto la tabla online
            housekeeping_online()
        #
        time.sleep(SLEEP_TIME)
    #