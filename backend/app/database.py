# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session
import os

# SQLite file in project root (backend/)
DB_FILE = os.getenv("DATABASE_URL", "sqlite:///./db.sqlite3")
# For SQLite, create_engine requires connect_args for thread check
engine = create_engine(
    DB_FILE,
    connect_args={"check_same_thread": False} if DB_FILE.startswith("sqlite") else {},
    echo=False,
)

# Synchronous session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for models
Base = declarative_base()

def init_db():
    """Create DB tables. Call at app startup."""
    Base.metadata.create_all(bind=engine)
