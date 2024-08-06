#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python

from dlg_base import Dlg_base
from dlg_spx_avrda import Dlg_spx_avrda

class Dlg_spx_xmega(Dlg_spx_avrda, Dlg_base):
    '''
    Superclase que se especializa en los dataloggers SPX_AVRDA
    '''
    def __init__(self):
        print("DLG SPXAVRDA")

    # Los SPX_AVRDA no cambian la configuracion base con la versión

    def get_base_hash_from_config(self, d_conf=None):
        return Dlg_spx_avrda.get_base_hash_from_config(self, d_conf)

    def get_response_base(self, d_conf=None):
        return Dlg_spx_avrda.get_response_base(self, d_conf)
     
    def get_ainputs_hash_from_config(self, d_conf=None):
        return Dlg_spx_avrda.get_ainputs_hash_from_config(self, d_conf)

    def get_response_ainputs(self, d_conf=None):
        return Dlg_spx_avrda.get_response_ainputs(self, d_conf)

    def get_counters_hash_from_config(self, d_conf=None):
        return Dlg_spx_avrda.get_counters_hash_from_config(self, d_conf)

    def get_response_counters(self, d_conf=None):
        return Dlg_spx_avrda.get_response_counters(self, d_conf)
 
    def get_modbus_hash_from_config(self, d_conf=None):
        return Dlg_spx_avrda.get_modbus_hash_from_config(self, d_conf)
     
    def get_response_modbus(self, d_conf=None):
        return Dlg_spx_avrda.get_response_modbus(self, d_conf)
    
    def get_piloto_hash_from_config(self, d_conf=None):
        return Dlg_spx_avrda.get_piloto_hash_from_config(self, d_conf)
 
    def get_response_piloto(self, d_conf=None):
        return Dlg_spx_avrda.get_response_piloto(self, d_conf)

    def get_consigna_hash_from_config(self, d_conf=None):
        return Dlg_spx_avrda.get_consigna_hash_from_config(self, d_conf)
    
    def get_response_consigna(self, d_conf=None):
        return Dlg_spx_avrda.get_response_consigna(self, d_conf)
    
    