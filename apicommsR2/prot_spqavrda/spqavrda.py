#!/home/pablo/Spymovil/python/proyectos/APICOMMS/venv/bin/python

from baseutils.dlgbase import Dlgbase

class Spqavrda(Dlgbase):
    '''
    Superclase que se especializa en los dataloggers SPX_AVRDA
    '''
    def __init__(self, d_args=None):
        self.d_args = d_args
        super().__init__(d_args)

