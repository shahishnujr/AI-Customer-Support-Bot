# backend/faq.py
import os
import json
import sqlite3
from typing import List, Dict, Any, Optional
import numpy as np
from dotenv import load_dotenv

# reuse the client from your llm_client
# path: backend/app/llm_client.py -> importable as app.llm_client if backend is run as top-level
from .llm_client import client as openai_client
  # <- re-uses your existing OpenAI client

load_dotenv()

DB_URL = os.getenv("DB_URL", "sqlite:///./ai-cs-bot.db")
if DB_URL.startswith("sqlite:///"):
    DB_FILE = DB_URL.replace("sqlite:///", "")
else:
    DB_FILE = "./ai-cs-bot.db"

EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")


# ---------------------
# SQLite helpers
# ---------------------
def get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_tables():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS faqs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            embedding TEXT NOT NULL,
            metadata TEXT
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            metadata TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT, -- 'user' or 'assistant' or 'system'
            content TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    conn.commit()
    conn.close()


init_tables()


# ---------------------
# Embeddings helpers
# ---------------------
def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Use the shared openai_client (from app.llm_client) to compute embeddings.
    Returns a list of embedding vectors (lists of floats) matching texts order.
    """
    if not texts:
        return []
    resp = openai_client.embeddings.create(model=EMBED_MODEL, input=texts)
    # resp.data -> list of objects with .embedding
    embeddings = [item.embedding for item in resp.data]
    return embeddings


# ---------------------
# FAQ CRUD + search
# ---------------------
def upsert_faqs(faq_items: List[Dict[str, Any]]):
    """
    Insert FAQ rows. faq_items: list of {"question": "...", "answer": "...", "metadata": {...}}
    (This function appends; no dedupe/upsert by question — extend if you want de-dup.)
    """
    texts = [f["question"].strip() + "\n" + f.get("answer", "").strip() for f in faq_items]
    embeddings = embed_texts(texts)
    conn = get_conn()
    cur = conn.cursor()
    for item, emb in zip(faq_items, embeddings):
        cur.execute(
            "INSERT INTO faqs (question, answer, embedding, metadata) VALUES (?, ?, ?, ?)",
            (item["question"], item.get("answer", ""), json.dumps(emb), json.dumps(item.get("metadata", {}))),
        )
    conn.commit()
    conn.close()


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    if a.size == 0 or b.size == 0:
        return 0.0
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0.0:
        return 0.0
    return float(np.dot(a, b) / denom)


def get_top_k_faqs(query: str, top_k: int = 3, threshold: float = 0.0) -> List[Dict[str, Any]]:
    """
    Compute embedding for the query and return top_k FAQ items with score >= threshold.
    Returns list of dicts: {id,question,answer,metadata,score}
    """
    if not query:
        return []

    q_emb = embed_texts([query])[0]
    qv = np.array(q_emb, dtype=float)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, question, answer, embedding, metadata FROM faqs")
    rows = cur.fetchall()
    scored = []
    for r in rows:
        emb = np.array(json.loads(r["embedding"]), dtype=float)
        score = _cosine_sim(qv, emb)
        scored.append(
            {
                "id": r["id"],
                "question": r["question"],
                "answer": r["answer"],
                "metadata": json.loads(r["metadata"]) if r["metadata"] else {},
                "score": score,
            }
        )
    conn.close()

    scored.sort(key=lambda x: x["score"], reverse=True)
    filtered = [s for s in scored if s["score"] >= threshold]
    return filtered[:top_k]


# ---------------------
# message/session helpers
# ---------------------
def save_message(session_id: str, role: str, content: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)", (session_id, role, content))
    conn.commit()
    conn.close()


def get_recent_messages(session_id: str, limit: int = 20):
    """
    Returns messages in chronological order (oldest -> newest) up to limit.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT role, content, created_at FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT ?", (session_id, limit))
    rows = cur.fetchall()
    conn.close()
    # reverse to chronological
    rows = list(rows)[::-1]
    return [{"role": r["role"], "content": r["content"], "created_at": r["created_at"]} for r in rows]
