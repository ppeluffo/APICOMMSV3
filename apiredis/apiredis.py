#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python
'''

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
3) Revisar condiciones de ERROR en metodos con parametros faltantes (PUT)

ERRORES:

ERROR R001: Redis not connected
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

BDREDIS_HOST = 'redis'
BDREDIS_PORT = '6379'
BDREDIS_DB = '0'

#BDREDIS_HOST = os.environ.get('BDREDIS_HOST','127.0.0.1')
#BDREDIS_PORT = os.environ.get('BDREDIS_PORT','6379')
#BDREDIS_DB = os.environ.get('BDREDIS_DB','0')

#APIREDIS_HOST = os.environ.get('APIREDIS_HOST','127.0.0.1')
#APIREDIS_PORT = os.environ.get('APIREDIS_PORT','5100')

#print(f'DB REDIS: HOST={BDREDIS_HOST},PORT={BDREDIS_PORT},ID={BDREDIS_DB} ')

'''
Pendiente:

GET     /apiredis/configuracion/dlgidfromuid?uid=<uid>  Retorna el DLGID asociado al UID
PUT     /apiredis/configuracion/dlgidfromuid?dlgid=<dlgid>&uid=<uid>    Actualiza el par ( DLGID, UID )

'READ_DLGID_FROM_UID'
'SAVE_DLGID_UID'
'''

class Ping(Resource):
    '''
    Devuelve el estado de la conexion a la BD Redis.
    '''
    def get(self):

        rh = redis.Redis( BDREDIS_HOST, BDREDIS_PORT, BDREDIS_DB, socket_connect_timeout=1)
        try:
            rh.ping()
            return {'rsp':'OK', 'REDIS_HOST':BDREDIS_HOST, 'REDIS_PORT':BDREDIS_PORT },200
        except redis.ConnectionError:
            app.logger.info( f'ERROR R001: Redis not connected, HOST:{BDREDIS_HOST}')
            return {'rsp':'ERROR', 'REDIS_HOST':BDREDIS_HOST, 'REDIS_PORT':BDREDIS_PORT },503

class DeleteRcd(Resource):
    
    def delete(self):
        ''' Borra el registro de la unidad
            Invocacion: /apiredis/delete?unit=DLGID

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
            app.logger.info( f'ERROR R001: Redis not connected, HOST:{BDREDIS_HOST}')
            return {'Err':f'No se puede conectar a REDIS HOST:{BDREDIS_HOST}'}, 500
        #
        return {'unit':args['unit'], 'Rsp':'Deleted'}, 200

