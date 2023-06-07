#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python
'''
Script que prueba todas los entrypoints implementados en la API redis.
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
                'LOCALADDR':'1',
                'M0': { 'ENABLE':'TRUE','NAME': 'CAU0', 'SLA_ADDR': '2','ADDR': '2069','NRO_RECS': '2','FCODE': '3','TYPE': 'FLOAT', 'CODEC': 'C1032','POW10': '0' },
                'M1': { 'ENABLE':'FALSE','NAME': 'X', 'SLA_ADDR': '2','ADDR': '2069','NRO_RECS': '2','FCODE': '3','TYPE': 'FLOAT', 'CODEC': 'C1032','POW10': '0' },
                'M2': { 'ENABLE':'FALSE','NAME': 'X', 'SLA_ADDR': '2','ADDR': '2069','NRO_RECS': '2','FCODE': '3','TYPE': 'FLOAT', 'CODEC': 'C1032','POW10': '0' },
                'M3': { 'ENABLE':'FALSE','NAME': 'X', 'SLA_ADDR': '2','ADDR': '2069','NRO_RECS': '2','FCODE': '3','TYPE': 'FLOAT', 'CODEC': 'C1032','POW10': '0' },
                'M4': { 'ENABLE':'FALSE','NAME': 'X', 'SLA_ADDR': '2','ADDR': '2069','NRO_RECS': '2','FCODE': '3','TYPE': 'FLOAT', 'CODEC': 'C1032','POW10': '0' }
            }
        }

PLC_CONF_TEMPLATE = { 'MEMBLOCK':{
        'RCVD_MBK_DEF': [
            ['UPA1_CAUDALIMETRO', 'float', 0],['UPA1_STATE1', 'uchar', 1],['UPA1_POS_ACTUAL_6', 'short', 8],
            ['UPA2_CAUDALIMETRO', 'float', 0],['BMB_STATE18', 'uchar', 1],['BMB_STATE19', 'uchar', 1]
        ],
        'SEND_MBK_DEF': [
            ['UPA1_ORDER_1', 'short', 1],['UPA1_CONSIGNA_6', 'short', 2560],['ESP_ORDER_8', 'short', 200],
            ['ALTURA_TANQUE_KIYU_1', 'float', 2560],['ALTURA_TANQUE_KIYU_2', 'float', 2560],
            ['PRESION_ALTA_SJ1', 'float', 0],['PRESION_BAJA_SQ1', 'float', 0]
        ],
        'RCVD_MBK_LENGTH':15,
        'SEND_MBK_LENGTH':24
        },
        'REMVARS':{
            'KIYU001': [
                ('HTQ1', 'ALTURA_TANQUE_KIYU_1'), 
                ('HTQ2', 'ALTURA_TANQUE_KIYU_2')
            ],
            'SJOSE001': [
                ('PA', 'PRESION_ALTA_SJ1'), 
                ('PB', 'PRESION_BAJA_SQ1')
            ]
        }
    }

D_DATA_TEMPLATE = {'DATE': '230519','TIME': '144412','HTQ': '-2.50','q0': '0.000','AI0': 'nan','QS': '0.000','bt': '12.480'}

D_ORDENES_ATVISE_TEMPLATE = {"UPA1_ORDER_1": 101, "UPA1_CONSIGNA_6": 102, "ESP_ORDER_8": 103}

class TestApiRedis:

    def __init__(self):
        self.host = '127.0.0.1'
        self.port = '5100'

    def set_host(self,host='192.168.0.20'):
        self.host = host

    def get_host(self):
        return self.host
    
    def set_port(self,port='5100'):
        self.port = port

    def get_port(self):
        return self.port
    
    def delete(self, id='DLGTEST'):
        '''
        '''
        url = f'http://{self.host}:{self.port}/apiredis/delete'
        req=requests.delete(url=url, params={'unit':id})
        if req.status_code == 200:
            print(f'DELETE <{id}> OK.')
        else:
            print(f'DELETE <{id}> FAIL. {req.status_code}')
        return
    
    def configuracion_debugId(self):
        '''
        '''
        url = f'http://{self.host}:{self.port}/apiredis/configuracion/debugid'
        req=requests.get(url=url)
        if req.status_code == 200:
            d_rsp = json.loads(req.json())
            debugId=d_rsp['debugId']
            print(f'CONF_DEBUGID <{debugId}> OK.')
        else:
            print(f'CONF_DEBUGID FAIL. {req.status_code}')
        return
    
    def configuracion_put(self,id='DLGTEST', d_conf = DLG_CONF_TEMPLATE):
        '''
        '''
        jd_conf = json.dumps(d_conf)
        url = f'http://{self.host}:{self.port}/apiredis/configuracion'
        req=requests.put(url=url,params={'unit':id}, json=jd_conf)
        if req.status_code == 200:
            print(f'SET_CONFIG <{id}> OK.')
        else:
            print(f'SET_CONFIG FAIL. {req.status_code}')
        return
    
    def configuracion_get(self,id='DLGTEST',d_conf_ref = DLG_CONF_TEMPLATE):
        url = f'http://{self.host}:{self.port}/apiredis/configuracion'
        req=requests.get(url=url,params={'unit':id})
        if req.status_code == 200:
            jd_conf=req.json()
            d_conf=json.loads(jd_conf)
            if json.dumps(d_conf,sort_keys=True) == json.dumps(d_conf_ref,sort_keys=True):
                print(f'GET_CONFIG <{id}> OK.')
            else:
                print(f'GET_CONFIG OK w/DIFF')
                print(f'DCONF_REF={d_conf_ref}')
                print(f'DCONF_REQ={d_conf}')
        else:
            print(f'GET CONFIG FAIL. {req.status_code}')
        return
    
    def ordenes_put(self,id='DLGTEST', orden='RESET'):
        '''
        '''
        d={'ordenes':orden}
        jd=json.dumps(d)
        url = f'http://{self.host}:{self.port}/apiredis/ordenes'
        req=requests.put(url=url, params={'unit':id}, json=jd)
        if req.status_code == 200:
            print(f'SET ORDENES <{id}> OK')
        else:
            print(f'SET ORDENES <{id}> FAIL')
        return
    
    def ordenes_get(self, id='DLGTEST', orden_ref = 'RESET' ):
        '''
        '''
        url = f'http://{self.host}:{self.port}/apiredis/ordenes'
        req=requests.get(url=url,params={'unit':id})
        if req.status_code == 200:
            jd_rsp=req.json()
            d_ordenes=json.loads(jd_rsp)
            orden = d_ordenes['ordenes']
            if orden == orden_ref:
                print(f'GET ORDENES <{id}> OK.')
            else:
                print(f'GET ORDENES OK w/DIFF')
        else:
            print(f'GET ORDENES FAIL. {req.status_code}')
        return
    
    def dataline_put(self, id='DLGTEST', d_data = D_DATA_TEMPLATE):
        '''
        '''
        jd_data = json.dumps(d_data)
        url = f'http://{self.host}:{self.port}/apiredis/dataline'
        req=requests.put(url=url,params={'unit':id, 'type':'DLG'}, json=jd_data)
        if req.status_code == 200:
            print(f'PUT_DATALINE <{id}> OK.')
        else:
            print(f'PUT_DATALINE FAIL. {req.status_code}')
        return

    def dataline_get(self,id='DLGTEST', d_data_ref=D_DATA_TEMPLATE):
        url = f'http://{self.host}:{self.port}/apiredis/dataline'
        req=requests.get(url=url,params={'unit':id})
        if req.status_code == 200:
            jd_data=req.json()
            d_data=json.loads(jd_data)
            if json.dumps(d_data,sort_keys=True) == json.dumps(d_data_ref,sort_keys=True):
                print(f'GET DATA <{id}> OK.')
            else:
                print(f'GET DATA OK w/DIFF')
                print(f'DATA_REF={d_data_ref}')
                print(f'DATA_REQ={d_data}')
        else:
            print(f'GET DATA FAIL. {req.status_code}')
        return

    def ordenes_atvise_put(self,id='PLCTEST', d_ordenes_atvise=D_ORDENES_ATVISE_TEMPLATE):
        '''
        '''
        d={ 'ordenes_atvise': d_ordenes_atvise }
        jd=json.dumps(d)
        url = f'http://{self.host}:{self.port}/apiredis/ordenes/atvise'
        req=requests.put(url=url, params={'unit':id}, json=jd)
        if req.status_code == 200:
            print(f'SET ORDENES_ATVISE <{id}> OK')
        else:
            print(f'SET ORDENES_ATVISE <{id}> FAIL')
        return
    
    def ordenes_atvise_get(self, id='PLCTEST', d_ordenes_atvise_ref=D_ORDENES_ATVISE_TEMPLATE ):
        '''
        '''
        url = f'http://{self.host}:{self.port}/apiredis/ordenes/atvise'
        req=requests.get(url=url,params={'unit':id})
        if req.status_code == 200:
            jd =req.json()
            d =json.loads(jd)['ordenes_atvise']
            if json.dumps(d,sort_keys=True) == json.dumps(d_ordenes_atvise_ref,sort_keys=True):
                print(f'GET ORDENES_ATVISE <{id}> OK.')
            else:
                print(f'GET ORDENES_ATVISE OK w/DIFF')
                print(f'DCONF_REF={d_ordenes_atvise_ref}')
                print(f'DCONF_REQ={d}')
        else:
            print(f'GET ORDENES_ATVISE. {req.status_code}')
        return
    

if __name__ == '__main__':

    api = TestApiRedis()

    api.configuracion_debugId()
    # DLG
    id = 'DLGTEST'
    print(f'Testing DLG c/id={id}')
    api.delete(id=id)
    api.configuracion_put(id=id, d_conf=DLG_CONF_TEMPLATE )
    api.configuracion_get(id=id, d_conf_ref=DLG_CONF_TEMPLATE)
    api.ordenes_put(id=id)
    api.ordenes_get(id=id)
    api.dataline_put(id=id, d_data=D_DATA_TEMPLATE)
    api.dataline_get(id=id, d_data_ref=D_DATA_TEMPLATE)
    #
    # PLC
    id='PLCTEST'
    print(f'Testing PLC c/id {id}')
    api.delete(id=id)
    api.configuracion_put(id=id, d_conf=PLC_CONF_TEMPLATE )
    api.configuracion_get(id=id, d_conf_ref=PLC_CONF_TEMPLATE)
    api.ordenes_atvise_put(id='PLCTEST', d_ordenes_atvise=D_ORDENES_ATVISE_TEMPLATE)
    api.ordenes_atvise_get(id='PLCTEST', d_ordenes_atvise_ref=D_ORDENES_ATVISE_TEMPLATE)










