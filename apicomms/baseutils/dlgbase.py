#!/home/pablo/Spymovil/python/proyectos/APICOMMS/venv/bin/python
"""
"""
import datetime as dt
import requests
from flask_restful import reqparse, request
from baseutils.baseutils import read_configuration, update_uid2id, read_debug_id, convert_dataline2dict, update_comms_conf
from baseutils.baseutils import str2int, u_hash

class Dlgbase:
    '''
    Superclase para procesar todos los modelos de dataloggers 
    y versiones de protocolo
    '''
    def __init__(self, d_args=None):
        self.id = None
        self.d_args = d_args

    ############################################################################################
    # PING
    
    def process_frame_ping(self):
        '''
        Los PING son iguales en todos los frames por lo que la implementaicon
        es global.
        ERRORES: 3XX
        '''
        # ID=PABLO&TYPE=SPXR3&VER=1.0.0&CLASS=PING
        response = 'CLASS=PONG'
        status_code = 200
        app = self.d_args.get('app',None)
        app.logger.info(f"(300) process_frame_ping: ID={self.id},RSP=[{response}]")
        return response, status_code
    
    ############################################################################################
    # BASE

    def get_base_hash_from_config(self, d_conf=None):
        '''
        Calculo el hash para la todas las versiones
        '''
        xhash = 0
        timerpoll = str2int(d_conf.get('BASE',{}).get('TPOLL','0'))
        timerdial = str2int(d_conf.get('BASE',{}).get('TDIAL','0'))
        pwr_modo = str2int(d_conf.get('BASE',{}).get('PWRS_MODO','0'))
        pwr_hhmm_on = str2int(d_conf.get('BASE',{}).get('PWRS_HHMM1','601'))
        pwr_hhmm_off = str2int(d_conf.get('BASE',{}).get('PWRS_HHMM2','2201'))
        #
        hash_str = f'[TIMERPOLL:{timerpoll:03d}]'
        xhash = u_hash(xhash, hash_str)
        #print(f'DEBUG::get_hash_config_base: hash_str={hash_str}, xhash={xhash}')
        #
        hash_str = f'[TIMERDIAL:{timerdial:03d}]'
        xhash = u_hash(xhash, hash_str)
        #print(f'DEBUG::get_hash_config_base: hash_str={hash_str}, xhash={xhash}')
        #
        hash_str = f'[PWRMODO:{pwr_modo}]'
        xhash = u_hash(xhash, hash_str)
        #print(f'DEBUG::get_hash_config_base: hash_str={hash_str}, xhash={xhash}')
        #
        hash_str = f'[PWRON:{pwr_hhmm_on:04}]'
        xhash = u_hash(xhash, hash_str)
        #print(f'DEBUG::get_hash_config_base: hash_str={hash_str}, xhash={xhash}')
        #
        hash_str = f'[PWROFF:{pwr_hhmm_off:04}]'
        xhash = u_hash(xhash, hash_str)
        #print(f'DEBUG::get_hash_config_base: hash_str={hash_str}, xhash={xhash}')
        #
        samples = str2int(d_conf.get('BASE',{}).get('SAMPLES','1'))
        almlevel = str2int(d_conf.get('BASE',{}).get('ALMLEVEL','0'))
        hash_str = f'[SAMPLES:{samples:02}]'
        xhash = u_hash(xhash, hash_str)
        #print(f'DEBUG::get_hash_config_base: hash_str={hash_str}, xhash={xhash}')
        #
        hash_str = f'[ALMLEVEL:{almlevel:02}]'
        xhash = u_hash(xhash, hash_str)
        #print(f'DEBUG::get_hash_config_base: hash_str={hash_str}, xhash={xhash}')
        #
        #print(f'DEBUG::get_hash_config_base: xhash={xhash}')
        return xhash
    
    def get_response_base(self, d_conf=None):
        '''
        Armo la respuesta para todas las versiones
        '''
        timerpoll = str2int( d_conf.get('BASE',{}).get('TPOLL','0'))
        #print(f'DEBUG::timerpoll={timerpoll}')
        timerdial = str2int(d_conf.get('BASE',{}).get('TDIAL','0'))
        #print(f'DEBUG::timerdial={timerdial}')
        pwr_modo = str2int(d_conf.get('BASE',{}).get('PWRS_MODO','0'))
        pwr_hhmm_on = str2int(d_conf.get('BASE',{}).get('PWRS_HHMM1','600'))
        pwr_hhmm_off = str2int(d_conf.get('BASE',{}).get('PWRS_HHMM2','2200'))
        if pwr_modo == 0:
            s_pwrmodo = 'CONTINUO'
        elif pwr_modo == 1:
            s_pwrmodo = 'DISCRETO'
        else:
            s_pwrmodo = 'MIXTO'
        #
        samples = str2int( d_conf.get('BASE',{}).get('SAMPLES','1'))
        almlevel = str2int( d_conf.get('BASE',{}).get('ALMLEVEL','0'))
        #
        response = 'CLASS=CONF_BASE&'
        response += f'TPOLL={timerpoll}&TDIAL={timerdial}&PWRMODO={s_pwrmodo}&PWRON={pwr_hhmm_on:04}&PWROFF={pwr_hhmm_off:04}'
        response += f'&SAMPLES={samples}&ALMLEVEL={almlevel}'
        #print(f'DEBUG::response={response}')
        return response
    
    def process_frame_base(self):
        '''
        ERRORES: 5XX
        '''
        # ID=PABLO&TYPE=SPXR3&VER=1.0.0&CLASS=CONF_BASE&UID=42125128300065090117010400000000&HASH=0x11
        # ID=SPQTEST&TYPE=SPQ_AVRDA&VER=1.2.3&CLASS=CONF_BASE&UID=42138365900098090136013700000000&IMEI=868191051391785&ICCID=8959801023149326185F&CSQ=51&HASH=0x42

        app = self.d_args.get('app',None)

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
        d_conf = read_configuration(self.d_args, dlgid)
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

    ############################################################################################
    # AINPUTS

    def get_ainputs_hash_from_config(self, d_conf=None):
        '''
        Calculo el hash para todas las versiones
        '''
        xhash = 0
        for channel in ['A0','A1','A2']:
            enable = d_conf.get('AINPUTS',{}).get(channel,{}).get('ENABLE','FALSE')
            name = d_conf.get('AINPUTS',{}).get(channel,{}).get('NAME','X')
            imin = str2int( d_conf.get('AINPUTS',{}).get(channel,{}).get('IMIN','0'))
            imax = str2int( d_conf.get('AINPUTS',{}).get(channel,{}).get('IMAX','0'))
            mmin = float( d_conf.get('AINPUTS',{}).get(channel,{}).get('MMIN','0'))
            mmax = float( d_conf.get('AINPUTS',{}).get(channel,{}).get('MMAX','0'))
            offset = float( d_conf.get('AINPUTS',{}).get(channel,{}).get('OFFSET','0'))
            hash_str = f'[{channel}:{enable},{name},{imin},{imax},{mmin:.02f},{mmax:.02f},{offset:.02f}]'
            xhash = u_hash(xhash, hash_str)
            #print(f'DEBUG::get_hash_config_ainputs: hash_str={hash_str}, xhash={xhash}')
        return xhash
 
    def get_response_ainputs(self, d_conf=None):
        '''
        Armo la respuesta para todas las versiones
        '''
        response = 'CLASS=CONF_AINPUTS&'
        for channel in ['A0','A1','A2']:
            enable = d_conf.get('AINPUTS',{}).get(channel,{}).get('ENABLE', 'FALSE')
            name = d_conf.get('AINPUTS',{}).get(channel,{}).get('NAME', 'X')
            imin = str2int(d_conf.get('AINPUTS',{}).get(channel,{}).get('IMIN', '4'))
            imax = str2int(d_conf.get('AINPUTS',{}).get(channel,{}).get('IMAX', '20'))
            mmin = float(d_conf.get('AINPUTS',{}).get(channel,{}).get('MMIN', 0.00))
            mmax = float(d_conf.get('AINPUTS',{}).get(channel,{}).get('MMAX', 10.00))
            offset = float(d_conf.get('AINPUTS',{}).get(channel,{}).get('OFFSET', 0.00))
            response += f'{channel}={enable},{name},{imin},{imax},{mmin},{mmax},{offset}&'
        #
        response = response[:-1]
        return response

    def process_frame_ainputs(self):
        '''
        ERRORES: 6XX
        '''
        # ID=PABLO&TYPE=SPXR3&VER=1.0.0&CLASS=CONF_AINPUTS&HASH=0x01
        app = self.d_args.get('app',None)

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
        d_conf = read_configuration(self.d_args, dlgid)
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
        
        debugid = read_debug_id(self.d_args)
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
    
    ############################################################################################
    # COUNTERS

    def get_counters_hash_from_config(self, d_conf=None):
        '''
        Calculo el hash para todas las versiones
        Los SPQ tienen un solo contador y no usan ringbuffer
        '''
        xhash = 0
        for channel in ['C0']:
            enable = d_conf.get('COUNTERS',{}).get(channel,{}).get('ENABLE','FALSE')
            name = d_conf.get('COUNTERS',{}).get(channel,{}).get('NAME','X')
            modo = d_conf.get('COUNTERS',{}).get(channel,{}).get('MODO','CAUDAL')
            magpp = float(d_conf.get('COUNTERS',{}).get(channel,{}).get('MAGPP','0'))
            #rbsize = str2int(d_conf.get('COUNTERS',{}).get(channel,{}).get('RBSIZE','1'))
            #hash_str = f'[{channel}:{enable},{name},{magpp:.03f},{modo},{rbsize}]'
            hash_str = f'[{channel}:{enable},{name},{magpp:.03f},{modo}]'
            xhash = u_hash(xhash, hash_str)
            #print(f'DEBUG HASH COUNTERS: hash_str={hash_str}')
        #
        #print(f'DEBUG HASH COUNTERS: hash={xhash}')
        return xhash

    def get_response_counters(self, d_conf=None):
        '''
        Armo la respuesta para todas las versiones
        Los SPQ tienen un solo contador y no usan ringbuffer
        '''
        response = 'CLASS=CONF_COUNTERS&'
        for channel in ['C0']:
            enable = d_conf.get('COUNTERS',{}).get(channel,{}).get('ENABLE','FALSE')
            name = d_conf.get('COUNTERS',{}).get(channel,{}).get('NAME', 'X')
            magpp = float(d_conf.get('COUNTERS',{}).get(channel,{}).get('MAGPP', 1.00))
            str_modo = d_conf.get('COUNTERS',{}).get(channel,{}).get('MODO','CAUDAL')
            #rbsize = str2int(d_conf.get('COUNTERS',{}).get(channel,{}).get('RBSIZE','1'))
            #response += f'{channel}={enable},{name},{magpp},{str_modo},{rbsize}&'
            response += f'{channel}={enable},{name},{magpp},{str_modo}&'
        #
        response = response[:-1]
        return response

    def process_frame_counters(self):
        '''
        ERRORES: 7XX
        '''
        # ID=PABLO&TYPE=SPXR3&VER=1.0.0&CLASS=CONF_COUNTERS&HASH=0x86
        app = self.d_args.get('app',None)

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
        d_conf = read_configuration(self.d_args, dlgid)
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
        
        debugid = read_debug_id(self.d_args)
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

    ############################################################################################
    # MODBUS

    def get_modbus_hash_from_config(self, d_conf=None):
        '''
        Calculo el hash para todas las versiones
        '''
        xhash = 0
        enable = d_conf.get('MODBUS',{}).get('ENABLE','FALSE')
        localaddr = str2int(d_conf.get('MODBUS',{}).get('LOCALADDR','1'))
        hash_str = f'[{enable},{localaddr:02d}]'
        xhash = u_hash(xhash, hash_str)
        #print(f'DEBUG HASH MODBUS: hash_str={hash_str}{xhash}')
        #,
        for channel in ['M0','M1','M2','M3','M4']:
            enable = d_conf.get('MODBUS',{}).get(channel,{}).get('ENABLE','FALSE')
            name = d_conf.get('MODBUS',{}).get(channel,{}).get('NAME','X')
            sla_addr = str2int(d_conf.get('MODBUS',{}).get(channel,{}).get('SLA_ADDR','0'))
            reg_addr = str2int(d_conf.get('MODBUS',{}).get(channel,{}).get('ADDR','0'))
            nro_regs = str2int(d_conf.get('MODBUS',{}).get(channel,{}).get('NRO_RECS','0'))
            fcode = str2int(d_conf.get('MODBUS',{}).get(channel,{}).get('FCODE','0'))
            mtype = d_conf.get('MODBUS',{}).get(channel,{}).get('TYPE','U16')
            codec = d_conf.get('MODBUS',{}).get(channel,{}).get('CODEC','C0123')
            pow10 = str2int(d_conf.get('MODBUS',{}).get(channel,{}).get('POW10','0'))
            hash_str = f'[{channel}:{enable},{name},{sla_addr:02d},{reg_addr:04d},{nro_regs:02d},{fcode:02d},{mtype},{codec},{pow10:02d}]'
            xhash = u_hash(xhash, hash_str)
            #print(f'DEBUG HASH MODBUS: hash_str={hash_str}{xhash}')
        #
        return xhash
    
    def get_response_modbus(self, d_conf=None):
        '''
        Armo la respuesta para todas las versiones
        '''
        enable = d_conf.get('MODBUS',{}).get('ENABLE','FALSE')
        localaddr = str2int(d_conf.get('MODBUS',{}).get('LOCALADDR','0x01'))

        response = f'CLASS=CONF_MODBUS&ENABLE={enable}&LOCALADDR={localaddr}&'

        for channel in ['M0','M1','M2','M3','M4']:
            enable = d_conf.get('MODBUS',{}).get(channel,{}).get('ENABLE','FALSE')
            name = d_conf.get('MODBUS',{}).get(channel,{}).get('NAME','X')
            sla_addr = str2int(d_conf.get('MODBUS',{}).get(channel,{}).get('SLA_ADDR','0'))
            reg_addr = str2int(d_conf.get('MODBUS',{}).get(channel,{}).get('ADDR','0'))
            nro_regs = str2int(d_conf.get('MODBUS',{}).get(channel,{}).get('NRO_RECS','0'))
            fcode = str2int(d_conf.get('MODBUS',{}).get(channel,{}).get('FCODE','0'))
            mtype = d_conf.get('MODBUS',{}).get(channel,{}).get('TYPE','U16')
            codec = d_conf.get('MODBUS',{}).get(channel,{}).get('CODEC','C0123')
            pow10 = str2int(d_conf.get('MODBUS',{}).get(channel,{}).get('POW10','0'))
            response += f'{channel}={enable},{name},{sla_addr},{reg_addr},{nro_regs},{fcode},{mtype},{codec},{pow10}&'
        #
        response = response[:-1]
        return response

    def process_frame_modbus(self):
        '''
        ERRORES: 8XX
        '''
        # ID=PABLO&TYPE=SPXR3&VER=1.0.0&CLASS=CONF_MODBUS&HASH=0x86
        app = self.d_args.get('app',None)

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
        d_conf = read_configuration(self.d_args, dlgid)
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
        
        debugid = read_debug_id(self.d_args)
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
    

    ############################################################################################
    # CONSIGNA

    def get_consigna_hash_from_config(self, d_conf=None):
        '''
        Calculo el hash para todas las versiones
        '''
        xhash = 0
        #print(f'DEBUG D_CONF_CONSIGNA={self.d_local_conf}')
        enable = d_conf.get('CONSIGNA',{}).get('ENABLE','FALSE')
        c_diurna = str2int( d_conf.get('CONSIGNA',{}).get('DIURNA','630'))
        c_nocturna = str2int( d_conf.get('CONSIGNA',{}).get('NOCTURNA','2330'))
        hash_str = f'[{enable},{c_diurna:04d},{c_nocturna:04d}]'
        xhash = u_hash(xhash, hash_str)
        #print(f'DEBUG HASH CONSIGNA: hash_str={hash_str}{xhash}')
        return xhash
    
    def get_response_consigna(self, d_conf=None):
        '''
        Armo la respuesta para todas las versiones
        '''
        enable =  d_conf.get('CONSIGNA',{}).get('ENABLE','FALSE')
        c_diurna =  d_conf.get('CONSIGNA',{}).get('DIURNA','630')
        c_nocturna =  d_conf.get('CONSIGNA',{}).get('NOCTURNA','2330')
        response = f'CLASS=CONF_CONSIGNA&ENABLE={enable}&DIURNA={c_diurna}&NOCTURNA={c_nocturna}'
        return response
    
    def process_frame_consigna(self):
        '''
        ERRORES: 10XX
        '''
        # ID=PABLO&TYPE=SPXR3&VER=1.0.0&CLASS=CONF_PILOTO&HASH=0x86
        app = self.d_args.get('app',None)

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
        d_conf = read_configuration(self.d_args, dlgid)
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
        
        debugid = read_debug_id(self.d_args)
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

    ############################################################################################
    # PILOTO

    def get_piloto_hash_from_config(self, d_conf=None):
        '''
        Calculo el hash para todas las versiones
        '''
        xhash = 0
        #print(f'DEBUG D_CONF_PILOTO={self.d_local_conf}')
        enable = d_conf.get('PILOTO',{}).get('ENABLE','FALSE')
        ppr = str2int(d_conf.get('PILOTO',{}).get('PPR','1000'))
        pwidth = str2int(d_conf.get('PILOTO',{}).get('PWIDTH','10'))
        hash_str = f'[{enable},{ppr:04d},{pwidth:02d}]'
        xhash = u_hash(xhash, hash_str)
        #print(f'DEBUG HASH PILOTO: hash_str={hash_str}{xhash}')
        #
        for channel in range(12):
            slot_name = f'SLOT{channel}'
            presion = float( d_conf.get('PILOTO',{}).get(slot_name,{}).get('PRES','0.0'))
            timeslot = str2int( d_conf.get('PILOTO',{}).get(slot_name,{}).get('TIME','0000'))
            hash_str = f'[S{channel:02d}:{timeslot:04d},{presion:0.2f}]'
            xhash = u_hash(xhash, hash_str)
            #print(f'DEBUG HASH PILOTO: hash_str={hash_str}{xhash}')
        # 
        return xhash

    def get_response_piloto(self, d_conf=None):
        '''
        Armo la respuesta para todas las versiones
        '''
        enable = d_conf.get('PILOTO',{}).get('ENABLE','FALSE')
        ppr = str2int(d_conf.get('PILOTO',{}).get('PPR','1000'))
        pwidth = str2int(d_conf.get('PILOTO',{}).get('PWIDTH','10'))
        response = f'CLASS=CONF_PILOTO&ENABLE={enable}&PULSEXREV={ppr}&PWIDTH={pwidth}&'
        #
        for channel in range(12):
            slot_name = f'SLOT{channel}'
            presion = float( d_conf.get('PILOTO',{}).get(slot_name,{}).get('PRES','0.0'))
            timeslot = str2int( d_conf.get('PILOTO',{}).get(slot_name,{}).get('TIME','0000'))
            response += f'S{channel}={timeslot:04d},{presion:0.2f}&'
        #
        response = response[:-1]
        return response

    def process_frame_piloto(self):
        '''
        ERRORES: 9XX
        '''
        # ID=PABLO&TYPE=SPXR3&VER=1.0.0&CLASS=CONF_PILOTO&HASH=0x86
        app = self.d_args.get('app',None)

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
        d_conf = read_configuration(self.d_args, dlgid)
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
        
        debugid = read_debug_id(self.d_args)
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

    ############################################################################################
    # DATA

    def process_frame_data(self, response=True):
        '''
        ERRORES: 11XX
        '''
        app = self.d_args.get('app',None)

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
            now=dt.datetime.now().strftime('%y%m%d%H%M')
            response = f'CLASS=DATA&CLOCK={now};{ordenes}'
            status_code = 200
            app.logger.info(f"(1107) process_frame_data INFO: ID={dlgid},RSP=[{response}]")
            return response, status_code

        else:
            # EMPTY RESPONSE
            return None, 204

    ############################################################################################

    def process_frame(self):
        '''
        Metodo global general de procesamiento de frames
        ERRORES: 2XX
        '''
        app = self.d_args.get('app',None)
        parser = reqparse.RequestParser()
        parser.add_argument('ID', type=str ,location='args', required=True)
        parser.add_argument('CLASS', type=str ,location='args', required=True)
        args = parser.parse_args()
        self.id = args.get('ID',None)
        if self.id is None:
            app.logger.info("(200) dlg_base_ERROR: QS=%(a)s", {'a': self.d_args['qs'] })
            response = 'ERROR:FAIL TO PARSE'
            status_code = 500
            app.logger.info(f"(201) dlg_base_ERROR: CLASS=PING,ID={self.id},RSP=[{response}]")
            return response, status_code

        # Proceso de acuerdo a la CLASE de frame recibido
        if args['CLASS'] == 'PING':
            return self.process_frame_ping()       
        
        if args['CLASS'] == 'CONF_BASE':
            return self.process_frame_base()
        
        if args['CLASS'] == 'CONF_AINPUTS':
            return self.process_frame_ainputs()
        
        if args['CLASS'] == 'CONF_COUNTERS':
            return self.process_frame_counters()
        
        if args['CLASS'] == 'CONF_MODBUS':
            return self.process_frame_modbus()
        
        if args['CLASS'] == 'CONF_CONSIGNA':
            return self.process_frame_consigna()
        
        if args['CLASS'] == 'CONF_PILOTO':
            return self.process_frame_piloto()
        
        if args['CLASS'] == 'DATA':
            return self.process_frame_data()

        if args['CLASS'] == 'CONF_ALL':
            return self.process_frame_configAll()

        if args['CLASS'] == 'DATANR':
            return self.process_frame_dataBulk()   
        
        
        # Catch all errors
        response = 'FAIL'
        status_code = 501
        return (response, status_code)
    
    
