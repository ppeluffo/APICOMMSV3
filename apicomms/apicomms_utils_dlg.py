#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python
'''
Clase especializada en utilidades de frames de dataloggers version SPXR3
'''

import re
import requests
import datetime as dt
import json

APIREDIS_HOST = 'appredis'
APIREDIS_PORT = '5100'

class dlgutils:

    def __init__(self, d_conf):
        self.d_local_conf = None
        self.ifw_ver = 0
        self.D_API_CONF = d_conf

    def u_hash( self, seed, line ):
        '''
        Calculo un hash con el string pasado en line.
        Devuelve un entero
        Se utiliza el algoritmo de Pearson
        https://es.abcdef.wiki/wiki/Pearson_hashing
        La función original usa una tabla de nros.aleatorios de 256 elementos.
	    Ya que son aleatorios, yo la modifico a algo mas simple.

        Es la misma implementacion que se usa en los dataloggers.
        '''

        hash_table = [ 93,  153, 124,  98, 233, 146, 184, 207, 215,  54, 208, 223, 254, 216, 162, 141,
		     10,  148, 232, 115,   7, 202,  66,  31,   1,  33,  51, 145, 198, 181,  13,  95,
		    242, 110, 107, 231, 140, 170,  44, 176, 166,   8,   9, 163, 150, 105, 113, 149,
		    171, 152,  58, 133, 186,  27,  53, 111, 210,  96,  35, 240,  36, 168,  67, 213,
		     12,  123, 101, 227, 182, 156, 190, 205, 218, 139,  68, 217,  79,  16, 196, 246,
		    154, 116,  29, 131, 197, 117, 127,  76,  92,  14,  38,  99,   2, 219, 192, 102,
		    252,  74,  91, 179,  71, 155,  84, 250, 200, 121, 159,  78,  69,  11,  63,   5,
		    126, 157, 120, 136, 185,  88, 187, 114, 100, 214, 104, 226,  40, 191, 194,  50,
		    221, 224, 128, 172, 135, 238,  25, 212,   0, 220, 251, 142, 211, 244, 229, 230,
		    46,   89, 158, 253, 249,  81, 164, 234, 103,  59,  86, 134,  60, 193, 109,  77,
		    180, 161, 119, 118, 195,  82,  49,  20, 255,  90,  26, 222,  39,  75, 243, 237,
		    17,   72,  48, 239,  70,  19,   3,  65, 206,  32, 129,  57,  62,  21,  34, 112,
		    4,    56, 189,  83, 228, 106,  61,   6,  24, 165, 201, 167, 132,  45, 241, 247,
		    97,   30, 188, 177, 125,  42,  18, 178,  85, 137,  41, 173,  43, 174,  73, 130,
		    203, 236, 209, 235,  15,  52,  47,  37,  22, 199, 245,  23, 144, 147, 138,  28,
		    183,  87, 248, 160,  55,  64, 204,  94, 225, 143, 175, 169,  80, 151, 108, 122 ]

        h = seed
        for c in line:
            h = hash_table[h ^ ord(c)]
        return h

    def version2int (self, str_version):
        '''
        VER tiene un formato tipo A.B.C.
        Lo convertimos a un numero A*100 + B*10 + C
        '''
        return int(re.sub(r"[A-Z,a-z,.]",'',str_version))

    def get_hash_config_base(self, d_conf, fw_ver):
        '''
        Calcula el hash de la configuracion base.
        RETURN: int
        '''
        self.d_local_conf = d_conf
        self.ifw_ver = self.version2int( fw_ver)
        #
        if self.ifw_ver == 110:
            return self.__get_hash_config_base_V110__()
        else:
            print("ERROR: Version no soportada")
            return -1
    
    def __get_hash_config_base_V110__(self):
        '''
        Calculo el hash para la versión 110
        '''
        xhash = 0
        timerpoll = int(self.d_local_conf.get('BASE',{}).get('TPOLL','0'))
        timerdial = int(self.d_local_conf.get('BASE',{}).get('TDIAL','0'))
        pwr_modo = int(self.d_local_conf.get('BASE',{}).get('PWRS_MODO','0'))
        pwr_hhmm_on = int(self.d_local_conf.get('BASE',{}).get('PWRS_HHMM1','601'))
        pwr_hhmm_off = int(self.d_local_conf.get('BASE',{}).get('PWRS_HHMM2','2201'))
        #
        hash_str = f'[TIMERPOLL:{timerpoll:03d}]'
        xhash = self.u_hash(xhash, hash_str)
        #print(f'DEBUG::get_hash_config_base: hash_str={hash_str}, xhash={xhash}')
        #
        hash_str = f'[TIMERDIAL:{timerdial:03d}]'
        xhash = self.u_hash(xhash, hash_str)
        #print(f'DEBUG::get_hash_config_base: hash_str={hash_str}, xhash={xhash}')
        #
        hash_str = f'[PWRMODO:{pwr_modo}]'
        xhash = self.u_hash(xhash, hash_str)
        #print(f'DEBUG::get_hash_config_base: hash_str={hash_str}, xhash={xhash}')
        #
        hash_str = f'[PWRON:{pwr_hhmm_on:04}]'
        xhash = self.u_hash(xhash, hash_str)
        #print(f'DEBUG::get_hash_config_base: hash_str={hash_str}, xhash={xhash}')
        #
        hash_str = f'[PWROFF:{pwr_hhmm_off:04}]'
        xhash = self.u_hash(xhash, hash_str)
        #print(f'DEBUG::get_hash_config_base: hash_str={hash_str}, xhash={xhash}')
        #
        samples = int(self.d_local_conf.get('BASE',{}).get('SAMPLES','1'))
        almlevel = int(self.d_local_conf.get('BASE',{}).get('ALMLEVEL','0'))
        hash_str = f'[SAMPLES:{samples:02}]'
        xhash = self.u_hash(xhash, hash_str)
        #print(f'DEBUG::get_hash_config_base: hash_str={hash_str}, xhash={xhash}')
        #
        hash_str = f'[ALMLEVEL:{almlevel:02}]'
        xhash = self.u_hash(xhash, hash_str)
        #print(f'DEBUG::get_hash_config_base: hash_str={hash_str}, xhash={xhash}')
        #
        #print(f'DEBUG::get_hash_config_base: xhash={xhash}')
        return xhash

    def get_response_base(self, d_conf, fw_ver):
        '''
        Calcula la respuesta de configuracion base
        RETURN: string
        '''
        #
        self.d_local_conf = d_conf
        self.ifw_ver = self.version2int( fw_ver)
        #
        if self.ifw_ver == 110:
            return self.__get_response_base_V110__()
        print("ERROR: Version no soportada")
        return 'ERROR:UNKNOWN VERSION'

    def __get_response_base_V110__(self):
        '''
        '''
        timerpoll = int( self.d_local_conf.get('BASE',{}).get('TPOLL','0'))
        timerdial = int(self.d_local_conf.get('BASE',{}).get('TDIAL','0'))
        pwr_modo = int(self.d_local_conf.get('BASE',{}).get('PWRS_MODO','0'))
        pwr_hhmm_on = int(self.d_local_conf.get('BASE',{}).get('PWRS_HHMM1','600'))
        pwr_hhmm_off = int(self.d_local_conf.get('BASE',{}).get('PWRS_HHMM2','2200'))
        if pwr_modo == 0:
            s_pwrmodo = 'CONTINUO'
        elif pwr_modo == 1:
            s_pwrmodo = 'DISCRETO'
        else:
            s_pwrmodo = 'MIXTO'
        #
        samples = int( self.d_local_conf.get('BASE',{}).get('SAMPLES','1'))
        almlevel = int( self.d_local_conf.get('BASE',{}).get('ALMLEVEL','0'))
        #
        response = 'CLASS=CONF_BASE&'
        response += f'TPOLL={timerpoll}&TDIAL={timerdial}&PWRMODO={s_pwrmodo}&PWRON={pwr_hhmm_on:04}&PWROFF={pwr_hhmm_off:04}'
        response += f'&SAMPLES={samples}&ALMLEVEL={almlevel}'  
        return response
    
    def get_hash_config_ainputs(self, d_conf, fw_ver):
        '''
        Calcula el hash de la configuracion de canales analoggicos.
        RETURN: int
        '''
        #
        self.d_local_conf = d_conf
        self.ifw_ver = self.version2int( fw_ver)
        #
        if self.ifw_ver == 110:
            return self.__get_hash_config_ainputs_V110__()
        else:
            print("ERROR: Version no soportada")
            return -1
    
    def __get_hash_config_ainputs_V110__(self):
        '''
        '''
        xhash = 0
        for channel in ['A0','A1','A2']:
            enable = self.d_local_conf.get('ANALOGS',{}).get(channel,{}).get('ENABLE','FALSE')
            name = self.d_local_conf.get('ANALOGS',{}).get(channel,{}).get('NAME','X')
            imin=int( self.d_local_conf.get('ANALOGS',{}).get(channel,{}).get('IMIN','0'))
            imax=int( self.d_local_conf.get('ANALOGS',{}).get(channel,{}).get('IMAX','0'))
            mmin=float( self.d_local_conf.get('ANALOGS',{}).get(channel,{}).get('MMIN','0'))
            mmax=float( self.d_local_conf.get('ANALOGS',{}).get(channel,{}).get('MMAX','0'))
            offset=float( self.d_local_conf.get('ANALOGS',{}).get(channel,{}).get('OFFSET','0'))
            hash_str = f'[{channel}:{enable},{name},{imin},{imax},{mmin:.02f},{mmax:.02f},{offset:.02f}]'
            xhash = self.u_hash(xhash, hash_str)
            #print(f'DEBUG::get_hash_config_ainputs: hash_str={hash_str}, xhash={xhash}')
        return xhash
    
    def get_response_ainputs(self, d_conf, fw_ver):
        '''
        Calcula la respuesta de configuracion de canales analogicos
        '''
        #
        self.d_local_conf = d_conf
        self.ifw_ver = self.version2int( fw_ver)
        #
        if self.ifw_ver == 110:
            return self.__get_response_ainputs_V110__()
        print("ERROR: Version no soportada")
        return 'ERROR:UNKNOWN VERSION'
 
    def __get_response_ainputs_V110__(self):
        '''
        '''
        response = 'CLASS=CONF_AINPUTS&'
        for channel in ['A0','A1','A2']:
            enable = self.d_local_conf.get('ANALOGS',{}).get(channel,{}).get('ENABLE', 'FALSE')
            name = self.d_local_conf.get('ANALOGS',{}).get(channel,{}).get('NAME', 'X')
            imin = int(self.d_local_conf.get('ANALOGS',{}).get(channel,{}).get('IMIN', 4))
            imax = int(self.d_local_conf.get('ANALOGS',{}).get(channel,{}).get('IMAX', 20))
            mmin = float(self.d_local_conf.get('ANALOGS',{}).get(channel,{}).get('MMIN', 0.00))
            mmax = float(self.d_local_conf.get('ANALOGS',{}).get(channel,{}).get('MMAX', 10.00))
            offset = float(self.d_local_conf.get('ANALOGS',{}).get(channel,{}).get('OFFSET', 0.00))
            response += f'{channel}={enable},{name},{imin},{imax},{mmin},{mmax},{offset}&'
        #
        response = response[:-1]
        return response
        
    def get_hash_config_counters(self, d_conf, fw_ver):
        '''
        Calcula el hash de la configuracion de canales digitales ( contadores ).
        RETURN: int
        '''
        #
        self.d_local_conf = d_conf
        self.ifw_ver = self.version2int( fw_ver)
        #
        if self.ifw_ver == 110:
            return self.__get_hash_config_counters_V110__()
        else:
            print("ERROR: Version no soportada")
            return -1

    def __get_hash_config_counters_V110__(self):
        '''
        '''
        xhash = 0
        for channel in ['C0','C1']:
            enable = self.d_local_conf.get('COUNTERS',{}).get(channel,{}).get('ENABLE','FALSE')
            name = self.d_local_conf.get('COUNTERS',{}).get(channel,{}).get('NAME','X')
            modo = self.d_local_conf.get('COUNTERS',{}).get(channel,{}).get('MODO','CAUDAL')
            magpp=float(self.d_local_conf.get('COUNTERS',{}).get(channel,{}).get('MAGPP','0'))
            rbsize=int(self.d_local_conf.get('COUNTERS',{}).get(channel,{}).get('RBSIZE','1'))
            hash_str = f'[{channel}:{enable},{name},{magpp:.03f},{modo},{rbsize}]'
            xhash = self.u_hash(xhash, hash_str)
        #
        return xhash
    
    def get_response_counters(self, d_conf, fw_ver):
        '''
        Calcula la respuesta de configuracion de canales contadores
        '''
        self.d_local_conf = d_conf
        self.ifw_ver = self.version2int( fw_ver)
        #
        if self.ifw_ver == 110:
            return self.__get_response_counters_V110__()
        print("ERROR: Version no soportada")  
        return 'ERROR:UNKNOWN VERSION'
    
    def __get_response_counters_V110__(self):
        '''
        '''
        response = 'CLASS=CONF_COUNTERS&'
        for channel in ['C0','C1']:
            enable = self.d_local_conf.get('COUNTERS',{}).get(channel,{}).get('ENABLE','FALSE')
            name = self.d_local_conf.get('COUNTERS',{}).get(channel,{}).get('NAME', 'X')
            magpp = float(self.d_local_conf.get('COUNTERS',{}).get(channel,{}).get('MAGPP', 1.00))
            str_modo = self.d_local_conf.get('COUNTERS',{}).get(channel,{}).get('MODO','CAUDAL')
            rbsize=int(self.d_local_conf.get('COUNTERS',{}).get(channel,{}).get('RBSIZE','1'))
            response += f'{channel}={enable},{name},{magpp},{str_modo},{rbsize}&'
        #
        response = response[:-1]
        return response

    def get_hash_config_modbus(self, d_conf, fw_ver):
        '''
        Calcula el hash de la configuracion de canales modbus.
        RETURN: int
        '''
        #
        self.d_local_conf = d_conf
        self.ifw_ver = self.version2int( fw_ver)
        #
        if self.ifw_ver == 110:
            return self.__get_hash_config_modbus_V110__()
        else:
            print("ERROR: Version no soportada")
            return -1

    def __get_hash_config_modbus_V110__(self):
        '''
        '''
        xhash = 0
        enable=self.d_local_conf.get('MODBUS',{}).get('ENABLE','FALSE')
        localaddr=int(self.d_local_conf.get('MODBUS',{}).get('LOCALADDR','1'))

        hash_str = f'[{enable}:{localaddr:02d}]'
        xhash = self.u_hash(xhash, hash_str)
        for channel in ['M0','M1','M2','M3','M4']:
            name = self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('NAME','X')
            sla_addr=int(self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('SLA_ADDR','0'))
            reg_addr=int(self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('ADDR','0'))
            nro_regs=int(self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('NRO_RECS','0'))
            fcode=int(self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('FCODE','0'))
            mtype=self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('TYPE','U16')
            codec=self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('CODEC','C0123')
            pow10=int(self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('POW10','0'))
            hash_str = f'[{channel}:TRUE,{name},{sla_addr:02d},{reg_addr:04d},{nro_regs:02d},{fcode:02d},{mtype},{codec},{pow10:02d}]'
            xhash = self.u_hash(xhash, hash_str)
        #
        return xhash

    def get_response_modbus(self, d_conf, fw_ver):
        '''
        Calcula la respuesta de configuracion de canales modbus
        '''
        self.d_local_conf = d_conf
        self.ifw_ver = self.version2int( fw_ver)
        #
        if self.ifw_ver == 110:
            return self.__get_response_modbus_V110__()
        print("ERROR: Version no soportada")  
        return 'ERROR:UNKNOWN VERSION'
 
    def __get_response_modbus_V110__(self):
        '''
        '''
        enable=self.d_local_conf.get('MODBUS',{}).get('ENABLE','FALSE')
        localaddr=int(self.d_local_conf.get('MODBUS',{}).get('LOCALADDR',0x01))

        response = f'CLASS=CONF_MODBUS&ENABLE={enable}&LOCALADDR={localaddr}&'

        for channel in ['M0','M1','M2','M3','M4']:
            enable = self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('ENABLE','FALSE')
            name = self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('NAME','X')
            sla_addr=int(self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('SLA_ADDR','0'))
            reg_addr=int(self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('ADDR','0'))
            nro_regs=int(self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('NRO_RECS','0'))
            fcode=int(self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('FCODE','0'))
            mtype=self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('TYPE','U16')
            codec=self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('CODEC','C0123')
            pow10=int(self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('POW10','0'))
            response += f'{channel}={enable},{name},{sla_addr},{reg_addr},{nro_regs},{fcode},{mtype},{codec},{pow10}&'
        #
        response = response[:-1]
        return response

    def process_data(self, app, d_payload, fw_ver):
        '''
        '''
        self.ifw_ver = self.version2int( fw_ver)
        #
        if self.ifw_ver == 110:
            return self.__process_data_V110__(app, d_payload)
        print("ERROR: Version no soportada")  
        return 'ERROR:UNKNOWN VERSION'
        
    def __process_data_V110__(self, app, d_args):

        # 1) Armo el payload.
        d_payload = {}
        ID = d_args.get('ID','NONE')
        VER = d_args.get('VER','NONE')
        TYPE = d_args.get('TYPE','NONE')
        CLASS = d_args.get('CLASS','NONE')

        for key in d_args:
            if key not in ('ID','TYPE','CLASS','VER'):
                d_payload[key] = d_args.get(key)
        #    
        # 1) Guardo los datos
        r_data = requests.put(f"http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/dataline", params={'unit':ID,'type':'DLG'}, json=json.dumps(d_payload), timeout=10 )
        if r_data.status_code != 200:
            # Si da error genero un mensaje pero continuo para no trancar al datalogger.
            app.logger.error(f"CLASS={CLASS},ID={ID},ERROR AL GUARDAR DATA EN REDIS. Err=({r_data.status_code}){r_data.text}")
        #
        # 3) Leo las ordenes
        r_data = requests.get(f"http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/ordenes", params={'unit':ID }, timeout=10 )
        ordenes = ''
        if r_data.status_code == 200:
            ordenes = r_data.json()
            app.logger.info(f"CLASS={CLASS},ID={ID }, ORDENES=[{ordenes}]")
        elif r_data.status_code == 204:
            # Si da error genero un mensaje pero continuo para no trancar al datalogger.
            app.logger.info(f"CLASS={CLASS},ID={ID},NO HAY RCD ORDENES")
        else:
            app.logger.error(f"CLASS={CLASS},ID={ID},ERROR AL LEER ORDENES. Err=({r_data.status_code}){r_data.text}")
        #
        # 3.1) Si RESET entonces borro la configuracion
        if 'RESET' in [ordenes]:
            _ = requests.delete(f"http://{APIREDIS_HOST}:{APIREDIS_PORT}/apiredis/configuracion", params={'unit':ID}, timeout=10 )
            app.logger.info(f"CLASS={CLASS},ID={ID}, DELETE REDIS RCD.")
        #
        # 4) Respondo
        now=dt.datetime.now().strftime('%y%m%d%H%M')
        return f'CLASS=DATA&CLOCK={now};{ordenes}'
    

