import psycopg2
import os
from dotenv import load_dotenv

load_dotenv("/home/ulises/Desarrollo/APICOMMSV3/mcp/.env")

try:
    conn = psycopg2.connect(
        host="192.168.0.8", # from .env APIDATOS_HOST is 192.168.0.8
        port="5432",
        database="bd_spcomms",
        user="admin",
        password="pexco599" # from apidatos.py defaults
    )
    cur = conn.cursor()
    cur.execute("SELECT version();")
    print(cur.fetchone()[0])
    conn.close()
except Exception as e:
    print("DB connect error:", e)
