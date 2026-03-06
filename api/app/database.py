# =============================================================================
# database.py — SQLAlchemy Database Setup
# =============================================================================
# What this file does:
#   Creates the database engine, session factory, and ORM base class that all
#   models inherit from. Also defines get_db, the dependency FastAPI injects
#   into every route that needs database access.
#
# Key decisions:
#   - DATABASE_URL env var: lets the same code run against SQLite locally and
#     PostgreSQL in Docker without changing a single line.
#   - check_same_thread=False: SQLite rejects cross-thread use by default.
#     FastAPI runs each request in a thread pool so we have to disable that check.
#   - get_db as a generator: the `yield` hands the session to the route handler,
#     then the `finally` block closes it no matter what — even if an exception
#     occurs mid-request. FastAPI's Depends() understands generators and calls
#     the cleanup automatically.
# =============================================================================

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./retro_games.db")

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
