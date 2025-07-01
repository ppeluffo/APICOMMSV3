#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python

from baseutils.dlgbase import Dlgbase
#from apidlg_utils import str2int, u_hash
from baseutils.baseutils import str2int, u_hash

class Spxavrda(Dlgbase):
    '''
    Superclase que se especializa en los dataloggers SPX_AVRDA
    '''
    def __init__(self, d_args=None):
        self.d_args = d_args
        super().__init__(d_args)

    # Los SPX_AVRDA no cambian la configuracion base con la versión
    
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

 
  