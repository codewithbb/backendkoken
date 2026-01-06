import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()  # laadt .env automatisch

def get_connection():
    server = os.getenv("AZURE_SQL_SERVER")
    database = os.getenv("AZURE_SQL_DATABASE")
    username = os.getenv("AZURE_SQL_USERNAME")
    password = os.getenv("AZURE_SQL_PASSWORD")
    driver   = os.getenv("AZURE_SQL_DRIVER", "{ODBC Driver 18 for SQL Server}")
    encrypt  = os.getenv("AZURE_SQL_ENCRYPT", "yes")
    trust    = os.getenv("AZURE_SQL_TRUST_CERT", "no")
    timeout  = os.getenv("AZURE_SQL_TIMEOUT", "30")

    if not all([server, database, username, password]):
        raise RuntimeError("Missing Azure SQL environment variables")

    conn_str = (
        f"DRIVER={driver};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        f"Encrypt={encrypt};"
        f"TrustServerCertificate={trust};"
        f"Connection Timeout={timeout};"
    )

    return pyodbc.connect(conn_str)
