#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python
'''
Script que prueba todas los entrypoints implementados en la API redis.
'''

'''
Configuraciones base por versiones de c/modulo
'''
BASE_CONF_TEMPLATE = { 
    '1.0.9': { 
        'ALMLEVEL': '10',
        'SAMPLES': '1',
        'PWRS_HHMM1': '1800',
        'PWRS_HHMM2': '1440',
        'PWRS_MODO': '0',
        'TDIAL': '900',
        'TPOLL': '30'  
        },
    '1.1.0': { 
        'ALMLEVEL': '10',
        'SAMPLES': '1',
        'PWRS_HHMM1': '1800',
        'PWRS_HHMM2': '1440',
        'PWRS_MODO': '0',
        'TDIAL': '900',
        'TPOLL': '60'  
        },
}

AINPUTS_CONF_TEMPLATE = { 
    '1.0.9': {
        'A0': {'IMAX': '20','IMIN': '4','MMAX': '10','MMIN': '0','NAME': 'X','OFFSET': '0'},
        'A1': {'IMAX': '20','IMIN': '4','MMAX': '10','MMIN': '0','NAME': 'X','OFFSET': '0'},
        'A2': {'IMAX': '20','IMIN': '4','MMAX': '10','MMIN': '0','NAME': 'X','OFFSET': '0'},   
        },
    '1.1.0': {
        'A0': {'ENABLE':'FALSE','IMAX': '20','IMIN': '4','MMAX': '10','MMIN': '0','NAME': 'X','OFFSET': '0'},
        'A1': {'ENABLE':'FALSE','IMAX': '20','IMIN': '4','MMAX': '10','MMIN': '0','NAME': 'X','OFFSET': '0'},
        'A2': {'ENABLE':'FALSE','IMAX': '20','IMIN': '4','MMAX': '10','MMIN': '0','NAME': 'X','OFFSET': '0'},   
        }
}

COUNTERS_CONF_TEMPLATE = { 
    '1.0.9': {
        'C0': {'MAGPP': '1.0','NAME': 'X','MODO':'CAUDAL'},
        'C1': {'MAGPP': '1.0','NAME': 'X','MODO':'CAUDAL'}  
        },
    '1.1.0': {
        'C0': {'ENABLE':'FALSE','MAGPP': '1.0','NAME': 'X','MODO':'CAUDAL'},
        'C1': {'ENABLE':'FALSE','MAGPP': '1.0','NAME': 'X','MODO':'CAUDAL'}   
        }
}

MODBUS_CONF_TEMPLATE = {
    '1.0.9': {
        'M0': { 'NAME': 'X', 'SLA_ADDR': '2','ADDR': '0','NRO_RECS': '2','FCODE': '0','TYPE': 'FLOAT', 'CODEC': 'C1032','POW10': '0' },
        'M1': { 'NAME': 'X', 'SLA_ADDR': '2','ADDR': '0','NRO_RECS': '2','FCODE': '0','TYPE': 'FLOAT', 'CODEC': 'C1032','POW10': '0' },
        'M2': { 'NAME': 'X', 'SLA_ADDR': '2','ADDR': '0','NRO_RECS': '2','FCODE': '0','TYPE': 'FLOAT', 'CODEC': 'C1032','POW10': '0' },
        'M3': { 'NAME': 'X', 'SLA_ADDR': '2','ADDR': '0','NRO_RECS': '2','FCODE': '0','TYPE': 'FLOAT', 'CODEC': 'C1032','POW10': '0' },
        'M4': { 'NAME': 'X', 'SLA_ADDR': '2','ADDR': '0','NRO_RECS': '2','FCODE': '0','TYPE': 'FLOAT', 'CODEC': 'C1032','POW10': '0' },
        },
    '1.1.0': {
        'LOCALADDR': '0x01',
        'ENABLE': 'FALSE',
        'M0': { 'NAME': 'X', 'SLA_ADDR': '2','ADDR': '0','NRO_RECS': '2','FCODE': '0','TYPE': 'FLOAT', 'CODEC': 'C1032','POW10': '0' },
        'M1': { 'NAME': 'X', 'SLA_ADDR': '2','ADDR': '0','NRO_RECS': '2','FCODE': '0','TYPE': 'FLOAT', 'CODEC': 'C1032','POW10': '0' },
        'M2': { 'NAME': 'X', 'SLA_ADDR': '2','ADDR': '0','NRO_RECS': '2','FCODE': '0','TYPE': 'FLOAT', 'CODEC': 'C1032','POW10': '0' },
        'M3': { 'NAME': 'X', 'SLA_ADDR': '2','ADDR': '0','NRO_RECS': '2','FCODE': '0','TYPE': 'FLOAT', 'CODEC': 'C1032','POW10': '0' },
        'M4': { 'NAME': 'X', 'SLA_ADDR': '2','ADDR': '0','NRO_RECS': '2','FCODE': '0','TYPE': 'FLOAT', 'CODEC': 'C1032','POW10': '0' },
        }    
}

PILOTO_CONF_TEMPLATE = {
    '1.1.0': {
        'ENABLE': 'FALSE',
        'PPR': '2000',
        'PWIDTH': '10',
        'SLOT0': { 'PREF':0.0, 'TIME':'0000'},
        'SLOT1': { 'PREF':0.0, 'TIME':'0000'},
        'SLOT2': { 'PREF':0.0, 'TIME':'0000'},
        'SLOT3': { 'PREF':0.0, 'TIME':'0000'},
        'SLOT4': { 'PREF':0.0, 'TIME':'0000'},
        'SLOT5': { 'PREF':0.0, 'TIME':'0000'},
        'SLOT6': { 'PREF':0.0, 'TIME':'0000'},
        'SLOT7': { 'PREF':0.0, 'TIME':'0000'},
        'SLOT8': { 'PREF':0.0, 'TIME':'0000'},
        'SLOT9': { 'PREF':0.0, 'TIME':'0000'},
        'SLOT10': { 'PREF':0.0, 'TIME':'0000'},
        'SLOT11': { 'PREF':0.0, 'TIME':'0000'},
        }    
}

'''
Configuraciones de dataloggers por versión:
'''
DLG_CONF_TEMPLATE = {
    '1.0.9': { 'BASE': BASE_CONF_TEMPLATE['1.0.9'], 
                'AINPUTS': AINPUTS_CONF_TEMPLATE['1.0.9'],
                'COUNTERS': COUNTERS_CONF_TEMPLATE['1.0.9'],
                'MODBUS': MODBUS_CONF_TEMPLATE['1.0.9']
    },
    '1.1.0': { 'BASE': BASE_CONF_TEMPLATE['1.1.0'], 
                'AINPUTS': AINPUTS_CONF_TEMPLATE['1.1.0'],
                'COUNTERS': COUNTERS_CONF_TEMPLATE['1.1.0'],
                'MODBUS': MODBUS_CONF_TEMPLATE['1.1.0'],
                'PILOTOS': PILOTO_CONF_TEMPLATE['1.1.0']

    }
}


