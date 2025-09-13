from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from .models import DiunUpdateData
from datetime import datetime, UTC

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
    image_created_at = Column(String)  # When the image was created (from DIUN)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))  # When webhook was received

def upsert_diun_update(db: Session, update_data: DiunUpdateData) -> DiunUpdate:
    """
    Create or update a DIUN update record, replacing any existing entries 
    for the same hostname and image name combination.
    
    Args:
        db: Database session
        update_data: DiunUpdateData object with parsed image data
    """
    # Delete existing entries for the same hostname and image_name combination
    existing_updates = db.query(DiunUpdate).filter(
        DiunUpdate.hostname == update_data.hostname,
        DiunUpdate.image_name == update_data.image_name
    ).all()
    for update in existing_updates:
        db.delete(update)

    # Create new update
    new_update = DiunUpdate(
        hostname=update_data.hostname,
        status=update_data.status,
        provider=update_data.provider,
        image_name=update_data.image_name,
        image_tag=update_data.image_tag,
        digest=update_data.digest,
        image_created_at=update_data.image_created_at,
        hub_link=update_data.hub_link,
    )
    db.add(new_update)
    
    # Commit both operations together
    db.commit()
    db.refresh(new_update)
    return new_update

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
