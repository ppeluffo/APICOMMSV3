#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python
'''
'''
import requests

class Utils:
    '''
    Funciones auxiliares de uso en apiplc y apidlg
    '''
    def __init__(self,d_args):
        self.ID = d_args.get('id',None)
        self.app = d_args.get('app',None)
        self.servers = d_args.get('servers',None)
        self.url_redis = f"http://{self.servers['APIREDIS_HOST']}:{self.servers['APIREDIS_PORT']}/apiredis/"
        self.url_conf = f"http://{self.servers['APICONF_HOST']}:{self.servers['APICONF_PORT']}/apiconf/"

    def read_debug_id(self):
        '''
        Consulta el nombre del equipo que debe logearse. Si hay error o no esta configurado
        devuelve 'UDEBUG'
        '''
        try:
            rsp = requests.get(self.url_redis + 'debugid', timeout=10 )
        except requests.exceptions.RequestException as err: 
            self.app.logger.info( f'(700) ApiUTILS_ERR001: Redis request exception, Err:{err}')
            return 'UDEBUG'
        
        if rsp.status_code == 200:
            d = rsp.json()
            debugid = d.get('debugid','UDEBUG')
            return debugid
        else:
            self.app.logger.info(f"(701) ApiUTILS_WARN001: No debug unit, Err=({rsp.status_code}){rsp.text}")
            # Seteo uno por default.
            _=requests.put(self.url_redis + 'debugid', json={'debugid':'UDEBUG'}, timeout=10 )
        return 'UDEBUG'

    def read_configuration(self, debug=False):
        '''
        Lee la configuracion de la unidad y la deja en self.d_conf. Retorna True/False.
        '''
        # Intento leer desde REDIS.
        try:
            r_conf = requests.get(self.url_redis + 'config', params={'unit':self.ID}, timeout=10 )
        except requests.exceptions.RequestException as err: 
            self.app.logger.info( f'(702) ApiUTILS_ERR001: Redis request exception, Err:{err}')
            return None
        #
        if r_conf.status_code == 200:
            d_conf = r_conf.json()
            if debug:
                self.app.logger.info(f"(703) ApiUTILS_INFO: ID={self.ID}, REDIS D_CONF={d_conf}")
            return d_conf
        #
        self.app.logger.info(f"(704) ApiUTILS_WARN002: No Rcd en Redis,ID={self.ID}, Err=({r_conf.status_code}){r_conf.text}")
        #
        # Intento leer desde SQL
        try:
            r_conf = requests.get(self.url_conf + 'config', params={'unit':self.ID}, timeout=10 )
        except requests.exceptions.RequestException as err:
            self.app.logger.info( f'(705) ApiUTILS_ERR002: Sql request exception, Err:{err}')
            return None
        #
        if r_conf.status_code == 200:
            if r_conf.json() == {}:
                self.app.logger.info(f"(706) ApiUTILS_WARN003: Rcd en Sql empty,ID={self.ID}, Err=({r_conf.status_code}){r_conf.text}")
                return None
        #
        elif r_conf.status_code == 204:
            # No hay datos en la SQL tampoco: Debo salir
            self.app.logger.info(f"(707) ApiUTILS_WARN004: No Rcd en Sql,ID={self.ID}, Err=({r_conf.status_code}){r_conf.text}")
            return None
        #
        else:
            self.app.logger.info(f"(708) ApiUTILS_ERR003: SQL read Error,ID={self.ID}, Err=({r_conf.status_code}){r_conf.text}")
            return None
        #
        # La api sql me devuelve un json
        d_conf = r_conf.json()
        self.app.logger.info(f"(709) ApiUTILS_INFO ID={self.ID}: SQL D_CONF={d_conf}")
        # Actualizo la redis.
        try:
            r_conf = requests.put(self.url_redis + 'config', params={'unit':self.ID}, json=d_conf, timeout=10 )
        except requests.exceptions.RequestException as err:
            self.app.logger.info(f"(710) ApiUTILS_ERR001: Redis request exception', Err:{err}")
            return None

        if r_conf.status_code != 200:
            self.app.logger.info(f"(711) ApiUTILS_ERR004: No puedo actualizar SQL config en REDIS, ID={self.ID}, Err=({r_conf.status_code}){r_conf.text}")
            return None
        #
        self.app.logger.info(f"(712) ApiUTILS_INFO ID={self.ID}, Config de SQL updated en Redis")
        return d_conf
    