# backend/add_sessions_metadata.py
import os
import sqlite3
import json
from dotenv import load_dotenv

# Load .env from backend/.env
here = os.path.dirname(__file__)
load_dotenv(dotenv_path=os.path.join(here, ".env"))

DB_URL = os.getenv("DB_URL", "sqlite:///./ai-cs-bot.db")
if DB_URL.startswith("sqlite:///"):
    DB_FILE = DB_URL.replace("sqlite:///", "")
else:
    DB_FILE = "./ai-cs-bot.db"

print("Using DB file:", DB_FILE)
conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

# Check if sessions table exists
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions';")
if not cur.fetchone():
    print("No sessions table found. Nothing to migrate (or you can recreate DB).")
    conn.close()
    raise SystemExit(1)

# Check existing columns
cur.execute("PRAGMA table_info(sessions);")
cols = [row[1] for row in cur.fetchall()]
print("Existing columns in sessions:", cols)

if "metadata" in cols:
    print("Column 'metadata' already exists. No action needed.")
else:
    print("Adding 'metadata' column to sessions table...")
    # SQLite supports adding a new column with a default value
    cur.execute("ALTER TABLE sessions ADD COLUMN metadata TEXT;")
    conn.commit()
    print("Column added.")
    # Optional: initialize existing rows to '{}' (not necessary, but clean)
    cur.execute("UPDATE sessions SET metadata = ? WHERE metadata IS NULL;", (json.dumps({}),))
    conn.commit()
    print("Existing rows initialized with empty JSON object for metadata.")
conn.close()
print("Done.")
