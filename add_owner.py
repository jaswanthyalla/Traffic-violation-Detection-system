import sqlite3

# 👇 DB check print
conn = sqlite3.connect("database/violations.db")
print("ADD OWNER DB:", conn)

cursor = conn.cursor()

cursor.execute("""
INSERT OR REPLACE INTO owners (plate_number, owner_name, phone)
VALUES (?, ?, ?)
""", ("AP30ak5566", "jaswanth yalla", "+919347637152"))

conn.commit()
conn.close()

print("Owner added")