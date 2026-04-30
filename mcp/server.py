#!/usr/bin/env python3
"""
MCP Server: comms_spymovil
Expone como herramientas (tools) MCP todas las operaciones disponibles
en las APIs del sistema APICOMMSV3 de Spymovil.

IMPORTANTE: Este servidor gestiona exclusivamente equipos de la infraestructura 
SPYMOVIL. Para equipos de ANTEL, utilizar el MCP correspondiente (config_equipos_antel).

  - apiredis  (puerto 5100): Redis / estado en tiempo real de los equipos Spymovil
  - apiconf   (puerto 5200): Configuraciones persistidas en PostgreSQL (Spymovil)
  - apidatos  (puerto 5300): Datos históricos / usuarios de datos (Spymovil)
"""

import os
import json
import httpx
import psycopg2
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Cargar variables de entorno desde archivo .env si existe
load_dotenv()

MCP_DATABASE_URL = os.environ.get("MCP_DATABASE_URL", "")

# ─── Configuración de hosts ────────────────────────────────────────────────────
APIREDIS_HOST = os.environ.get("APIREDIS_HOST", "localhost")
APIREDIS_PORT = os.environ.get("APIREDIS_PORT", "5100")
APICONF_HOST  = os.environ.get("APICONF_HOST",  "localhost")
APICONF_PORT  = os.environ.get("APICONF_PORT",  "5200")
APIDATOS_HOST = os.environ.get("APIDATOS_HOST", "localhost")
APIDATOS_PORT = os.environ.get("APIDATOS_PORT", "5300")
APICOMMS_HOST = os.environ.get("APICOMMS_HOST", "localhost")
APICOMMS_PORT = os.environ.get("APICOMMS_PORT", "5000")

APIREDIS_BASE = f"http://{APIREDIS_HOST}:{APIREDIS_PORT}"
APICONF_BASE  = f"http://{APICONF_HOST}:{APICONF_PORT}"
APIDATOS_BASE = f"http://{APIDATOS_HOST}:{APIDATOS_PORT}"
APICOMMS_BASE = f"http://{APICOMMS_HOST}:{APICOMMS_PORT}"

TIMEOUT = 10.0

mcp = FastMCP("comms_spymovil")

# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _get(url: str, params: dict | None = None) -> dict:
    try:
        r = httpx.get(url, params=params, timeout=TIMEOUT)
        if r.status_code == 204:
            return {"status": 204, "msg": "Sin contenido (No Content)"}
        return {"status": r.status_code, "data": r.json()}
    except Exception as e:
        return {"status": -1, "error": str(e)}


def _put(url: str, params: dict | None = None, body: dict | None = None) -> dict:
    try:
        r = httpx.put(url, params=params, json=body, timeout=TIMEOUT)
        return {"status": r.status_code, "data": r.json()}
    except Exception as e:
        return {"status": -1, "error": str(e)}


def _post(url: str, params: dict | None = None, body=None) -> dict:
    try:
        r = httpx.post(url, params=params, json=body, timeout=TIMEOUT)
        if r.status_code == 204:
            return {"status": 204, "msg": "Sin contenido (No Content)"}
        return {"status": r.status_code, "data": r.json()}
    except Exception as e:
        return {"status": -1, "error": str(e)}


def _delete(url: str, params: dict | None = None) -> dict:
    try:
        r = httpx.delete(url, params=params, timeout=TIMEOUT)
        if r.status_code == 204:
            return {"status": 204, "msg": "Sin contenido (No Content)"}
        return {"status": r.status_code, "data": r.json()}
    except Exception as e:
        return {"status": -1, "error": str(e)}


# ══════════════════════════════════════════════════════════════════════════════
#  APIREDIS  –  Estado en tiempo real (Redis)
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def redis_ping() -> dict:
    """Verifica la conectividad con el servicio apiredis y la base Redis."""
    return _get(f"{APIREDIS_BASE}/apiredis/ping")


@mcp.tool()
def redis_get_config(unit: str) -> dict:
    """
    Obtiene la configuración en tiempo real (almacenada en Redis) para una unidad.

    Args:
        unit: Identificador de la unidad (DLGID / PLCID).
    """
    return _get(f"{APIREDIS_BASE}/apiredis/config", params={"unit": unit})


