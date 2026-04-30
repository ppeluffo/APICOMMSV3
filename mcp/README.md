# MCP comms_spymovil

> [!IMPORTANT]
> Este servidor MCP gestiona **exclusivamente** el sistema de comunicaciones y equipos de **Spymovil** (APICOMMSV3).
> **No afecta a los equipos de ANTEL**, los cuales deben gestionarse a través del MCP `config_equipos_antel`.

Servidor MCP que expone como herramientas todas las operaciones de las APIs del sistema **APICOMMSV3** de Spymovil.

## APIs cubiertas

| Servicio   | Puerto | Descripción |
|------------|--------|-------------|
| `apiredis` | 5100   | Estado en tiempo real de equipos (Redis) |
| `apiconf`  | 5200   | Configuraciones persistidas (PostgreSQL) |
| `apidatos` | 5300   | Datos históricos y usuarios de datos |

## Instalación

```bash
cd mcp
pip install -r requirements.txt
```

## Configuración del cliente MCP (Antigravity / Claude Desktop)

Puedes copiar el archivo `.env.example` a `.env` y ajustarlo según sea necesario.

Agregar en el archivo de configuración MCP del cliente:

```json
{
  "mcpServers": {
    "comms_spymovil": {
      "command": "python",
      "args": ["/home/ulises/Desarrollo/APICOMMSV3/mcp/server.py"],
      "env": {
        "APIREDIS_HOST": "localhost",
        "APIREDIS_PORT": "5100",
        "APICONF_HOST":  "localhost",
        "APICONF_PORT":  "5200",
        "APIDATOS_HOST": "localhost",
        "APIDATOS_PORT": "5300"
      }
    }
  }
}
```

## Variables de entorno

| Variable        | Default       | Descripción |
|-----------------|---------------|-------------|
| `APIREDIS_HOST` | `localhost`   | Host del servicio apiredis |
| `APIREDIS_PORT` | `5100`        | Puerto del servicio apiredis |
| `APICONF_HOST`  | `localhost`   | Host del servicio apiconf |
| `APICONF_PORT`  | `5200`        | Puerto del servicio apiconf |
| `APIDATOS_HOST` | `localhost`   | Host del servicio apidatos |
| `APIDATOS_PORT` | `5300`        | Puerto del servicio apidatos |

## Tools disponibles

### 🔴 apiredis – Redis (tiempo real)

| Tool | Método | Endpoint |
|------|--------|----------|
| `redis_ping` | GET | `/apiredis/ping` |
| `redis_get_config(unit)` | GET | `/apiredis/config` |
| `redis_put_config(unit, config)` | PUT | `/apiredis/config` |
| `redis_delete_unit(unit)` | DELETE | `/apiredis/delete` |
| `redis_get_debugid()` | GET | `/apiredis/debugid` |
| `redis_set_debugid(debugid)` | PUT | `/apiredis/debugid` |
| `redis_get_uid2id(uid)` | GET | `/apiredis/uid2id` |
| `redis_put_uid2id(uid, unit_id)` | PUT | `/apiredis/uid2id` |
| `redis_get_ordenes(unit)` | GET | `/apiredis/ordenes` |
| `redis_put_ordenes(unit, ordenes)` | PUT | `/apiredis/ordenes` |
| `redis_delete_ordenes(unit)` | DELETE | `/apiredis/ordenes` |
| `redis_get_ordenes_atvise(unit)` | GET | `/apiredis/ordenesatvise` |
| `redis_put_ordenes_atvise(unit, ordenes_atvise)` | PUT | `/apiredis/ordenesatvise` |
| `redis_delete_ordenes_atvise(unit)` | DELETE | `/apiredis/ordenesatvise` |
| `redis_get_dataline(unit)` | GET | `/apiredis/dataline` |
| `redis_put_dataline(unit, tipo, data)` | PUT | `/apiredis/dataline` |
| `redis_get_queue_length(qname)` | GET | `/apiredis/queuelength` |
| `redis_get_queue_items(qname, count)` | GET | `/apiredis/queueitems` |
| `redis_get_log_queue_length()` | GET | `/apiredis/logqueuelength` |
| `redis_pop_log_queue(count)` | GET | `/apiredis/logqueuepop` |
| `redis_push_log_queue(log_data)` | PUT | `/apiredis/logqueuepush` |
| `redis_get_stats()` | GET | `/apiredis/stats` |

### 🟡 apiconf – Configuración (PostgreSQL)

| Tool | Método | Endpoint |
|------|--------|----------|
| `conf_ping()` | GET | `/apiconf/ping` |
| `conf_get_versiones(tipo)` | GET | `/apiconf/versiones` |
| `conf_get_template(tipo, version)` | GET | `/apiconf/template` |
| `conf_get_config(unit)` | GET | `/apiconf/config` |
| `conf_post_config(unit, config)` | POST | `/apiconf/config` |
| `conf_get_all_units()` | GET | `/apiconf/unidades` |
| `conf_get_uid2id(uid)` | GET | `/apiconf/uid2id` |
| `conf_put_uid2id(uid, unit_id)` | PUT | `/apiconf/uid2id` |
| `conf_post_comms_id_params(...)` | POST | `/apiconf/commsidparams` |

### 🟢 apidatos – Datos históricos

| Tool | Método | Endpoint |
|------|--------|----------|
| `datos_ping()` | GET | `/apidatos/ping` |
| `datos_create_user(label)` | POST | `/apidatos/usuarios` |
| `datos_get_user(user_id)` | GET | `/apidatos/usuarios` |
| `datos_delete_user(user_id)` | DELETE | `/apidatos/usuarios` |
| `datos_get_chunk(user_id)` | GET | `/apidatos/datos` |
| `datos_list_all_users()` | GET | `/apidatos/config/usuarios` |
| `datos_list_all_equipment_configs()` | GET | `/apidatos/config/equipos` |
