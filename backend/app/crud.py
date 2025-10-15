# app/crud.py
from typing import List, Optional
from sqlalchemy.orm import Session as DbSession
from . import models
from .database import SessionLocal
from datetime import datetime

# --- dependency helper (if you want to use directly) ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- session helpers ---
def create_session(db: DbSession, user_id: Optional[str] = None, meta_json: Optional[str] = None) -> models.Session:
    sess = models.Session(user_id=user_id, meta_json=meta_json)
    db.add(sess)
    db.commit()
    db.refresh(sess)
    return sess

def get_session(db: DbSession, session_id: int) -> Optional[models.Session]:
    return db.query(models.Session).filter(models.Session.id == session_id).first()

def update_session_last_active(db: DbSession, session_id: int):
    db.query(models.Session).filter(models.Session.id == session_id).update({"last_active": datetime.utcnow()})
    db.commit()

# --- message helpers ---
def add_message(db: DbSession, session_id: int, role: str, content: str, escalated: bool = False) -> models.Message:
    msg = models.Message(session_id=session_id, role=role, content=content, escalated=escalated)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

def get_messages(db: DbSession, session_id: int, limit: int = 100, offset: int = 0) -> List[models.Message]:
    return db.query(models.Message).filter(models.Message.session_id == session_id).order_by(models.Message.created_at).offset(offset).limit(limit).all()

def get_recent_messages(db: DbSession, session_id: int, limit: int = 10) -> List[models.Message]:
    # Return last `limit` messages in chronological order
    q = db.query(models.Message).filter(models.Message.session_id == session_id).order_by(models.Message.created_at.desc()).limit(limit).all()
    return list(reversed(q))
