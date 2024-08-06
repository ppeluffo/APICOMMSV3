#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python

from dlg_base import Dlg_base
from apidlgR2_utils import str2int, u_hash

class Dlg_spx_avrda(Dlg_base):
    '''
    Superclase que se especializa en los dataloggers SPX_AVRDA
    '''
    def __init__(self):
        #print("DLG SPXAVRDA")
        Dlg_base.__init__(self)

    # Los SPX_AVRDA no cambian la configuracion base con la versión

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
    
    def get_ainputs_hash_from_config(self, d_conf=None):
        '''
        Calculo el hash para todas las versiones
        '''
        xhash = 0
        for channel in ['A0','A1','A2']:
            enable = d_conf.get('AINPUTS',{}).get(channel,{}).get('ENABLE','FALSE')
            name = d_conf.get('AINPUTS',{}).get(channel,{}).get('NAME','X')
            imin = str2int( d_conf.get('AINPUTS',{}).get(channel,{}).get('IMIN','4'))
            imax = str2int( d_conf.get('AINPUTS',{}).get(channel,{}).get('IMAX','20'))
            mmin = float( d_conf.get('AINPUTS',{}).get(channel,{}).get('MMIN','0'))
            mmax = float( d_conf.get('AINPUTS',{}).get(channel,{}).get('MMAX','10'))
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

    def get_counters_hash_from_config(self, d_conf=None):
        '''
        Calculo el hash para todas las versiones
        '''
        xhash = 0
        for channel in ['C0','C1']:
            enable =d_conf.get('COUNTERS',{}).get(channel,{}).get('ENABLE','FALSE')
            name = d_conf.get('COUNTERS',{}).get(channel,{}).get('NAME','X')
            modo = d_conf.get('COUNTERS',{}).get(channel,{}).get('MODO','CAUDAL')
            magpp = float(d_conf.get('COUNTERS',{}).get(channel,{}).get('MAGPP','1'))
            rbsize = str2int(d_conf.get('COUNTERS',{}).get(channel,{}).get('RBSIZE','1'))
            hash_str = f'[{channel}:{enable},{name},{magpp:.03f},{modo},{rbsize}]'
            xhash = u_hash(xhash, hash_str)
            #print(f'DEBUG HASH COUNTERS: hash_str={hash_str}')
        #
        return xhash

    def get_response_counters(self, d_conf=None):
        '''
        Armo la respuesta para todas las versiones
        '''
        response = 'CLASS=CONF_COUNTERS&'
        for channel in ['C0','C1']:
            enable = d_conf.get('COUNTERS',{}).get(channel,{}).get('ENABLE','FALSE')
            name = d_conf.get('COUNTERS',{}).get(channel,{}).get('NAME', 'X')
            magpp = float(d_conf.get('COUNTERS',{}).get(channel,{}).get('MAGPP', 1.00))
            str_modo = d_conf.get('COUNTERS',{}).get(channel,{}).get('MODO','CAUDAL')
            rbsize = str2int(d_conf.get('COUNTERS',{}).get(channel,{}).get('RBSIZE','1'))
            response += f'{channel}={enable},{name},{magpp},{str_modo},{rbsize}&'
        #
        response = response[:-1]
        return response

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
    
    