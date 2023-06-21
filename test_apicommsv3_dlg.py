#!/home/pablo/Spymovil/python/proyectos/venv_apicomms/bin/python
'''
Script de testing del servidor apicommsV3 para dataloggers.
Se simulan N dataloggers enviando datos
'''

import pprint
import requests
import sys
from datetime import datetime, timedelta
import numpy as np
from multiprocessing import Process,Value, Lock, Event
import time
import os
import signal
import argparse

#APICOMMS_HOST = '127.0.0.1'
APICOMMS_HOST = '192.168.0.8'
APICOMMS_PORT = '5000'

#APICONF_HOST = '127.0.0.1'
APICONF_HOST = '192.168.0.8'
APICONF_PORT = '5200'

#NRO_UNIDADES = 20
#NRO_PROCESOS = 5
#INIT_DATE = '23-01-01 00:00'

# create a shared event
exit_event = Event()

def get_next_timestamp(timestamp):
    '''
    '''
    new_timestamp = timestamp + timedelta(minutes=1)
    return new_timestamp

def get_new_value(value,seed=22):
    '''
    '''
    np.random.seed(seed)
    step_set = [-1, 0, 1]
    step = np.random.choice(a=step_set, size=1)[0]
    new_value = value * ( 1 + step / 10)
    if new_value < 1:
        new_value = 1 + np.abs(step/10)
    #
    return new_value

def simular_datos( init_date, init_val, nro_puntos):
    
    date = datetime.strptime(init_date, '%y-%m-%d %H:%M')
    value = init_val
    for i in range(nro_puntos):
        date = get_next_timestamp(date)
        value = get_new_value(value)
        print(f'{date}:{value}')

def asignar_dataloggers_a_procesos(l_unidades):
    '''
    Genera una lista por proceso y reparte las unidades entre todas
    Devuelve una lista de listas
    '''
    l_unidades_proceso = [ [] for i in range(NRO_PROCESOS)]
    idp = 0
    for unidad in l_unidades:
        l_unidades_proceso[idp].append(unidad)
        idp = idp + 1
        if idp == NRO_PROCESOS:
            idp = 0
    return l_unidades_proceso

def proces_simular_dataloggers(nro_frames, lck, l_dataloggers):
    '''
    Proceso que recibe una lista de dataloggers y genera una carga constante 
    real de datos.
    Cada datalogger debe transmitir c/1 minuto.
    '''
    pid = os.getpid()
    np.random.seed(pid)
    nro_unidades = len(l_dataloggers)
    tiempo_entre_frames = int(60 / nro_unidades)
    date = datetime.strptime(INIT_DATE, '%y-%m-%d %H:%M')
    #
    l_params_dates = [ date for i in range(nro_unidades)]
    l_params_values_pA = [ (1+np.random.random()*3) for i in range(nro_unidades)]
    l_params_values_pB = [ (1+np.random.random()*3) for i in range(nro_unidades)]
    l_params_values_CAU0 = [ (1+np.random.random()*3) for i in range(nro_unidades)]
    l_params_values_bt = [ (12+np.random.random()) for i in range(nro_unidades)]
    #
    delay = np.random.randint(1,10)
    print(f'Process {pid}:{tiempo_entre_frames}:{delay}:{l_dataloggers}')
    # Espero para arrancar
    time.sleep( delay )
    while True:
        for i,uid in enumerate(l_dataloggers):
            l_params_dates[i] = get_next_timestamp( l_params_dates[i] )
            l_params_values_pA[i] = get_new_value(l_params_values_pA[i], pid)
            l_params_values_pB[i] = get_new_value(l_params_values_pB[i], pid)
            l_params_values_CAU0[i] = get_new_value(l_params_values_CAU0[i], pid)
            with lck:
                nro_frames.value += 1
            #
            url = f'http://{APICOMMS_HOST}:{APICOMMS_PORT}/apicomms'
            params = {'ID':uid,
                      'TYPE':'SPXR3', 
                      'VER':'1.1.0', 
                      'CLASS':'DATA', 
                      'DATE':'230321',
                      'TIME':'094504',
                      'pA':f'{l_params_values_pA[i]:0.3f}',
                      'pB':f'{l_params_values_pB[i]:0.3f}',
                      'CAU0':f'{l_params_values_CAU0[i]:0.3f}',
                      'bt':f'{l_params_values_bt[i]:0.3f}'
                      }
            req=requests.get(url=url, params=params, timeout=10)
            if req.status_code != 200:
                print(f'SEND FAIL: {pid}')
            #print(f'{pid}::{uid}:{l_params_dates[i]}=>{l_params_values_pA[i]:0.3f},{l_params_values_pB[i]:0.3f},{l_params_values_CAU0[i]:0.3f},{l_params_values_bt[i]:0.3f}')
            time.sleep(tiempo_entre_frames)
            #
            if exit_event.is_set():
                sys.exit(0)
    #                      

