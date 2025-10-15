# backend/fix_sessions_schema.py
import os, sqlite3, json
from dotenv import load_dotenv

here = os.path.dirname(__file__)
load_dotenv(dotenv_path=os.path.join(here, ".env"))

DB_URL = os.getenv("DB_URL", "sqlite:///./ai-cs-bot.db")
DB_FILE = DB_URL.replace("sqlite:///", "") if DB_URL.startswith("sqlite:///") else DB_URL

print("DB file:", DB_FILE)
conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

# 1) Inspect existing schema
print("Existing sessions schema:")
cur.execute("PRAGMA table_info(sessions);")
rows = cur.fetchall()
for r in rows:
    print(r)
print("Existing messages schema:")
cur.execute("PRAGMA table_info(messages);")
for r in cur.fetchall():
    print(r)

# 2) Read current rows (safe copy)
cur.execute("SELECT id, user_id, metadata, created_at FROM sessions")
sessions_rows = cur.fetchall()
cur.execute("SELECT id, session_id, role, content, created_at FROM messages")
messages_rows = cur.fetchall()
print(f"Found {len(sessions_rows)} session rows and {len(messages_rows)} message rows (will preserve).")

# 3) Create new tables with correct schema names
cur.execute("CREATE TABLE IF NOT EXISTS sessions_new (id TEXT PRIMARY KEY, user_id TEXT, metadata TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
cur.execute("CREATE TABLE IF NOT EXISTS messages_new (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, role TEXT, content TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
conn.commit()

# 4) Copy data into new tables, casting ids to str
for r in sessions_rows:
    old_id, user_id, metadata, created_at = r
    new_id = str(old_id) if old_id is not None else None
    metadata_val = metadata if metadata is not None else json.dumps({})
    cur.execute("INSERT INTO sessions_new (id, user_id, metadata, created_at) VALUES (?, ?, ?, ?)", (new_id, user_id, metadata_val, created_at))

for r in messages_rows:
    _, session_id, role, content, created_at = r
    new_session_id = str(session_id) if session_id is not None else None
    cur.execute("INSERT INTO messages_new (session_id, role, content, created_at) VALUES (?, ?, ?, ?)", (new_session_id, role, content, created_at))

conn.commit()
print("Copied rows into sessions_new and messages_new.")

# 5) Drop old tables and rename new ones (backup original by renaming first)
cur.execute("ALTER TABLE sessions RENAME TO sessions_old_backup;")
cur.execute("ALTER TABLE messages RENAME TO messages_old_backup;")
cur.execute("ALTER TABLE sessions_new RENAME TO sessions;")
cur.execute("ALTER TABLE messages_new RENAME TO messages;")
conn.commit()

print("Renamed new tables into place. Old tables renamed to *_old_backup (you can delete them later).")

# 6) Verify
cur.execute("PRAGMA table_info(sessions);")
print("New sessions schema:", cur.fetchall())
cur.execute("SELECT COUNT(*) FROM sessions;")
print("Sessions count:", cur.fetchone()[0])
cur.execute("SELECT COUNT(*) FROM messages;")
print("Messages count:", cur.fetchone()[0])

conn.close()
print("Migration complete. Restart uvicorn.")