@mcp.tool()
def redis_put_config(unit: str, config: dict) -> dict:
    """
    Actualiza (override) la configuración en Redis para una unidad.

    Args:
        unit:   Identificador de la unidad.
        config: Diccionario con la configuración completa a almacenar.
    """
    return _put(f"{APIREDIS_BASE}/apiredis/config", params={"unit": unit}, body=config)


@mcp.tool()
def redis_delete_unit(unit: str) -> dict:
    """
    Elimina el registro completo de una unidad en Redis.

    Args:
        unit: Identificador de la unidad a eliminar.
    """
    return _delete(f"{APIREDIS_BASE}/apiredis/delete", params={"unit": unit})


@mcp.tool()
def redis_get_debugid() -> dict:
    """Retorna el ID de la unidad que está actualmente en modo debug."""
    return _get(f"{APIREDIS_BASE}/apiredis/debugid")


@mcp.tool()
def redis_set_debugid(debugid: str) -> dict:
    """
    Establece la unidad que debe estar en modo debug.

    Args:
        debugid: Identificador de la unidad a poner en debug.
    """
    return _put(f"{APIREDIS_BASE}/apiredis/debugid", body={"debugid": debugid})


@mcp.tool()
def redis_get_uid2id(uid: str) -> dict:
    """
    Obtiene el DLGID/PLCID asociado a un UID de hardware.

    Args:
        uid: UID del hardware (chipID, etc.).
    """
    return _get(f"{APIREDIS_BASE}/apiredis/uid2id", params={"uid": uid})


@mcp.tool()
def redis_put_uid2id(uid: str, unit_id: str) -> dict:
    """
    Actualiza la asociación entre un UID de hardware y un ID de unidad.

    Args:
        uid:     UID del hardware.
        unit_id: Identificador de la unidad (DLGID / PLCID).
    """
    return _put(f"{APIREDIS_BASE}/apiredis/uid2id", body={"uid": uid, "id": unit_id})


@mcp.tool()
def redis_get_ordenes(unit: str) -> dict:
    """
    Lee las órdenes pendientes para una unidad (ej. RESET, PRENDER_BOMBA).

    Args:
        unit: Identificador de la unidad.
    """
    return _get(f"{APIREDIS_BASE}/apiredis/ordenes", params={"unit": unit})


@mcp.tool()
def redis_put_ordenes(unit: str, ordenes: str) -> dict:
    """
    Actualiza (override) las órdenes para una unidad.

    Args:
        unit:    Identificador de la unidad.
        ordenes: String de órdenes separadas por ';' (ej. 'RESET;PRENDER_BOMBA').
    """
    return _put(f"{APIREDIS_BASE}/apiredis/ordenes", params={"unit": unit}, body={"ordenes": ordenes})


@mcp.tool()
def redis_delete_ordenes(unit: str) -> dict:
    """
    Elimina las órdenes pendientes de una unidad.

    Args:
        unit: Identificador de la unidad.
    """
    return _delete(f"{APIREDIS_BASE}/apiredis/ordenes", params={"unit": unit})


@mcp.tool()
def redis_get_ordenes_atvise(unit: str) -> dict:
    """
    Retorna las órdenes Atvise para una unidad (diccionario TAG→valor).

    Args:
        unit: Identificador de la unidad.
    """
    return _get(f"{APIREDIS_BASE}/apiredis/ordenesatvise", params={"unit": unit})


@mcp.tool()
def redis_put_ordenes_atvise(unit: str, ordenes_atvise: dict) -> dict:
    """
    Actualiza las órdenes Atvise para una unidad.

    Args:
        unit:           Identificador de la unidad.
        ordenes_atvise: Diccionario con las órdenes Atvise (ej. {'UPA1_ORDER_1': 101}).
    """
    return _put(
        f"{APIREDIS_BASE}/apiredis/ordenesatvise",
        params={"unit": unit},
        body={"ordenes_atvise": ordenes_atvise},
    )


@mcp.tool()
def redis_delete_ordenes_atvise(unit: str) -> dict:
    """
    Elimina las órdenes Atvise de una unidad.

    Args:
        unit: Identificador de la unidad.
    """
    return _delete(f"{APIREDIS_BASE}/apiredis/ordenesatvise", params={"unit": unit})


@mcp.tool()
def redis_get_dataline(unit: str) -> dict:
    """
    Retorna la última línea de datos recibida de una unidad.

    Args:
        unit: Identificador de la unidad.
    """
    return _get(f"{APIREDIS_BASE}/apiredis/dataline", params={"unit": unit})


