#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python
'''
API de comunicaciones SPCOMMS para los dataloggers y plc.
-----------------------------------------------------------------------------
R001 @ 2023-06-15: (commsv3_apicomms:1.1)
- Se modifica el procesamiento de frames de modo que al procesar uno de DATA sea
  como los PING, no se lee la configuracion ya que no se necesita y genera carga
  innecesaria.
- Se manejan todos los parámetros por variables de entorno
- Se agrega un entrypoint 'ping' que permite ver si la api esta operativa

'''

import os
import datetime as dt
import logging
import requests
from flask import Flask
from flask_restful import Resource, Api
from apidlg import ApiDlg
from apiplc import ApiPlc
from apioceanus import ApiOceanus

app = Flask(__name__)
api = Api(app)
 
API_VERSION = 'R002 @ 2023-09-26'

APIREDIS_HOST = os.environ.get('APIREDIS_HOST', 'apiredis')
APIREDIS_PORT = os.environ.get('APIREDIS_PORT', '5100')
APICONF_HOST = os.environ.get('APICONF_HOST', 'apiconf')
APICONF_PORT = os.environ.get('APICONF_PORT', '5200')

# SOLO EN TESTING ALONE !!!
"""
APIREDIS_HOST = '127.0.0.1'
APIREDIS_PORT = '5100'
APICONF_HOST = '127.0.0.1'
APICONF_PORT = '5200'
"""

servers = {
   'APIREDIS_HOST': APIREDIS_HOST,
   'APIREDIS_PORT': APIREDIS_PORT,
   'APICONF_HOST' : APICONF_HOST,
   'APICONF_PORT' : APICONF_PORT
}


class Ping(Resource):
    '''
    Responde el estado de las conexiones con las apis auxiliares.
    '''
    def get(self):
        '''
        '''
        # Pruebo la conexion a REDIS
        redis_status = 'ERR'
        try:
            r_conf = requests.get(f"http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/ping",timeout=10 )
            if r_conf.status_code == 200:
                redis_status = 'OK'
        except requests.exceptions.RequestException as err: 
            app.logger.info( f'(400) ApiCOMMS_ERR001: Redis request exception, HOST:{APIREDIS_HOST}:{APIREDIS_PORT}, Err:{err}')
        #
        # Pruebo la conexion a SQL
        sql_status = 'ERR'
        try:
            r_conf = requests.get(f"http://{APICONF_HOST}:{APICONF_PORT}/apiconf/ping",timeout=10 )
            if r_conf.status_code == 200:
                sql_status = 'OK'
        except requests.exceptions.RequestException as err: 
            app.logger.info( f'(401) ApiCOMMS_ERR002: Sql request exception, HOST:{APICONF_HOST}:{APICONF_PORT}, Err:{err}')
        #
        #
        if redis_status == 'OK' and sql_status == 'OK':
            ping_status = 'OK'
        else:
            ping_status = 'FAIL'
            
        return {'rsp':f'{ping_status}','redis_status':redis_status, 'sql_status':sql_status, 'version':API_VERSION, 'API_REDIS':f'{APIREDIS_HOST}:{APIREDIS_PORT}','API_CONF':f'{APICONF_HOST}:{APICONF_PORT}' }, 200

class Help(Resource):
    '''
    Devuelve el estado de la conexion a la BD Redis.
    '''
    def get(self):
        '''
        '''
        return {}, 200

api.add_resource( ApiPlc, '/apiplc', resource_class_kwargs={ 'app': app, 'servers':servers })
api.add_resource( ApiDlg, '/apidlg', resource_class_kwargs={ 'app': app, 'servers':servers })
api.add_resource( ApiOceanus, '/apioceanus', resource_class_kwargs={ 'app': app, 'servers':servers })
api.add_resource( Help,   '/apicomms/help')
api.add_resource( Ping,   '/apicomms/ping')

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

    app.logger.info( f'Starting ApiCOMMS: REDIS_HOST={APIREDIS_HOST}, REDIS_PORT={APIREDIS_PORT}' )
    app.logger.info( f'         ApiCOMMS: CONF_HOST={APICONF_HOST}, CONF_PORT={APICONF_PORT}' )

if __name__ == '__main__':
    APIREDIS_HOST = '127.0.0.1'
    APICONF_HOST = '127.0.0.1'
    app.run(host='0.0.0.0', port=5000, debug=True)
