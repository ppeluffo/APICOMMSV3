#!/home/pablo/Spymovil/python/proyectos/APICOMMSV3/venv/bin/python
'''
Funciones donde implemento los objetos Memblocks.

'MEMBLOCK' = { 'RCVD_MBK_LENGTH': 21, 'RCVD_MBK_DEF': [   ('var1','uchar',0), ('var2','uchar',1), ('var3','float',2), ('var4','short',3), ('var5','short',5)],
             'SEND_MBK_LENGTH': 21, 'SEND_MBK_DEF': [   ('var1','uchar',0), ('var2','uchar',1), ('var3','float',2), ('var4','short',3), ('var5','short',5)],
           }

'REMVARS': {'KYTQ003': [['HTQ1', 'NIVEL_TQ_KIYU']]}

b=pack('ififf',14,123.4,100,3.14,2.7)
b'\x0e\x00\x00\x00\xcd\xcc\xf6Bd\x00\x00\x00\xc3\xf5H@\xcd\xcc,@'
b'\n\x0bf\xe6\xf6Bb\x04W\x02\xecq\xe4C:\x16\x00\x00\x00\x00\x00\x0b\xa3'}

{ 'MEMBLOCK':{'RCVD_MBK_DEF': [
                              ['UPA1_CAUDALIMETRO', 'float', 0],['UPA1_STATE1', 'uchar', 1],['UPA1_POS_ACTUAL_6', 'short', 8],
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
        'KIYU001': [
            ('HTQ1', 'ALTURA_TANQUE_KIYU_1'), 
            ('HTQ2', 'ALTURA_TANQUE_KIYU_2')
            ],
        'SJOSE001': [
            ('PA', 'PRESION_ALTA_SJ1'), 
            ('PB', 'PRESION_BAJA_SQ1')
            ]
        }
}

RCVD_MBK_LENGTH y SEND_MBK_LENGTH incluyen los 2 bytes del CRC.!!!
En este caso el len('RCVD_MBK_DEF') es 13 
            
Datos simulados a transmitir por el PLC

d={'UPA1_CAUDALIMETRO': 123.45,
 'UPA1_STATE1': 100,
 'UPA1_POS_ACTUAL_6': 120,
 'UPA2_CAUDALIMETRO': 32.45,
 'BMB_STATE18': 20,
 'BMB_STATE19': 40
 }

 sformat,largo,var_names = mbk.__process_mbk__(mbk.rcvd_mbk_def)
 sformat = '<fBhfBB'
 largo = 13
 var_names = 'UPA1_CAUDALIMETRO UPA1_STATE1 UPA1_POS_ACTUAL_6 UPA2_CAUDALIMETRO BMB_STATE18 BMB_STATE19 '

ntuple = namedtuple('nt', d.keys())(*d.values())
nt(UPA1_CAUDALIMETRO=123.45, UPA1_STATE1=100, UPA1_POS_ACTUAL_6=120, UPA2_CAUDALIMETRO=32.45, BMB_STATE18=20, BMB_STATE19=40)

tx_bytestream = pack( sformat, *ntuple)
b'f\xe6\xf6Bdx\x00\xcd\xcc\x01B\x14('

crc = computeCRC(tx_bytestream)
crc=36181

tx_bytestream += crc.to_bytes(2,'big')
b'f\xe6\xf6Bdx\x00\xcd\xcc\x01B\x14(\x8dU'

 Este es el payload que debo recibir en modo test.

'''

from collections import namedtuple
from struct import unpack_from, pack
from pymodbus.utilities import computeCRC


