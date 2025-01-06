#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python
'''
Api de configuracion SQL de dataloggers y PLC para el servidor APISERVER

https://www.gorgias.com/blog/prevent-idle-in-transaction-engineering
https://4geeks.com/lesson/everything-you-need-to-start-using-sqlalchemy


BASE DE DATOS:
psql>CREATE DATABASE bd_unidades;
psql>CREATE TABLE configuraciones ( pk SERIAL PRIMARY KEY, unit_id VARCHAR (20), uid VARCHAR (50), jconfig JSON);

pip install --upgrade wheel
apt-get install libpq-dev
pip install psycopg2

-----------------------------------------------------------------------------
R002 @ 2025-01-03
- Creo un nuevo entrypoint '/apiconf/commsidparams' al cual le mando un json con 
  el dlgid, simid, uid, iccid y crea una entrada en la bd.
-----------------------------------------------------------------------------
R001 @ 2023-06-17 (commsv3_apiconf:1.2)
- En el entrypoint '/apiconf/unidades' el json que devuelvo tiene una nueva
  clave 'nro_unidades'
  
-----------------------------------------------------------------------------
R001 @ 2023-06-14 (commsv3_apiconf:1.1)
- Se manejan todos los parámetros por variables de entorno
- Se agrega un entrypoint 'ping' que permite ver si la api esta operativa

'''
import os
import json
from sqlalchemy import create_engine, exc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from sqlalchemy.pool import NullPool
import logging
from flask import Flask, request, jsonify
from flask_restful import Resource, Api, reqparse
from apiconf_templates import DLG_CONF_TEMPLATE, PLC_CONF_TEMPLATE
from collections.abc import MutableMapping

PGSQL_HOST = os.environ.get('PGSQL_HOST', 'pgsql')
PGSQL_PORT = os.environ.get('PGSQL_PORT','5432')
PGSQL_USER = os.environ.get('PGSQL_USER', 'admin')
PGSQL_PASSWD = os.environ.get('PGSQL_PASSWD', 'pexco599')
PGSQL_BD = os.environ.get('PGSQL_BD','bd_spcomms')

APICONF_HOST = os.environ.get('APICONF_HOST','apiconf')
APICONF_PORT = os.environ.get('APICONF_PORT','5200')

API_VERSION = 'R001 @ 2023-06-17'

app = Flask(__name__)
api = Api(app)

