#!/home/pablo/Spymovil/python/proyectos/APICOMMS/venv/bin/python
'''
API de comunicaciones SPCOMMS para los dataloggers y plc.
-----------------------------------------------------------------------------
R003 @ 2025-04-28:
- Agrego un TAG que me indique el timestamp de lo que demoran las transacciones
  y si terminan. 
  Esto es porque parece que hay veces que el servidor deja de responder.

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
from flask import Response 

from baseutils.baseutils import version2int, format_response, tag_generator, tagLog

from prot_fwdlgx.fwdlgxR10X import FwdlgxR10X
from prot_fwdlgx.fwdlgxR11X import FwdlgxR11X

from prot_spxavrda.spxavrdaR11X import SpxavrdaR11X
from prot_spxavrda.spxavrdaR12X import SpxavrdaR12X

from prot_spxxmega.spxxmegaR11X import SpxxmegaR11X
from prot_spxxmega.spxxmegaR12X import SpxxmegaR12X
from prot_spxxmega.spxxmegaR13X import SpxxmegaR13X

from prot_spqavrda.spqavrdaR11X import SpqavrdaR11X
from prot_spqavrda.spqavrdaR12X import SpqavrdaR12X
from prot_spqavrda.spqavrdaR13X import SpqavrdaR13X

from prot_dpdavrda.dpdavrdaR10X import DpdavrdaR10X

API_VERSION = 'R003 @ 2025-04-28'


#--------------------------------------------------------------------------------------------
class Apidlg(Resource):
    ''' 
    Clase especializada en atender los dataloggers
    Recibe como kwargs un diccionario con 2 claves: una es la app flask ppal
    que es la que tiene el link del log handler, y otro es un diccionario de los
    servidores de las api auxiliares.
    Al invocarlo ya genero el TAG para identificar la conexión
    '''
    def __init__(self, **kwargs):
        self.app = kwargs['app']
        self.servers = kwargs['servers']
        self.qs = None
        self.tag = tag_generator()
        
    def get(self):
        ''' 
        Procesa los GET de los dataloggers: configuracion y datos.
        '''
        self.qs = request.query_string
        #self.qs = request.query_string.decode('utf-8')
        self.app.logger.info("(100) Rcvd Frame: aQS=%(a)s", {'a': self.qs })

        parser = reqparse.RequestParser()
        parser.add_argument('TYPE', type=str ,location='args', required=True)
        parser.add_argument('VER', type=str ,location='args', required=True)
        parser.add_argument('HW', type=str ,location='args', required=False)
        parser.add_argument('ID', type=str ,location='args', required=False)
        parser.add_argument('CLASS', type=str ,location='args', required=False)
        args = parser.parse_args()
        fw_type = args.get('TYPE',None)
        fw_ver = args.get('VER','0.0.0')
        dlg_hw = args.get('HW','NONE')
        dlg_id = args.get('ID','NONE')
        dlg_frame = args.get('CLASS','NONE')
        # El chequeo de errores se hace porque parse_args() aborta y retorna None
        if fw_type is None:
            raw_response = 'ERROR:FAIL TO PARSE'
            status_code = 500
            self.app.logger.info(f"(101) Rcvd Frame ERROR: RSP=[{raw_response}]")
            response = format_response(raw_response)
            return response, status_code

        ifw_ver = version2int(fw_ver)

        #print(f'TAG={self.tag} LB=START TS={timestamp()} ID={id} TYPE={dlg_type} VER={dlg_ver} HW={dlg_hw}')
        # Hago un selector del tipo y protocolo para seleccionar el objeto que
        # tiene la representacion mas adecuada
        # Debemos pasarle la app y los servers para que hagan el log por la app.
        d_args = {'app':self.app, 
                  'servers':self.servers, 
                  'qs':self.qs,
                  'url_redis': f"http://{self.servers['APIREDIS_HOST']}:{self.servers['APIREDIS_PORT']}/apiredis/",
                  'url_conf':f"http://{self.servers['APICONF_HOST']}:{self.servers['APICONF_PORT']}/apiconf/" }

        # Log en pantalla y redis para monitorear la aplicacion
        tagLog( redis_url=d_args.get('url_redis',None), 
               args={'LABEL':'START', 'TAG':self.tag, 'ID':dlg_id,'TYPE':fw_type,'VER':fw_ver,'HW':dlg_hw, 'CLASS':dlg_frame} 
               )

        # El nuevo firmware unificado es solo FWDLGX
        if ( fw_type == 'FWDLGX'):
            # [('1.0.2', 59), ('1.0.1', 18), ('1.0.0', 6), ('1.0.3', 6), ('1.0.4', 1)]
            if ifw_ver == 100:
                # ('1.0.0', 6), ('1.0.1', 18),('1.0.2', 59),('1.0.3', 6), ('1.0.4', 1)
                dlg = FwdlgxR10X(d_args)
            elif ifw_ver == 110:
                dlg = FwdlgxR11X(d_args)
            else:
                # Por defecto usamos la version mas vieja
                dlg = FwdlgxR10X(d_args)
        
        # Versiones anteriores.
        elif (fw_type == 'SPX_AVRDA') or (fw_type == 'SPXR2'):
            # SPXR2->('1.1.0', 14)
            # SPX_AVRDA->('1.2.0', 107)
            if ifw_ver == 110:
                dlg = SpxavrdaR11X(d_args)
            elif ifw_ver == 120:
                dlg = SpxavrdaR12X(d_args)
            else:
                # Por defecto usamos la version mas vieja
                dlg = SpxavrdaR11X(d_args)

        elif (fw_type == 'SPX_XMEGA') or (fw_type == 'SPXR3'):
            # SPXR3->('1.1.0', 96)
            # SPX_XMEGA->[('1.2.0', 2)]
            if ifw_ver <= 110:
                dlg = SpxxmegaR11X(d_args)
            elif ifw_ver <= 120:
                dlg = SpxxmegaR12X(d_args)
            elif ifw_ver <= 130:
                # 2025-02-28: FWDLGX
                dlg = SpxxmegaR13X(d_args)
            else:
                # Por defecto usamos la version mas vieja
                dlg = SpxxmegaR11X(d_args)

        elif (fw_type == 'SPQ_AVRDA'):
            # SPQ_AVRDA->[('1.3.7', 56), ('1.2.6', 6), ('1.3.9', 27), ('1.3.3', 15), ('1.3.6', 13), ('1.3.4', 1)]
            if ifw_ver <= 110:
                dlg = SpqavrdaR11X(d_args)
            elif ifw_ver <= 120:
                dlg = SpqavrdaR12X(d_args)
            elif ifw_ver <= 130:
                dlg = SpqavrdaR13X(d_args)
            else:
                # Por defecto usamos la version mas vieja
                dlg = SpqavrdaR11X(d_args)

        elif (fw_type == 'DPD'):
            # DPD->[('1.0.7', 1)]
            dlg = DpdavrdaR10X(d_args)

        else:

            # Por defecto usamos la version mas vieja
             dlg = FwdlgxR10X(d_args)

        # Proceso el frame y envio la respuesta
        (raw_response, status_code) = dlg.process_frame()
        if raw_response is not None:
            response = format_response(raw_response)

        tagLog( redis_url=d_args.get('url_redis',None), 
               args={'LABEL':'STOP', 'TAG':self.tag } 
               )
        if raw_response is not None:
            return response, status_code
        else:
            return Response(status=204)
