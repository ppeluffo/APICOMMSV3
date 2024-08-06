#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python

from dlg_spq_avrda import Dlg_spq_avrda

class Dlg_spq_avrda_R110(Dlg_spq_avrda):
    '''
    '''
    def __init__(self, d_args=None):
        '''
        '''
        self.d_args = d_args
        #print("DLG SPQAVRDA R110")
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