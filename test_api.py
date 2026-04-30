import os
import requests
from dotenv import load_dotenv

load_dotenv("/home/ulises/Desarrollo/spymovil_authorization/mcp/config_equipos_mcp/.env")

API_BASE_URL = os.getenv("COMMS_API_URL", "https://apicommsweb.spymovil.com")
API_USER = os.getenv("COMMS_USER")
API_PASS = os.getenv("COMMS_PASS")

from requests.auth import HTTPBasicAuth
auth = HTTPBasicAuth(API_USER, API_PASS)

res = requests.get(f"{API_BASE_URL}/apiweb/listarunidades", auth=auth)
print("listarunidades:", res.status_code)
if res.status_code == 200:
    data = res.json()
    print("PLCs:", len(data.get("l_plcs", [])))
    print("DLGs:", len(data.get("l_dlgs", [])))

res_all = requests.get(f"{API_BASE_URL}/apiweb/config_equipos", auth=auth)
print("config_equipos (no params):", res_all.status_code)

