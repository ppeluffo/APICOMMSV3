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
        'SLOT0': { 'PRES':0.0, 'TIME':'0000'},
        'SLOT1': { 'PRES':0.0, 'TIME':'0000'},
        'SLOT2': { 'PRES':0.0, 'TIME':'0000'},
        'SLOT3': { 'PRES':0.0, 'TIME':'0000'},
        'SLOT4': { 'PRES':0.0, 'TIME':'0000'},
        'SLOT5': { 'PRES':0.0, 'TIME':'0000'},
        'SLOT6': { 'PRES':0.0, 'TIME':'0000'},
        'SLOT7': { 'PRES':0.0, 'TIME':'0000'},
        'SLOT8': { 'PRES':0.0, 'TIME':'0000'},
        'SLOT9': { 'PRES':0.0, 'TIME':'0000'},
        'SLOT10': { 'PRES':0.0, 'TIME':'0000'},
        'SLOT11': { 'PRES':0.0, 'TIME':'0000'},
        }    
}

'''
Configuraciones de dataloggers por versión:
'''
DLG_CONF_TEMPLATE = {
    '1.1.0': { 'BASE': BASE_CONF_TEMPLATE['1.1.0'], 
                'AINPUTS': AINPUTS_CONF_TEMPLATE['1.1.0'],
                'COUNTERS': COUNTERS_CONF_TEMPLATE['1.1.0'],
                'MODBUS': MODBUS_CONF_TEMPLATE['1.1.0'],
                'PILOTO': PILOTO_CONF_TEMPLATE['1.1.0']

    },
    '1.0.9': { 'BASE': BASE_CONF_TEMPLATE['1.0.9'], 
                'AINPUTS': AINPUTS_CONF_TEMPLATE['1.0.9'],
                'COUNTERS': COUNTERS_CONF_TEMPLATE['1.0.9'],
                'MODBUS': MODBUS_CONF_TEMPLATE['1.0.9']
    }
}

PLC_CONF_TEMPLATE = {
    'R2': { 'MEMBLOCK': 
                {'CONFIGURACION': [
                    ['ALT_MAX_TQ1', 'float', 10], ['ALT_MIN_TQ1', 'float', 2], ['PRES_ALM_1', 'short', 101],['TIMER_B2', 'short', 200]
                    ],
                'DATOS_PLC': [
                    ['UPA1_CAUDALIMETRO', 'float', 0],['UPA1_STATE1', 'uchar', 1],['UPA1_POS_ACTUAL_6', 'short', 8],
                    ['UPA2_CAUDALIMETRO', 'float', 0],['BMB_STATE18', 'uchar', 1]
                    ],
                'DATOS_SRV': [
                    ['TIMESTAMP', 'short', 1, 'SYS', 'None'],
                    ['RESET', 'short', 0, 'ATVISE', 'None'],
                    ['UPA1_ORDER_1', 'short', 100, 'ATVISE','None'],
                    ['UPA1_CONSIGNA_6', 'short', 2560, 'ATVISE','None'],
                    ['ESP_ORDER_8', 'short', 200, 'ATVISE','None'], 
                    ['ALTURA_TANQUE_KIYU_1', 'float', 0,'DL001','HTQ1'],
                    ['ALTURA_TANQUE_KIYU_2', 'float', 0,'DL002','HTQ2']
                    ]
                }
        },

    'R1': { 'MEMBLOCK':{'RCVD_MBK_DEF': [
                              ['UPA2_CAUDALIMETRO', 'float', 0],['BMB_STATE18', 'uchar', 1],['BMB_STATE19', 'uchar', 1]
                            ],
             'SEND_MBK_DEF': [
                              ['UPA1_ORDER_1', 'short', 1],['UPA1_CONSIGNA_6', 'short', 2560],['ESP_ORDER_8', 'short', 200],
                              ['ALTURA_TANQUE_KIYU_1', 'float', 2560],['ALTURA_TANQUE_KIYU_2', 'float', 2560],
                              ['PRESION_ALTA_SJ1', 'float', 0],['PRESION_BAJA_SQ1', 'float', 0]
                            ],
             'RCVD_MBK_LENGTH':15,
             'SEND_MBK_LENGTH':24
                },

            'REMVARS':{
                'DLG001': [
                    ('HTQ1', 'ALTURA_TANQUE_KIYU_1'), 
                    ('HTQ2', 'ALTURA_TANQUE_KIYU_2')
                    ],
                'DLG002': [
                    ('PA', 'PRESION_ALTA_SJ1'), 
                    ('PB', 'PRESION_BAJA_SQ1')
                    ]
                }
            }
}