'''
ERROR SQL001: Pgsql engine error
ERROR SQL002: Pgsql connection error
ERROR SQL003: Pgsql execute error

WARN SQL001: No config rcd in SQL


'''
class BD_SQL_BASE:

    def __init__(self):
        self.engine = None
        self.conn = None
        self.response = ''
        self.status_code = 0
        self.url = f'postgresql+psycopg2://{PGSQL_USER}:{PGSQL_PASSWD}@{PGSQL_HOST}:{PGSQL_PORT}/{PGSQL_BD}'

    def connect(self):
        # Engine
        try:
            self.engine = create_engine(url=self.url, echo=False, isolation_level="AUTOCOMMIT", poolclass=NullPool, connect_args={'connect_timeout': 5})
        except SQLAlchemyError as err:
            app.logger.info( f'(100) ApiCONF_ERR001: Pgsql engine error, HOST:{PGSQL_HOST}:{PGSQL_PORT}, Err:{err}')
            return False 
        # Connection
        try:
            self.conn = self.engine.connect()
            self.conn.autocommit = True
        except SQLAlchemyError as err:
            app.logger.info( f'(101) ApiCONF_ERR002: Pgsql connection error, HOST:{PGSQL_HOST}:{PGSQL_PORT}, Err:{err}')
            return False
        #
        return True
        #

    def close(self):
        '''
        '''
        app.logger.info( f'(DEBUG) ApiCONF_INFO: Sql close and dispose R2. HOST:{PGSQL_HOST}:{PGSQL_PORT}')
        self.conn.invalidate()
        self.conn.close()     
        self.engine.dispose()

    def kill_idle_connections(self):
        '''
        Funcion que mata las tareas idle de la bd.
        https://linuxhint.com/kill-idle-connections-postgresql/
        select pid,state, usename,datname,datid from pg_stat_activity where state = 'idle' and datname=current_database()
        '''
        sql = '''
        select pid from pg_stat_activity where state = 'idle' and datname=current_database() order  by pid asc
        '''
        query = text(sql)
        rp = self.conn.execute(query)
        # Dejo al menos 3 conexiones
        i = 0
        for row in rp.fetchall():
            pid = row[0]
            i += 1
            if i < 4:
                continue
            print(f'DEBUG: {pid}')
            sql = f"select pg_terminate_backend({pid})"
            query = text(sql)
            #_ = self.conn.execute(query)

    def remove_idle_connections(self):
        sql = '''
        WITH inactive_connections AS (
            SELECT pid, rank() over (partition by client_addr order by backend_start ASC) as rank
    `   FROM pg_stat_activity
        WHERE
            -- Exclude the thread owned connection (ie no auto-kill)
            pid <> pg_backend_pid( )
        AND
            -- Exclude known applications connections
            application_name !~ '(?:psql)|(?:pgAdmin.+)'
        AND
            -- Include connections to the same database the thread is connected to
            datname = current_database() 
        AND
            -- Include connections using the same thread username connection
            usename = current_user 
        AND
            -- Include inactive connections only
            state in ('idle', 'idle in transaction', 'idle in transaction (aborted)', 'disabled') 
        AND
            -- Include old connections (found with the state_change field)
            current_timestamp - state_change > interval '5 minutes' 
        )
        SELECT pg_terminate_backend(pid)
        FROM inactive_connections 
        WHERE rank > 1
        '''
        query = text(sql)
        try:
            #print(sql)
            _ = self.conn.execute(query)
        except Exception as err:
            app.logger.info( f'(116) ApiDATOS_ERR005: Sql exec error, HOST:{PGSQL_HOST}:{PGSQL_PORT}, Err:{err}')
        #

    def exec_sql(self, sql):
        # Ejecuta la orden sql.
        # Retorna un resultProxy o None
        if not self.connect():
            app.logger.info( f'(102) ApiCONF_ERR002: Pgsql connection error, HOST:{PGSQL_HOST}:{PGSQL_PORT}')
            return {'res':False }
        #
        try:
            query = text(sql)
        except Exception as err:
            app.logger.info( f'(103) ApiCONF_ERR003: Sql query error, HOST:{PGSQL_HOST}:{PGSQL_PORT}, Err:{sql}')
            app.logger.info( f'(104) ApiCONF_ERR004: Sql query exception, HOST:{PGSQL_HOST}:{PGSQL_PORT}, Err:{err}')
            return {'res':False }
        #
        try:
            #print(sql)
            rp = self.conn.execute(query)
        except Exception as err:
            app.logger.info( f'(105) ApiDATOS_ERR005: Sql exec error, HOST:{PGSQL_HOST}:{PGSQL_PORT}, Err:{err}')
            return {'res':False }
        #
        return {'res':True,'rp':rp }

    def read_configuration(self, unit_id):
        '''
        Lee el jconfig  del usuario
        '''
        sql = f"SELECT jconfig FROM configuraciones WHERE unit_id = '{unit_id}'" 
        d_res = self.exec_sql(sql)
        if not d_res.get('res',False):
            app.logger.info( '(105) ApiCONF_ERR007: select_user FAIL')
        return d_res
        #

    def insert_configuration(self, unit_id, jd_config ):
        '''
        Inserta un nuevo usuario en la tabla usuarios
        Retorna True/False
        '''
        # Determino si existe el registro (UPDATE) o no (INSERT)
        sql = f"SELECT pk FROM configuraciones WHERE unit_id = '{unit_id}'"
        d_res = self.exec_sql(sql)
        if not d_res.get('res',False):
            app.logger.info( '(106) ApiCONF_ERR008: insert_user FAIL')
            return d_res
        #
        rp = d_res.get('rp',None)
        if rp.rowcount == 0:
            # Hago un INSERT:
            sql = f"INSERT INTO configuraciones (unit_id, uid, jconfig ) VALUES ('{unit_id}','0','{jd_config}')"
        else:
            row = rp.fetchone()
            pk = row[0]
            sql = f"UPDATE configuraciones SET jconfig = '{jd_config}' WHERE pk = '{pk}'"
        #
        d_res = self.exec_sql(sql)
        if not d_res.get('res',False):
            app.logger.info( '(107) ApiCONF_ERR008: insert_user FAIL')
        return d_res

    def read_uid(self, uid):
        '''
        '''
        sql = f"SELECT id FROM recoverid WHERE uid = '{uid}'" 
        d_res = self.exec_sql(sql)
        if not d_res.get('res',False):
            app.logger.info( '(108) ApiCONF_ERR012: read_uid FAIL')
        return d_res

    def insert_uid(self, id, uid):
        '''
        '''
        sql = f"DELETE FROM recoverid WHERE uid = '{uid}'"
        d_res = self.exec_sql(sql)
        sql = f"DELETE FROM recoverid WHERE id = '{id}'"
        d_res = self.exec_sql(sql)
        #
        sql = f"INSERT INTO recoverid (id, uid ) VALUES ('{id}','{uid}')"
        d_res = self.exec_sql(sql)
        if not d_res.get('res',False):
            app.logger.info( '(109) ApiCONF_ERR011: insert_uid FAIL')
            return d_res
        #
        return d_res

    def read_allunits(self):
        '''
        Lee todas las unidades configuradas.
        '''
        sql = "SELECT unit_id FROM configuraciones"
        d_res = self.exec_sql(sql)
        if not d_res.get('res',False):
            app.logger.info( '(105) ApiCONF_ERR007: select_user FAIL')
        return d_res

    def insert_comms_id_config(self, d_config ):
        '''
        Inserta un nuevo usuario en la tabla usuarios
        Retorna True/False
        {
            "UID": "xxxxxxxx",
            "IMEI": "xxxxxxxx",
            "ICCID": "xxxxxxxx",
            "TYPE": "xxxxxxxx",
            "VER": "xxxxxxxx"
        }
        '''
        dlgid = d_config.get('DLGID',None)
        uid = d_config.get('UID','NONE')
        imei = d_config.get('IMEI','NONE')
        iccid = d_config.get('ICCID','NONE')
        type = d_config.get('TYPE','NONE')
        ver = d_config.get('VER','NONE')

        #print(f'BD_DEBUG: dlgid={dlgid},uid={uid},imei={imei},iccid={iccid}')

        # Hago un INSERT:
        sql = f"INSERT INTO comms_logs (fecha, dlgid, type, ver, uid, imei, iccid ) VALUES ('NOW()', '{dlgid}','{type}','{ver}','{uid}','{imei}','{iccid}')"
        d_res = self.exec_sql(sql)
        if not d_res.get('res',False):
            app.logger.info( '(107) ApiCONF_ERR008: insert_comms_id_config FAIL')
        return d_res