@mcp.tool()
def redis_put_dataline(unit: str, tipo: str, data: dict) -> dict:
    """
    Actualiza la última línea de datos de una unidad y la encola en RXDATA_QUEUE.

    Args:
        unit:  Identificador de la unidad.
        tipo:  Tipo de protocolo (ej. 'PLCR3', 'SPQ_AVRDA').
        data:  Diccionario con los valores de la línea.
    """
    return _put(
        f"{APIREDIS_BASE}/apiredis/dataline",
        params={"unit": unit, "type": tipo},
        body=data,
    )


@mcp.tool()
def redis_get_queue_length(qname: str) -> dict:
    """
    Retorna la cantidad de elementos en una cola Redis.

    Args:
        qname: Nombre de la cola (ej. 'RXDATA_QUEUE', 'LOG_QUEUE').
    """
    return _get(f"{APIREDIS_BASE}/apiredis/queuelength", params={"qname": qname})


@mcp.tool()
def redis_get_queue_items(qname: str, count: int) -> dict:
    """
    Extrae (pop) elementos de una cola Redis.

    Args:
        qname: Nombre de la cola.
        count: Cantidad máxima de elementos a extraer.
    """
    return _get(
        f"{APIREDIS_BASE}/apiredis/queueitems",
        params={"qname": qname, "count": count},
    )


@mcp.tool()
def redis_get_log_queue_length() -> dict:
    """Retorna la cantidad de elementos en la cola LOG_QUEUE."""
    return _get(f"{APIREDIS_BASE}/apiredis/logqueuelength")


@mcp.tool()
def redis_pop_log_queue(count: int) -> dict:
    """
    Extrae (pop) registros de la cola LOG_QUEUE.

    Args:
        count: Cantidad de registros a extraer.
    """
    return _get(f"{APIREDIS_BASE}/apiredis/logqueuepop", params={"count": count})


@mcp.tool()
def redis_push_log_queue(log_data: str) -> dict:
    """
    Encola un string de log en LOG_QUEUE.

    Args:
        log_data: String de log a encolar.
    """
    return _put(f"{APIREDIS_BASE}/apiredis/logqueuepush", body=json.dumps({"log_data": log_data}))


@mcp.tool()
def redis_get_stats() -> dict:
    """
    Retorna los timestamps del último acceso de todas las unidades
    (tabla TIMESTAMP en Redis).
    """
    return _get(f"{APIREDIS_BASE}/apiredis/stats")


# ══════════════════════════════════════════════════════════════════════════════
#  APICONF  –  Configuraciones persistidas en PostgreSQL
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def conf_ping() -> dict:
    """Verifica la conectividad con el servicio apiconf y la base PostgreSQL."""
    return _get(f"{APICONF_BASE}/apiconf/ping")


@mcp.tool()
def conf_get_versiones(tipo: str) -> dict:
    """
    Retorna la lista de versiones de templates disponibles.

    Args:
        tipo: 'DLG' para DataLogger o 'PLC' para PLC.
    """
    return _get(f"{APICONF_BASE}/apiconf/versiones", params={"type": tipo})


@mcp.tool()
def conf_get_template(tipo: str, version: str = "LATEST") -> dict:
    """
    Retorna el template de configuración para un tipo y versión dados.

    Args:
        tipo:    'DLG' o 'PLC'.
        version: Versión del template (ej. '1.1.0') o 'LATEST' para la última.
    """
    return _get(f"{APICONF_BASE}/apiconf/template", params={"type": tipo, "ver": version})


@mcp.tool()
def conf_get_config(unit: str) -> dict:
    """
    Lee la configuración de una unidad desde PostgreSQL.

    Args:
        unit: Identificador de la unidad.
    """
    return _get(f"{APICONF_BASE}/apiconf/config", params={"unit": unit})


@mcp.tool()
def conf_post_config(unit: str, config: dict) -> dict:
    """
    Crea o actualiza la configuración de una unidad en PostgreSQL.

    Args:
        unit:   Identificador de la unidad.
        config: Diccionario con la configuración completa.
    """
    return _post(f"{APICONF_BASE}/apiconf/config", params={"unit": unit}, body=config)


@mcp.tool()
def conf_get_all_units() -> dict:
    """Lista todas las unidades configuradas en PostgreSQL."""
    return _get(f"{APICONF_BASE}/apiconf/unidades")


