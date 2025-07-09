# backend/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()  # Define it here directly ✅

SQLALCHEMY_DATABASE_URL = "sqlite:///./backend/backend.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def init_db():
    from backend import models  # ✅ local import avoids circular issue
    Base.metadata.create_all(bind=engine)
