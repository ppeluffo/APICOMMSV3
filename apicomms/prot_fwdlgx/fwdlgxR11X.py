#!/home/pablo/Spymovil/python/proyectos/APICOMMS/venv/bin/python

import datetime as dt
from flask_restful import reqparse, request
from baseutils.baseutils import read_configuration, update_uid2id, read_debug_id, update_comms_conf, convert_dataline2dict  
from baseutils.baseutils import convert_line2dict
import requests
from prot_fwdlgx.fwdlgxR10X import FwdlgxR10X

class FwdlgxR11X(FwdlgxR10X):
    '''
    El R110 es una subclase de R100 por lo tanto R110 hereda de R100 (super)
    '''
    def __init__(self, d_args=None):
        self.d_args = d_args
        super().__init__(d_args)
            
    '''
    Implemento TODOS los metodos personalizados por version que voy a usar
    en la clase padre de todas.
    Si el método no tienen particularidades, lo refiero por herencia
    '''

    ############################################################################################
    # CONFIG ALL
    
    def process_frame_configAll(self):
        '''
        ERRORES: 5XX
        '''
        # ID=SPQTEST&HW=SPQ_AVRDA_R1&TYPE=FWDLGX&VER=1.0.4&CLASS=CONF_ALL&UID=42419193000040100136011800000000&IMEI=868191051472973&
        #                                 ICCID=8959801019445151129F&CSQ=73&WDG=32&BH=0x42&AH=0xA4&CH=0xBC&MH=0x2B&PH=0x15

        app = self.d_args.get('app',None)

        if self.d_args['debugFlag'] is True:
            app.logger.info("DEBUG: FwdlgxR11X:: process_frame_configAll")


        parser = reqparse.RequestParser()
        parser.add_argument('ID', type=str ,location='args', required=True)
        parser.add_argument('HW', type=str ,location='args', required=False)
        parser.add_argument('TYPE', type=str ,location='args', required=False)
        parser.add_argument('VER', type=str ,location='args', required=False)
        
        parser.add_argument('UID', type=str ,location='args', required=True)
        parser.add_argument('IMEI', type=str ,location='args', required=False)
        parser.add_argument('ICCID', type=str ,location='args', required=False)
        parser.add_argument('CSQ', type=str ,location='args', required=False)

        parser.add_argument('WDG', type=str ,location='args', required=True)

        parser.add_argument('BH', type=str ,location='args', required=True)
        parser.add_argument('AH', type=str ,location='args', required=True)
        parser.add_argument('CH', type=str ,location='args', required=True)
        parser.add_argument('MH', type=str ,location='args', required=True)
        parser.add_argument('PH', type=str ,location='args', required=True)

        args = parser.parse_args()
        dlgid = args.get('ID',None)
        # El chequeo de errores se hace porque parse_args() aborta y retorna None
        if dlgid is None:
            app.logger.info("(500) process_frame_base ERROR: No dlgid")
            response = 'ERROR:NO DLGID'
            status_code = 500
            app.logger.info(f"(501)process_frame_base ERROR: RSP=[{response}]")
            return response, status_code
        
        # Chequeo la causa de conexión: 
        wdg = int(args.get('WDG',-1))
        if (wdg & 0x01) != 0:
            app.logger.info(f"(507) process_frame_configAll: {dlgid} RESET CAUSE PORF")
        elif (wdg & 0x02) != 0:
            app.logger.info(f"(507) process_frame_configAll: {dlgid} RESET CAUSE BORF")
        elif (wdg & 0x04) != 0:
            app.logger.info(f"(507) process_frame_configAll: {dlgid} RESET CAUSE EXTF")
        elif (wdg & 0x08) != 0:
            app.logger.info(f"(507) process_frame_configAll: {dlgid} RESET CAUSE WDRF")
        elif (wdg & 0x10) != 0:
            app.logger.info(f"(507) process_frame_configAll: {dlgid} RESET CAUSE SWRF")
        else:
            app.logger.info(f"(507) process_frame_configAll: {dlgid} RESET CAUSE UNKNOWN")

        # Leo la configuracion del datalogger
        d_conf = read_configuration(self.d_args, dlgid)
        # Chequeo la configuracion
        if d_conf is None:
            response = 'CLASS=CONF_ALL&CONFIG=ERROR' 
            status_code = 200
            app.logger.info(f"(503) process_frame_base ERROR: ID={dlgid},RSP=[{response}]")
            return response, status_code
           
        # Actualizo RECOVER UID2ID
        uid = args.get('UID',None)
        update_uid2id(self.d_args, dlgid, uid)

        # Actualizo los parámetros de comunicaciones
        imei = args.get('IMEI',None)
        iccid = args.get('ICCID',None)
        type = args.get('TYPE',None)
        ver = args.get('VER',None)

        #print(f'DEBUG d_args={d_args}')
        _ = update_comms_conf( self.d_args, {'DLGID':dlgid, 'TYPE':type, 'VER':ver, 'UID':uid, 'IMEI':imei, 'ICCID':iccid})

        app.logger.info(f"(507) process_frame_base: {dlgid} TYPE={args.get('TYPE',None)}")
        app.logger.info(f"(508) process_frame_base: {dlgid} VER={args.get('VER',None)}")

        app.logger.info(f"(507) process_frame_base: {dlgid} UID={args.get('UID',None)}")
        app.logger.info(f"(508) process_frame_base: {dlgid} IMEI={args.get('IMEI',None)}")
        app.logger.info(f"(509) process_frame_base: {dlgid} ICCID={args.get('ICCID',None)}")
        app.logger.info(f"(510) process_frame_base: {dlgid} CSQ={args.get('CSQ',None)}")

        debugid = read_debug_id(self.d_args)

        response = 'CLASS=CONF_ALL'
        new_conf = False
        # Calculo el hash de las configuracion de la BD.
        bd_Bhash = self.get_base_hash_from_config(d_conf)
        if dlgid == debugid:
            app.logger.info(f"(504) process_frame_base: ID={dlgid}: BD_Bhash={bd_Bhash}, UI_Bhash={int(args['BH'],16)}")
        if bd_Bhash != int(args['BH'],16):
            response += '&BASE'
            new_conf = True

        bd_Ahash = self.get_ainputs_hash_from_config(d_conf)
        if dlgid == debugid:
            app.logger.info(f"(504) process_frame_base: ID={dlgid}: BD_Ahash={bd_Ahash}, UI_Ahash={int(args['AH'],16)}")
        if bd_Ahash != int(args['AH'],16):
            response += '&AINPUTS'
            new_conf = True

        bd_Chash = self.get_counters_hash_from_config(d_conf)
        if dlgid == debugid:
            app.logger.info(f"(504) process_frame_base: ID={dlgid}: BD_Chash={bd_Chash}, UI_Chash={int(args['CH'],16)}")
        if bd_Chash != int(args['CH'],16):
            response += '&COUNTER'
            new_conf = True

        bd_Mhash = self.get_modbus_hash_from_config(d_conf)
        if dlgid == debugid:
            app.logger.info(f"(504) process_frame_base: ID={dlgid}: BD_Mhash={bd_Mhash}, UI_Mhash={int(args['MH'],16)}")
        if bd_Mhash != int(args['MH'],16):
            response += '&MODBUS'
            new_conf = True

        bd_Phash = self.get_consigna_hash_from_config(d_conf)
        if dlgid == debugid:
            app.logger.info(f"(504) process_frame_base: ID={dlgid}: BD_Phash={bd_Phash}, UI_Phash={int(args['PH'],16)}")
        if bd_Phash != int(args['PH'],16):
            response += '&PRESION'
            new_conf = True

        if not new_conf:
            response += '&CONFIG=OK'

        status_code = 200
        app.logger.info(f"(505) process_frame_base: ID={dlgid},RSP=[{response}]")
        return response, status_code
            
        # No coinciden: mando la nueva configuracion
        response = self.get_response_base(d_conf)
        status_code = 200
        app.logger.info(f"(506) process_frame_base: ID={dlgid},RSP=[{response}]")
        return response, status_code


    ############################################################################################
    # DATA

    def process_frame_data(self, response=True):
        '''
        En esta version debo agregar el WOD 
        ERRORES: 11XX
        '''
        app = self.d_args.get('app',None)

        if self.d_args['debugFlag'] is True:
            app.logger.info("DEBUG: FwdlgxR11X:: process_frame_data")

        # ID=PABLO&TYPE=SPXR3&VER=1.0.0&CLASS=DATA&DATE=230321&TIME=094504&A0=0.00&A1=0.00&A2=0.00&C0=0.000&C1=0.000&bt=12.496
        # ID=SPQTEST&HW=SPQ_AVRDA&TYPE=FWDLGX&VER=1.0.0&CLASS=DATA&DATE=230321&TIME=094504&A0=0.00&A1=0.00&A2=0.00&C0=0.000&C1=0.000&bt=12.496
        # request.args es un dict con todos los pares key:value del url.
        parser = reqparse.RequestParser()
        parser.add_argument('ID', type=str ,location='args', required=True)
        args = parser.parse_args()
        dlgid = args.get('ID',None)
        # El chequeo de errores se hace porque parse_args() aborta y retorna None
        if dlgid is None:
            app.logger.info("(1100) process_frame_data ERROR: No dlgid")
            response = 'ERROR:NO DLGID'
            status_code = 500
            app.logger.info(f"(1101) process_frame_data ERROR: RSP=[{response}]")
            return response, status_code
        
        debugid = read_debug_id(self.d_args)
        d_payload = convert_dataline2dict(request.args)
        
        if d_payload is None:
            return 'ERROR:UNKNOWN VERSION',200

        # 1) Guardo los datos
        r_datos = requests.put(self.d_args['url_redis'] + 'dataline', params={'unit':dlgid,'type':'DLG'}, json=d_payload, timeout=10 )
        if r_datos.status_code != 200:
            # Si da error genero un mensaje pero continuo para no trancar al datalogger.
            app.logger.error(f"(1102) process_frame_data INFO: ID={dlgid},ERROR AL GUARDAR DATA EN REDIS. Err=({r_datos.status_code}){r_datos.text}")
        #

        if response:
        
            # 3) Leo las ordenes
            r_ordenes = requests.get(self.d_args['url_redis'] + 'ordenes', params={'unit':dlgid}, timeout=10 )
            d_ordenes = None
            if r_ordenes.status_code == 200:
                d_ordenes = r_ordenes.json()
                ordenes = d_ordenes.get('ordenes','')
                if dlgid == debugid:
                    app.logger.info(f"(1103) process_frame_data INFO: ID={dlgid}, D_ORDENES={d_ordenes}")
            elif r_ordenes.status_code == 204:
                # Si da error genero un mensaje pero continuo para no trancar al datalogger.
                if dlgid == debugid:
                    app.logger.info(f"(1104) process_frame_data INFO: ID={dlgid},NO HAY RCD ORDENES")
                ordenes = ''
            else:
                app.logger.error(f"(1105) process_frame_data INFO: ID={dlgid},ERROR AL LEER ORDENES. Err=({r_ordenes.status_code}){r_ordenes.text}")
                ordenes = ''
            #
            # 3.1) Si RESET entonces borro la configuracion
            if 'RESET' in ordenes:
                _ = requests.delete(self.d_args['url_redis'] + 'delete', params={'unit':dlgid}, timeout=10 )
                app.logger.info(f"(1106) process_frame_data INFO: ID={dlgid}, DELETE REDIS RCD.")
            #
            # 3.2) Borro las ordenes
            _ = requests.delete(self.d_args['url_redis'] + 'ordenes', params={'unit':dlgid}, timeout=10 )

            # 4) Respondo
            #now=dt.datetime.now().strftime('%y%m%d%H%M')
            now=dt.datetime.now().strftime('%y%m%d%H%M') + str(dt.datetime.now().isoweekday())
            response = f'CLASS=DATA&CLOCK={now};{ordenes}'
            status_code = 200
            app.logger.info(f"(1107) process_frame_data INFO: ID={dlgid},RSP=[{response}]")
            return response, status_code

        else:
            # EMPTY RESPONSE
            return None, 204
        
    ############################################################################################
    # DATA_BULK

    def process_frame_dataBulk(self):
        '''
        ERRORES: 11XX
        Recibimos muchas lineas de datos en el mismo frame
        '''
        app = self.d_args.get('app',None)

        if self.d_args['debugFlag'] is True:
            app.logger.info("DEBUG: FwdlgxR11X:: process_frame_dataBulk")


        # ID=SPQTEST&HW=SPQ_AVRDA&TYPE=FWDLGX&VER=1.0.0&CLASS=DATA
        # &CTL=1&DATE=230321&TIME=094504&A0=0.00&A1=0.00&A2=0.00&C0=0.000&C1=0.000&bt=12.496
        # &CTL=2&DATE=230321&TIME=094504&A0=0.00&A1=0.00&A2=0.00&C0=0.000&C1=0.000&bt=12.496
        # &CTL=3&DATE=230321&TIME=094504&A0=0.00&A1=0.00&A2=0.00&C0=0.000&C1=0.000&bt=12.496
        # &CTL=4&DATE=230321&TIME=094504&A0=0.00&A1=0.00&A2=0.00&C0=0.000&C1=0.000&bt=12.496
        #
        #
        # &CTL=N&DATE=230321&TIME=094504&A0=0.00&A1=0.00&A2=0.00&C0=0.000&C1=0.000&bt=12.496
        # request.args es un dict con todos los pares key:value del url.
        parser = reqparse.RequestParser()
        parser.add_argument('ID', type=str ,location='args', required=True)
        parser.add_argument('HW', type=str ,location='args', required=False)
        parser.add_argument('TYPE', type=str ,location='args', required=False)
        parser.add_argument('VER', type=str ,location='args', required=False)
        args = parser.parse_args()
        dlgid = args.get('ID',None)
        hw = args.get('HW',None)
        type = args.get('TYPE',None)
        ver = args.get('VER',None)

        # El chequeo de errores se hace porque parse_args() aborta y retorna None
        if dlgid is None:
            app.logger.info("(1100) process_frame_data ERROR: No dlgid")
            response = 'ERROR:NO DLGID'
            status_code = 500
            app.logger.info(f"(1101) process_frame_data ERROR: RSP=[{response}]")
            return response, status_code
        
        debugid = read_debug_id(self.d_args)

        #raw_query = request.query_string.decode('utf-8')
        raw_query = self.d_args['qs'].decode('utf-8')
        # Genero una lista con c/linea de datos
        lines = raw_query.split("CTL=")
        lines = lines[1:]

        for line in lines:
            d_payload = convert_line2dict(line)
        
            if d_payload is None:
                return 'ERROR:UNKNOWN VERSION',200

            # 1) Guardo los datos
            r_datos = requests.put(self.d_args['url_redis'] + 'dataline', params={'unit':dlgid,'type':'DLG'}, json=d_payload, timeout=10 )
            if r_datos.status_code != 200:
                # Si da error genero un mensaje pero continuo para no trancar al datalogger.
                app.logger.error(f"(1102) process_frame_data INFO: ID={dlgid},ERROR AL GUARDAR DATA EN REDIS. Err=({r_datos.status_code}){r_datos.text}")
            #
 
        # Al final de procesar todo el bulk, leo las ordenes
        r_ordenes = requests.get(self.d_args['url_redis'] + 'ordenes', params={'unit':dlgid}, timeout=10 )
        d_ordenes = None
        if r_ordenes.status_code == 200:
            d_ordenes = r_ordenes.json()
            ordenes = d_ordenes.get('ordenes','')
            if dlgid == debugid:
                app.logger.info(f"(1103) process_frame_data INFO: ID={dlgid}, D_ORDENES={d_ordenes}")
        elif r_ordenes.status_code == 204:
            # Si da error genero un mensaje pero continuo para no trancar al datalogger.
            if dlgid == debugid:
                app.logger.info(f"(1104) process_frame_data INFO: ID={dlgid},NO HAY RCD ORDENES")
            ordenes = ''
        else:
            app.logger.error(f"(1105) process_frame_data INFO: ID={dlgid},ERROR AL LEER ORDENES. Err=({r_ordenes.status_code}){r_ordenes.text}")
            ordenes = ''
        #
        # 3.1) Si RESET entonces borro la configuracion
        if 'RESET' in ordenes:
            _ = requests.delete(self.d_args['url_redis'] + 'delete', params={'unit':dlgid}, timeout=10 )
            app.logger.info(f"(1106) process_frame_data INFO: ID={dlgid}, DELETE REDIS RCD.")
        #
        # 3.2) Borro las ordenes
        _ = requests.delete(self.d_args['url_redis'] + 'ordenes', params={'unit':dlgid}, timeout=10 )

        # 4) Respondo
        #now=dt.datetime.now().strftime('%y%m%d%H%M')
        now=dt.datetime.now().strftime('%y%m%d%H%M') + str(dt.datetime.now().isoweekday())
        response = f'CLASS=DATA&CLOCK={now};{ordenes}'
        status_code = 200
        app.logger.info(f"(1107) process_frame_data INFO: ID={dlgid},RSP=[{response}]")
        return response, status_code

    ############################################################################################


