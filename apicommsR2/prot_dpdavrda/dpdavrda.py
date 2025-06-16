#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python

from baseutils.dlgbase import Dlgbase

class Dpdavrda(Dlgbase):
    '''
    El FWDLGX es una subclase de DlgBase por lo tanto  hereda de dlgBase (super)
    '''
    def __init__(self, d_args=None):
        self.d_args = d_args
        super().__init__(d_args)

    