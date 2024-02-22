#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python
'''
Clase especializada en utilidades de frames de dataloggers version SPXR3
'''
import re
import datetime as dt

class dlgutils:

    def __init__(self):
        self.d_local_conf = None
        self.ifw_ver = 0

    def str2int(self, s):
        '''
        Convierte un string a un nro.entero con la base correcta.
        '''
        if not isinstance(s, str):
            return 0
        if 'X' in s.upper():
            return int(s,16)
        return int(s)
    
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
        return self.str2int( re.sub(r"[A-Z,a-z,.]",'',str_version))
 

    def get_hash_config_base(self, d_conf, fw_ver):
        '''
        Calcula el hash de la configuracion base.
        RETURN: int
        '''
        self.d_local_conf = d_conf
        #print(f"DEBUG: self.d_local_conf={self.d_local_conf}")
        self.ifw_ver = self.version2int( fw_ver)
        #print(f"DEBUG: self.ifw_ver={self.ifw_ver}")

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
        timerpoll = self.str2int(self.d_local_conf.get('BASE',{}).get('TPOLL','0'))
        timerdial = self.str2int(self.d_local_conf.get('BASE',{}).get('TDIAL','0'))
        pwr_modo = self.str2int(self.d_local_conf.get('BASE',{}).get('PWRS_MODO','0'))
        pwr_hhmm_on = self.str2int(self.d_local_conf.get('BASE',{}).get('PWRS_HHMM1','601'))
        pwr_hhmm_off = self.str2int(self.d_local_conf.get('BASE',{}).get('PWRS_HHMM2','2201'))
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
        samples = self.str2int(self.d_local_conf.get('BASE',{}).get('SAMPLES','1'))
        almlevel = self.str2int(self.d_local_conf.get('BASE',{}).get('ALMLEVEL','0'))
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
        timerpoll = self.str2int( self.d_local_conf.get('BASE',{}).get('TPOLL','0'))
        #print(f'DEBUG::timerpoll={timerpoll}')
        timerdial = self.str2int(self.d_local_conf.get('BASE',{}).get('TDIAL','0'))
        #print(f'DEBUG::timerdial={timerdial}')
        pwr_modo = self.str2int(self.d_local_conf.get('BASE',{}).get('PWRS_MODO','0'))
        pwr_hhmm_on = self.str2int(self.d_local_conf.get('BASE',{}).get('PWRS_HHMM1','600'))
        pwr_hhmm_off = self.str2int(self.d_local_conf.get('BASE',{}).get('PWRS_HHMM2','2200'))
        if pwr_modo == 0:
            s_pwrmodo = 'CONTINUO'
        elif pwr_modo == 1:
            s_pwrmodo = 'DISCRETO'
        else:
            s_pwrmodo = 'MIXTO'
        #
        samples = self.str2int( self.d_local_conf.get('BASE',{}).get('SAMPLES','1'))
        almlevel = self.str2int( self.d_local_conf.get('BASE',{}).get('ALMLEVEL','0'))
        #
        response = 'CLASS=CONF_BASE&'
        response += f'TPOLL={timerpoll}&TDIAL={timerdial}&PWRMODO={s_pwrmodo}&PWRON={pwr_hhmm_on:04}&PWROFF={pwr_hhmm_off:04}'
        response += f'&SAMPLES={samples}&ALMLEVEL={almlevel}'
        #print(f'DEBUG::response={response}')
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
            enable = self.d_local_conf.get('AINPUTS',{}).get(channel,{}).get('ENABLE','FALSE')
            name = self.d_local_conf.get('AINPUTS',{}).get(channel,{}).get('NAME','X')
            imin=self.str2int( self.d_local_conf.get('AINPUTS',{}).get(channel,{}).get('IMIN','0'))
            imax=self.str2int( self.d_local_conf.get('AINPUTS',{}).get(channel,{}).get('IMAX','0'))
            mmin=float( self.d_local_conf.get('AINPUTS',{}).get(channel,{}).get('MMIN','0'))
            mmax=float( self.d_local_conf.get('AINPUTS',{}).get(channel,{}).get('MMAX','0'))
            offset=float( self.d_local_conf.get('AINPUTS',{}).get(channel,{}).get('OFFSET','0'))
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
            enable = self.d_local_conf.get('AINPUTS',{}).get(channel,{}).get('ENABLE', 'FALSE')
            name = self.d_local_conf.get('AINPUTS',{}).get(channel,{}).get('NAME', 'X')
            imin = self.str2int(self.d_local_conf.get('AINPUTS',{}).get(channel,{}).get('IMIN', '4'))
            imax = self.str2int(self.d_local_conf.get('AINPUTS',{}).get(channel,{}).get('IMAX', '20'))
            mmin = float(self.d_local_conf.get('AINPUTS',{}).get(channel,{}).get('MMIN', 0.00))
            mmax = float(self.d_local_conf.get('AINPUTS',{}).get(channel,{}).get('MMAX', 10.00))
            offset = float(self.d_local_conf.get('AINPUTS',{}).get(channel,{}).get('OFFSET', 0.00))
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
            rbsize=self.str2int(self.d_local_conf.get('COUNTERS',{}).get(channel,{}).get('RBSIZE','1'))
            hash_str = f'[{channel}:{enable},{name},{magpp:.03f},{modo},{rbsize}]'
            xhash = self.u_hash(xhash, hash_str)
            #print(f'DEBUG HASH COUNTERS: hash_str={hash_str}')
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
            rbsize=self.str2int(self.d_local_conf.get('COUNTERS',{}).get(channel,{}).get('RBSIZE','1'))
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
        localaddr=self.str2int(self.d_local_conf.get('MODBUS',{}).get('LOCALADDR','1'))
        hash_str = f'[{enable},{localaddr:02d}]'
        xhash = self.u_hash(xhash, hash_str)
        #print(f'DEBUG HASH MODBUS: hash_str={hash_str}{xhash}')
        
        #,
        for channel in ['M0','M1','M2','M3','M4']:
            enable = self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('ENABLE','FALSE')
            name = self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('NAME','X')
            sla_addr=self.str2int(self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('SLA_ADDR','0'))
            reg_addr=self.str2int(self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('ADDR','0'))
            nro_regs=self.str2int(self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('NRO_RECS','0'))
            fcode=self.str2int(self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('FCODE','0'))
            mtype=self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('TYPE','U16')
            codec=self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('CODEC','C0123')
            pow10=self.str2int(self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('POW10','0'))
            hash_str = f'[{channel}:{enable},{name},{sla_addr:02d},{reg_addr:04d},{nro_regs:02d},{fcode:02d},{mtype},{codec},{pow10:02d}]'
            xhash = self.u_hash(xhash, hash_str)
            #print(f'DEBUG HASH MODBUS: hash_str={hash_str}{xhash}')
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
        localaddr=self.str2int(self.d_local_conf.get('MODBUS',{}).get('LOCALADDR','0x01'))

        response = f'CLASS=CONF_MODBUS&ENABLE={enable}&LOCALADDR={localaddr}&'

        for channel in ['M0','M1','M2','M3','M4']:
            enable = self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('ENABLE','FALSE')
            name = self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('NAME','X')
            sla_addr=self.str2int(self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('SLA_ADDR','0'))
            reg_addr=self.str2int(self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('ADDR','0'))
            nro_regs=self.str2int(self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('NRO_RECS','0'))
            fcode=self.str2int(self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('FCODE','0'))
            mtype=self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('TYPE','U16')
            codec=self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('CODEC','C0123')
            pow10=self.str2int(self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('POW10','0'))
            response += f'{channel}={enable},{name},{sla_addr},{reg_addr},{nro_regs},{fcode},{mtype},{codec},{pow10}&'
        #
        response = response[:-1]
        return response

    def convert_dataline2dict (self, d_url_args, fw_ver):
        '''
        '''
        self.ifw_ver = self.version2int( fw_ver)
        #
        if self.ifw_ver == 110:
            return self.__process_data_V110__(d_url_args)
        #
        print("(459) ApiCOMMS_ERR010: Version no soportada")  
        return None
        
    def __process_data_V110__(self, d_url_args):

        # 1) Armo el payload.
        d_payload = {}
        for key in d_url_args:
            if key not in ('ID','TYPE','CLASS','VER'):
                d_payload[key] = d_url_args.get(key)
        #
        return d_payload

    def get_hash_config_piloto(self, d_conf_piloto, fw_ver):
        '''
        Calcula el hash de la configuracion del piloto.
        RETURN: int
        '''
        #

        self.d_local_conf = d_conf_piloto
        self.ifw_ver = self.version2int( fw_ver)
        #
        if self.ifw_ver == 110:
            return self.__get_hash_config_piloto_V110__()
        else:
            print("ERROR: Version no soportada")
            return -1

    def __get_hash_config_piloto_V110__(self):
        '''
        '''
        xhash = 0
        #print(f'DEBUG D_CONF_PILOTO={self.d_local_conf}')
        enable=self.d_local_conf.get('ENABLE','FALSE')
        ppr=self.str2int(self.d_local_conf.get('PPR','1000'))
        pwidth=self.str2int(self.d_local_conf.get('PWIDTH','10'))
        hash_str = f'[{enable},{ppr:04d},{pwidth:02d}]'
        xhash = self.u_hash(xhash, hash_str)
        print(f'DEBUG HASH MODBUS: hash_str={hash_str}{xhash}')
        #
        for channel in range(12):
            slot_name = f'SLOT{channel}'
            presion = float( self.d_local_conf.get(slot_name,{}).get('PRES','0.0'))
            timeslot = self.str2int( self.d_local_conf.get(slot_name,{}).get('TIME','0000'))
            hash_str = f'[S{channel:02d}:{timeslot:04d},{presion:0.2f}]'
            xhash = self.u_hash(xhash, hash_str)
            #print(f'DEBUG HASH MODBUS: hash_str={hash_str}{xhash}')
        # 
        return xhash

    def get_response_piloto(self, d_conf_piloto, fw_ver):
        '''
        Calcula la respuesta de configuracion de canales modbus
        '''
        self.d_local_conf = d_conf_piloto
        self.ifw_ver = self.version2int( fw_ver)
        #
        if self.ifw_ver == 110:
            return self.__get_response_piloto_V110__()
        print("ERROR: Version no soportada")  
        return 'ERROR:UNKNOWN VERSION'
 
    def __get_response_piloto_V110__(self):
        '''
        '''
        enable=self.d_local_conf.get('ENABLE','FALSE')
        ppr=self.str2int(self.d_local_conf.get('PPR','1000'))
        pwidth=self.str2int(self.d_local_conf.get('PWIDTH','10'))
        response = f'CLASS=CONF_PILOTO&ENABLE={enable}&PULSEXREV={ppr}&PWIDTH={pwidth}&'
        #
        for channel in range(12):
            slot_name = f'SLOT{channel}'
            presion = float( self.d_local_conf.get(slot_name,{}).get('PRES','0.0'))
            timeslot = self.str2int( self.d_local_conf.get(slot_name,{}).get('TIME','0000'))
            response += f'S{channel}={timeslot:04d},{presion:0.2f}&'
        #
        response = response[:-1]
        return response

    def get_hash_config_consigna(self, d_conf_consigna, fw_ver):
        '''
        Calcula el hash de la configuracion del consigna.
        RETURN: int
        '''
        #

        self.d_local_conf = d_conf_consigna
        self.ifw_ver = self.version2int( fw_ver)
        #
        if self.ifw_ver == 110:
            return self.__get_hash_config_consigna_V110__()
        else:
            print("ERROR: Version no soportada")
            return -1

    def __get_hash_config_consigna_V110__(self):
        '''
        '''
        xhash = 0
        #print(f'DEBUG D_CONF_CONSIGNA={self.d_local_conf}')
        enable=self.d_local_conf.get('ENABLE','FALSE')
        c_diurna = self.str2int( self.d_local_conf.get('DIURNA','630'))
        c_nocturna = self.str2int( self.d_local_conf.get('NOCTURNA','2330'))
        hash_str = f'[{enable},{c_diurna:04d},{c_nocturna:04d}]'
        xhash = self.u_hash(xhash, hash_str)
        #print(f'DEBUG HASH CONSIGNA: hash_str={hash_str}{xhash}')
        return xhash

    def get_response_consigna(self, d_conf_consigna, fw_ver):
        '''
        Calcula la respuesta de configuracion de canales modbus
        '''
        self.d_local_conf = d_conf_consigna
        self.ifw_ver = self.version2int( fw_ver)
        #
        if self.ifw_ver == 110:
            return self.__get_response_consigna_V110__()
        print("ERROR: Version no soportada")  
        return 'ERROR:UNKNOWN VERSION'
 
    def __get_response_consigna_V110__(self):
        '''
        '''
        enable=self.d_local_conf.get('ENABLE','FALSE')
        c_diurna = self.d_local_conf.get('DIURNA','630')
        c_nocturna = self.d_local_conf.get('NOCTURNA','2330')
        response = f'CLASS=CONF_CONSIGNA&ENABLE={enable}&DIURNA={c_diurna}&NOCTURNA={c_nocturna}'
        return response