@mcp.tool()
def conf_get_uid2id(uid: str) -> dict:
    """
    Retorna el ID de unidad asociado a un UID en la tabla recoverid de PostgreSQL.

    Args:
        uid: UID del hardware.
    """
    return _get(f"{APICONF_BASE}/apiconf/uid2id", params={"uid": uid})


@mcp.tool()
def conf_put_uid2id(uid: str, unit_id: str) -> dict:
    """
    Crea o actualiza la asociación UID↔ID en la tabla recoverid de PostgreSQL.

    Args:
        uid:     UID del hardware.
        unit_id: Identificador de la unidad (no puede ser 'DEFAULT').
    """
    return _put(f"{APICONF_BASE}/apiconf/uid2id", body={"uid": uid, "id": unit_id})


@mcp.tool()
def conf_post_comms_id_params(dlgid: str, uid: str, imei: str, iccid: str,
                               tipo: str = "NONE", ver: str = "NONE") -> dict:
    """
    Registra los parámetros de comunicaciones de una unidad en la tabla comms_logs.

    Args:
        dlgid: Identificador de la unidad.
        uid:   UID del hardware.
        imei:  IMEI del módem.
        iccid: ICCID de la SIM.
        tipo:  Tipo de equipo (opcional).
        ver:   Versión de firmware (opcional).
    """
    payload = json.dumps({
        "DLGID": dlgid,
        "UID":   uid,
        "IMEI":  imei,
        "ICCID": iccid,
        "TYPE":  tipo,
        "VER":   ver,
    })
    return _post(f"{APICONF_BASE}/apiconf/commsidparams", body=payload)


# ══════════════════════════════════════════════════════════════════════════════
#  APIDATOS  –  Datos históricos y gestión de usuarios de datos
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def datos_ping() -> dict:
    """Verifica la conectividad con el servicio apidatos y la base PostgreSQL."""
    return _get(f"{APIDATOS_BASE}/apidatos/ping")


@mcp.tool()
def datos_create_user(label: str) -> dict:
    """
    Crea un nuevo usuario de datos y retorna su user_id generado.

    Args:
        label: Etiqueta o descripción del usuario (ej. 'cliente_scada').
    """
    return _post(f"{APIDATOS_BASE}/apidatos/usuarios", params={"label": label})


@mcp.tool()
def datos_get_user(user_id: str) -> dict:
    """
    Retorna los datos de un usuario (fecha último acceso, puntero de datos, label).

    Args:
        user_id: ID del usuario generado al crear.
    """
    return _get(f"{APIDATOS_BASE}/apidatos/usuarios", params={"user": user_id})


@mcp.tool()
def datos_delete_user(user_id: str) -> dict:
    """
    Elimina un usuario de datos.

    Args:
        user_id: ID del usuario a eliminar.
    """
    return _delete(f"{APIDATOS_BASE}/apidatos/usuarios", params={"user": user_id})


@mcp.tool()
def datos_get_chunk(user_id: str) -> dict:
    """
    Obtiene el siguiente chunk de datos para un usuario (paginación automática).
    Cada llamada avanza el puntero interno del usuario.

    Args:
        user_id: ID del usuario de datos.
    """
    return _get(f"{APIDATOS_BASE}/apidatos/datos", params={"user": user_id})


@mcp.tool()
def datos_list_all_users() -> dict:
    """Lista todos los usuarios de datos registrados en el sistema."""
    return _get(f"{APIDATOS_BASE}/apidatos/config/usuarios")


@mcp.tool()
def datos_list_all_equipment_configs() -> dict:
    """
    Lista todas las configuraciones de equipos almacenadas en PostgreSQL
    (tabla configuraciones: unit_id, uid, jconfig).
    """
    return _get(f"{APIDATOS_BASE}/apidatos/config/equipos")


