#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python

from dlg_dpd_avrda import Dlg_dpd_avrda

class Dlg_dpd_avrda_R100(Dlg_dpd_avrda):
    '''
    Superclase que se especializa en los DPD
    '''
    def __init__(self, d_args=None):
        '''
        '''
        self.d_args = d_args
        #print("DPD S1")
        Dlg_dpd_avrda.__init__(self)

    def process_frame(self):
        '''
        '''
        return Dlg_dpd_avrda.process_frame(self, self.d_args)
    
    def process_frame_ping(self):
        '''
        '''
        return Dlg_dpd_avrda.process_frame_ping(self, self.d_args)

    def process_frame_data(self):
        '''
        '''
        return Dlg_dpd_avrda.process_frame_data(self, self.d_args)
    

    # Los SPQ_AVRDA no cambian la configuracion base con la versión    