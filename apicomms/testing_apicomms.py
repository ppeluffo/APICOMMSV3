#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python
'''
Script de testeo de la apicomms.
Se encarga de enviar frames (todos los tipos), todos las versiones, todos los SP?
y mostrar las respuestas.
'''

import requests

versiones = { 'SPX_AVRDA':['1.1.0','1.2.0'],
             'SPX_XMEGA':['1.1.0', '1.2.0'],
             'SPQ_AVRDA':['1.1.0', '1.2.0']
             }

dlgid = 'DNOTQ001'

url_base = 'http://localhost:5001/apidlg?'

frames = {
    'ping':'CLASS=PING',
    'base':'CLASS=CONF_BASE&UID=ABDCZXYT&HASH=0x12',
    'ainputs':'CLASS=CONF_AINPUTS&HASH=0x15',
    'counters':'CLASS=CONF_COUNTERS&HASH=0x12',
    'modbus':'CLASS=CONF_MODBUS&HASH=0x12',
    'piloto':'CLASS=CONF_PILOTO&HASH=0x12',
    'consigna':'CLASS=CONF_CONSIGNA&HASH=0x12',
    'data':'CLASS=DATA&VER=1.1.0&DATE=230321&TIME=094504&A0=0.00&A1=0.00&A2=0.00&C0=0.000&C1=0.000&bt=12.496',
    'recover':'CLASS=RECOVER&UID=ABDCZXYT' 
    }

if __name__ == '__main__':

    for tipo, l_versiones in versiones.items():
        for ver in l_versiones:
            for frame, frame_url in frames.items():
                if frame == 'recover':
                    url = url_base + f'ID=DEFAULT&TYPE={tipo}&VER={ver}&{frame_url}'
                else:
                    url = url_base + f'ID={dlgid}&TYPE={tipo}&VER={ver}&{frame_url}'
                print(f'{tipo}:{ver}')
                print(url)
                rsp = requests.get(url,timeout=10)
                print(f'RSP_STATUS_CODE={rsp.status_code}')
                if rsp.status_code == 200:
                    print(f'RSP_RESPONSE={rsp.text}')
                print()


