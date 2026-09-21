from sqlalchemy.orm import DeclarativeBase

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings

# Use configured database URL (defaults to SQLite for local development)
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# SQLite requires check_same_thread=False; other databases do not
connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Connect to the DB
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)

# Operation Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Base Model
class Base(DeclarativeBase):
    pass


# dependency to give a session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
