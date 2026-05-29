import logging
import os

import pyodbc
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SQL_SERVER = os.getenv("SQL_SERVER")
SQL_DATABASE = os.getenv("SQL_DATABASE")
SQL_USERNAME = os.getenv("SQL_USERNAME")
SQL_PASSWORD = os.getenv("SQL_PASSWORD")
SQL_AUTH_MODE = os.getenv("SQL_AUTH_MODE", "sql").lower()


def get_sql_connection():

    if SQL_AUTH_MODE == "windows":

        connection_string = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={SQL_SERVER};"
            f"DATABASE={SQL_DATABASE};"
            "Trusted_Connection=yes;"
            "Encrypt=no;"
            "TrustServerCertificate=yes;"
        )

    else:

        connection_string = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={SQL_SERVER};"
            f"DATABASE={SQL_DATABASE};"
            f"UID={SQL_USERNAME};"
            f"PWD={SQL_PASSWORD};"
            "Encrypt=no;"
            "TrustServerCertificate=yes;"
        )

    logger.debug("SQL connection attempt to %s / %s", SQL_SERVER, SQL_DATABASE)

    try:
        conn = pyodbc.connect(connection_string)
        logger.debug("SQL connected successfully")
        return conn

    except Exception:
        logger.exception("SQL connection failed (server=%s db=%s)", SQL_SERVER, SQL_DATABASE)
        raise
