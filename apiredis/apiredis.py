#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python
'''
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

'''

import os
import pickle
import datetime as dt
import redis
import json
from flask import Flask, request, jsonify
from flask_restful import Resource, Api, reqparse

app = Flask(__name__)
api = Api(app)

#REDIS_HOST='127.0.0.1'
#REDIS_HOST='192.168.0.6'
#REDIS_PORT='6379'
#REDIS_DB='0'

REDIS_HOST = os.environ.get('REDIS_HOST','127.0.0.1')
REDIS_PORT = os.environ.get('REDIS_PORT','6379')
REDIS_DB = os.environ.get('REDIS_DB','0')

APIREDIS_PORT = os.environ.get('APIREDIS_PORT','5100')

print(f'DB REDIS: HOST={REDIS_HOST},PORT={REDIS_PORT},ID={REDIS_DB} ')

'''
Pendiente:

GET     /apiredis/configuracion/dlgidfromuid?uid=<uid>  Retorna el DLGID asociado al UID
PUT     /apiredis/configuracion/dlgidfromuid?dlgid=<dlgid>&uid=<uid>    Actualiza el par ( DLGID, UID )

'READ_DLGID_FROM_UID'
'SAVE_DLGID_UID'
'''

class Configuracion(Resource):

    def get(self):
        ''' Devuelve la configuracion del dispositivo
            Invocacion: /apiredis/configuracion?unit=DLGID
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('unit',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        rh = redis.Redis( REDIS_HOST, REDIS_PORT, REDIS_DB)
        try:
            pdict = rh.hget( args['unit'], 'PKCONFIG')
        except redis.ConnectionError:
            app.logger.debug( f'Configuracion/get ERROR: Redis not connected, HOST:{REDIS_HOST}')
            return {'Err':f'No se puede conectar a REDIS HOST:{REDIS_HOST}'}, 500
        #
        if pdict is None:
            app.logger.info( f'Configuracion/get: NO config rcd, code 204')
            return {},204   # NO CONTENT
        #
        # En la redis la configuracion es un dict serializado.
        dconf = pickle.loads(pdict)
        return dconf, 200
   
    def delete(self):
        ''' Borra el registro de configuracion
            Invocacion: /apiredis/configuracion?unit=DLGID
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('unit',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        rh = redis.Redis( REDIS_HOST, REDIS_PORT, REDIS_DB)
        try:
            _=rh.delete(args['unit'])
        except redis.ConnectionError:
            app.logger.debug( f'Configuracion/delete ERROR: Redis not connected, HOST:{REDIS_HOST}')
            return {'Err':f'No se puede conectar a REDIS HOST:{REDIS_HOST}'}, 500
        #
        return {'unit':args['unit'], 'Rsp':'Deleted'}, 200

    def put(self):
        ''' Actualiza(override) la configuracion para la unidad
            NO CHEQUEA EL FORMATO
            Invocacion: /apiredis/configuracion?unit=DLGID
            Como es PUT, la configuracion la mandamos en un json { dict_config }
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('unit',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        # get_json() convierte el objeto JSON a un python dict: lo serializo pickle
        dict_config = request.get_json()
        pk_dconfig = pickle.dumps(dict_config)
        #
        rh = redis.Redis( REDIS_HOST, REDIS_PORT, REDIS_DB)
        try:
            _ = rh.hset( args['unit'],'PKCONFIG', pk_dconfig)
        except redis.ConnectionError:
            app.logger.debug( f'Configuracion/put ERROR: Redis not connected, HOST:{REDIS_HOST}')
            return {'Err':f'No se puede conectar a REDIS HOST:{REDIS_HOST}'}, 500
        #
        return dict_config, 200

class ConfiguracionDebug(Resource):

    def get(self):
        ''' Retorna el id de la unidad que debe hacerse el debug
            Invocacion: /apiredis/configuracion/debugid?
        '''
        rh = redis.Redis( REDIS_HOST, REDIS_PORT, REDIS_DB)
        try:
            debug_id = rh.hget('SPCOMMS', 'DEBUG_ID')
        except redis.ConnectionError:
            app.logger.debug( f'ConfiguracionDebug/get ERROR: Redis not connected, HOST:{REDIS_HOST}')
            return {'Err': f'No se puede conectar a REDIS HOST:{REDIS_HOST}'}, 500
        #
        if debug_id is None:
            app.logger.info( f'ConfiguracionDebug/get: NO debug_unit rcd, code 204')
            return {},204   # NO CONTENT
        #
        return debug_id.decode(), 200
    
class ConfiguracionDlgidUid(Resource):
    pass

class Ordenes(Resource):

    def get(self):
        ''' Devuelve las ordenes para la unidad
            Invocacion: /apiredis/ordenes?unit=DLGID
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('unit',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        rh = redis.Redis( REDIS_HOST, REDIS_PORT, REDIS_DB)
        try:
            ordenes = rh.hget( args['unit'], 'ORDENES' )
        except redis.ConnectionError:
            app.logger.debug( f'Ordenes/get ERROR: Redis not connected, HOST:{REDIS_HOST}')
            return {'Err':f'No se puede conectar a REDIS HOST:{REDIS_HOST}'}, 500
        #
        if ordenes is None:
            app.logger.info( f'Ordenes/get: NO ordenes rcd, code 204')
            return {},204   # NO CONTENT
        #
        return ordenes.decode(), 200

    def put(self):
        ''' Actualiza(override) las ordenes para la unidad
            NO CHEQUEA EL FORMATO DE LA LINEA DE ORDENES
            Invocacion: /apiredis/ordenes?unit=DLGID
            Como es PUT, la orden la mandamos en un json {'ordenes':orden }
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('unit',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        request_json_data = request.get_json()
        if 'ordenes' not in request_json_data:
            app.logger.debug('Ordenes/Put ERROR: No ordenes in request_json_data')
            return {'Err':'No ordenes'}, 406
        #
        ordenes = request_json_data['ordenes']
        #app.logger.debug(f'Ordenes/Put DBUG: ordenes={ordenes}')
        rh = redis.Redis( REDIS_HOST, REDIS_PORT, REDIS_DB)
        try:
            _ = rh.hset( args['unit'], 'ORDENES', ordenes )
        except redis.ConnectionError:
            app.logger.debug( f'Ordenes/Put ERROR: Redis not connected, HOST:{REDIS_HOST}')
            return {'Err':f'No se puede conectar a REDIS HOST:{REDIS_HOST}'}, 500
        #
        return {'ordenes':ordenes}, 200

class OrdenesPkatvise(Resource):

    def get(self):
        ''' Retorna un diccionario con la ultima linea de ordenes para atvise
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('unit',type=str,location='args',required=True)
        args=parser.parse_args()
    
        rh = redis.Redis( REDIS_HOST, REDIS_PORT, REDIS_DB)
        try:
            pk_atvise = rh.hget( args['unit'],'PKATVISE')
        except redis.ConnectionError:
            app.logger.debug( f'OrdenesPkatvise/get ERROR: Redis not connected, HOST:{REDIS_HOST}')
            return {'Err':f'No se puede conectar a REDIS HOST:{REDIS_HOST}'}, 500
        #
        if pk_atvise is None:
            app.logger.info( f'OrdenesPkatvise/get: NO pkatvise ordenes rcd, code 204')
            return {},204   # NO CONTENT
        #
        orders_atvise = pickle.loads(pk_atvise)
        return orders_atvise, 200

    def put(self):
        ''' Actualiza(override) la configuracion de ordenes de atvise para la unidad
            NO CHEQUEA EL FORMATO
            Como es PUT, la configuracion la mandamos en un json { ordenes_atvise }
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('unit',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        # get_json() convierte el objeto JSON a un python dict: lo serializo pickle
        dict_ordenes_atvise = request.get_json()
        pk_dict_ordenes_atvise = pickle.dumps(dict_ordenes_atvise)
        #
        rh = redis.Redis( REDIS_HOST, REDIS_PORT, REDIS_DB)
        try:
            _ = rh.hset( args['unit'],'PKATVISE', pk_dict_ordenes_atvise)
        except redis.ConnectionError:
            app.logger.debug( f'OrdenesPkatvise/get ERROR: Redis not connected, HOST:{REDIS_HOST}')
            return {'Err':f'No se puede conectar a REDIS HOST:{REDIS_HOST}'}, 500
        #
        return dict_ordenes_atvise, 200

class DataLine(Resource):

    # Retorna un diccionario con la ultima linea
    def get(self):
        ''' Leemos la ultima linea que envio el datalogger.
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('unit',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        rh = redis.Redis( REDIS_HOST, REDIS_PORT, REDIS_DB)
        try:
            pdict = rh.hget( args['unit'], 'PKLINE')
        except redis.ConnectionError:
            app.logger.debug( f'DataLine/get ERROR: Redis not connected, HOST:{REDIS_HOST}')
            return {'Err':f'No se puede conectar a REDIS HOST:{REDIS_HOST}'}, 500
        #
        if pdict is None:
            app.logger.info( f'DataLine/get: NO dataline rcd, code 204')
            return {},204   # NO CONTENT
        #
        # En la redis la configuracion es un dict serializado.
        dline = pickle.loads(pdict)
        return dline, 200

    def put(self):
        ''' Actualiza(override) la ultima linea eviada por la unidad.
            NO CHEQUEA EL FORMATO
            Como es PUT, la configuracion la mandamos en un json { dict_line }
            Encola la linea en RXDATA_QUEUE para su posterior procesamiento
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('unit',type=str,location='args',required=True)
        parser.add_argument('type',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        # get_json() convierte el objeto JSON a un python dict: lo serializo pickle
        jd_line = request.get_json()    # Es un str
        d_line = json.loads(jd_line)    # Es un dict
        pk_dline = pickle.dumps(d_line) # Es un bytearray
        #
        rh = redis.Redis( REDIS_HOST, REDIS_PORT, REDIS_DB)
        # Actualizamos el registro PKLINE
        try:
            _ = rh.hset( args['unit'],'PKLINE', pk_dline )
        except redis.ConnectionError:
            app.logger.debug( f'DataLine/get ERROR: Redis not connected, HOST:{REDIS_HOST}')
            return {'Err':f'No se puede conectar a REDIS HOST:{REDIS_HOST}'}, 500
        #
        # Actualizamos la tabla con los timestamps en cada linea nueva que insertamos.
        timestamp = dt.datetime.now()
        ptimestamp = pickle.dumps(timestamp)
        _ = rh.hset('TIMESTAMP', args['unit'], ptimestamp )
        #
        # Encolamos en RXDATA_QUEUE
        d_persistent = {'TYPE':args['type'], 'ID':args['unit'], 'D_LINE':d_line}
        pk_d_persistent = pickle.dumps(d_persistent)
        try:
            _ = rh.rpush( 'RXDATA_QUEUE', pk_d_persistent)
        except redis.ConnectionError:
            app.logger.debug( f'DataLine/get ERROR: Redis not connected, HOST:{REDIS_HOST}')
            return {'Err':f'No se puede conectar a REDIS HOST:{REDIS_HOST}'}, 500
        #
        return d_line, 200
    
class QueueLength(Resource):
    
    def get(self):
        ''' Retorna el largo de la cola pasasa como parametro
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('qname',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        rh = redis.Redis( REDIS_HOST, REDIS_PORT, REDIS_DB)
        try:
            qlength = rh.llen(args['qname'])
        except redis.ConnectionError:
            app.logger.debug( f'QueueLength/get ERROR: Redis not connected, HOST:{REDIS_HOST}')
            return {'Err':f'No se puede conectar a REDIS HOST:{REDIS_HOST}'}, 500
        #
        if qlength is None:
            app.logger.info( f'QueueLength/get: NO qlength rcd, code 204')
            return {},204   # NO CONTENT
        #
        return {'qname': args['qnames'], 'length': qlength.decode()}, 200

class QueueItems(Resource):
    
    def get(self):
        ''' Retorna los elementos de una cola
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('qname',type=str,location='args',required=True)
        parser.add_argument('count',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        rh = redis.Redis( REDIS_HOST, REDIS_PORT, REDIS_DB)
        try:
            l_pkdatos = []
            l_pkdatos = rh.lpop(args['qname'], args['count'])
        except redis.ConnectionError:
            app.logger.debug( f'QueueItems/get ERROR: Redis not connected, HOST:{REDIS_HOST}')
            return {'Err':f'No se puede conectar a REDIS HOST:{REDIS_HOST}'}, 500
        #
        if l_pkdatos is None:
            app.logger.info( f'QueueItems/get: NO l_pkdatos rcd, code 204')
            return {},204   # NO CONTENT
        #
        l_datos = []
        for i in l_pkdatos:
            l_datos.append( pickle.loads(i))

        return jsonify(l_datos)
    
class Help(Resource):

    def get(self):
        ''' Retorna la descripcion de los metodos disponibles
        '''
        d_options = {
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
api.add_resource( Configuracion, '/apiredis/configuracion')
api.add_resource( ConfiguracionDebug, '/apiredis/configuracion/debugid')
api.add_resource( Ordenes, '/apiredis/ordenes')
api.add_resource( OrdenesPkatvise, '/apiredis/ordenes/atvise')
api.add_resource( DataLine, '/apiredis/dataline')
api.add_resource( QueueLength, '/apiredis/queuelength')
api.add_resource( QueueItems, '/apiredis/queueitems')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=APIREDIS_PORT, debug=True)

