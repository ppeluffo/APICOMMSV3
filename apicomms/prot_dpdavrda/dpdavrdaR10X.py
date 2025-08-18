#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python

from prot_dpdavrda.dpdavrda import Dpdavrda

class DpdavrdaR10X(Dpdavrda):
    '''
    '''
    def __init__(self, d_args=None):
        '''
        '''
        self.d_args = d_args
        super().__init__(d_args)
