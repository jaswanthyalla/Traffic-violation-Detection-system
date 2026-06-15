import sqlite3
print("CHECK DB:", "database/violations.db")

conn = sqlite3.connect("database/violations.db")
cursor = conn.cursor()

# Show all owners
cursor.execute("SELECT * FROM owners")
rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()