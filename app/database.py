import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Load environment variables from .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Engine creation is deferred until a database URL is configured. This allows
# model metadata and migrations to be inspected without a local .env file.
engine = None
SessionLocal = None
if DATABASE_URL:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )


# Base class for all database models
class Base(DeclarativeBase):
    pass


# Dependency for database sessions
def get_db():
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is not configured in .env")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()