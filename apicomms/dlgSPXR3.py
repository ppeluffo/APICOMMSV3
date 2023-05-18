#!/home/pablo/Spymovil/python/proyectos/COMMSV3/venv/bin/python
'''
Clase especializada en utilidades de frames de dataloggers version SPXR3
'''

import re

class dlgutils:

    def __init__(self):
        self.d_local_conf = None

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
        xhash = 0
        timerpoll = int(self.d_local_conf.get('BASE',{}).get('TPOLL','0'))
        timerdial = int(self.d_local_conf.get('BASE',{}).get('TDIAL','0'))
        pwr_modo = int(self.d_local_conf.get('BASE',{}).get('PWRS_MODO','0'))
        pwr_hhmm_on = int(self.d_local_conf.get('BASE',{}).get('PWRS_HHMM1','601'))
        pwr_hhmm_off = int(self.d_local_conf.get('BASE',{}).get('PWRS_HHMM2','2201'))
        #
        hash_str = f'[TIMERPOLL:{timerpoll:03d}]'
        xhash = self.u_hash(xhash, hash_str)
        #d_log = { 'MODULE':__name__, 'FUNCTION':'calcular_hash_config_base', 'LEVEL':'ERROR',
        #        'DLGID': d_params['DLGID'], 'MSG':f'DEBUG: HASH_BASE: hash_str=<{hash_str}>, hash={xhash}' }
        #log2(d_log)
        #
        hash_str = f'[TIMERDIAL:{timerdial:03d}]'
        xhash = self.u_hash(xhash, hash_str)
        #d_log = { 'MODULE':__name__, 'FUNCTION':'calcular_hash_config_base', 'LEVEL':'ERROR',
        #        'DLGID': d_params['DLGID'], 'MSG':f'DEBUG: HASH_BASE: hash_str=<{hash_str}>, hash={xhash}' }
        #log2(d_log)
        #
        hash_str = f'[PWRMODO:{pwr_modo}]'
        xhash = self.u_hash(xhash, hash_str)
        #d_log = { 'MODULE':__name__, 'FUNCTION':'calcular_hash_config_base', 'LEVEL':'ERROR',
        #        'DLGID': d_params['DLGID'], 'MSG':f'DEBUG: HASH_BASE: hash_str=<{hash_str}>, hash={xhash}' }
        #log2(d_log)
        #
        hash_str = f'[PWRON:{pwr_hhmm_on:04}]'
        xhash = self.u_hash(xhash, hash_str)
        #d_log = { 'MODULE':__name__, 'FUNCTION':'calcular_hash_config_base', 'LEVEL':'ERROR',
        #        'DLGID': d_params['DLGID'], 'MSG':f'DEBUG: HASH_BASE: hash_str=<{hash_str}>, hash={xhash}' }
        #log2(d_log)
        #
        hash_str = f'[PWROFF:{pwr_hhmm_off:04}]'
        xhash = self.u_hash(xhash, hash_str)
        #d_log = { 'MODULE':__name__, 'FUNCTION':'calcular_hash_config_base', 'LEVEL':'ERROR',
        #        'DLGID': d_params['DLGID'], 'MSG':f'DEBUG: HASH_BASE: hash_str=<{hash_str}>, hash={xhash}' }
        #log2(d_log)
        #
        # A partir de la version 105 incorporamos 'samples'y almlevel'
        int_fw_ver = self.version2int( fw_ver)
        if int_fw_ver >= 105:
            samples = int(self.d_local_conf.get('BASE',{}).get('SAMPLES','1'))
            almlevel = int(self.d_local_conf.get('BASE',{}).get('ALMLEVEL','0'))
            hash_str = f'[SAMPLES:{samples:02}]'
            xhash = self.u_hash(xhash, hash_str)
            #d_log = { 'MODULE':__name__, 'FUNCTION':'calcular_hash_config_base', 'LEVEL':'ERROR',
            #    'DLGID': d_params['DLGID'], 'MSG':f'DEBUG: HASH_BASE: hash_str=<{hash_str}>, hash={xhash}' }
            #log2(d_log)
            #
            hash_str = f'[ALMLEVEL:{almlevel:02}]'
            xhash = self.u_hash(xhash, hash_str)
            #d_log = { 'MODULE':__name__, 'FUNCTION':'calcular_hash_config_base', 'LEVEL':'ERROR',
            #    'DLGID': d_params['DLGID'], 'MSG':f'DEBUG: HASH_BASE: hash_str=<{hash_str}>, hash={xhash}' }
            #log2(d_log)
        #
        return xhash

    def get_response_base(self, d_conf, fw_ver):
        '''
        Calcula la respuesta de configuracion base
        RETURN: string
        '''
        #
        self.d_local_conf = d_conf
        #
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
        response = 'CLASS=CONF_BASE&'
        response += f'TPOLL={timerpoll}&TDIAL={timerdial}&PWRMODO={s_pwrmodo}&PWRON={pwr_hhmm_on:04}&PWROFF={pwr_hhmm_off:04}'
        #
        int_fw_ver = self.version2int( fw_ver)
        if int_fw_ver >= 105:
            samples = int( self.d_local_conf.get('BASE',{}).get('SAMPLES','1'))
            almlevel = int( self.d_local_conf.get('BASE',{}).get('ALMLEVEL','0'))
            response += f'&SAMPLES={samples}&ALMLEVEL={almlevel}'
        #    
        return response
    
    def get_hash_config_ainputs(self, d_conf, fw_ver):
        '''
        Calcula el hash de la configuracion de canales analoggicos.
        RETURN: int
        '''
        #
        self.d_local_conf = d_conf
        int_fw_ver = self.version2int( fw_ver)
        xhash = 0
        for channel in ['A0','A1','A2']:
            name = self.d_local_conf.get('BASE',{}).get(channel,{}).get('NAME','X')
            if name == 'X':
                hash_str = f'[{channel}:X,4,20,0.00,10.00,0.00]'
            else:
                imin=int( self.d_local_conf.get('BASE',{}).get(channel,{}).get('IMIN','0'))
                imax=int( self.d_local_conf.get('BASE',{}).get(channel,{}).get('IMAX','0'))
                mmin=float( self.d_local_conf.get('BASE',{}).get(channel,{}).get('MMIN','0'))
                mmax=float( self.d_local_conf.get('BASE',{}).get(channel,{}).get('MMAX','0'))
                offset=float( self.d_local_conf.get('BASE',{}).get(channel,{}).get('OFFSET','0'))
                hash_str = f'[{channel}:{name},{imin},{imax},{mmin:.02f},{mmax:.02f},{offset:.02f}]'
            #
            xhash = self.u_hash(xhash, hash_str)
        return xhash
    
    def get_response_ainputs(self, d_conf, fw_ver):
        '''
        Calcula la respuesta de configuracion de canales analogicos
        '''
        #
        self.d_local_conf = d_conf
        int_fw_ver = self.version2int( fw_ver)
        response = 'CLASS=CONF_AINPUTS&'
        for channel in ['A0','A1','A2']:
            name = self.d_local_conf.get('ANALOGS',{}).get(channel,{}).get('NAME', 'X')
            imin = int(self.d_local_conf.get('ANALOGS',{}).get(channel,{}).get('IMIN', 4))
            imax = int(self.d_local_conf.get('ANALOGS',{}).get(channel,{}).get('IMAX', 20))
            mmin = float(self.d_local_conf.get('ANALOGS',{}).get(channel,{}).get('MMIN', 0.00))
            mmax = float(self.d_local_conf.get('ANALOGS',{}).get(channel,{}).get('MMAX', 10.00))
            offset = float(self.d_local_conf.get('ANALOGS',{}).get(channel,{}).get('OFFSET', 0.00))
            response += f'{channel}={name},{imin},{imax},{mmin},{mmax},{offset}&'
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
        int_fw_ver = self.version2int( fw_ver)
        xhash = 0
        for channel in ['C0','C1']:
            name = self.d_local_conf.get('COUNTERS',{}).get(channel,{}).get('NAME','X')
            if name == 'X':
                hash_str = f'[{channel}:X,1.000,0]'
            else:
                str_modo = self.d_local_conf.get('COUNTERS',{}).get(channel,{}).get('MODO','CAUDAL')
                if str_modo == 'CAUDAL':
                    modo = 0    # caudal
                else:
                    modo = 1    # pulsos
                magpp=float(self.d_local_conf.get('COUNTERS',{}).get(channel,{}).get('MAGPP','0'))
                hash_str = f'[{channel}:{name},{magpp:.03f},{modo}]'
                #
            # La version 108 incorpora el tamaño del ringbuffer de caudalimetros
            if int_fw_ver >= 108:
                hash_str=hash_str[:-1]
                if name == 'X':
                    hash_str += ',1]'
                else:
                    rbsize=int(self.d_local_conf.get('COUNTERS',{}).get(channel,{}).get('RBSIZE','1'))
                    hash_str += f',{rbsize}]'
            #
            xhash = self.u_hash(xhash, hash_str)
        #
        return xhash
    
    def get_response_counters(self, d_conf, fw_ver):
        '''
        Calcula la respuesta de configuracion de canales contadores
        '''
        self.d_local_conf = d_conf
        int_fw_ver = self.version2int( fw_ver)
        response = 'CLASS=CONF_COUNTERS&'
        for channel in ['C0','C1']:
            name = self.d_local_conf.get('COUNTERS',{}).get(channel,{}).get('NAME', 'X')
            magpp = float(self.d_local_conf.get('COUNTERS',{}).get(channel,{}).get('MAGPP', 1.00))
            str_modo = self.d_local_conf.get('COUNTERS',{}).get(channel,{}).get('MODO','CAUDAL')
            rbsize=int(self.d_local_conf.get('COUNTERS',{}).get(channel,{}).get('RBSIZE','1'))
            #
            if int_fw_ver >= 108:
                response += f'{channel}={name},{magpp},{str_modo},{rbsize}&'
            else:
                response += f'{channel}={name},{magpp},{str_modo}&'
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
        int_fw_ver = self.version2int( fw_ver)
        xhash = 0
        for channel in ['M0','M1','M2','M3','M4']:
            name = self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('NAME','X')
            if name == 'X':
                hash_str = f'[{channel}:X,00,0000,00,00,U16,C0123,00]'
            else:
                sla_addr=int(self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('SLA_ADDR','0'))
                reg_addr=int(self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('ADDR','0'))
                nro_regs=int(self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('NRO_RECS','0'))
                fcode=int(self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('FCODE','0'))
                mtype=self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('TYPE','U16')
                codec=self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('CODEC','C0123')
                pow10=int(self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('POW10','0'))
                hash_str = f'[{channel}:{name},{sla_addr:02d},{reg_addr:04d},{nro_regs:02d},{fcode:02d},{mtype},{codec},{pow10:02d}]'
            #
            xhash = self.u_hash(xhash, hash_str)
        #
        return xhash
    
    def get_response_modbus(self, d_conf, fw_ver):
        '''
        Calcula la respuesta de configuracion de canales modbus
        '''
        self.d_local_conf = d_conf
        int_fw_ver = self.version2int( fw_ver)
        response = 'CLASS=CONF_MODBUS&'
        for channel in ['M0','M1','M2','M3','M4']:
            name = self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('NAME','X')
            sla_addr=int(self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('SLA_ADDR','0'))
            reg_addr=int(self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('ADDR','0'))
            nro_regs=int(self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('NRO_RECS','0'))
            fcode=int(self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('FCODE','0'))
            mtype=self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('TYPE','U16')
            codec=self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('CODEC','C0123')
            pow10=int(self.d_local_conf.get('MODBUS',{}).get(channel,{}).get('POW10','0'))
            response += f'{channel}={name},{sla_addr},{reg_addr},{nro_regs},{fcode},{mtype},{codec},{pow10}&'
        #
        response = response[:-1]
        return response
  
    
