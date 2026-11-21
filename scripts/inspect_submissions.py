import sqlite3
import os

db_path = "codeguard.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get current table sql
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='submissions'")
res = cursor.fetchone()
print("Current submissions schema:")
print(res[0] if res else "Not found")

# Check pragma table_info
cursor.execute("PRAGMA table_info(submissions)")
cols = cursor.fetchall()
print("\nColumns:")
for c in cols:
    print(c)
conn.close()