class Configuracion(Resource):

    def get(self):
        ''' Devuelve la configuracion del dispositivo en un json.
            Invocacion: /apiredis/configuracion?unit=DLGID
            La redis retorna un pickle.

            Testing:
            req=requests.get('http://127.0.0.1:5100/apiredis/configuracion', params={'unit':'PABLO'})
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
            app.logger.info( f'ERROR R001: Redis not connected, HOST:{BDREDIS_HOST}')
            return {'Err':f'No se puede conectar a REDIS HOST:{BDREDIS_HOST}'}, 500
        #
        if pk_config is None:
            app.logger.info( f'WARN_R001: No configuration rcd')
            return {},204   # NO CONTENT
        #
        # En la redis la configuracion es un dict serializado en bytestring
        # Lo paso a un json
        d_config = pickle.loads(pk_config)
        jd_config = json.dumps(d_config)
        return jd_config,200
   
    def put(self):
        ''' Actualiza(override) la configuracion para la unidad
            NO CHEQUEA EL FORMATO
            Invocacion: /apiredis/configuracion?unit=DLGID
            Como es PUT, la configuracion la mandamos en un json { dict_config }
            Se testea con:
            req=requests.put('http://127.0.0.1:5100/apiredis/configuracion', params={'unit':'DLGTEST'}, json=jd_conf)
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('unit',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        # get_json() convierte el objeto JSON a un python dict: lo serializo pickle
        jd_config = request.get_json()
        # app.logger.info(f'DEBUG PKCONFIG={jd_config}')
        d_config = json.loads(jd_config)
        pk_config = pickle.dumps(d_config)
        #
        rh = redis.Redis( BDREDIS_HOST, BDREDIS_PORT, BDREDIS_DB)
        try:
            _ = rh.hset( args['unit'],'PKCONFIG', pk_config)
        except redis.ConnectionError:
            app.logger.info( f'ERROR R001: Redis not connected, HOST:{BDREDIS_HOST}')
            return {'Err':f'No se puede conectar a REDIS HOST:{BDREDIS_HOST}'}, 500
        #
        return jd_config, 200

class ConfiguracionDebug(Resource):

    def get(self):
        ''' Retorna el id de la unidad que debe hacerse el debug
            Invocacion: /apiredis/configuracion/debugid?

            Testing:
            req=requests.get('http://127.0.0.1:5100/apiredis/configuracion/debugid')
            json.loads(req.json())
            {'debugId': 'PLCTEST'}

        '''
        rh = redis.Redis( BDREDIS_HOST, BDREDIS_PORT, BDREDIS_DB)
        try:
            debug_id = rh.hget('SPCOMMS', 'DEBUG_ID')
        except redis.ConnectionError:
            app.logger.info( f'ERROR R001: Redis not connected, HOST:{BDREDIS_HOST}')
            return {'Err': f'No se puede conectar a REDIS HOST:{BDREDIS_HOST}'}, 500
        #
        if debug_id is None:
            app.logger.info( f'WARN_R002: No debug_unit rcd, code 204')
            return {},204   # NO CONTENT
        #
        d_resp = {'debugId': debug_id.decode() }
        jd_resp = json.dumps(d_resp)
        return jd_resp,200
    
class ConfiguracionDlgidUid(Resource):
        
    def get(self):
        ''' Devuelve el par UID/ID en un json
            Invocacion: /apiredis/ordenes?unit=DLGID

            Testing:
            req=requests.get('http://127.0.0.1:5100/apiredis/configuracion/uid2id',params={'uid':'UID'})
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
            app.logger.info( f'ERROR R001: Redis not connected, HOST:{BDREDIS_HOST}')
            return {'Err':f'No se puede conectar a REDIS HOST:{BDREDIS_HOST}'}, 500
        #
        if unit_id is None:
            app.logger.info( f'WARN_R003: No uid2dlgi rcd, code 204')
            return {},204   # NO CONTENT
        #
        d_resp = {'uid': args['uid'], 'id':unit_id }
        jd_resp = json.dumps(d_resp)
        return jd_resp,200

    def put(self):
        ''' Actualiza(override) las tupla UID/DLGID
            Invocacion: apiredis/configuracion/uid2id?
            Como es PUT, la orden la mandamos en un json {'uid':UID, 'unit': ID }

            Testing:
            d={'uid':'012345678', 'unit':'DLGTEST'}
            jd=json.dumps(d)
            req=requests.put('http://127.0.0.1:5100/apiredis/configuracion/uid2id?, json=jd)
            json.loads(req.json())

        '''
        parser = reqparse.RequestParser()
        parser.add_argument('unit',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        jd_params = request.get_json()
        d_params = json.loads(jd_params)
        if 'uid' not in d_params:
            app.logger.info('ERROR R002: No UID in request_json_data')
            return {'Err':'No UID'}, 406
        #
        if 'unit' not in d_params:
            app.logger.info('ERROR R003: No UNIT ID in request_json_data')
            return {'Err':'No UNITID'}, 406
        #
        #app.logger.debug(f'Ordenes/Put DBUG: ordenes={ordenes}')
        rh = redis.Redis( BDREDIS_HOST, BDREDIS_PORT, BDREDIS_DB)
        try:
            _ = rh.hset( 'UID2DLGID', args['uid'], args['unit'] )
        except redis.ConnectionError:
            app.logger.info( f'ERROR R001: Redis not connected, HOST:{BDREDIS_HOST}')
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
            app.logger.info( f'ERROR R001: Redis not connected, HOST:{BDREDIS_HOST}')
            return {'Err':f'No se puede conectar a REDIS HOST:{BDREDIS_HOST}'}, 500
        #
        if pk_ordenes is None:
            app.logger.info( f'WARN_R004: No ordenes rcd, code 204')
            return {},204   # NO CONTENT
        #
        ordenes = pickle.loads(pk_ordenes)
        d_resp = {'ordenes': ordenes }
        jd_resp = json.dumps(d_resp)
        return jd_resp,200

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
        jd_params = request.get_json()
        d_params = json.loads(jd_params)
        if 'ordenes' not in d_params:
            app.logger.info('ERROR R004: No ordenes in request_json_data')
            return {'Err':'No ordenes'}, 406
        #
        ordenes = d_params['ordenes']
        #app.logger.debug(f'Ordenes/Put DBUG: ordenes={ordenes}')
        rh = redis.Redis( BDREDIS_HOST, BDREDIS_PORT, BDREDIS_DB)
        try:
            pk_ordenes = pickle.dumps(ordenes)
            _ = rh.hset( args['unit'], 'PKORDENES', pk_ordenes )
        except redis.ConnectionError:
            app.logger.info( f'ERROR R001: Redis not connected, HOST:{BDREDIS_HOST}')
            return {'Err':f'No se puede conectar a REDIS HOST:{BDREDIS_HOST}'}, 500
        #
        d_resp = {'ordenes': ordenes }
        jd_resp = json.dumps(d_resp)
        return jd_resp,200

class OrdenesPkatvise(Resource):

    def get(self):
        ''' 
        Retorna un diccionario con la ultima linea de ordenes para atvise

        Testing:
        req=requests.get('http://127.0.0.1:5100/apiredis/ordenes/atvise',params={'unit':'PLCTEST'})
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
            app.logger.info( f'ERROR R001: Redis not connected, HOST:{BDREDIS_HOST}')
            return {'Err':f'No se puede conectar a REDIS HOST:{BDREDIS_HOST}'}, 500
        #
        if pk_atvise is None:
            app.logger.info( f'WARN_R005: No pkordenes rcd, code 204')
            return {},204   # NO CONTENT
        #
        ordenes_atvise = pickle.loads(pk_atvise)
        d_resp = {'ordenes_atvise': ordenes_atvise }
        jd_resp = json.dumps(d_resp)
        return jd_resp,200

    def put(self):
        ''' Actualiza(override) la configuracion de ordenes de atvise para la unidad
            NO CHEQUEA EL FORMATO
            Como es PUT, la configuracion la mandamos en un json { ordenes_atvise }

            Testing:
            jat=json.dumps({'ordenes_atvise':{"UPA1_ORDER_1": 101, "UPA1_CONSIGNA_6": 102, "ESP_ORDER_8": 103}})
            req=requests.put('http://127.0.0.1:5100/apiredis/ordenes/atvise', params={'unit':'PLCTEST'}, json=jat)

        '''
        parser = reqparse.RequestParser()
        parser.add_argument('unit',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        jd_params = request.get_json()
        d_params = json.loads(jd_params)
        if 'ordenes_atvise' not in d_params:
            app.logger.info('ERROR_R005: No ordenes atvise in request_json_data')
            return {'Err':'No ordenes'}, 406
        #
        ordenes_atvise = d_params['ordenes_atvise']
        rh = redis.Redis( BDREDIS_HOST, BDREDIS_PORT, BDREDIS_DB)
        try:
            pk_ordenes_atvise = pickle.dumps(ordenes_atvise)
            _ = rh.hset( args['unit'],'PKATVISE', pk_ordenes_atvise)
        except redis.ConnectionError:
            app.logger.info( f'ERROR R001: Redis not connected, HOST:{BDREDIS_HOST}')
            return {'Err':f'No se puede conectar a REDIS HOST:{BDREDIS_HOST}'}, 500
        #
        d_resp = {'ordenes_atvise': ordenes_atvise }
        jd_resp = json.dumps(d_resp)
        return jd_resp,200

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
            app.logger.info( f'ERROR R001: Redis not connected, HOST:{BDREDIS_HOST}')
            return {'Err':f'No se puede conectar a REDIS HOST:{BDREDIS_HOST}'}, 500
        #
        if pk_dline is None:
            app.logger.info( f'ERROR R006: No dataline rcd, code 204')
            return {},204   # NO CONTENT
        #
        # En la redis la configuracion es un dict serializado.
        d_data = pickle.loads(pk_dline)
        jd_resp = json.dumps(d_data)
        return jd_resp,200

    def put(self):
        ''' Actualiza(override) la ultima linea eviada por la unidad.
            NO CHEQUEA EL FORMATO
            Como es PUT, la configuracion la mandamos en un json { dict_line }
            Encola la linea en RXDATA_QUEUE para su posterior procesamiento

            Testing:
            d_data = {'DATE': '230519','TIME': '144412','HTQ': '-2.50', 'q0': '0.000','AI0': 'nan','QS': '0.000','bt': '12.480'}
            j_data = json.dumps(data
            req=requests.put('http://127.0.0.1:5100/apiredis/dataline', params={'unit':'DLGTEST','type':'PLCR3'}, json=j_data)
            json.loads(req.json())

        '''
        parser = reqparse.RequestParser()
        parser.add_argument('unit',type=str,location='args',required=True)
        parser.add_argument('type',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        # get_json() convierte el objeto JSON a un python dict: lo serializo pickle
        jd_params = request.get_json()      # Es un str
        d_params = json.loads(jd_params)    # Es un dict      
        #
        rh = redis.Redis( BDREDIS_HOST, BDREDIS_PORT, BDREDIS_DB)
        # Actualizamos el registro PKLINE
        try:
            pk_line = pickle.dumps(d_params) # Es un bytearray
            _ = rh.hset( args['unit'],'PKLINE', pk_line )
        except redis.ConnectionError:
            app.logger.info( f'ERROR R001: Redis not connected, HOST:{BDREDIS_HOST}')
            return {'Err':f'No se puede conectar a REDIS HOST:{BDREDIS_HOST}'}, 500
        #
        # Actualizamos la tabla con los timestamps en cada linea nueva que insertamos.
        timestamp = dt.datetime.now()
        ptimestamp = pickle.dumps(timestamp)
        _ = rh.hset('TIMESTAMP', args['unit'], ptimestamp )
        #
        # Encolamos en RXDATA_QUEUE
        d_persistent = {'TYPE':args['type'], 'ID':args['unit'], 'D_LINE':d_params}
        pk_d_persistent = pickle.dumps(d_persistent)
        try:
            _ = rh.rpush( 'RXDATA_QUEUE', pk_d_persistent)
        except redis.ConnectionError:
            app.logger.debug( f'ERROR R001: Redis not connected, HOST:{BDREDIS_HOST}')
            return {'Err':f'No se puede conectar a REDIS HOST:{BDREDIS_HOST}'}, 500
        #
        jd_resp = json.dumps(d_persistent)
        return jd_resp,200
    
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
            app.logger.debug( f'ERROR R001: Redis not connected, HOST:{BDREDIS_HOST}')
            return {'Err':f'No se puede conectar a REDIS HOST:{BDREDIS_HOST}'}, 500
        #
        if qlength is None:
            app.logger.info( f'ERROR R007: No qlength rcd, code 204')
            return {},204   # NO CONTENT
        #
        d_resp =  {'qname': args['qname'], 'length': qlength}
        jd_resp = json.dumps(d_resp)
        return jd_resp,200
    
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
            app.logger.info( f'ERROR R001: Redis not connected, HOST:{BDREDIS_HOST}')
            return {'Err':f'No se puede conectar a REDIS HOST:{BDREDIS_HOST}'}, 500
        #
        if l_pkdatos is None:
            app.logger.info( f'ERROR R008: No l_pkdatos rcd, code 204')
            return {},204   # NO CONTENT
        #
        # Des-serializo los elementos de la lista.
        l_datos = []
        for i in l_pkdatos:
            l_datos.append( pickle.loads(i))

        #return jsonify(l_datos)
        jd_resp = json.dumps(l_datos)
        return jd_resp, 200
    
class Help(Resource):

    def get(self):
        ''' Retorna la descripcion de los metodos disponibles
        '''
        d_options = {
            'GET /apiredis/ping': 'Indica el estado de la api.',
            'GET /apiredis/configuracion?unit=DLGID':'Retorna la configuracion de la unit',
            'DELETE /apiredis/configuracion?unit=DLGID':'Borra la configuracion de la unit',
            'GET /apiredis/configuracion/debugid': 'Retorna el unitID usado para debug',
            'PUT /apiredis/configuracion?unit=DLGID': 'Actualiza la configuracion de la unit',
            'GET /apiredis/ordenes?unit=DLGID': 'Retorna la linea de ordenes para unit',
            'PUT /apiredis/ordenes?unit=DLGID': 'Actualiza(override) la linea de ordenes (json PUT Body) para unit',
            'GET /apiredis/ordenes/atvise?unit=DLGID': 'Retorna la linea de ordenes ATVISE para unit',
            'PUT /apiredis/ordenes/atvise?unit=DLGID': 'Actualiza(override) la linea de ordenes ATVISE (json PUT Body) para unit',
            'GET /apiredis/dataline?unit=DLGID': 'Retorna diccionario con datos de ultima linea recibida',
            'PUT /apiredis/dataline?unit=DLGID': 'Actualiza los datos de ultima linea recibida (json PUT Body) y el timestamp',
            'GET /apiredis/queuelength?qname=<qn>': 'Devuelve el la cantidad de elementos de la cola',
            'GET /apiredis/queueitems?qname=<qn>&<count=nn>':'Devuelve count elementos de la cola',
        }
        return d_options, 200


api.add_resource( Help, '/apiredis/help')
api.add_resource( Ping, '/apiredis/ping')
api.add_resource( DeleteRcd, '/apiredis/delete')
api.add_resource( Configuracion, '/apiredis/configuracion')
api.add_resource( ConfiguracionDebug, '/apiredis/configuracion/debugid')
api.add_resource( ConfiguracionDlgidUid, '/apiredis/configuracion/uid2id')
api.add_resource( Ordenes, '/apiredis/ordenes')
api.add_resource( OrdenesPkatvise, '/apiredis/ordenes/atvise')
api.add_resource( DataLine, '/apiredis/dataline')
api.add_resource( QueueLength, '/apiredis/queuelength')
api.add_resource( QueueItems, '/apiredis/queueitems')

# Lineas para que cuando corre desde gunicorn utilize el log handle de este
if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

# Lineas para cuando corre en modo independiente
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5100, debug=True)