@mcp.tool()
def buscar_equipos_por_hardware(tipo_entrada: str, valor: str) -> dict:
    """
    Busca masivamente en todas las configuraciones JSON de los equipos.
    Puede buscar por una variable simple o por múltiples variables simultáneamente.
    
    DOCUMENTACIÓN IMPORTANTE PARA AGENTES:
    - Cuando busques equipos midiendo magnitudes (presiones, caudales, etc.), recuerda que existen campos de estado de habilitación.
    - La simple presencia de una configuración NO implica que esté activa. Debes comprobar el estado ("ENABLE": "TRUE").
    - Los canales están estructurados en 'AINPUTS' (analógicos), 'COUNTERS' (pulsos/digitales) y 'MODBUS'.
    - Para saber exactamente qué mide cualquier variable (analógica, pulso o modbus), debes revisar obligatoriamente el TAG vinculado en Aqua (`config_puntos_mcp`), ya que la configuración del equipo dicta el "cómo" pero Aqua dicta el "qué".
    - Para buscar por hardware de forma estricta, usa un JSON en `tipo_entrada`. Ejemplo: 
      '{"AINPUTS.A0.ENABLE": "TRUE"}'
    
    Args:
        tipo_entrada: Ruta de la variable (ej. 'AINPUTS.A0.MODO') o un string JSON con múltiples condiciones.
        valor: Valor esperado (como string). Si tipo_entrada es un JSON, este campo se ignora.
    """
    if not MCP_DATABASE_URL:
        return {"status": -1, "error": "MCP_DATABASE_URL no está configurada en .env"}

    # Parsear condiciones
    condiciones = {}
    if tipo_entrada.strip().startswith("{"):
        try:
            condiciones = json.loads(tipo_entrada)
        except json.JSONDecodeError:
            return {"status": -1, "error": "tipo_entrada no es un JSON válido."}
    else:
        condiciones = {tipo_entrada: valor}

    try:
        conn = psycopg2.connect(MCP_DATABASE_URL)
        cur = conn.cursor()
        
        # Si hay un valor simple, hacemos un filtro rápido SQL para optimizar
        rows = []
        if len(condiciones) == 1 and not tipo_entrada.strip().startswith("{"):
            valor_safe = str(valor).replace("'", "''")
            query = f"SELECT unit_id, jconfig FROM configuraciones WHERE jconfig::text LIKE '%{valor_safe}%'"
            cur.execute(query)
            rows = cur.fetchall()
        else:
            # Si hay múltiples condiciones, traemos todo (o podríamos encadenar LIKEs, pero procesar en Python es rápido)
            cur.execute("SELECT unit_id, jconfig FROM configuraciones")
            rows = cur.fetchall()
        
        conn.close()
    except Exception as e:
        return {"status": -1, "error": f"Error conectando a BD: {str(e)}"}

    def find_in_config(config, path_parts, expected_value):
        if not path_parts:
            return str(config).lower() == str(expected_value).lower()
        
        key = path_parts[0]
        rest = path_parts[1:]
        
        if isinstance(config, dict):
            if key in config:
                return find_in_config(config[key], rest, expected_value)
        elif isinstance(config, list):
            try:
                idx = int(key)
                if 0 <= idx < len(config):
                    return find_in_config(config[idx], rest, expected_value)
            except ValueError:
                pass
            for item in config:
                if find_in_config(item, path_parts, expected_value):
                    return True
        return False

    resultados_plc = []
    resultados_dlg = []
    
    for unit_id, jconfig in rows:
        if isinstance(jconfig, str):
            try:
                jconfig = json.loads(jconfig)
            except json.JSONDecodeError:
                continue
                
        cumple_todas = True
        for ruta, val_esperado in condiciones.items():
            if not find_in_config(jconfig, ruta.split('.'), val_esperado):
                cumple_todas = False
                break
                
        if cumple_todas:
            # Diferenciar DLG de PLC
            if "MEMBLOCK" in jconfig or "REMVARS" in jconfig or "DATOS_PLC" in str(jconfig):
                resultados_plc.append(unit_id)
            else:
                resultados_dlg.append(unit_id)
                
    return {
        "status": 200,
        "resumen": {
            "total_encontrados": len(resultados_plc) + len(resultados_dlg),
            "cantidad_plc": len(resultados_plc),
            "cantidad_dlg": len(resultados_dlg)
        },
        "equipos_plc": resultados_plc,
        "equipos_dlg": resultados_dlg
    }


# ══════════════════════════════════════════════════════════════════════════════
#  APICOMMS  –  Proxy de comunicaciones
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def comms_ping() -> dict:
    """Verifica la conectividad con el servicio apicomms y su enlace con apiredis/apiconf."""
    return _get(f"{APICOMMS_BASE}/apicomms/ping")


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    mcp.run(transport="stdio")
