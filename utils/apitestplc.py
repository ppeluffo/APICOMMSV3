#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python
'''
API de comunicaciones SPCOMMS para los dataloggers y plc.
'''

import os
import json
import requests
import datetime as dt
from flask import Flask, request, make_response
from flask_restful import Resource, Api, reqparse
import apicomms_utils_dlg
import apicomms_utils_plc

app = Flask(__name__)
api = Api(app)

class PlcTest(Resource):
    '''
    Clase de pruebas de PLCs
    '''
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('ID',type=str,location='args',required=True)
        parser.add_argument('VER',type=str,location='args',required=True)
        parser.add_argument('TYPE',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        app.logger.debug('APICOMMS: GET')
        return {'Msg':'SPYMOVIL OK', 'ID':args['ID'], 'VER':args['VER'], 'TYPE':args['TYPE'] } , 200

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('ID',type=str,location='args',required=True)
        parser.add_argument('VER',type=str,location='args',required=True)
        parser.add_argument('TYPE',type=str,location='args',required=True)
        args=parser.parse_args()

        app.logger.debug('APICOMMS: POST')

        rxdata = request.get_data()
        app.logger.debug(f'POST RX DATA = [{rxdata}]')

        sresp = b'respuesta de Spymovil'
        #sresp = b'\n\x0bf\xe6\xf6Bb\x04W\x02\xecq\xe4C:\x16\x00\x00\x00\x00\x00\x0b\xa3'
        response = make_response(sresp)
        response.headers['Content-type'] = 'application/binary'
        return response
    
        #return 'SPYMOVIL POST OK', 200

api.add_resource( PlcTest, '/apicomms/plctest')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    
