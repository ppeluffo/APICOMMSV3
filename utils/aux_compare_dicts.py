#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python
'''
Script de test para desarrollar un metodo de determinar cuando me mandan 
un diccionario de configuracion, si tiene claves de mas o de menos.
Debo determinar ambos grupos.

REF: https://www.geeksforgeeks.org/python-convert-nested-dictionary-into-flattened-dictionary/

'''

D_TEMPLATE = {'ANALOGS': {
                        'A0': {'ENABLE':'TRUE', 'IMAX': '20','IMIN': '4','MMAX': '10','MMIN': '0','NAME': 'HTQ','OFFSET': '0'},
                        'A1': {'ENABLE':'FALSE','IMAX': '20','IMIN': '4','MMAX': '10','MMIN': '0','NAME': 'X','OFFSET': '0'},
                        'A2': {'ENABLE':'FALSE','IMAX': '20','IMIN': '4','MMAX': '10','MMIN': '0','NAME': 'X','OFFSET': '0'}
                        },
            'BASE': {'ALMLEVEL': '10','FIRMWARE': '4.0.0a','SAMPLES': '1',
                     'PWRS_HHMM1': '1800','PWRS_HHMM2': '1440','PWRS_MODO': '0',
                     #'TDIAL': '900','TPOLL': '30'
                     },
            'COUNTERS': {
                       'C0': {'ENABLE':'TRUE','MAGPP': '0.01','NAME': 'q0','MODO':'CAUDAL'},
                       'C1': {'ENABLE':'FALSE','MAGPP': '0.01','NAME': 'X','MODO':'CAUDAL'}
                        },
            'MODBUS': {
                'ENABLE':'TRUE',
                'LOCALADDR':'2',
                'M0': { 'ENABLE':'TRUE','NAME': 'CAU0', 'SLA_ADDR': '2','ADDR': '2069','NRO_RECS': '2','FCODE': '3','TYPE': 'FLOAT', 'CODEC': 'C1032','POW10': '0' },
                'M1': { 'ENABLE':'FALSE','NAME': 'X', 'SLA_ADDR': '2','ADDR': '2069','NRO_RECS': '2','FCODE': '3','TYPE': 'FLOAT', 'CODEC': 'C1032','POW10': '0' },
                'M2': { 'ENABLE':'FALSE','NAME': 'X', 'SLA_ADDR': '2','ADDR': '2069','NRO_RECS': '2','FCODE': '3','TYPE': 'FLOAT', 'CODEC': 'C1032','POW10': '0' },
                'M3': { 'ENABLE':'FALSE','NAME': 'X', 'SLA_ADDR': '2','ADDR': '2069','NRO_RECS': '2','FCODE': '3','TYPE': 'FLOAT', 'CODEC': 'C1032','POW10': '0' },
                'M4': { 'ENABLE':'FALSE','NAME': 'X', 'SLA_ADDR': '2','ADDR': '2069','NRO_RECS': '2','FCODE': '3','TYPE': 'FLOAT', 'CODEC': 'C1032','POW10': '0' }
            }
        }

D_TEST = {'ANALOGS': {
                        'A0': {'ENABLE':'TRUE', 'IMAX': '20','IMIN': '4','MMAX': '10','MMIN': '0','NAME': 'HTQ','OFFSET': '0'},
                        'A1': {'ENABLE':'FALSE','IMAX': '20','IMIN': '4','MMAX': '10','MMIN': '0','NAME': 'X','OFFSET': '0'},
                        'A2': {'ENABLE':'FALSE','IMAX': '20','IMIN': '4','MMAX': '10','MMIN': '0','NAME': 'X','OFFSET': '0'}
                        },
            'BASE': {'ALMLEVEL': '10','FIRMWARE': '4.0.0a','SAMPLES': '1',
                     'PWRS_HHMM1': '1800','PWRS_HHMM2': '1440','PWRS_MODO': '0',
                     'TDIAL': '900','TPOLL': '30'
                     },
            'COUNTERS': {
                      # 'C0': {'ENABLE':'TRUE','MAGPP': '0.01','NAME': 'q0','MODO':'CAUDAL'},
                       'C1': {'ENABLE':'FALSE','MAGPP': '0.01','NAME': 'X','MODO':'CAUDAL'}
                        },
            'MODBUS': {
                'ENABLE':'TRUE',
                'LOCALADDR':'2',
                'M0': { 'ENABLE':'TRUE','NAME': 'CAU0', 'SLA_ADDR': '2','ADDR': '2069','NRO_RECS': '2','FCODE': '3','TYPE': 'FLOAT', 'CODEC': 'C1032','POW10': '0' },
                'M1': { 'ENABLE':'FALSE','NAME': 'X', 'SLA_ADDR': '2','ADDR': '2069','NRO_RECS': '2','FCODE': '3','TYPE': 'FLOAT', 'CODEC': 'C1032','POW10': '0' },
                'M2': { 'ENABLE':'FALSE','NAME': 'X', 'SLA_ADDR': '2','ADDR': '2069','NRO_RECS': '2','FCODE': '3','TYPE': 'FLOAT', 'CODEC': 'C1032','POW10': '0' },
                'M3': { 'ENABLE':'FALSE','NAME': 'X', 'SLA_ADDR': '2','ADDR': '2069','NRO_RECS': '2','FCODE': '3','TYPE': 'FLOAT', 'CODEC': 'C1032','POW10': '0' },
                'M4': { 'ENABLE':'FALSE','NAME': 'X', 'SLA_ADDR': '2','ADDR': '2069','NRO_RECS': '2','FCODE': '3','TYPE': 'FLOAT', 'CODEC': 'C1032','POW10': '0' }
            }
        }

from collections.abc import MutableMapping

def convert_flatten(d, parent_key ='', sep =':'):
    '''
    '''
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
 
        if isinstance(v, MutableMapping):
            items.extend(convert_flatten(v, new_key, sep = sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def compare_dicts(d_reference, d_other):

    set_reference = set( convert_flatten(d_reference).keys())
    set_other = set( convert_flatten(d_other).keys())
    claves_de_mas = list(set_other - set_reference)
    claves_de_menos = list(set_reference - set_other)   
    return claves_de_mas, claves_de_menos

if __name__ == '__main__':

    claves_de_mas, claves_de_menos = compare_dicts(D_TEMPLATE, D_TEST)
    print(f'Claves de mas: {claves_de_mas}')
    print(f'Claves de menos: {claves_de_menos}')
