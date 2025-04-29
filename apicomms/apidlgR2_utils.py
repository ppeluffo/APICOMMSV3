#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python
'''
ERRORES 12XX

Esquema de versionado:

Versión principal (FUNCIONALIDADES): significa actualizaciones o cambios importantes, 
    que pueden incluir cambios incompatibles con versiones anteriores.
                    
Versión menor (PROTOCOLO): indica actualizaciones más pequeñas con nuevas características
    o mejoras, manteniendo la compatibilidad con versiones anteriores dentro de la misma versión principal.
                
Versión de parche (PATCHES): Representa correcciones de errores, parches o actualizaciones 
    menores que no introducen nuevas características, manteniendo además la compatibilidad 
    con versiones anteriores dentro de la misma versión mayor y menor.
                   
'''

import re
import requests
import json
import string
import random
import datetime


def tagLog(redis_url, args={}, verbose=True):

    timestamp = datetime.datetime.now()

    tag = args.pop('TAG', None)
    label = args.pop('LABEL', None)
    slog = f"TAG={tag} LB={label} TS={timestamp}"

    for k in args:
        slog += f" {k}={args.get(k,'NONE')}"
    if verbose:
        print(slog)

    # Inserto en la redis a travez de la API
    d_payload = {'log_data': slog}
    jd_payload = json.dumps(d_payload)
    r_datos = requests.put(redis_url + 'logqueuepush', json=jd_payload, timeout=10 )
    if r_datos.status_code != 200:
        # Si da error genero un mensaje pero continuo para no trancar al datalogger.
        print(f"(1102) process_frame_data INFO: ERROR AL GUARDAR LOG EN REDIS. Err=({r_datos.status_code}){r_datos.text}")
        print(redis_url)
        #
    return slog

def timestamp():
    return datetime.datetime.now()

def tag_generator(size=9, chars=string.ascii_uppercase + string.digits):
    """
    Genera un tag de 6 caracteres unico para identificar las conexiones
    https://stackoverflow.com/questions/2257441/random-string-generation-with-upper-case-letters-and-digits
    """
    return ''.join(random.choice(chars) for _ in range(size))


def u_hash(seed, line):
    '''
    Calculo un hash con el string pasado en line.
    Devuelve un entero
    Se utiliza el algoritmo de Pearson
    https://es.abcdef.wiki/wiki/Pearson_hashing
    La función original usa una tabla de nros.aleatorios de 256 elementos.
	Ya que son aleatorios, yo la modifico a algo mas simple.

    Es la misma implementacion que se usa en los dataloggers.
    '''

    hash_table = [ 93,  153, 124,  98, 233, 146, 184, 207, 215,  54, 208, 223, 254, 216, 162, 141,
		10,  148, 232, 115,   7, 202,  66,  31,   1,  33,  51, 145, 198, 181,  13,  95,
		242, 110, 107, 231, 140, 170,  44, 176, 166,   8,   9, 163, 150, 105, 113, 149,
		171, 152,  58, 133, 186,  27,  53, 111, 210,  96,  35, 240,  36, 168,  67, 213,
		12,  123, 101, 227, 182, 156, 190, 205, 218, 139,  68, 217,  79,  16, 196, 246,
		154, 116,  29, 131, 197, 117, 127,  76,  92,  14,  38,  99,   2, 219, 192, 102,
		252,  74,  91, 179,  71, 155,  84, 250, 200, 121, 159,  78,  69,  11,  63,   5,
		126, 157, 120, 136, 185,  88, 187, 114, 100, 214, 104, 226,  40, 191, 194,  50,
		221, 224, 128, 172, 135, 238,  25, 212,   0, 220, 251, 142, 211, 244, 229, 230,
		46,   89, 158, 253, 249,  81, 164, 234, 103,  59,  86, 134,  60, 193, 109,  77,
		180, 161, 119, 118, 195,  82,  49,  20, 255,  90,  26, 222,  39,  75, 243, 237,
		17,   72,  48, 239,  70,  19,   3,  65, 206,  32, 129,  57,  62,  21,  34, 112,
		4,    56, 189,  83, 228, 106,  61,   6,  24, 165, 201, 167, 132,  45, 241, 247,
		97,   30, 188, 177, 125,  42,  18, 178,  85, 137,  41, 173,  43, 174,  73, 130,
		203, 236, 209, 235,  15,  52,  47,  37,  22, 199, 245,  23, 144, 147, 138,  28,
		183,  87, 248, 160,  55,  64, 204,  94, 225, 143, 175, 169,  80, 151, 108, 122 ]

    h = seed
    for c in line:
        h = hash_table[h ^ ord(c)]
    return h

