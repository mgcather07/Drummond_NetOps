import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

SQL_SERVER = os.getenv("SQL_SERVER")
SQL_DATABASE = os.getenv("SQL_DATABASE")
SQL_USERNAME = os.getenv("SQL_USERNAME")
SQL_PASSWORD = os.getenv("SQL_PASSWORD")
SQL_AUTH_MODE = os.getenv("SQL_AUTH_MODE", "sql").lower()


def get_sql_connection():

    if SQL_AUTH_MODE == "windows":

        connection_string = f"""
        DRIVER={{ODBC Driver 18 for SQL Server}};
        SERVER={SQL_SERVER};
        DATABASE={SQL_DATABASE};
        Trusted_Connection=yes;
        Encrypt=no;
        TrustServerCertificate=yes;
        """

    else:

        connection_string = f"""
        DRIVER={{ODBC Driver 18 for SQL Server}};
        SERVER={SQL_SERVER};
        DATABASE={SQL_DATABASE};
        UID={SQL_USERNAME};
        PWD={SQL_PASSWORD};
        Encrypt=no;
        TrustServerCertificate=yes;
        """

    print("Attempting SQL connection...\n")

    try:
        conn = pyodbc.connect(connection_string)

        print("✅ SQL CONNECTION SUCCESSFUL\n")

        return conn

    except Exception as e:

        print("❌ SQL CONNECTION FAILED\n")
        print(f"ERROR TYPE: {type(e).__name__}")
        print(f"ERROR: {e}\n")

        raise