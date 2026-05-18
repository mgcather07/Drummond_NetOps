from app.database.sql import get_sql_connection

conn = get_sql_connection()

cursor = conn.cursor()
cursor.execute("SELECT TOP 1 * FROM dbo.users")

row = cursor.fetchone()
print("SQL CONNECTED!")
print(row)

conn.close()