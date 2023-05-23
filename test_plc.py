#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python
'''
Se usa para mandar datos a la API como si fuesemos un PLC.

REF: https://stackoverflow.com/questions/14365027/python-post-binary-data

REF: https://stackoverflow.com/questions/9029287/how-to-extract-http-response-body-from-a-python-requests-call
'''
import requests

API_SERVER='127.0.0.1'
API_PORT='5000'

if __name__ == '__main__':

    url = f'http://{API_SERVER}:{API_PORT}/apicomms'
    params = { 'ID':'PLCTEST','VER':'1.0.0','TYPE':'PLCR3'}
    data = b'f\xe6\xf6Bdx\x00\xcd\xcc\x01B\x14(\x8dU'
    headers={'Content-Type': 'application/octet-stream'}

    res = requests.post( url=url, params=params, data=data, headers=headers)
    print(f'response_code={res.status_code}')