#!/home/pablo/Spymovil/python/proyectos/APICOMMS/venv/bin/python

from prot_fwdlgx.fwdlgxR10X import FwdlgxR10X

class FwdlgxR11X(FwdlgxR10X):
    '''
    El R110 es una subclase de R100 por lo tanto R110 hereda de R100 (super)
    '''
    def __init__(self, d_args=None):
        self.d_args = d_args
        super().__init__(d_args)
            
    '''
    Implemento TODOS los metodos personalizados por version que voy a usar
    en la clase padre de todas.
    Si el método no tienen particularidades, lo refiero por herencia
    '''