class dataloggers():
    '''
    '''
    def __init__(self):
        self.l_unidades = None
        self.template = None

    def get_l_unidades(self):
        return self.l_unidades
    
    def get_template(self):
        return self.template
    
    def generar_unidades(self,nro_unidades):
        '''
        Genera una lista con los nombres de las unidades que vamos
        a usar en el testing
        '''
        self.l_unidades = [f'DLGTEST{i:02d}' for i in range(nro_unidades)]

    def read_template(self):
        '''
        Leemos desde la apiconf el template de la ultima version
        '''
        url = f'http://{APICONF_HOST}:{APICONF_PORT}/apiconf/template'
        params={'ver':'latest','type':'DLG'}
        req=requests.get(url=url,params=params, timeout=10)
        if req.status_code == 200:
            d_rsp = req.json()
            self.template = d_rsp.get('template',{})
        else:
            print('Request config template Error')
         
    def configurar_unidades(self, verbose=False):
        '''
        Para que la prueba no falle, las unidades deben estar configuradas en la bd.
        Usamos la configuracion por defecto porque no la usamos. Es solo para que no
        se generen problemas c/dato que enviamos.
        '''
        url = f'http://{APICONF_HOST}:{APICONF_PORT}/apiconf/config'
        if verbose:
            print(f'Configurando {len(self.l_unidades)}...')
        mod=int(len(self.l_unidades)/20)
        for i,unit in enumerate(self.l_unidades):
            params={'unit':unit}
            req=requests.post(url=url,params=params, json=self.template, timeout=10)
            if i % mod == 0:
                print(f'{i:03d} ', end='', flush=True)
            if req.status_code != 200:
                print(f'Config unit {unit} Error')
        print('')
        #   

def clt_C_handler(signum):
    exit_event.set()

def process_arguments():
    '''
    Proceso la linea de comandos.
    d_vp es un diccionario donde guardamos todas las variables del programa
    Corrijo los parametros que sean necesarios
    '''

    parser = argparse.ArgumentParser(description='Testing del sistema APICOMMSV3')
    parser.add_argument('-p', '--process', dest='nro_procesos', action='store', default='5',
                        help='Numero de procesos')
    parser.add_argument('-u', '--unidades', dest='nro_unidades', action='store', default='20',
                        help='Numero de unidades')
    parser.add_argument('-d', '--date', dest='initial_date', action='store', default='23-01-01 00:00',
                        help='Fecha de inicio de frames')
    parser.add_argument('-a', '--apicomms_host', dest='apicomms_host', action='store', default='127.0.0.1',
                        help='IP del host de apicomms')
    parser.add_argument('-a', '--apiconf_host', dest='apiconf_host', action='store', default='127.0.0.1',
                        help='IP del host de apiconf')
    
    args = parser.parse_args()
    d_args = vars(args)
    return d_args

if __name__ == '__main__':

    signal.signal(signal.SIGINT, clt_C_handler)

    d_args = process_arguments()
    NRO_PROCESOS = int( d_args['nro_procesos'],10)
    NRO_UNIDADES = int( d_args['nro_unidades'],10)
    INIT_DATE = d_args['initial_date']

    print('Arguments:')
    print(f'    NRO_UNIDADES={NRO_UNIDADES}')
    print(f'    NRO_PROCESOS={NRO_PROCESOS}')
    print(f'    INIT_DATE={INIT_DATE}')

    dlg = dataloggers()
    dlg.generar_unidades(NRO_UNIDADES)
    #print(f'Lista de unidades: {dlg.get_l_unidades()}')
    dlg.read_template()
    #print('Template:')
    #pprint.pprint(dlg.get_template())
    print('Configurando unidades...')
    dlg.configurar_unidades(verbose=True)
    print('Unidades configuradas...')
    #simular_datos('23-01-01 00:00', 3, 1440)

    nro_frames = Value('i',0)
    lck = Lock()
    #
    #
    l_unidades_proceso = asignar_dataloggers_a_procesos(dlg.get_l_unidades())
    l_process = []
    for l in l_unidades_proceso:
        p = Process(target = proces_simular_dataloggers, args = (nro_frames, lck, l))
        l_process.append(p)
        p.start()
        
    #
    minutes_running = 0
    while True:
        time.sleep(60)
        with lck:
            i=nro_frames.value
            nro_frames.value = 0
        minutes_running += 1
        print(f'MAIN: {minutes_running:02d} frames={i}')
        if exit_event.is_set():
            sys.exit(0)


    
