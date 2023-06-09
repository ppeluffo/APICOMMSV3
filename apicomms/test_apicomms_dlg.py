#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python
'''
Script que testea la apicomms simulando ser un DATALOGGER
'''
import requests
import json

class ApicommsTestDlg:

    def __init__(self):
        self.ID = 'DLGTEST'
        self.VER = '1.1.0'
        self.TYPE = 'DLG'
        self.apihost = '127.0.0.1'
        self.apiport = '5000'
        self.url = None

    def sendPing(self):
        '''
         ID=PABLO&TYPE=SPXR3&VER=1.0.0&CLASS=PING
        '''
        self.set_ID('DLGTEST')
        self.set_TYPE('DLG')
        self.set_VER('1.1.0')
        self.url = f'http://{self.apihost}:{self.apiport}/apicomms'
        params = {'ID':self.ID, 'TYPE':self.TYPE, 'VER':self.VER, 'CLASS':'PING'}
        req=requests.get(url=self.url, params=params, timeout=10)
        if req.status_code == 200:
            print(f'TEST PING OK.')
            rsp = req.text
            print(f'RSP={rsp}')
        else:
            print(f'TEST PING FAIL. {req.status_code}')
        return
    
    def sendConfigBase(self):
        '''
        ID=PABLO&TYPE=SPXR3&VER=1.0.0&CLASS=CONF_BASE&UID=42125128300065090117010400000000&HASH=0x11
        '''
        self.set_ID('DLGTEST')
        self.set_TYPE('DLG')
        self.set_VER('1.1.0')
        self.url = f'http://{self.apihost}:{self.apiport}/apicomms'
        params = {'ID':self.ID, 'TYPE':self.TYPE, 'VER':self.VER, 'CLASS':'CONF_BASE', 'UID':'01234566789', 'HASH':'0x10'}
        req=requests.get(url=self.url, params=params, timeout=10)
        if req.status_code == 200:
            print(f'TEST CONF_BASE OK.')
            rsp = req.text
            print(f'RSP={rsp}')
        else:
            print(f'TEST CONF_BASE FAIL: {req.status_code}')
        return
   
    def sendConfigAinputs(self):
        '''
        ID=PABLO&TYPE=SPXR3&VER=1.0.0&CLASS=CONF_AINPUTS&HASH=0x10
        '''
        self.set_ID('DLGTEST')
        self.set_TYPE('SPXR3')
        self.set_VER('1.1.0')
        self.url = f'http://{self.apihost}:{self.apiport}/apicomms'
        params = {'ID':self.ID, 'TYPE':self.TYPE, 'VER':self.VER, 'CLASS':'CONF_AINPUTS', 'HASH':'0x10'}
        req=requests.get(url=self.url, params=params, timeout=10)
        if req.status_code == 200:
            print(f'TEST CONF_AINPUTS OK.')
            rsp = req.text
            print(f'RSP={rsp}')
        else:
            print(f'TEST CONF_AINPUTS FAIL: {req.status_code}')
        return
    
    def sendConfigCounters(self):
        '''
        ID=PABLO&TYPE=SPXR3&VER=1.0.0&CLASS=CONF_COUNTERS&HASH=0x10
        '''
        self.set_ID('DLGTEST')
        self.set_TYPE('SPXR3')
        self.set_VER('1.1.0')
        self.url = f'http://{self.apihost}:{self.apiport}/apicomms'
        params = {'ID':self.ID, 'TYPE':self.TYPE, 'VER':self.VER, 'CLASS':'CONF_COUNTERS', 'HASH':'0x10'}
        req=requests.get(url=self.url, params=params, timeout=10)
        if req.status_code == 200:
            print(f'TEST CONF_COUNTERS OK.')
            rsp = req.text
            print(f'RSP={rsp}')
        else:
            print(f'TEST CONF_COUNTERS FAIL: {req.status_code}')
        return
    
    def sendConfigModbus(self):
        '''
        ID=PABLO&TYPE=SPXR3&VER=1.0.0&CLASS=CONF_MODBUS&HASH=0x10
        '''
        self.set_ID('DLGTEST')
        self.set_TYPE('SPXR3')
        self.set_VER('1.1.0')
        self.url = f'http://{self.apihost}:{self.apiport}/apicomms'
        params = {'ID':self.ID, 'TYPE':self.TYPE, 'VER':self.VER, 'CLASS':'CONF_MODBUS', 'HASH':'0x10'}
        req=requests.get(url=self.url, params=params, timeout=10)
        if req.status_code == 200:
            print(f'TEST CONF_MODBUS OK.')
            rsp = req.text
            print(f'RSP={rsp}')
        else:
            print(f'TEST CONF_MODBUS FAIL: {req.status_code}')
        return
    
    def sendData(self):
        '''
        ID=PABLO&TYPE=SPXR3&VER=1.1.0&CLASS=DATA&DATE=230321&TIME=094504&A0=1.24&A1=3.45&A2=7.89&C0=0.120&C1=10.400&bt=12.49
        '''
        self.set_ID('DLGTEST')
        self.set_TYPE('SPXR3')
        self.set_VER('1.1.0')
        self.url = f'http://{self.apihost}:{self.apiport}/apicomms'
        params = {'ID':self.ID, 'TYPE':self.TYPE, 'VER':self.VER, 'CLASS':'DATA', 'DATE':'230321','TIME':'094504',
                  'A0':'1.24','A1':'3.45','A2':'7.89','C0':'0.120','C1': '10.400','bt':'12.49'}
        req=requests.get(url=self.url, params=params, timeout=10)
        if req.status_code == 200:
            print(f'TEST DATA OK.')
            rsp = req.text
            print(f'RSP={rsp}')
        else:
            print(f'TEST DATA FAIL: {req.status_code}')
        return

    def set_ID(self,ID):
        self.ID = ID

    def get_ID(self):
        return self.ID
    
    def set_VER(self,VER):
        self.VER = VER

    def get_VER(self):
        return self.VER
    
    def set_TYPE(self,TYPE):
        self.TYPE = TYPE

    def get_TYPE(self):
        return self.TYPE
    
    def set_apihost(self,apihost):
        self.apihost = apihost

    def get_apihost(self):
        return self.apihost
    
    def set_apiport(self,apiport):
        self.apiport = apiport

    def get_apiport(self):
        return self.apiport
    
if __name__ == '__main__':
    
    test = ApicommsTestDlg()
    test.sendPing()
    test.sendConfigBase()
    test.sendConfigAinputs()
    test.sendConfigCounters()
    test.sendConfigModbus()
    test.sendData()




