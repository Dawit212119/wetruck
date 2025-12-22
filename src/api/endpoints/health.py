from fastapi import APIRouter, Depends,HTTPException,status
from sqlalchemy import text
from sqlalchemy.orm import Session
from src.core.db.session import get_db  # <- new session dependency
from src.core.app_logging import logger


router = APIRouter()

@router.get("/check")
def health_check(db: Session = Depends(get_db)):
    """
    Simple health check endpoint to verify database connectivity using the new session.
    """
    try:
        result = db.execute(text("SELECT 1"))
        row = result.fetchone()
        logger.info(f"DB connected, result: {row[0]}")
        return {"status": "ok", "db": f"connected, result: {row[0]}"}
    except Exception as e:
        logger.exception("DB connection failed")
        return {"status": "error", "db": f"error: {str(e)}"}




