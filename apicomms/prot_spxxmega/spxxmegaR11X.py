#!/home/pablo/Spymovil/python/proyectos/APICOMMS/venv/bin/python

from prot_spxxmega.spxxmega import Spxxmega

class SpxxmegaR11X(Spxxmega):
    '''
    El R11X es una subclase de Spxavrda por lo tanto  hereda de Spxavrda(super)
    '''
    def __init__(self, d_args=None):
        self.d_args = d_args
        super().__init__(d_args)
            
    '''
    Implemento TODOS los metodos personalizados por version que voy a usar
    en la clase padre de todas.
    Si el método no tienen particularidades, lo refiero por herencia
    '''