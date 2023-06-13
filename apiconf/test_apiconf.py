#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python
'''
Script que prueba todas los entrypoints implementados en la APIconf.
'''

import requests
import json

DLG_CONF_TEMPLATE = {'ANALOGS': {
                        'A0': {'ENABLE':'TRUE', 'IMAX': '20','IMIN': '4','MMAX': '10','MMIN': '0','NAME': 'HTQ','OFFSET': '0'},
                        'A1': {'ENABLE':'FALSE','IMAX': '20','IMIN': '4','MMAX': '10','MMIN': '0','NAME': 'X','OFFSET': '0'},
                        'A2': {'ENABLE':'FALSE','IMAX': '20','IMIN': '4','MMAX': '10','MMIN': '0','NAME': 'X','OFFSET': '0'}
                        },
            'BASE': {'ALMLEVEL': '10','FIRMWARE': '4.0.0a','SAMPLES': '1',
                     'PWRS_HHMM1': '1800','PWRS_HHMM2': '1440','PWRS_MODO': '0',
                     'TDIAL': '900','TPOLL': '30'
                     },
            'COUNTERS': {
                       'C0': {'ENABLE':'TRUE','MAGPP': '0.01','NAME': 'q0','MODO':'CAUDAL'},
                       'C1': {'ENABLE':'FALSE','MAGPP': '0.01','NAME': 'X','MODO':'CAUDAL'}
                        },
            'MODBUS': {
                'ENABLE':'TRUE',
                'LOCALADDR':'2',
                'M0': { 'ENABLE':'TRUE','NAME': 'CAU0', 'SLA_ADDR': '2','ADDR': '2069','NRO_RECS': '2','FCODE': '3','TYPE': 'FLOAT', 'CODEC': 'C1032','POW10': '0' },
                'M1': { 'ENABLE':'FALSE','NAME': 'X', 'SLA_ADDR': '2','ADDR': '2069','NRO_RECS': '2','FCODE': '3','TYPE': 'FLOAT', 'CODEC': 'C1032','POW10': '0' },
                'M2': { 'ENABLE':'FALSE','NAME': 'X', 'SLA_ADDR': '2','ADDR': '2069','NRO_RECS': '2','FCODE': '3','TYPE': 'FLOAT', 'CODEC': 'C1032','POW10': '0' },
                'M3': { 'ENABLE':'FALSE','NAME': 'X', 'SLA_ADDR': '2','ADDR': '2069','NRO_RECS': '2','FCODE': '3','TYPE': 'FLOAT', 'CODEC': 'C1032','POW10': '0' },
                'M4': { 'ENABLE':'FALSE','NAME': 'X', 'SLA_ADDR': '2','ADDR': '2069','NRO_RECS': '2','FCODE': '3','TYPE': 'FLOAT', 'CODEC': 'C1032','POW10': '0' }
            }
        }

class TestApiConf:

    def __init__(self):
        self.host = '127.0.0.1'
        self.port = '5200'

    def set_host(self,host='192.168.0.20'):
        self.host = host

    def get_host(self):
        return self.host
    
    def set_port(self,port='5200'):
        self.port = port

    def get_port(self):
        return self.port
  
    def configuracion_get(self,id='DLGTEST'):
        url = f'http://{self.host}:{self.port}/apiconf/config'
        req=requests.get(url=url,params={'unit':id})
        if req.status_code == 200:
            jd_conf=req.json()
            d_conf=json.loads(jd_conf)
            print(f'GET_CONFIG <{id}> OK.')
            print(f'JD_CONF={jd_conf}')
            print(f'D_CONF={d_conf}')
        else:
            print(f'GET CONFIG FAIL. {req.status_code}')
        return

    def configuracion_post(self, id='DLGTEST', d_conf=DLG_CONF_TEMPLATE):
        '''
        '''
        print(d_conf)
        jd_conf = json.dumps(d_conf)
        url = f'http://{self.host}:{self.port}/apiconf/config'
        req=requests.post(url=url,params={'unit':id}, json=jd_conf)
        if req.status_code == 200:
            print(f'SET_CONFIG <{id}> OK.')
        else:
            print(f'SET_CONFIG FAIL. {req.status_code}')
        return

if __name__ == '__main__':

    api = TestApiConf()
 #   api.configuracion_post()
    api.configuracion_get()
