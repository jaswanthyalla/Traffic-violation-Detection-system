import sqlite3

conn = sqlite3.connect("database/violations.db")
cursor = conn.cursor()

cursor.execute("DELETE FROM violations")
conn.commit()
conn.close()

print("Old data deleted")