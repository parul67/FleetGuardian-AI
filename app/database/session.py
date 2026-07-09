from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import OperationalError
from app.core.config import settings

def _make_engine(database_url: str):
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    return create_engine(
        database_url,
        connect_args=connect_args,
        pool_pre_ping=True
    )


def _get_engine():
    """
    Use the configured database when it is reachable.
    Fall back to local SQLite when the app is started outside Docker and the
    Postgres service hostname cannot be resolved.
    """
    primary_engine = _make_engine(settings.DATABASE_URL)
    try:
        with primary_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return primary_engine
    except OperationalError as exc:
        if "could not translate host name \"postgres\"" not in str(exc):
            raise

        fallback_url = "sqlite:///./fleetguardian.db"
        fallback_engine = _make_engine(fallback_url)
        settings.DATABASE_URL = fallback_url
        return fallback_engine


engine = _get_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db() -> Generator:
    """Dependency database session lifecycle manager."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
