#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python

from prot_spqavrda.spqavrda import Spqavrda

class SpqavrdaR11X(Spqavrda):
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
 