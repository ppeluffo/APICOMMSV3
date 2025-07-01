#!/home/pablo/Spymovil/python/proyectos/APICOMMS/venv/bin/python

#from apidlg_utils import str2int, u_hash
from baseutils.baseutils import str2int, u_hash

from prot_spqavrda.spqavrda import Spqavrda

class SpqavrdaR12X(Spqavrda):
    '''
    El R12X es una subclase de R11X por lo tanto R12X hereda de R11X (super)
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
    # BASE
    # No usa SAMPLES ni ALARM

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
        response = 'CLASS=CONF_BASE&'
        response += f'TPOLL={timerpoll}&TDIAL={timerdial}&PWRMODO={s_pwrmodo}&PWRON={pwr_hhmm_on:04}&PWROFF={pwr_hhmm_off:04}'
        #print(f'DEBUG::response={response}')
        return response
 