class Kill(Resource):
    def get(self):
        bdsql = BD_SQL_BASE()
        bdsql.connect()
        bdsql.kill_idle_connections()
        bdsql.close()
        return {'rsp':'OK'},200  
       
class Test(Resource):
    '''
    Abre una conexion y la cierra.
    '''
    def get(self):
        #
        bdsql = BD_SQL_BASE()
        bdsql.connect()
        bdsql.remove_idle_connections()
        bdsql.close()
        return {'rsp':'OK'},200

class Ping(Resource):
    '''
    Prueba la conexion a la SQL
    '''
    def get(self):

        bdpgsl = BD_SQL_BASE()
        if bdpgsl.connect():
            print("Connected to PGSQL!")
            bdpgsl.close()
            return {'rsp':'OK','version':API_VERSION,'SQL_HOST':PGSQL_HOST, 'SQL_PORT':PGSQL_PORT },200
        #
        d_rsp = {'rsp':'ERROR', 'msg':f'ApiCONF_ERR001: Pgsql connect error, HOST:{PGSQL_HOST}:{PGSQL_PORT}' }
        return d_rsp, 500

class GetTemplate(Resource):
    '''
    Retorna un json con el template de la version solicitada.
    Si esta es "latest" se manda la ultima version
    '''
    def get(self):
        '''
        Testing:
            req=requests.get('http://127.0.0.1:5200/apiconf/template', params={'ver':'1.1.0','type':'PLC'})
            jd_template=req.json()
            d_template=json.loads(jd_template)
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('ver',type=str,location='args',required=True)
        parser.add_argument('type',type=str,location='args',required=True)
        args=parser.parse_args()
        s_version = args['ver']
        s_type = args['type']
        #
        if s_type.upper() == 'DLG':
            if s_version.upper() == 'LATEST':
                s_version = list(DLG_CONF_TEMPLATE.keys())[0]
        #
            if s_version not in list(DLG_CONF_TEMPLATE.keys()):
                return {},204
        #
            d_template = DLG_CONF_TEMPLATE[s_version]
            d_rsp = {'version': s_version, 'template': d_template}
            return d_rsp,200

        if s_type.upper() == 'PLC':
            if s_version.upper() == 'LATEST':
                s_version = list(PLC_CONF_TEMPLATE.keys())[0]

            if s_version not in list(PLC_CONF_TEMPLATE.keys()):
                return {},204
        #
            d_template = PLC_CONF_TEMPLATE[s_version]
            d_rsp = {'version': s_version, 'template': d_template}
            return d_rsp,200
        
        return {},204
        
class GetVersiones(Resource):
    '''
    Retorna un json con la lista de versiones disponibles.
    '''
    def get(self):
        '''
        Retorna una json con la lista de versiones disponibles
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('type',type=str,location='args',required=True)
        args=parser.parse_args()
        s_type = args['type']
        #
        if s_type.upper() == 'DLG':
            l_versiones = list( DLG_CONF_TEMPLATE.keys())
            d_rsp = { 'versiones': l_versiones}
            return d_rsp,200

        if s_type.upper() == 'PLC':
            l_versiones = list( PLC_CONF_TEMPLATE.keys())
            d_rsp = { 'versiones': l_versiones}
            return d_rsp,200
        
        return {}, 204
    
