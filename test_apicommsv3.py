#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python


import requests
import argparse
import json


class TestApiRedis():

    def __init__(self):
        self.host = None
        self.port = None
        self.unit = None
        self.fw = None
        self.entry = None
        self.debugid = None

    def set_debugid(self, debugid):
        self.debugid = debugid

    def set_host(self, host):
        self.host = host

    def set_port(self, port):
        self.port = port

    def set_unit(self, unit):
        self.unit = unit

    def set_fw(self, fw):
        self.fw = fw

    def set_entry(self, entry):
        self.entry = entry
        
    def process_entry(self):
        if self.entry == 'ping':
            self.ping()
        elif self.entry == 'get_debugid':
            self.GET_debugid()
        elif self.entry == 'put_debugid':
            self.PUT_debugid()
        elif self.entry == 'get_config':
            self.GET_config()


    def ping(self):
        '''
        '''
        url = f'http://{self.host}:{self.port}/apiredis/ping'
        print(f'PING url={url}')
        try:
            req=requests.get(url=url)
        except requests.exceptions.RequestException as err: 
            print('REDIS NOT CONNECTED. EXIT')
            print(f'Err: {err}')
            return

        if req.status_code == 200:
                print(f'PING OK.')
        else:
            print(f'PING FAIL. {req.status_code}')
        return
    
    def GET_debugid(self):
        '''
        '''
        url = f'http://{self.host}:{self.port}/apiredis/debugid'
        print(f'GET_DEBUGID url={url}')
        try:
            req=requests.get(url=url)
        except requests.exceptions.RequestException as err: 
            print('REDIS NOT CONNECTED. EXIT')
            print(f'Err: {err}')
            return
        
        if req.status_code == 200:
            d_rsp = json.loads(req.json())
            debugId=d_rsp['debugid']
            print(f'CONF_DEBUGID <{debugId}> OK.')
        else:
            print(f'CONF_DEBUGID FAIL. {req.status_code}')
        return
    
    def PUT_debugid(self):
        '''
        '''
        url = f'http://{self.host}:{self.port}/apiredis/debugid'
        print(f'SET_DEBUGID url={url}')
        d = {'debugid':self.debugid}
        try:
            req=requests.put(url=url, json=d)
        except requests.exceptions.RequestException as err: 
            print('REDIS NOT CONNECTED. EXIT')
            print(f'Err: {err}')
            return
        
        if req.status_code == 200:
            print('SET_DEBUGID OK.')
        else:
            print(f'SET_DEBUGID FAIL. {req.status_code}')
        return

    def GET_config(self):
        '''
        '''
        url = f'http://{self.host}:{self.port}/apiredis/config'
        print(f'GET_CONFIG url={url}')
        params = {'unit':self.unit}
        try:
            req=requests.get(url=url, params=params)
        except requests.exceptions.RequestException as err: 
            print('REDIS NOT CONNECTED. EXIT')
            print(f'Err: {err}')
            return
        
        if req.status_code == 200:
            jd_rsp = req.json()
            d_rsp = json.loads(jd_rsp)
            print(f'CONFIG={d_rsp}')
        else:
            print(f'CONFIG FAIL. {req.status_code}')
        return       

def process_arguments():
    '''
    Proceso la linea de comandos.
    d_vp es un diccionario donde guardamos todas las variables del programa
    Corrijo los parametros que sean necesarios
    '''

    parser = argparse.ArgumentParser(description='Testing del sistema APICOMMSV3')
    parser.add_argument('-a', '--api', dest='api', action='store', default='apicomms',
                        help='API a testear: apicomms, apiredis, apiconf')
    parser.add_argument('-i', '--ip', dest='host', action='store', default='127.0.0.1',
                        help='IP del servicio de la Api')
    parser.add_argument('-p', '--port', dest='port', action='store', default='5000',
                        help='PORT del servicio de la APi (apicomms:5000, apiredis:5100, apiconf:5200)')
    parser.add_argument('-d', '--unit', dest='unit', action='store', default='DLGTEST',
                        help='ID de la unidad a usar')
    parser.add_argument('-f', '--fw', dest='fw', action='store', default='1.1.0',
                        help='Version del firmware a usar en los frames')
    parser.add_argument('-e', '--entry', dest='entrypoint', action='store', default='',
                        help='Nombre del entrypoint de la api')
    parser.add_argument('-', '--debugid', dest='debugid', action='store', default='',
                        help='id de unidad a debugear')

    args = parser.parse_args()
    d_args = vars(args)
    return d_args

def print_entrypoints():
    print('APIREDIS:')
    print('-ping, get_debugid')


if __name__ == '__main__':

    # Diccionario con variables generales para intercambiar entre funciones
    d_args = process_arguments()

    print('Arguments:')
    print(f"  API={d_args['api']}")
    print(f"  IP={d_args['host']},PORT={d_args['port']}")
    print(f"  UNIT={d_args['unit']},FW={d_args['fw']}")
    print(f"  ENTRY={d_args['entrypoint']}")

    if d_args['api'] == 'apiredis':
        test = TestApiRedis()
        test.set_host(d_args['host'])
        test.set_port(d_args['port'])
        test.set_unit(d_args['unit'])
        test.set_fw(d_args['fw'])
        test.set_debugid(d_args['debugid'])
        test.set_entry(d_args['entrypoint'])
        test.process_entry()

