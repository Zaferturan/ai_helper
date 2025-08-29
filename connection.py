import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL

# Get absolute path for database file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "ai_helper.db")

# Create SQLAlchemy engine with absolute path
engine = create_engine(
    f"sqlite:///{DATABASE_PATH}",
    echo=True,  # Set to False in production
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={"check_same_thread": False}  # SQLite için gerekli
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 