class Config(Resource):

    def __convert_flatten__(self, d, parent_key ='', sep =':'):
        '''
        '''
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
 
            if isinstance(v, MutableMapping):
                items.extend(self.__convert_flatten__(v, new_key, sep = sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def __compare_dicts__(self, d_reference, d_other):
        '''
        Compara 2 diccionarios y devuelve 2 listas con las claves
        diferentes en uno y otro.
        '''
        set_reference = set( self.__convert_flatten__(d_reference).keys())
        set_other = set( self.__convert_flatten__(d_other).keys())
        k_de_mas = list(set_other - set_reference)
        k_de_menos = list(set_reference - set_other)   
        return k_de_mas, k_de_menos
    
    def get(self):
        '''
        Lee la configuracion de un equipo de la SQL
        En la BS almacenamos json.(strings)
        Retornamos un json.
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('unit',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        bdsql = BD_SQL_BASE()
        d_res =  bdsql.read_configuration(args['unit'])
        if not d_res.get('res',False):
            bdsql.close()
            return {'rsp':'ERROR', 'msg':'Error en pgsql'},500
        #
        rp = d_res.get('rp',None)
        if rp.rowcount == 0:
            app.logger.info( f'(110) ApiCONF_WARN001: No config rcd in SQL')
            bdsql.close()
            return {},204

        row = rp.fetchone()
        d_config = row[0]
        bdsql.close()
        return d_config, 200
        
    def post(self):
        '''
        Crea/actualiza la configuracion de una unidad.
        Recibimos un json que almacenamos.
        No lo chequeamos !!!
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('unit',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        d_config = request.get_json()
        # Lo debo re-serializar para que la BD no salte.
        # https://stackoverflow.com/questions/26745519/converting-dictionary-to-json
        #
        jd_config = json.dumps(d_config)
        bdsql = BD_SQL_BASE()
        d_res =  bdsql.insert_configuration(args['unit'], jd_config)
        if not d_res.get('res',False):
            bdsql.close()
            return {'rsp':'ERROR', 'msg':'Error en pgsql'},500
        # 
        return {'rsp':'OK'}, 200

class GetAllUnits(Config):

    def get(self):
        '''
        Genera un listado de todas las uniades configuradas.
        '''
        #
        bdsql = BD_SQL_BASE()
        d_res =  bdsql.read_allunits()
        if not d_res.get('res',False):
            bdsql.close()
            return {'rsp':'ERROR', 'msg':'Error en pgsql'},500
        #
        rp = d_res.get('rp',None)
        if rp.rowcount == 0:
            app.logger.info( f'(110) ApiCONF_WARN001: No config rcd in SQL')
            bdsql.close()
            return {},204

        l_unidades = []
        for row in rp.fetchall():
            l_unidades.append(row[0])

        l_unidades = sorted(l_unidades)
        nro_unidades = len(l_unidades)
        d_rsp = {'nro_unidades':nro_unidades, 'l_unidades':l_unidades}
        return d_rsp,200

class Uid2id(Resource):

    def get(self):
        '''
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('uid',type=str,location='args',required=True)
        args=parser.parse_args()
        uid = args['uid']
        #
        bdsql = BD_SQL_BASE()
        d_res =  bdsql.read_uid(uid)
        if not d_res.get('res',False):
            bdsql.close()
            return {'rsp':'ERROR', 'msg':'Error en pgsql'},500
        #
        rp = d_res.get('rp',None)
        if rp.rowcount == 0:
            app.logger.info( f'(112) ApiCONF_WARN001: No config rcd in SQL')
            bdsql.close()
            return {},204

        row = rp.fetchone()
        unit_id = row[0]
        bdsql.close()
        d_resp = {'uid': uid, 'id':unit_id }
        return d_resp,200
        
    def put(self):
        '''
        Crea/actualiza la configuracion de una unidad.
        Recibimos un json que almacenamos.
        No lo chequeamos !!!
        '''
        d_params = request.get_json()
        if 'uid' not in d_params:
            app.logger.info( f'(113) ApiCONF_ERR009: No UID in request_json_data')
            return {'Err':'No UID'}, 406
        #
        if 'id' not in d_params:
            app.logger.info( f'(114) ApiCONF_ERR010: No ID in request_json_data')
            return {'Err':'No ID'}, 406
        # 
        if d_params['id'] == 'DEFAULT':
            app.logger.info( f'(115) ApiCONF_ERR013: No ID no puede ser DEFAULT')
            return {'Err':'ID no puede ser DEFAULT'}, 406
        
        bdsql = BD_SQL_BASE()
        d_res =  bdsql.insert_uid( d_params['id'], d_params['uid'] )
        if not d_res.get('res',False):
            bdsql.close()
            return {'rsp':'ERROR', 'msg':'Error en pgsql'},500
        #
        return {'rsp':'OK'}, 200
    
class Help(Resource):

    def get(self):
        ''' Retorna la descripcion de los metodos disponibles
        '''
        d_options = {
            'GET /apiconf/versiones':'Retorna una lista con todas las versiones que se manejan',
            'GET /apiconf/template':'Retorna el template de la version indicada',
            'GET /apiconf/config':' Retorna la configuracion de la unidad solicitada',
            'POST /apiconf/config':'Crea/Actualiza la configuracion de la unidad indicada',
            'GET /apiconf/unidades':' Retorna una lista con todas las unidades configuradas',
            'POST /apiconf/commsidparams':'Actualiza la configuracion de comunicaciones de la unidad indicada',
        }
        return d_options, 200

class CommsIdParams(Resource):
            
    def post(self):
        '''
        Inserta la configuracion de los parametros de comunicaciones de una unidad.
        Recibimos un json que almacenamos.
        No lo chequeamos !!!
        {
            "UID": "xxxxxxxx",
            "IMEI": "xxxxxxxx",
            "ICCID": "xxxxxxxx",
        }
        '''
        #parser = reqparse.RequestParser()
        #parser.add_argument('unit',type=str,location='args',required=True)
        #args=parser.parse_args()
        #
        js_config = request.get_json()
        d_config = json.loads(js_config)
        #print(f'DEBUG d_config={d_config}')
        #print(f'DEBUG: d_config_type={type(d_config)}')

        # Lo debo re-serializar para que la BD no salte.
        # https://stackoverflow.com/questions/26745519/converting-dictionary-to-json
        #
        bdsql = BD_SQL_BASE()
        d_res =  bdsql.insert_comms_id_config(d_config)
        if not d_res.get('res',False):
            bdsql.close()
            return {'rsp':'ERROR', 'msg':'Error en pgsql'},500
         
        return {'rsp':'OK'}, 200

api.add_resource( Kill, '/apiconf/kill')
api.add_resource( Test, '/apiconf/test')
api.add_resource( Ping, '/apiconf/ping')
api.add_resource( Help, '/apiconf/help')
api.add_resource( GetVersiones, '/apiconf/versiones')
api.add_resource( GetTemplate, '/apiconf/template')
api.add_resource( GetAllUnits, '/apiconf/unidades')
api.add_resource( Config, '/apiconf/config')
api.add_resource( Uid2id, '/apiconf/uid2id')
api.add_resource( CommsIdParams, '/apiconf/commsidparams')

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

    app.logger.info( f'Starting APICONF: SQL_HOST={PGSQL_HOST}, SQL_PORT={PGSQL_PORT}' )

if __name__ == '__main__':
    PGSQL_HOST = '127.0.0.1'
    app.run(host='0.0.0.0', port=5200, debug=True)



