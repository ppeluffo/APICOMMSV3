#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python
'''
Implementacion de una API para leer datos de la base online SQL.
En esta base se almacenan los datos de todas las unidades.
Los clientes autorizados piden datos que se transmiten en chunks de hasta
N elementos.
Se hace una paginacion de los elementos enviados a c/cliente.
Cada peticion del cliente se le manda un nuevo chunk a partir del ultimo solicitado.

-----------------------------------------------------------------------------
R001 @ 2023-06-14 (commsv3_apidatos:1.1)
- Se manejan todos los parámetros por variables de entorno
- Se agrega un entrypoint 'ping' que permite ver si la api esta operativa
- Se agrega CRUD para usuarios

'''

import os
import json
import random, string
import datetime as dt
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool
from sqlalchemy import text
import logging
from flask import Flask, request, jsonify
from flask_restful import Resource, Api, reqparse


PGSQL_HOST = os.environ.get('PGSQL_HOST', 'pgsql')
PGSQL_PORT = os.environ.get('PGSQL_PORT','5432')
PGSQL_USER = os.environ.get('PGSQL_USER', 'admin')
PGSQL_PASSWD = os.environ.get('PGSQL_PASSWD', 'pexco599')
PGSQL_BD = os.environ.get('PGSQL_BD','bd_spcomms')

APIDATOS_HOST = os.environ.get('APIDATOS_HOST','apidatos')
APIDATOS_PORT = os.environ.get('APIDATOS_PORT','5300')

MAX_SELECT_CHUNK_SIZE = os.environ.get(' MAX_SELECT_CHUNK_SIZE', 100)

API_VERSION = 'R001 @ 2023-06-15'

app = Flask(__name__)
api = Api(app)

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
            app.logger.info( f'(200) ApiDATOS_ERR001: Pgsql engine error, HOST:{PGSQL_HOST}:{PGSQL_PORT}, Err:{err}')
            return False 
        # Connection
        try:
            self.conn = self.engine.connect()
            self.conn.autocommit = True
        except SQLAlchemyError as err:
            app.logger.info( f'(201) ApiDATOS_ERR002: Pgsql connection error, HOST:{PGSQL_HOST}:{PGSQL_PORT}, Err:{err}')
            return False
        #
        return True
        #

    def close(self):
        app.logger.info( f'(DEBUG) ApiDATOS_INFO: Sql close and dispose R2. HOST:{PGSQL_HOST}:{PGSQL_PORT}')
        self.conn.invalidate()
        self.conn.close()     
        self.engine.dispose()

    def exec_sql(self, sql):
        # Ejecuta la orden sql.
        # Retorna un resultProxy o None
        if not self.connect():
            app.logger.info( f'(202) ApiDATOS_ERR002: Pgsql connection error, HOST:{PGSQL_HOST}:{PGSQL_PORT}')
            return {'res':False }
        #
        try:
            query = text(sql)
        except Exception as err:
            app.logger.info( f'(203) ApiDATOS_ERR003: Sql query error, HOST:{PGSQL_HOST}:{PGSQL_PORT}, Err:{sql}')
            app.logger.info( f'(204) ApiDATOS_ERR004: Sql query exception, HOST:{PGSQL_HOST}:{PGSQL_PORT}, Err:{err}')
            return {'res':False }
        #
        try:
            #print(sql)
            rp = self.conn.execute(query)
        except Exception as err:
            app.logger.info( f'(205) ApiDATOS_ERR005: Sql exec error, HOST:{PGSQL_HOST}:{PGSQL_PORT}, Err:{err}')
            return {'res':False }
        #
        return {'res':True,'rp':rp }

    def insert_user(self, user_id):
        '''
        Inserta un nuevo usuario en la tabla usuarios
        Retorna True/False
        '''
        dnow = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql = f"INSERT INTO usuarios ( user_id, fecha_ultimo_acceso, data_ptr ) VALUES ('{user_id}', '{dnow}','0') ON CONFLICT DO NOTHING" 
        d_res = self.exec_sql(sql)
        if not d_res.get('res',False):
            app.logger.info( '(206) ApiDATOS_ERR006: insert_user FAIL')
        return d_res
    
    def read_user(self, user_id):
        '''
        Lee todos los datos del usuario
        '''
        sql = f"SELECT fecha_ultimo_acceso, data_ptr FROM usuarios WHERE user_id = '{user_id}'" 
        d_res = self.exec_sql(sql)
        if not d_res.get('res',False):
            app.logger.info( '(207) ApiDATOS_ERR007: select_user FAIL')
        return d_res
        #

    def delete_user(self, user_id):
        '''
        El rp.rowcount indica cuantas filas fueron afectadas
        '''
        sql = f"DELETE FROM usuarios WHERE user_id = '{user_id}'" 
        d_res = self.exec_sql(sql)
        if not d_res.get('res',False):
            app.logger.info( '(208) ApiDATOS_ERR008: delete_user FAIL')
        return d_res

    def read_data_chunk(self, data_ptr):
        '''
        Lee todos los datos de la tabla online a partir de la key data_ptr
        '''
        sql = f"SELECT * FROM online WHERE id > '{data_ptr}' ORDER by id LIMIT {MAX_SELECT_CHUNK_SIZE}" 
        d_res = self.exec_sql(sql)
        if not d_res.get('res',False):
            app.logger.info( '(209) ApiDATOS_ERR009: read data chunk FAIL')
        return d_res

    def update_user(self, user_id, pk):
        '''
        Actualiza al usuario con la ultima consulta de datos.
        '''
        dnow = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql = f"UPDATE usuarios SET data_ptr = '{pk}', fecha_ultimo_acceso = '{dnow}' WHERE user_id = '{user_id}'" 
        d_res = self.exec_sql(sql)
        if not d_res.get('res',False):
            app.logger.info( '(210) ApiDATOS_ERR010: update user FAIL')
        return d_res

