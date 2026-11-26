import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

URL = os.getenv("DATABASE_URL", "sqlite:///./mindmate.db")
for _p in ("postgres://", "postgresql://"):  # hosts hand out these; SQLAlchemy needs the driver name
    if URL.startswith(_p):
        URL = "postgresql+psycopg://" + URL[len(_p):]
engine = create_engine(URL, connect_args={"check_same_thread": False} if URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
