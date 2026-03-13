from sqlalchemy import create_engine, Column, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
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
    __table_args__ = (
        UniqueConstraint('hostname', 'image_name', name='uq_hostname_image_name'),
    )

    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String, index=True)
    status = Column(String, index=True)
    provider = Column(String)
    image_name = Column(String, index=True)
    image_tag = Column(String)
    hub_link = Column(String)
    digest = Column(String)
    image_created_at = Column(DateTime)  # When the image was created (from DIUN)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))  # When webhook was received

def upsert_diun_update(db: Session, update_data: DiunUpdateData) -> DiunUpdate:
    """
    Create or update a DIUN update record atomically using SQLite ON CONFLICT DO UPDATE,
    replacing any existing entry for the same hostname and image name combination.

    Args:
        db: Database session
        update_data: DiunUpdateData object with parsed image data
    """
    stmt = sqlite_insert(DiunUpdate).values(
        hostname=update_data.hostname,
        status=update_data.status,
        provider=update_data.provider,
        image_name=update_data.image_name,
        image_tag=update_data.image_tag,
        digest=update_data.digest,
        image_created_at=update_data.image_created_at,
        hub_link=update_data.hub_link,
        created_at=datetime.now(UTC),
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=['hostname', 'image_name'],
        set_=dict(
            status=stmt.excluded.status,
            provider=stmt.excluded.provider,
            image_tag=stmt.excluded.image_tag,
            digest=stmt.excluded.digest,
            image_created_at=stmt.excluded.image_created_at,
            hub_link=stmt.excluded.hub_link,
            created_at=stmt.excluded.created_at,
        )
    )
    db.execute(stmt)
    db.commit()
    return db.query(DiunUpdate).filter(
        DiunUpdate.hostname == update_data.hostname,
        DiunUpdate.image_name == update_data.image_name,
    ).one()

def delete_diun_update(db: Session, update_id: int) -> bool:
    """
    Delete a DIUN update record by ID.
    
    Args:
        db: Database session
        update_id: ID of the update to delete
        
    Returns:
        True if the update was found and deleted, False if not found
    """
    update = db.query(DiunUpdate).filter(DiunUpdate.id == update_id).first()
    if not update:
        return False
        
    db.delete(update)
    db.commit()
    return True

def delete_all_diun_updates(db: Session) -> int:
    """
    Delete all DIUN update records.
    
    Args:
        db: Database session
        
    Returns:
        Number of records deleted
    """
    count = db.query(DiunUpdate).count()
    db.query(DiunUpdate).delete()
    db.commit()
    return count

def get_all_diun_updates(db: Session, skip: int = 0, limit: int | None = None) -> list[DiunUpdate]:
    """
    Get DIUN update records ordered by creation time (newest first).

    Args:
        db: Database session
        skip: Number of records to skip (offset)
        limit: Maximum number of records to return (None = no limit)

    Returns:
        List of DiunUpdate records ordered by created_at descending
    """
    query = db.query(DiunUpdate).order_by(DiunUpdate.created_at.desc()).offset(skip)
    if limit is not None:
        query = query.limit(limit)
    return query.all()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
