import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# In production (PythonAnywhere), set DATABASE_URL env var.
# Locally, falls back to SQLite for development.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./jycloapp.db")

# SQLite needs check_same_thread; MySQL/Postgres do not.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# Use pool_recycle to avoid MySQL "gone away" errors on PythonAnywhere (which times out after 300s).
# pool_pre_ping verifies the connection is alive before using it.
engine = create_engine(
    DATABASE_URL, 
    connect_args=connect_args,
    pool_recycle=280,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
