import sys

file_path = '/home/ulises/Desarrollo/APICOMMSV3/apidatos/apidatos.py'
with open(file_path, 'r') as f:
    content = f.read()

# 1. Insert search_configuraciones_equipos in BD_SQL_BASE
insert_sql_method = """
    def search_configuraciones_equipos(self, valor):
        '''
        Filtra las configuraciones usando LIKE en la BD para optimizar.
        '''
        valor_safe = str(valor).replace("'", "''")
        sql = f"SELECT unit_id, uid, jconfig FROM configuraciones WHERE jconfig::text LIKE '%{valor_safe}%'"
        d_res = self.exec_sql(sql)
        if not d_res.get('res',False):
            app.logger.info( '(213) ApiDATOS_ERR009: search dconfiguraciones FAIL')
        return d_res
"""

# Find where to insert it, e.g. after read_configuraciones_equipos
if "def search_configuraciones_equipos" not in content:
    content = content.replace(
        "    def update_user(self, user_id, pk):",
        insert_sql_method + "\n    def update_user(self, user_id, pk):"
    )

# 2. Insert BuscarEquipos Resource
insert_resource = """
class BuscarEquipos(Resource):
    '''
    Busca equipos filtrando por un path de configuracion JSON y un valor.
    '''
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('path', type=str, required=True, location='args')
        parser.add_argument('value', type=str, required=True, location='args')
        args = parser.parse_args()
        
        path_parts = args['path'].split('.')
        expected_value = args['value']
        
        bdsql = BD_SQL_BASE()
        d_res = bdsql.search_configuraciones_equipos(expected_value)
        if not d_res.get('res', False):
            bdsql.close()
            return {'rsp':'ERROR', 'msg':'Error en pgsql'}, 500
            
        rp = d_res.get('rp', None)
        if rp.rowcount == 0:
            bdsql.close()
            return {'equipos_plc': [], 'equipos_dlg': [], 'resumen': {'total_encontrados': 0, 'cantidad_plc': 0, 'cantidad_dlg': 0}}, 200
            
        def find_in_config(config, parts, exp_val):
            if not parts:
                return str(config).lower() == str(exp_val).lower()
            key = parts[0]
            rest = parts[1:]
            if isinstance(config, dict):
                if key in config: return find_in_config(config[key], rest, exp_val)
            elif isinstance(config, list):
                try:
                    idx = int(key)
                    if 0 <= idx < len(config): return find_in_config(config[idx], rest, exp_val)
                except ValueError: pass
                for item in config:
                    if find_in_config(item, parts, exp_val): return True
            return False

        resultados_plc = []
        resultados_dlg = []
        
        import json
        rows = rp.fetchall()
        for row in rows:
            unit_id = row[0]
            jconfig = row[2]
            if isinstance(jconfig, str):
                try:
                    jconfig = json.loads(jconfig)
                except json.JSONDecodeError:
                    continue
                    
            if find_in_config(jconfig, path_parts, expected_value):
                if "MEMBLOCK" in jconfig or "REMVARS" in jconfig or "DATOS_PLC" in str(jconfig):
                    resultados_plc.append(unit_id)
                else:
                    resultados_dlg.append(unit_id)
                    
        bdsql.close()
        
        return {
            "resumen": {
                "total_encontrados": len(resultados_plc) + len(resultados_dlg),
                "cantidad_plc": len(resultados_plc),
                "cantidad_dlg": len(resultados_dlg)
            },
            "equipos_plc": resultados_plc,
            "equipos_dlg": resultados_dlg
        }, 200
"""

if "class BuscarEquipos(Resource):" not in content:
    content = content.replace(
        "api.add_resource( Ping, '/apidatos/ping')",
        insert_resource + "\napi.add_resource( Ping, '/apidatos/ping')"
    )
    content = content.replace(
        "api.add_resource( ConfiguracionEquipos, '/apidatos/config/equipos')",
        "api.add_resource( ConfiguracionEquipos, '/apidatos/config/equipos')\napi.add_resource( BuscarEquipos, '/apidatos/config/buscar')"
    )

with open(file_path, 'w') as f:
    f.write(content)

print("Updated apidatos.py")
