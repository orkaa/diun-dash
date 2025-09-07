from fastapi import FastAPI, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from .database import SessionLocal, engine, DiunUpdate, Base, get_db
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
from alembic.config import Config
from alembic import command
import logging

# Configure application logging without interfering with uvicorn
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Function to run Alembic migrations
def run_migrations():
    # Ensure the database directory exists
    db_file_path = os.path.abspath("diun.db")
    db_directory = os.path.dirname(db_file_path)
    if not os.path.exists(db_directory):
        os.makedirs(db_directory)

    alembic_cfg = Config("src/alembic.ini")
    command.upgrade(alembic_cfg, "head")

# Run migrations on startup  
logger.info("Starting application...")
run_migrations()
logger.info("Migrations completed.")
logger.info("Starting FastAPI application")

app = FastAPI()

templates = Jinja2Templates(directory="templates")

@app.post("/webhook")
async def receive_webhook(
    request: Request,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    logger.info("Received webhook request")
    
    if authorization != os.environ.get("DIUN_WEBHOOK_TOKEN"):
        logger.warning("Unauthorized webhook request")
        raise HTTPException(status_code=401, detail="Unauthorized")

    data = await request.json()
    logger.info(f"Processing webhook data for image: {data.get('image', 'unknown')}")
    image_full = data.get("image", "")
    image_parts = image_full.rsplit(':', 1)
    image_name = image_parts[0] if len(image_parts) > 1 else image_full
    image_tag = image_parts[1] if len(image_parts) > 1 else "latest"

    # Delete existing entries for the same image_name
    existing_updates = db.query(DiunUpdate).filter(DiunUpdate.image_name == image_name).all()
    for update in existing_updates:
        db.delete(update)
    db.commit()

    new_update = DiunUpdate(
        hostname=data.get("hostname"),
        status=data.get("status"),
        provider=data.get("provider"),
        image_name=image_name,
        image_tag=image_tag,
        hub_link=data.get("hub_link"),
        digest=data.get("digest"),
    )
    db.add(new_update)
    db.commit()
    db.refresh(new_update)
    logger.info(f"Successfully processed update for {image_name}:{image_tag}")
    return {"message": "Webhook received"}

@app.delete("/updates/{update_id}")
async def delete_update(update_id: int, db: Session = Depends(get_db)):
    update = db.query(DiunUpdate).filter(DiunUpdate.id == update_id).first()
    if not update:
        raise HTTPException(status_code=404, detail="Update not found")
    db.delete(update)
    db.commit()
    return {"message": "Update marked as fixed"}

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Session = Depends(get_db)):
    updates = db.query(DiunUpdate).order_by(DiunUpdate.created_at.desc()).all()
    return templates.TemplateResponse("index.html", {"request": request, "updates": updates})