class Ping(Resource):
    '''
    Prueba la conexion a la SQL
    '''
    def get(self):
        '''
        '''
        bdpgsl = BD_SQL_BASE()
        if bdpgsl.connect():
            print("Connected to PGSQL!")
            bdpgsl.close()
            return {'rsp':'OK','version':API_VERSION,'SQL_HOST':PGSQL_HOST, 'SQL_PORT':PGSQL_PORT },200
        #
        d_rsp = {'rsp':'ERROR', 'msg':f'ApiDATOS_ERR001: Pgsql connect error, HOST:{PGSQL_HOST}:{PGSQL_PORT}' }
        bdpgsl.close()
        return d_rsp, 500
             
class Usuarios(Resource):

    def post(self):
        '''
        Implementacion del CREATE USERS
        '''
        # Creamos un id de 20 caracteres aleatorios.
        random.seed(dt.datetime.now().timestamp())
        user_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))
        #
        # Creo una entrada en la BD
        bdsql = BD_SQL_BASE()
        d_res = bdsql.insert_user(user_id)
        if not d_res.get('res',False):
            bdsql.close()
            return {'rsp':'ERROR', 'msg':'Error en pgsql'},500
        #
        bdsql.close()
        return {'user_id':user_id},200
        
    def get(self):
        '''
        Retorna para un usuario dado los datos propios
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('user',type=str,location='args',required=True)
        args=parser.parse_args()
        bdsql = BD_SQL_BASE()
        d_res =  bdsql.read_user(args['user'])
        if not d_res.get('res',False):
            bdsql.close()
            return {'rsp':'ERROR', 'msg':'Error en pgsql'},500
        #
        rp = d_res.get('rp',None)
        if rp.rowcount == 0:
            bdsql.close()
            return {},204

        row = rp.fetchone()
        # La fecha es un datetime !!!
        fechaUltimoAcceso = row[0].strftime("%m/%d/%Y, %H:%M:%S")
        data_ptr = row[1]
        bdsql.close()
        return {'user':args['user'],'fechaUltimoAcceso':fechaUltimoAcceso,'data_ptr':data_ptr }, 200
    
    def delete(self):
        '''
        Borra el usuario de la BD
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('user',type=str,location='args',required=True)
        args=parser.parse_args()
        bdsql = BD_SQL_BASE()
        d_res =  bdsql.delete_user(args['user'])
        if not d_res.get('res',False):
            bdsql.close()
            return {'rsp':'ERROR', 'msg':'Error en pgsql'},500
        #
        rp = d_res.get('rp',None)
        if rp.rowcount == 0:
            bdsql.close()
            return {},204

        bdsql.close()
        return {'rsp':'OK'}, 200
    
class Datos(Resource):
    '''
    Pide datos.
    Se entrega un chunk de datos y se marca en la tabla de usuarios
    '''  
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('user',type=str,location='args',required=True)
        args=parser.parse_args()
        bdsql = BD_SQL_BASE()
        #
        # Verificamos que el usuario exista
        d_res =  bdsql.read_user(args['user'])
        # Error
        if not d_res.get('res',False):
            bdsql.close()
            return {'rsp':'ERROR','msg':'Error en pgsql'},500
        #
        rp = d_res.get('rp',None)
        # No existe usuario
        if rp.rowcount == 0:
            bdsql.close()
            return {},204
        #
        # Usuario aceptado: leo el ptr del ultimo dato enviado
        row = rp.fetchone()
        data_ptr = row[1]
        #
        # Leo un chunk de datos desde el ultimo enviado
        d_res = bdsql.read_data_chunk(data_ptr)
        if not d_res.get('res',False):
            bdsql.close()
            return {'rsp':'ERROR', 'msg':'Error en pgsql'},500
        #
        rp = d_res.get('rp',None)
        # No hat datos
        if rp.rowcount == 0:
            bdsql.close()
            return {},204
        #
        l_results = []
        rows = rp.fetchall()
        for row in rows:
            pk = row[0]
            fechadata = row[1].strftime("%m/%d/%Y, %H:%M:%S")
            fechasys = row[2].strftime("%m/%d/%Y, %H:%M:%S")
            unit_id = row[3]
            mag_name = row[4]
            mag_val = float(row[5])
            rcd = (fechadata, fechasys,unit_id,mag_name, mag_val)
            l_results.append(rcd)
        #
        # Actualizo el puntero del usuario
        bdsql.update_user(args['user'], pk)
        #
        bdsql.close()
        return {'l_datos':l_results }, 200

class Help(Resource):

    def get(self):
        ''' Retorna la descripcion de los metodos disponibles
        '''
        d_options = {
            'GET /apidatos/ping':'Prueba las respuesta y conexión a Pgsql',
            'POST /apidatos/usuarios':'Crea un nuevo usuario y retorna su id',
            'GET /apidatos/usuarios?user=USER':'Devuelve los datos del usuario',
            'DELETE /apidatos/usuarios?user=USER':'Borra el usuario',
            'GET /apidatos/datos?user=USER':'Pide un chunk de datos.',
        }
        return d_options, 200

api.add_resource( Ping, '/apidatos/ping')
api.add_resource( Help, '/apidatos/help')
api.add_resource( Usuarios, '/apidatos/usuarios')
api.add_resource( Datos, '/apidatos/datos')

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

    app.logger.info( f'Starting APIDATOS: SQL_HOST={PGSQL_HOST}, SQL_PORT={PGSQL_PORT}' )

if __name__ == '__main__':
    PGSQL_HOST = '127.0.0.1'
    MAX_CHUNK_SIZE = 10
    app.run(host='0.0.0.0', port=5300, debug=True)


