#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python
'''
'''

from flask import Flask
from flask_restful import Resource, Api, request, reqparse
from dlg import Dlg
from plc import Plc

app = Flask(__name__)
api = Api(app)

class Tests(Resource):

    def get(self):
        return {'Rsp': 'GET OK'}, 200

    def post(self):
        '''
        Procesa los POST que vienen de los PLC
        '''
        # Leo los argumentos que vinen en el URL.
        parser = reqparse.RequestParser()
        parser.add_argument('ID',type=str,location='args',required=True)
        parser.add_argument('VER',type=str,location='args',required=True)
        parser.add_argument('TYPE',type=str,location='args',required=True)
        args=parser.parse_args()
    
        # Logs general.
        app.logger.info("ApiTest INFO: PLC_QS=%(a)s", {'a': request.query_string })
        return {'Rsp': 'POST OK'}, 200
        #
 
class Ping(Resource):
    '''
    Prueba la conexion a la BD Redis
    '''
    def get(self):
        '''
        '''
        return {'rsp':'OK'}, 200
  
api.add_resource( Tests, '/tests')
api.add_resource( Ping, '/tests/ping')
api.add_resource( Dlg, '/dlg', resource_class_kwargs={ 'app': app })
api.add_resource( Plc,  '/plc')


if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6000, debug=True)
