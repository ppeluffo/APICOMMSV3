#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python
'''

Testing c/gunicorn:
gunicorn --bind=0.0.0.0:8000 --log-level=debug wsgi:app

-----------------------------------------------------------------------------
R001 @ 2023-06-14 (commsv3_apiredis:1.1)
- Se modifican las respuestas de modo que se respondan con objetos json y
  no strings.
- Se normalizan los mensajes de error.
- Se agregan try a los manejos con pickle
- Se normalizan las respuestas.


Version 1.1 @ 2023-05-23:
-------------------------
Cambiamos para guardar todo en la redis en formato pickle.
Todo lo que recibimos e enviamos por la API debe ser un json.


Version 1.0
-----------
Primera version de una API para interactuar con la BD Redis
Todas las respuestas son json.
1- Probamos desde postman
2- Instalamos nginx, gurnicon y probamos con postman
3- Probamos desde qtconsole vs nginx

Recursos:
- Configuracion / Ordenes / Datalines / Help.

Metodos | URL | Acciones

GET     /apiredis/configuracion?unit=<id>       Retorna la configuracion de la unidad
DELETE  /apiredis/configuracion?unit=<id>       Borra el registro de configuracion de la unidad
PUT     /apiredis/configuracion?unit=<id>       Actualiza (override) la configuracion. (json PUT Body)
GET     /apiredis/configuracion/debugid?        Retorna el id que se usa para debug

GET     /apiredis/ordenes?unit=<id>             Lee las ordenes para la unidad
PUT     /apiredis/ordenes?unit=<id>             Actualiza (override) el registro de ordenes. (json PUT Body)

GET     /apiredis/ordenes/atvise?unit=<id>      
PUT     /apiredis/ordenesatvise?unit=<id>      

GET     /apiredis/dataline?unit=<id>            Recupera una linea de datos
PUT     /apiredis/dataline?unit=<id>            Actualiza una linea de datos. (json PUT Body)

GET     /apiredis/queuelength?qname=<qn>                Devuelve el la cantidad de elementos de la cola.
GET     /apiredis/queueitems?qname=<qn>&<count=nn>      Devuelve count elementos de la cola. (json Body)

Respuestas:
Los datos se devuelven en un json.
OK 200
Si no nos conectamos al servidor: 500
Si no hay registro:(NO CONTENT):  204

Notas de desarrollo:
1) en parser.add_argument('unit',type=str,location='args',required=True) usar location y type para que no hayan conflictos
   con otros parametros.
2) return jsonify({}),204 da error porque no banca el err_code.
   Flask 1.1 automaticamente jasonifica los diccionarios en las respuestas por lo que no se necesita.

ERRORES:
ApiREDIS_ERR001: Redis not connected
ERROR R002: No UID in request_json_data
ERROR R003: No UNIT ID in request_json_data
ERROR R004: No ordenes in request_json_data
ERROR_R005: No ordenes atvise in request_json_data
ERROR R006: No dataline rcd
ERROR R007: No qlength rcd
ERROR R008: No l_pkdatos rcd

WARNINGS:
WARN_R001: No configuration rcd
WARN_R002: No debug_unit rcd
WARN_R003: No uid2dlgi rcd
WARN_R004: No ordenes rcd
WARN_R005: No pkordenes rcd
WARN R006: No dataline rcd
'''

import os
import datetime as dt
import redis
import json
import pickle
import logging
from flask import Flask, request, jsonify
from flask_restful import Resource, Api, reqparse

app = Flask(__name__)
api = Api(app)

BDREDIS_HOST = os.environ.get('BDREDIS_HOST','redis')
BDREDIS_PORT = os.environ.get('BDREDIS_PORT','6379')
BDREDIS_DB = os.environ.get('BDREDIS_DB','0')

API_VERSION = 'R001 @ 2023-06-14'

