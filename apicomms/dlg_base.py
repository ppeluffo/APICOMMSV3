#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python

import datetime as dt
import requests
from flask_restful import reqparse, request
from apidlgR2_utils import read_configuration, update_uid2id, read_debug_id, convert_dataline2dict, update_comms_conf

class Dlg_base:
    '''
    Superclase para procesar todos los modelos de dataloggers 
    y versiones de protocolo
    '''
    def __init__(self):
        #print("DLG BASE")
        self.id = None
    
    def process_frame_ping(self, d_args=None):
        '''
        Los PING son iguales en todos los frames por lo que la implementaicon
        es global.
        ERRORES: 3XX
        '''
        # ID=PABLO&TYPE=SPXR3&VER=1.0.0&CLASS=PING
        response = 'CLASS=PONG'
        status_code = 200
        app = d_args.get('app',None)
        app.logger.info(f"(300) process_frame_ping: ID={self.id},RSP=[{response}]")
        return response, status_code
    
    def process_frame_recover(self, d_args=None):
        '''
        Los RECOVER son iguales para todos las versiones.
        ERRORES: 4XX
        '''
        app = d_args.get('app',None)
        parser = reqparse.RequestParser()
        parser.add_argument('UID', type=str ,location='args', required=True)
        args = parser.parse_args()

        # El chequeo de errores se hace porque parse_args() aborta y retorna None
        uid = args.get('UID',None)
        if uid is None:
            app.logger.info("(400) dlg_base_ERROR: No uid")
            response = 'ERROR:FAIL TO PARSE'
            status_code = 500
            app.logger.info(f"(401) dlg_base_ERROR: RSP=[{response}]")
            return response, status_code
        #
        # Vemos si la redis tiene los datos uid->id
        try:
            r_conf = requests.get( d_args['url_redis'] + 'uid2id', params={'uid':args['UID']}, timeout=10 )
        except requests.exceptions.RequestException as err: 
            app.logger.info(f"(402) dlg_base_ERROR: Redis request exception', Err:{err}")
            response = 'CONFIG=ERROR' 
            status_code = 200
            app.logger.info(f"(403) dlg_base_ERROR: Recoverid Error: UID={args['UID']}: RSP_ERROR=[{response}]")
            return response, status_code
        #
        # Esta en la REDIS...
        if r_conf.status_code == 200:
            d_rsp = r_conf.json()
            new_id = d_rsp['id']
            app.logger.info(f"(404) dlg_base_INFO: Recoverid (uid,id) in REDIS: NEW_ID={new_id}")
            response = f"CLASS=RECOVER&ID={new_id}"
            status_code = 200
            app.logger.info(f"(405) dlg_base_INFO: CLASS=RECOVERID,ID={new_id},RSP=[{response}]")
            return response, status_code
        #

        # No esta en REDIS: buscamos en SQL
        try:
            r_conf = requests.get(d_args['url_conf'] + 'uid2id', params={'uid':args['UID']}, timeout=10 )
        except requests.exceptions.RequestException as err: 
            app.logger.info(f"(406) dlg_base_ERROR: Redis request exception', Err:{err}")
            response = 'CONFIG=ERROR' 
            status_code = 200
            app.logger.info(f"(407) dlg_base_ERROR: UID={uid}: RSP_ERROR=[{response}]")
            return response, status_code
        #
        # Esta en SQL
        if r_conf.status_code == 200:
            d_rsp = r_conf.json()
            new_id = d_rsp['id']
            app.logger.info(f"(408) dlg_base_INFO: Recoverid (uid,id) in SQL: NEW_ID={new_id}")
            response = f"CLASS=RECOVER&ID={new_id}"
            status_code = 200
            app.logger.info(f"(409) dlg_base_INFO: CLASS=RECOVER,ID={new_id},RSP=[{response}]")
            #
            # Actualizo la redis y mando la respuesta al equipo
            d_conf = {'id':new_id,'uid':args['UID']}
            try:
                r_conf = requests.put( d_args['url_conf'] + 'uid2id', json=d_conf, timeout=10 )
            except requests.exceptions.RequestException as err: 
                app.logger.info(f"(410) dlg_base_ERROR: Redis request exception', Err:{err}")
            #
            app.logger.info(f"(411) dlg_base_INFO: Recoverid SQL update Redis: ID={new_id}")
            return response, status_code
        #
        # No estaba en Redis ni SQL
        if r_conf.status_code == 204:
            # No hay datos en la SQL tampoco: Debo salir
            app.logger.info(f"(412) dlg_base_ERROR: UID={uid}, Err:No Rcd en SQL. Err=({r_conf.status_code}){r_conf.text}")
            response = 'CONFIG=ERROR;NO HAY REGISTRO EN BD' 
            status_code = 200
            return response, status_code
        #
        # Error general
        response = 'CONFIG=ERROR' 
        status_code = 200
        app.logger.info(f"(413) dlg_base_INFO: UID={uid}: RSP_ERROR=[{response}]")
        return response, status_code

    def process_frame_base(self, d_args=None):
        '''
        ERRORES: 5XX
        '''
        # ID=PABLO&TYPE=SPXR3&VER=1.0.0&CLASS=CONF_BASE&UID=42125128300065090117010400000000&HASH=0x11
        # ID=SPQTEST&TYPE=SPQ_AVRDA&VER=1.2.3&CLASS=CONF_BASE&UID=42138365900098090136013700000000&IMEI=868191051391785&ICCID=8959801023149326185F&CSQ=51&HASH=0x42

        app = d_args.get('app',None)

        parser = reqparse.RequestParser()
        parser.add_argument('TYPE', type=str ,location='args', required=False)
        parser.add_argument('VER', type=str ,location='args', required=False)
        parser.add_argument('ID', type=str ,location='args', required=True)
        parser.add_argument('UID', type=str ,location='args', required=True)
        parser.add_argument('IMEI', type=str ,location='args', required=False)
        parser.add_argument('ICCID', type=str ,location='args', required=False)
        parser.add_argument('CSQ', type=str ,location='args', required=False)
        parser.add_argument('HASH', type=str ,location='args', required=True)
        args = parser.parse_args()
        dlgid = args.get('ID',None)
        # El chequeo de errores se hace porque parse_args() aborta y retorna None
        if dlgid is None:
            app.logger.info("(500) process_frame_base ERROR: No dlgid")
            response = 'ERROR:NO DLGID'
            status_code = 500
            app.logger.info(f"(501)process_frame_base ERROR: RSP=[{response}]")
            return response, status_code
        
        # Leo la configuracion del datalogger
        d_conf = read_configuration(d_args, dlgid)
        # Chequeo la configuracion
        if d_conf is None:
            response = 'CLASS=CONF_BASE&CONFIG=ERROR' 
            status_code = 200
            app.logger.info(f"(503) process_frame_base ERROR: ID={dlgid},RSP=[{response}]")
            return response, status_code
        
        if 'BASE' not in d_conf.keys():
            app.logger.info("(502) process_frame_base ERROR: NO BASE in keys !!. Default config.")
            #response = 'ERROR: ID MAL CONFIGURADO EN SERVIDOR' 
            #status_code = 200
            #return response, status_code
    
        # Actualizo RECOVER UID2ID
        uid = args.get('UID',None)
        update_uid2id(d_args, dlgid, uid)

        # Actualizo los parámetros de comunicaciones
        imei = args.get('IMEI',None)
        iccid = args.get('ICCID',None)
        type = args.get('TYPE',None)
        ver = args.get('VER',None)

        #print(f'DEBUG d_args={d_args}')
        _ = update_comms_conf( d_args, {'DLGID':dlgid, 'TYPE':type, 'VER':ver, 'UID':uid, 'IMEI':imei, 'ICCID':iccid})

        app.logger.info(f"(507) process_frame_base: {dlgid} TYPE={args.get('TYPE',None)}")
        app.logger.info(f"(508) process_frame_base: {dlgid} VER={args.get('VER',None)}]")

        app.logger.info(f"(507) process_frame_base: {dlgid} UID={args.get('UID',None)}")
        app.logger.info(f"(508) process_frame_base: {dlgid} IMEI={args.get('IMEI',None)}]")
        app.logger.info(f"(509) process_frame_base: {dlgid} ICCID={args.get('ICCID',None)}]")
        app.logger.info(f"(510) process_frame_base: {dlgid} CSQ={args.get('CSQ',None)}]")

        debugid = read_debug_id(d_args)
        # Calculo el hash de la configuracion de la BD.
        bd_hash = self.get_base_hash_from_config(d_conf)
        if dlgid == debugid:
            app.logger.info(f"(504) process_frame_base: ID={dlgid}: BD_hash={bd_hash}, UI_hash={int(args['HASH'],16)}")
        #print(f"DEBUG::__get_conf_base__: bd_hash={bd_hash}, dlg_hash={self.args['HASH']}")
        if bd_hash == int(args['HASH'],16):
            response = 'CLASS=CONF_BASE&CONFIG=OK'
            status_code = 200
            app.logger.info(f"(505) process_frame_base: ID={dlgid},RSP=[{response}]")
            return response, status_code
            
        # No coinciden: mando la nueva configuracion
        response = self.get_response_base(d_conf)
        status_code = 200
        app.logger.info(f"(506) process_frame_base: ID={dlgid},RSP=[{response}]")
        return response, status_code
    
    def process_frame_ainputs(self, d_args=None):
        '''
        ERRORES: 6XX
        '''
        # ID=PABLO&TYPE=SPXR3&VER=1.0.0&CLASS=CONF_AINPUTS&HASH=0x01
        app = d_args.get('app',None)

        parser = reqparse.RequestParser()
        parser.add_argument('ID', type=str ,location='args', required=True)
        parser.add_argument('HASH', type=str ,location='args', required=True)
        args = parser.parse_args()
        dlgid = args.get('ID',None)
        # El chequeo de errores se hace porque parse_args() aborta y retorna None
        if dlgid is None:
            app.logger.info("(600) process_frame_ainputs ERROR: No dlgid")
            response = 'ERROR:NO DLGID'
            status_code = 500
            app.logger.info(f"(601) dprocess_frame_ainputs ERROR: RSP=[{response}]")
            return response, status_code
        
        # Leo la configuracion del datalogger
        d_conf = read_configuration(d_args, dlgid)
        # Chequeo la configuracion
        if d_conf is None:
            response = 'CLASS=CONF_AINPUTS&CONFIG=ERROR' 
            status_code = 200
            app.logger.info(f"(603) process_frame_ainputs ERROR: ID={dlgid},RSP=[{response}]")
            return response, status_code
        
        if 'AINPUTS' not in d_conf.keys():
            app.logger.info("(602) process_frame_ainputs ERROR: NO AINPUTS in keys !!. Default config.")
            #response = 'ERROR: ID MAL CONFIGURADO EN SERVIDOR' 
            #status_code = 200
            #return response, status_code
        
        debugid = read_debug_id(d_args)
        # Calculo el hash de la configuracion de la BD.
        bd_hash = self.get_ainputs_hash_from_config(d_conf)
        if dlgid == debugid:
            app.logger.info(f"(604) process_frame_ainputs INFO: ID={dlgid}: BD_hash={bd_hash}, UI_hash={int(args['HASH'],16)}")

        if bd_hash == int(args['HASH'],16):
            response = 'CLASS=CONF_AINPUTS&CONFIG=OK'
            status_code = 200
            app.logger.info(f"(605) process_frame_ainputs INFO: ID={dlgid},RSP=[{response}]")
            return response, status_code
            
        # No coinciden: mando la nueva configuracion
        response = self.get_response_ainputs(d_conf)
        status_code = 200
        app.logger.info(f"(606) process_frame_ainputs INFO: ID={dlgid},RSP=[{response}]")
        return response, status_code
    
    def process_frame_counters(self, d_args=None):
        '''
        ERRORES: 7XX
        '''
        # ID=PABLO&TYPE=SPXR3&VER=1.0.0&CLASS=CONF_COUNTERS&HASH=0x86
        app = d_args.get('app',None)

        parser = reqparse.RequestParser()
        parser.add_argument('ID', type=str ,location='args', required=True)
        parser.add_argument('HASH', type=str ,location='args', required=True)
        args = parser.parse_args()
        dlgid = args.get('ID',None)
        # El chequeo de errores se hace porque parse_args() aborta y retorna None
        if dlgid is None:
            app.logger.info("(700) process_frame_counters ERROR: No dlgid")
            response = 'ERROR:NO DLGID'
            status_code = 500
            app.logger.info(f"(701) process_frame_counters ERROR: RSP=[{response}]")
            return response, status_code
        
        # Leo la configuracion del datalogger
        d_conf = read_configuration(d_args, dlgid)
        # Chequeo la configuracion
        if d_conf is None:
            response = 'CLASS=CONF_COUNTERS&CONFIG=ERROR' 
            status_code = 200
            app.logger.info(f"(703) process_frame_counters INFO: ID={dlgid},RSP=[{response}]")
            return response, status_code
        
        if 'COUNTERS' not in d_conf.keys():
            app.logger.info("(702) process_frame_counters ERROR: NO COUNTERS in keys !!. Default config.")
            #response = 'ERROR: ID MAL CONFIGURADO EN SERVIDOR' 
            #status_code = 200
            #return response, status_code
        
        debugid = read_debug_id(d_args)
        # Calculo el hash de la configuracion de la BD.
        bd_hash = self.get_counters_hash_from_config(d_conf)
        if dlgid == debugid:
            app.logger.info(f"(704) process_frame_counters INFO: ID={dlgid}: BD_hash={bd_hash}, UI_hash={int(args['HASH'],16)}")

        if bd_hash == int(args['HASH'],16):
            response = 'CLASS=CONF_COUNTERS&CONFIG=OK'
            status_code = 200
            app.logger.info(f"(705) process_frame_counters INFO: ID={dlgid},RSP=[{response}]")
            return response, status_code
            
        # No coinciden: mando la nueva configuracion
        response = self.get_response_counters(d_conf)
        status_code = 200
        app.logger.info(f"(706) process_frame_counters INFO: ID={dlgid},RSP=[{response}]")
        return response, status_code
    
    def process_frame_modbus(self, d_args=None):
        '''
        ERRORES: 8XX
        '''
        # ID=PABLO&TYPE=SPXR3&VER=1.0.0&CLASS=CONF_MODBUS&HASH=0x86
        app = d_args.get('app',None)

        parser = reqparse.RequestParser()
        parser.add_argument('ID', type=str ,location='args', required=True)
        parser.add_argument('HASH', type=str ,location='args', required=True)
        args = parser.parse_args()
        dlgid = args.get('ID',None)
        # El chequeo de errores se hace porque parse_args() aborta y retorna None
        if dlgid is None:
            app.logger.info("(800) process_frame_modbus ERROR: No dlgid")
            response = 'ERROR:NO DLGID'
            status_code = 500
            app.logger.info(f"(801) process_frame_modbus ERROR: RSP=[{response}]")
            return response, status_code
        
        # Leo la configuracion del datalogger
        d_conf = read_configuration(d_args, dlgid)
        # Chequeo la configuracion
        if d_conf is None:
            response = 'CLASS=CONF_MODBUS&CONFIG=ERROR' 
            status_code = 200
            app.logger.info(f"(803) process_frame_modbus INFO: ID={dlgid},RSP=[{response}]")
            return response, status_code
        
        if 'MODBUS' not in d_conf.keys():
            app.logger.info("(802) process_frame_modbus ERROR: NO MODBUS in keys !!. Default config.")
            #response = 'ERROR: ID MAL CONFIGURADO EN SERVIDOR' 
            #status_code = 200
            #return response, status_code
        
        debugid = read_debug_id(d_args)
        # Calculo el hash de la configuracion de la BD.
        bd_hash = self.get_modbus_hash_from_config(d_conf)
        if dlgid == debugid:
            app.logger.info(f"(804) process_frame_modbus INFO: ID={dlgid}: BD_hash={bd_hash}, UI_hash={int(args['HASH'],16)}")

        if bd_hash == int(args['HASH'],16):
            response = 'CLASS=CONF_MODBUS&CONFIG=OK'
            status_code = 200
            app.logger.info(f"(805) process_frame_modbus INFO: ID={dlgid},RSP=[{response}]")
            return response, status_code
            
        # No coinciden: mando la nueva configuracion
        response = self.get_response_modbus(d_conf)
        status_code = 200
        app.logger.info(f"(706) process_frame_modbus INFO: ID={dlgid},RSP=[{response}]")
        return response, status_code
    
    def process_frame_piloto(self, d_args=None):
        '''
        ERRORES: 9XX
        '''
        # ID=PABLO&TYPE=SPXR3&VER=1.0.0&CLASS=CONF_PILOTO&HASH=0x86
        app = d_args.get('app',None)

        parser = reqparse.RequestParser()
        parser.add_argument('ID', type=str ,location='args', required=True)
        parser.add_argument('HASH', type=str ,location='args', required=True)
        args = parser.parse_args()
        dlgid = args.get('ID',None)
        # El chequeo de errores se hace porque parse_args() aborta y retorna None
        if dlgid is None:
            app.logger.info("(900) process_frame_piloto ERROR: No dlgid")
            response = 'ERROR:NO DLGID'
            status_code = 500
            app.logger.info(f"(901) process_frame_piloto ERROR: RSP=[{response}]")
            return response, status_code
        
        # Leo la configuracion del datalogger
        d_conf = read_configuration(d_args, dlgid)
        # Chequeo la configuracion
        if d_conf is None:
            response = 'CLASS=CONF_PILOTO&CONFIG=ERROR' 
            status_code = 200
            app.logger.info(f"(903) process_frame_piloto INFO: ID={dlgid},RSP=[{response}]")
            return response, status_code
        
        if 'PILOTO' not in d_conf.keys():
            app.logger.info("(902) process_frame_piloto ERROR: NO PILOTO in keys !!. Default config.")
            #response = 'ERROR: ID MAL CONFIGURADO EN SERVIDOR' 
            #status_code = 200
            #return response, status_code
        
        debugid = read_debug_id(d_args)
        # Calculo el hash de la configuracion de la BD.
        bd_hash = self.get_piloto_hash_from_config(d_conf)
        if dlgid == debugid:
            app.logger.info(f"(904) process_frame_piloto INFO: ID={dlgid}: BD_hash={bd_hash}, UI_hash={int(args['HASH'],16)}")

        if bd_hash == int(args['HASH'],16):
            response = 'CLASS=CONF_PILOTO&CONFIG=OK'
            status_code = 200
            app.logger.info(f"(905) process_frame_piloto INFO: ID={dlgid},RSP=[{response}]")
            return response, status_code
            
        # No coinciden: mando la nueva configuracion
        response = self.get_response_piloto(d_conf)
        status_code = 200
        app.logger.info(f"(906) process_frame_piloto INFO: ID={dlgid},RSP=[{response}]")
        return response, status_code

    def process_frame_consigna(self, d_args=None):
        '''
        ERRORES: 10XX
        '''
        # ID=PABLO&TYPE=SPXR3&VER=1.0.0&CLASS=CONF_PILOTO&HASH=0x86
        app = d_args.get('app',None)

        parser = reqparse.RequestParser()
        parser.add_argument('ID', type=str ,location='args', required=True)
        parser.add_argument('HASH', type=str ,location='args', required=True)
        args = parser.parse_args()
        dlgid = args.get('ID',None)
        # El chequeo de errores se hace porque parse_args() aborta y retorna None
        if dlgid is None:
            app.logger.info("(1000) process_frame_consigna ERROR: No dlgid")
            response = 'ERROR:NO DLGID'
            status_code = 500
            app.logger.info(f"(1001) process_frame_consigna ERROR: RSP=[{response}]")
            return response, status_code
        
        # Leo la configuracion del datalogger
        d_conf = read_configuration(d_args, dlgid)
        # Chequeo la configuracion
        if d_conf is None:
            response = 'CLASS=CONF_CONSIGNA&CONFIG=ERROR' 
            status_code = 200
            app.logger.info(f"(1003) process_frame_consigna INFO: ID={dlgid},RSP=[{response}]")
            return response, status_code
        
        if 'CONSIGNA' not in d_conf.keys():
            app.logger.info("(1002) process_frame_consigna ERROR: NO CONSIGNA in keys !!. Default config.")
            #response = 'ERROR: ID MAL CONFIGURADO EN SERVIDOR' 
            #status_code = 200
            #return response, status_code
        
        debugid = read_debug_id(d_args)
        # Calculo el hash de la configuracion de la BD.
        bd_hash = self.get_consigna_hash_from_config(d_conf)
        if dlgid == debugid:
            app.logger.info(f"(1004) process_frame_consigna INFO: ID={dlgid}: BD_hash={bd_hash}, UI_hash={int(args['HASH'],16)}")

        if bd_hash == int(args['HASH'],16):
            response = 'CLASS=CONF_CONSIGNA&CONFIG=OK'
            status_code = 200
            app.logger.info(f"(1005) process_frame_consigna INFO: ID={dlgid},RSP=[{response}]")
            return response, status_code
            
        # No coinciden: mando la nueva configuracion
        response = self.get_response_consigna(d_conf)
        status_code = 200
        app.logger.info(f"(1006) process_frame_consigna INFO: ID={dlgid},RSP=[{response}]")
        return response, status_code

    def process_frame_data(self, d_args=None):
        '''
        ERRORES: 11XX
        '''
        app = d_args.get('app',None)

        # ID=PABLO&TYPE=SPXR3&VER=1.0.0&CLASS=DATA&DATE=230321&TIME=094504&A0=0.00&A1=0.00&A2=0.00&C0=0.000&C1=0.000&bt=12.496
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
        
        debugid = read_debug_id(d_args)
        d_payload = convert_dataline2dict(request.args)
        
        if d_payload is None:
            return 'ERROR:UNKNOWN VERSION',200

        # 1) Guardo los datos
        r_datos = requests.put(d_args['url_redis'] + 'dataline', params={'unit':dlgid,'type':'DLG'}, json=d_payload, timeout=10 )
        if r_datos.status_code != 200:
            # Si da error genero un mensaje pero continuo para no trancar al datalogger.
            app.logger.error(f"(1102) process_frame_data INFO: ID={dlgid},ERROR AL GUARDAR DATA EN REDIS. Err=({r_datos.status_code}){r_datos.text}")
        #
        # 3) Leo las ordenes
        r_ordenes = requests.get(d_args['url_redis'] + 'ordenes', params={'unit':dlgid}, timeout=10 )
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
            _ = requests.delete(d_args['url_redis'] + 'delete', params={'unit':dlgid}, timeout=10 )
            app.logger.info(f"(1106) process_frame_data INFO: ID={dlgid}, DELETE REDIS RCD.")
        #
        # 3.2) Borro las ordenes
        _ = requests.delete(d_args['url_redis'] + 'ordenes', params={'unit':dlgid}, timeout=10 )

        # 4) Respondo
        now=dt.datetime.now().strftime('%y%m%d%H%M')
        response = f'CLASS=DATA&CLOCK={now};{ordenes}'
        status_code = 200
        app.logger.info(f"(1107) process_frame_data INFO: ID={dlgid},RSP=[{response}]")
        return response, status_code
    
    ############################################################################################

    def process_frame(self, d_args=None):
        '''
        Metodo global general de procesamiento de frames
        ERRORES: 2XX
        '''
        app = d_args.get('app',None)
        parser = reqparse.RequestParser()
        parser.add_argument('ID', type=str ,location='args', required=True)
        parser.add_argument('CLASS', type=str ,location='args', required=True)
        args = parser.parse_args()
        self.id = args.get('ID',None)
        if self.id is None:
            app.logger.info("(200) dlg_base_ERROR: QS=%(a)s", {'a': d_args['qs'] })
            response = 'ERROR:FAIL TO PARSE'
            status_code = 500
            app.logger.info(f"(201) dlg_base_ERROR: CLASS=PING,ID={self.id},RSP=[{response}]")
            return response, status_code

        # Proceso de acuerdo a la CLASE de frame recibido
        if args['CLASS'] == 'PING':
            return self.process_frame_ping()
            
        if  args['CLASS'] == 'RECOVER':
            return self.process_frame_recover() 
        
        if  args['CLASS'] == 'CONF_BASE':
            return self.process_frame_base()

        if  args['CLASS'] == 'CONF_AINPUTS':
            return self.process_frame_ainputs() 
        
        if  args['CLASS'] == 'CONF_COUNTERS':
            return self.process_frame_counters() 

        if args['CLASS'] == 'CONF_MODBUS':
            return self.process_frame_modbus()

        if args['CLASS'] == 'CONF_PILOTO':
            return self.process_frame_piloto()

        if args['CLASS'] == 'CONF_CONSIGNA':
            return self.process_frame_consigna()
        
        if args['CLASS'] == 'DATA':
            return self.process_frame_data()
        
        # Catch all errors
        response = 'FAIL'
        status_code = 501
        return (response, status_code)
    
 