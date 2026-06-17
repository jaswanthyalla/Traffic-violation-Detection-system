import sqlite3

conn = sqlite3.connect("database/violations.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS owners (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plate_number TEXT UNIQUE,
    owner_name TEXT,
    phone TEXT
)
""")

conn.commit()
conn.close()

print("✅ Owners table created successfully")