def format_response(reponse_text):
    '''
    Necesitamos este formateo para que los dlg. puedan parsear la respuesta
    '''
    #return f'<html><body><h1>{response}</h1></body></html>'
    return (f'<html>{reponse_text}</html>')

def str2int(s):
    '''
    Convierte un string a un nro.entero con la base correcta.
    '''
    if not isinstance(s, str):
        return 0
    if 'X' in s.upper():
        return int(s,16)
    return int(s)
        
def version2int (str_version):
    '''
    La version (VER) tiene un formato tipo A.B.C
    A: Funcionalidad
    B: Protocolo
    C: Patch
    Lo convertimos a un numero A*100 + B*10 + 0
    No devolvemos el patch. !!!  
    '''
    components = str_version.split('.')
    try:
        mayor = int(components[0]) * 100
    except:
        mayor = 0

    try:
        minor = int(components[1]) * 10
    except:
        minor = 0

    try:
        patch = int(re.sub(r"[A-Z,a-z,.]",'', components[2]))
    except:
        path = 0

    return mayor + minor
    # return str2int( re.sub(r"[A-Z,a-z,.]",'',str_version))

def read_debug_id(d_args=None):
    '''
    Consulta el nombre del equipo que debe logearse. Si hay error o no esta configurado
    devuelve 'UDEBUG'
    '''
    app = d_args.get('app',None)
    try:
        rsp = requests.get(d_args['url_redis'] + 'debugid', timeout=10 )
    except requests.exceptions.RequestException as err: 
        app.logger.info( f'(1200) read_debug_id ERROR: Redis request exception, Err:{err}')
        return 'UDEBUG'
        
    if rsp.status_code == 200:
        d = rsp.json()
        debugid = d.get('debugid','UDEBUG')
        return debugid
    else:
        app.logger.info(f"(1201) read_debug_id WARN: No debug unit, Err=({rsp.status_code}){rsp.text}")
        # Seteo uno por default.
        _=requests.put(d_args['url_redis'] + 'debugid', json={'debugid':'UDEBUG'}, timeout=10 )
    return 'UDEBUG'

def read_configuration(d_args=None, dlgid=None):
    '''
    Lee la configuracion de la unidad y la deja en self.d_conf. Retorna True/False.
    '''
    app = d_args.get('app',None)
    debugid = read_debug_id(d_args)

    # Intento leer desde REDIS.
    try:
        r_conf = requests.get(d_args['url_redis'] + 'config', params={'unit':dlgid}, timeout=10 )
    except requests.exceptions.RequestException as err: 
        app.logger.info( f'(1202) read_configuration ERROR: Redis request exception, Err:{err}')
        return None
    #
    if r_conf.status_code == 200:
        d_conf = r_conf.json()
        if debugid == dlgid:
            app.logger.info(f"(1203) read_configuration INFO: ID={dlgid}, REDIS D_CONF={d_conf}")
        return d_conf
    #
    app.logger.info(f"(1204) read_configuration WARN: No Rcd en Redis,ID={dlgid}, Err=({r_conf.status_code}){r_conf.text}")
    #
    # Intento leer desde SQL
    try:
        r_conf = requests.get(d_args['url_conf'] + 'config', params={'unit':dlgid}, timeout=10 )
    except requests.exceptions.RequestException as err:
        app.logger.info( f'(1205) read_configuration ERROR: Sql request exception, Err:{err}')
        return None
    #
    if r_conf.status_code == 200:
        if r_conf.json() == {}:
            app.logger.info(f"(1206) read_configuration WARN: Rcd en Sql empty,ID={dlgid}, Err=({r_conf.status_code}){r_conf.text}")
            return None
    #
    elif r_conf.status_code == 204:
        # No hay datos en la SQL tampoco: Debo salir
        app.logger.info(f"(1207) read_configuration WARN: No Rcd en Sql,ID={dlgid}, Err=({r_conf.status_code}){r_conf.text}")
        return None
    #
    else:
        app.logger.info(f"(1208) read_configuration ERROR: SQL read Error,ID={dlgid}, Err=({r_conf.status_code}){r_conf.text}")
        return None
    #
    # La api sql me devuelve un json
    d_conf = r_conf.json()
    app.logger.info(f"(1209) read_configuration INFO ID={dlgid}: SQL D_CONF={d_conf}")
    # Actualizo la redis.
    try:
        r_conf = requests.put(d_args['url_redis'] + 'config', params={'unit':dlgid}, json=d_conf, timeout=10 )
    except requests.exceptions.RequestException as err:
        app.logger.info(f"(1210) read_configuration ERROR: Redis request exception', Err:{err}")
        return None

    if r_conf.status_code != 200:
        app.logger.info(f"(1211) read_configuration ERROR: No puedo actualizar SQL config en REDIS, ID={dlgid}, Err=({r_conf.status_code}){r_conf.text}")
        return None
    #
    app.logger.info(f"(1212) read_configuration INFO ID={dlgid}, Config de SQL updated en Redis")
    return d_conf

