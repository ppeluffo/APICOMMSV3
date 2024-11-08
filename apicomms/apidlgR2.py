#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python
'''
API de comunicaciones SPCOMMS para los dataloggers y plc.
-----------------------------------------------------------------------------
R002 @ 2023-09-13: (commsv3_apicomms:1.2)
- Agrego a la configuracion las consignas

R001 @ 2023-06-15: (commsv3_apicomms:1.1)
- Se modifica el procesamiento de frames de modo que al procesar uno de DATA sea
  como los PING, no se lee la configuracion ya que no se necesita y genera carga
  innecesaria.
- Se manejan todos los parámetros por variables de entorno
- Se agrega un entrypoint 'ping' que permite ver si la api esta operativa

'''

from flask_restful import Resource, request, reqparse
from dlg_spx_avrda_r110 import Dlg_spx_avrda_R110
from dlg_spx_avrda_r120 import Dlg_spx_avrda_R120

from dlg_spx_xmega_r110 import Dlg_spx_xmega_R110 
from dlg_spx_xmega_r120 import Dlg_spx_xmega_R120

from dlg_spq_avrda_r110 import Dlg_spq_avrda_R110
from dlg_spq_avrda_r120 import Dlg_spq_avrda_R120
from dlg_spq_avrda_r130 import Dlg_spq_avrda_R130

from dlg_dpd_avrda_r100 import Dlg_dpd_avrda_R100

from apidlgR2_utils import version2int, format_response

API_VERSION = 'R002 @ 2024-04-01'

class ApidlgR2(Resource):
    ''' 
    Clase especializada en atender los dataloggers
    Recibe como kwargs un diccionario con 2 claves: una es la app flask ppal
    que es la que tiene el link del log handler, y otro es un diccionario de los
    servidores de las api auxiliares.
    '''
    def __init__(self, **kwargs):
        self.app = kwargs['app']
        self.servers = kwargs['servers']
        self.qs = None
        
    def get(self):
        ''' 
        Procesa los GET de los dataloggers: configuracion y datos.
        '''
        self.qs = request.query_string
        self.app.logger.info("(100) Rcvd Frame: aQS=%(a)s", {'a': self.qs })

        parser = reqparse.RequestParser()
        parser.add_argument('TYPE', type=str ,location='args', required=True)
        parser.add_argument('VER', type=str ,location='args', required=True)
        args = parser.parse_args()
        dlg_type = args['TYPE']
        dlg_ver = args['VER']
        # El chequeo de errores se hace porque parse_args() aborta y retorna None
        if dlg_type is None:
            raw_response = 'ERROR:FAIL TO PARSE'
            status_code = 500
            self.app.logger.info(f"(101) Rcvd Frame ERROR: RSP=[{raw_response}]")
            response = format_response(raw_response)
            return response, status_code

        dlg_ifw_ver = version2int(dlg_ver)
        #print(f'TYPE={dlg_type}, VER={dlg_ver}, IFW={dlg_ifw_ver}')
        
        # Hago un selector del tipo y protocolo para seleccionar el objeto que
        # tiene la representacion mas adecuada
        # Debemos pasarle la app y los servers para que hagan el log por la app.
        d_args = {'app':self.app, 
                  'servers':self.servers, 
                  'qs':self.qs,
                  'url_redis': f"http://{self.servers['APIREDIS_HOST']}:{self.servers['APIREDIS_PORT']}/apiredis/",
                  'url_conf':f"http://{self.servers['APICONF_HOST']}:{self.servers['APICONF_PORT']}/apiconf/" }

        if (dlg_type == 'SPX_AVRDA') or (dlg_type == 'SPXR2'):
            if dlg_ifw_ver <= 110:
                dlg = Dlg_spx_avrda_R110(d_args)
            elif dlg_ifw_ver <= 120:
                dlg = Dlg_spx_avrda_R120(d_args)
            else:
                # Por defecto usamos la version mas vieja
                dlg = Dlg_spx_avrda_R110(d_args)

        elif (dlg_type == 'SPX_XMEGA') or (dlg_type == 'SPXR3'):
            if dlg_ifw_ver <= 110:
                dlg = Dlg_spx_xmega_R110(d_args)
            elif dlg_ifw_ver <= 120:
                dlg = Dlg_spx_xmega_R120(d_args)
            else:
                # Por defecto usamos la version mas vieja
                dlg = Dlg_spx_xmega_R110(d_args)

        elif (dlg_type == 'SPQ_AVRDA'):
            if dlg_ifw_ver <= 110:
                dlg = Dlg_spq_avrda_R110(d_args)
            elif dlg_ifw_ver <= 120:
                dlg = Dlg_spq_avrda_R120(d_args)
            elif dlg_ifw_ver <= 130:
                dlg = Dlg_spq_avrda_R130(d_args)
            else:
                # Por defecto usamos la version mas vieja
                dlg = Dlg_spq_avrda_R110(d_args)

        elif (dlg_type == 'DPD'):
            dlg = Dlg_dpd_avrda_R100(d_args)

        else:

            dlg = Dlg_spx_avrda_R120(d_args)

        # Proceso el frame y envio la respuesta
        (raw_response, status_code) = dlg.process_frame()
        response = format_response(raw_response)
        return response, status_code
    
