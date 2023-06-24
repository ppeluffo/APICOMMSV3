#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python

from flask_restful import reqparse
from flask_restful import Resource


class Plc(Resource):

    def __init__(self ):
        pass

    def get(self):
        '''
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('ID',type=str,location='args',required=True)
        parser.add_argument('VER',type=str,location='args',required=True)
        parser.add_argument('TYPE',type=str,location='args',required=True)
        args=parser.parse_args()
        #
        id = args['ID']
        ver = args['VER']
        tipo = args['TYPE']

        # Logs general.
        print(f"Test DLG: ID={id},VER={ver},TYPE={tipo}")

        d_rsp = {'Res':'OK','Msg':'PLC', 'ID':id,'VER':ver,'TYPE':tipo}
        return d_rsp, 200