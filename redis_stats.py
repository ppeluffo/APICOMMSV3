#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python
'''
Script que lee las stats de la BD redis y genera un informe
'''
import requests
import datetime as dt

HOST='192.168.0.8'
PORT='5100'
MAXTIMEOUT=15

def read_dstats():
    '''
    Funcion que se conecta a la aPI
    '''
    url = f'http://{HOST}:{PORT}/apiredis/stats'
    try:
        res = requests.get(url=url,timeout=10 )
        if res.status_code == 200:
            d_res = res.json()
            return d_res
        else:
            print(f'ERROR: request status={res.status_code}')
            return
    except requests.exceptions.RequestException as err: 
        print('ERROR: Redis request exception, Err:{err}')
        #

if __name__ == '__main__':

    now = dt.datetime.now()
    #
    d_stats = read_dstats()
    d_results = {}
    #
    for unit in d_stats:
        last_connection = dt.datetime.strptime(d_stats[unit],"%y-%m-%d %H:%M:%S")
        delta_time_in_seconds = int(( now - last_connection ).total_seconds()/60)
        if delta_time_in_seconds > MAXTIMEOUT:
            d_results[unit] = delta_time_in_seconds
            #print(f'{unit},DT={delta_time_in_seconds}')
    #
    # Ordeno los resultados
    d_r = dict(sorted(d_results.items(), key=lambda item: item[1]))
    # Los imprimo:
    for i,unit in enumerate(d_r):
        print(f'{i:03d}: {unit}, secs={d_r[unit]}')

