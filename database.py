from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

DATABASE_URL = "sqlite:///./data/diun.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class DiunUpdate(Base):
    __tablename__ = "diun_updates"

    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String, index=True)
    status = Column(String, index=True)
    provider = Column(String)
    image_name = Column(String, index=True)
    image_tag = Column(String)
    hub_link = Column(String)
    digest = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
