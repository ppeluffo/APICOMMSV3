import httpx
import json

r = httpx.get("http://localhost:5300/apidatos/config/equipos")
print("apidatos config/equipos status:", r.status_code)
if r.status_code == 200:
    data = r.json()
    print("Total Spymovil configs:", len(data))

