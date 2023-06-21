#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python
'''
Api de configuracion SQL de dataloggers y PLC para el servidor APISERVER

BASE DE DATOS:
psql>CREATE DATABASE bd_unidades;
psql>CREATE TABLE configuraciones ( pk SERIAL PRIMARY KEY, unit_id VARCHAR (20), uid VARCHAR (50), jconfig JSON);

pip install --upgrade wheel
apt-get install libpq-dev
pip install psycopg2

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
            self.engine = create_engine(url=self.url, echo=False, isolation_level="AUTOCOMMIT", poolclass=NullPool)
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
        #app.logger.info( f'(DEBUG) ApiCONF_INFO: Sql close and dispose R2. HOST:{PGSQL_HOST}:{PGSQL_PORT}')
        self.conn.invalidate()
        self.conn.close()     
        self.engine.dispose()

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
                s_version = list(DLG_CONF_TEMPLATE.keys())[-1]
        #
            if s_version not in list(DLG_CONF_TEMPLATE.keys()):
                return {},204
        #
            d_template = DLG_CONF_TEMPLATE[s_version]
            d_rsp = {'version': s_version, 'template': d_template}
            return d_rsp,200

        if s_type.upper() == 'PLC':
            if s_version.upper() == 'LATEST':
                s_version = list(PLC_CONF_TEMPLATE.keys())[-1]

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
        '''
        #
        sql = "SELECT unit_id FROM configuraciones"
        query = text(sql)
        if self.__bd_connect__():
            try:
                rp = self.conn.execute(query)
            except SQLAlchemyError as err:
                app.logger.info( f'(111) ApiCONF_ERR003: Pgsql execute error, HOST:{PGSQL_HOST}:{PGSQL_PORT}, Err:{err}')
                d_rsp = {'rsp':'ERROR', 'msg':f'ApiCONF_ERR003: Pgsql connection error, HOST:{PGSQL_HOST}:{PGSQL_PORT}' }
                self.response = d_rsp
                self.status_code = 500
                return self.response, self.status_code
            finally:
                self.conn.close()
        else:
            return self.response, self.status_code

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
        }
        return d_options, 200

api.add_resource( Ping, '/apiconf/ping')
api.add_resource( Help, '/apiconf/help')
api.add_resource( GetVersiones, '/apiconf/versiones')
api.add_resource( GetTemplate, '/apiconf/template')
api.add_resource( GetAllUnits, '/apiconf/unidades')
api.add_resource( Config, '/apiconf/config')
api.add_resource( Uid2id, '/apiconf/uid2id')

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

    app.logger.info( f'Starting APICONF: SQL_HOST={PGSQL_HOST}, SQL_PORT={PGSQL_PORT}' )

if __name__ == '__main__':
    PGSQL_HOST = '127.0.0.1'
    app.run(host='0.0.0.0', port=5200, debug=True)



