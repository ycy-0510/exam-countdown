import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "app.db"

DATABASE_DB_PATH = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

engine = create_engine(
    DATABASE_DB_PATH, 
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine,autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

def init_db():
    DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    from . import models # Import models to register them with SQLAlchemy
    Base.metadata.create_all(bind=engine)
