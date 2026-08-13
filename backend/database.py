"""SQLAlchemy engine, session, and FastAPI DB dependency.

See Docs/BUILD_PLAN.md §7. The engine is created lazily from DATABASE_URL; if
the URL is not yet configured the app still boots (so /health can report
db_connected=false) instead of crashing on import.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import DATABASE_URL

# Declarative base shared by the ORM models (models.py).
Base = declarative_base()

SQLITE_FALLBACK = "sqlite:///./backend.db"
effective_url = DATABASE_URL if DATABASE_URL else SQLITE_FALLBACK

is_sqlite = effective_url.startswith("sqlite")
engine = create_engine(
    effective_url,
    connect_args={"check_same_thread": False} if is_sqlite else {},
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency yielding a DB session (used from M1 onward)."""
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is not configured in backend/.env")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