class Ping(Resource):
    '''
    Devuelve el estado de la conexion a la BD Redis.
    '''
    def get(self):

        rh = redis.Redis( BDREDIS_HOST, BDREDIS_PORT, BDREDIS_DB, socket_connect_timeout=1)
        try:
            rh.ping()
            d_rsp = {'rsp':'OK','version':API_VERSION,'REDIS_HOST':BDREDIS_HOST,'REDIS_PORT':BDREDIS_PORT }
            return d_rsp,200
        except redis.ConnectionError:
            app.logger.info( f'(001) ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}')
            d_rsp = {'rsp':'ERROR', 'msg':f'ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}' }
            return d_rsp, 500

class DeleteRcd(Resource):
    
    def delete(self):
        ''' Borra el registro de la unidad
            Invocacion: /apiredis/delete?unit=ID

            Testing:
            req=requests.delete('http://127.0.0.1:5100/apiredis/delete', params={'unit':'PABLO'})
            jd_conf=req.json()
            d_conf=json.loads(jd_conf)
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('unit',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        rh = redis.Redis( BDREDIS_HOST, BDREDIS_PORT, BDREDIS_DB)
        try:
            _=rh.delete(args['unit'])
        except redis.ConnectionError:
            app.logger.info( f'(002) ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}')
            d_rsp = {'rsp':'ERROR','msg':f'ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}' }
            return d_rsp, 500
        #
        return {'rsp':'OK'}, 200

class Config(Resource):

    def get(self):
        ''' Devuelve la configuracion del dispositivo en un json.
            Invocacion: /apiredis/config?unit=ID
            La redis retorna un pickle.

            Testing:
            req=requests.get('http://127.0.0.1:5100/apiredis/config', params={'unit':'PABLO'})
            jd_conf=req.json()
            d_conf=json.loads(jd_conf)

        '''
        parser = reqparse.RequestParser()
        parser.add_argument('unit',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        rh = redis.Redis( BDREDIS_HOST, BDREDIS_PORT, BDREDIS_DB)
        try:
            pk_config = rh.hget( args['unit'], 'PKCONFIG')
        except redis.ConnectionError:
            app.logger.info( f'(003) ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}')
            d_rsp = {'rsp':'ERROR', 'msg':f'ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}' }
            return d_rsp, 500
        #
        if pk_config is None:
            app.logger.info( f'(004) ApiREDIS_WARN001: No configuration rcd')
            return {},204   # NO CONTENT
        #
        # En la redis la configuracion es un dict serializado en bytestring
        try:
            d_config = pickle.loads(pk_config)
        except Exception:
            d_rsp = {'rsp':'ERROR', 'msg': 'pickle loads error'}
            return d_rsp, 409
        #
        return d_config,200
   
    def put(self):
        ''' Actualiza(override) la configuracion para la unidad
            NO CHEQUEA EL FORMATO
            Invocacion: /apiredis/config?unit=ID
            Como es PUT, la configuracion la mandamos en un json { dict_config }
            Se testea con:
            req=requests.put('http://127.0.0.1:5100/apiredis/config', params={'unit':'DLGTEST'}, json=jd_conf)

            En la REDIS se guarda un pickle !!!.
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('unit',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        d_params = request.get_json()
        if not isinstance(d_params, dict):
            d_rsp = {'rsp':'ERROR', 'msg':'No es una instancia de dict.'}
            return d_rsp, 406
        
        try:
            pk_config = pickle.dumps(d_params)
        except Exception:
            d_rsp = {'rsp':'ERROR', 'msg':'pickle dumps error'}
            return d_rsp, 409
        #
        rh = redis.Redis( BDREDIS_HOST, BDREDIS_PORT, BDREDIS_DB)
        try:
            _ = rh.hset( args['unit'],'PKCONFIG', pk_config)
        except redis.ConnectionError:
            app.logger.info( f'(005) ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}')
            d_rsp = {'rsp':'ERROR', 'msg':f'ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}' }
            return d_rsp, 500
        #
        return {'rsp':'OK'}, 200

class DebugId(Resource):

    def get(self):
        ''' Retorna el id de la unidad que debe hacerse el debug
            Invocacion: /apiredis/configuracion/debugid?

            Testing:
            req=requests.get('http://127.0.0.1:5100/apiredis/debugid')
            json.loads(req.json())
            {'debugId': 'PLCTEST'}

        '''
        rh = redis.Redis( BDREDIS_HOST, BDREDIS_PORT, BDREDIS_DB)
        try:
            debug_id = rh.hget('SPCOMMS', 'DEBUG_ID')
        except redis.ConnectionError:
            app.logger.info( f'(006) ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}')
            d_rsp = {'rsp':'ERROR', 'msg':f'ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}' }
            return d_rsp, 500
        #
        if debug_id is None:
            app.logger.info( f'(007) ApiREDIS_WARN002: No debug_unit rcd')
            return {},204   # NO CONTENT
        #
        d_resp = {'debugid': debug_id.decode() }
        return d_resp, 200
    
    def put(self):
        ''' 
        Actualiza el DEBUG_ID
        Como es PUT, la orden la mandamos en un json {'ordenes':orden }

        Testing:
        d={'debugid': 'PLCTEST'}
        jd=json.dumps(d)
        req=requests.put('http://127.0.0.1:5100/apiredis/ordenes', json=jd)
        json.loads(req.json())
        '''
        #
        d_params = request.get_json()
        if not isinstance(d_params, dict):
            d_rsp = {'rsp':'ERROR', 'msg':'No es una instancia de dict.'}
            return d_rsp, 406
        #
        if 'debugid' not in d_params:
            app.logger.info('(008) ApiREDIS_ERR002: No debugid in request_json_data')
            d_rsp = {'rsp':'ERROR', 'msg':'ApiREDIS_ERR002: No debugid in request_json_data'}
            return d_rsp, 406
        #
        debugid = d_params.get('debugid','UNKNOWN')
        rh = redis.Redis( BDREDIS_HOST, BDREDIS_PORT, BDREDIS_DB)
        try:
            _ = rh.hset('SPCOMMS', 'DEBUG_ID', debugid )
        except redis.ConnectionError:
            app.logger.info( f'(009) ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}')
            d_rsp = {'rsp':'ERROR', 'msg':f'ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}' }
            return d_rsp, 500
        #
        return {'rsp':'OK'},200
    
class Uid2id(Resource):
        
    def get(self):
        ''' Devuelve el par UID/ID en un json
            Invocacion: /apiredis/uid2id?unit=DLGID

            Testing:
            req=requests.get('http://127.0.0.1:5100/apiredis/uid2id',params={'uid':'UID'})
            json.loads(req.json())
            {'id':'DLGTEST','uid':'01234567'}

        '''
        parser = reqparse.RequestParser()
        parser.add_argument('uid',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        rh = redis.Redis( BDREDIS_HOST, BDREDIS_PORT, BDREDIS_DB)
        try:
            unit_id = rh.hget( args['uid'], 'UID2DLGID' )
        except redis.ConnectionError:
            app.logger.info( f'REDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}')
            return {'Err':f'No se puede conectar a REDIS HOST:{BDREDIS_HOST}'}, 500
        #
        if unit_id is None:
            app.logger.info( f'REDIS_WARN003: No uid2dlgid rcd, code 204')
            return {},204   # NO CONTENT
        #
        d_resp = {'uid': args['uid'], 'id':unit_id }
        jd_resp = json.dumps(d_resp)
        return jd_resp,200

    def put(self):
        ''' Actualiza(override) las tupla UID/DLGID
            Invocacion: apiredis/uid2id?
            Como es PUT, la orden la mandamos en un json {'uid':UID, 'unit': ID }

            Testing:
            d={'uid':'012345678', 'unit':'DLGTEST'}
            jd=json.dumps(d)
            req=requests.put('http://127.0.0.1:5100/apiredis/uid2id?, json=jd)
            json.loads(req.json())

        '''
        parser = reqparse.RequestParser()
        parser.add_argument('unit',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        jd_params = request.get_json()
        d_params = json.loads(jd_params)
        if 'uid' not in d_params:
            app.logger.info('REDIS_ERR002: No UID in request_json_data')
            return {'Err':'No UID'}, 406
        #
        if 'unit' not in d_params:
            app.logger.info('REDIS_ERR003: No ID in request_json_data')
            return {'Err':'No ID'}, 406
        #
        #app.logger.debug(f'Ordenes/Put DBUG: ordenes={ordenes}')
        rh = redis.Redis( BDREDIS_HOST, BDREDIS_PORT, BDREDIS_DB)
        try:
            _ = rh.hset( 'UID2DLGID', args['uid'], args['unit'] )
        except redis.ConnectionError:
            app.logger.info( f'REDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}')
            return {'Err':f'No se puede conectar a REDIS HOST:{BDREDIS_HOST}'}, 500
        #
        d_resp = {'uid':args['uid'], 'unit':args['unit']}
        jd_resp = json.dumps(d_resp)
        return jd_resp,200
    
class Ordenes(Resource):

    def get(self):
        ''' Devuelve las ordenes para la unidad en un json
            Invocacion: /apiredis/ordenes?unit=DLGID

            Testing:
            req=requests.get('http://127.0.0.1:5100/apiredis/ordenes',params={'unit':'DLGTEST'})
            json.loads(req.json())
            {'ordenes': 'RESET;PRENDER_BOMBA'}

        '''
        parser = reqparse.RequestParser()
        parser.add_argument('unit',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        rh = redis.Redis( BDREDIS_HOST, BDREDIS_PORT, BDREDIS_DB)
        try:
            pk_ordenes = rh.hget( args['unit'], 'PKORDENES' )
        except redis.ConnectionError:
            app.logger.info( f'(010) ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}')
            d_rsp = {'rsp':'ERROR', 'msg':f'ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}' }
            jd_rsp = json.dumps(d_rsp)
            return jd_rsp, 500
        #
        if pk_ordenes is None:
            #app.logger.info( f'REDIS_WARN004: No ordenes rcd, code 204')
            return {},204   # NO CONTENT
        #
        try:
            ordenes = pickle.loads(pk_ordenes)
        except Exception:
            d_rsp = {'rsp':'ERROR', 'msg': 'pickle loads error'}
            return d_rsp, 409
        
        d_resp = {'ordenes': ordenes }
        #jd_resp = json.dumps(d_resp)
        return d_resp,200

    def put(self):
        ''' Actualiza(override) las ordenes para la unidad
            NO CHEQUEA EL FORMATO DE LA LINEA DE ORDENES
            Invocacion: /apiredis/ordenes?unit=DLGID
            Como es PUT, la orden la mandamos en un json {'ordenes':orden }

            Testing:
            d={'ordenes':'Reset;Apagar;Prender'}
            jd=json.dumps(d)
            req=requests.put('http://127.0.0.1:5100/apiredis/ordenes', params={'unit':'DLGTEST'}, json=jd)
            json.loads(req.json())

        '''
        parser = reqparse.RequestParser()
        parser.add_argument('unit',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        d_params = request.get_json()
        if not isinstance(d_params, dict):
            d_rsp = {'rsp':'ERROR', 'msg': 'No es una instancia de dict.'}
            return d_rsp, 406
        #
        if 'ordenes' not in d_params:
            app.logger.info('(011) ApiREDIS_ERR003: No ordenes in request_json_data')
            d_rsp = {'rsp':'ERROR', 'msg':'ApiREDIS_ERR003: No ordenes in request_json_data'}
            return d_rsp, 406
        
        ordenes = d_params.get('ordenes','')
        rh = redis.Redis( BDREDIS_HOST, BDREDIS_PORT, BDREDIS_DB)
        try:
            pk_ordenes = pickle.dumps(ordenes)
        except Exception:
            d_rsp = {'rsp':'ERROR', 'msg':'pickle dumps error'}
            return d_rsp, 409
        #
        try:
            _ = rh.hset( args['unit'], 'PKORDENES', pk_ordenes )
        except redis.ConnectionError:
            app.logger.info( f'(012) ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}')
            d_rsp = {'rsp':'ERROR', 'msg':f'ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}' }
            return d_rsp, 500
        #
        return {'rsp':'OK'},200

    def delete(self):
        ''' Borra las ordenes para la unidad
            Invocacion: /apiredis/ordenes?unit=DLGID

            Testing:
            d={'ordenes':'Reset;Apagar;Prender'}
            jd=json.dumps(d)
            req=requests.del('http://127.0.0.1:5100/apiredis/ordenes', params={'unit':'DLGTEST'})
            json.loads(req.json())

        '''
        parser = reqparse.RequestParser()
        parser.add_argument('unit',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        #app.logger.debug(f'Ordenes/Put DBUG: ordenes={ordenes}')
        rh = redis.Redis( BDREDIS_HOST, BDREDIS_PORT, BDREDIS_DB)
        try:
            _ = rh.hdel( args['unit'], 'PKORDENES' )
        except redis.ConnectionError:
            app.logger.info( f'(013) ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}')
            d_rsp = {'rsp':'ERROR', 'msg':f'ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}' }
            return d_rsp, 500
        #
        return {'rsp':'OK'},200
    
class OrdenesAtvise(Resource):

    def get(self):
        ''' 
        Retorna un diccionario con la ultima linea de ordenes para atvise

        Testing:
        req=requests.get('http://127.0.0.1:5100/apiredis/ordenesatvise',params={'unit':'PLCTEST'})
        json.loads(req.json())
        {'ordenes_atvise': {'UPA1_ORDER_1': 101, 'UPA1_CONSIGNA_6': 102, 'ESP_ORDER_8': 103}}
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('unit',type=str,location='args',required=True)
        args=parser.parse_args()
    
        rh = redis.Redis( BDREDIS_HOST, BDREDIS_PORT, BDREDIS_DB)
        try:
            pk_atvise = rh.hget( args['unit'],'PKATVISE')
        except redis.ConnectionError:
            app.logger.info( f'(014) ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}')
            d_rsp = {'rsp':'ERROR', 'msg':f'ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}' }
            return d_rsp, 500
        #
        if pk_atvise is None:
            #app.logger.info( f'REDIS_WARN005: No pkordenes rcd, code 204')
            return {},204   # NO CONTENT
        #
        try:
            ordenes_atvise = pickle.loads(pk_atvise)
        except Exception:
            d_rsp = {'rsp':'ERROR', 'msg':'pickle loads error'}
            return d_rsp, 409
        #
        d_resp = {'ordenes_atvise': ordenes_atvise }
        return d_resp,200

    def put(self):
        ''' Actualiza(override) la configuracion de ordenes de atvise para la unidad
            NO CHEQUEA EL FORMATO
            Como es PUT, la configuracion la mandamos en un json { ordenes_atvise }

            Testing:
            jat=json.dumps({'ordenes_atvise':{"UPA1_ORDER_1": 101, "UPA1_CONSIGNA_6": 102, "ESP_ORDER_8": 103}})
            req=requests.put('http://127.0.0.1:5100/apiredis/ordenesatvise', params={'unit':'PLCTEST'}, json=jat)

        '''
        parser = reqparse.RequestParser()
        parser.add_argument('unit',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        d_params = request.get_json()
        if not isinstance(d_params, dict):
            d_rsp = {'rsp':'ERROR', 'msg':'No es una instancia de dict.'}
            return d_rsp, 406

        if 'ordenes_atvise' not in d_params:
            app.logger.info('(015) ApiREDIS_ERR004: No ordenes atvise in request_json_data')
            return {'rsp':'ERROR','msg':'ApiREDIS_ERR004: No ordenes atvise in request_json_data'}, 406
        #
        ordenes_atvise = d_params.get('ordenes_atvise','')
        rh = redis.Redis( BDREDIS_HOST, BDREDIS_PORT, BDREDIS_DB)
        try:
            pk_ordenes_atvise = pickle.dumps(ordenes_atvise)
        except Exception:
            d_rsp = {'rsp':'ERROR', 'msg':'pickle dumps error'}
            return d_rsp, 409
        #
        try: 
            _ = rh.hset( args['unit'],'PKATVISE', pk_ordenes_atvise)
        except redis.ConnectionError:
            app.logger.info( f'(016) ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}')
            d_rsp = {'rsp':'ERROR', 'msg':f'ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}' }
            return d_rsp, 500
        #
        return {'rsp':'OK'},200

    def delete(self):
        ''' Delete ordenes de atvise para la unidad
            NO CHEQUEA EL FORMATO

            Testing:
            req=requests.del('http://127.0.0.1:5100/apiredis/ordenesatvise', params={'unit':'PLCTEST'})

        '''
        parser = reqparse.RequestParser()
        parser.add_argument('unit',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        rh = redis.Redis( BDREDIS_HOST, BDREDIS_PORT, BDREDIS_DB)
        try:
            _ = rh.hdel( args['unit'],'PKATVISE')
        except redis.ConnectionError:
            app.logger.info( f'(017) ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}')
            d_rsp = {'rsp':'ERROR', 'msg':f'ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}' }
            return d_rsp, 500
        #
        return {'rsp':'OK'},200
    
class DataLine(Resource):

    # Retorna un diccionario con la ultima linea
    def get(self):
        ''' 
        Leemos la ultima linea que envio el datalogger.

        Testing:
        req=requests.get('http://127.0.0.1:5100/apiredis/dataline',params={'unit':'PABLO'})
        json.loads(req.json())
        {'DATE': '230519','TIME': '144412','HTQ': '-2.50','q0': '0.000','AI0': 'nan','QS': '0.000','bt': '12.480'}
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('unit',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        rh = redis.Redis( BDREDIS_HOST, BDREDIS_PORT, BDREDIS_DB)
        try:
            pk_dline = rh.hget( args['unit'], 'PKLINE')
        except redis.ConnectionError:
            app.logger.info( f'(018) ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}')
            d_rsp = {'rsp':'ERROR', 'msg':f'ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}' }
            return d_rsp, 500
        #
        if pk_dline is None:
            #app.logger.info( f'REDIS_WARN006: No dataline rcd, code 204')
            return {},204   # NO CONTENT
        #
        # En la redis la configuracion es un dict serializado.        
        try:
            d_data = pickle.loads(pk_dline)
        except Exception:
            d_rsp = {'rsp':'Error', 'msg': f'pickle loads error'}
            return d_rsp, 409
        #
        return d_data,200

    def put(self):
        ''' Actualiza(override) la ultima linea eviada por la unidad.
            NO CHEQUEA EL FORMATO
            Como es PUT, la configuracion la mandamos en un json { dict_line }
            Encola la linea en RXDATA_QUEUE para su posterior procesamiento

            Testing:
            d_data = {'DATE': '230519','TIME': '144412','HTQ': '-2.50', 'q0': '0.000','AI0': 'nan','QS': '0.000','bt': '12.480'}
            j_data = json.dumps(data)
            req=requests.put('http://127.0.0.1:5100/apiredis/dataline', params={'unit':'DLGTEST','type':'PLCR3'}, json=j_data)
            json.loads(req.json())

        '''
        parser = reqparse.RequestParser()
        parser.add_argument('unit',type=str,location='args',required=True)
        parser.add_argument('type',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        # get_json() convierte el objeto JSON a un python dict: lo serializo pickle
        d_params = request.get_json()
        if not isinstance(d_params, dict):
            d_rsp = {'rsp':'ERROR', 'msg':'No es una instancia de dict.'}
            return d_rsp, 406  
        #
        rh = redis.Redis( BDREDIS_HOST, BDREDIS_PORT, BDREDIS_DB)
        try:
            # Actualizamos el registro PKLINE
            pk_line = pickle.dumps(d_params) # Es un bytearray
            _ = rh.hset( args['unit'],'PKLINE', pk_line )
        except redis.ConnectionError:
            app.logger.info( f'(019) ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}')
            d_rsp = {'rsp':'ERROR', 'msg':f'ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}' }
            return d_rsp, 500
        #
        # Actualizamos la tabla con los timestamps en cada linea nueva que insertamos.
        timestamp = dt.datetime.now()
        ptimestamp = pickle.dumps(timestamp)
        _ = rh.hset('TIMESTAMP', args['unit'], ptimestamp )
        #
        # Encolamos en RXDATA_QUEUE
        d_persistent = {'TYPE':args['type'], 'ID':args['unit'], 'D_LINE':d_params}
        try:
            pk_d_persistent = pickle.dumps(d_persistent)
        except Exception:
            d_rsp = {'rsp':'ERROR', 'msg':'pickle dumps error'}
            return d_rsp, 409
        #
        try:
            _ = rh.rpush( 'RXDATA_QUEUE', pk_d_persistent)
        except redis.ConnectionError:
            app.logger.info( f'(020) ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}')
            d_rsp = {'rsp':'ERROR', 'msg':f'ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}' }
            return d_rsp, 500
        #
        return {'rsp':'OK'},200
    
class QueueLength(Resource):
    
    def get(self):
        ''' 
        Retorna el largo de la cola pasasa como parametro

        Testing:
        req=requests.get('http://127.0.0.1:5100/apiredis/queuelength',params={'qname':'RXDATA_QUEUE'})
        json.loads(req.json())
        {'qname': 'RXDATA_QUEUE', 'length': 595}
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('qname',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        rh = redis.Redis( BDREDIS_HOST, BDREDIS_PORT, BDREDIS_DB)
        try:
            qlength = rh.llen(args['qname'])
        except redis.ConnectionError:
            app.logger.info( f'(021) ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}')
            d_rsp = {'rsp':'ERROR', 'msg':f'ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}' }
            return d_rsp, 500
        #
        if qlength is None:
            app.logger.info( f'(022) ApiREDIS_ERR006: No qlength rcd')
            return {},204   # NO CONTENT
        #
        d_resp =  {'qname': args['qname'], 'length': qlength}
        return d_resp,200
    
class QueueItems(Resource):
    
    def get(self):
        ''' 
        Retorna los elementos de una cola

        Testing:
        req=requests.get('http://127.0.0.1:5100/apiredis/queueitems',params={'qname':'RXDATA_QUEUE','count':5})
        l_datos = json.loads(req.json())
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('qname',type=str,location='args',required=True)
        parser.add_argument('count',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        rh = redis.Redis( BDREDIS_HOST, BDREDIS_PORT, BDREDIS_DB)
        try:
            l_pkdatos = []
            l_pkdatos = rh.lpop(args['qname'], args['count'])
        except redis.ConnectionError:
            app.logger.info( f'(023) ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}')
            d_rsp = {'rsp':'ERROR', 'msg':f'ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}' }
            #jd_rsp = json.dumps(d_rsp)
            return d_rsp, 500
        #
        if l_pkdatos is None:
            app.logger.info( f'(024) ApiREDIS_ERR005: No l_pkdatos rcd')
            return {},204   # NO CONTENT
        #
        # Des-serializo los elementos de la lista.
        l_datos = []
        for i in l_pkdatos:
            try:
                l_datos.append( pickle.loads(i))
            except Exception:
                d_rsp = {'rsp':'ERROR', 'msg':'pickle loads error'}
                return d_rsp, 409
        #
        d_rsp = { 'ldatos':l_datos}
        return d_rsp, 200
    
class Stats(Resource):

    def get(self):
        rh = redis.Redis( BDREDIS_HOST, BDREDIS_PORT, BDREDIS_DB)
        try:
            d_res = rh.hgetall( 'TIMESTAMP' )
        except redis.ConnectionError:
            app.logger.info( f'(025) ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}')
            d_rsp = {'rsp':'ERROR', 'msg':f'ApiREDIS_ERR001: Redis not connected, HOST:{BDREDIS_HOST}:{BDREDIS_PORT}' }
            #jd_rsp = json.dumps(d_rsp)
            return d_rsp, 500
        #
        if d_res is None:
            app.logger.info( f'(026) ApiREDIS_WARN003: No stats rcd')
            return {},204   # NO CONTENT
        #
        d_timestamps = {}
        for unitid in d_res:
            pk_ts = d_res[unitid]
            try:
                ts = pickle.loads(pk_ts)
            except Exception:
                d_rsp = {'rsp':'ERROR', 'msg': 'pickle loads error'}
                return d_rsp, 409
            
            if isinstance(unitid,bytes):
                unitid=unitid.decode()
            d_timestamps[unitid]= ts.strftime('%y-%m-%d %H:%M:%S')
            
        return d_timestamps,200

class Help(Resource):

    def get(self):
        ''' Retorna la descripcion de los metodos disponibles
        '''
        d_options = {
            'GET /apiredis/ping': 'Indica el estado de la api.',
            'DELETE /apiredis/delete?unit=DLGID':'Borra la configuracion de la unit',
            'GET /apiredis/debugid': 'Retorna el unitID usado para debug',
            'PUT /apiredis/debugid': 'Setea el unitID usado para debug',
            'GET /apiredis/config?unit=DLGID':'Retorna la configuracion de la unit',
            'PUT /apiredis/config?unit=DLGID': 'Actualiza la configuracion de la unit',
            'GET /apiredis/uid2id?uid=<uid>': 'Retorna el DLGID asociado al UID',
            'PUT /apiredis/uid2id?dlgid=<dlgid>&uid=<uid>': 'Actualiza el par ( DLGID, UID )',
            'GET /apiredis/ordenes?unit=DLGID': 'Retorna la linea de ordenes para unit',
            'PUT /apiredis/ordenes?unit=DLGID': 'Actualiza(override) la linea de ordenes (json PUT Body) para unit',
            'GET /apiredis/ordenesatvise?unit=DLGID': 'Retorna la linea de ordenes ATVISE para unit',
            'PUT /apiredis/ordenesatvise?unit=DLGID': 'Actualiza(override) la linea de ordenes ATVISE (json PUT Body) para unit',
            'GET /apiredis/dataline?unit=DLGID': 'Retorna diccionario con datos de ultima linea recibida',
            'PUT /apiredis/dataline?unit=DLGID': 'Actualiza los datos de ultima linea recibida (json PUT Body) y el timestamp',
            'GET /apiredis/queuelength?qname=<qn>': 'Devuelve el la cantidad de elementos de la cola',
            'GET /apiredis/queueitems?qname=<qn>&<count=nn>':'Devuelve count elementos de la cola',
            'GET /apiredis/stats':'Devuelve todos los elementos en la lista TIMESTAMP',
        }
        return d_options, 200

class Test(Resource):

    def get(self):
        d_rsp = {'KIYU001': [('HTQ1', 'ALTURA_TANQUE_KIYU_1'), ('HTQ2', 'ALTURA_TANQUE_KIYU_2')],
                 'SJOSE001': [('PA', 'PRESION_ALTA_SJ1'), ('PB', 'PRESION_BAJA_SQ1')],
                 'VALOR1':1.23,
                 'VALOR2':-34.5}
        jd_rsp = json.dumps(d_rsp)
        return d_rsp, 200
    
    def put(self):
        d_params = request.get_json()
        print(f'DEBUG:{d_params}')
        td = type(d_params)
        print(f'DEBUG_TYPE:{td}')
        return {'Rsp':'OK', 'type':td},200


api.add_resource( Help, '/apiredis/help')
api.add_resource( Ping, '/apiredis/ping')
api.add_resource( DebugId, '/apiredis/debugid')
api.add_resource( DeleteRcd, '/apiredis/delete')
api.add_resource( Config, '/apiredis/config')
api.add_resource( Uid2id, '/apiredis/uid2id')
api.add_resource( Ordenes, '/apiredis/ordenes')
api.add_resource( OrdenesAtvise, '/apiredis/ordenesatvise')
api.add_resource( DataLine, '/apiredis/dataline')
api.add_resource( QueueLength, '/apiredis/queuelength')
api.add_resource( QueueItems, '/apiredis/queueitems')
api.add_resource( Stats, '/apiredis/stats')
api.add_resource( Test, '/apiredis/test')

# Lineas para que cuando corre desde gunicorn utilize el log handle de este
# https://trstringer.com/logging-flask-gunicorn-the-manageable-way/

if __name__ != '__main__':
    # SOLO PARA TESTING !!!
    # BDREDIS_HOST = '127.0.0.1'
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

    app.logger.info( f'Starting APIREDIS: REDIS_HOST={BDREDIS_HOST}, REDIS_PORT={BDREDIS_PORT}' )


# Lineas para cuando corre en modo independiente
if __name__ == '__main__':
    BDREDIS_HOST = '127.0.0.1'
    BDREDIS_PORT = 6379
    app.run(host='0.0.0.0', port=5100, debug=True)

