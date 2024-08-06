#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python

from dlg_spq_avrda import Dlg_spq_avrda
from apidlgR2_utils import str2int, u_hash

class Dlg_spq_avrda_R120(Dlg_spq_avrda):
    '''
    '''
    def __init__(self, d_args=None):
        self.d_args = d_args
        #print("DLG SPQAVRDA R120")
        Dlg_spq_avrda.__init__(self)

    def process_frame(self):
        '''
        '''
        return Dlg_spq_avrda.process_frame(self, self.d_args)
    
    def process_frame_ping(self):
        '''
        '''
        return Dlg_spq_avrda.process_frame_ping(self, self.d_args)

    def process_frame_recover(self):
        '''
        '''
        return Dlg_spq_avrda.process_frame_recover(self, self.d_args)
    
    def get_base_hash_from_config(self, d_conf=None):
        '''
        Calculo el hash para la version 1.2.0 ya que usa menos parametros. !!!
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

    def process_frame_base(self):
        '''
        '''
        return Dlg_spq_avrda.process_frame_base(self, self.d_args)
    
    def process_frame_ainputs(self):
        '''
        '''
        return Dlg_spq_avrda.process_frame_ainputs(self, self.d_args)

    def process_frame_counters(self):
        '''
        '''
        return Dlg_spq_avrda.process_frame_counters(self, self.d_args)
    
    def process_frame_modbus(self):
        '''
        '''
        return Dlg_spq_avrda.process_frame_modbus(self, self.d_args)
    
    def process_frame_piloto(self):
        '''
        '''
        return Dlg_spq_avrda.process_frame_piloto(self, self.d_args)
    
    def process_frame_consigna(self):
        '''
        '''
        return Dlg_spq_avrda.process_frame_consigna(self, self.d_args)
    
    def process_frame_data(self):
        '''
        '''
        return Dlg_spq_avrda.process_frame_data(self, self.d_args)