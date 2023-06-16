#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python
'''
Script de testing del servidor apicommsV3 para dataloggers.
Se simulan N dataloggers enviando datos
'''

import requests
import sys

APICONF_HOST = '127.0.0.1'
APICONF_PORT = '5200'

def generar_unidades(nro_unidades):
    '''
    Genera una lista con los nombres de las unidades que vamos
    a usar en el testing
    '''
    l_unidades = [f'DLGTEST{i:02d}' for i in range(nro_unidades)]
    return l_unidades

def read_config_template():
    url = f'http://{APICONF_HOST}:{APICONF_PORT}/apiconf/template'
    params={'ver':'latest','type':'DLG'}
    req=requests.get(url=url,params=params, timeout=10)
    if req.status_code == 200:
        d_rsp = req.json()
        d_config_template = d_rsp.get('template',{})
    else:
        print('Request config template Error')
        sys.exit(1) 
    return d_config_template
  
def configurar_unidades(l_unidades, d_config_template):
    '''
    Para que la prueba no falle, las unidades deben estar configuradas en la bd.
    Usamos la configuracion por defecto porque no la usamos. Es solo para que no
    se generen problemas c/dato que enviamos.
    '''
    # Leo la configuracion de la APICONF (template) y lo uso para configurar
    # las unidades.
    url = f'http://{APICONF_HOST}:{APICONF_PORT}/apiconf/config'
    for unit in l_unidades:
        params={'unit':unit}
        req=requests.post(url=url,params=params, json=d_config_template, timeout=10)
        if req.status_code != 200:
            print('Config unit Error')
            sys.exit(1)
    #

if __name__ == '__main__':

    l_unidades = generar_unidades(10)
    print(l_unidades)

    d_config_template = read_config_template()
    print(d_config_template)

    configurar_unidades(l_unidades, d_config_template)

