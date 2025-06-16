#!/home/pablo/Spymovil/python/proyectos/APICOMMS/venv/bin/python


from prot_fwdlgx.fwdlgx import Fwdlgx

class FwdlgxR10X(Fwdlgx):
    '''
    El R100 es una subclase de FWDLGX por lo tanto  hereda de FWDLGX(super)
    '''
    def __init__(self, d_args=None):
        self.d_args = d_args
        super().__init__(d_args)
            
    '''
    Implemento TODOS los metodos personalizados por version que voy a usar
    en la clase padre de todas.
    Si el método no tienen particularidades, lo refiero por herencia
    '''
        
    
 