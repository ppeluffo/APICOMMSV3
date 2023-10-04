#!/usr/bin/python3
'''
Scritp de monitoreo de estado de energia eléctrica.
Se hacen pings hacia la IP publica del router de Antel cada 1 minuto
con un timeout de 10 secs.
Luego de 5 pings sin respuesta, asumimos que no hay corriente eléctrica
y apagamos el equipo donde estamos corriendo.
'''

from time import sleep
import os
import argparse

TARGET_IP = '190.64.69.33'
TIEMPO_ENTRE_PINGS = 60
PING_TIMEOUT = 10
MAX_PING_ERRORS = 5
PING_RESPONSES = [ "Time out", "unreachable", "Unreachable"]

def ping(host=TARGET_IP,timeout=10):
    '''
    Envio 1 solo frame de ping ( -c 1 ) y espero hasta 10 secs (-W 10)
    '''
    response = os.popen(f"ping -c 1 -W {timeout} {host}").read()
    if any( word in response for word in PING_RESPONSES):
        return False
    return True

def shutdown():
    '''
    Apaga en modo suave el servidor.
    https://stackoverflow.com/questions/35546497/how-to-shutdown-and-then-reboot-linux-machine-using-python-language-or-shell-scr
    '''
    os.system('systemctl reboot -i')


def process_arguments():
    '''
    Proceso la linea de comandos.
    d_vp es un diccionario donde guardamos todas las variables del programa
    Corrijo los parametros que sean necesarios
    '''

    parser = argparse.ArgumentParser(description='Monitor de 220V')
    parser.add_argument('-d', '--destination', dest='target_ip', action='store', default=TARGET_IP,
                        help='Direccion ip destino')
    parser.add_argument('-s', '--sleep', dest='tiempo_entre_pings', action='store', default=TIEMPO_ENTRE_PINGS,
                        help='Numero de unidades')
    parser.add_argument('-t', '--timeout', dest='ping_timeout', action='store', default=PING_TIMEOUT,
                        help='Timeout de pings')
    parser.add_argument('-e', '--max_errors', dest='max_errors', action='store', default=MAX_PING_ERRORS,
                        help='Maximo nro.errores para shutdown')
  
    args = parser.parse_args()
    d_args = vars(args)
    return d_args


if __name__ == '__main__':
    #
    arguments = process_arguments()

    target_ip = arguments['target_ip']
    tiempo_entre_pings = int(arguments['tiempo_entre_pings'])
    ping_timeout = int(arguments['ping_timeout'])
    max_errors = int(arguments['max_errors'])

    print(f'TARGET_IP={target_ip}')
    print(f'TIEMPO_ENTRE_PINGS={tiempo_entre_pings}')
    print(f'PING TIMEOUT={ping_timeout}')
    print(f'MAX ERROR={max_errors}')

    contador_errores = 0

    #
    while True:
        sleep(tiempo_entre_pings)
        if not ping(target_ip,ping_timeout):
            contador_errores += 1
            print(f'>Monitor Errores Energía eléctrica: ERROR {contador_errores}')
        else:
            contador_errores = 0
            print(f'>Monitor Errores Energía eléctrica: OK')

        if contador_errores == max_errors:
            print('>Monitor Errores Energía eléctrica: SHUTDOWN ordenado')
            shutdown()
            break