def update_uid2id(d_args=None, id=None, uid=None):
    '''
    Actualiza el uid para futuro recover
    '''
    app = d_args.get('app',None)
    try:
        r_conf = requests.get(d_args['url_redis'] + '/uid2id', params={'uid':uid}, timeout=10 )
    except requests.exceptions.RequestException as err: 
        app.logger.info(f"(1213) update_uid2id ERROR: Redis request exception', Err:{err}")
        app.logger.info(f"(1214) update_uid2id ERROR: Recoverid Error: UID={uid}")
        return False
    #
    # Esta en la REDIS...
    if r_conf.status_code == 200:
        d_rsp = r_conf.json()
        nid = d_rsp['id']
        if nid == id:
            # Redis esta actualizada: Salgo.
            return True
    # 
    # En todos los otros casos, intento actualizar Redis y Sql
    d_conf = {'id':id,'uid':uid}
    try:
        r_conf = requests.put(d_args['url_redis'] + 'uid2id', json=d_conf, timeout=10 )
        app.logger.info("(1215) update_uid2id INFO uid2id update Redis")
    except requests.exceptions.RequestException as err: 
        app.logger.info(f"(1216) update_uid2id ERROR: Redis request exception', Err:{err}")
        return False
    #
    try:
        r_conf = requests.put(d_args['url_conf'] + 'uid2id', json=d_conf, timeout=10 )
        app.logger.info("(1217) update_uid2id INFO: uid2id update SQL")
    except requests.exceptions.RequestException as err: 
        app.logger.info(f"(1218) update_uid2id ERROR: Redis request exception', Err:{err}")
        return False      
        #
    return True

def convert_dataline2dict(d_url_args=None):
    '''
    d_url_args es un diccionario devuelto por requests.args.
    Filtramos las keys no datos.
    '''
    d_payload = {}
    for key in d_url_args:
        if key not in ('ID','TYPE','CLASS','VER'):
            d_payload[key] = d_url_args.get(key)
        #
    return d_payload

def update_comms_conf( d_args=None, d_comms_conf=None):
    '''
    Recibo un dict {'DLGID':dlgid, 'TYPE':type, 'VER':ver, 'UID':uid, 'IMEI':imei, 'ICCID':iccid}
    y usando la apiconf lo inserto en la BD.
    El diccionario lo convierto a json para pasarlo como parámetro en un POST
    '''
    app = d_args.get('app',None)

    #print(f'DEBUG: dict={d_comms_conf}')
    j_dict = json.dumps(d_comms_conf)
    #print(f'DEBUG: jdict={j_dict}')
    #
    try:
        req = requests.post(d_args['url_conf'] + 'commsidparams', json=j_dict, timeout=10 )
        app.logger.info("(1219) update_comms_conf INFO: Apiconf update SQL")
    except requests.exceptions.RequestException as err: 
        app.logger.info(f"(1220) update_comms_conf ERROR: Apiconf request exception', Err:{err}")
        return False      
        #
    return True