class Memblock:
    ''' Defino los objetos memblock que se usan en las comunicaciones de los PLC '''

    def __init__(self,app):

        self.debug = False

        self.app = app              # Para poder usar el log
        self.plcid = None
        self.rcvd_mbk_def = []      # Definicion del MBK que recibe el servidor desde el PLC
        self.rcvd_mbk_length = 0
        self.send_mbk_def = []      # Definicion del MBK que envia el servidor al PLC
        self.send_mbk_length = 0

        self.rx_payload = ''        # bytestring recibido en el body del POST.
        self.rx_payload_length = 0
        self.d_rx_payload = {}      # dict. con las variables y valores recibidos.

        self.tx_bytestream = None   # datos serializados de salida

    def set_debug(self,):
        '''
        '''
        self.debug = True

    def load_configuration(self, plcid, d_mbk):
        ''' Configura el objeto con los elementos del d_mbk '''
        self.plcid = plcid
        self.rcvd_mbk_def = d_mbk.get('RCVD_MBK_DEF',[])
        self.rcvd_mbk_length = d_mbk.get('RCVD_MBK_LENGTH',0)
        self.send_mbk_def = d_mbk.get('SEND_MBK_DEF',[])
        self.send_mbk_length = d_mbk.get('SEND_MBK_LENGTH',0)
        #

    def load_rx_payload(self, rx_payload):
        ''' Carga en el objeto mbk los datos del payload '''
        self.rx_payload = rx_payload
        self.rx_payload_length = len(self.rx_payload)
        if self.debug:
            self.app.logger.info( f'(460) ApiCOMMS_INFO: ID={self.plcid},rx_payload=({self.rx_payload_length})[{self.rx_payload}]')

    def get_d_rx_payload(self):
        '''
        Devuelve el diccionario de datos enviados por el PLC
        '''
        return self.d_rx_payload
    
    def convert_rxbytes2dict( self):
        '''
        Toma el payload; 
        Chequea si el crc es correcto.
        Lo decodifica de acuerdo a la struct definida en el memblock
        y retorna un dict con las variables y sus valores.
        Utiliza el r_mbk ( RCVD)
        La defincion de la struct puede tener menos bytes que el bloque !!!. Para esto debo usar 'unpack_from'
        '''
        # 1) El CRC debe ser correcto
        if not self.__check_payload_crc_valid__():
            self.app.logger.error('ID={self.plcid}, FUNC=convert_bytes2dict, ERROR: MBK_CRC_ERR' )
            return False

        # 2) El payload debe tener largo para ser decodificado de acuerdo al memblock def.
        if self.rx_payload_length < self.rcvd_mbk_length:
            self.app.logger.error( f'ID={self.plcid}, FUNC=convert_bytes2dict, ERROR: MBK_RCVD_LENGTH_ERR: payload_length={self.rx_payload_length}, mbk_length={self.rcvd_mbk_length}' )
            return False
        #
        # 3) Calculo los componentes del memblock de recepcion (formato,largo, lista de nombres)
        sformat, _ , var_names = self.__process_mbk__(self.rcvd_mbk_def)
        if self.debug:
            self.app.logger.info( f'(461) ApiCOMMS_INFO: ID={self.plcid}, convert_bytes2dict: RXVD_MBK_DEF={self.rcvd_mbk_def}')
        #
        # 4) Desempaco los datos recibidos del PLC de acuerdo al formato dado (del RCVD_MBK)
        # RCVD_MBK es una lista porque importa el orden de las variables !!!
        # El resultado es una tupla de valores
        try:
            t_vals = unpack_from(sformat, self.rx_payload)
        except ValueError as err:
            self.app.logger.error( f'(462) ApiCOMMS_ERR011: No puedo UNPACK, ID={self.plcid}, sformat={sformat}, rx_payload=[{self.rx_payload}], error={err}' )
            return False
        #
        # 5) Genero una namedtuple con los valores anteriores y los nombres de las variables
        # Creo una namedtuple con la lista de nombres del rx_mbk
        t_names = namedtuple('T_RCVD_VARS', var_names)
        try:
            rx_tuple = t_names._make(t_vals)
        except ValueError:
            self.app.logger.error( f'(463) ApiCOMMS_ERR012: No puedo generar tupla de valores, ID={self.plcid}' )
            return False
        #
        # La convierto a diccionario
        self.d_rx_payload = rx_tuple._asdict()
        if self.debug:
            self.app.logger.info(  f'(464) ApiCOMMS_INFO: ID={self.plcid}, convert_bytes2dict,d_rx_payload={self.d_rx_payload}' )
        return True
 
    def convert_dict2bytes( self, plcid, d_responses ):
        '''
        Recibo un diccionario con variables definidas en la estructura de un plc memblock.
        Utiliza el s_mbk ( SEND )
        El d_data puede tener mas variables que las que tiene el mbk.
        Serializo la estructura de acuerdo al mbk.!! (solo puedo mandar lo que dicta el memblock )
        Relleno con 0 hasta completar el largo del memblock
        Agrego el CRC del largo del memblock
        Retorno un bytearray.
        '''
        self.plcid = plcid
        d_tx_payload = {}
        for tp in self.send_mbk_def:
            # t = ['ESP_ORDER_8', 'short', 200]
            dst_var_name, _, dst_default_value = tp
            d_tx_payload[dst_var_name] = d_responses.get(dst_var_name, dst_default_value)
        #
        # En d_payload tengo todas las variables definidas en el send_mbk con sus valores reales o x defecto
        if self.debug:
            self.app.logger.info(  f'(465) ApiCOMMS_INFO: ID={self.plcid}, convert_dict2bytes,d_tx_payload={d_tx_payload}' )
        #
        # Convierto el diccionario a una namedtuple (template)
        # SEND_MBK es una lista porque importa el orden de las variables !!!.
        sformat, largo, var_names = self.__process_mbk__(self.send_mbk_def) 
        ntuple = namedtuple('nt', d_tx_payload.keys())(*d_tx_payload.values())
        if self.debug:
            self.app.logger.info(  f'(466) ApiCOMMS_INFO: ID={self.plcid}, convert_dict2bytes,sformat={sformat}' )
            self.app.logger.info(  f'(467) ApiCOMMS_INFO: ID={self.plcid}, onvert_dict2bytes,ntuple={ntuple}' )
        #
        # Convierto los valores de la ntuple a los tipos definidos en el mbk
        # Si el valor es un string y el tipo es 'h' lo convierto a int
        # Si el valor es un string y el tipo es 'f' lo convierto a float
        list_values = []
        for idx, x in enumerate(ntuple):
            try:
                idf = idx + 1
                if type(x) == str:
                    if sformat[idf] == 'h':
                        x = int(x)
                    elif sformat[idf] == 'f':
                        x = float(x)
                list_values.append(x)
            except Exception as ex:
                self.app.logger.debug(  f'(468) ApiCOMMS_ERR013: No puedo armar respuesta. ID={self.plcid},idx={idx},x={x},type(x)={type(x)},sformat[idf]={sformat[idf]} ntuple[idx]={ntuple[idx]},Err={ex}' )
                continue
        #
        if self.debug:
            self.app.logger.info(  f'(469) ApiCOMMS_INFO: ID={self.plcid},convert_dict2bytes,list_values={list_values}' )
        #
        # Convierto la ntuple a un bytearray serializado 
        try:
            # self.tx_bytestream = pack( sformat, *ntuple)   
            self.tx_bytestream = pack( sformat, *list_values)      
        except Exception as ex:
            self.app.logger.debug(  f'(470) ApiCOMMS_ERR014: No puedo convertir tupla. ID={self.plcid}, {ntuple},Err={ex}' )
            self.app.logger.debug(  f'(471) ApiCOMMS_ERR015: Error en txbytestram. ID={self.plcid}tx_bytestream={self.tx_bytestream}' )
            return self.tx_bytestream
        #
        # Controlo errores: el payload no puede ser mas largo que el tamaño del bloque (frame)
        if len(self.tx_bytestream) > self.send_mbk_length:
            self.app.logger.debug(  f'(472) ApiCOMMS_ERR016: Error txbytestream length. ID={self.plcid}, tx_bytestream={len(self.tx_bytestream)}, send_mbk_length={self.send_mbk_length}' )
            return self.tx_bytestream
        #
        # Relleno con 0 el bloque
        largo_relleno = self.send_mbk_length - len(self.tx_bytestream)
        relleno = bytes(largo_relleno*[0])
        self.tx_bytestream += relleno
        #
        # Calculo el CRC y lo agrego al final. Lo debo convertir a bytes antes.
        crc = computeCRC(self.tx_bytestream)
        self.tx_bytestream += crc.to_bytes(2,'big')
        #
        return self.tx_bytestream

    def __check_payload_crc_valid__(self):
        '''
        Calcula el CRC del payload y lo compara el que trae.
        El payload trae el CRC que envia el PLC en los 2 ultimos bytes
        El payload es un bytestring
        '''
        crc = int.from_bytes(self.rx_payload[-2:],'big')
        calc_crc = computeCRC(self.rx_payload[:-2])
        if crc == calc_crc:
            return True
        else:
            return False
    
    def __process_mbk__( self, l_mbk_def:list ):
        '''
        Toma una lista de definicion de un memblok de recepcion y genera 3 elementos:
        -un iterable con los nombres en orden
        -el formato a usar en la conversion de struct
        -el largo total definido por las variables
        '''
        #
        sformat = '<'
        largo = 0
        var_names = ''
        for ( name, tipo, _) in l_mbk_def:
            var_names += f'{name} '
            if tipo.lower() == 'char':
                sformat += 'c'
                largo += 1
            elif tipo.lower() == 'schar':
                sformat += 'b'
                largo += 1
            elif tipo.lower() == 'uchar':
                sformat += 'B'
                largo += 1
            elif tipo.lower() == 'short':
                sformat += 'h'
                largo += 2
            elif tipo.lower() == 'int':
                sformat += 'i'
                largo += 4
            elif tipo.lower() == 'float':
                sformat += 'f'
                largo += 4
            elif tipo.lower() == 'unsigned':
                sformat += 'H'
                largo += 2
            else:
                sformat += '?'
        #
        return sformat, largo, var_names
