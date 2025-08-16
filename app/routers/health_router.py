from fastapi import APIRouter, Depends, Path
from sqlalchemy import text

# Import your dependencies and logger
from db import get_db, Session
from app_log_config import logger

router = APIRouter()


@router.get("/status/router")
def get_status():
    logger.info("Router endpoint '/status/router' was hit.")
    return {"status": "Router is OK!",}


@router.get("/status/database")
def get_status(db: Session = Depends(get_db)):
    logger.info("Router endpoint '/status/db' was hit.")
    # Simple DB check
    db.execute(text("SELECT 1"))
    return {"status": "Database is OK!"}
