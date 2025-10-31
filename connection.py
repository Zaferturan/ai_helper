from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from config import DATABASE_URL, POSTGRES_SCHEMA_NAME

# Prepare connect_args for PostgreSQL schema
_connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}
elif DATABASE_URL.startswith("postgresql") and POSTGRES_SCHEMA_NAME != "ai_helper":
    # Set search_path for PostgreSQL schema using connect_args
    # Format: "-c option=value" for PostgreSQL connection options
    _connect_args = {"options": f"-csearch_path={POSTGRES_SCHEMA_NAME}"}

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args=_connect_args
)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency for database sessions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

