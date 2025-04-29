#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python

from dlg_spx_xmega import Dlg_spx_xmega

class Dlg_spx_xmega_R130(Dlg_spx_xmega):
    '''
    '''
    def __init__(self, d_args=None):
        '''
        '''
        self.d_args = d_args
        #print("DLG SPXAVRDA R120")
        Dlg_spx_xmega.__init__(self)

    def process_frame(self):
        '''
        '''
        return Dlg_spx_xmega.process_frame(self, self.d_args)
    
    def process_frame_ping(self):
        '''
        '''
        return Dlg_spx_xmega.process_frame_ping(self, self.d_args)

    def process_frame_recover(self):
        '''
        '''
        return Dlg_spx_xmega.process_frame_recover(self, self.d_args)
    
    def process_frame_base(self):
        '''
        Esta clase la modificamos porque no usamos  SAMPLE ni ALARMLEVEL
        Es para los equipos SPX_XMEGA con firmware unificado FWDLGX R 1.3.0
        '''
        return Dlg_spx_xmega.process_frame_base(self, self.d_args)
    
    def process_frame_ainputs(self):
        '''
        '''
        return Dlg_spx_xmega.process_frame_ainputs(self, self.d_args)

    def process_frame_counters(self):
        '''
        '''
        return Dlg_spx_xmega.process_frame_counters(self, self.d_args)
    
    def process_frame_data(self):
        '''
        '''
        return Dlg_spx_xmega.process_frame_data(self, self.d_args)